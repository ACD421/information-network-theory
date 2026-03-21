"""
Quantum Error Correction Syndrome Analysis on Google Willow Data
Analyzes residual correlations between real hardware data and SI1000 noise model.
"""
import os, json, sys
import numpy as np
from scipy import optimize, stats
import stim
import warnings
warnings.filterwarnings('ignore')

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:\Users\andre\Claudius\google_105Q_surface_code_d3_d5_d7'

EXPERIMENTS = [
    ('d3', 'r50', f'{BASE}/d3_at_q6_7/Z/r50'),
    ('d5', 'r50', f'{BASE}/d5_at_q4_7/Z/r50'),
    ('d5', 'r90', f'{BASE}/d5_at_q4_7/Z/r90'),
    ('d7', 'r50', f'{BASE}/d7_at_q6_7/Z/r50'),
    ('d7', 'r90', f'{BASE}/d7_at_q6_7/Z/r90'),
    ('d7', 'r130', f'{BASE}/d7_at_q6_7/Z/r130'),
]

def load_detection_events(path, n_det):
    """Load .b8 detection events file."""
    bytes_per_shot = (n_det + 7) // 8
    raw = np.fromfile(os.path.join(path, 'detection_events.b8'), dtype=np.uint8)
    n_shots = len(raw) // bytes_per_shot
    print(f"  Loaded {n_shots:,} shots, {n_det} detectors, {bytes_per_shot} bytes/shot")
    raw = raw[:n_shots * bytes_per_shot].reshape(n_shots, bytes_per_shot)
    # Unpack bits
    bits = np.unpackbits(raw, axis=1, bitorder='little')[:, :n_det]
    return bits.astype(np.float32), n_shots

def get_detector_coords(circuit):
    """Extract detector coordinates from a stim circuit."""
    coords = {}
    det_idx = 0
    for instruction in circuit.flattened():
        if instruction.name == 'DETECTOR':
            c = list(instruction.gate_args_copy())
            coords[det_idx] = c
            det_idx += 1
    return coords, det_idx

def compute_correlation_matrix(data, max_det=None):
    """Compute Pearson correlation matrix efficiently."""
    if max_det and data.shape[1] > max_det:
        data = data[:, :max_det]
    n = data.shape[1]
    # Center
    means = data.mean(axis=0)
    centered = data - means
    stds = centered.std(axis=0)
    stds[stds == 0] = 1.0  # avoid division by zero
    normalized = centered / stds
    corr = (normalized.T @ normalized) / data.shape[0]
    np.fill_diagonal(corr, 1.0)
    return corr

def simulate_baseline(stim_path, n_shots):
    """Generate simulated detection events from noisy circuit."""
    circuit = stim.Circuit.from_file(stim_path)
    sampler = circuit.compile_detector_sampler()
    # Sample in batches to manage memory
    batch_size = min(n_shots, 50000)
    all_samples = []
    remaining = n_shots
    while remaining > 0:
        batch = min(batch_size, remaining)
        samples = sampler.sample(batch)
        all_samples.append(samples.astype(np.float32))
        remaining -= batch
    return np.vstack(all_samples)

def compute_distance_matrix(coords, n_det):
    """Compute pairwise distances from detector coordinates (first 2 dims = spatial)."""
    pos = np.zeros((n_det, 2))
    for i in range(n_det):
        if i in coords and len(coords[i]) >= 2:
            pos[i, 0] = coords[i][0]
            pos[i, 1] = coords[i][1]
    # Pairwise distances
    diff = pos[:, np.newaxis, :] - pos[np.newaxis, :, :]
    dist = np.sqrt((diff**2).sum(axis=-1))
    return dist, pos

def bin_correlations_by_distance(corr_matrix, dist_matrix, n_bins=20):
    """Bin mean |correlation| by spatial distance."""
    n = corr_matrix.shape[0]
    # Upper triangle only
    triu_idx = np.triu_indices(n, k=1)
    dists = dist_matrix[triu_idx]
    corrs = np.abs(corr_matrix[triu_idx])

    # Filter out zero distances
    mask = dists > 0.01
    dists = dists[mask]
    corrs = corrs[mask]

    if len(dists) == 0:
        return np.array([]), np.array([])

    # Log-spaced bins
    d_min, d_max = dists.min(), dists.max()
    if d_min <= 0:
        d_min = 0.1
    bins = np.logspace(np.log10(d_min), np.log10(d_max), n_bins + 1)

    bin_centers = []
    bin_means = []
    for i in range(n_bins):
        mask_bin = (dists >= bins[i]) & (dists < bins[i+1])
        if mask_bin.sum() > 0:
            bin_centers.append(np.sqrt(bins[i] * bins[i+1]))
            bin_means.append(corrs[mask_bin].mean())

    return np.array(bin_centers), np.array(bin_means)

def fit_power_law(x, y):
    """Fit y = a * x^b, return (a, b, r_squared)."""
    mask = (x > 0) & (y > 0)
    if mask.sum() < 3:
        return None, None, 0
    lx, ly = np.log(x[mask]), np.log(y[mask])
    try:
        slope, intercept, r, p, se = stats.linregress(lx, ly)
        return np.exp(intercept), slope, r**2
    except:
        return None, None, 0

def fit_exponential(x, y):
    """Fit y = a * exp(-b * x), return (a, b, r_squared)."""
    mask = (x > 0) & (y > 0)
    if mask.sum() < 3:
        return None, None, 0
    try:
        def exp_func(x, a, b):
            return a * np.exp(-b * x)
        popt, pcov = optimize.curve_fit(exp_func, x[mask], y[mask],
                                         p0=[y[mask].max(), 1.0], maxfev=5000)
        y_pred = exp_func(x[mask], *popt)
        ss_res = ((y[mask] - y_pred)**2).sum()
        ss_tot = ((y[mask] - y[mask].mean())**2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        return popt[0], popt[1], r2
    except:
        return None, None, 0

def compute_temporal_autocorrelation(data, coords, n_det, max_lag=5):
    """Compute temporal autocorrelation by grouping detectors by spatial position."""
    # Group detectors by spatial coords (first 2 dims), the 3rd dim is time
    spatial_groups = {}
    for i in range(n_det):
        if i in coords and len(coords[i]) >= 3:
            key = (round(coords[i][0], 2), round(coords[i][1], 2))
            t = coords[i][2]
            if key not in spatial_groups:
                spatial_groups[key] = []
            spatial_groups[key].append((t, i))

    # Sort each group by time
    for key in spatial_groups:
        spatial_groups[key].sort()

    # Compute lag correlations
    lag_corrs = {lag: [] for lag in range(1, max_lag + 1)}
    for key, detectors in spatial_groups.items():
        if len(detectors) < 2:
            continue
        for i in range(len(detectors)):
            for j in range(i + 1, len(detectors)):
                t_i, d_i = detectors[i]
                t_j, d_j = detectors[j]
                lag = int(round(t_j - t_i))
                if 1 <= lag <= max_lag:
                    # Pearson correlation between these two detector columns
                    a = data[:, d_i]
                    b = data[:, d_j]
                    # Quick correlation
                    a_c = a - a.mean()
                    b_c = b - b.mean()
                    denom = np.sqrt((a_c**2).sum() * (b_c**2).sum())
                    if denom > 0:
                        c = (a_c * b_c).sum() / denom
                        lag_corrs[lag].append(c)

    result = {}
    for lag in range(1, max_lag + 1):
        if lag_corrs[lag]:
            result[lag] = {
                'mean': np.mean(lag_corrs[lag]),
                'std': np.std(lag_corrs[lag]),
                'count': len(lag_corrs[lag])
            }
    return result

def classify_boundary_bulk(coords, n_det):
    """Classify detectors as boundary or bulk based on distance from center."""
    pos = np.zeros((n_det, 2))
    valid = []
    for i in range(n_det):
        if i in coords and len(coords[i]) >= 2:
            pos[i, 0] = coords[i][0]
            pos[i, 1] = coords[i][1]
            valid.append(i)

    if len(valid) < 5:
        return [], []

    center = pos[valid].mean(axis=0)
    dists_from_center = np.sqrt(((pos[valid] - center)**2).sum(axis=1))
    max_dist = dists_from_center.max()

    boundary = [valid[i] for i, d in enumerate(dists_from_center) if d >= 0.7 * max_dist]
    bulk = [valid[i] for i, d in enumerate(dists_from_center) if d <= 0.5 * max_dist]

    return boundary, bulk

def analyze_experiment(d, r, path):
    """Run full analysis on one experiment."""
    print(f"\n{'='*70}")
    print(f"  EXPERIMENT: {d}/{r}")
    print(f"{'='*70}")

    # Load metadata
    meta_path = os.path.join(path, 'metadata.json')
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        print(f"  Metadata: {json.dumps(meta, indent=2)[:300]}")

    # Load circuit to get detector count and coordinates
    noisy_stim = os.path.join(path, 'circuit_noisy_si1000.stim')
    ideal_stim = os.path.join(path, 'circuit_ideal.stim')

    circuit_path = ideal_stim if os.path.exists(ideal_stim) else noisy_stim
    circuit = stim.Circuit.from_file(circuit_path)
    coords, n_det = get_detector_coords(circuit)
    print(f"  Detectors: {n_det}, Coords available: {len(coords)}")

    # Load real detection events
    print("  Loading real detection events...")
    real_data, n_shots = load_detection_events(path, n_det)

    # Compute real firing rates
    real_rates = real_data.mean(axis=0)
    print(f"  Real firing rates: mean={real_rates.mean():.6f}, std={real_rates.std():.6f}, "
          f"min={real_rates.min():.6f}, max={real_rates.max():.6f}")

    # Simulate baseline
    print(f"  Simulating {n_shots:,} shots from SI1000 model...")
    noisy_circuit = stim.Circuit.from_file(noisy_stim)
    sim_data = simulate_baseline(noisy_stim, n_shots)
    n_det_sim = sim_data.shape[1]
    print(f"  Simulated detectors: {n_det_sim}")

    # Ensure same number of detectors
    n_use = min(n_det, n_det_sim)
    if n_use < n_det:
        print(f"  WARNING: Trimming to {n_use} detectors")
        real_data = real_data[:, :n_use]
        sim_data = sim_data[:, :n_use]

    # Simulated firing rates
    sim_rates = sim_data.mean(axis=0)
    print(f"  Sim firing rates: mean={sim_rates.mean():.6f}, std={sim_rates.std():.6f}, "
          f"min={sim_rates.min():.6f}, max={sim_rates.max():.6f}")

    rate_diff = real_rates[:n_use] - sim_rates[:n_use]
    print(f"  Rate difference (real-sim): mean={rate_diff.mean():.6f}, "
          f"std={rate_diff.std():.6f}, max|diff|={np.abs(rate_diff).max():.6f}")

    # Correlation matrices
    print("  Computing correlation matrices...")
    real_corr = compute_correlation_matrix(real_data)
    sim_corr = compute_correlation_matrix(sim_data)

    # Residual
    residual = real_corr - sim_corr
    np.fill_diagonal(residual, 0)  # zero out diagonal

    # Upper triangle stats
    triu_idx = np.triu_indices(n_use, k=1)
    res_vals = residual[triu_idx]

    res_mean = res_vals.mean()
    res_std = res_vals.std()
    res_max = np.abs(res_vals).max()

    # Significance thresholds
    frac_2sigma = (np.abs(res_vals) > 2 * res_std).mean()
    frac_3sigma = (np.abs(res_vals) > 3 * res_std).mean()

    print(f"\n  --- RESIDUAL STATISTICS ---")
    print(f"  Mean residual:     {res_mean:.8f}")
    print(f"  Std residual:      {res_std:.8f}")
    print(f"  Max |residual|:    {res_max:.8f}")
    print(f"  Fraction > 2σ:     {frac_2sigma:.6f}  (noise expectation: 0.0455)")
    print(f"  Fraction > 3σ:     {frac_3sigma:.6f}  (noise expectation: 0.0027)")

    # Eigenvalue analysis
    print("\n  --- EIGENVALUE ANALYSIS ---")
    eigenvalues = np.linalg.eigvalsh(residual)
    eigenvalues = np.sort(eigenvalues)[::-1]  # descending

    pos_eigs = eigenvalues[eigenvalues > 0]
    pos_sum = pos_eigs.sum() if len(pos_eigs) > 0 else 1

    print(f"  Top 5 eigenvalues: {eigenvalues[:5]}")
    if len(pos_eigs) > 0:
        top_frac = pos_eigs[0] / pos_sum
        print(f"  Top eigenvalue fraction: {top_frac:.6f} (structured if > 0.15)")

        # Participation ratio
        pr = pos_sum**2 / (pos_eigs**2).sum() if (pos_eigs**2).sum() > 0 else 0
        print(f"  Participation ratio: {pr:.2f} / {len(pos_eigs)} "
              f"(low = concentrated, high = spread)")

    # Distance-binned correlations
    print("\n  --- SPATIAL DECAY ANALYSIS ---")
    dist_matrix, positions = compute_distance_matrix(coords, n_use)

    d_real, c_real = bin_correlations_by_distance(real_corr, dist_matrix)
    d_sim, c_sim = bin_correlations_by_distance(sim_corr, dist_matrix)
    d_res, c_res = bin_correlations_by_distance(np.abs(residual), dist_matrix)

    if len(d_res) >= 3:
        pl_a, pl_b, pl_r2 = fit_power_law(d_res, c_res)
        ex_a, ex_b, ex_r2 = fit_exponential(d_res, c_res)

        print(f"  Power law fit:       |r| ~ {pl_a:.6f} * d^{pl_b:.4f}  (R²={pl_r2:.4f})")
        print(f"  Exponential fit:     |r| ~ {ex_a:.6f} * exp(-{ex_b:.4f}*d)  (R²={ex_r2:.4f})")

        if pl_r2 > ex_r2:
            print(f"  >> POWER LAW WINS (R²={pl_r2:.4f} vs {ex_r2:.4f}) — STRUCTURED")
        else:
            print(f"  >> EXPONENTIAL WINS (R²={ex_r2:.4f} vs {pl_r2:.4f}) — NOISE-LIKE")

    # Temporal autocorrelation
    print("\n  --- TEMPORAL AUTOCORRELATION ---")
    real_temporal = compute_temporal_autocorrelation(real_data, coords, n_use)
    sim_temporal = compute_temporal_autocorrelation(sim_data, coords, n_use)

    if real_temporal:
        for lag in sorted(real_temporal.keys()):
            r_t = real_temporal[lag]
            s_t = sim_temporal.get(lag, {'mean': 0, 'std': 0, 'count': 0})
            excess = r_t['mean'] - s_t['mean']
            print(f"  Lag {lag}: real={r_t['mean']:.8f} sim={s_t['mean']:.8f} "
                  f"excess={excess:.8f} (n={r_t['count']})")
            if lag >= 2 and excess > 2 * r_t['std'] / np.sqrt(r_t['count']):
                print(f"    >> NON-MARKOVIAN MEMORY DETECTED at lag {lag}")
    else:
        print("  No temporal structure found in detector coordinates")

    # Boundary vs Bulk
    print("\n  --- BOUNDARY vs BULK ---")
    boundary, bulk = classify_boundary_bulk(coords, n_use)
    print(f"  Boundary detectors: {len(boundary)}, Bulk detectors: {len(bulk)}")

    if len(boundary) > 2 and len(bulk) > 2:
        # Get residual stats for each group
        boundary_pairs = []
        bulk_pairs = []
        for i in range(len(boundary)):
            for j in range(i+1, len(boundary)):
                boundary_pairs.append(residual[boundary[i], boundary[j]])
        for i in range(len(bulk)):
            for j in range(i+1, len(bulk)):
                bulk_pairs.append(residual[bulk[i], bulk[j]])

        if boundary_pairs and bulk_pairs:
            bp = np.array(boundary_pairs)
            blp = np.array(bulk_pairs)
            print(f"  Boundary: mean|r|={np.abs(bp).mean():.8f}, std={bp.std():.8f}")
            print(f"  Bulk:     mean|r|={np.abs(blp).mean():.8f}, std={blp.std():.8f}")
            ratio = np.abs(bp).mean() / np.abs(blp).mean() if np.abs(blp).mean() > 0 else float('inf')
            print(f"  Boundary/Bulk ratio: {ratio:.4f}")
            if ratio > 1.3:
                print(f"    >> BOUNDARY ENHANCEMENT DETECTED (ratio={ratio:.4f})")

    # Return summary dict
    result = {
        'd': d, 'r': r, 'n_det': n_use, 'n_shots': n_shots,
        'real_rate_mean': float(real_rates.mean()),
        'sim_rate_mean': float(sim_rates.mean()),
        'rate_diff_mean': float(rate_diff.mean()),
        'rate_diff_max': float(np.abs(rate_diff).max()),
        'res_mean': float(res_mean),
        'res_std': float(res_std),
        'res_max': float(res_max),
        'frac_2sigma': float(frac_2sigma),
        'frac_3sigma': float(frac_3sigma),
        'top_eigenvalue': float(eigenvalues[0]) if len(eigenvalues) > 0 else 0,
        'top_eig_frac': float(pos_eigs[0] / pos_sum) if len(pos_eigs) > 0 else 0,
        'participation_ratio': float(pr) if len(pos_eigs) > 0 else 0,
    }

    if len(d_res) >= 3:
        result['pl_exponent'] = float(pl_b) if pl_b is not None else None
        result['pl_r2'] = float(pl_r2)
        result['exp_r2'] = float(ex_r2)
        result['spatial_winner'] = 'power_law' if pl_r2 > ex_r2 else 'exponential'

    if len(boundary) > 2 and len(bulk) > 2 and boundary_pairs and bulk_pairs:
        result['boundary_bulk_ratio'] = float(ratio)

    return result

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    print("="*70)
    print("  GOOGLE WILLOW QUANTUM ERROR CORRECTION SYNDROME ANALYSIS")
    print("  Residual Correlation Structure: Real Hardware vs SI1000 Model")
    print("="*70)

    results = []
    for d, r, path in EXPERIMENTS:
        if os.path.exists(path):
            try:
                result = analyze_experiment(d, r, path)
                results.append(result)
            except Exception as e:
                print(f"\n  ERROR in {d}/{r}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"\n  SKIPPING {d}/{r}: path not found ({path})")

    # Summary table
    print("\n\n" + "="*70)
    print("  SUMMARY TABLE")
    print("="*70)

    header = f"{'Exp':>8} {'n_det':>6} {'shots':>8} {'Rate Δ':>8} {'Res σ':>10} {'Max|R|':>10} {'>2σ':>8} {'>3σ':>8} {'λ₁ frac':>8} {'PR':>6} {'PL exp':>8} {'Spatial':>10} {'B/B':>6}"
    print(header)
    print("-" * len(header))

    for r in results:
        exp = f"{r['d']}/{r['r']}"
        pl_exp = f"{r.get('pl_exponent', 'N/A'):.3f}" if r.get('pl_exponent') is not None else "N/A"
        spatial = r.get('spatial_winner', 'N/A')[:7]
        bb = f"{r.get('boundary_bulk_ratio', 0):.3f}" if r.get('boundary_bulk_ratio') else "N/A"

        print(f"{exp:>8} {r['n_det']:>6} {r['n_shots']:>8,} "
              f"{r['rate_diff_mean']:>8.5f} {r['res_std']:>10.7f} {r['res_max']:>10.7f} "
              f"{r['frac_2sigma']:>8.5f} {r['frac_3sigma']:>8.5f} "
              f"{r['top_eig_frac']:>8.5f} {r['participation_ratio']:>6.1f} "
              f"{pl_exp:>8} {spatial:>10} {bb:>6}")

    # Verdict
    print("\n" + "="*70)
    print("  VERDICT")
    print("="*70)

    structured_count = 0
    noise_count = 0
    for r in results:
        structured = 0
        if r['frac_2sigma'] > 0.06:
            structured += 1
        if r['top_eig_frac'] > 0.15:
            structured += 1
        if r.get('spatial_winner') == 'power_law':
            structured += 1
        if structured >= 2:
            structured_count += 1
            print(f"  {r['d']}/{r['r']}: STRUCTURED ({structured}/3 indicators)")
        else:
            noise_count += 1
            print(f"  {r['d']}/{r['r']}: NOISE-LIKE ({structured}/3 indicators)")

    # Scaling check
    if len(results) >= 3:
        d_values = []
        frac_values = []
        for r in results:
            d_val = int(r['d'][1:])
            d_values.append(d_val)
            frac_values.append(r['frac_2sigma'])

        # Check if structure scales with code distance
        d3_fracs = [r['frac_2sigma'] for r in results if r['d'] == 'd3']
        d5_fracs = [r['frac_2sigma'] for r in results if r['d'] == 'd5']
        d7_fracs = [r['frac_2sigma'] for r in results if r['d'] == 'd7']

        print(f"\n  Scaling with code distance:")
        if d3_fracs: print(f"    d3: mean(>2σ) = {np.mean(d3_fracs):.5f}")
        if d5_fracs: print(f"    d5: mean(>2σ) = {np.mean(d5_fracs):.5f}")
        if d7_fracs: print(f"    d7: mean(>2σ) = {np.mean(d7_fracs):.5f}")

        if d7_fracs and d3_fracs and np.mean(d7_fracs) > np.mean(d3_fracs) * 1.3:
            print("    >> STRUCTURE SCALES WITH CODE DISTANCE")

    print(f"\n  Overall: {structured_count} structured, {noise_count} noise-like")
    print("="*70)
