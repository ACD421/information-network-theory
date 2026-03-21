"""
Z = pi Framework - Full Planck Likelihood Validation
=====================================================
CAMB v1.6.5 + Planck 2018 likelihoods (native Python)

Likelihoods evaluated:
  - plik_lite_native TTTEEE (high-ell, l=30-2508, foreground-marginalized)
  - Commander TT (low-ell, l=2-29, Gibbs-based native)
  - SimAll EE (low-ell, l=2-29, simulation-based native)
"""

import numpy as np
import camb
import os
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PI = np.pi
PACKAGES_PATH = "C:/Users/andre/cosmology_data"

# ============================================================
# Z = pi FRAMEWORK PARAMETERS (from paper Section G)
# ============================================================
Omega_m   = 1.0 / PI          # 0.31831
f_b       = 1.0 / (2 * PI)    # baryon fraction
Omega_b   = Omega_m * f_b     # Omega_b = 1/(2*pi^2)
Omega_cdm = Omega_m * (1 - f_b)
Omega_k   = 1.0 / (32 * PI**3)  # 0.00101
tau_fw    = 1.0 / (2 * PI**2)   # 0.05066
n_s_fw    = 1.0 - 1.0 / PI**3   # 0.96775
A_s_fw    = np.exp(-6 * PI) / PI # 2.073e-9

# Paper's H0 (analytical from theta* = 1.04110)
H0_paper = 66.4702
# theta* target from Planck 2018
theta_star = 0.0104110

# LCDM best-fit (Planck 2018 TT,TE,EE+lowE)
H0_lcdm    = 67.36
ombh2_lcdm = 0.02237
omch2_lcdm = 0.1200
tau_lcdm   = 0.0544
ns_lcdm    = 0.9649
As_lcdm    = 2.100e-9


def run_camb(ombh2, omch2, tau_val, ns_val, As_val,
             omega_k=0.0, H0=None, cosmomc_theta=None,
             use_ppf_wz=False, label="model"):
    """Run CAMB with either H0 or cosmomc_theta as anchor."""
    t0 = time.time()
    pars = camb.CAMBparams()

    cosmo_kwargs = dict(
        ombh2=ombh2, omch2=omch2, omk=omega_k,
        tau=tau_val, mnu=0.06, nnu=3.046, num_massive_neutrinos=1
    )
    if cosmomc_theta is not None:
        cosmo_kwargs['cosmomc_theta'] = cosmomc_theta
    else:
        cosmo_kwargs['H0'] = H0

    pars.set_cosmology(**cosmo_kwargs)
    pars.InitPower.set_params(As=As_val, ns=ns_val, r=0)

    if use_ppf_wz:
        a_arr = np.logspace(-4, 0, 500)
        z_arr = 1.0 / a_arr - 1.0
        w_arr = -1.0 + (1.0 / PI) * np.cos(PI * z_arr)
        pars.set_dark_energy_w_a(a_arr, w_arr, dark_energy_model='ppf')
    else:
        pars.set_dark_energy(w=-1.0)

    pars.set_for_lmax(2600, lens_potential_accuracy=1)
    pars.WantTransfer = True
    pars.set_matter_power(redshifts=[0])

    results = camb.get_results(pars)
    powers = results.get_cmb_power_spectra(pars, CMB_unit='muK')
    totCL = powers['total']
    lensCL = powers['lens_potential']  # [L(L+1)]^2/(2pi) * C_L^{pp}

    derived = results.get_derived_params()
    sigma8 = float(np.squeeze(results.get_sigma8()))
    H0_out = pars.H0

    dt = time.time() - t0
    print(f"  [{label}] {dt:.1f}s | H0={H0_out:.4f} theta*={derived['thetastar']:.5f} "
          f"rs={derived['rstar']:.2f} z*={derived['zstar']:.2f} "
          f"zdrag={derived['zdrag']:.2f} zeq={derived['zeq']:.1f} "
          f"s8={sigma8:.4f}")

    return totCL, lensCL, results, derived, sigma8


# ============================================================
# RUN CAMB
# ============================================================
print("=" * 72)
print("Z = pi FRAMEWORK - PLANCK LIKELIHOOD VALIDATION")
print(f"CAMB v{camb.__version__}")
print("=" * 72)

# Compute physical densities from framework
h_paper = H0_paper / 100.0
ombh2_fw = Omega_b * h_paper**2
omch2_fw = Omega_cdm * h_paper**2

print(f"\n  Framework physical densities:")
print(f"    Omega_b  = 1/(2*pi^2) = {Omega_b:.6f}")
print(f"    Omega_c  = (2*pi-1)/(2*pi^2) = {Omega_cdm:.6f}")
print(f"    Omega_m  = 1/pi = {Omega_m:.6f}")
print(f"    Omega_k  = 1/(32*pi^3) = {Omega_k:.6f}")
print(f"    tau      = 1/(2*pi^2) = {tau_fw:.6f}")
print(f"    n_s      = 1-1/pi^3 = {n_s_fw:.6f}")
print(f"    A_s      = exp(-6*pi)/pi = {A_s_fw:.4e}")
print(f"    omb*h2   = {ombh2_fw:.6f}")
print(f"    omc*h2   = {omch2_fw:.6f}")

models = {}

# Model 1: Framework anchored to theta* = 1.04110 with w=-1
# (Paper footnote [4]: low-ell uses w=-1 approximation)
print(f"\n--- Framework anchored to theta*={theta_star} (w=-1) ---")
models["FW-theta"] = run_camb(ombh2_fw, omch2_fw, tau_fw, n_s_fw, A_s_fw,
                               omega_k=Omega_k, cosmomc_theta=theta_star,
                               use_ppf_wz=False, label="FW-theta*")

# Model 2: Framework with H0=66.47 and w=-1
print(f"\n--- Framework H0={H0_paper} (w=-1) ---")
models["FW-H0-w1"] = run_camb(ombh2_fw, omch2_fw, tau_fw, n_s_fw, A_s_fw,
                                omega_k=Omega_k, H0=H0_paper,
                                use_ppf_wz=False, label="FW-H0-w1")

# Model 3: Framework with H0=66.47 and PPF w(z)
print(f"\n--- Framework H0={H0_paper} (PPF) ---")
models["FW-H0-PPF"] = run_camb(ombh2_fw, omch2_fw, tau_fw, n_s_fw, A_s_fw,
                                 omega_k=Omega_k, H0=H0_paper,
                                 use_ppf_wz=True, label="FW-H0-PPF")

# Model 4: Framework anchored to theta* = 1.04110 with PPF w(z)
print(f"\n--- Framework anchored to theta*={theta_star} (PPF) ---")
models["FW-theta-PPF"] = run_camb(ombh2_fw, omch2_fw, tau_fw, n_s_fw, A_s_fw,
                                    omega_k=Omega_k, cosmomc_theta=theta_star,
                                    use_ppf_wz=True, label="FW-theta*-PPF")

# LCDM best-fit
print(f"\n--- LCDM best-fit ---")
models["LCDM"] = run_camb(ombh2_lcdm, omch2_lcdm, tau_lcdm,
                           ns_lcdm, As_lcdm, omega_k=0.0,
                           H0=H0_lcdm, use_ppf_wz=False, label="LCDM")


# ============================================================
# LOW-ELL LIKELIHOODS
# ============================================================
print("\n" + "=" * 72)
print("LOW-ELL LIKELIHOODS")
print("=" * 72)

# Commander TT
from cobaya.likelihoods.planck_2018_lowl.TT import TT as CommanderTT
cmd = CommanderTT({"packages_path": PACKAGES_PATH})

print("\n  Commander TT (l=2-29):")
cmd_results = {}
for name in models:
    logL = cmd.log_likelihood(models[name][0][:, 0])
    cmd_results[name] = logL
    chi2 = -2 * logL
    print(f"    {name:20s}  logL = {logL:10.4f}  chi2 = {chi2:8.2f}")

# SimAll EE
from cobaya.likelihoods.planck_2018_lowl.EE import EE as SimAllEE
sim = SimAllEE({"packages_path": PACKAGES_PATH})

print("\n  SimAll EE (l=2-29):")
sim_results = {}
for name in models:
    logL = sim.log_likelihood(models[name][0][:, 1])
    sim_results[name] = logL
    chi2 = -2 * logL
    print(f"    {name:20s}  logL = {logL:10.4f}  chi2 = {chi2:8.2f}")


# ============================================================
# LENSING: Planck 2018 CMB-marginalized
# ============================================================
print("\n" + "=" * 72)
print("LENSING: Planck 2018 (CMB-marginalized, 9 bins)")
print("=" * 72)

from cobaya.likelihoods.planck_2018_lensing import CMBMarged as LensCMBMarged
lens = LensCMBMarged({"packages_path": PACKAGES_PATH})

lens_results = {}
for name in models:
    dls_pp = {'pp': models[name][1][:2501, 0]}
    logL = lens.log_likelihood(dls_pp)
    chi2 = -2 * logL
    lens_results[name] = logL
    print(f"    {name:20s}  logL = {logL:10.4f}  chi2 = {chi2:8.2f}")


# ============================================================
# HIGH-ELL: plik_lite_native TTTEEE
# ============================================================
print("\n" + "=" * 72)
print("HIGH-ELL: plik_lite_native TTTEEE (l=30-2508)")
print("=" * 72)

plik_results = {}
try:
    from cobaya.likelihoods.base_classes.planck_pliklite import PlanckPlikLite

    plik = object.__new__(PlanckPlikLite)
    plik.path = os.path.join(PACKAGES_PATH, "data", "planck_2018_pliklite_native")
    plik.dataset_file = "plik_lite_v22.dataset"
    plik.dataset_params = {"use_cl": "tt te ee"}
    plik.calibration_param = "A_planck"

    dataset_path = os.path.join(plik.path, plik.dataset_file)
    plik.load_dataset_file(dataset_path, plik.dataset_params)

    print(f"  Loaded: {plik.nbins} bins, lmax={plik.lmax}")

    for name in models:
        cls = models[name][0]
        chi2 = plik.get_chi_squared(0, cls[:, 0], cls[:, 3], cls[:, 1])
        logL = -0.5 * chi2
        plik_results[name] = logL
        print(f"    {name:20s}  chi2 = {chi2:10.2f}  logL = {logL:10.2f}")

    plik_ok = True
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback; traceback.print_exc()
    plik_ok = False


# ============================================================
# HIGH-ELL: CamSpec2021 TTTEEE (unbinned)
# ============================================================
print("\n" + "=" * 72)
print("HIGH-ELL: CamSpec2021 TTTEEE (unbinned, l=30-2500)")
print("=" * 72)

cs_results = {}
try:
    from cobaya.likelihoods.planck_2018_highl_CamSpec2021.TTTEEE import TTTEEE as CamSpecTTTEEE

    cs = CamSpecTTTEEE({"packages_path": PACKAGES_PATH})

    n_data = cs.data_vector.shape[0]
    print(f"  Loaded: {n_data} data points, spectra: {cs.use_cl}")
    print(f"  Nspec={cs.Nspec}, used_sizes={cs.used_sizes}")

    # CamSpec2021 foreground params: use_fg_residual_model=0 (powerlaw only)
    # Best-fit values from Planck 2018 CamSpec analysis
    cs_fg_params = {
        "use_fg_residual_model": 0,
        "A_planck": 1.0,
        "cal0": 1.0,
        "cal2": 1.0,
        "calTE": 1.0,
        "calEE": 1.0,
        "amp_100": 0.0,
        "amp_143": 10.0,
        "amp_217": 20.0,
        "amp_143x217": 10.0,
        "n_100": 1.0,
        "n_143": 1.0,
        "n_217": 1.0,
        "n_143x217": 1.0,
    }

    for name in models:
        cls = models[name][0]
        chi2 = cs.chi_squared(cls[:, 0], cls[:, 3], cls[:, 1], cs_fg_params)
        logL = -0.5 * chi2
        cs_results[name] = logL
        print(f"    {name:20s}  chi2 = {chi2:10.2f}  logL = {logL:10.2f}")

    cs_ok = True
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback; traceback.print_exc()
    cs_ok = False


# ============================================================
# DELTA-CHI2 SUMMARY
# ============================================================
print("\n" + "=" * 72)
print("DELTA-CHI2 vs LCDM")
print("  Positive = LCDM fits better, Negative = Framework fits better")
print("=" * 72)

for fw_name in ["FW-theta", "FW-theta-PPF", "FW-H0-w1", "FW-H0-PPF"]:
    print(f"\n  === {fw_name} vs LCDM ===")

    dchi2_cmd = -2 * (cmd_results[fw_name] - cmd_results["LCDM"])
    dchi2_sim = -2 * (sim_results[fw_name] - sim_results["LCDM"])
    dchi2_lens = -2 * (lens_results[fw_name] - lens_results["LCDM"])
    print(f"    Commander TT:     Dchi2 = {dchi2_cmd:+8.3f}  [{'FW' if dchi2_cmd < 0 else 'LCDM'}]")
    print(f"    SimAll EE:        Dchi2 = {dchi2_sim:+8.3f}  [{'FW' if dchi2_sim < 0 else 'LCDM'}]")
    print(f"    Lensing (CMBmrg): Dchi2 = {dchi2_lens:+8.3f}  [{'FW' if dchi2_lens < 0 else 'LCDM'}]")

    total_lowl = dchi2_cmd + dchi2_sim + dchi2_lens

    if plik_ok and fw_name in plik_results:
        dchi2_plik = -2 * (plik_results[fw_name] - plik_results["LCDM"])
        print(f"    plik_lite TTTEEE: Dchi2 = {dchi2_plik:+8.3f}  [{'FW' if dchi2_plik < 0 else 'LCDM'}]")
        total = total_lowl + dchi2_plik
        print(f"    TOTAL (plik_lite):Dchi2 = {total:+8.3f}")

    if cs_ok and fw_name in cs_results:
        dchi2_cs = -2 * (cs_results[fw_name] - cs_results["LCDM"])
        print(f"    CamSpec2021:      Dchi2 = {dchi2_cs:+8.3f}  [{'FW' if dchi2_cs < 0 else 'LCDM'}]")
        total_cs = total_lowl + dchi2_cs
        print(f"    TOTAL (CamSpec):  Dchi2 = {total_cs:+8.3f}")


# ============================================================
# BIC COMPARISON
# ============================================================
print("\n" + "=" * 72)
print("BIC COMPARISON")
print("=" * 72)

N = 680  # effective data points (plik 613 + low-ell 58 + lensing 9)
lnN = np.log(N)
k_lcdm = 6  # H0, omb, omc, tau, ns, As
k_fw = 1    # H0 from theta* (all others derived from pi)

fw_name = "FW-theta"
for hi_label, hi_results, hi_ok in [("plik_lite", plik_results, plik_ok),
                                      ("CamSpec2021", cs_results, cs_ok)]:
    if not hi_ok or fw_name not in hi_results:
        continue
    print(f"\n  {fw_name} vs LCDM ({hi_label} + Commander + SimAll + Lensing):")

    total_logL_fw = hi_results[fw_name] + cmd_results[fw_name] + sim_results[fw_name] + lens_results[fw_name]
    total_logL_lcdm = hi_results["LCDM"] + cmd_results["LCDM"] + sim_results["LCDM"] + lens_results["LCDM"]

    chi2_fw = -2 * total_logL_fw
    chi2_lcdm = -2 * total_logL_lcdm

    bic_fw = chi2_fw + k_fw * lnN
    bic_lcdm = chi2_lcdm + k_lcdm * lnN
    dbic = bic_lcdm - bic_fw

    print(f"    LCDM:      chi2 = {chi2_lcdm:.2f}, k={k_lcdm}, BIC = {bic_lcdm:.2f}")
    print(f"    Framework: chi2 = {chi2_fw:.2f}, k={k_fw}, BIC = {bic_fw:.2f}")
    print(f"    DBIC = {dbic:+.1f} ({'Framework' if dbic > 0 else 'LCDM'} preferred)")

    if abs(dbic) > 10:
        scale = "DECISIVE"
    elif abs(dbic) > 6:
        scale = "STRONG"
    elif abs(dbic) > 2:
        scale = "POSITIVE"
    else:
        scale = "Inconclusive"
    odds = np.exp(abs(dbic)/2)
    print(f"    Jeffreys: {scale} | Odds: {odds:.0f}:1")


# ============================================================
# PAPER CROSS-CHECK
# ============================================================
print("\n" + "=" * 72)
print("PAPER CROSS-CHECK (im2(4).html)")
print("=" * 72)

# Use theta*-anchored model for comparison
fw_key = "FW-theta"
der_fw = models[fw_key][3]
s8_fw = models[fw_key][4]

print(f"\n  Using model: {fw_key}")
print(f"  Paper derived parameters vs this run:")
print(f"    {'Param':12s} {'Paper':>10s} {'This run':>10s} {'Delta':>10s}")
paper = {
    'theta*': (1.04110, der_fw['thetastar']),
    'H0':     (66.47, models[fw_key][2].hubble_parameter(0)),
    'r_s': (144.88, der_fw.get('rstar', 0)),
    'r_drag': (147.55, der_fw.get('rdrag', 0)),
    'z_eq': (3361.5, der_fw.get('zeq', 0)),
    'z*': (1089.77, der_fw.get('zstar', 0)),
    'z_drag': (1059.85, der_fw.get('zdrag', 0)),
    'sigma8': (0.7767, s8_fw),
}
for name, (p, c) in paper.items():
    print(f"    {name:12s} {p:10.4f} {c:10.4f} {c-p:+10.4f}")

# Paper's claimed chi2 values
if plik_ok:
    print(f"\n  Paper plik TTTEEE claims: LCDM chi2=2395.53, FW chi2=2402.26, Dchi2=+6.73")
    dchi2_plik = -2 * (plik_results[fw_key] - plik_results["LCDM"])
    print(f"  plik_lite (this run):    LCDM chi2={-2*plik_results['LCDM']:.2f}, "
          f"FW chi2={-2*plik_results[fw_key]:.2f}, Dchi2={dchi2_plik:+.2f}")
    print(f"  NOTE: plik_lite != full plik (lite is foreground-marginalized, 613 bins vs ~750+)")

    print(f"\n  Paper Commander TT: Dchi2 = -1.11")
    dchi2_cmd = -2 * (cmd_results[fw_key] - cmd_results["LCDM"])
    print(f"  This run:           Dchi2 = {dchi2_cmd:+.3f}")

    print(f"\n  Paper SimAll EE: Dchi2 = -0.39")
    dchi2_sim = -2 * (sim_results[fw_key] - sim_results["LCDM"])
    print(f"  This run:        Dchi2 = {dchi2_sim:+.3f}")

print("\nDone.")
