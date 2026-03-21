"""
CHECK MATRIX PROJECTION TEST

Hypothesis: The power-law exponent scaling with d is explained by the
parity check matrix H(d) acting as a spatial filter on physically
correlated noise. Same noise, different projection → different exponent.

Method:
1. Extract the detector error model from each Stim circuit
2. Build the detector-to-fault mapping (which physical faults trigger which detectors)
3. Model physical noise with spatial correlation: Sigma_ij = sigma^2 * f(dist(i,j))
   where f is a power-law or exponential with tunable parameters
4. Compute predicted syndrome correlations: C_syndrome = H @ Sigma_physical @ H^T
5. Bin by detector distance, fit power law
6. Find ONE physical correlation function that best predicts ALL code distances
7. Compare predicted vs observed PL exponent scaling

If one physical noise model predicts the correct d-dependence → classical explanation.
If no physical model works → something else is going on.
"""
import os, sys, time
import numpy as np
from scipy import optimize, stats
import stim
import warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:\Users\andre\Claudius\google_105Q_surface_code_d3_d5_d7'

EXPERIMENTS = [
    ('d3', 'r50', f'{BASE}/d3_at_q6_7/Z/r50'),
    ('d5', 'r50', f'{BASE}/d5_at_q4_7/Z/r50'),
    ('d7', 'r50', f'{BASE}/d7_at_q6_7/Z/r50'),
]

# ============================================================
# EXTRACT DETECTOR STRUCTURE FROM STIM CIRCUITS
# ============================================================

def get_detector_coords(circuit):
    coords = {}
    det_idx = 0
    for instruction in circuit.flattened():
        if instruction.name == 'DETECTOR':
            coords[det_idx] = list(instruction.gate_args_copy())
            det_idx += 1
    return coords, det_idx

def build_detector_fault_matrix(circuit):
    """
    Build the matrix mapping faults to detectors.
    Uses Stim's detector error model to find which errors affect which detectors.
    Returns: fault_matrix (n_det x n_faults), fault_coords (spatial positions of faults)
    """
    dem = circuit.detector_error_model(decompose_errors=True)

    # Parse the DEM to build detector-fault incidence
    n_det = circuit.num_detectors
    faults = []  # list of (detector_set, probability)

    for instruction in dem.flattened():
        if instruction.type == 'error':
            prob = instruction.args_copy()[0]
            dets = []
            for target in instruction.targets_copy():
                if target.is_relative_detector_id():
                    dets.append(target.val)
            if dets:
                faults.append((dets, prob))

    n_faults = len(faults)
    print(f"  DEM: {n_det} detectors, {n_faults} fault mechanisms")

    # Build incidence matrix H: H[det, fault] = 1 if fault triggers detector
    H = np.zeros((n_det, n_faults), dtype=np.float32)
    fault_probs = np.zeros(n_faults)

    for f_idx, (dets, prob) in enumerate(faults):
        fault_probs[f_idx] = prob
        for d in dets:
            if d < n_det:
                H[d, f_idx] = 1.0

    return H, fault_probs, n_faults

def extract_fault_spatial_structure(circuit, H, n_faults):
    """
    For each fault, estimate its spatial location based on which detectors it triggers.
    Fault position = centroid of triggered detectors' spatial coords.
    """
    coords, n_det = get_detector_coords(circuit)
    fault_positions = np.zeros((n_faults, 2))

    for f in range(n_faults):
        triggered = np.where(H[:, f] > 0)[0]
        if len(triggered) > 0:
            positions = []
            for d in triggered:
                if d in coords and len(coords[d]) >= 2:
                    positions.append([coords[d][0], coords[d][1]])
            if positions:
                fault_positions[f] = np.mean(positions, axis=0)

    return fault_positions

def compute_syndrome_correlation_from_physical(H, physical_cov, fault_probs):
    """
    Given H (detector x fault) and a physical fault covariance matrix,
    compute the predicted syndrome correlation matrix.

    For independent faults with correlation:
    C_syndrome[i,j] = sum_{f,g} H[i,f] * Sigma[f,g] * H[j,g]
                     = (H @ Sigma @ H^T)[i,j]

    The diagonal gives detector firing rates, off-diagonal gives correlations.
    """
    # Syndrome covariance
    syndrome_cov = H @ physical_cov @ H.T

    # Convert to correlation matrix
    diag = np.sqrt(np.diag(syndrome_cov))
    diag[diag == 0] = 1.0
    syndrome_corr = syndrome_cov / np.outer(diag, diag)
    np.fill_diagonal(syndrome_corr, 1.0)

    return syndrome_corr

# ============================================================
# PHYSICAL NOISE MODELS
# ============================================================

def make_physical_covariance(fault_positions, fault_probs, corr_func, params):
    """
    Build physical fault covariance matrix.
    Sigma[f,g] = sqrt(p_f * p_g) * corr_func(dist(f,g), params)
    """
    n = len(fault_probs)
    # Pairwise distances
    diff = fault_positions[:, np.newaxis, :] - fault_positions[np.newaxis, :, :]
    dist = np.sqrt((diff**2).sum(axis=-1))

    # Correlation matrix
    C = corr_func(dist, params)

    # Scale by fault probabilities
    p_sqrt = np.sqrt(fault_probs)
    Sigma = np.outer(p_sqrt, p_sqrt) * C

    return Sigma

def power_law_corr(dist, params):
    """C(d) = 1 for d=0, (d/scale)^alpha for d>0"""
    scale, alpha = params
    C = np.ones_like(dist)
    mask = dist > 0.01
    C[mask] = np.clip((dist[mask] / scale) ** alpha, 0, 1)
    return C

def exponential_corr(dist, params):
    """C(d) = exp(-d/length)"""
    length = params[0]
    return np.exp(-dist / length)

# ============================================================
# ANALYSIS HELPERS
# ============================================================

def compute_distance_matrix(coords, n_det):
    pos = np.zeros((n_det, 2))
    for i in range(n_det):
        if i in coords and len(coords[i]) >= 2:
            pos[i] = [coords[i][0], coords[i][1]]
    diff = pos[:, np.newaxis, :] - pos[np.newaxis, :, :]
    return np.sqrt((diff**2).sum(axis=-1)), pos

def bin_correlations_by_distance(corr_matrix, dist_matrix, n_bins=20):
    n = corr_matrix.shape[0]
    triu_idx = np.triu_indices(n, k=1)
    dists = dist_matrix[triu_idx]
    corrs = np.abs(corr_matrix[triu_idx])
    mask = dists > 0.01
    dists, corrs = dists[mask], corrs[mask]
    if len(dists) == 0:
        return np.array([]), np.array([])
    d_min = max(dists.min(), 0.1)
    bins = np.logspace(np.log10(d_min), np.log10(dists.max()), n_bins + 1)
    centers, means = [], []
    for i in range(n_bins):
        m = (dists >= bins[i]) & (dists < bins[i+1])
        if m.sum() > 0:
            centers.append(np.sqrt(bins[i] * bins[i+1]))
            means.append(corrs[m].mean())
    return np.array(centers), np.array(means)

def fit_power_law(x, y):
    mask = (x > 0) & (y > 0)
    if mask.sum() < 3: return None, None, 0
    try:
        slope, intercept, r, p, se = stats.linregress(np.log(x[mask]), np.log(y[mask]))
        return np.exp(intercept), slope, r**2
    except: return None, None, 0

# ============================================================
# MAIN TEST
# ============================================================

def load_real_residual_exponent(path, d_label):
    """Load real data and compute the rate-matched PL exponent for reference."""
    noisy_stim = os.path.join(path, 'circuit_noisy_si1000.stim')
    ideal_stim = os.path.join(path, 'circuit_ideal.stim')
    circuit_path = ideal_stim if os.path.exists(ideal_stim) else noisy_stim
    circuit = stim.Circuit.from_file(circuit_path)
    coords, n_det = get_detector_coords(circuit)

    bytes_per_shot = (n_det + 7) // 8
    raw = np.fromfile(os.path.join(path, 'detection_events.b8'), dtype=np.uint8)
    n_shots = len(raw) // bytes_per_shot
    raw = raw[:n_shots * bytes_per_shot].reshape(n_shots, bytes_per_shot)
    real_data = np.unpackbits(raw, axis=1, bitorder='little')[:, :n_det].astype(np.float32)
    real_rates = real_data.mean(axis=0)

    # SI1000 simulation
    noisy_circuit = stim.Circuit.from_file(noisy_stim)
    sampler = noisy_circuit.compile_detector_sampler()
    sim_data = sampler.sample(n_shots).astype(np.float32)
    n_det = min(n_det, sim_data.shape[1])
    real_data = real_data[:, :n_det]
    sim_data = sim_data[:, :n_det]

    # Rate-match
    rng = np.random.default_rng(42)
    sim_matched = sim_data.copy()
    sim_rates = sim_data.mean(axis=0)
    for d in range(n_det):
        sr, rr = sim_rates[d], real_rates[d] if d < len(real_rates) else sim_rates[d]
        if rr > sr and sr < 1.0:
            p_flip = min((rr - sr) / (1.0 - sr), 1.0)
            zeros = sim_matched[:, d] < 0.5
            flips = rng.random(n_shots) < p_flip
            sim_matched[:, d] = np.where(zeros & flips, 1.0, sim_matched[:, d])
        elif rr < sr and sr > 0:
            p_flip = min((sr - rr) / sr, 1.0)
            ones = sim_matched[:, d] > 0.5
            flips = rng.random(n_shots) < p_flip
            sim_matched[:, d] = np.where(ones & flips, 0.0, sim_matched[:, d])

    real_corr = compute_correlation_matrix(real_data)
    matched_corr = compute_correlation_matrix(sim_matched)
    residual = real_corr - matched_corr
    np.fill_diagonal(residual, 0)

    dist_matrix, _ = compute_distance_matrix(coords, n_det)
    d_r, c_r = bin_correlations_by_distance(np.abs(residual), dist_matrix)
    _, pl_exp, pl_r2 = fit_power_law(d_r, c_r)

    return pl_exp, pl_r2

def compute_correlation_matrix(data):
    means = data.mean(axis=0)
    centered = data - means
    stds = centered.std(axis=0)
    stds[stds == 0] = 1.0
    normalized = centered / stds
    corr = (normalized.T @ normalized) / data.shape[0]
    np.fill_diagonal(corr, 1.0)
    return corr

if __name__ == '__main__':
    print("="*70)
    print("  CHECK MATRIX PROJECTION TEST")
    print("  Can H(d) acting on fixed physical noise explain d-dependence?")
    print("="*70)

    # Step 1: Extract detector-fault matrices for each code distance
    circuit_data = {}
    for d_label, r_label, path in EXPERIMENTS:
        print(f"\n  Loading {d_label}/{r_label}...")
        noisy_stim = os.path.join(path, 'circuit_noisy_si1000.stim')
        ideal_stim = os.path.join(path, 'circuit_ideal.stim')
        circuit_path = ideal_stim if os.path.exists(ideal_stim) else noisy_stim
        circuit = stim.Circuit.from_file(circuit_path)
        coords, n_det = get_detector_coords(circuit)

        print(f"  Building detector error model...")
        H, fault_probs, n_faults = build_detector_fault_matrix(circuit)
        fault_pos = extract_fault_spatial_structure(circuit, H, n_faults)

        dist_matrix, det_positions = compute_distance_matrix(coords, n_det)

        # Sparsity of H
        nnz = (H > 0).sum()
        print(f"  H shape: {H.shape}, nonzero: {nnz}, "
              f"avg detectors/fault: {nnz/n_faults:.2f}")

        # Detector spatial extent
        if len(coords) > 0:
            all_pos = np.array([coords[i][:2] for i in range(min(n_det, len(coords))) if i in coords])
            extent = all_pos.max(axis=0) - all_pos.min(axis=0)
            print(f"  Detector spatial extent: {extent[0]:.1f} x {extent[1]:.1f}")

        circuit_data[d_label] = {
            'H': H, 'fault_probs': fault_probs, 'n_faults': n_faults,
            'fault_pos': fault_pos, 'n_det': n_det, 'coords': coords,
            'dist_matrix': dist_matrix, 'det_positions': det_positions,
            'circuit': circuit
        }

    # Step 2: Get observed rate-matched PL exponents for reference
    print("\n" + "="*70)
    print("  OBSERVED (rate-matched) PL EXPONENTS")
    print("="*70)
    observed_exponents = {}
    for d_label, r_label, path in EXPERIMENTS:
        print(f"  Computing {d_label}/{r_label}...")
        exp, r2 = load_real_residual_exponent(path, d_label)
        observed_exponents[d_label] = exp
        print(f"  {d_label}: PL exponent = {exp:.4f}, R2 = {r2:.4f}")

    # Step 3: Scan physical noise models and predict syndrome PL exponents
    print("\n" + "="*70)
    print("  PREDICTED PL EXPONENTS FROM CHECK MATRIX PROJECTION")
    print("="*70)

    # Try a range of physical correlation parameters
    # Physical noise: power-law with various exponents
    physical_alphas = [-0.5, -1.0, -1.5, -2.0, -2.5, -3.0]
    physical_scales = [1.0, 2.0, 5.0]

    best_fit = None
    best_error = float('inf')

    print(f"\n  {'Phys alpha':>12} {'Phys scale':>12} "
          f"{'d3 pred':>10} {'d5 pred':>10} {'d7 pred':>10} "
          f"{'d3 obs':>10} {'d5 obs':>10} {'d7 obs':>10} {'RMS err':>10}")
    print(f"  {'-'*96}")

    for alpha in physical_alphas:
        for scale in physical_scales:
            predicted = {}
            for d_label in ['d3', 'd5', 'd7']:
                cd = circuit_data[d_label]
                H = cd['H']
                fp = cd['fault_probs']
                fpos = cd['fault_pos']
                n_det = cd['n_det']

                # Build physical covariance with power-law correlations
                # Use a subset of faults for computational feasibility
                max_faults = min(cd['n_faults'], 5000)
                if cd['n_faults'] > max_faults:
                    # Subsample highest-probability faults
                    top_idx = np.argsort(fp)[-max_faults:]
                    H_sub = H[:, top_idx]
                    fp_sub = fp[top_idx]
                    fpos_sub = fpos[top_idx]
                else:
                    H_sub = H
                    fp_sub = fp
                    fpos_sub = fpos

                try:
                    Sigma = make_physical_covariance(fpos_sub, fp_sub,
                                                     power_law_corr, (scale, alpha))
                    syn_corr = compute_syndrome_correlation_from_physical(H_sub, Sigma, fp_sub)

                    # Compute PL exponent of predicted syndrome correlations
                    dm = cd['dist_matrix']
                    d_r, c_r = bin_correlations_by_distance(np.abs(syn_corr), dm)
                    _, pl_exp, pl_r2 = fit_power_law(d_r, c_r)
                    predicted[d_label] = pl_exp
                except Exception as e:
                    predicted[d_label] = None

            # Compute fit quality
            if all(v is not None for v in predicted.values()):
                errors = []
                for d_label in ['d3', 'd5', 'd7']:
                    if observed_exponents[d_label] is not None:
                        errors.append((predicted[d_label] - observed_exponents[d_label])**2)
                if errors:
                    rms = np.sqrt(np.mean(errors))

                    d3p = f"{predicted['d3']:.4f}" if predicted['d3'] else "N/A"
                    d5p = f"{predicted['d5']:.4f}" if predicted['d5'] else "N/A"
                    d7p = f"{predicted['d7']:.4f}" if predicted['d7'] else "N/A"
                    d3o = f"{observed_exponents['d3']:.4f}" if observed_exponents['d3'] else "N/A"
                    d5o = f"{observed_exponents['d5']:.4f}" if observed_exponents['d5'] else "N/A"
                    d7o = f"{observed_exponents['d7']:.4f}" if observed_exponents['d7'] else "N/A"

                    print(f"  {alpha:>12.1f} {scale:>12.1f} "
                          f"{d3p:>10} {d5p:>10} {d7p:>10} "
                          f"{d3o:>10} {d5o:>10} {d7o:>10} {rms:>10.4f}")

                    if rms < best_error:
                        best_error = rms
                        best_fit = {
                            'alpha': alpha, 'scale': scale,
                            'predicted': predicted.copy(), 'rms': rms
                        }

    # Step 4: Try exponential physical correlation too
    print(f"\n  Exponential physical correlation:")
    exp_lengths = [1.0, 2.0, 3.0, 5.0, 8.0, 12.0, 20.0]

    for length in exp_lengths:
        predicted = {}
        for d_label in ['d3', 'd5', 'd7']:
            cd = circuit_data[d_label]
            H = cd['H']
            fp = cd['fault_probs']
            fpos = cd['fault_pos']

            max_faults = min(cd['n_faults'], 5000)
            if cd['n_faults'] > max_faults:
                top_idx = np.argsort(fp)[-max_faults:]
                H_sub, fp_sub, fpos_sub = H[:, top_idx], fp[top_idx], fpos[top_idx]
            else:
                H_sub, fp_sub, fpos_sub = H, fp, fpos

            try:
                Sigma = make_physical_covariance(fpos_sub, fp_sub,
                                                 exponential_corr, (length,))
                syn_corr = compute_syndrome_correlation_from_physical(H_sub, Sigma, fp_sub)
                dm = cd['dist_matrix']
                d_r, c_r = bin_correlations_by_distance(np.abs(syn_corr), dm)
                _, pl_exp, pl_r2 = fit_power_law(d_r, c_r)
                predicted[d_label] = pl_exp
            except:
                predicted[d_label] = None

        if all(v is not None for v in predicted.values()):
            errors = [(predicted[dl] - observed_exponents[dl])**2
                      for dl in ['d3', 'd5', 'd7'] if observed_exponents[dl] is not None]
            if errors:
                rms = np.sqrt(np.mean(errors))
                d3p = f"{predicted['d3']:.4f}"
                d5p = f"{predicted['d5']:.4f}"
                d7p = f"{predicted['d7']:.4f}"
                d3o = f"{observed_exponents['d3']:.4f}"
                d5o = f"{observed_exponents['d5']:.4f}"
                d7o = f"{observed_exponents['d7']:.4f}"

                print(f"  len={length:>5.1f}       "
                      f"{d3p:>10} {d5p:>10} {d7p:>10} "
                      f"{d3o:>10} {d5o:>10} {d7o:>10} {rms:>10.4f}")

                if rms < best_error:
                    best_error = rms
                    best_fit = {
                        'type': 'exponential', 'length': length,
                        'predicted': predicted.copy(), 'rms': rms
                    }

    # Step 5: Check the KEY QUESTION - does the predicted exponent FLATTEN with d?
    print("\n" + "="*70)
    print("  KEY TEST: Does H(d) projection reproduce the flattening?")
    print("="*70)

    if best_fit:
        print(f"\n  Best physical noise model: {best_fit}")
        pred = best_fit['predicted']
        obs = observed_exponents

        # Does predicted exponent trend toward 0 with d?
        d_vals = [3, 5, 7]
        pred_vals = [pred[f'd{d}'] for d in d_vals]
        obs_vals = [obs[f'd{d}'] for d in d_vals]

        pred_slope, _, pred_r, _, _ = stats.linregress(d_vals, pred_vals)
        obs_slope, _, obs_r, _, _ = stats.linregress(d_vals, obs_vals)

        print(f"\n  Observed flattening:  slope = {obs_slope:.5f}/d, R = {obs_r:.4f}")
        print(f"  Predicted flattening: slope = {pred_slope:.5f}/d, R = {pred_r:.4f}")

        if pred_slope > 0 and obs_slope > 0:
            ratio = pred_slope / obs_slope
            print(f"  Ratio: {ratio:.3f}")

            if 0.5 < ratio < 2.0:
                print(f"\n  >> CHECK MATRIX PROJECTION EXPLAINS THE FLATTENING")
                print(f"  >> The d-dependence is an artifact of how H(d) filters fixed physical noise.")
                print(f"  >> No code-awareness required. Classical explanation SUFFICIENT.")
            elif 0.2 < ratio < 5.0:
                print(f"\n  >> CHECK MATRIX PROJECTION PARTIALLY EXPLAINS THE FLATTENING")
                print(f"  >> H(d) filtering accounts for {ratio*100:.0f}% of the effect.")
                print(f"  >> Some residual d-dependence remains unexplained.")
            else:
                print(f"\n  >> CHECK MATRIX PROJECTION DOES NOT EXPLAIN THE FLATTENING")
                print(f"  >> The predicted trend is {ratio:.1f}x the observed trend.")
                print(f"  >> Something beyond classical noise filtering couples to d.")
        elif pred_slope * obs_slope < 0:
            print(f"\n  >> WRONG DIRECTION: H(d) projection predicts OPPOSITE trend!")
            print(f"  >> The flattening is NOT explained by check matrix filtering.")
        else:
            print(f"\n  >> Insufficient data to determine trend.")

    # Step 6: Structural analysis - HOW does H(d) differ?
    print("\n" + "="*70)
    print("  STRUCTURAL ANALYSIS: How does H(d) change with code distance?")
    print("="*70)

    for d_label in ['d3', 'd5', 'd7']:
        cd = circuit_data[d_label]
        H = cd['H']
        n_det = cd['n_det']
        n_faults = cd['n_faults']

        # Average number of detectors per fault
        avg_det_per_fault = (H > 0).sum(axis=0).mean()
        # Average number of faults per detector
        avg_fault_per_det = (H > 0).sum(axis=1).mean()
        # Fraction of H that's nonzero (connectivity)
        connectivity = (H > 0).sum() / (n_det * n_faults) if n_det * n_faults > 0 else 0

        # H overlap: how much do different detectors share faults?
        # Overlap[i,j] = number of faults that trigger both i and j
        # This IS the check matrix structure that creates syndrome correlations
        # Compute for a random subset
        n_sample = min(500, n_det)
        idx = np.random.choice(n_det, n_sample, replace=False)
        H_sample = H[idx]
        overlap = (H_sample @ H_sample.T)
        np.fill_diagonal(overlap, 0)
        avg_overlap = overlap.mean()
        max_overlap = overlap.max()

        # Overlap vs distance
        dm_sample = cd['dist_matrix'][np.ix_(idx, idx)]
        triu = np.triu_indices(n_sample, k=1)
        dists = dm_sample[triu]
        overlaps = overlap[triu]
        mask = dists > 0.01

        if mask.sum() > 10:
            dists_f, overlaps_f = dists[mask], overlaps[mask]
            _, ov_slope, ov_r2 = fit_power_law(dists_f, overlaps_f + 0.01)
        else:
            ov_slope, ov_r2 = None, 0

        print(f"\n  {d_label}: {n_det} det, {n_faults} faults")
        print(f"    Avg det/fault: {avg_det_per_fault:.2f}")
        print(f"    Avg fault/det: {avg_fault_per_det:.2f}")
        print(f"    Connectivity:  {connectivity:.6f}")
        print(f"    Avg overlap:   {avg_overlap:.4f}")
        print(f"    Max overlap:   {max_overlap:.0f}")
        if ov_slope is not None:
            print(f"    Overlap vs dist PL: exponent={ov_slope:.4f}, R2={ov_r2:.4f}")

    print("\n" + "="*70)
    print("  DONE")
    print("="*70)
