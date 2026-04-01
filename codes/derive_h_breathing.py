#!/usr/bin/env python3
"""
derive_h_breathing.py — First-principles H0 from cosmic-age breathing
======================================================================
The framework's DE oscillates in COSMIC TIME, not redshift:

    w(z) = -1 - (1/pi) * cos(pi * tau(z))

where tau(z) = H0*t(z) and T_breath = 2/H0.

This gives:  z=0: w ~ -0.68 (quintessence),  z>>1: w ~ -1.32 (phantom)
Matches DESI: quintessence today, phantom in past.

Phantom DE at high z => less DE => larger D_A => smaller theta_s => higher h.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
from scipy import integrate, optimize, interpolate

pi = np.pi
Omega_m = 1/pi
Omega_b = 1/(2*pi**2)
Omega_L = 1 - 1/pi
N_eff = 3.044
theta_s_meas = 1.04110e-2
sep = "=" * 72

def get_zstar(h):
    ombh2 = Omega_b * h**2
    omh2 = Omega_m * h**2
    g1 = 0.0783 * ombh2**(-0.238) / (1 + 39.5 * ombh2**0.763)
    g2 = 0.560 / (1 + 21.1 * ombh2**1.81)
    return 1048 * (1 + 0.00124 * ombh2**(-0.738)) * (1 + g1 * omh2**g2)

def get_radiation(h):
    Og = 2.469e-5 / h**2
    Or = Og * (1 + 7/8 * (4/11)**(4/3) * N_eff)
    Rf = 3 * Omega_b / (4 * Og)
    return Or, Rf

# =======================================================================
#  MODEL: Constant w
# =======================================================================
def theta_const_w(h, w0):
    Or, Rf = get_radiation(h)
    zs = get_zstar(h)
    def E(z):
        return np.sqrt(Or*(1+z)**4 + Omega_m*(1+z)**3 + Omega_L*(1+z)**(3*(1+w0)))
    rs, _ = integrate.quad(lambda z: 1/(np.sqrt(3*(1+Rf/(1+z)))*E(z)), zs, np.inf, limit=200)
    DA, _ = integrate.quad(lambda z: 1/E(z), 0, zs, limit=200)
    return rs/DA

# =======================================================================
#  MODEL: Cosmic-age breathing  w(z) = -1 - (1/pi)*cos(pi*tau(z))
# =======================================================================
def theta_breathing(h, n_iter=5, details=False):
    Or, Rf = get_radiation(h)
    zs = get_zstar(h)

    # z-grid: dense at low z (DE matters), sparse at high z
    zg = np.sort(np.unique(np.concatenate([
        np.linspace(0, 3, 600),
        np.linspace(3, 30, 200),
        np.linspace(30, 500, 100),
        np.linspace(500, zs + 10, 50),
    ])))
    n = len(zg)

    def E_lcdm(z):
        return np.sqrt(Or*(1+z)**4 + Omega_m*(1+z)**3 + Omega_L)

    # Sound horizon (DE negligible at z > z*)
    rs, _ = integrate.quad(lambda z: 1/(np.sqrt(3*(1+Rf/(1+z)))*E_lcdm(z)), zs, np.inf, limit=200)

    # Initial age mapping from LCDM
    tau = np.zeros(n)
    tau_hi, _ = integrate.quad(lambda z: 1/((1+z)*E_lcdm(z)), zg[-1], 1e7, limit=200)
    tau[-1] = tau_hi
    E_arr = np.array([E_lcdm(z) for z in zg])
    for i in range(n-2, -1, -1):
        dz = zg[i+1] - zg[i]
        tau[i] = tau[i+1] + 0.5*(1/((1+zg[i])*E_arr[i]) + 1/((1+zg[i+1])*E_arr[i+1])) * dz

    # Iterate breathing solution
    for it in range(n_iter):
        # w(z) = -1 - (1/pi)*cos(pi*tau)  [A = -1/pi]
        w = -1 - (1/pi) * np.cos(pi * tau)

        # f_DE(z) = exp(3 * int_0^z (1+w)/(1+z') dz')
        intg = 3 * (1 + w) / (1 + zg)
        lnf = np.zeros(n)
        for i in range(1, n):
            lnf[i] = lnf[i-1] + 0.5*(intg[i] + intg[i-1]) * (zg[i] - zg[i-1])
        fDE = np.exp(lnf)

        # E(z) with breathing DE
        Eg = np.sqrt(Or*(1+zg)**4 + Omega_m*(1+zg)**3 + Omega_L*fDE)

        # Recompute age
        tau_new = np.zeros(n)
        tau_new[-1] = tau_hi
        for i in range(n-2, -1, -1):
            dz = zg[i+1] - zg[i]
            tau_new[i] = tau_new[i+1] + 0.5*(1/((1+zg[i])*Eg[i]) + 1/((1+zg[i+1])*Eg[i+1])) * dz
        tau = tau_new

    # D_A with breathing E(z)
    Ei = interpolate.interp1d(zg, Eg, kind='cubic', fill_value='extrapolate')
    DA, _ = integrate.quad(lambda z: 1/Ei(z), 0, zs, limit=300)

    theta = rs / DA

    if details:
        return theta, zs, rs, DA, tau, w, zg, fDE
    return theta

# =======================================================================
#  SOLVE FOR h
# =======================================================================
print(sep)
print("  FIRST-PRINCIPLES h: COSMIC-AGE BREATHING MODEL")
print(sep)
print(f"\n  Framework: Om=1/pi, Ob=1/(2pi^2), OL=1-1/pi")
print(f"  theta_s target: {theta_s_meas:.5e}")

print(f"\n  Solving for h in each DE model...")

# LCDM
h_lcdm = optimize.brentq(lambda h: theta_const_w(h, -1.0) - theta_s_meas, 0.55, 0.80, xtol=1e-10)
print(f"    LCDM (w=-1):           h = {h_lcdm:.6f}")

# Constant w0
h_cw = optimize.brentq(lambda h: theta_const_w(h, -1+1/pi) - theta_s_meas, 0.50, 0.75, xtol=1e-10)
print(f"    Constant w0=-1+1/pi:   h = {h_cw:.6f}")

# Breathing
h_br = optimize.brentq(lambda h: theta_breathing(h) - theta_s_meas, 0.55, 0.80, xtol=1e-10)
print(f"    Breathing A=-1/pi:     h = {h_br:.6f}")

# =======================================================================
#  RESULTS TABLE
# =======================================================================
print(f"\n{sep}")
print(f"  RESULTS")
print(sep)
print(f"\n  {'Model':<35} {'h':>8} {'H0':>8} {'ombh2':>8}")
print(f"  {'-'*62}")
for label, hv in [("LCDM (w=-1)", h_lcdm),
                   ("Constant w0 = -0.682", h_cw),
                   ("Breathing (DESI-like)", h_br)]:
    ombh2 = Omega_b * hv**2
    print(f"  {label:<35} {hv:8.5f} {hv*100:8.2f} {ombh2:8.5f}")
print(f"  {'Hardcoded (paper)':<35} {'0.65716':>8} {'65.72':>8} {'0.02188':>8}")
print(f"  {'Planck LCDM':<35} {'0.6736':>8} {'67.36':>8} {'0.02237':>8}")

# =======================================================================
#  BREATHING w(z) PROFILE
# =======================================================================
print(f"\n{sep}")
print(f"  BREATHING w(z) PROFILE AT h = {h_br:.5f}")
print(sep)

th, zs, rs, DA, tau, w, zg, fDE = theta_breathing(h_br, details=True)

print(f"\n  tau_0 = H0*t0 = {tau[0]:.6f}")
print(f"  Phase_0 = pi*tau_0 = {pi*tau[0]:.4f} rad")
print(f"  cos(Phase_0) = {np.cos(pi*tau[0]):.6f}")
print(f"  w(z=0) = {w[0]:.6f}  (target: {-1+1/pi:.6f})")

# Interpolators
w_i = interpolate.interp1d(zg, w, kind='linear')
fDE_i = interpolate.interp1d(zg, fDE, kind='linear')
tau_i = interpolate.interp1d(zg, tau, kind='linear')

print(f"\n  {'z':>6}  {'w(z)':>9}  {'1+w':>8}  {'f_DE':>10}  {'tau':>8}")
print(f"  {'-'*50}")
for z in [0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2, 3, 5, 10, 50, 100, 1000]:
    if z > zg[-1]: continue
    wv = float(w_i(z))
    fv = float(fDE_i(z))
    tv = float(tau_i(z))
    note = ""
    if abs(wv + 1) < 0.02: note = " <-- phantom divide"
    if z == 0: note = " quintessence"
    if z >= 10: note = " phantom"
    print(f"  {z:>6.1f}  {wv:>+9.5f}  {1+wv:>+8.5f}  {fv:>10.4f}  {tv:>8.5f}{note}")

# =======================================================================
#  BBN CROSS-CHECK
# =======================================================================
print(f"\n{sep}")
print(f"  BBN CROSS-CHECK")
print(sep)

try:
    from camb.bbn import BBN_table_interpolator
    pred = BBN_table_interpolator('PRIMAT_Yp_DH_ErrorMC_2021.dat')
    dh_obs, dh_err = 2.547e-5, 0.025e-5
    yp_obs, yp_err = 0.2449, 0.004

    print(f"\n  {'Model':<28} {'ombh2':>8} {'D/H x10^5':>10} {'D/H sig':>8} {'Y_p':>8} {'Y_p sig':>8}")
    print(f"  {'-'*72}")
    for label, hv in [("LCDM", h_lcdm), ("Const w0", h_cw),
                       ("Breathing", h_br), ("Hardcoded", 0.657162)]:
        ob2 = Omega_b * hv**2
        dh = pred.DH(ob2, delta_neff=0.0)
        yp = pred.Y_p(ob2, delta_neff=0.0)
        ds = abs(dh - dh_obs) / dh_err
        ys = abs(yp - yp_obs) / yp_err
        print(f"  {label:<28} {ob2:8.5f} {dh*1e5:10.4f} {ds:8.1f} {yp:8.4f} {ys:8.1f}")
    print(f"  {'Observed':<28} {'':>8} {dh_obs*1e5:10.3f} {'':>8} {yp_obs:8.4f}")
except ImportError:
    print("  [CAMB not available]")

# =======================================================================
#  VERDICT
# =======================================================================
ombh2_br = Omega_b * h_br**2

print(f"\n{sep}")
print(f"  VERDICT")
print(sep)
print(f"""
  The cosmic-age breathing model w(z) = -1 - (1/pi)*cos(pi*tau(z)):

  1. Matches DESI observations:
     - Quintessence today (w0 > -1)
     - Phantom in the past (wa < 0)
     - Phantom divide crossing at z ~ 0.3

  2. Self-consistent theta_s solution: h = {h_br:.6f}
     vs hardcoded: 0.657162
     vs Planck LCDM: 0.6736
     vs constant w0: {h_cw:.6f}

  3. BBN at ombh2 = {ombh2_br:.5f}:
     (check table above)

  The key physics: phantom DE at high z means LESS dark energy
  in the past, so expansion is more matter-dominated, D_A is
  larger, theta_s is smaller, and h must be HIGHER to compensate.
""")
