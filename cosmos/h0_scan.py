"""
Z = pi Framework - H0 Profile Likelihood Scan
==============================================
Scan H0 with all other params locked to pi.
Find the H0 that minimizes total Planck chi2.
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

# Framework parameters (all from pi)
Omega_b   = 1.0 / (2 * PI**2)
Omega_cdm = (2*PI - 1) / (2 * PI**2)
Omega_k   = 1.0 / (32 * PI**3)
tau_fw    = 1.0 / (2 * PI**2)
n_s_fw    = 1.0 - 1.0 / PI**3
A_s_fw    = np.exp(-6 * PI) / PI

# Load likelihoods
print("Loading likelihoods...")
from cobaya.likelihoods.planck_2018_lowl.TT import TT as CommanderTT
from cobaya.likelihoods.planck_2018_lowl.EE import EE as SimAllEE
from cobaya.likelihoods.planck_2018_lensing import CMBMarged as LensCMBMarged
from cobaya.likelihoods.base_classes.planck_pliklite import PlanckPlikLite
from cobaya.likelihoods.planck_2018_highl_CamSpec2021.TTTEEE import TTTEEE as CamSpecTTTEEE

cmd = CommanderTT({"packages_path": PACKAGES_PATH})
sim = SimAllEE({"packages_path": PACKAGES_PATH})
lens = LensCMBMarged({"packages_path": PACKAGES_PATH})

# plik_lite manual init
plik = object.__new__(PlanckPlikLite)
plik.path = os.path.join(PACKAGES_PATH, "data", "planck_2018_pliklite_native")
plik.dataset_file = "plik_lite_v22.dataset"
plik.dataset_params = {"use_cl": "tt te ee"}
plik.calibration_param = "A_planck"
plik.load_dataset_file(os.path.join(plik.path, plik.dataset_file), plik.dataset_params)

# CamSpec2021
cs = CamSpecTTTEEE({"packages_path": PACKAGES_PATH})
cs_fg_params = {
    "use_fg_residual_model": 0,
    "A_planck": 1.0, "cal0": 1.0, "cal2": 1.0, "calTE": 1.0, "calEE": 1.0,
    "amp_100": 0.0, "amp_143": 10.0, "amp_217": 20.0, "amp_143x217": 10.0,
    "n_100": 1.0, "n_143": 1.0, "n_217": 1.0, "n_143x217": 1.0,
}

print("Likelihoods loaded.\n")

# LCDM reference
print("Running LCDM reference...")
pars_lcdm = camb.CAMBparams()
pars_lcdm.set_cosmology(H0=67.36, ombh2=0.02237, omch2=0.1200, tau=0.0544,
                         mnu=0.06, nnu=3.046, num_massive_neutrinos=1)
pars_lcdm.InitPower.set_params(As=2.1e-9, ns=0.9649)
pars_lcdm.set_for_lmax(2600, lens_potential_accuracy=1)
pars_lcdm.WantTransfer = True
pars_lcdm.set_matter_power(redshifts=[0])
res_lcdm = camb.get_results(pars_lcdm)
pow_lcdm = res_lcdm.get_cmb_power_spectra(pars_lcdm, CMB_unit='muK')

chi2_lcdm_cmd = -2 * cmd.log_likelihood(pow_lcdm['total'][:, 0])
chi2_lcdm_sim = -2 * sim.log_likelihood(pow_lcdm['total'][:, 1])
chi2_lcdm_lens = -2 * lens.log_likelihood({'pp': pow_lcdm['lens_potential'][:2501, 0]})
chi2_lcdm_plik = plik.get_chi_squared(0, pow_lcdm['total'][:, 0],
                                        pow_lcdm['total'][:, 3],
                                        pow_lcdm['total'][:, 1])
chi2_lcdm_cs = cs.chi_squared(pow_lcdm['total'][:, 0], pow_lcdm['total'][:, 3],
                               pow_lcdm['total'][:, 1], cs_fg_params)

print(f"  LCDM: cmd={chi2_lcdm_cmd:.2f} sim={chi2_lcdm_sim:.2f} "
      f"lens={chi2_lcdm_lens:.2f} plik={chi2_lcdm_plik:.2f} cs={chi2_lcdm_cs:.2f}")
chi2_lcdm_total_plik = chi2_lcdm_cmd + chi2_lcdm_sim + chi2_lcdm_lens + chi2_lcdm_plik
chi2_lcdm_total_cs = chi2_lcdm_cmd + chi2_lcdm_sim + chi2_lcdm_lens + chi2_lcdm_cs
print(f"  LCDM total (plik): {chi2_lcdm_total_plik:.2f}")
print(f"  LCDM total (CS21): {chi2_lcdm_total_cs:.2f}")


# H0 scan
print("\n" + "=" * 72)
print("H0 PROFILE LIKELIHOOD SCAN")
print("=" * 72)

H0_values = np.arange(64.0, 72.1, 0.25)
results_scan = []

for H0 in H0_values:
    h = H0 / 100.0
    ombh2 = Omega_b * h**2
    omch2 = Omega_cdm * h**2

    try:
        pars = camb.CAMBparams()
        pars.set_cosmology(H0=H0, ombh2=ombh2, omch2=omch2, omk=Omega_k,
                           tau=tau_fw, mnu=0.06, nnu=3.046, num_massive_neutrinos=1)
        pars.InitPower.set_params(As=A_s_fw, ns=n_s_fw)
        pars.set_for_lmax(2600, lens_potential_accuracy=1)
        pars.WantTransfer = True
        pars.set_matter_power(redshifts=[0])

        res = camb.get_results(pars)
        powers = res.get_cmb_power_spectra(pars, CMB_unit='muK')
        derived = res.get_derived_params()
        sigma8 = float(np.squeeze(res.get_sigma8()))

        totCL = powers['total']
        lensCL = powers['lens_potential']

        c2_cmd = -2 * cmd.log_likelihood(totCL[:, 0])
        c2_sim = -2 * sim.log_likelihood(totCL[:, 1])
        c2_lens = -2 * lens.log_likelihood({'pp': lensCL[:2501, 0]})
        c2_plik = plik.get_chi_squared(0, totCL[:, 0], totCL[:, 3], totCL[:, 1])
        c2_cs = cs.chi_squared(totCL[:, 0], totCL[:, 3], totCL[:, 1], cs_fg_params)

        total_plik = c2_cmd + c2_sim + c2_lens + c2_plik
        total_cs = c2_cmd + c2_sim + c2_lens + c2_cs

        row = {
            'H0': H0, 'theta': derived['thetastar'], 's8': sigma8,
            'cmd': c2_cmd, 'sim': c2_sim, 'lens': c2_lens,
            'plik': c2_plik, 'cs': c2_cs,
            'total_plik': total_plik, 'total_cs': total_cs,
        }
        results_scan.append(row)

        print(f"  H0={H0:6.2f} | theta*={derived['thetastar']:.5f} s8={sigma8:.4f} | "
              f"cmd={c2_cmd:7.2f} sim={c2_sim:7.2f} lens={c2_lens:6.2f} "
              f"plik={c2_plik:8.2f} cs={c2_cs:10.2f} | "
              f"tot_plik={total_plik:8.2f} tot_cs={total_cs:10.2f}")

    except Exception as e:
        print(f"  H0={H0:6.2f} | FAILED: {e}")


# Find best H0
print("\n" + "=" * 72)
print("BEST-FIT H0")
print("=" * 72)

arr = results_scan
best_plik = min(arr, key=lambda r: r['total_plik'])
best_cs = min(arr, key=lambda r: r['total_cs'])
best_cmd = min(arr, key=lambda r: r['cmd'])
best_sim = min(arr, key=lambda r: r['sim'])
best_lens = min(arr, key=lambda r: r['lens'])

print(f"\n  Best H0 (Commander TT):    {best_cmd['H0']:.2f}  chi2={best_cmd['cmd']:.2f}")
print(f"  Best H0 (SimAll EE):       {best_sim['H0']:.2f}  chi2={best_sim['sim']:.2f}")
print(f"  Best H0 (Lensing):         {best_lens['H0']:.2f}  chi2={best_lens['lens']:.2f}")
print(f"  Best H0 (plik_lite):       {min(arr, key=lambda r: r['plik'])['H0']:.2f}")
print(f"  Best H0 (CamSpec2021):     {min(arr, key=lambda r: r['cs'])['H0']:.2f}")

print(f"\n  Best H0 (total w/ plik):   {best_plik['H0']:.2f}")
print(f"    theta* = {best_plik['theta']:.5f}")
print(f"    sigma8 = {best_plik['s8']:.4f}")
print(f"    chi2   = {best_plik['total_plik']:.2f}")
print(f"    Dchi2 vs LCDM = {best_plik['total_plik'] - chi2_lcdm_total_plik:+.2f}")

print(f"\n  Best H0 (total w/ CS21):   {best_cs['H0']:.2f}")
print(f"    theta* = {best_cs['theta']:.5f}")
print(f"    sigma8 = {best_cs['s8']:.4f}")
print(f"    chi2   = {best_cs['total_cs']:.2f}")
print(f"    Dchi2 vs LCDM = {best_cs['total_cs'] - chi2_lcdm_total_cs:+.2f}")

# BIC at best-fit
lnN = np.log(680)
for label, best, lcdm_total in [("plik_lite", best_plik, chi2_lcdm_total_plik),
                                  ("CamSpec2021", best_cs, chi2_lcdm_total_cs)]:
    chi2_key = 'total_plik' if 'plik' in label else 'total_cs'
    bic_fw = best[chi2_key] + 1 * lnN
    bic_lcdm = lcdm_total + 6 * lnN
    dbic = bic_lcdm - bic_fw
    print(f"\n  BIC ({label}) at best H0={best['H0']:.2f}:")
    print(f"    LCDM BIC = {bic_lcdm:.2f}")
    print(f"    FW   BIC = {bic_fw:.2f}")
    print(f"    DBIC = {dbic:+.1f} ({'Framework' if dbic > 0 else 'LCDM'})")

print("\nDone.")
