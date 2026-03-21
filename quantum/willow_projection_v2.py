"""
CHECK MATRIX PROJECTION TEST v2

Fixed: always use noisy circuit for DEM, handle large fault sets,
compute predictions properly.
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

def get_detector_coords(circuit):
    coords = {}
    det_idx = 0
    for instruction in circuit.flattened():
        if instruction.name == 'DETECTOR':
            coords[det_idx] = list(instruction.gate_args_copy())
            det_idx += 1
    return coords, det_idx

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
    if len(dists) == 0: return np.array([]), np.array([])
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

def compute_correlation_matrix(data):
    means = data.mean(axis=0)
    centered = data - means
    stds = centered.std(axis=0)
    stds[stds == 0] = 1.0
    normalized = centered / stds
    corr = (normalized.T @ normalized) / data.shape[0]
    np.fill_diagonal(corr, 1.0)
    return corr

def build_dem_matrix(circuit):
    """Build detector-fault incidence from NOISY circuit DEM."""
    dem = circuit.detector_error_model(decompose_errors=True)
    n_det = circuit.num_detectors
    faults = []
    for instruction in dem.flattened():
        if instruction.type == 'error':
            prob = instruction.args_copy()[0]
            dets = [t.val for t in instruction.targets_copy() if t.is_relative_detector_id()]
            if dets:
                faults.append((dets, prob))
    n_faults = len(faults)
    H = np.zeros((n_det, n_faults), dtype=np.float32)
    probs = np.zeros(n_faults)
    for f_idx, (dets, prob) in enumerate(faults):
        probs[f_idx] = prob
        for d in dets:
            if d < n_det: H[d, f_idx] = 1.0
    return H, probs, n_faults

def fault_positions_from_H(H, coords, n_faults):
    """Estimate fault spatial positions from detector coords."""
    positions = np.zeros((n_faults, 2))
    for f in range(n_faults):
        triggered = np.where(H[:, f] > 0)[0]
        pts = [[coords[d][0], coords[d][1]] for d in triggered if d in coords and len(coords[d]) >= 2]
        if pts: positions[f] = np.mean(pts, axis=0)
    return positions

# ============================================================
# PROJECTION COMPUTATION
# ============================================================

def project_physical_noise(H, fault_probs, fault_pos, phys_corr_func, params,
                           max_faults=3000):
    """
    Compute syndrome correlation from physical noise projection.
    C_syn = H @ Sigma_phys @ H^T
    where Sigma_phys[f,g] = sqrt(p_f * p_g) * corr_func(dist(f,g))
    """
    n_faults = H.shape[1]

    # Subsample if too many faults
    if n_faults > max_faults:
        idx = np.argsort(fault_probs)[-max_faults:]
        H = H[:, idx]
        fault_probs = fault_probs[idx]
        fault_pos = fault_pos[idx]
        n_faults = max_faults

    # Pairwise fault distances
    diff = fault_pos[:, np.newaxis, :] - fault_pos[np.newaxis, :, :]
    dist = np.sqrt((diff**2).sum(axis=-1))

    # Physical correlation
    C_phys = phys_corr_func(dist, params)

    # Scale by probabilities
    p_sqrt = np.sqrt(np.abs(fault_probs))
    Sigma = np.outer(p_sqrt, p_sqrt) * C_phys

    # Project through H
    syn_cov = H @ Sigma @ H.T

    # Normalize to correlation
    diag = np.sqrt(np.abs(np.diag(syn_cov)))
    diag[diag == 0] = 1.0
    syn_corr = syn_cov / np.outer(diag, diag)
    np.fill_diagonal(syn_corr, 1.0)

    return syn_corr

def power_law_corr(dist, params):
    scale, alpha = params
    C = np.ones_like(dist)
    mask = dist > 0.01
    C[mask] = np.clip((dist[mask] / scale) ** alpha, 0, 1)
    return C

def exponential_corr(dist, params):
    return np.exp(-dist / params[0])

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("="*70)
    print("  CHECK MATRIX PROJECTION TEST v2")
    print("  Can H(d) + fixed physical noise explain PL flattening?")
    print("="*70)

    # Load circuits and build DEMs
    data = {}
    for d_label, r_label, path in EXPERIMENTS:
        print(f"\n  === {d_label}/{r_label} ===")
        # ALWAYS use noisy circuit for DEM
        noisy_stim = os.path.join(path, 'circuit_noisy_si1000.stim')
        circuit = stim.Circuit.from_file(noisy_stim)
        coords, n_det = get_detector_coords(circuit)

        print(f"  Building DEM from noisy circuit...")
        H, probs, n_faults = build_dem_matrix(circuit)
        print(f"  {n_det} detectors, {n_faults} faults, "
              f"H nonzero: {(H > 0).sum()}")

        fpos = fault_positions_from_H(H, coords, n_faults)
        dist_matrix, det_pos = compute_distance_matrix(coords, n_det)

        data[d_label] = {
            'H': H, 'probs': probs, 'n_faults': n_faults,
            'fpos': fpos, 'n_det': n_det, 'coords': coords,
            'dist_matrix': dist_matrix, 'circuit': circuit
        }

    # Observed exponents (rate-matched, from previous run)
    # Recompute quickly
    print("\n" + "="*70)
    print("  OBSERVED RATE-MATCHED EXPONENTS")
    print("="*70)

    observed = {}
    for d_label, r_label, path in EXPERIMENTS:
        noisy_stim = os.path.join(path, 'circuit_noisy_si1000.stim')
        circuit = stim.Circuit.from_file(noisy_stim)
        coords, n_det = get_detector_coords(circuit)

        bytes_per_shot = (n_det + 7) // 8
        raw = np.fromfile(os.path.join(path, 'detection_events.b8'), dtype=np.uint8)
        n_shots = len(raw) // bytes_per_shot
        raw = raw[:n_shots * bytes_per_shot].reshape(n_shots, bytes_per_shot)
        real_data = np.unpackbits(raw, axis=1, bitorder='little')[:, :n_det].astype(np.float32)
        real_rates = real_data.mean(axis=0)

        sampler = circuit.compile_detector_sampler()
        sim_data = sampler.sample(n_shots).astype(np.float32)
        n_use = min(n_det, sim_data.shape[1])
        real_data, sim_data = real_data[:, :n_use], sim_data[:, :n_use]

        # Rate-match
        rng = np.random.default_rng(42)
        sim_m = sim_data.copy()
        sr = sim_data.mean(axis=0)
        for i in range(n_use):
            rr = real_rates[i] if i < len(real_rates) else sr[i]
            if rr > sr[i] and sr[i] < 1:
                pf = min((rr - sr[i])/(1-sr[i]), 1)
                z = sim_m[:, i] < 0.5
                sim_m[:, i] = np.where(z & (rng.random(n_shots) < pf), 1, sim_m[:, i])
            elif rr < sr[i] and sr[i] > 0:
                pf = min((sr[i] - rr)/sr[i], 1)
                o = sim_m[:, i] > 0.5
                sim_m[:, i] = np.where(o & (rng.random(n_shots) < pf), 0, sim_m[:, i])

        rc = compute_correlation_matrix(real_data)
        mc = compute_correlation_matrix(sim_m)
        residual = rc - mc
        np.fill_diagonal(residual, 0)

        dm = data[d_label]['dist_matrix'][:n_use, :n_use]
        dr, cr = bin_correlations_by_distance(np.abs(residual), dm)
        _, pl_exp, pl_r2 = fit_power_law(dr, cr)
        observed[d_label] = {'exp': pl_exp, 'r2': pl_r2}
        print(f"  {d_label}: PL exp = {pl_exp:.4f}, R2 = {pl_r2:.4f}")

    # ============================================================
    # PROJECTION SCAN
    # ============================================================
    print("\n" + "="*70)
    print("  SCANNING PHYSICAL NOISE MODELS")
    print("="*70)

    results_table = []

    # Power-law physical noise
    print(f"\n  --- Power-law physical correlations ---")
    print(f"  {'alpha':>8} {'scale':>8} | {'d3 pred':>10} {'d5 pred':>10} {'d7 pred':>10} | "
          f"{'d3 obs':>10} {'d5 obs':>10} {'d7 obs':>10} | {'RMS':>8} {'Trend?':>8}")
    print(f"  {'-'*100}")

    for alpha in [-0.3, -0.5, -0.8, -1.0, -1.5, -2.0, -3.0]:
        for scale in [1.0, 2.0, 4.0, 8.0]:
            predicted = {}
            for d_label in ['d3', 'd5', 'd7']:
                cd = data[d_label]
                try:
                    syn_corr = project_physical_noise(
                        cd['H'], cd['probs'], cd['fpos'],
                        power_law_corr, (scale, alpha), max_faults=3000)
                    # Compute the RESIDUAL of projected noise vs SI1000 projection
                    # We want: what does the EXTRA correlation look like?
                    # The projected correlation IS the extra part (on top of independent noise)
                    dm = cd['dist_matrix']
                    dr, cr = bin_correlations_by_distance(np.abs(syn_corr), dm)
                    _, pe, pr2 = fit_power_law(dr, cr)
                    predicted[d_label] = pe
                except Exception as e:
                    predicted[d_label] = None

            if all(v is not None for v in predicted.values()):
                errors = [(predicted[dl] - observed[dl]['exp'])**2 for dl in ['d3','d5','d7']]
                rms = np.sqrt(np.mean(errors))

                # Check if predicted exponents flatten with d (like observed)
                pvals = [predicted[f'd{d}'] for d in [3,5,7]]
                trend_slope, _, _, _, _ = stats.linregress([3,5,7], pvals)
                flattens = "YES" if trend_slope > 0 else "no"

                print(f"  {alpha:>8.1f} {scale:>8.1f} | "
                      f"{predicted['d3']:>10.4f} {predicted['d5']:>10.4f} {predicted['d7']:>10.4f} | "
                      f"{observed['d3']['exp']:>10.4f} {observed['d5']['exp']:>10.4f} {observed['d7']['exp']:>10.4f} | "
                      f"{rms:>8.4f} {flattens:>8}")

                results_table.append({
                    'type': 'power_law', 'alpha': alpha, 'scale': scale,
                    'pred': predicted, 'rms': rms, 'flattens': flattens,
                    'trend_slope': trend_slope
                })

    # Exponential physical noise
    print(f"\n  --- Exponential physical correlations ---")
    print(f"  {'length':>8} {'':>8} | {'d3 pred':>10} {'d5 pred':>10} {'d7 pred':>10} | "
          f"{'d3 obs':>10} {'d5 obs':>10} {'d7 obs':>10} | {'RMS':>8} {'Trend?':>8}")
    print(f"  {'-'*100}")

    for length in [0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0, 20.0]:
        predicted = {}
        for d_label in ['d3', 'd5', 'd7']:
            cd = data[d_label]
            try:
                syn_corr = project_physical_noise(
                    cd['H'], cd['probs'], cd['fpos'],
                    exponential_corr, (length,), max_faults=3000)
                dm = cd['dist_matrix']
                dr, cr = bin_correlations_by_distance(np.abs(syn_corr), dm)
                _, pe, pr2 = fit_power_law(dr, cr)
                predicted[d_label] = pe
            except:
                predicted[d_label] = None

        if all(v is not None for v in predicted.values()):
            errors = [(predicted[dl] - observed[dl]['exp'])**2 for dl in ['d3','d5','d7']]
            rms = np.sqrt(np.mean(errors))
            pvals = [predicted[f'd{d}'] for d in [3,5,7]]
            trend_slope, _, _, _, _ = stats.linregress([3,5,7], pvals)
            flattens = "YES" if trend_slope > 0 else "no"

            print(f"  {length:>8.1f} {'':>8} | "
                  f"{predicted['d3']:>10.4f} {predicted['d5']:>10.4f} {predicted['d7']:>10.4f} | "
                  f"{observed['d3']['exp']:>10.4f} {observed['d5']['exp']:>10.4f} {observed['d7']['exp']:>10.4f} | "
                  f"{rms:>8.4f} {flattens:>8}")

            results_table.append({
                'type': 'exponential', 'length': length,
                'pred': predicted, 'rms': rms, 'flattens': flattens,
                'trend_slope': trend_slope
            })

    # ============================================================
    # VERDICT
    # ============================================================
    print("\n" + "="*70)
    print("  VERDICT")
    print("="*70)

    # Find best overall fit
    if results_table:
        best = min(results_table, key=lambda x: x['rms'])
        print(f"\n  Best fit: {best['type']}, RMS={best['rms']:.4f}")
        print(f"  Predicted: d3={best['pred']['d3']:.4f}, d5={best['pred']['d5']:.4f}, d7={best['pred']['d7']:.4f}")
        print(f"  Observed:  d3={observed['d3']['exp']:.4f}, d5={observed['d5']['exp']:.4f}, d7={observed['d7']['exp']:.4f}")

        # Find best among those that reproduce the flattening
        flattening_models = [r for r in results_table if r['flattens'] == 'YES']
        if flattening_models:
            best_flat = min(flattening_models, key=lambda x: x['rms'])
            print(f"\n  Best flattening model: {best_flat['type']}, RMS={best_flat['rms']:.4f}")
            print(f"  Predicted: d3={best_flat['pred']['d3']:.4f}, d5={best_flat['pred']['d5']:.4f}, d7={best_flat['pred']['d7']:.4f}")
            print(f"  Trend slope: {best_flat['trend_slope']:.5f} (observed: ", end="")
            obs_slope, _, _, _, _ = stats.linregress([3,5,7], [observed[f'd{d}']['exp'] for d in [3,5,7]])
            print(f"{obs_slope:.5f})")

            ratio = best_flat['trend_slope'] / obs_slope if obs_slope != 0 else 0
            print(f"  Trend ratio: {ratio:.3f}")

            if 0.3 < ratio < 3.0 and best_flat['rms'] < 0.15:
                print(f"\n  >> H(d) PROJECTION REPRODUCES THE FLATTENING")
                print(f"  >> A single physical noise correlation, projected through different")
                print(f"  >> check matrices, creates the appearance of code-aware correlations.")
                print(f"  >> CLASSICAL EXPLANATION IS SUFFICIENT.")
            else:
                print(f"\n  >> H(d) projection gives trend ratio {ratio:.3f}")
                if ratio < 0.3:
                    print(f"  >> The flattening is too strong to be explained by projection alone.")
                elif ratio > 3.0:
                    print(f"  >> Projection OVER-predicts flattening — wrong mechanism.")
                if best_flat['rms'] > 0.15:
                    print(f"  >> And the absolute exponent values don't match (RMS={best_flat['rms']:.4f})")
        else:
            print(f"\n  >> NO physical noise model reproduces the flattening!")
            print(f"  >> All projections show OPPOSITE trend or no trend.")
            print(f"  >> Check matrix filtering does NOT explain the d-dependence.")

        # Count how many models flatten
        n_flat = len(flattening_models)
        n_total = len(results_table)
        print(f"\n  Models that flatten: {n_flat}/{n_total}")

    # Structural comparison
    print(f"\n  --- H(d) Structure ---")
    obs_slope, _, obs_r, _, _ = stats.linregress([3,5,7], [observed[f'd{d}']['exp'] for d in [3,5,7]])
    print(f"  Observed exponent slope: {obs_slope:.5f}/d (R={obs_r:.4f})")

    for d_label in ['d3', 'd5', 'd7']:
        cd = data[d_label]
        n_det, n_faults = cd['H'].shape
        connectivity = (cd['H'] > 0).sum() / max(n_det * n_faults, 1)
        avg_dets = (cd['H'] > 0).sum(axis=0).mean() if n_faults > 0 else 0
        avg_faults = (cd['H'] > 0).sum(axis=1).mean()

        # The key structural number: effective rank of H
        # (how many independent directions H spans)
        # Approximate via sampling
        if n_faults > 0:
            n_sample = min(2000, n_faults)
            idx = np.random.choice(n_faults, n_sample, replace=False)
            s = np.linalg.svdvals(cd['H'][:, idx].astype(np.float64))
            eff_rank = (s > s[0] * 0.01).sum()
            rank_ratio = eff_rank / min(n_det, n_sample)
        else:
            eff_rank = 0
            rank_ratio = 0

        print(f"  {d_label}: {n_det}x{n_faults}, connectivity={connectivity:.6f}, "
              f"avg_det/fault={avg_dets:.2f}, eff_rank={eff_rank} ({rank_ratio:.3f})")

    print("\n" + "="*70)
