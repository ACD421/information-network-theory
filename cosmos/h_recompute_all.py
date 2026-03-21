#!/usr/bin/env python3
"""
h_recompute_all.py  —  Complete recomputation of ALL h-dependent paper tables
with self-consistent h (PPF + theta* iteration) vs paper h = 0.66470.

Covers:
  §3  Eight Predictions table
  §6  Planck Likelihood Results (chi2)
  §7  CAMB Derived Parameters table
  §8  S8 tension, sound horizon
  §G  Complete Parameter Summary
  §C.8 Fuzzy Sphere Distance Correction
  BIC  Bayesian Information Criterion

All 27 particle physics predictions are h-INDEPENDENT (pure geometry)
and are listed but NOT recomputed (they don't change).

Author: Claude Code for Andrew Dorman
"""

import sys, math, json, time, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import numpy as np

PI = math.pi

# =============================================================
# FRAMEWORK CONSTANTS (h-independent, from d=4, Z=π)
# =============================================================
Omega_m   = 1.0 / PI                        # 0.31831
f_b       = 1.0 / (2*PI)                    # 0.15915
Omega_b   = 1.0 / (2*PI**2)                 # 0.05066
Omega_c   = (2*PI - 1) / (2*PI**2)          # 0.26764
Omega_k   = 1.0 / (32*PI**3)                # 0.00101
Omega_L   = 1.0 - Omega_m - Omega_k         # ~0.68068
tau_fw    = 1.0 / (2*PI**2)                 # 0.05066
n_s_fw    = 1.0 - 1.0/PI**3                 # 0.96775
A_s_fw    = math.exp(-6*PI) / PI             # 2.073e-9
w0_fw     = -1.0 + 1.0/PI                   # -0.6817
theta_star = 0.0104110                       # Planck anchor

# Fuzzy sphere distance correction
FUZZY_FACTOR = 323.0 / 324.0                 # 1 - 1/324

# Paper's h value
h_paper = 0.664702
# Self-consistent h (from iteration with PPF)
h_self  = 0.657162

print("=" * 90)
print("  Z = π FRAMEWORK: COMPLETE h-DEPENDENT RECOMPUTATION")
print("  Paper h = {:.6f}  vs  Self-consistent h = {:.6f}  (Δh = {:.4f}, {:.2f}%)".format(
    h_paper, h_self, h_paper - h_self, 100*(h_paper-h_self)/h_paper))
print("=" * 90)

# =============================================================
# PART 0: h-INDEPENDENT quantities (no recomputation needed)
# =============================================================
print("\n" + "─"*90)
print("PART 0: h-INDEPENDENT PREDICTIONS — THESE DO NOT CHANGE")
print("─"*90)

h_independent = [
    ("Ωm",            "1/π",           0.31831,  "0.3153 ± 0.0073",  0.41),
    ("fb",            "1/(2π)",        0.15915,  "0.1571 ± 0.0020",  1.03),
    ("Ωk",            "1/(32π³)",      0.00101,  "0.0007 ± 0.0019",  0.16),
    ("τ",             "1/(2π²)",       0.05066,  "0.0544 ± 0.0073",  0.51),
    ("ns",            "1 − 1/π³",      0.96775,  "0.9649 ± 0.0042",  0.68),
    ("As",            "e^(-6π)/π",     2.073e-9, "(2.10±0.03)×10⁻⁹", 0.90),
    ("w₀",            "−1 + 1/π",     -0.6817,  "−0.75 ± 0.07",     0.98),
    ("Vus",           "sin(1/π)/√2 corr", 0.22516, "0.2250 ± 0.0008", 0.20),
    ("Vud",           "√(1−Vus²−Vub²)", 0.97431, "0.97373 ± 0.00031", 1.89),
    ("λ_Higgs",       "(π/24)(1−1/9π²)", 0.12943, "0.12938 ± 0.00005", 0.92),
    ("mH",            "v√((9π²−1)/(108π))", 125.27, "125.25 ± 0.17 GeV", 0.12),
    ("1/α₁",          "RG × cos(1/π)", 59.07,   "59.02 ± 0.35",     0.14),
    ("1/α₂",          "RG × 1",       29.62,   "29.58 ± 0.05",     0.83),
    ("1/α₃",          "RG × cos(1/π)", 8.89,    "8.48 ± 0.42",      0.98),
    ("sin²θW",        "breathing corr", 0.23129, "0.23122 ± 0.00004", 1.75),
    ("sin²θ₁₂",      "1/3 − 1/(12π)", 0.30681, "0.307 ± 0.013",    0.01),
    ("sin²θ₂₃",      "1/2 + 1/(2π²)", 0.55066, "0.546 ± 0.021",    0.22),
    ("sin²θ₁₃",      "sin²(1/π)·(π²−1)/(4π²)", 0.02201, "0.02203 ± 0.00056", 0.04),
    ("δ_CKM",         "π(1/3+sin²β/2)−1/(6π)", 65.78, "65.5° ± 2.8°", 0.10),
    ("mμ",            "breathing sphere", 105.68, "105.658 ± ~1%", 0.02),
    ("me",            "breathing sphere", 0.5096, "0.5110 ± ~1%",  0.27),
    ("mb",            "GJ + QCD",      2.701,   "2.839 ± ~0.09",   1.53),
    ("ms",            "(mμ/3) × η_s", 93.4,    "93.4 ± 8.4 MeV",  0.00),
    ("md",            "3me × η_d",    4.62,    "4.67 ± 0.48 MeV", 0.10),
    ("Δm²₂₁",        "seesaw t₀²",   7.67e-5, "(7.53±0.16)×10⁻⁵", 0.87),
    ("|Δm²₃₂|",      "seesaw t₀²",   2.452e-3,"(2.453±0.033)×10⁻³", 0.04),
    ("mu(2GeV)",      "2me × η_u",    2.15,    "2.16 ± 0.49 MeV", 0.02),
    ("mc(mc)",        "n·mμ × η_c",   1.264,   "1.270 ± 0.020 GeV", 0.30),
    ("A_Wolf",        "√(1−1/π)",     0.8257,  "0.826 ± 0.015",   0.02),
    ("ρ̄",            "1/(2π)",        0.15915, "0.159 ± 0.010",   0.02),
    ("|Vcb|",         "Aλ²",          0.04186, "0.04182 ± 0.00085", 0.04),
    ("|Vub|",         "Aλ³(ρ̄²+η̄²)^½", 0.00366, "0.00369 ± 0.00011", 0.31),
    ("|Vtd|",         "Aλ³|1−ρ̄−iη̄|", 0.00860, "0.00857 ± 0.00020", 0.15),
    ("δ_PMNS",        "3π/2−δ_CKM",   204.2,   "197° ± 24°",      0.30),
]

chi2_indep = sum(t[4]**2 for t in h_independent)
print(f"\n  {len(h_independent)} predictions, all purely geometric (d=4, Z=π, β=1/π, N=3)")
print(f"  Sum of σ² = {chi2_indep:.2f}")
print(f"  These are SAFE regardless of h.\n")

for name, formula, pred, obs, sigma in h_independent[:8]:
    print(f"  {name:12s} = {pred:<14}  obs: {obs:<25s}  {sigma:.2f}σ  ✓")
print(f"  ... and {len(h_independent)-8} more particle physics predictions (all unchanged)")

# =============================================================
# PART 1: h-DEPENDENT physical densities
# =============================================================
print("\n" + "─"*90)
print("PART 1: h-DEPENDENT PHYSICAL DENSITIES")
print("─"*90)

def compute_physical_densities(h):
    ombh2 = Omega_b * h**2
    omch2 = Omega_c * h**2
    omh2  = Omega_m * h**2
    return ombh2, omch2, omh2

ombh2_p, omch2_p, omh2_p = compute_physical_densities(h_paper)
ombh2_s, omch2_s, omh2_s = compute_physical_densities(h_self)

print(f"\n  {'Quantity':15s}  {'Paper (h={:.5f})':>22s}  {'Self-con (h={:.5f})':>22s}  {'Δ':>10s}  {'Δ%':>8s}")
print(f"  {'─'*15}  {'─'*22}  {'─'*22}  {'─'*10}  {'─'*8}")
print(f"  {'H₀':15s}  {h_paper*100:22.4f}  {h_self*100:22.4f}  {(h_paper-h_self)*100:+10.4f}  {100*(h_paper-h_self)/h_paper:+8.3f}%")
print(f"  {'ωb = Ωbh²':15s}  {ombh2_p:22.5f}  {ombh2_s:22.5f}  {ombh2_p-ombh2_s:+10.5f}  {100*(ombh2_p-ombh2_s)/ombh2_p:+8.3f}%")
print(f"  {'ωc = Ωch²':15s}  {omch2_p:22.5f}  {omch2_s:22.5f}  {omch2_p-omch2_s:+10.5f}  {100*(omch2_p-omch2_s)/omch2_p:+8.3f}%")
print(f"  {'ωm = Ωmh²':15s}  {omh2_p:22.5f}  {omh2_s:22.5f}  {omh2_p-omh2_s:+10.5f}  {100*(omh2_p-omh2_s)/omh2_p:+8.3f}%")

# Planck observed values for comparison
ombh2_planck = 0.02237
omch2_planck = 0.1200
print(f"\n  Planck best-fit: ωb = {ombh2_planck}, ωc = {omch2_planck}")
print(f"  Paper  vs Planck: Δωb = {ombh2_p - ombh2_planck:+.5f}, Δωc = {omch2_p - omch2_planck:+.5f}")
print(f"  Self-c vs Planck: Δωb = {ombh2_s - ombh2_planck:+.5f}, Δωc = {omch2_s - omch2_planck:+.5f}")

# =============================================================
# PART 2: CAMB DERIVED PARAMETERS
# =============================================================
print("\n" + "─"*90)
print("PART 2: CAMB DERIVED PARAMETERS (requires CAMB)")
print("─"*90)

try:
    import camb
    HAS_CAMB = True
    print("  CAMB v{} loaded".format(camb.__version__))
except ImportError:
    HAS_CAMB = False
    print("  WARNING: CAMB not available. Using analytic approximations only.")

def run_camb(ombh2, omch2, tau, ns, As, omega_k, cosmomc_theta, use_ppf=False, label=""):
    """Run CAMB and return results dict with all derived parameters."""
    pars = camb.CAMBparams()

    # PPF BEFORE set_cosmology
    if use_ppf:
        a_arr = np.logspace(-4, 0, 500)
        z_arr = 1.0/a_arr - 1.0
        w_arr = -1.0 + (1.0/PI)*np.cos(PI*z_arr)
        pars.set_dark_energy_w_a(a_arr, w_arr, dark_energy_model='ppf')

    pars.set_cosmology(
        ombh2=ombh2, omch2=omch2, omk=omega_k,
        tau=tau, cosmomc_theta=cosmomc_theta,
        mnu=0.06, nnu=3.046, num_massive_neutrinos=1
    )
    pars.InitPower.set_params(As=As, ns=ns)
    pars.set_for_lmax(2600, lens_potential_accuracy=1)
    pars.set_matter_power(redshifts=[0.0], kmax=2.0)
    pars.WantTransfer = True

    results = camb.get_results(pars)
    derived = results.get_derived_params()

    H0 = results.Params.H0           # Not in derived dict
    r_s_camb = derived['rstar']      # sound horizon at z*
    r_drag_camb = derived['rdrag']    # drag horizon
    z_star = derived['zstar']
    z_drag = derived['zdrag']
    z_eq   = derived['zeq']
    sigma8 = results.get_sigma8_0()

    # Fuzzy sphere correction
    r_s_phys = r_s_camb * FUZZY_FACTOR
    r_drag_phys = r_drag_camb * FUZZY_FACTOR

    # S8
    S8 = sigma8 * math.sqrt(Omega_m / 0.3)

    # Get power spectra for chi2
    totCL = results.get_cmb_power_spectra(params=pars, CMB_unit='muK', raw_cl=False)['total']
    lensCL = results.get_cmb_power_spectra(params=pars, CMB_unit='muK', raw_cl=False)['lens_potential']

    return {
        'label': label,
        'H0': H0,
        'h': H0/100.0,
        'ombh2': ombh2,
        'omch2': omch2,
        'r_s_camb': r_s_camb,
        'r_s_phys': r_s_phys,
        'r_drag_camb': r_drag_camb,
        'r_drag_phys': r_drag_phys,
        'z_star': z_star,
        'z_drag': z_drag,
        'z_eq': z_eq,
        'sigma8': sigma8,
        'S8': S8,
        'totCL': totCL,
        'lensCL': lensCL,
    }

if HAS_CAMB:
    print("\n  Running CAMB for paper parameters (h={:.5f}, w=-1+cos/π PPF)...".format(h_paper))
    t0 = time.time()
    res_paper = run_camb(
        ombh2=ombh2_p, omch2=omch2_p, tau=tau_fw, ns=n_s_fw, As=A_s_fw,
        omega_k=Omega_k, cosmomc_theta=theta_star, use_ppf=True, label="Paper"
    )
    print(f"    Done in {time.time()-t0:.1f}s. CAMB returned H0={res_paper['H0']:.4f}")

    print(f"  Running CAMB for self-consistent parameters (h={h_self:.5f}, PPF)...")
    t0 = time.time()
    res_self = run_camb(
        ombh2=ombh2_s, omch2=omch2_s, tau=tau_fw, ns=n_s_fw, As=A_s_fw,
        omega_k=Omega_k, cosmomc_theta=theta_star, use_ppf=True, label="Self-consistent"
    )
    print(f"    Done in {time.time()-t0:.1f}s. CAMB returned H0={res_self['H0']:.4f}")

    # Also run LCDM for comparison
    print(f"  Running CAMB for ΛCDM (Planck best-fit)...")
    t0 = time.time()
    res_lcdm = run_camb(
        ombh2=0.02237, omch2=0.1200, tau=0.0544, ns=0.9649, As=2.10e-9,
        omega_k=0.0, cosmomc_theta=0.0104092, use_ppf=False, label="LCDM"
    )
    print(f"    Done in {time.time()-t0:.1f}s. CAMB returned H0={res_lcdm['H0']:.4f}")

    # =============================================================
    # §7 TABLE: CAMB DERIVED PARAMETERS
    # =============================================================
    print("\n" + "─"*90)
    print("§7 TABLE RECOMPUTATION: CAMB Derived Parameters (Geometrically Corrected)")
    print("─"*90)

    # Planck observed values with uncertainties
    obs = {
        'theta_star': (1.04110, 0.00031),
        'r_s':        (144.43, 0.26),
        'r_drag':     (147.09, 0.26),
        'z_eq':       (3387, 21),
        'z_star':     (1089.92, 0.25),
        'z_drag':     (1059.94, 0.30),
        'sigma8_lcdm': (0.8111, 0.006),
        'S8_lens':    (0.776, 0.017),
    }

    def tension(pred, obs_val, obs_err):
        return abs(pred - obs_val) / obs_err if obs_err > 0 else 0

    print(f"\n  {'Quantity':12s}  {'Paper':>12s}  {'Self-con':>12s}  {'ΛCDM':>12s}  {'Planck Obs':>18s}  {'σ(paper)':>10s}  {'σ(self)':>10s}  {'VIOLATION':>10s}")
    print(f"  {'─'*12}  {'─'*12}  {'─'*12}  {'─'*12}  {'─'*18}  {'─'*10}  {'─'*10}  {'─'*10}")

    rows = [
        ("100θ*", theta_star*100, theta_star*100, 1.04092, obs['theta_star'][0], obs['theta_star'][1]),
        ("r_s (Mpc)", res_paper['r_s_phys'], res_self['r_s_phys'], res_lcdm['r_s_camb'], obs['r_s'][0], obs['r_s'][1]),
        ("r_drag (Mpc)", res_paper['r_drag_phys'], res_self['r_drag_phys'], res_lcdm['r_drag_camb'], obs['r_drag'][0], obs['r_drag'][1]),
        ("z_eq", res_paper['z_eq'], res_self['z_eq'], res_lcdm['z_eq'], obs['z_eq'][0], obs['z_eq'][1]),
        ("z*", res_paper['z_star'], res_self['z_star'], res_lcdm['z_star'], obs['z_star'][0], obs['z_star'][1]),
        ("z_drag", res_paper['z_drag'], res_self['z_drag'], res_lcdm['z_drag'], obs['z_drag'][0], obs['z_drag'][1]),
        ("σ₈", res_paper['sigma8'], res_self['sigma8'], res_lcdm['sigma8'], obs['sigma8_lcdm'][0], obs['sigma8_lcdm'][1]),
        ("S₈", res_paper['S8'], res_self['S8'], res_lcdm['S8'], obs['S8_lens'][0], obs['S8_lens'][1]),
    ]

    for name, val_p, val_s, val_l, obs_v, obs_e in rows:
        t_p = tension(val_p, obs_v, obs_e)
        t_s = tension(val_s, obs_v, obs_e)
        # Mark violations > 2σ
        flag = "!!!" if t_s > 2.0 else ("*" if t_s > 1.5 else "")
        if name == "σ₈":
            # σ₈ comparison is tricky (see paper note)
            print(f"  {name:12s}  {val_p:12.4f}  {val_s:12.4f}  {val_l:12.4f}  {obs_v:.4f} ± {obs_e:.4f}†  {t_p:10.2f}σ  {t_s:10.2f}σ  {flag}")
        elif name == "100θ*":
            print(f"  {name:12s}  {val_p:12.5f}  {val_s:12.5f}  {val_l:12.5f}  {obs_v:.5f} ± {obs_e:.5f}  {t_p:10.2f}σ  {t_s:10.2f}σ  {flag}")
        elif "z_" in name or name in ("z*", "z_eq"):
            print(f"  {name:12s}  {val_p:12.1f}  {val_s:12.1f}  {val_l:12.1f}  {obs_v:.1f} ± {obs_e:.1f}      {t_p:10.2f}σ  {t_s:10.2f}σ  {flag}")
        else:
            print(f"  {name:12s}  {val_p:12.2f}  {val_s:12.2f}  {val_l:12.2f}  {obs_v:.2f} ± {obs_e:.2f}      {t_p:10.2f}σ  {t_s:10.2f}σ  {flag}")

    print(f"\n  † σ₈ Planck value is ΛCDM-derived (see paper §7 note). Direct comparison: S₈ from lensing.")

    # =============================================================
    # §3 TABLE: H₀ row update
    # =============================================================
    print("\n" + "─"*90)
    print("§3 TABLE UPDATE: H₀ Prediction")
    print("─"*90)

    H0_obs = 67.37
    H0_err = 0.54
    H0_paper_pred = h_paper * 100
    H0_self_pred = res_self['H0']

    t_paper = tension(H0_paper_pred, H0_obs, H0_err)
    t_self  = tension(H0_self_pred, H0_obs, H0_err)

    print(f"\n  Paper:     H₀ = {H0_paper_pred:.2f} km/s/Mpc  (obs {H0_obs} ± {H0_err})  → {t_paper:.2f}σ")
    print(f"  Self-con:  H₀ = {H0_self_pred:.2f} km/s/Mpc  (obs {H0_obs} ± {H0_err})  → {t_self:.2f}σ")
    print(f"  VIOLATION: H₀ tension goes from {t_paper:.2f}σ → {t_self:.2f}σ")

    # =============================================================
    # §C.8: FUZZY SPHERE DISTANCE CORRECTION
    # =============================================================
    print("\n" + "─"*90)
    print("§C.8 RECOMPUTATION: Fuzzy Sphere Distance Correction")
    print("─"*90)

    print(f"\n  {'':30s}  {'Paper h':>14s}  {'Self-con h':>14s}")
    print(f"  {'─'*30}  {'─'*14}  {'─'*14}")
    print(f"  {'r_s(CAMB)':30s}  {res_paper['r_s_camb']:14.2f}  {res_self['r_s_camb']:14.2f}")
    print(f"  {'r_s(corrected) = CAMB×323/324':30s}  {res_paper['r_s_phys']:14.2f}  {res_self['r_s_phys']:14.2f}")
    print(f"  {'r_drag(CAMB)':30s}  {res_paper['r_drag_camb']:14.2f}  {res_self['r_drag_camb']:14.2f}")
    print(f"  {'r_drag(corrected)':30s}  {res_paper['r_drag_phys']:14.2f}  {res_self['r_drag_phys']:14.2f}")

    t_rs_p = tension(res_paper['r_s_phys'], 144.43, 0.26)
    t_rs_s = tension(res_self['r_s_phys'], 144.43, 0.26)
    t_rd_p = tension(res_paper['r_drag_phys'], 147.09, 0.26)
    t_rd_s = tension(res_self['r_drag_phys'], 147.09, 0.26)

    print(f"\n  r_s tension:    paper {t_rs_p:.2f}σ  →  self-con {t_rs_s:.2f}σ")
    print(f"  r_drag tension: paper {t_rd_p:.2f}σ  →  self-con {t_rd_s:.2f}σ")

    if t_rs_s > 2.0 or t_rd_s > 2.0:
        print(f"  *** VIOLATION: Sound horizon / drag horizon now in > 2σ tension! ***")

    # =============================================================
    # §6: PLANCK LIKELIHOOD — plik chi2 comparison
    # =============================================================
    print("\n" + "─"*90)
    print("§6 RECOMPUTATION: Planck Likelihood (plik chi2)")
    print("─"*90)

    # Try to compute plik chi2
    try:
        sys.path.insert(0, 'C:/Users/andre/Claudius')
        from clipy import ClikPlik
        HAS_PLIK = True
    except:
        HAS_PLIK = False

    if HAS_PLIK:
        print("  Loading plik likelihood...")
        plik = ClikPlik()

        # Planck 2018 best-fit nuisance parameters
        nuis_bestfit = [
            243.83, 29.54, 54.49, 29.43, 6.89, 6.34, 1.65, 6.95,
            1.62, 10.45, 8.63, 2.70, 3.10, 0.999, 0.9981, 0.99625,
            100.03, 1.0002, 1.021, 0.9999, 1.0005, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0
        ]

        def compute_plik_chi2(totCL, label):
            """Compute plik chi2 from CAMB power spectra."""
            lmax = min(totCL.shape[0] - 1, 2508)
            n_ell = lmax + 1

            # Build plik vector: [TT(0..2508), EE(0..2508), TE(0..2508), 47 nuisance]
            vec = np.zeros(3 * n_ell + 47)
            vec[0:n_ell] = totCL[:n_ell, 0]        # TT
            vec[n_ell:2*n_ell] = totCL[:n_ell, 1]  # EE
            vec[2*n_ell:3*n_ell] = totCL[:n_ell, 3] # TE
            vec[3*n_ell:3*n_ell+47] = nuis_bestfit

            chi2 = -2.0 * plik(vec)
            return chi2

        chi2_paper = compute_plik_chi2(res_paper['totCL'], "Paper")
        chi2_self  = compute_plik_chi2(res_self['totCL'], "Self-consistent")
        chi2_lcdm  = compute_plik_chi2(res_lcdm['totCL'], "LCDM")

        print(f"\n  {'Model':25s}  {'plik χ²':>12s}  {'Δχ² vs ΛCDM':>14s}")
        print(f"  {'─'*25}  {'─'*12}  {'─'*14}")
        print(f"  {'ΛCDM (6 free params)':25s}  {chi2_lcdm:12.2f}  {'ref':>14s}")
        print(f"  {'FW-PPF paper h':25s}  {chi2_paper:12.2f}  {chi2_paper-chi2_lcdm:+14.2f}")
        print(f"  {'FW-PPF self-con h':25s}  {chi2_self:12.2f}  {chi2_self-chi2_lcdm:+14.2f}")

        dchi2_paper = chi2_paper - chi2_lcdm
        dchi2_self  = chi2_self - chi2_lcdm

        print(f"\n  Paper claimed Δχ²(plik) = +6.73")
        print(f"  Paper h gives:  Δχ²(plik) = {dchi2_paper:+.2f}")
        print(f"  Self-con gives: Δχ²(plik) = {dchi2_self:+.2f}")

        if dchi2_self > 20:
            print(f"  *** MAJOR VIOLATION: plik Δχ² increased by {dchi2_self-dchi2_paper:+.1f} ***")

        # =============================================================
        # BIC RECALCULATION
        # =============================================================
        print("\n" + "─"*90)
        print("BIC RECALCULATION")
        print("─"*90)

        N_data = 671
        lnN = math.log(N_data)

        # The paper uses "information-content" chi2 (without covariance log-det)
        # For ΔBIC we need the same basis. Use the absolute chi2 difference.
        # Paper: ΛCDM χ²_info = 1013.0, FW χ²_info = 1019.9
        # Our delta should be relative

        k_lcdm = 6
        k_fw = 1

        # CMB-only BIC
        print(f"\n  CMB-only BIC (N = {N_data}, ln(N) = {lnN:.3f}):")

        # Paper values
        bic_lcdm_paper = 1013.0 + k_lcdm * lnN  # Paper's info chi2
        bic_fw_paper   = 1019.9 + k_fw * lnN

        # Self-consistent: add the delta chi2 from self-consistent
        chi2_info_fw_self = 1019.9 + (dchi2_self - dchi2_paper)  # adjust for actual chi2 change
        bic_fw_self = chi2_info_fw_self + k_fw * lnN

        print(f"\n  {'':30s}  {'Paper':>14s}  {'Self-con':>14s}")
        print(f"  {'─'*30}  {'─'*14}  {'─'*14}")
        print(f"  {'ΛCDM BIC':30s}  {bic_lcdm_paper:14.1f}  {bic_lcdm_paper:14.1f}")
        print(f"  {'FW BIC':30s}  {bic_fw_paper:14.1f}  {bic_fw_self:14.1f}")
        print(f"  {'ΔBIC (FW preferred if +)':30s}  {bic_lcdm_paper - bic_fw_paper:+14.1f}  {bic_lcdm_paper - bic_fw_self:+14.1f}")

        dbic_self = bic_lcdm_paper - bic_fw_self
        if dbic_self < 0:
            print(f"\n  *** VIOLATION: ΔBIC flips NEGATIVE ({dbic_self:+.1f}). ΛCDM now preferred! ***")
        elif dbic_self < 10:
            print(f"\n  *** WARNING: ΔBIC dropped below 'decisive' threshold ({dbic_self:+.1f} < 10) ***")
        else:
            print(f"\n  ΔBIC still in 'decisive' range ({dbic_self:+.1f} > 10)")

    else:
        print("  plik not available. Estimating from previous results...")
        print(f"  From previous h-iteration runs:")
        print(f"    FW self-consistent plik χ² ≈ 2402.44")
        print(f"    ΛCDM plik χ² ≈ 2344.62")
        print(f"    Δχ²(plik) ≈ +57.82")
        print(f"    With lowl: Δχ²(total) ≈ +56.97")
        print(f"  *** MAJOR VIOLATION: plik penalty increased from +6.73 to ~+58 ***")

        dchi2_self_est = 56.97
        chi2_info_fw_self_est = 1019.9 + (dchi2_self_est - 5.23)
        bic_fw_self_est = chi2_info_fw_self_est + 1 * math.log(671)
        bic_lcdm = 1013.0 + 6 * math.log(671)
        dbic_est = bic_lcdm - bic_fw_self_est
        print(f"\n  Estimated ΔBIC: {dbic_est:+.1f}")

    # =============================================================
    # §8: S₈ TENSION RESOLUTION
    # =============================================================
    print("\n" + "─"*90)
    print("§8 RECOMPUTATION: S₈ Tension Resolution")
    print("─"*90)

    S8_lens = 0.776
    S8_lens_err = 0.017
    S8_lcdm = res_lcdm['S8']
    S8_paper = res_paper['S8']
    S8_self  = res_self['S8']

    t_s8_lcdm = tension(S8_lcdm, S8_lens, S8_lens_err)
    t_s8_paper = tension(S8_paper, S8_lens, S8_lens_err)
    t_s8_self  = tension(S8_self, S8_lens, S8_lens_err)

    print(f"\n  {'Model':25s}  {'S₈':>8s}  {'vs lensing':>12s}")
    print(f"  {'─'*25}  {'─'*8}  {'─'*12}")
    print(f"  {'ΛCDM':25s}  {S8_lcdm:.4f}  {t_s8_lcdm:.2f}σ")
    print(f"  {'FW-PPF paper h':25s}  {S8_paper:.4f}  {t_s8_paper:.2f}σ")
    print(f"  {'FW-PPF self-con h':25s}  {S8_self:.4f}  {t_s8_self:.2f}σ")

    print(f"\n  Paper claimed: FW S₈ = 0.807 (1.84σ), ΛCDM = 0.832 (3.3σ)")
    print(f"  Paper claimed FW resolves S₈ tension. Does self-consistent h still resolve it?")
    if t_s8_self < t_s8_lcdm:
        print(f"  ✓ YES: self-con FW ({t_s8_self:.2f}σ) still better than ΛCDM ({t_s8_lcdm:.2f}σ)")
    else:
        print(f"  ✗ NO: self-con FW ({t_s8_self:.2f}σ) worse than ΛCDM ({t_s8_lcdm:.2f}σ)")

else:
    # No CAMB — use analytic estimates
    print("\n  [Analytic approximations without CAMB]")

    # Approximate z_eq from omega_m * h^2 / omega_r
    omega_r = 4.15e-5 / (0.6727**2)  # radiation density parameter

    for label, h_val, ombh2, omch2 in [("Paper", h_paper, ombh2_p, omch2_p),
                                         ("Self-con", h_self, ombh2_s, omch2_s)]:
        omh2 = ombh2 + omch2
        z_eq_approx = omh2 / (4.15e-5 * (1 + 0.2271 * 3.046 * (7/8) * (4/11)**(4/3))) / (h_val**2)
        print(f"\n  {label}: ωb={ombh2:.5f}, ωc={omch2:.5f}, ωm={omh2:.5f}")
        print(f"    z_eq ≈ {omh2 / 4.15e-5:.1f} (rough)")

# =============================================================
# PART 3: COMPREHENSIVE IMPACT SUMMARY
# =============================================================
print("\n" + "="*90)
print("  COMPREHENSIVE IMPACT SUMMARY")
print("="*90)

print("""
┌─────────────────────────────────────────────────────────────────────┐
│                    WHAT SURVIVES (h-INDEPENDENT)                    │
├─────────────────────────────────────────────────────────────────────┤
│  27 particle physics predictions:  ALL SAFE                        │
│    CKM: Vus, Vud, Vcb, Vub, Vtd, Vts, Vcs, Vcd, Vtb  (9 elems) │
│    PMNS: sin²θ₁₂, sin²θ₂₃, sin²θ₁₃, δ_PMNS          (4 angles)│
│    Higgs: mH = 125.27 GeV, λ = π/24−1/(216π)          (2 values)│
│    Gauge: 1/α₁, 1/α₂, 1/α₃, sin²θW                   (4 values)│
│    Masses: mμ, me, mb, ms, md, mu, mc                   (7 masses)│
│    Neutrinos: Δm²₂₁, |Δm²₃₂|                          (2 split.) │
│                                                                     │
│  7 cosmological RATIOS (h-independent):                             │
│    Ωm = 1/π, fb = 1/(2π), Ωk = 1/(32π³)                          │
│    τ = 1/(2π²), ns = 1−1/π³, As = e^(-6π)/π                      │
│    w₀ = −1+1/π                                                     │
│                                                                     │
│  Total safe: 34 of 35 predictions                                  │
├─────────────────────────────────────────────────────────────────────┤
│                   WHAT IS DAMAGED (h-DEPENDENT)                     │
├─────────────────────────────────────────────────────────────────────┤
│  1. H₀: 66.47 → 65.72  (tension 1.67σ → ~3.1σ)                   │
│  2. ωb = Ωb·h²: 0.02238 → 0.02188  (2.3% lower)                  │
│  3. ωc = Ωc·h²: 0.11826 → 0.11559  (2.3% lower)                  │
│  4. r_s, r_drag: CAMB values shift (different ωb, ωc)             │
│  5. z_eq: shifts (depends on ωm)                                   │
│  6. σ₈, S₈: shift (growth history changes)                        │
│  7. CMB χ²: plik penalty ~+58 (was +6.73)                         │
│  8. BIC: may flip or drop below decisive                           │
│                                                                     │
│  ROOT CAUSE: PPF w(z) ≠ w=-1 in θ*→H₀ mapping.                   │
│  Paper used h=0.66470 (w=-1 calibration) but PPF shifts H₀ down.  │
│  Self-consistent iteration: h converges to 0.65716.                │
└─────────────────────────────────────────────────────────────────────┘
""")

# =============================================================
# PART 4: CAN THE FRAMEWORK BE SAVED?
# =============================================================
print("─"*90)
print("PART 4: POSSIBLE REMEDIES")
print("─"*90)

print("""
  OPTION A: The fuzzy sphere correction applies to the θ*→H₀ mapping
    If D_A gets the 1−1/324 correction but r_s does NOT (or vice versa),
    then θ* = r_s/D_A would shift, changing the H₀ calibration.
    The paper assumes BOTH get the same factor → θ* unchanged.
    If only D_A is corrected: θ*_eff shifts, potentially recovering h=0.6647.
    STATUS: Would require modifying §C.8 cross-check (ii).

  OPTION B: The PPF w(z) should NOT enter the θ* calibration
    If the paper's intent is that H₀ is calibrated from θ* with w=-1
    (the monopole), and PPF is a post-hoc perturbation that does NOT
    modify the background calibration, then h=0.66470 is correct.
    The PPF breathing mode affects LATE-TIME observables only.
    STATUS: Physically arguable if monopole/dipole separation holds.
    But CAMB's C_ℓ must still use the FULL w(z) → inconsistency.

  OPTION C: Redefine ωb, ωc as framework constants, not h-dependent
    If ωb = 1/(2π²)·h_paper² and ωc = [(2π-1)/(2π²)]·h_paper² are
    the GEOMETRIC predictions (fixed by Z=π + θ* calibration at w=-1),
    then the self-consistent h only affects H₀, not the densities.
    The C_ℓ would be computed with paper densities + PPF → H₀ floats.
    STATUS: Changes the derivation chain at §G.

  OPTION D: Accept the damage, recompute everything
    Publish with h=0.65716. H₀ = 65.72 (3.1σ from Planck, but closer
    to SH0ES tension midpoint). ωb, ωc shift 2.3%. CMB fit degrades
    significantly. BIC advantage may survive if χ² penalty < ~50.
    STATUS: Honest but painful. The 34/35 particle physics predictions
    remain untouched.
""")

# =============================================================
# PART 5: FULL 35-PREDICTION RECALCULATED χ²
# =============================================================
print("─"*90)
print("PART 5: RECALCULATED TOTAL χ²/dof (with self-consistent h)")
print("─"*90)

# H₀ tension changes
if HAS_CAMB:
    H0_self_actual = res_self['H0']
else:
    H0_self_actual = h_self * 100

t_H0_new = abs(H0_self_actual - H0_obs) / H0_err

# Update the chi2 sum: remove old H₀ tension, add new
chi2_paper_total = 19.22  # Paper's total chi2 over 35 predictions
H0_old_sigma = 1.67
chi2_without_H0 = chi2_paper_total - H0_old_sigma**2
chi2_new_total = chi2_without_H0 + t_H0_new**2

print(f"\n  Paper total χ² = {chi2_paper_total:.2f} (35 predictions)")
print(f"  Paper H₀ contribution: {H0_old_sigma:.2f}² = {H0_old_sigma**2:.2f}")
print(f"  Self-con H₀: {H0_self_actual:.2f} km/s/Mpc → {t_H0_new:.2f}σ → σ² = {t_H0_new**2:.2f}")
print(f"\n  New total χ² = {chi2_paper_total:.2f} - {H0_old_sigma**2:.2f} + {t_H0_new**2:.2f} = {chi2_new_total:.2f}")
print(f"  New χ²/dof = {chi2_new_total:.2f}/35 = {chi2_new_total/35:.3f}")

from scipy.stats import chi2 as chi2_dist
p_paper = 1.0 - chi2_dist.cdf(chi2_paper_total, 35)
p_new = 1.0 - chi2_dist.cdf(chi2_new_total, 35)
print(f"\n  Paper p-value: {p_paper:.4f}")
print(f"  New p-value:   {p_new:.4f}")

if chi2_new_total / 35 < 1.0:
    print(f"\n  χ²/dof = {chi2_new_total/35:.3f} < 1.0 → framework still fits better than chance")
else:
    print(f"\n  *** χ²/dof = {chi2_new_total/35:.3f} > 1.0 → fit quality degraded ***")

# =============================================================
# WRITE RESULTS TO FILE
# =============================================================
results_file = "C:/Users/andre/Claudius/h_recompute_results.json"
output = {
    'h_paper': h_paper,
    'h_self': h_self,
    'delta_h_percent': 100*(h_paper - h_self)/h_paper,
    'ombh2_paper': ombh2_p,
    'ombh2_self': ombh2_s,
    'omch2_paper': omch2_p,
    'omch2_self': omch2_s,
    'H0_paper': h_paper * 100,
    'H0_self': H0_self_actual,
    'H0_tension_paper': float(H0_old_sigma),
    'H0_tension_self': float(t_H0_new),
    'chi2_total_paper': chi2_paper_total,
    'chi2_total_self': float(chi2_new_total),
    'chi2_dof_paper': chi2_paper_total / 35,
    'chi2_dof_self': float(chi2_new_total / 35),
    'p_value_paper': float(p_paper),
    'p_value_self': float(p_new),
    'n_safe_predictions': 34,
    'n_damaged_predictions': 1,
    'damaged': ['H0 (direct), plus CAMB-derived: r_s, r_drag, z_eq, sigma8, S8, CMB chi2'],
}

if HAS_CAMB:
    output.update({
        'r_s_paper': res_paper['r_s_phys'],
        'r_s_self': res_self['r_s_phys'],
        'r_drag_paper': res_paper['r_drag_phys'],
        'r_drag_self': res_self['r_drag_phys'],
        'z_eq_paper': res_paper['z_eq'],
        'z_eq_self': res_self['z_eq'],
        'sigma8_paper': res_paper['sigma8'],
        'sigma8_self': res_self['sigma8'],
        'S8_paper': res_paper['S8'],
        'S8_self': res_self['S8'],
    })

with open(results_file, 'w') as f:
    json.dump(output, f, indent=2)
print(f"\n  Results saved to {results_file}")

print("\n" + "="*90)
print("  DONE. See above for complete h-dependent recomputation.")
print("="*90)
