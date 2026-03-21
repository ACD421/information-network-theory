"""
THE KILLER TEST: Can classical noise models reproduce the Willow residual?

We test 3 noise models of increasing complexity against d7/r90 (strongest signal):
  Model A: Spatially correlated bit flips (power-law kernel)
  Model B: TLS fluctuators (shot-block-varying error rates → non-Markovian)
  Model C: Combined A + B

For each, we generate synthetic data ON TOP of SI1000 baseline,
compute the residual vs SI1000, and extract the 4 signatures:
  1. Spatial decay: power-law exponent + R²
  2. Temporal autocorrelation at lags 2-5
  3. Eigenvalue structure (top fraction, participation ratio)
  4. Boundary/bulk ratio

If ANY model reproduces all 4 → the residual is classical noise modeling gap.
If NONE can → something the SI1000 model fundamentally can't capture.
"""
import os, json, sys, time
import numpy as np
from scipy import optimize, stats
import stim
import warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:\Users\andre\Claudius\google_105Q_surface_code_d3_d5_d7'

# ============================================================
# ANALYSIS FUNCTIONS (same as before, condensed)
# ============================================================

def get_detector_coords(circuit):
    coords = {}
    det_idx = 0
    for instruction in circuit.flattened():
        if instruction.name == 'DETECTOR':
            coords[det_idx] = list(instruction.gate_args_copy())
            det_idx += 1
    return coords, det_idx

def compute_correlation_matrix(data):
    means = data.mean(axis=0)
    centered = data - means
    stds = centered.std(axis=0)
    stds[stds == 0] = 1.0
    normalized = centered / stds
    corr = (normalized.T @ normalized) / data.shape[0]
    np.fill_diagonal(corr, 1.0)
    return corr

def compute_distance_matrix(coords, n_det):
    pos = np.zeros((n_det, 2))
    for i in range(n_det):
        if i in coords and len(coords[i]) >= 2:
            pos[i, 0] = coords[i][0]
            pos[i, 1] = coords[i][1]
    diff = pos[:, np.newaxis, :] - pos[np.newaxis, :, :]
    dist = np.sqrt((diff**2).sum(axis=-1))
    return dist, pos

def bin_correlations_by_distance(corr_matrix, dist_matrix, n_bins=20):
    n = corr_matrix.shape[0]
    triu_idx = np.triu_indices(n, k=1)
    dists = dist_matrix[triu_idx]
    corrs = np.abs(corr_matrix[triu_idx])
    mask = dists > 0.01
    dists, corrs = dists[mask], corrs[mask]
    if len(dists) == 0:
        return np.array([]), np.array([])
    d_min, d_max = max(dists.min(), 0.1), dists.max()
    bins = np.logspace(np.log10(d_min), np.log10(d_max), n_bins + 1)
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

def fit_exponential(x, y):
    mask = (x > 0) & (y > 0)
    if mask.sum() < 3: return None, None, 0
    try:
        popt, _ = optimize.curve_fit(lambda x, a, b: a * np.exp(-b * x),
                                      x[mask], y[mask], p0=[y[mask].max(), 1.0], maxfev=5000)
        y_pred = popt[0] * np.exp(-popt[1] * x[mask])
        ss_res = ((y[mask] - y_pred)**2).sum()
        ss_tot = ((y[mask] - y[mask].mean())**2).sum()
        return popt[0], popt[1], 1 - ss_res/ss_tot if ss_tot > 0 else 0
    except: return None, None, 0

def compute_temporal_autocorrelation(data, coords, n_det, max_lag=5):
    spatial_groups = {}
    for i in range(n_det):
        if i in coords and len(coords[i]) >= 3:
            key = (round(coords[i][0], 2), round(coords[i][1], 2))
            spatial_groups.setdefault(key, []).append((coords[i][2], i))
    for key in spatial_groups:
        spatial_groups[key].sort()
    lag_corrs = {lag: [] for lag in range(1, max_lag + 1)}
    for key, detectors in spatial_groups.items():
        if len(detectors) < 2: continue
        for i in range(len(detectors)):
            for j in range(i+1, len(detectors)):
                lag = int(round(detectors[j][0] - detectors[i][0]))
                if 1 <= lag <= max_lag:
                    a = data[:, detectors[i][1]]
                    b = data[:, detectors[j][1]]
                    ac, bc = a - a.mean(), b - b.mean()
                    denom = np.sqrt((ac**2).sum() * (bc**2).sum())
                    if denom > 0:
                        lag_corrs[lag].append((ac * bc).sum() / denom)
    result = {}
    for lag in range(1, max_lag + 1):
        if lag_corrs[lag]:
            result[lag] = {'mean': np.mean(lag_corrs[lag]), 'std': np.std(lag_corrs[lag]),
                          'count': len(lag_corrs[lag])}
    return result

def classify_boundary_bulk(coords, n_det):
    pos = np.zeros((n_det, 2))
    valid = []
    for i in range(n_det):
        if i in coords and len(coords[i]) >= 2:
            pos[i] = [coords[i][0], coords[i][1]]
            valid.append(i)
    if len(valid) < 5: return [], []
    center = pos[valid].mean(axis=0)
    dists = np.sqrt(((pos[valid] - center)**2).sum(axis=1))
    mx = dists.max()
    return ([valid[i] for i, d in enumerate(dists) if d >= 0.7*mx],
            [valid[i] for i, d in enumerate(dists) if d <= 0.5*mx])

def extract_signatures(data, coords, n_det, dist_matrix, label=""):
    """Extract all 4 signatures from a dataset."""
    print(f"\n  [{label}] Computing correlation matrix ({n_det} detectors, {data.shape[0]} shots)...")
    corr = compute_correlation_matrix(data)

    # Firing rates
    rates = data.mean(axis=0)
    print(f"  [{label}] Firing rates: mean={rates.mean():.6f}, std={rates.std():.6f}")

    return corr, rates

def compute_residual_signatures(residual, coords, n_det, dist_matrix, label=""):
    """Compute all signature metrics from a residual matrix."""
    np.fill_diagonal(residual, 0)
    triu_idx = np.triu_indices(n_det, k=1)
    vals = residual[triu_idx]

    res_mean, res_std = vals.mean(), vals.std()
    res_max = np.abs(vals).max()
    frac_2s = (np.abs(vals) > 2 * res_std).mean()
    frac_3s = (np.abs(vals) > 3 * res_std).mean()

    # Eigenvalues
    eigs = np.sort(np.linalg.eigvalsh(residual))[::-1]
    pos_eigs = eigs[eigs > 0]
    pos_sum = pos_eigs.sum() if len(pos_eigs) > 0 else 1
    top_frac = pos_eigs[0] / pos_sum if len(pos_eigs) > 0 else 0
    pr = pos_sum**2 / (pos_eigs**2).sum() if len(pos_eigs) > 0 and (pos_eigs**2).sum() > 0 else 0

    # Spatial decay
    d_r, c_r = bin_correlations_by_distance(np.abs(residual), dist_matrix)
    pl_a, pl_b, pl_r2 = fit_power_law(d_r, c_r)
    ex_a, ex_b, ex_r2 = fit_exponential(d_r, c_r)

    # Boundary/bulk
    boundary, bulk = classify_boundary_bulk(coords, n_det)
    bb_ratio = None
    if len(boundary) > 2 and len(bulk) > 2:
        bp = [residual[boundary[i], boundary[j]] for i in range(len(boundary)) for j in range(i+1, len(boundary))]
        blp = [residual[bulk[i], bulk[j]] for i in range(len(bulk)) for j in range(i+1, len(bulk))]
        if bp and blp:
            bb_ratio = np.abs(np.array(bp)).mean() / max(np.abs(np.array(blp)).mean(), 1e-10)

    sig = {
        'res_mean': res_mean, 'res_std': res_std, 'res_max': res_max,
        'frac_2s': frac_2s, 'frac_3s': frac_3s,
        'top_eig_frac': top_frac, 'participation_ratio': pr,
        'n_pos_eigs': len(pos_eigs),
        'pl_exponent': pl_b, 'pl_r2': pl_r2,
        'exp_r2': ex_r2,
        'spatial_winner': 'power_law' if pl_r2 > ex_r2 else 'exponential',
        'bb_ratio': bb_ratio
    }
    return sig

# ============================================================
# NOISE MODELS
# ============================================================

def model_a_spatial_correlated(sim_data, dist_matrix, coords, n_det,
                                p_flip=0.04, correlation_range=3.0, power=-1.0):
    """
    Model A: Spatially correlated bit flips.
    Each shot: pick random seed detectors, flip them AND nearby detectors
    with probability decaying as distance^power.
    """
    n_shots = sim_data.shape[0]
    result = sim_data.copy()

    # Build spatial coupling matrix
    # For each detector, probability of correlated flip with each other
    coupling = np.zeros((n_det, n_det))
    for i in range(n_det):
        for j in range(n_det):
            if i != j and dist_matrix[i, j] > 0:
                coupling[i, j] = min(1.0, (dist_matrix[i, j] / correlation_range) ** power)
            elif i == j:
                coupling[i, j] = 1.0

    # Normalize rows to get conditional probabilities
    row_sums = coupling.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    coupling = coupling / row_sums

    # For each shot, choose seed detectors and propagate flips
    rng = np.random.default_rng(42)
    for shot in range(n_shots):
        # Each detector has p_flip chance of being a seed
        seeds = rng.random(n_det) < p_flip
        if not seeds.any():
            continue
        seed_idx = np.where(seeds)[0]
        for s in seed_idx:
            # Flip correlated detectors
            flip_probs = coupling[s] * 0.5  # scale down propagation
            flips = rng.random(n_det) < flip_probs
            result[shot] = np.abs(result[shot] - flips.astype(np.float32))

    return result

def model_a_fast(sim_data, dist_matrix, coords, n_det, p_extra=0.04, decay_exp=-1.0):
    """
    Model A (fast): Add spatially correlated noise.
    Uses vectorized approach: for each pair of detectors, add correlated flips
    with probability proportional to distance^decay_exp.
    """
    n_shots = sim_data.shape[0]
    result = sim_data.copy()
    rng = np.random.default_rng(42)

    # Add independent extra flips first (base rate mismatch)
    base_flips = rng.random((n_shots, n_det)) < p_extra
    result = np.abs(result - base_flips.astype(np.float32))

    # Add spatially correlated flips: for nearby detector pairs, add correlated errors
    # Build neighbor list (only pairs within distance 4)
    pairs = []
    for i in range(n_det):
        for j in range(i+1, min(i+100, n_det)):  # local neighborhood
            d = dist_matrix[i, j]
            if 0 < d < 6:
                p_corr = 0.005 * (d ** decay_exp)  # correlated flip probability
                p_corr = min(p_corr, 0.05)
                pairs.append((i, j, p_corr))

    print(f"    Model A: {len(pairs)} correlated pairs, p_extra={p_extra}")

    # Apply correlated flips
    for i, j, p_corr in pairs:
        corr_flips = rng.random(n_shots) < p_corr
        result[:, i] = np.abs(result[:, i] - corr_flips.astype(np.float32))
        result[:, j] = np.abs(result[:, j] - corr_flips.astype(np.float32))

    return result

def model_b_tls(sim_data, stim_path, coords, n_det, n_blocks=100, rate_spread=0.3):
    """
    Model B: TLS fluctuators.
    Divide shots into blocks. For each block, scale the effective error rate
    by a factor drawn from a log-normal distribution.
    This creates non-Markovian temporal correlations.
    """
    n_shots = sim_data.shape[0]
    block_size = n_shots // n_blocks
    rng = np.random.default_rng(123)

    # Generate block-varying error rate multipliers (log-normal → 1/f-like)
    log_multipliers = rng.normal(0, rate_spread, n_blocks)
    multipliers = np.exp(log_multipliers)

    print(f"    Model B: {n_blocks} blocks of {block_size} shots, "
          f"rate multipliers: {multipliers.min():.3f} to {multipliers.max():.3f}")

    # For each block, resample from the circuit with modified noise strength
    # Since we can't easily modify Stim circuit noise parameters,
    # we approximate by: for blocks with high multiplier, add extra flips;
    # for blocks with low multiplier, suppress some flips
    result = sim_data.copy()

    base_rate = sim_data.mean()  # ~0.034

    for b in range(n_blocks):
        start = b * block_size
        end = min(start + block_size, n_shots)
        target_rate = base_rate * multipliers[b]
        current_rate = result[start:end].mean()

        if target_rate > current_rate:
            # Add extra flips
            extra_p = (target_rate - current_rate)
            extra_flips = rng.random((end - start, n_det)) < extra_p
            result[start:end] = np.abs(result[start:end] - extra_flips.astype(np.float32))
        else:
            # Suppress some flips (set some 1s back to 0)
            suppress_p = (current_rate - target_rate) / max(current_rate, 0.001)
            suppress = rng.random((end - start, n_det)) < suppress_p
            result[start:end] = result[start:end] * (1 - suppress * result[start:end])

    actual_block_rates = [result[b*block_size:min((b+1)*block_size, n_shots)].mean()
                         for b in range(n_blocks)]
    print(f"    Block rate range: {min(actual_block_rates):.6f} to {max(actual_block_rates):.6f}")

    return result

def model_b_tls_temporal(sim_data, coords, n_det, memory_length=5, memory_strength=0.003):
    """
    Model B variant: Direct temporal memory injection.
    For each spatial position, add autocorrelated noise at specified lags.
    """
    result = sim_data.copy()
    rng = np.random.default_rng(456)

    # Group detectors by spatial position
    spatial_groups = {}
    for i in range(n_det):
        if i in coords and len(coords[i]) >= 3:
            key = (round(coords[i][0], 2), round(coords[i][1], 2))
            spatial_groups.setdefault(key, []).append((coords[i][2], i))
    for key in spatial_groups:
        spatial_groups[key].sort()

    n_positions = len(spatial_groups)
    print(f"    Model B-temporal: {n_positions} spatial positions, "
          f"memory_length={memory_length}, strength={memory_strength}")

    n_shots = sim_data.shape[0]

    # For each spatial position, create temporal correlation:
    # if detector at time t fired, increase probability of detector at time t+lag firing
    for key, detectors in spatial_groups.items():
        for lag in range(1, memory_length + 1):
            strength = memory_strength / lag  # 1/lag decay
            for i in range(len(detectors) - lag):
                t_i, d_i = detectors[i]
                t_j, d_j = detectors[i + lag]
                # For each shot where d_i fired, flip d_j with probability `strength`
                fired = result[:, d_i] > 0.5
                extra = rng.random(n_shots) < strength
                flip_mask = fired & extra
                result[:, d_j] = np.abs(result[:, d_j] - flip_mask.astype(np.float32))

    return result

def model_c_combined(sim_data, dist_matrix, stim_path, coords, n_det):
    """
    Model C: Combined spatial correlations + TLS + temporal memory.
    The kitchen sink model.
    """
    print("    Model C: Applying spatial correlations...")
    data = model_a_fast(sim_data, dist_matrix, coords, n_det,
                        p_extra=0.04, decay_exp=-1.0)
    print("    Model C: Applying TLS block fluctuations...")
    data = model_b_tls(data, None, coords, n_det,
                       n_blocks=200, rate_spread=0.25)
    print("    Model C: Applying temporal memory...")
    data = model_b_tls_temporal(data, coords, n_det,
                                memory_length=5, memory_strength=0.004)
    return data

# ============================================================
# MAIN: Test on d7/r90 (strongest signal)
# ============================================================

def run_test(d_label, r_label, path):
    print("="*80)
    print(f"  NOISE MODEL TEST: {d_label}/{r_label}")
    print("="*80)

    # Load circuit
    noisy_stim = os.path.join(path, 'circuit_noisy_si1000.stim')
    ideal_stim = os.path.join(path, 'circuit_ideal.stim')
    circuit_path = ideal_stim if os.path.exists(ideal_stim) else noisy_stim
    circuit = stim.Circuit.from_file(circuit_path)
    coords, n_det = get_detector_coords(circuit)
    print(f"  Detectors: {n_det}")

    # Load real data
    print("  Loading real detection events...")
    bytes_per_shot = (n_det + 7) // 8
    raw = np.fromfile(os.path.join(path, 'detection_events.b8'), dtype=np.uint8)
    n_shots = len(raw) // bytes_per_shot
    raw = raw[:n_shots * bytes_per_shot].reshape(n_shots, bytes_per_shot)
    real_data = np.unpackbits(raw, axis=1, bitorder='little')[:, :n_det].astype(np.float32)
    print(f"  {n_shots:,} shots loaded")

    # Generate SI1000 baseline
    print("  Generating SI1000 baseline...")
    noisy_circuit = stim.Circuit.from_file(noisy_stim)
    sampler = noisy_circuit.compile_detector_sampler()
    batch_size = min(n_shots, 50000)
    sim_chunks = []
    remaining = n_shots
    while remaining > 0:
        b = min(batch_size, remaining)
        sim_chunks.append(sampler.sample(b).astype(np.float32))
        remaining -= b
    sim_data = np.vstack(sim_chunks)
    n_det = min(n_det, sim_data.shape[1])
    real_data = real_data[:, :n_det]
    sim_data = sim_data[:, :n_det]

    # Distance matrix
    dist_matrix, positions = compute_distance_matrix(coords, n_det)

    # ---- REAL RESIDUAL ----
    print("\n  === REAL RESIDUAL ===")
    real_corr = compute_correlation_matrix(real_data)
    sim_corr = compute_correlation_matrix(sim_data)
    real_residual = real_corr - sim_corr
    real_sig = compute_residual_signatures(real_residual, coords, n_det, dist_matrix, "REAL")
    real_temporal = compute_temporal_autocorrelation(real_data, coords, n_det)
    sim_temporal = compute_temporal_autocorrelation(sim_data, coords, n_det)
    real_temporal_excess = {}
    for lag in real_temporal:
        real_temporal_excess[lag] = real_temporal[lag]['mean'] - sim_temporal.get(lag, {'mean': 0})['mean']

    print_signatures("REAL", real_sig, real_temporal_excess)

    # ---- MODEL A: Spatial correlations ----
    print("\n  === MODEL A: Spatially Correlated Noise ===")
    t0 = time.time()
    model_a_data = model_a_fast(sim_data.copy(), dist_matrix, coords, n_det)
    print(f"    Generated in {time.time()-t0:.1f}s")
    model_a_corr = compute_correlation_matrix(model_a_data)
    model_a_residual = model_a_corr - sim_corr
    model_a_sig = compute_residual_signatures(model_a_residual, coords, n_det, dist_matrix, "A")
    model_a_temporal = compute_temporal_autocorrelation(model_a_data, coords, n_det)
    model_a_excess = {}
    for lag in model_a_temporal:
        model_a_excess[lag] = model_a_temporal[lag]['mean'] - sim_temporal.get(lag, {'mean': 0})['mean']
    print_signatures("MODEL A", model_a_sig, model_a_excess)

    # ---- MODEL B: TLS + temporal memory ----
    print("\n  === MODEL B: TLS Fluctuators + Temporal Memory ===")
    t0 = time.time()
    # Apply both TLS block variation and direct temporal coupling
    model_b_data = model_b_tls(sim_data.copy(), noisy_stim, coords, n_det,
                                n_blocks=200, rate_spread=0.3)
    model_b_data = model_b_tls_temporal(model_b_data, coords, n_det,
                                         memory_length=5, memory_strength=0.004)
    print(f"    Generated in {time.time()-t0:.1f}s")
    model_b_corr = compute_correlation_matrix(model_b_data)
    model_b_residual = model_b_corr - sim_corr
    model_b_sig = compute_residual_signatures(model_b_residual, coords, n_det, dist_matrix, "B")
    model_b_temporal = compute_temporal_autocorrelation(model_b_data, coords, n_det)
    model_b_excess = {}
    for lag in model_b_temporal:
        model_b_excess[lag] = model_b_temporal[lag]['mean'] - sim_temporal.get(lag, {'mean': 0})['mean']
    print_signatures("MODEL B", model_b_sig, model_b_excess)

    # ---- MODEL C: Kitchen sink ----
    print("\n  === MODEL C: Combined (Spatial + TLS + Temporal) ===")
    t0 = time.time()
    model_c_data = model_c_combined(sim_data.copy(), dist_matrix, noisy_stim, coords, n_det)
    print(f"    Generated in {time.time()-t0:.1f}s")
    model_c_corr = compute_correlation_matrix(model_c_data)
    model_c_residual = model_c_corr - sim_corr
    model_c_sig = compute_residual_signatures(model_c_residual, coords, n_det, dist_matrix, "C")
    model_c_temporal = compute_temporal_autocorrelation(model_c_data, coords, n_det)
    model_c_excess = {}
    for lag in model_c_temporal:
        model_c_excess[lag] = model_c_temporal[lag]['mean'] - sim_temporal.get(lag, {'mean': 0})['mean']
    print_signatures("MODEL C", model_c_sig, model_c_excess)

    # ---- COMPARISON TABLE ----
    print("\n" + "="*80)
    print("  COMPARISON TABLE")
    print("="*80)

    all_sigs = [("REAL", real_sig, real_temporal_excess),
                ("Model A", model_a_sig, model_a_excess),
                ("Model B", model_b_sig, model_b_excess),
                ("Model C", model_c_sig, model_c_excess)]

    header = f"{'':>12} {'Res std':>10} {'Max|R|':>10} {'>2s frac':>10} {'Top eig%':>10} {'PR':>8} {'PL exp':>10} {'PL R2':>8} {'Exp R2':>8} {'Spatial':>10} {'B/B':>8}"
    print(header)
    print("-" * len(header))

    for name, sig, tex in all_sigs:
        pl_exp = f"{sig['pl_exponent']:.4f}" if sig['pl_exponent'] is not None else "N/A"
        bb = f"{sig['bb_ratio']:.4f}" if sig['bb_ratio'] is not None else "N/A"
        print(f"{name:>12} {sig['res_std']:>10.7f} {sig['res_max']:>10.6f} "
              f"{sig['frac_2s']:>10.6f} {sig['top_eig_frac']:>10.6f} "
              f"{sig['participation_ratio']:>8.1f} {pl_exp:>10} "
              f"{sig['pl_r2']:>8.4f} {sig['exp_r2']:>8.4f} "
              f"{sig['spatial_winner']:>10} {bb:>8}")

    # Temporal comparison
    print(f"\n{'':>12} {'Lag1 exc':>12} {'Lag2 exc':>12} {'Lag3 exc':>12} {'Lag4 exc':>12} {'Lag5 exc':>12}")
    print("-" * 75)
    for name, sig, tex in all_sigs:
        vals = [f"{tex.get(lag, 0):>12.8f}" for lag in range(1, 6)]
        print(f"{name:>12} {' '.join(vals)}")

    # ---- SCORING ----
    print("\n" + "="*80)
    print("  SIGNATURE MATCH SCORING")
    print("="*80)

    for name, sig, tex in all_sigs[1:]:  # skip REAL
        score = 0
        total = 4
        details = []

        # 1. Power law spatial decay
        if sig['spatial_winner'] == real_sig['spatial_winner']:
            # Check if exponent is in same ballpark
            if (sig['pl_exponent'] is not None and real_sig['pl_exponent'] is not None):
                exp_ratio = sig['pl_exponent'] / real_sig['pl_exponent'] if real_sig['pl_exponent'] != 0 else 0
                if 0.3 < exp_ratio < 3.0:
                    score += 1
                    details.append(f"Spatial: MATCH (PL exp {sig['pl_exponent']:.4f} vs {real_sig['pl_exponent']:.4f})")
                else:
                    details.append(f"Spatial: WRONG EXPONENT ({sig['pl_exponent']:.4f} vs {real_sig['pl_exponent']:.4f})")
            else:
                details.append("Spatial: cannot compare exponents")
        else:
            details.append(f"Spatial: WRONG TYPE ({sig['spatial_winner']} vs {real_sig['spatial_winner']})")

        # 2. Temporal memory
        real_lag2 = real_temporal_excess.get(2, 0)
        model_lag2 = tex.get(2, 0)
        if real_lag2 > 0 and model_lag2 > 0:
            ratio = model_lag2 / real_lag2
            if 0.3 < ratio < 3.0:
                score += 1
                details.append(f"Temporal lag2: MATCH ({model_lag2:.6f} vs {real_lag2:.6f}, ratio={ratio:.2f})")
            else:
                details.append(f"Temporal lag2: WRONG MAGNITUDE ({model_lag2:.6f} vs {real_lag2:.6f}, ratio={ratio:.2f})")
        elif real_lag2 > 0 and model_lag2 <= 0:
            details.append(f"Temporal lag2: MODEL HAS NO MEMORY ({model_lag2:.8f})")
        else:
            details.append("Temporal lag2: neither has significant memory")

        # 3. Eigenvalue structure
        real_pr_frac = real_sig['participation_ratio'] / real_sig['n_pos_eigs'] if real_sig['n_pos_eigs'] > 0 else 0
        model_pr_frac = sig['participation_ratio'] / sig['n_pos_eigs'] if sig['n_pos_eigs'] > 0 else 0
        pr_ratio = model_pr_frac / real_pr_frac if real_pr_frac > 0 else 0
        if 0.5 < pr_ratio < 2.0:
            score += 1
            details.append(f"Eigenstructure: MATCH (PR frac {model_pr_frac:.4f} vs {real_pr_frac:.4f})")
        else:
            details.append(f"Eigenstructure: MISMATCH (PR frac {model_pr_frac:.4f} vs {real_pr_frac:.4f})")

        # 4. Boundary/bulk
        if sig['bb_ratio'] is not None and real_sig['bb_ratio'] is not None:
            # Both should show same direction (both > 1 or both < 1)
            if (sig['bb_ratio'] < 1) == (real_sig['bb_ratio'] < 1):
                if abs(sig['bb_ratio'] - real_sig['bb_ratio']) < 0.3:
                    score += 1
                    details.append(f"Boundary/bulk: MATCH ({sig['bb_ratio']:.4f} vs {real_sig['bb_ratio']:.4f})")
                else:
                    details.append(f"Boundary/bulk: SAME DIRECTION but different magnitude ({sig['bb_ratio']:.4f} vs {real_sig['bb_ratio']:.4f})")
            else:
                details.append(f"Boundary/bulk: WRONG DIRECTION ({sig['bb_ratio']:.4f} vs {real_sig['bb_ratio']:.4f})")
        else:
            details.append("Boundary/bulk: cannot compare")

        print(f"\n  {name}: {score}/{total} signatures matched")
        for d in details:
            print(f"    {d}")

    # ---- FINAL VERDICT ----
    print("\n" + "="*80)
    print("  FINAL VERDICT")
    print("="*80)

    # Check if ANY model got 4/4
    best_score = 0
    best_model = None
    for name, sig, tex in all_sigs[1:]:
        s = 0
        # Recompute score
        if sig['spatial_winner'] == real_sig['spatial_winner']:
            if sig['pl_exponent'] is not None and real_sig['pl_exponent'] is not None:
                r = sig['pl_exponent'] / real_sig['pl_exponent'] if real_sig['pl_exponent'] != 0 else 0
                if 0.3 < r < 3.0: s += 1
        real_l2 = real_temporal_excess.get(2, 0)
        model_l2 = tex.get(2, 0)
        if real_l2 > 0 and model_l2 > 0 and 0.3 < model_l2/real_l2 < 3.0: s += 1
        rpf = real_sig['participation_ratio'] / real_sig['n_pos_eigs'] if real_sig['n_pos_eigs'] > 0 else 0
        mpf = sig['participation_ratio'] / sig['n_pos_eigs'] if sig['n_pos_eigs'] > 0 else 0
        if rpf > 0 and 0.5 < mpf/rpf < 2.0: s += 1
        if sig['bb_ratio'] is not None and real_sig['bb_ratio'] is not None:
            if (sig['bb_ratio'] < 1) == (real_sig['bb_ratio'] < 1):
                if abs(sig['bb_ratio'] - real_sig['bb_ratio']) < 0.3: s += 1
        if s > best_score:
            best_score = s
            best_model = name

    if best_score >= 4:
        print(f"  {best_model} reproduces ALL 4 signatures.")
        print(f"  CONCLUSION: The residual is CLASSICALLY EXPLAINABLE.")
        print(f"  The Willow data is consistent with {best_model} noise on top of SI1000.")
    elif best_score >= 3:
        print(f"  {best_model} reproduces {best_score}/4 signatures.")
        print(f"  CONCLUSION: MOSTLY classically explainable. One signature remains anomalous.")
    elif best_score >= 2:
        print(f"  Best model ({best_model}) only reproduces {best_score}/4 signatures.")
        print(f"  CONCLUSION: PARTIALLY explainable. The residual has structure that")
        print(f"  simple classical noise models struggle to reproduce simultaneously.")
    else:
        print(f"  Best model ({best_model}) only reproduces {best_score}/4 signatures.")
        print(f"  CONCLUSION: NO classical noise model reproduces the residual structure.")
        print(f"  The combination of power-law flattening + non-Markovian memory +")
        print(f"  diffuse eigenstructure may require a fundamentally different explanation.")

    print("="*80)

def print_signatures(label, sig, temporal_excess):
    print(f"\n  [{label}] Residual: mean={sig['res_mean']:.8f}, std={sig['res_std']:.8f}, max|R|={sig['res_max']:.6f}")
    print(f"  [{label}] >2sigma: {sig['frac_2s']:.6f}, >3sigma: {sig['frac_3s']:.6f}")
    print(f"  [{label}] Top eig frac: {sig['top_eig_frac']:.6f}, PR: {sig['participation_ratio']:.1f}/{sig['n_pos_eigs']}")
    pl = f"{sig['pl_exponent']:.4f}" if sig['pl_exponent'] is not None else "N/A"
    print(f"  [{label}] Spatial: PL exp={pl}, PL R2={sig['pl_r2']:.4f}, Exp R2={sig['exp_r2']:.4f} -> {sig['spatial_winner']}")
    bb = f"{sig['bb_ratio']:.4f}" if sig['bb_ratio'] is not None else "N/A"
    print(f"  [{label}] Boundary/Bulk ratio: {bb}")
    for lag in sorted(temporal_excess.keys()):
        print(f"  [{label}] Temporal lag {lag}: excess={temporal_excess[lag]:.8f}")

if __name__ == '__main__':
    # Primary test: d7/r90 (strongest signal)
    path_d7r90 = f'{BASE}/d7_at_q6_7/Z/r90'
    if os.path.exists(path_d7r90):
        run_test('d7', 'r90', path_d7r90)
    else:
        print(f"Path not found: {path_d7r90}")

    # Secondary test: d5/r50 (different code distance)
    path_d5r50 = f'{BASE}/d5_at_q4_7/Z/r50'
    if os.path.exists(path_d5r50):
        print("\n\n")
        run_test('d5', 'r50', path_d5r50)
