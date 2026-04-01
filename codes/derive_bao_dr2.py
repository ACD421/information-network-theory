#!/usr/bin/env python3
"""
derive_bao_dr2.py  —  Z = pi vs LCDM: DESI DR2 BAO (March 2025)
=================================================================
14 million galaxies, 3 years of data, 13 measurements, 7 redshift bins.
Full covariance matrix from CobayaSampler/bao_data.

Source: arXiv:2503.14738
Data:   github.com/CobayaSampler/bao_data/tree/master/desi_bao_dr2
"""

import numpy as np
import sys, os
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

Z = np.pi
d = 4
N = 3
c_light = 299792.458  # km/s

# Framework parameters
h_fw = 0.657162
Omega_m = 1/Z
Omega_b = 1/(2*Z**2)
Omega_cdm = Omega_m - Omega_b
Omega_k = 1/(32*Z**3)
Omega_L = 1 - 1/Z
tau_fw = 1/(2*Z**2)
n_s_fw = 1 - 1/Z**3
A_s_fw = np.exp(-6*Z)/Z

ombh2_fw = Omega_b * h_fw**2
omch2_fw = Omega_cdm * h_fw**2

# =====================================================================
# DESI DR2 BAO DATA (arXiv:2503.14738, Table IV)
# From CobayaSampler/bao_data/desi_bao_dr2/
# =====================================================================

# Data vector: 13 measurements
# Order: DV(0.295), DM(0.51), DH(0.51), DM(0.706), DH(0.706),
#         DM(0.934), DH(0.934), DM(1.321), DH(1.321),
#         DM(1.484), DH(1.484), DH(2.33), DM(2.33)

dr2_z    = [0.295, 0.510, 0.510, 0.706, 0.706, 0.934, 0.934,
            1.321, 1.321, 1.484, 1.484, 2.330, 2.330]
dr2_type = ['DV/rd','DM/rd','DH/rd','DM/rd','DH/rd','DM/rd','DH/rd',
            'DM/rd','DH/rd','DM/rd','DH/rd','DH/rd','DM/rd']
dr2_val  = np.array([
    7.94167639,     # BGS DV/rd
    13.58758434,    # LRG1 DM/rd
    21.86294686,    # LRG1 DH/rd
    17.35069094,    # LRG2 DM/rd
    19.45534918,    # LRG2 DH/rd
    21.57563956,    # LRG3+ELG1 DM/rd
    17.64149464,    # LRG3+ELG1 DH/rd
    27.60085612,    # ELG2 DM/rd
    14.17602155,    # ELG2 DH/rd
    30.51190063,    # QSO DM/rd
    12.81699964,    # QSO DH/rd
    8.631545674846294,   # Lya DH/rd
    38.988973961958784,  # Lya DM/rd
])
dr2_tracer = ['BGS','LRG1','LRG1','LRG2','LRG2','LRG3+ELG1','LRG3+ELG1',
              'ELG2','ELG2','QSO','QSO','Lya','Lya']

# Full 13x13 covariance matrix (block-diagonal)
dr2_cov = np.zeros((13, 13))
# BGS (1x1)
dr2_cov[0,0] = 5.79e-03
# LRG1 (2x2)
dr2_cov[1,1] = 2.83e-02;  dr2_cov[1,2] = -3.26e-02
dr2_cov[2,1] = -3.26e-02; dr2_cov[2,2] = 1.84e-01
# LRG2 (2x2)
dr2_cov[3,3] = 3.24e-02;  dr2_cov[3,4] = -2.37e-02
dr2_cov[4,3] = -2.37e-02; dr2_cov[4,4] = 1.11e-01
# LRG3+ELG1 (2x2)
dr2_cov[5,5] = 2.62e-02;  dr2_cov[5,6] = -1.13e-02
dr2_cov[6,5] = -1.13e-02; dr2_cov[6,6] = 4.04e-02
# ELG2 (2x2)
dr2_cov[7,7] = 1.05e-01;  dr2_cov[7,8] = -2.90e-02
dr2_cov[8,7] = -2.90e-02; dr2_cov[8,8] = 5.04e-02
# QSO (2x2)
dr2_cov[9,9]   = 5.83e-01;  dr2_cov[9,10]  = -1.95e-01
dr2_cov[10,9]  = -1.95e-01; dr2_cov[10,10] = 2.68e-01
# Lya (2x2) — note order: DH first, then DM in data vector
dr2_cov[11,11] = 1.02e-02;  dr2_cov[11,12] = -2.31e-02
dr2_cov[12,11] = -2.31e-02; dr2_cov[12,12] = 2.83e-01

dr2_icov = np.linalg.inv(dr2_cov)
dr2_err = np.sqrt(np.diag(dr2_cov))

# Also compare with DR1 data for reference
dr1_data = [
    (0.295, 'DV/rd', 7.93, 0.15, 'BGS'),
    (0.510, 'DM/rd', 13.62, 0.25, 'LRG1'),
    (0.510, 'DH/rd', 20.98, 0.61, 'LRG1'),
    (0.706, 'DM/rd', 16.85, 0.32, 'LRG2'),
    (0.706, 'DH/rd', 20.08, 0.60, 'LRG2'),
    (0.930, 'DM/rd', 21.71, 0.28, 'LRG3+ELG1'),
    (0.930, 'DH/rd', 17.88, 0.35, 'LRG3+ELG1'),
    (1.317, 'DM/rd', 27.79, 0.69, 'ELG2'),
    (1.317, 'DH/rd', 13.82, 0.42, 'ELG2'),
    (1.491, 'DM/rd', 30.69, 0.80, 'QSO'),
    (1.491, 'DH/rd', 13.23, 0.55, 'QSO'),
    (2.330, 'DM/rd', 39.71, 0.94, 'Lya'),
    (2.330, 'DH/rd', 8.52, 0.17, 'Lya'),
]

print("=" * 80)
print("  Z = pi FRAMEWORK vs LCDM: DESI DR2 BAO (14M galaxies, 3yr)")
print("=" * 80)

try:
    import camb

    # =====================================================================
    # FRAMEWORK COSMOLOGY
    # =====================================================================
    pars_fw = camb.CAMBparams()

    z_de = np.linspace(0, 10, 500)
    a_de = 1.0/(1.0 + z_de)
    a_de = a_de[::-1]
    z_from_a = 1.0/a_de - 1.0
    w_de = np.array([-1.0 + (1.0/Z)*np.cos(Z*zz) for zz in z_from_a])
    pars_fw.set_dark_energy_w_a(a_de, w_de, dark_energy_model='ppf')
    pars_fw.set_cosmology(ombh2=ombh2_fw, omch2=omch2_fw, H0=None,
        cosmomc_theta=1.04110/100.0, tau=tau_fw, mnu=0.06,
        num_massive_neutrinos=1, nnu=3.046, omk=Omega_k)
    pars_fw.InitPower.set_params(As=A_s_fw, ns=n_s_fw)

    results_fw = camb.get_results(pars_fw)
    derived_fw = results_fw.get_derived_params()
    H0_fw_camb = pars_fw.H0
    rd_fw = derived_fw['rdrag']

    # =====================================================================
    # LCDM (Planck 2018 best-fit)
    # =====================================================================
    pars_lcdm = camb.CAMBparams()
    pars_lcdm.set_cosmology(ombh2=0.02237, omch2=0.1200, H0=67.36,
        tau=0.0544, mnu=0.06, num_massive_neutrinos=1, nnu=3.046)
    pars_lcdm.InitPower.set_params(As=2.1e-9, ns=0.9649)
    results_lcdm = camb.get_results(pars_lcdm)
    derived_lcdm = results_lcdm.get_derived_params()
    rd_lcdm = derived_lcdm['rdrag']

    # =====================================================================
    # COMPUTE PREDICTIONS
    # =====================================================================
    def compute_bao(results, rd, z_eff, mtype):
        DM = results.comoving_radial_distance(z_eff)
        Hz = results.hubble_parameter(z_eff)
        DH = c_light / Hz

        if mtype == 'DV/rd':
            DV = (DM**2 * z_eff * DH)**(1.0/3.0)
            return DV / rd
        elif mtype == 'DM/rd':
            return DM / rd
        elif mtype == 'DH/rd':
            return DH / rd

    # Build prediction vectors
    pred_fw = np.array([compute_bao(results_fw, rd_fw, z, t)
                        for z, t in zip(dr2_z, dr2_type)])
    pred_lcdm = np.array([compute_bao(results_lcdm, rd_lcdm, z, t)
                          for z, t in zip(dr2_z, dr2_type)])

    # =====================================================================
    # CHI-SQUARED WITH FULL COVARIANCE MATRIX
    # =====================================================================
    resid_fw = pred_fw - dr2_val
    resid_lcdm = pred_lcdm - dr2_val

    chi2_fw_full = resid_fw @ dr2_icov @ resid_fw
    chi2_lcdm_full = resid_lcdm @ dr2_icov @ resid_lcdm

    # Also compute diagonal-only chi2 for comparison with DR1 method
    chi2_fw_diag = np.sum((resid_fw / dr2_err)**2)
    chi2_lcdm_diag = np.sum((resid_lcdm / dr2_err)**2)

    N_data = len(dr2_val)

    print(f"\n  COSMOLOGICAL PARAMETERS:")
    print(f"  {'':>20} {'Framework':>14} {'LCDM':>14}")
    print(f"  {'H0 (km/s/Mpc)':>20} {H0_fw_camb:>14.2f} {pars_lcdm.H0:>14.2f}")
    print(f"  {'r_d (Mpc)':>20} {rd_fw:>14.2f} {rd_lcdm:>14.2f}")
    print(f"  {'Omega_m':>20} {Omega_m:>14.5f} {0.3153:>14.5f}")
    print(f"  {'Omega_b':>20} {Omega_b:>14.5f} {0.0493:>14.5f}")
    print(f"  {'w(z=0)':>20} {-1+1/Z:>14.5f} {-1.0:>14.5f}")
    print(f"  {'Omega_k':>20} {Omega_k:>14.6f} {0.0:>14.6f}")

    print(f"\n  DESI DR2 BAO COMPARISON (13 measurements, 7 redshift bins):")
    print(f"  {'z':>6} {'Type':>8} {'Tracer':>12} {'DR2':>10} {'err':>8} {'FW':>10} {'LCDM':>10} {'FW sig':>8} {'LC sig':>8}")
    print(f"  {'-'*6:>6} {'-'*8:>8} {'-'*12:>12} {'-'*10:>10} {'-'*8:>8} {'-'*10:>10} {'-'*10:>10} {'-'*8:>8} {'-'*8:>8}")

    for i in range(N_data):
        sig_fw = resid_fw[i] / dr2_err[i]
        sig_lcdm = resid_lcdm[i] / dr2_err[i]
        print(f"  {dr2_z[i]:>6.3f} {dr2_type[i]:>8} {dr2_tracer[i]:>12} "
              f"{dr2_val[i]:>10.4f} {dr2_err[i]:>8.4f} "
              f"{pred_fw[i]:>10.4f} {pred_lcdm[i]:>10.4f} "
              f"{sig_fw:>+8.2f} {sig_lcdm:>+8.2f}")

    print(f"\n  CHI-SQUARED (full covariance matrix):")
    print(f"  Framework: chi2 = {chi2_fw_full:.2f}  (chi2/N = {chi2_fw_full/N_data:.3f})")
    print(f"  LCDM:      chi2 = {chi2_lcdm_full:.2f}  (chi2/N = {chi2_lcdm_full/N_data:.3f})")
    print(f"  Delta chi2 = {chi2_lcdm_full - chi2_fw_full:+.2f} (positive = FW wins)")
    print(f"  N_data = {N_data}")

    print(f"\n  CHI-SQUARED (diagonal only, for comparison):")
    print(f"  Framework: chi2 = {chi2_fw_diag:.2f}")
    print(f"  LCDM:      chi2 = {chi2_lcdm_diag:.2f}")
    print(f"  Delta chi2 = {chi2_lcdm_diag - chi2_fw_diag:+.2f}")

    # =====================================================================
    # DR1 vs DR2 COMPARISON
    # =====================================================================
    print(f"\n  DR1 vs DR2 SHIFTS:")
    print(f"  {'z':>6} {'Type':>8} {'Tracer':>12} {'DR1':>10} {'DR2':>10} {'Shift':>10} {'DR1 err':>10}")
    print(f"  {'-'*6:>6} {'-'*8:>8} {'-'*12:>12} {'-'*10:>10} {'-'*10:>10} {'-'*10:>10} {'-'*10:>10}")
    for i, (z1, t1, v1, e1, tr1) in enumerate(dr1_data):
        shift = dr2_val[i] - v1
        print(f"  {z1:>6.3f} {t1:>8} {tr1:>12} {v1:>10.4f} {dr2_val[i]:>10.4f} {shift:>+10.4f} {e1:>10.4f}")

    # =====================================================================
    # WHERE FRAMEWORK WINS AND LOSES
    # =====================================================================
    print(f"\n  POINT-BY-POINT WINNER:")
    fw_wins = 0
    lcdm_wins = 0
    for i in range(N_data):
        abs_fw = abs(resid_fw[i] / dr2_err[i])
        abs_lcdm = abs(resid_lcdm[i] / dr2_err[i])
        if abs_fw < abs_lcdm:
            winner = "FW WINS"
            fw_wins += 1
        else:
            winner = "LCDM WINS"
            lcdm_wins += 1
        print(f"  z={dr2_z[i]:.3f} {dr2_type[i]:>8} {dr2_tracer[i]:>12}: "
              f"{winner:>10} (|FW|={abs_fw:.3f}, |LC|={abs_lcdm:.3f} sigma)")
    print(f"\n  Score: Framework {fw_wins}, LCDM {lcdm_wins} (out of {N_data})")

    # =====================================================================
    # w(z) EFFECT ON H(z)
    # =====================================================================
    print(f"\n  DARK ENERGY EQUATION OF STATE EFFECT:")
    print(f"  w(z) = -1 + cos(pi*z)/pi")
    print(f"  {'z':>6} {'w(z)':>10} {'H_FW':>10} {'H_LCDM':>10} {'ratio':>10}")
    for z_check in [0.3, 0.5, 0.7, 0.93, 1.0, 1.3, 1.5, 2.0, 2.33]:
        Hz_fw_v = results_fw.hubble_parameter(z_check)
        Hz_lcdm_v = results_lcdm.hubble_parameter(z_check)
        w_z = -1 + np.cos(Z*z_check)/Z
        print(f"  {z_check:>6.2f} {w_z:>+10.5f} {Hz_fw_v:>10.2f} {Hz_lcdm_v:>10.2f} {Hz_fw_v/Hz_lcdm_v:>10.5f}")

    # =====================================================================
    # DESI DR2 KEY FINDING: 3.1 sigma against LCDM
    # =====================================================================
    print(f"\n  DESI DR2 KEY CONTEXT:")
    print(f"  DESI DR2 itself finds dynamical DE preferred at 3.1 sigma over LCDM")
    print(f"  Their best-fit: w0 = -0.75, wa = -0.75 (CPL parametrization)")
    print(f"  Framework: w(z) = -1 + cos(pi*z)/pi (DERIVED, not fitted)")
    print(f"    w(0) = {-1 + 1/Z:+.5f}")
    print(f"    w(0.5) = {-1 + np.cos(Z*0.5)/Z:+.5f}")
    print(f"    w(1.0) = {-1 + np.cos(Z*1.0)/Z:+.5f}")
    print(f"    w(2.0) = {-1 + np.cos(Z*2.0)/Z:+.5f}")

    # Effective w0, wa approximation of the framework
    # w(z) ~ w0 + wa * z/(1+z) at low z
    # w(0) = -1 + 1/pi = -0.6817 -> w0 ~ -0.68
    # dw/dz at z=0: -sin(pi*0)/pi * pi/pi = 0 -> wa comes from curvature
    # Better: fit w0, wa to the framework w(z) over DESI range
    from scipy.optimize import curve_fit
    z_fit = np.linspace(0, 2.5, 100)
    w_fw_fit = np.array([-1 + np.cos(Z*zz)/Z for zz in z_fit])
    def cpl(z, w0, wa):
        return w0 + wa * z / (1+z)
    popt, _ = curve_fit(cpl, z_fit, w_fw_fit)
    print(f"\n  CPL approximation of framework w(z) over z=[0,2.5]:")
    print(f"    w0_eff = {popt[0]:.4f}")
    print(f"    wa_eff = {popt[1]:.4f}")
    print(f"    DESI DR2 best-fit: w0 ~ -0.75, wa ~ -0.75")

    # =====================================================================
    # FINAL VERDICT
    # =====================================================================
    print(f"\n{'='*80}")
    if chi2_fw_full < chi2_lcdm_full:
        print(f"  FRAMEWORK WINS ON DESI DR2")
    else:
        print(f"  LCDM WINS ON DESI DR2")
    print(f"  Framework chi2 = {chi2_fw_full:.2f}, LCDM chi2 = {chi2_lcdm_full:.2f}")
    print(f"  Delta chi2 = {chi2_lcdm_full - chi2_fw_full:+.2f}")
    print(f"  Framework has 0 free parameters. LCDM has 6.")
    if chi2_fw_full < chi2_lcdm_full:
        # AIC-like comparison
        aic_fw = chi2_fw_full + 2*0  # 0 free params
        aic_lcdm = chi2_lcdm_full + 2*6  # 6 free params (H0, ombh2, omch2, tau, ns, As)
        bic_fw = chi2_fw_full + 0*np.log(N_data)
        bic_lcdm = chi2_lcdm_full + 6*np.log(N_data)
        print(f"\n  Information criteria (BAO only):")
        print(f"  AIC:  FW = {aic_fw:.2f}, LCDM = {aic_lcdm:.2f}, Delta = {aic_lcdm - aic_fw:+.2f}")
        print(f"  BIC:  FW = {bic_fw:.2f}, LCDM = {bic_lcdm:.2f}, Delta = {bic_lcdm - bic_fw:+.2f}")

    print(f"\n  The chain: Z = pi -> Omega_m = 1/pi, Omega_b = 1/(2pi^2)")
    print(f"            -> w(z) = -1 + cos(pi*z)/pi (DERIVED)")
    print(f"            -> h = 0.657162 (self-consistent)")
    print(f"            -> BAO distances vs 14 million galaxies")
    print(f"{'='*80}")

except ImportError:
    print("  CAMB not available — cannot run BAO comparison")
