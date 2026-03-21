"""
Z = pi Framework - BAO Distance Ratio Check
=============================================
BAO measures rs*H(z)/c and D_A(z)/rs - never rs alone.
Check if framework's larger rs is compensated by different H(z).
"""

import numpy as np
import camb
import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PI = np.pi
c_km_s = 299792.458  # km/s

def setup_camb(H0, ombh2, omch2, omk, tau, As, ns, ppf=False):
    pars = camb.CAMBparams()
    pars.set_cosmology(H0=H0, ombh2=ombh2, omch2=omch2, omk=omk,
                       tau=tau, mnu=0.06, nnu=3.046, num_massive_neutrinos=1)
    pars.InitPower.set_params(As=As, ns=ns)
    if ppf:
        a_arr = np.logspace(-4, 0, 500)
        z_arr = 1.0/a_arr - 1.0
        w_arr = -1.0 + (1.0/PI)*np.cos(PI*z_arr)
        pars.set_dark_energy_w_a(a_arr, w_arr, dark_energy_model='ppf')
    pars.set_for_lmax(2600, lens_potential_accuracy=1)
    results = camb.get_results(pars)
    return pars, results


# Framework (PPF, H0=66.47)
h_fw = 66.4702 / 100
ombh2_fw = (1/(2*PI**2)) * h_fw**2
omch2_fw = ((2*PI-1)/(2*PI**2)) * h_fw**2

pars_fw, res_fw = setup_camb(66.4702, ombh2_fw, omch2_fw, 1/(32*PI**3),
                              1/(2*PI**2), np.exp(-6*PI)/PI, 1-1/PI**3, ppf=True)
d_fw = res_fw.get_derived_params()
rdrag_fw = d_fw['rdrag']

# Framework (w=-1, H0=66.47)
pars_fw1, res_fw1 = setup_camb(66.4702, ombh2_fw, omch2_fw, 1/(32*PI**3),
                                1/(2*PI**2), np.exp(-6*PI)/PI, 1-1/PI**3, ppf=False)
d_fw1 = res_fw1.get_derived_params()
rdrag_fw1 = d_fw1['rdrag']

# LCDM best-fit
pars_lcdm, res_lcdm = setup_camb(67.36, 0.02237, 0.1200, 0.0,
                                   0.0544, 2.1e-9, 0.9649, ppf=False)
d_lcdm = res_lcdm.get_derived_params()
rdrag_lcdm = d_lcdm['rdrag']

print("=" * 80)
print("BAO DISTANCE RATIO ANALYSIS")
print("=" * 80)
print(f"\n  Framework rdrag = {rdrag_fw:.2f} Mpc (PPF) / {rdrag_fw1:.2f} Mpc (w=-1)")
print(f"  LCDM rdrag      = {rdrag_lcdm:.2f} Mpc")
print(f"  Ratio FW/LCDM   = {rdrag_fw/rdrag_lcdm:.4f}")

# BAO data points
# Format: (name, z, quantity, value, error)
# DM = comoving angular diameter distance = (1+z)*D_A
# DH = c/H(z)
# DV = [z * DH * DM^2]^(1/3)
bao_data = [
    # SDSS/6dF/MGS - DV/rdrag
    ("6dFGS",     0.106, "DV/rd", 2.976, 0.133),
    ("SDSS MGS",  0.15,  "DV/rd", 4.466, 0.168),
    # BOSS DR12 consensus - DM/rd and DH/rd
    ("BOSS z=0.38", 0.38, "DM/rd", 10.27, 0.15),
    ("BOSS z=0.38", 0.38, "DH/rd", 24.89, 0.58),
    ("BOSS z=0.51", 0.51, "DM/rd", 13.38, 0.18),
    ("BOSS z=0.51", 0.51, "DH/rd", 22.43, 0.48),
    ("BOSS z=0.61", 0.61, "DM/rd", 15.45, 0.20),
    ("BOSS z=0.61", 0.61, "DH/rd", 20.76, 0.43),
    # eBOSS Lyman-alpha
    ("eBOSS Lya",  2.334, "DM/rd", 37.6, 1.9),
    ("eBOSS Lya",  2.334, "DH/rd", 8.86, 0.29),
    # DESI 2024 (first year)
    ("DESI BGS",   0.30, "DV/rd", 7.93, 0.15),
    ("DESI LRG1",  0.51, "DM/rd", 13.62, 0.25),
    ("DESI LRG1",  0.51, "DH/rd", 20.98, 0.61),
    ("DESI LRG2",  0.71, "DM/rd", 16.85, 0.32),
    ("DESI LRG2",  0.71, "DH/rd", 20.08, 0.60),
    ("DESI ELG2",  1.32, "DM/rd", 27.79, 0.69),
    ("DESI ELG2",  1.32, "DH/rd", 13.82, 0.42),
    ("DESI QSO",   1.49, "DM/rd", 26.07, 0.67),  # approximate
    ("DESI QSO",   1.49, "DH/rd", 13.23, 0.55),
    ("DESI Lya",   2.33, "DM/rd", 39.71, 0.94),
    ("DESI Lya",   2.33, "DH/rd", 8.52, 0.17),
]

print("\n" + "-" * 110)
hdr = f"  {'Survey':16s} {'z':>5s} {'Qty':>6s} {'FW(PPF)':>9s} {'FW(w1)':>9s} {'LCDM':>9s} {'Data':>9s} {'err':>6s} {'T(PPF)':>7s} {'T(w1)':>7s} {'T(LCDM)':>8s}"
print(hdr)
print("  " + "-" * 108)

chi2_fw_ppf = 0
chi2_fw_w1 = 0
chi2_lcdm = 0
n_points = 0

for name, z, qty, obs_val, obs_err in bao_data:
    # Compute distances for each model
    # DM = comoving distance (for flat: chi; for curved: f_K(chi))
    # CAMB: angular_diameter_distance gives D_A in Mpc
    # DM = (1+z) * D_A

    DA_fw = res_fw.angular_diameter_distance(z)
    DM_fw = (1+z) * DA_fw
    Hz_fw = res_fw.hubble_parameter(z)
    DH_fw = c_km_s / Hz_fw
    DV_fw = (z * DH_fw * DM_fw**2) ** (1./3.)

    DA_fw1 = res_fw1.angular_diameter_distance(z)
    DM_fw1 = (1+z) * DA_fw1
    Hz_fw1 = res_fw1.hubble_parameter(z)
    DH_fw1 = c_km_s / Hz_fw1
    DV_fw1 = (z * DH_fw1 * DM_fw1**2) ** (1./3.)

    DA_lcdm = res_lcdm.angular_diameter_distance(z)
    DM_lcdm = (1+z) * DA_lcdm
    Hz_lcdm = res_lcdm.hubble_parameter(z)
    DH_lcdm = c_km_s / Hz_lcdm
    DV_lcdm = (z * DH_lcdm * DM_lcdm**2) ** (1./3.)

    if qty == "DM/rd":
        pred_fw = DM_fw / rdrag_fw
        pred_fw1 = DM_fw1 / rdrag_fw1
        pred_lcdm = DM_lcdm / rdrag_lcdm
    elif qty == "DH/rd":
        pred_fw = DH_fw / rdrag_fw
        pred_fw1 = DH_fw1 / rdrag_fw1
        pred_lcdm = DH_lcdm / rdrag_lcdm
    elif qty == "DV/rd":
        pred_fw = DV_fw / rdrag_fw
        pred_fw1 = DV_fw1 / rdrag_fw1
        pred_lcdm = DV_lcdm / rdrag_lcdm

    t_fw = abs(pred_fw - obs_val) / obs_err
    t_fw1 = abs(pred_fw1 - obs_val) / obs_err
    t_lcdm = abs(pred_lcdm - obs_val) / obs_err

    chi2_fw_ppf += ((pred_fw - obs_val) / obs_err)**2
    chi2_fw_w1 += ((pred_fw1 - obs_val) / obs_err)**2
    chi2_lcdm += ((pred_lcdm - obs_val) / obs_err)**2
    n_points += 1

    best = "PPF" if t_fw <= min(t_fw1, t_lcdm) else ("w1" if t_fw1 <= t_lcdm else "LCDM")

    print(f"  {name:16s} {z:5.3f} {qty:>6s} {pred_fw:9.3f} {pred_fw1:9.3f} {pred_lcdm:9.3f} "
          f"{obs_val:9.3f} {obs_err:6.3f} {t_fw:6.2f}s {t_fw1:6.2f}s {t_lcdm:7.2f}s  [{best}]")

print("  " + "-" * 108)
print(f"\n  Total BAO chi2 ({n_points} points):")
print(f"    Framework PPF: {chi2_fw_ppf:.2f}  (chi2/N = {chi2_fw_ppf/n_points:.2f})")
print(f"    Framework w=1: {chi2_fw_w1:.2f}  (chi2/N = {chi2_fw_w1/n_points:.2f})")
print(f"    LCDM:          {chi2_lcdm:.2f}  (chi2/N = {chi2_lcdm/n_points:.2f})")

dchi2_ppf = chi2_fw_ppf - chi2_lcdm
dchi2_w1 = chi2_fw_w1 - chi2_lcdm
print(f"\n    Dchi2 (PPF vs LCDM): {dchi2_ppf:+.2f}")
print(f"    Dchi2 (w1 vs LCDM):  {dchi2_w1:+.2f}")

# Show the compensation effect
print("\n" + "=" * 80)
print("THE COMPENSATION EFFECT")
print("=" * 80)

for z in [0.38, 0.51, 0.61, 1.0, 2.33]:
    DA_fw = res_fw.angular_diameter_distance(z)
    DM_fw = (1+z) * DA_fw
    Hz_fw = res_fw.hubble_parameter(z)

    DA_lcdm = res_lcdm.angular_diameter_distance(z)
    DM_lcdm = (1+z) * DA_lcdm
    Hz_lcdm = res_lcdm.hubble_parameter(z)

    # Show how rs*H(z)/c = DH/rdrag works
    rsHz_fw = rdrag_fw * Hz_fw / c_km_s
    rsHz_lcdm = rdrag_lcdm * Hz_lcdm / c_km_s

    DM_rd_fw = DM_fw / rdrag_fw
    DM_rd_lcdm = DM_lcdm / rdrag_lcdm

    print(f"\n  z = {z}:")
    print(f"    rd*H(z)/c:  FW(PPF) = {rsHz_fw:.4f}  LCDM = {rsHz_lcdm:.4f}  ratio = {rsHz_fw/rsHz_lcdm:.4f}")
    print(f"    DM/rd:      FW(PPF) = {DM_rd_fw:.4f}  LCDM = {DM_rd_lcdm:.4f}  ratio = {DM_rd_fw/DM_rd_lcdm:.4f}")
    print(f"    H(z):       FW(PPF) = {Hz_fw:.2f}    LCDM = {Hz_lcdm:.2f}    ratio = {Hz_fw/Hz_lcdm:.4f}")
    print(f"    DM:         FW(PPF) = {DM_fw:.2f}    LCDM = {DM_lcdm:.2f}    ratio = {DM_fw/DM_lcdm:.4f}")

print("\nDone.")
