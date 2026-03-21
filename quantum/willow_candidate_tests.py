"""
CANDIDATE DISCRIMINATION TESTS

Test 1 (Candidate 2 - Criticality):
  Separate SPATIAL-ONLY correlations (same time step, different position)
  from spatiotemporal correlations. If the spatial-only PL exponent depends
  on rounds at fixed d → criticality. If it depends only on d → topological.

Test 2 (Candidate 1 - Near-miss chains):
  Compute connected cluster statistics in real vs simulated detection events.
  Look for excess clusters with spatial extent approaching d.

Test 3 (Candidate 3 - Topological):
  If the spatial-only exponent depends ONLY on d and scales as d/2 (bulk depth),
  that's the topological prediction.
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
    ('d5', 'r90', f'{BASE}/d5_at_q4_7/Z/r90'),
    ('d7', 'r50', f'{BASE}/d7_at_q6_7/Z/r50'),
    ('d7', 'r90', f'{BASE}/d7_at_q6_7/Z/r90'),
    ('d7', 'r130', f'{BASE}/d7_at_q6_7/Z/r130'),
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

def load_and_rate_match(path, circuit):
    """Load real data, generate SI1000, rate-match, return both."""
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

    return real_data, sim_m, coords, n_use, n_shots

# ============================================================
# TEST 1: SPATIAL-ONLY PL EXPONENT (Criticality vs Topological)
# ============================================================

def compute_spatial_only_exponent(real_data, sim_matched, coords, n_det):
    """
    Compute PL exponent using ONLY detector pairs at the SAME time step.
    This isolates spatial from temporal effects.
    """
    # Group detectors by time coordinate (3rd dim)
    time_groups = {}
    for i in range(n_det):
        if i in coords and len(coords[i]) >= 3:
            t = round(coords[i][2], 1)
            time_groups.setdefault(t, []).append(i)

    # Pick time steps with enough detectors (skip first/last which may be boundary)
    valid_times = sorted([t for t, dets in time_groups.items() if len(dets) >= 8])
    if len(valid_times) < 3:
        return None, None, None, None

    # Use middle 80% of time steps
    n_skip = max(1, len(valid_times) // 10)
    valid_times = valid_times[n_skip:-n_skip]

    # For each time step, compute spatial correlation of residual
    all_dists = []
    all_residuals = []

    for t in valid_times:
        dets = time_groups[t]
        n_t = len(dets)
        if n_t < 4:
            continue

        # Extract data for these detectors
        real_slice = real_data[:, dets]
        sim_slice = sim_matched[:, dets]

        # Correlation matrices
        real_corr = compute_correlation_matrix(real_slice)
        sim_corr = compute_correlation_matrix(sim_slice)
        residual = real_corr - sim_corr
        np.fill_diagonal(residual, 0)

        # Spatial distances (first 2 coords only)
        pos = np.zeros((n_t, 2))
        for idx, d in enumerate(dets):
            if d in coords and len(coords[d]) >= 2:
                pos[idx] = [coords[d][0], coords[d][1]]

        for i in range(n_t):
            for j in range(i + 1, n_t):
                dist = np.sqrt(((pos[i] - pos[j])**2).sum())
                if dist > 0.01:
                    all_dists.append(dist)
                    all_residuals.append(abs(residual[i, j]))

    if len(all_dists) < 50:
        return None, None, None, None

    all_dists = np.array(all_dists)
    all_residuals = np.array(all_residuals)

    # Bin by distance
    d_min, d_max = max(all_dists.min(), 0.1), all_dists.max()
    n_bins = 15
    bins = np.logspace(np.log10(d_min), np.log10(d_max), n_bins + 1)
    centers, means = [], []
    for i in range(n_bins):
        m = (all_dists >= bins[i]) & (all_dists < bins[i + 1])
        if m.sum() > 0:
            centers.append(np.sqrt(bins[i] * bins[i + 1]))
            means.append(all_residuals[m].mean())

    centers, means = np.array(centers), np.array(means)
    _, pl_exp, pl_r2 = fit_power_law(centers, means)
    _, _, ex_r2 = fit_exponential(centers, means)

    return pl_exp, pl_r2, ex_r2, len(valid_times)

# ============================================================
# TEST 2: ERROR CHAIN ANALYSIS (Near-miss chains)
# ============================================================

def compute_cluster_statistics(data, coords, n_det, d_code, max_shots=10000):
    """
    For each shot, find connected clusters of firing detectors.
    A cluster is a set of detectors connected by spatial proximity (distance < 2.5).
    Report: cluster size distribution, max spatial extent, fraction near-d.
    """
    # Build adjacency: detectors within spatial distance 2.5 of each other
    # (Only use spatial coords, same time step)
    time_groups = {}
    for i in range(n_det):
        if i in coords and len(coords[i]) >= 3:
            t = round(coords[i][2], 1)
            time_groups.setdefault(t, []).append(i)

    # Build spatial neighbor graph within each time step
    neighbors = {i: set() for i in range(n_det)}
    for t, dets in time_groups.items():
        pos = {}
        for d in dets:
            if d in coords:
                pos[d] = (coords[d][0], coords[d][1])
        det_list = list(pos.keys())
        for i_idx in range(len(det_list)):
            for j_idx in range(i_idx + 1, len(det_list)):
                di, dj = det_list[i_idx], det_list[j_idx]
                dx = pos[di][0] - pos[dj][0]
                dy = pos[di][1] - pos[dj][1]
                dist = np.sqrt(dx**2 + dy**2)
                if dist < 2.5:
                    neighbors[di].add(dj)
                    neighbors[dj].add(di)

    # Also connect same-position detectors across adjacent time steps
    sorted_times = sorted(time_groups.keys())
    for t_idx in range(len(sorted_times) - 1):
        t1, t2 = sorted_times[t_idx], sorted_times[t_idx + 1]
        for d1 in time_groups[t1]:
            for d2 in time_groups[t2]:
                if d1 in coords and d2 in coords:
                    dx = coords[d1][0] - coords[d2][0]
                    dy = coords[d1][1] - coords[d2][1]
                    if abs(dx) < 0.1 and abs(dy) < 0.1:
                        neighbors[d1].add(d2)
                        neighbors[d2].add(d1)

    # Process shots
    n_shots = min(data.shape[0], max_shots)
    cluster_sizes = []
    cluster_extents = []
    near_d_count = 0
    total_clusters = 0

    for shot in range(n_shots):
        firing = set(np.where(data[shot] > 0.5)[0])
        if not firing:
            continue

        # Find connected components via BFS
        visited = set()
        for start in firing:
            if start in visited:
                continue
            # BFS
            cluster = set()
            queue = [start]
            while queue:
                node = queue.pop(0)
                if node in visited or node not in firing:
                    continue
                visited.add(node)
                cluster.add(node)
                for nb in neighbors.get(node, set()):
                    if nb not in visited and nb in firing:
                        queue.append(nb)

            if len(cluster) >= 2:
                total_clusters += 1
                cluster_sizes.append(len(cluster))

                # Spatial extent of cluster
                positions = []
                for d in cluster:
                    if d in coords and len(coords[d]) >= 2:
                        positions.append([coords[d][0], coords[d][1]])
                if len(positions) >= 2:
                    positions = np.array(positions)
                    extent = np.max(np.ptp(positions, axis=0))
                    cluster_extents.append(extent)

                    # Near-d: extent > 0.7 * (d_code - 1) * 2
                    # (spatial extent of the full code is roughly 2*(d-1))
                    code_span = 2 * (d_code - 1)
                    if extent > 0.6 * code_span:
                        near_d_count += 1

    return {
        'total_clusters': total_clusters,
        'cluster_sizes': np.array(cluster_sizes) if cluster_sizes else np.array([0]),
        'cluster_extents': np.array(cluster_extents) if cluster_extents else np.array([0]),
        'near_d_count': near_d_count,
        'near_d_fraction': near_d_count / max(total_clusters, 1),
        'n_shots': n_shots
    }

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("=" * 70)
    print("  CANDIDATE DISCRIMINATION TESTS")
    print("=" * 70)

    # ================================================================
    # TEST 1: SPATIAL-ONLY PL EXPONENT
    # ================================================================
    print("\n" + "=" * 70)
    print("  TEST 1: SPATIAL-ONLY PL EXPONENT (same-time detector pairs)")
    print("  Criticality predicts: exponent depends on rounds at fixed d")
    print("  Topological predicts: exponent depends ONLY on d")
    print("=" * 70)

    spatial_results = {}

    for d_label, r_label, path in EXPERIMENTS:
        print(f"\n  --- {d_label}/{r_label} ---")
        noisy_stim = os.path.join(path, 'circuit_noisy_si1000.stim')
        circuit = stim.Circuit.from_file(noisy_stim)

        real_data, sim_matched, coords, n_use, n_shots = load_and_rate_match(path, circuit)

        pl_exp, pl_r2, ex_r2, n_times = compute_spatial_only_exponent(
            real_data, sim_matched, coords, n_use)

        if pl_exp is not None:
            winner = "PL" if pl_r2 > ex_r2 else "EXP"
            print(f"  Spatial-only PL exp: {pl_exp:.4f} (R2={pl_r2:.4f})")
            print(f"  Exponential R2: {ex_r2:.4f}")
            print(f"  Winner: {winner}")
            print(f"  Time steps used: {n_times}")
            spatial_results[(d_label, r_label)] = {
                'exp': pl_exp, 'pl_r2': pl_r2, 'ex_r2': ex_r2, 'winner': winner
            }
        else:
            print(f"  Insufficient data for spatial-only analysis")

    # Analyze d-dependence vs rounds-dependence
    print("\n" + "-" * 70)
    print("  SPATIAL-ONLY EXPONENT SUMMARY")
    print("-" * 70)
    print(f"  {'Experiment':<12} {'PL exponent':>14} {'PL R2':>10} {'Winner':>8}")
    for (d, r), res in sorted(spatial_results.items()):
        print(f"  {d}/{r:<8} {res['exp']:>14.4f} {res['pl_r2']:>10.4f} {res['winner']:>8}")

    # Test: at fixed d=7, does exponent depend on rounds?
    d7_exps = [(r, spatial_results[('d7', r)]['exp'])
               for r in ['r50', 'r90', 'r130'] if ('d7', r) in spatial_results]
    if len(d7_exps) >= 2:
        rounds = [int(r[1:]) for r, _ in d7_exps]
        exps = [e for _, e in d7_exps]
        slope_r, _, r_r, p_r, _ = stats.linregress(rounds, exps)
        print(f"\n  d7: exponent vs rounds: slope={slope_r:.6f}/round, R={r_r:.4f}, p={p_r:.4f}")

        if abs(r_r) > 0.8 and p_r < 0.2:
            print(f"  >> EXPONENT DEPENDS ON ROUNDS at fixed d=7")
            print(f"  >> SUPPORTS CANDIDATE 2 (criticality)")
        else:
            print(f"  >> Exponent STABLE across rounds at d=7")
            print(f"  >> SUPPORTS CANDIDATE 3 (topological)")

    # Test: at fixed d=5, does exponent depend on rounds?
    d5_exps = [(r, spatial_results[('d5', r)]['exp'])
               for r in ['r50', 'r90'] if ('d5', r) in spatial_results]
    if len(d5_exps) >= 2:
        rounds = [int(r[1:]) for r, _ in d5_exps]
        exps = [e for _, e in d5_exps]
        diff = exps[1] - exps[0]
        pct = diff / abs(exps[0]) * 100
        print(f"\n  d5: r50={exps[0]:.4f}, r90={exps[1]:.4f}, change={pct:+.1f}%")
        if abs(pct) > 20:
            print(f"  >> EXPONENT CHANGES with rounds at d=5")
        else:
            print(f"  >> Exponent STABLE across rounds at d=5")

    # Test: exponent vs d at fixed r=50
    r50_exps = [(d, spatial_results[(d, 'r50')]['exp'])
                for d in ['d3', 'd5', 'd7'] if (d, 'r50') in spatial_results]
    if len(r50_exps) >= 3:
        d_vals = [int(d[1:]) for d, _ in r50_exps]
        exps = [e for _, e in r50_exps]
        slope_d, _, r_d, p_d, _ = stats.linregress(d_vals, exps)
        print(f"\n  Fixed r=50: exponent vs d: slope={slope_d:.5f}/d, R={r_d:.4f}, p={p_d:.4f}")

        # Does exponent scale as bulk depth (d/2)?
        bulk_depths = [d / 2 for d in d_vals]
        slope_bd, _, r_bd, _, _ = stats.linregress(bulk_depths, exps)
        print(f"  Exponent vs bulk depth (d/2): slope={slope_bd:.5f}, R={r_bd:.4f}")

    # ================================================================
    # TEST 2: ERROR CHAIN / CLUSTER ANALYSIS
    # ================================================================
    print("\n\n" + "=" * 70)
    print("  TEST 2: ERROR CHAIN CLUSTER ANALYSIS")
    print("  Near-miss chains: excess clusters with extent approaching d?")
    print("=" * 70)

    for d_label, r_label, path in [('d3', 'r50', f'{BASE}/d3_at_q6_7/Z/r50'),
                                    ('d5', 'r50', f'{BASE}/d5_at_q4_7/Z/r50'),
                                    ('d7', 'r50', f'{BASE}/d7_at_q6_7/Z/r50')]:
        print(f"\n  --- {d_label}/{r_label} ---")
        d_code = int(d_label[1:])
        noisy_stim = os.path.join(path, 'circuit_noisy_si1000.stim')
        circuit = stim.Circuit.from_file(noisy_stim)
        real_data, sim_matched, coords, n_use, n_shots = load_and_rate_match(path, circuit)

        print(f"  Analyzing real data clusters...")
        real_clusters = compute_cluster_statistics(real_data, coords, n_use, d_code, max_shots=5000)

        print(f"  Analyzing simulated data clusters...")
        sim_clusters = compute_cluster_statistics(sim_matched, coords, n_use, d_code, max_shots=5000)

        print(f"\n  {'Metric':<35} {'Real':>12} {'Sim (matched)':>15} {'Ratio':>10}")
        print(f"  {'-'*72}")

        r_tc = real_clusters['total_clusters']
        s_tc = sim_clusters['total_clusters']
        print(f"  {'Total clusters':<35} {r_tc:>12} {s_tc:>15} {r_tc/max(s_tc,1):>10.3f}")

        r_ms = real_clusters['cluster_sizes'].mean()
        s_ms = sim_clusters['cluster_sizes'].mean()
        print(f"  {'Mean cluster size':<35} {r_ms:>12.2f} {s_ms:>15.2f} {r_ms/max(s_ms,0.01):>10.3f}")

        if len(real_clusters['cluster_sizes']) > 0:
            r_max = real_clusters['cluster_sizes'].max()
            s_max = sim_clusters['cluster_sizes'].max()
            print(f"  {'Max cluster size':<35} {r_max:>12} {s_max:>15} {r_max/max(s_max,1):>10.3f}")

        r_me = real_clusters['cluster_extents'].mean() if len(real_clusters['cluster_extents']) > 0 else 0
        s_me = sim_clusters['cluster_extents'].mean() if len(sim_clusters['cluster_extents']) > 0 else 0
        print(f"  {'Mean cluster extent':<35} {r_me:>12.2f} {s_me:>15.2f} {r_me/max(s_me,0.01):>10.3f}")

        if len(real_clusters['cluster_extents']) > 0:
            r_maxe = real_clusters['cluster_extents'].max()
            s_maxe = sim_clusters['cluster_extents'].max()
            print(f"  {'Max cluster extent':<35} {r_maxe:>12.2f} {s_maxe:>15.2f}")

        r_nd = real_clusters['near_d_fraction']
        s_nd = sim_clusters['near_d_fraction']
        ratio_nd = r_nd / max(s_nd, 1e-6)
        print(f"  {'Near-d fraction (>{0.6*2*(d_code-1):.0f})':<35} {r_nd:>12.6f} {s_nd:>15.6f} {ratio_nd:>10.3f}")

        # Extent distribution comparison
        if len(real_clusters['cluster_extents']) > 10 and len(sim_clusters['cluster_extents']) > 10:
            code_span = 2 * (d_code - 1)
            # Fraction of clusters in different extent ranges
            for threshold_frac in [0.3, 0.5, 0.7, 0.9]:
                threshold = threshold_frac * code_span
                r_frac = (real_clusters['cluster_extents'] > threshold).mean()
                s_frac = (sim_clusters['cluster_extents'] > threshold).mean()
                excess = r_frac / max(s_frac, 1e-6)
                marker = " <<< EXCESS" if excess > 2.0 else ""
                print(f"  {'Extent > ' + f'{threshold:.1f}':<35} {r_frac:>12.6f} {s_frac:>15.6f} {excess:>10.3f}{marker}")

    # ================================================================
    # FINAL DISCRIMINATION
    # ================================================================
    print("\n\n" + "=" * 70)
    print("  CANDIDATE DISCRIMINATION SUMMARY")
    print("=" * 70)

    print("""
  Three candidates for what couples to code distance:

  1. NEAR-MISS CHAINS: Classical correlated errors creating
     scale-dependent clusters approaching length d.

  2. MEASUREMENT-INDUCED CRITICALITY: Repeated measurements
     push the system toward a phase transition where
     correlation length diverges with system size.

  3. TOPOLOGICAL COUPLING: The code's tensor network
     structure creates bulk-depth-dependent correlations.

  The discriminating tests:
  """)

    # Verdict on rounds-dependence (Test 1)
    if d7_exps and len(d7_exps) >= 3:
        rounds = [int(r[1:]) for r, _ in d7_exps]
        exps = [e for _, e in d7_exps]
        slope_r, _, r_r, p_r, _ = stats.linregress(rounds, exps)

        variation = (max(exps) - min(exps)) / abs(np.mean(exps)) * 100

        print(f"  TEST 1 (spatial-only exponent vs rounds at d=7):")
        print(f"    r50={d7_exps[0][1]:.4f}, r90={d7_exps[1][1]:.4f}, r130={d7_exps[2][1]:.4f}")
        print(f"    Variation: {variation:.1f}%")

        if variation > 30:
            print(f"    VERDICT: Strong rounds-dependence.")
            print(f"    -> FAVORS Candidate 2 (criticality)")
            print(f"    -> DISFAVORS Candidate 3 (topological, expects d-only)")
        elif variation > 15:
            print(f"    VERDICT: Moderate rounds-dependence.")
            print(f"    -> Mild evidence for Candidate 2")
        else:
            print(f"    VERDICT: Exponent stable across rounds.")
            print(f"    -> FAVORS Candidate 3 (topological)")
            print(f"    -> DISFAVORS Candidate 2 (criticality)")

    # d-dependence at fixed rounds
    if r50_exps and len(r50_exps) >= 3:
        d_vals = [int(d[1:]) for d, _ in r50_exps]
        exps = [e for _, e in r50_exps]
        print(f"\n  TEST 1b (spatial-only exponent vs d at fixed r=50):")
        print(f"    d3={exps[0]:.4f}, d5={exps[1]:.4f}, d7={exps[2]:.4f}")

        # Test bulk depth scaling
        bulk_depths = [d / 2 for d in d_vals]
        slope_bd, intercept_bd, r_bd, _, _ = stats.linregress(bulk_depths, exps)
        print(f"    vs bulk depth (d/2): slope={slope_bd:.5f}, R={r_bd:.4f}")
        if abs(r_bd) > 0.95:
            print(f"    -> EXCELLENT fit to bulk depth scaling")

    # Verdict on chains (Test 2)
    print(f"\n  TEST 2 (near-d chain excess):")
    print(f"    See cluster statistics above for each code distance.")
    print(f"    If real/sim ratio of near-d clusters >> 1, chains are the mechanism.")
    print(f"    If ratio ~ 1, chains don't explain the residual.")

    print("\n" + "=" * 70)
