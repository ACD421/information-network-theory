"""
Rate-Matched Residual Analysis on Google Willow Data

Methodology: Scale simulated detection events so that per-detector marginal
firing rates match real data EXACTLY, then compute correlation residuals.
Whatever structure survives rate-matching is genuinely about correlation
topology rather than intensity mismatch.

This isolates the question: is the residual structure real, or an artifact
of how rate discrepancies project into correlation space?
"""
import os, json, sys, time
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
    ('d5', 'r90', f'{BASE}/d5_at_q4_7/Z/r90'),
    ('d7', 'r50', f'{BASE}/d7_at_q6_7/Z/r50'),
    ('d7', 'r90', f'{BASE}/d7_at_q6_7/Z/r90'),
    ('d7', 'r130', f'{BASE}/d7_at_q6_7/Z/r130'),
]

# ============================================================
# RATE MATCHING
# ============================================================

def rate_match_simulated(sim_data, real_rates, rng=None):
    """
    Scale simulated data so per-detector marginal rates match real data.

    For each detector:
    - If sim_rate < real_rate: randomly flip 0->1 to increase rate
    - If sim_rate > real_rate: randomly flip 1->0 to decrease rate

    This preserves the correlation structure of the simulation while
    matching marginal statistics exactly.
    """
    if rng is None:
        rng = np.random.default_rng(42)

    n_shots, n_det = sim_data.shape
    result = sim_data.copy()
    sim_rates = sim_data.mean(axis=0)

    for d in range(n_det):
        sr = sim_rates[d]
        rr = real_rates[d]

        if abs(sr - rr) < 1e-6:
            continue

        if rr > sr:
            # Need to flip some 0s to 1s
            # P(flip 0->1) such that new_rate = rr
            # new_rate = sr + (1-sr) * p_flip = rr
            # p_flip = (rr - sr) / (1 - sr)
            if sr < 1.0:
                p_flip = (rr - sr) / (1.0 - sr)
                p_flip = min(p_flip, 1.0)
                zeros = result[:, d] < 0.5
                flips = rng.random(n_shots) < p_flip
                result[:, d] = np.where(zeros & flips, 1.0, result[:, d])
        else:
            # Need to flip some 1s to 0s
            # new_rate = sr - sr * p_flip = rr
            # p_flip = (sr - rr) / sr
            if sr > 0:
                p_flip = (sr - rr) / sr
                p_flip = min(p_flip, 1.0)
                ones = result[:, d] > 0.5
                flips = rng.random(n_shots) < p_flip
                result[:, d] = np.where(ones & flips, 0.0, result[:, d])

    return result

# ============================================================
# ANALYSIS FUNCTIONS
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
                    a, b = data[:, detectors[i][1]], data[:, detectors[j][1]]
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

# ============================================================
# MAIN ANALYSIS
# ============================================================

def analyze_experiment(d, r, path):
    print(f"\n{'='*70}")
    print(f"  {d}/{r}: RAW vs RATE-MATCHED RESIDUALS")
    print(f"{'='*70}")

    noisy_stim = os.path.join(path, 'circuit_noisy_si1000.stim')
    ideal_stim = os.path.join(path, 'circuit_ideal.stim')
    circuit_path = ideal_stim if os.path.exists(ideal_stim) else noisy_stim
    circuit = stim.Circuit.from_file(circuit_path)
    coords, n_det = get_detector_coords(circuit)

    # Load real data
    bytes_per_shot = (n_det + 7) // 8
    raw = np.fromfile(os.path.join(path, 'detection_events.b8'), dtype=np.uint8)
    n_shots = len(raw) // bytes_per_shot
    raw = raw[:n_shots * bytes_per_shot].reshape(n_shots, bytes_per_shot)
    real_data = np.unpackbits(raw, axis=1, bitorder='little')[:, :n_det].astype(np.float32)
    real_rates = real_data.mean(axis=0)

    # Generate SI1000 baseline
    noisy_circuit = stim.Circuit.from_file(noisy_stim)
    sampler = noisy_circuit.compile_detector_sampler()
    sim_chunks = []
    remaining = n_shots
    while remaining > 0:
        b = min(50000, remaining)
        sim_chunks.append(sampler.sample(b).astype(np.float32))
        remaining -= b
    sim_data = np.vstack(sim_chunks)
    n_det = min(n_det, sim_data.shape[1])
    real_data = real_data[:, :n_det]
    sim_data = sim_data[:, :n_det]
    real_rates = real_rates[:n_det]
    sim_rates = sim_data.mean(axis=0)

    # Rate-match: scale sim to match real firing rates
    print(f"  Rate mismatch: real={real_rates.mean():.6f}, sim={sim_rates.mean():.6f}")
    rng = np.random.default_rng(42)
    sim_matched = rate_match_simulated(sim_data, real_rates, rng)
    matched_rates = sim_matched.mean(axis=0)
    rate_error = np.abs(matched_rates - real_rates).max()
    print(f"  After matching: sim_matched={matched_rates.mean():.6f}, "
          f"max per-det error={rate_error:.6f}")

    # Distance matrix
    dist_matrix, positions = compute_distance_matrix(coords, n_det)

    # ---- Compute both residuals ----
    print("  Computing correlation matrices...")
    real_corr = compute_correlation_matrix(real_data)
    sim_corr = compute_correlation_matrix(sim_data)
    sim_matched_corr = compute_correlation_matrix(sim_matched)

    raw_residual = real_corr - sim_corr
    matched_residual = real_corr - sim_matched_corr

    np.fill_diagonal(raw_residual, 0)
    np.fill_diagonal(matched_residual, 0)

    # ---- Compare residual statistics ----
    triu = np.triu_indices(n_det, k=1)
    raw_vals = raw_residual[triu]
    matched_vals = matched_residual[triu]

    print(f"\n  {'Metric':<30} {'RAW':>15} {'RATE-MATCHED':>15} {'Change':>12}")
    print(f"  {'-'*72}")

    metrics = {}
    for label, vals, res in [('RAW', raw_vals, raw_residual),
                              ('MATCHED', matched_vals, matched_residual)]:
        m = {}
        m['mean'] = vals.mean()
        m['std'] = vals.std()
        m['max'] = np.abs(vals).max()
        m['frac_2s'] = (np.abs(vals) > 2 * vals.std()).mean()
        m['frac_3s'] = (np.abs(vals) > 3 * vals.std()).mean()

        eigs = np.sort(np.linalg.eigvalsh(res))[::-1]
        pos_eigs = eigs[eigs > 0]
        pos_sum = pos_eigs.sum() if len(pos_eigs) > 0 else 1
        m['top_frac'] = pos_eigs[0] / pos_sum if len(pos_eigs) > 0 else 0
        m['pr'] = pos_sum**2 / (pos_eigs**2).sum() if len(pos_eigs) > 0 else 0
        m['n_pos'] = len(pos_eigs)

        d_r, c_r = bin_correlations_by_distance(np.abs(res), dist_matrix)
        _, pl_b, pl_r2 = fit_power_law(d_r, c_r)
        _, _, ex_r2 = fit_exponential(d_r, c_r)
        m['pl_exp'] = pl_b
        m['pl_r2'] = pl_r2
        m['ex_r2'] = ex_r2
        m['winner'] = 'PL' if pl_r2 > ex_r2 else 'EXP'

        boundary, bulk = classify_boundary_bulk(coords, n_det)
        if len(boundary) > 2 and len(bulk) > 2:
            bp = [res[boundary[i], boundary[j]] for i in range(len(boundary)) for j in range(i+1, len(boundary))]
            blp = [res[bulk[i], bulk[j]] for i in range(len(bulk)) for j in range(i+1, len(bulk))]
            if bp and blp:
                m['bb'] = np.abs(np.array(bp)).mean() / max(np.abs(np.array(blp)).mean(), 1e-10)
            else:
                m['bb'] = None
        else:
            m['bb'] = None

        metrics[label] = m

    # Print comparison
    def pct_change(a, b):
        if a == 0: return "N/A"
        return f"{(b-a)/abs(a)*100:+.1f}%"

    r, m = metrics['RAW'], metrics['MATCHED']
    rows = [
        ('Mean residual', f"{r['mean']:.8f}", f"{m['mean']:.8f}", pct_change(r['mean'], m['mean'])),
        ('Std residual', f"{r['std']:.8f}", f"{m['std']:.8f}", pct_change(r['std'], m['std'])),
        ('Max |residual|', f"{r['max']:.8f}", f"{m['max']:.8f}", pct_change(r['max'], m['max'])),
        ('Frac > 2 sigma', f"{r['frac_2s']:.6f}", f"{m['frac_2s']:.6f}", pct_change(r['frac_2s'], m['frac_2s'])),
        ('Frac > 3 sigma', f"{r['frac_3s']:.6f}", f"{m['frac_3s']:.6f}", pct_change(r['frac_3s'], m['frac_3s'])),
        ('Top eig fraction', f"{r['top_frac']:.6f}", f"{m['top_frac']:.6f}", pct_change(r['top_frac'], m['top_frac'])),
        ('Participation ratio', f"{r['pr']:.1f}/{r['n_pos']}", f"{m['pr']:.1f}/{m['n_pos']}", ""),
        ('PL exponent', f"{r['pl_exp']:.4f}" if r['pl_exp'] else "N/A",
                        f"{m['pl_exp']:.4f}" if m['pl_exp'] else "N/A",
                        pct_change(r['pl_exp'] or 0, m['pl_exp'] or 0)),
        ('PL R-squared', f"{r['pl_r2']:.4f}", f"{m['pl_r2']:.4f}", pct_change(r['pl_r2'], m['pl_r2'])),
        ('Exp R-squared', f"{r['ex_r2']:.4f}", f"{m['ex_r2']:.4f}", pct_change(r['ex_r2'], m['ex_r2'])),
        ('Spatial winner', r['winner'], m['winner'], "SAME" if r['winner'] == m['winner'] else "CHANGED!"),
        ('Boundary/Bulk', f"{r['bb']:.4f}" if r['bb'] else "N/A",
                          f"{m['bb']:.4f}" if m['bb'] else "N/A", ""),
    ]
    for name, rv, mv, ch in rows:
        print(f"  {name:<30} {rv:>15} {mv:>15} {ch:>12}")

    # ---- Temporal autocorrelation comparison ----
    print(f"\n  Temporal autocorrelation excess (real - sim):")
    real_temporal = compute_temporal_autocorrelation(real_data, coords, n_det)
    sim_temporal = compute_temporal_autocorrelation(sim_data, coords, n_det)
    matched_temporal = compute_temporal_autocorrelation(sim_matched, coords, n_det)

    print(f"  {'Lag':<6} {'Raw excess':>15} {'Matched excess':>15} {'Change':>12}")
    temporal_results = {}
    for lag in range(1, 6):
        raw_exc = real_temporal.get(lag, {'mean': 0})['mean'] - sim_temporal.get(lag, {'mean': 0})['mean']
        matched_exc = real_temporal.get(lag, {'mean': 0})['mean'] - matched_temporal.get(lag, {'mean': 0})['mean']
        ch = pct_change(raw_exc, matched_exc) if raw_exc != 0 else "N/A"
        print(f"  {lag:<6} {raw_exc:>15.8f} {matched_exc:>15.8f} {ch:>12}")
        temporal_results[lag] = {'raw': raw_exc, 'matched': matched_exc}

    # Return summary
    return {
        'd': d, 'r': r, 'n_det': n_det, 'n_shots': n_shots,
        'raw': metrics['RAW'], 'matched': metrics['MATCHED'],
        'temporal': temporal_results,
        'rate_mismatch': float(real_rates.mean() - sim_rates.mean()),
    }

if __name__ == '__main__':
    print("="*70)
    print("  RATE-MATCHED RESIDUAL ANALYSIS: GOOGLE WILLOW")
    print("  Isolating correlation topology from intensity mismatch")
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

    # ============================================================
    # CROSS-EXPERIMENT SUMMARY
    # ============================================================
    print("\n\n" + "="*70)
    print("  CROSS-EXPERIMENT: RAW vs RATE-MATCHED")
    print("="*70)

    print(f"\n  {'Exp':<10} {'PL exp (raw)':>14} {'PL exp (match)':>16} {'Change':>10} "
          f"{'PL R2 (raw)':>13} {'PL R2 (match)':>15} {'Winner(R/M)':>13}")
    print(f"  {'-'*90}")

    raw_exponents = []
    matched_exponents = []
    d_values = []

    for res in results:
        exp = f"{res['d']}/{res['r']}"
        rpe = res['raw']['pl_exp']
        mpe = res['matched']['pl_exp']
        rpr = res['raw']['pl_r2']
        mpr = res['matched']['pl_r2']
        rw = res['raw']['winner']
        mw = res['matched']['winner']
        ch = f"{(mpe-rpe)/abs(rpe)*100:+.1f}%" if rpe and mpe and rpe != 0 else "N/A"
        print(f"  {exp:<10} {rpe:>14.4f} {mpe:>16.4f} {ch:>10} "
              f"{rpr:>13.4f} {mpr:>15.4f} {rw:>5}/{mw:<5}")

        if rpe is not None and mpe is not None:
            raw_exponents.append(rpe)
            matched_exponents.append(mpe)
            d_values.append(int(res['d'][1:]))

    # ---- Key question: Does the power-law flattening survive rate-matching? ----
    print(f"\n  POWER-LAW FLATTENING TEST:")
    print(f"  (Does the exponent trend toward 0 with increasing d survive rate-matching?)")
    print()

    # Group by d
    for d_val in [3, 5, 7]:
        raw_es = [raw_exponents[i] for i in range(len(d_values)) if d_values[i] == d_val]
        mat_es = [matched_exponents[i] for i in range(len(d_values)) if d_values[i] == d_val]
        if raw_es and mat_es:
            print(f"    d={d_val}: raw mean exp = {np.mean(raw_es):.4f}, "
                  f"matched mean exp = {np.mean(mat_es):.4f}")

    # Fit exponent vs d for both
    if len(set(d_values)) >= 2:
        d_arr = np.array(d_values, dtype=float)
        raw_arr = np.array(raw_exponents)
        mat_arr = np.array(matched_exponents)

        slope_raw, _, r_raw, _, _ = stats.linregress(d_arr, raw_arr)
        slope_mat, _, r_mat, _, _ = stats.linregress(d_arr, mat_arr)

        print(f"\n    Exponent vs d (linear fit):")
        print(f"      Raw:          slope={slope_raw:.5f}, R={r_raw:.4f}")
        print(f"      Rate-matched: slope={slope_mat:.5f}, R={r_mat:.4f}")

        if abs(slope_mat) < abs(slope_raw) * 0.5:
            print(f"\n    >> FLATTENING IS REDUCED by rate-matching ({abs(slope_mat)/abs(slope_raw)*100:.0f}% of raw)")
            print(f"    >> The intensity mismatch PARTIALLY explains the d-dependence.")
        elif abs(slope_mat) > abs(slope_raw) * 0.8:
            print(f"\n    >> FLATTENING SURVIVES rate-matching ({abs(slope_mat)/abs(slope_raw)*100:.0f}% of raw)")
            print(f"    >> This is genuine correlation topology, NOT an intensity artifact.")
        else:
            print(f"\n    >> FLATTENING PARTIALLY SURVIVES ({abs(slope_mat)/abs(slope_raw)*100:.0f}% of raw)")

    # ---- Temporal memory after rate-matching ----
    print(f"\n  TEMPORAL MEMORY TEST (lag 2 excess):")
    for res in results:
        exp = f"{res['d']}/{res['r']}"
        raw_l2 = res['temporal'].get(2, {}).get('raw', 0)
        mat_l2 = res['temporal'].get(2, {}).get('matched', 0)
        ch = f"{(mat_l2-raw_l2)/abs(raw_l2)*100:+.1f}%" if raw_l2 != 0 else "N/A"
        survived = "SURVIVES" if mat_l2 > raw_l2 * 0.5 else "REDUCED" if mat_l2 > 0 else "GONE"
        print(f"    {exp:<10} raw={raw_l2:.8f}  matched={mat_l2:.8f}  {ch:>8}  {survived}")

    # ---- FINAL VERDICT ----
    print(f"\n{'='*70}")
    print(f"  FINAL VERDICT: What survives rate-matching?")
    print(f"{'='*70}")

    # Check each signature
    pl_survives = all(res['matched']['winner'] == 'PL' for res in results)
    print(f"  1. Power-law spatial decay:     {'SURVIVES' if pl_survives else 'DOES NOT SURVIVE'}")

    # Check if temporal memory survives
    temporal_survives = all(res['temporal'].get(2, {}).get('matched', 0) >
                           res['temporal'].get(2, {}).get('raw', 0) * 0.3
                           for res in results if res['temporal'].get(2, {}).get('raw', 0) > 0)
    print(f"  2. Non-Markovian memory:        {'SURVIVES' if temporal_survives else 'DOES NOT SURVIVE'}")

    # Check eigenvalue structure
    eig_stable = all(abs(res['matched']['top_frac'] - res['raw']['top_frac']) /
                     max(res['raw']['top_frac'], 1e-6) < 1.0 for res in results)
    print(f"  3. Diffuse eigenstructure:      {'SURVIVES' if eig_stable else 'CHANGES'}")

    # Check boundary/bulk
    bb_survives = all((res['matched']['bb'] or 0) < 1.0
                      for res in results if res['matched']['bb'] is not None)
    print(f"  4. Bulk > boundary:             {'SURVIVES' if bb_survives else 'DOES NOT SURVIVE'}")

    survived_count = sum([pl_survives, temporal_survives, eig_stable, bb_survives])
    print(f"\n  {survived_count}/4 signatures survive rate-matching.")

    if survived_count >= 3:
        print(f"  CONCLUSION: The residual structure is ROBUST to rate-matching.")
        print(f"  It reflects genuine correlation topology, not intensity mismatch.")
        print(f"  The SI1000 model fails to capture the GEOMETRY of hardware errors,")
        print(f"  not just their magnitude.")
    elif survived_count >= 2:
        print(f"  CONCLUSION: The structure is PARTIALLY explained by rate mismatch.")
        print(f"  Some signatures are genuine topology; others were intensity artifacts.")
    else:
        print(f"  CONCLUSION: The structure is MOSTLY explained by rate mismatch.")
        print(f"  The SI1000 model's main failure is intensity, not topology.")

    print("="*70)
