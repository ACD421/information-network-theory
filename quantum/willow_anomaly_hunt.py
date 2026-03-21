"""
ANOMALY HUNT: Find the genuinely unexplainable in the Willow data.

Not summary statistics — the specific structures that don't fit any model.
"""
import os, sys, time, json
import numpy as np
from scipy import optimize, stats
from collections import defaultdict
import stim
import warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:\Users\andre\Claudius\google_105Q_surface_code_d3_d5_d7'

EXPERIMENTS = [
    ('d3', 'r50', f'{BASE}/d3_at_q6_7/Z/r50'),
    ('d5', 'r50', f'{BASE}/d5_at_q4_7/Z/r50'),
    ('d7', 'r50', f'{BASE}/d7_at_q6_7/Z/r50'),
    ('d7', 'r90', f'{BASE}/d7_at_q6_7/Z/r90'),
]

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

def load_and_rate_match(path, circuit):
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

    rng = np.random.default_rng(42)
    sim_m = sim_data.copy()
    sr = sim_data.mean(axis=0)
    for i in range(n_use):
        rr = real_rates[i] if i < len(real_rates) else sr[i]
        if rr > sr[i] and sr[i] < 1:
            pf = min((rr - sr[i]) / (1 - sr[i]), 1)
            z = sim_m[:, i] < 0.5
            sim_m[:, i] = np.where(z & (rng.random(n_shots) < pf), 1, sim_m[:, i])
        elif rr < sr[i] and sr[i] > 0:
            pf = min((sr[i] - rr) / sr[i], 1)
            o = sim_m[:, i] > 0.5
            sim_m[:, i] = np.where(o & (rng.random(n_shots) < pf), 0, sim_m[:, i])

    return real_data, sim_m, sim_data, coords, n_use, n_shots, real_rates[:n_use]

# ============================================================
# HUNT 1: THE STRONGEST RESIDUAL PAIRS — WHO ARE THEY?
# ============================================================

def hunt_strongest_pairs(residual, coords, n_det, top_n=20):
    """Find the detector pairs with largest |residual| and characterize them."""
    triu = np.triu_indices(n_det, k=1)
    vals = residual[triu]
    indices = np.argsort(np.abs(vals))[::-1][:top_n]

    print(f"\n  Top {top_n} residual pairs:")
    print(f"  {'Rank':>4} {'Det_i':>6} {'Det_j':>6} {'Residual':>10} "
          f"{'Dist':>8} {'Same_t':>7} {'Pos_i':>20} {'Pos_j':>20}")

    pair_info = []
    for rank, idx in enumerate(indices):
        i, j = triu[0][idx], triu[1][idx]
        val = vals[idx]

        ci = coords.get(i, [0, 0, 0])
        cj = coords.get(j, [0, 0, 0])
        spatial_dist = np.sqrt((ci[0]-cj[0])**2 + (ci[1]-cj[1])**2) if len(ci) >= 2 and len(cj) >= 2 else -1
        same_time = abs(ci[2] - cj[2]) < 0.5 if len(ci) >= 3 and len(cj) >= 3 else False

        pos_i = f"({ci[0]:.0f},{ci[1]:.0f},t={ci[2]:.0f})" if len(ci) >= 3 else str(ci[:2])
        pos_j = f"({cj[0]:.0f},{cj[1]:.0f},t={cj[2]:.0f})" if len(cj) >= 3 else str(cj[:2])

        print(f"  {rank+1:>4} {i:>6} {j:>6} {val:>10.6f} "
              f"{spatial_dist:>8.2f} {'YES' if same_time else 'no':>7} "
              f"{pos_i:>20} {pos_j:>20}")

        pair_info.append({
            'i': i, 'j': j, 'val': val,
            'spatial_dist': spatial_dist, 'same_time': same_time,
            'ci': ci, 'cj': cj
        })

    # Statistics about top pairs
    same_t = sum(1 for p in pair_info if p['same_time'])
    diff_t = top_n - same_t
    dists = [p['spatial_dist'] for p in pair_info if p['spatial_dist'] > 0]
    signs = [1 if p['val'] > 0 else -1 for p in pair_info]

    print(f"\n  Same time step: {same_t}/{top_n}")
    print(f"  Mean spatial dist: {np.mean(dists):.2f}")
    print(f"  Positive residuals: {sum(1 for s in signs if s > 0)}, "
          f"Negative: {sum(1 for s in signs if s < 0)}")

    return pair_info

# ============================================================
# HUNT 2: DIRECTIONAL ANISOTROPY
# ============================================================

def hunt_directional_anisotropy(residual, coords, n_det):
    """
    Do residual correlations depend on DIRECTION, not just distance?
    In an isotropic noise model, correlations depend only on distance.
    Anisotropy = the lattice structure leaking through.
    """
    print(f"\n  --- Directional Anisotropy ---")

    # Compute angle and distance for each pair, bin by both
    angles_list = []
    dists_list = []
    resids_list = []

    # Use only same-time pairs for clean spatial structure
    time_groups = {}
    for i in range(n_det):
        if i in coords and len(coords[i]) >= 3:
            t = round(coords[i][2], 1)
            time_groups.setdefault(t, []).append(i)

    for t, dets in time_groups.items():
        for idx_a in range(len(dets)):
            for idx_b in range(idx_a + 1, len(dets)):
                i, j = dets[idx_a], dets[idx_b]
                ci, cj = coords[i], coords[j]
                dx = cj[0] - ci[0]
                dy = cj[1] - ci[1]
                dist = np.sqrt(dx**2 + dy**2)
                if dist < 0.1:
                    continue
                angle = np.arctan2(dy, dx) % np.pi  # 0 to pi (undirected)
                angles_list.append(angle)
                dists_list.append(dist)
                resids_list.append(residual[i, j])

    if len(angles_list) < 100:
        print("  Insufficient same-time pairs")
        return

    angles = np.array(angles_list)
    dists = np.array(dists_list)
    resids = np.abs(np.array(resids_list))

    # Bin by angle (6 bins from 0 to pi)
    n_angle_bins = 6
    angle_bins = np.linspace(0, np.pi, n_angle_bins + 1)
    angle_labels = [f"{np.degrees(angle_bins[i]):.0f}-{np.degrees(angle_bins[i+1]):.0f}deg"
                    for i in range(n_angle_bins)]

    print(f"  {'Angle':>16} {'Mean |resid|':>14} {'Std':>10} {'Count':>8} {'Norm':>8}")

    angle_means = []
    for i in range(n_angle_bins):
        mask = (angles >= angle_bins[i]) & (angles < angle_bins[i+1])
        if mask.sum() > 0:
            m = resids[mask].mean()
            s = resids[mask].std()
            angle_means.append(m)
            print(f"  {angle_labels[i]:>16} {m:>14.8f} {s:>10.8f} {mask.sum():>8}")

    if len(angle_means) > 1:
        anisotropy = (max(angle_means) - min(angle_means)) / np.mean(angle_means)
        print(f"\n  Anisotropy ratio: {anisotropy:.4f}")
        if anisotropy > 0.1:
            print(f"  >> SIGNIFICANT ANISOTROPY — residual depends on lattice direction")
        else:
            print(f"  >> Approximately isotropic")

    # Also check: do specific lattice directions (45deg, 90deg, 135deg for surface code)
    # show different correlations?
    # Surface code has stabilizers along diagonal directions
    for target_angle, label in [(0, "horizontal"), (np.pi/4, "diagonal-45"),
                                 (np.pi/2, "vertical"), (3*np.pi/4, "diagonal-135")]:
        mask = np.abs(angles - target_angle) < np.pi/12  # within 15 degrees
        if mask.sum() > 10:
            m = resids[mask].mean()
            print(f"  {label:>20}: mean|resid|={m:.8f} (n={mask.sum()})")

# ============================================================
# HUNT 3: WHICH DETECTORS ARE ANOMALOUS?
# ============================================================

def hunt_anomalous_detectors(real_data, sim_matched, residual, coords, n_det, real_rates):
    """Find detectors whose behavior deviates most from SI1000."""
    print(f"\n  --- Most Anomalous Detectors ---")

    # Per-detector anomaly score: sum of |residual| with all other detectors
    anomaly_scores = np.abs(residual).sum(axis=1)
    anomaly_scores /= anomaly_scores.mean()  # normalize

    # Rate anomaly
    sim_rates = sim_matched.mean(axis=0)
    rate_ratio = real_rates / np.clip(sim_rates, 1e-6, None)

    # Variance anomaly
    real_var = real_data.var(axis=0)
    sim_var = sim_matched.var(axis=0)
    var_ratio = real_var / np.clip(sim_var, 1e-6, None)

    top_idx = np.argsort(anomaly_scores)[::-1][:15]

    print(f"  {'Rank':>4} {'Det':>6} {'Anom score':>12} {'Rate ratio':>12} "
          f"{'Var ratio':>12} {'Position':>25}")
    for rank, idx in enumerate(top_idx):
        pos = coords.get(idx, [])
        pos_str = f"({pos[0]:.0f},{pos[1]:.0f},t={pos[2]:.0f})" if len(pos) >= 3 else str(pos[:2])
        print(f"  {rank+1:>4} {idx:>6} {anomaly_scores[idx]:>12.4f} "
              f"{rate_ratio[idx]:>12.4f} {var_ratio[idx]:>12.4f} {pos_str:>25}")

    # Do anomalous detectors cluster spatially?
    top_positions = []
    for idx in top_idx:
        if idx in coords and len(coords[idx]) >= 2:
            top_positions.append([coords[idx][0], coords[idx][1]])

    if len(top_positions) > 2:
        top_positions = np.array(top_positions)
        centroid = top_positions.mean(axis=0)
        spread = np.std(top_positions, axis=0)
        print(f"\n  Anomalous detector centroid: ({centroid[0]:.2f}, {centroid[1]:.2f})")
        print(f"  Spread: ({spread[0]:.2f}, {spread[1]:.2f})")

        # Compare to overall detector spread
        all_pos = np.array([[coords[i][0], coords[i][1]] for i in range(n_det)
                           if i in coords and len(coords[i]) >= 2])
        all_spread = np.std(all_pos, axis=0)
        concentration = spread / all_spread
        print(f"  Overall spread: ({all_spread[0]:.2f}, {all_spread[1]:.2f})")
        print(f"  Concentration ratio: ({concentration[0]:.3f}, {concentration[1]:.3f})")
        if (concentration < 0.7).any():
            print(f"  >> ANOMALOUS DETECTORS ARE SPATIALLY CLUSTERED")

    # Are anomalous detectors preferentially at boundary or bulk?
    all_pos_arr = np.array([[coords[i][0], coords[i][1]] for i in range(n_det)
                            if i in coords and len(coords[i]) >= 2])
    center = all_pos_arr.mean(axis=0)
    all_dists = np.sqrt(((all_pos_arr - center)**2).sum(axis=1))
    max_dist = all_dists.max()

    top_dists = []
    for idx in top_idx:
        if idx in coords and len(coords[idx]) >= 2:
            d = np.sqrt((coords[idx][0] - center[0])**2 + (coords[idx][1] - center[1])**2)
            top_dists.append(d / max_dist)

    if top_dists:
        mean_norm_dist = np.mean(top_dists)
        print(f"  Mean normalized distance from center: {mean_norm_dist:.3f}")
        print(f"  (0.5 = uniform, >0.5 = boundary-biased, <0.5 = bulk-biased)")

# ============================================================
# HUNT 4: TEMPORAL STRUCTURE DEEP DIVE
# ============================================================

def hunt_temporal_structure(real_data, sim_matched, coords, n_det):
    """Deep dive into temporal correlation structure."""
    print(f"\n  --- Temporal Deep Dive ---")

    # Group by spatial position, sort by time
    spatial_groups = {}
    for i in range(n_det):
        if i in coords and len(coords[i]) >= 3:
            key = (round(coords[i][0], 2), round(coords[i][1], 2))
            spatial_groups.setdefault(key, []).append((coords[i][2], i))
    for key in spatial_groups:
        spatial_groups[key].sort()

    # Compute lag correlations for each spatial position
    max_lag = 10
    real_lag_by_position = defaultdict(lambda: {lag: [] for lag in range(1, max_lag+1)})
    sim_lag_by_position = defaultdict(lambda: {lag: [] for lag in range(1, max_lag+1)})

    for key, detectors in spatial_groups.items():
        if len(detectors) < 3:
            continue
        for i in range(len(detectors)):
            for j in range(i+1, min(i+max_lag+1, len(detectors))):
                lag = int(round(detectors[j][0] - detectors[i][0]))
                if lag < 1 or lag > max_lag:
                    continue
                d_i, d_j = detectors[i][1], detectors[j][1]
                # Real
                a, b = real_data[:, d_i], real_data[:, d_j]
                ac, bc = a - a.mean(), b - b.mean()
                denom = np.sqrt((ac**2).sum() * (bc**2).sum())
                if denom > 0:
                    real_lag_by_position[key][lag].append((ac * bc).sum() / denom)
                # Sim
                a, b = sim_matched[:, d_i], sim_matched[:, d_j]
                ac, bc = a - a.mean(), b - b.mean()
                denom = np.sqrt((ac**2).sum() * (bc**2).sum())
                if denom > 0:
                    sim_lag_by_position[key][lag].append((ac * bc).sum() / denom)

    # Aggregate lag correlations
    print(f"  {'Lag':>4} {'Real mean':>12} {'Sim mean':>12} {'Excess':>12} {'Excess/Lag1':>12} {'Decay':>10}")
    excess_values = []
    for lag in range(1, max_lag + 1):
        real_all = []
        sim_all = []
        for key in real_lag_by_position:
            real_all.extend(real_lag_by_position[key][lag])
            sim_all.extend(sim_lag_by_position[key][lag])
        if real_all and sim_all:
            rm = np.mean(real_all)
            sm = np.mean(sim_all)
            excess = rm - sm
            excess_values.append(excess)
            ratio_to_lag1 = excess / excess_values[0] if len(excess_values) > 0 and excess_values[0] != 0 else 0
            decay = ""
            if lag >= 2 and len(excess_values) >= 2 and excess_values[0] > 0:
                # Fit power law to excess vs lag
                if excess > 0:
                    decay = f"lag^{np.log(excess/excess_values[0])/np.log(lag):.2f}"
            print(f"  {lag:>4} {rm:>12.8f} {sm:>12.8f} {excess:>12.8f} {ratio_to_lag1:>12.4f} {decay:>10}")

    # What's the decay law for the excess?
    if len(excess_values) >= 4:
        lags = np.arange(2, min(len(excess_values)+1, max_lag+1))
        excs = np.array(excess_values[1:len(lags)+1])  # skip lag 1
        mask = excs > 0
        if mask.sum() >= 3:
            lags_fit = lags[mask].astype(float)
            excs_fit = excs[mask]
            slope, intercept, r, _, _ = stats.linregress(np.log(lags_fit), np.log(excs_fit))
            print(f"\n  Temporal excess decay (lags 2-{max_lag}): power law exponent = {slope:.4f}, R = {r:.4f}")
            if abs(slope + 1) < 0.3:
                print(f"  >> EXCESS DECAYS AS 1/lag — characteristic of 1/f noise")
            elif abs(slope + 0.5) < 0.3:
                print(f"  >> EXCESS DECAYS AS 1/sqrt(lag) — subdiffusive")
            elif abs(slope + 2) < 0.3:
                print(f"  >> EXCESS DECAYS AS 1/lag^2 — normal Markovian relaxation")

    # Per-position temporal excess variance: are some positions more non-Markovian?
    pos_excess_lag2 = {}
    for key in real_lag_by_position:
        if real_lag_by_position[key][2] and sim_lag_by_position[key][2]:
            re = np.mean(real_lag_by_position[key][2])
            se = np.mean(sim_lag_by_position[key][2])
            pos_excess_lag2[key] = re - se

    if pos_excess_lag2:
        excesses = list(pos_excess_lag2.values())
        print(f"\n  Per-position lag-2 excess: mean={np.mean(excesses):.8f}, "
              f"std={np.std(excesses):.8f}")
        print(f"  Range: [{min(excesses):.8f}, {max(excesses):.8f}]")
        cv = np.std(excesses) / abs(np.mean(excesses)) if np.mean(excesses) != 0 else 0
        print(f"  Coefficient of variation: {cv:.4f}")
        if cv > 1.5:
            print(f"  >> MEMORY IS HIGHLY HETEROGENEOUS — some positions much more non-Markovian")

            # Where are the most non-Markovian positions?
            sorted_pos = sorted(pos_excess_lag2.items(), key=lambda x: abs(x[1]), reverse=True)
            print(f"\n  Most non-Markovian positions:")
            for (x, y), exc in sorted_pos[:8]:
                print(f"    ({x:.0f}, {y:.0f}): excess = {exc:.8f}")

# ============================================================
# HUNT 5: THE EXACT SCALING LAW
# ============================================================

def hunt_scaling_law(all_results):
    """Pin down the exact mathematical relationship between decay length and d."""
    print(f"\n{'='*70}")
    print(f"  HUNT 5: THE EXACT SCALING LAW")
    print(f"{'='*70}")

    d_vals = []
    exponents = []
    for (d_label, r_label), exp_val in all_results.items():
        if r_label == 'r50':  # Fixed rounds for clean comparison
            d = int(d_label[1:])
            d_vals.append(d)
            exponents.append(exp_val)

    d_arr = np.array(d_vals, dtype=float)
    exp_arr = np.array(exponents)
    decay_lengths = 1.0 / np.abs(exp_arr)

    print(f"\n  d  | exponent  | decay length | d/decay | log(decay)/log(d)")
    for d, e, dl in zip(d_vals, exponents, decay_lengths):
        ratio = d / dl
        log_ratio = np.log(dl) / np.log(d) if d > 1 else 0
        print(f"  {d}  | {e:>9.4f} | {dl:>12.4f} | {ratio:>7.2f} | {log_ratio:>7.4f}")

    # Test various scaling hypotheses
    print(f"\n  Scaling hypotheses (decay_length = f(d)):")

    # Linear: decay_length = a * d + b
    if len(d_vals) >= 3:
        slope, intercept, r, p, se = stats.linregress(d_arr, decay_lengths)
        print(f"  Linear (a*d + b):       a={slope:.5f}, b={intercept:.5f}, R={r:.4f}")

    # Power: decay_length = a * d^b
    if len(d_vals) >= 3:
        s, i, r, p, se = stats.linregress(np.log(d_arr), np.log(decay_lengths))
        print(f"  Power (a * d^b):        a={np.exp(i):.5f}, b={s:.5f}, R={r:.4f}")

    # Bulk depth: decay_length = a * (d-1)/2 + b
    bulk = (d_arr - 1) / 2
    if len(d_vals) >= 3:
        slope, intercept, r, p, se = stats.linregress(bulk, decay_lengths)
        print(f"  Bulk depth ((d-1)/2):   a={slope:.5f}, b={intercept:.5f}, R={r:.4f}")

    # Inverse: exponent = -C/d
    if len(d_vals) >= 3:
        inv_d = 1.0 / d_arr
        slope, intercept, r, p, se = stats.linregress(inv_d, exp_arr)
        print(f"  Inverse (exp = C/d):    C={slope:.5f}, offset={intercept:.5f}, R={r:.4f}")

    # Log: decay_length = a * ln(d) + b
    if len(d_vals) >= 3:
        slope, intercept, r, p, se = stats.linregress(np.log(d_arr), decay_lengths)
        print(f"  Logarithmic (a*ln(d)):  a={slope:.5f}, b={intercept:.5f}, R={r:.4f}")

    # d^2 (area): exponent = -C/d^2
    if len(d_vals) >= 3:
        inv_d2 = 1.0 / d_arr**2
        slope, intercept, r, p, se = stats.linregress(inv_d2, exp_arr)
        print(f"  Area (exp = C/d^2):     C={slope:.5f}, offset={intercept:.5f}, R={r:.4f}")

    # The EXACT relationship test: is exponent = -a/(d-1) + b ?
    if len(d_vals) >= 3:
        inv_dm1 = 1.0 / (d_arr - 1)
        slope, intercept, r, p, se = stats.linregress(inv_dm1, exp_arr)
        print(f"  exp = a/(d-1) + b:      a={slope:.5f}, b={intercept:.5f}, R={r:.4f}")

    # Best fit identification
    print(f"\n  ** Checking if exponent tracks qubit count, edge count, or logical weight:")
    n_data_qubits = [2*d**2 - 1 for d in d_vals]  # approximate
    n_measure_qubits = [d**2 - 1 for d in d_vals]  # approximate
    n_stabilizers_per_round = [(d**2 - 1) for d in d_vals]

    for name, vals in [("n_data_qubits", n_data_qubits),
                       ("n_measure_qubits", n_measure_qubits),
                       ("logical_weight (d)", d_vals)]:
        v = np.array(vals, dtype=float)
        s, i, r, p, se = stats.linregress(v, exp_arr)
        print(f"    vs {name:>20}: R={r:.4f}")

# ============================================================
# HUNT 6: SHOT-TO-SHOT VARIABILITY
# ============================================================

def hunt_shot_variability(real_data, sim_matched, coords, n_det, n_blocks=20):
    """
    Is the anomaly constant across shots or does it fluctuate?
    Divide data into blocks, compute residual per block, see if it's stable.
    """
    print(f"\n  --- Shot-to-Shot Variability ---")

    n_shots = real_data.shape[0]
    block_size = n_shots // n_blocks

    block_stds = []
    block_max_resids = []

    for b in range(n_blocks):
        start = b * block_size
        end = min(start + block_size, n_shots)
        rc = compute_correlation_matrix(real_data[start:end])
        sc = compute_correlation_matrix(sim_matched[start:end])
        res = rc - sc
        np.fill_diagonal(res, 0)
        triu = np.triu_indices(n_det, k=1)
        vals = res[triu]
        block_stds.append(vals.std())
        block_max_resids.append(np.abs(vals).max())

    stds = np.array(block_stds)
    maxes = np.array(block_max_resids)

    print(f"  Block residual std: mean={stds.mean():.8f}, "
          f"cv={stds.std()/stds.mean():.4f}")
    print(f"  Block max|resid|:  mean={maxes.mean():.6f}, "
          f"cv={maxes.std()/maxes.mean():.4f}")

    cv_std = stds.std() / stds.mean()
    if cv_std > 0.3:
        print(f"  >> RESIDUAL FLUCTUATES STRONGLY between blocks")
        print(f"  >> This suggests intermittent noise sources (cosmic rays, TLS switching)")

        # Which blocks are worst?
        worst = np.argsort(maxes)[::-1][:3]
        best = np.argsort(maxes)[:3]
        print(f"  Worst blocks: {worst} (max resid: {maxes[worst]})")
        print(f"  Best blocks:  {best} (max resid: {maxes[best]})")
    else:
        print(f"  >> Residual is STABLE across blocks — persistent, not intermittent")

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("="*70)
    print("  ANOMALY HUNT: The Strange and Unexplainable")
    print("="*70)

    all_spatial_exponents = {}

    for d_label, r_label, path in EXPERIMENTS:
        print(f"\n\n{'#'*70}")
        print(f"  {d_label}/{r_label}")
        print(f"{'#'*70}")

        noisy_stim = os.path.join(path, 'circuit_noisy_si1000.stim')
        circuit = stim.Circuit.from_file(noisy_stim)

        real_data, sim_matched, sim_raw, coords, n_use, n_shots, real_rates = \
            load_and_rate_match(path, circuit)

        # Compute residual
        real_corr = compute_correlation_matrix(real_data)
        sim_corr = compute_correlation_matrix(sim_matched)
        residual = real_corr - sim_corr
        np.fill_diagonal(residual, 0)

        # Compute spatial-only exponent
        time_groups = {}
        for i in range(n_use):
            if i in coords and len(coords[i]) >= 3:
                t = round(coords[i][2], 1)
                time_groups.setdefault(t, []).append(i)

        valid_times = sorted([t for t, d in time_groups.items() if len(d) >= 8])
        n_skip = max(1, len(valid_times) // 10)
        valid_times = valid_times[n_skip:-n_skip]

        all_d, all_r = [], []
        for t in valid_times:
            dets = time_groups[t]
            if len(dets) < 4: continue
            rc = compute_correlation_matrix(real_data[:, dets])
            sc = compute_correlation_matrix(sim_matched[:, dets])
            res = rc - sc
            np.fill_diagonal(res, 0)
            pos = np.zeros((len(dets), 2))
            for idx, d in enumerate(dets):
                if d in coords: pos[idx] = [coords[d][0], coords[d][1]]
            for i in range(len(dets)):
                for j in range(i+1, len(dets)):
                    dist = np.sqrt(((pos[i]-pos[j])**2).sum())
                    if dist > 0.01:
                        all_d.append(dist)
                        all_r.append(abs(res[i,j]))

        if all_d:
            ad, ar = np.array(all_d), np.array(all_r)
            d_min = max(ad.min(), 0.1)
            bins = np.logspace(np.log10(d_min), np.log10(ad.max()), 16)
            centers, means = [], []
            for i in range(len(bins)-1):
                m = (ad >= bins[i]) & (ad < bins[i+1])
                if m.sum() > 0:
                    centers.append(np.sqrt(bins[i]*bins[i+1]))
                    means.append(ar[m].mean())
            centers, means = np.array(centers), np.array(means)
            mask = (centers > 0) & (means > 0)
            if mask.sum() >= 3:
                slope, intercept, r, p, se = stats.linregress(
                    np.log(centers[mask]), np.log(means[mask]))
                all_spatial_exponents[(d_label, r_label)] = slope
                print(f"\n  Spatial-only PL exponent: {slope:.4f}")

        # Run all hunts
        hunt_strongest_pairs(residual, coords, n_use)
        hunt_directional_anisotropy(residual, coords, n_use)
        hunt_anomalous_detectors(real_data, sim_matched, residual, coords, n_use, real_rates)
        hunt_temporal_structure(real_data, sim_matched, coords, n_use)
        hunt_shot_variability(real_data, sim_matched, coords, n_use)

    # Scaling law hunt across all experiments
    hunt_scaling_law(all_spatial_exponents)

    print(f"\n\n{'='*70}")
    print(f"  SUMMARY OF ANOMALIES")
    print(f"{'='*70}")
    print(f"""
  This script looked for six types of anomaly:
  1. Strongest residual pairs - who and where
  2. Directional anisotropy - lattice direction dependence
  3. Anomalous detectors - spatial clustering
  4. Temporal structure - decay law, heterogeneity
  5. Exact scaling law - what mathematical function fits
  6. Shot variability - persistent vs intermittent
    """)
