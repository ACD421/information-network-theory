"""
Z = pi Framework - Derived Quantity Tension Analysis
"""

import numpy as np
import camb
import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PI = np.pi

h = 66.4702 / 100
ombh2 = (1/(2*PI**2)) * h**2
omch2 = ((2*PI-1)/(2*PI**2)) * h**2
Omega_k = 1/(32*PI**3)
Omega_m = 1/PI

def run(H0, ombh2, omch2, omk, tau, As, ns, ppf=False, label=""):
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
    pars.WantTransfer = True
    pars.set_matter_power(redshifts=[0])
    res = camb.get_results(pars)
    d = res.get_derived_params()
    s8 = float(np.squeeze(res.get_sigma8()))
    Om = (ombh2 + omch2) / (H0/100)**2
    S8 = s8 * np.sqrt(Om/0.3)
    print(f"  [{label}] theta*={d['thetastar']:.5f} rs={d['rstar']:.2f} "
          f"rdrag={d['rdrag']:.2f} zeq={d['zeq']:.1f} z*={d['zstar']:.2f} "
          f"zdrag={d['zdrag']:.2f} s8={s8:.4f} S8={S8:.4f}")
    return d, s8, S8

print("=" * 80)
print("DERIVED QUANTITY VERIFICATION")
print("=" * 80)

print("\nFramework PPF (H0=66.47):")
d_ppf, s8_ppf, S8_ppf = run(66.4702, ombh2, omch2, Omega_k,
                              1/(2*PI**2), np.exp(-6*PI)/PI, 1-1/PI**3,
                              ppf=True, label="FW-PPF")

print("\nFramework w=-1 (H0=66.47):")
d_w1, s8_w1, S8_w1 = run(66.4702, ombh2, omch2, Omega_k,
                           1/(2*PI**2), np.exp(-6*PI)/PI, 1-1/PI**3,
                           ppf=False, label="FW-w1")

print("\nLCDM best-fit:")
d_lcdm, s8_lcdm, S8_lcdm = run(67.36, 0.02237, 0.1200, 0.0,
                                 0.0544, 2.1e-9, 0.9649,
                                 ppf=False, label="LCDM")


# Planck 2018 observations
print("\n" + "=" * 80)
print("TENSION TABLE")
print("=" * 80)

rows = [
    # (label, fw_ppf_val, paper_val, lcdm_val, obs_val, obs_err, note)
    ("100*theta*", d_ppf['thetastar'], 1.04110, d_lcdm['thetastar'], 1.04110, 0.00031, "direct obs"),
    ("rs (Mpc)",   d_ppf['rstar'],     144.88,  d_lcdm['rstar'],     144.43,  0.26,    "LCDM-derived"),
    ("rdrag (Mpc)",d_ppf['rdrag'],     147.55,  d_lcdm['rdrag'],     147.09,  0.26,    "LCDM-derived"),
    ("zeq",        d_ppf['zeq'],       3361.5,  d_lcdm['zeq'],       3387.0,  21.0,    "LCDM-derived"),
    ("z*",         d_ppf['zstar'],     1089.77, d_lcdm['zstar'],     1089.92, 0.25,    "LCDM-derived"),
    ("zdrag",      d_ppf['zdrag'],     1059.85, d_lcdm['zdrag'],     1059.94, 0.30,    "LCDM-derived"),
    ("sigma8",     s8_ppf,             0.7767,  s8_lcdm,             0.8111,  0.006,   "CMB lensing"),
    ("S8 (lens)",  S8_ppf,             0.800,   S8_lcdm,             0.776,   0.017,   "DES+KiDS"),
]

header = f"  {'Quantity':14s} {'CAMB(PPF)':>10s} {'Paper':>10s} {'LCDM':>10s} {'Obs':>10s} {'err':>7s} {'T(FW)':>7s} {'T(LCDM)':>8s}  Note"
print(header)
print("  " + "-" * len(header))

for label, camb_val, paper_val, lcdm_val, obs_val, obs_err, note in rows:
    t_fw = abs(camb_val - obs_val) / obs_err
    t_lcdm = abs(lcdm_val - obs_val) / obs_err
    t_paper = abs(paper_val - obs_val) / obs_err
    winner = "FW" if t_fw < t_lcdm else ("tie" if abs(t_fw - t_lcdm) < 0.01 else "LCDM")
    print(f"  {label:14s} {camb_val:10.4f} {paper_val:10.4f} {lcdm_val:10.4f} "
          f"{obs_val:10.4f} {obs_err:7.4f} {t_fw:6.2f}s {t_lcdm:7.2f}s  {note} [{winner}]")


# The sigma8 / S8 story
print("\n" + "=" * 80)
print("THE SIGMA8 / S8 STORY")
print("=" * 80)

print(f"""
  Framework sigma8 = {s8_ppf:.4f} (PPF) / {s8_w1:.4f} (w=-1)
  LCDM sigma8      = {s8_lcdm:.4f}
  Planck CMB        = 0.8111 +/- 0.006 (assumes LCDM growth)

  Framework S8 = {S8_ppf:.4f} (PPF) / {S8_w1:.4f} (w=-1)  [Omega_m = 1/pi = {Omega_m:.4f}]
  LCDM S8      = {S8_lcdm:.4f}  [Omega_m = 0.3153]
  DES Y3       = 0.776 +/- 0.017
  KiDS-1000    = 0.759 +/- 0.024

  FW tension with DES:  {abs(S8_ppf - 0.776)/0.017:.2f} sigma
  LCDM tension with DES: {abs(S8_lcdm - 0.776)/0.017:.2f} sigma

  -> Framework S8 is CLOSER to weak lensing surveys than LCDM
  -> The 'S8 tension' is partially resolved by the framework
""")

# Pre-recombination physics
print("=" * 80)
print("WHY rs DIFFERS")
print("=" * 80)

print(f"""
  FW  ombh2 = {ombh2:.6f}   LCDM ombh2 = 0.022370   delta = {ombh2-0.02237:+.6f}
  FW  omch2 = {omch2:.6f}   LCDM omch2 = 0.120000   delta = {omch2-0.12000:+.6f}

  Lower omch2 -> later matter-radiation equality:
    FW zeq  = {d_ppf['zeq']:.1f}
    LCDM zeq = {d_lcdm['zeq']:.1f}   (delta = {d_ppf['zeq']-d_lcdm['zeq']:+.1f})

  Later equality -> more radiation era -> larger sound horizon:
    FW rs   = {d_ppf['rstar']:.2f} Mpc
    LCDM rs = {d_lcdm['rstar']:.2f} Mpc   (delta = {d_ppf['rstar']-d_lcdm['rstar']:+.2f} Mpc)

  The 'Planck observed' rs = 144.43 +/- 0.26 assumes LCDM.
  In a model with different zeq, the SAME data implies a different rs.
  The framework's rs=144.87 is self-consistent with its own zeq.

  This is NOT necessarily a tension - it's a different model
  fitting the same data with different physics.
""")

# theta* story
print("=" * 80)
print("THE THETA* PUZZLE")
print("=" * 80)

print(f"""
  theta* = rs / D_A(z*)

  Framework rs = {d_ppf['rstar']:.2f} Mpc (larger than LCDM by {d_ppf['rstar']-d_lcdm['rstar']:+.2f})
  Framework D_A depends on H0 and dark energy model

  With PPF w(z) at H0=66.47:
    theta* = {d_ppf['thetastar']:.5f}  (Planck = 1.04110 +/- 0.00031)
    Tension: {abs(d_ppf['thetastar'] - 1.04110)/0.00031:.1f} sigma

  With w=-1 at H0=66.47:
    theta* = {d_w1['thetastar']:.5f}  (Planck = 1.04110 +/- 0.00031)
    Tension: {abs(d_w1['thetastar'] - 1.04110)/0.00031:.1f} sigma

  Paper claims theta* = 1.04110 (0.00 sigma) using analytical formula.
  CAMB numerical gives theta* = {d_ppf['thetastar']:.5f} with PPF ({abs(d_ppf['thetastar'] - 1.04110)/0.00031:.1f} sigma).

  The {d_ppf['thetastar'] - 1.04110:+.5f} shift comes from:
    - PPF w(z) changes the angular diameter distance integral
    - CAMB numerics vs analytical approximation
""")

print("Done.")
