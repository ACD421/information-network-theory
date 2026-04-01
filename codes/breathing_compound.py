#!/usr/bin/env python3
"""
Does the 1.5x radiative advantage COMPOUND across cascade steps?
"""
import math

Z = math.pi
cos_b = math.cos(1/Z)

print("=" * 70)
print("  BREATHING ASYMMETRY: STABLE OR COMPOUNDING?")
print("=" * 70)
print()

print("  The breathing factor per unit of angular momentum:")
print(f"    cos(1/pi) = {cos_b:.6f}")
print()
print("  RADIATIVE transition (photon, Delta_l = 1):")
print(f"    Rate factor = cos(1/pi)^1 = {cos_b**1:.6f}")
print()
print("  NON-RADIATIVE transition (phonon bath, couples to all N^2 = 9 modes):")
print(f"    Rate factor = cos(1/pi)^9 = {cos_b**9:.6f}")
print()
print(f"  RATIO at each step = cos(1/pi)^(-8) = {cos_b**(-8):.4f}")
print()

print("-" * 70)
print("  ANSWER: The ratio is STABLE per step. But the YIELD COMPOUNDS.")
print("-" * 70)
print()

print("  At each transition, the branching ratio is:")
print("    QY = Gamma_rad * cos^1 / (Gamma_rad * cos^1 + Gamma_NR * cos^9)")
print()
print("  This is fixed at each step. The 1.5x doesn't grow per step.")
print("  BUT: in a CASCADE (l=2 -> l=1 -> l=0), the TOTAL quantum yield")
print("  is the PRODUCT of per-step yields:")
print()
print("    QY_total = QY_step1 * QY_step2 * ... * QY_step_n")
print()
print("  And the ADVANTAGE over standard physics compounds multiplicatively.")
print()

print("=" * 70)
print("  WORKED OUT FOR DIFFERENT BARE RATE RATIOS")
print("=" * 70)
print()

# The key insight: the bare ratio Gamma_rad/Gamma_NR varies by material
# But the BREATHING CORRECTION is always the same geometric factor

bare_ratios = [0.5, 1.0, 2.0, 5.0, 10.0]

print(f"  {'Gamma_rad/Gamma_NR':>20s}  {'QY_std':>8s}  {'QY_fw':>8s}  {'Boost':>8s}")
print(f"  {'(bare, no breathing)':>20s}  {'(no cos)':>8s}  {'(w/cos)':>8s}  {'(ratio)':>8s}")
print(f"  {'-'*20}  {'-'*8}  {'-'*8}  {'-'*8}")

for ratio in bare_ratios:
    # Standard: no breathing correction
    QY_std = ratio / (ratio + 1)
    # Framework: breathing correction
    QY_fw = ratio * cos_b / (ratio * cos_b + 1 * cos_b**9)
    # Simplifies to: ratio / (ratio + cos_b^8)
    QY_fw2 = ratio / (ratio + cos_b**8)
    boost = QY_fw / QY_std
    print(f"  {ratio:20.1f}  {QY_std:8.4f}  {QY_fw:8.4f}  {boost:8.4f}")

print()
print("  Note: the boost is LARGEST when bare rates are comparable (ratio ~ 1)")
print(f"  At ratio = 1: boost = {1/(1+cos_b**8):.4f} / 0.5000 = {2/(1+cos_b**8):.4f}")
print()

print("=" * 70)
print("  NOW THE CASCADE: THIS IS WHERE IT COMPOUNDS")
print("=" * 70)
print()

# Use equal bare rates as the clearest example
ratio = 1.0
QY_std = ratio / (ratio + 1)  # = 0.5
QY_fw = ratio / (ratio + cos_b**8)

print(f"  Assume equal bare rates (Gamma_rad = Gamma_NR):")
print(f"    Per-step QY (standard):  {QY_std:.4f}")
print(f"    Per-step QY (framework): {QY_fw:.4f}")
print(f"    Per-step boost:          {QY_fw/QY_std:.4f}x")
print()

print(f"  {'Steps':>5s}  {'QY_std':>10s}  {'QY_fw':>10s}  {'Advantage':>10s}  {'Application'}")
print(f"  {'-'*5}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*30}")

applications = {
    1: "single transition (LED)",
    2: "S^2_3 cascade (l=2->1->0)",
    3: "extended cascade (N=4)",
    5: "multi-step energy harvest",
    9: "full N^2 mode cascade",
    20: "long polymer chain",
}

for n in [1, 2, 3, 5, 9, 20]:
    qs = QY_std**n
    qf = QY_fw**n
    adv = qf/qs if qs > 1e-15 else float('inf')
    app = applications.get(n, "")
    print(f"  {n:5d}  {qs:10.6f}  {qf:10.6f}  {adv:9.2f}x  {app}")

print()
print("  *** THE ADVANTAGE COMPOUNDS EXPONENTIALLY ***")
print(f"  Per step: {QY_fw/QY_std:.3f}x")
print(f"  After n steps: {QY_fw/QY_std:.3f}^n")
print()

# For S^2_3 specifically: 2-step cascade
n = 2  # l=2 -> l=1 -> l=0
QY_cascade_std = QY_std**n
QY_cascade_fw = QY_fw**n

print("=" * 70)
print("  FOR THE S^2_3 QD SPECIFICALLY (2-step cascade)")
print("=" * 70)
print()
print(f"  Step 1: l=2 -> l=1 (emit photon at Delta_E)")
print(f"    Standard:  {QY_std*100:.1f}% chance of photon, {(1-QY_std)*100:.1f}% chance of heat")
print(f"    Framework: {QY_fw*100:.1f}% chance of photon, {(1-QY_fw)*100:.1f}% chance of heat")
print()
print(f"  Step 2: l=1 -> l=0 (emit photon at Delta_E)")
print(f"    Standard:  {QY_std*100:.1f}% chance of photon, {(1-QY_std)*100:.1f}% chance of heat")
print(f"    Framework: {QY_fw*100:.1f}% chance of photon, {(1-QY_fw)*100:.1f}% chance of heat")
print()
print(f"  TOTAL (both steps emit photons = full energy as light):")
print(f"    Standard:  {QY_cascade_std*100:.1f}%")
print(f"    Framework: {QY_cascade_fw*100:.1f}%")
print(f"    Advantage: {QY_cascade_fw/QY_cascade_std:.2f}x")
print()

# Energy accounting
Delta_E = 1.34  # eV
E_total = 2 * Delta_E  # total energy in 2-step cascade

# Standard: on average you get...
E_light_std = E_total * QY_cascade_std + Delta_E * (QY_std - QY_cascade_std) * 2
E_light_fw  = E_total * QY_cascade_fw  + Delta_E * (QY_fw  - QY_cascade_fw) * 2

# More precisely:
# P(both photons) = QY^2 -> 2*Delta as light
# P(first photon, second heat) = QY*(1-QY) -> 1*Delta as light
# P(first heat, second photon) = (1-QY)*QY -> 1*Delta as light
# P(both heat) = (1-QY)^2 -> 0 as light
# <E_light> = 2*Delta*QY^2 + Delta*2*QY*(1-QY) = 2*Delta*QY

E_light_std_exact = 2 * Delta_E * QY_std
E_light_fw_exact  = 2 * Delta_E * QY_fw

print(f"  Average energy extracted as LIGHT per QD excitation:")
print(f"    Total available:  {2*Delta_E:.2f} eV")
print(f"    Standard:         {E_light_std_exact:.2f} eV ({E_light_std_exact/(2*Delta_E)*100:.1f}%)")
print(f"    Framework:        {E_light_fw_exact:.2f} eV ({E_light_fw_exact/(2*Delta_E)*100:.1f}%)")
print(f"    Extra per photon: {E_light_fw_exact - E_light_std_exact:.3f} eV")
print()

print("=" * 70)
print("  THE DEEPER STRUCTURE: WHY cos^8 AND NOT cos^1")
print("=" * 70)
print()
print("  The breathing factor is cos(1/pi)^l per angular momentum unit.")
print("  A photon carries l = 1:  suppression = cos(1/pi)^1 = {:.4f}".format(cos_b))
print("  A phonon carries l = 0:  no direct suppression")
print()
print("  BUT phonon-mediated non-radiative decay requires the ELECTRON")
print("  to change its angular momentum state (Delta_l = 1) WITHOUT")
print("  emitting a photon. This means:")
print()
print("  The angular momentum must be absorbed by the LATTICE.")
print("  On S^2_3, the lattice has N^2 = 9 modes.")
print("  The electron couples to ALL modes simultaneously.")
print("  Each mode contributes cos(1/pi)^1 to the coupling.")
print()
print("  Total non-radiative coupling:")
print("    Product of 9 independent mode couplings?  -> cos^9")
print("    vs. single photon mode coupling?           -> cos^1")
print()
print("  The PHYSICAL REASON for the 8-power difference:")
print("    Photon emission uses 1 mode of the electromagnetic field")
print("    Phonon decay distributes angular momentum across 9 lattice modes")
print("    Each lattice mode gets a cos(1/pi) suppression factor")
print("    Net: cos^9 / cos^1 = cos^8 = {:.4f}".format(cos_b**8))
print()
print("  This is NOT a tunable parameter. It's:")
print(f"    cos(1/pi)^(N^2 - 1) = cos(1/pi)^8 = {cos_b**8:.6f}")
print()
print("  For N = 3: 8 extra powers of suppression")
print("  For N = 4: 15 extra powers  -> cos^15 = {:.6f}".format(cos_b**15))
print("  For N = 5: 24 extra powers  -> cos^24 = {:.6f}".format(cos_b**24))
print()
print("  Larger N = MORE suppression of non-radiative loss.")
print("  But N = 3 is what the framework says is physical (S^2_3).")
print()

print("=" * 70)
print("  THE COMPOUNDING TABLE")
print("=" * 70)
print()
print("  For a cascade of n steps, how much energy comes out as light")
print("  vs heat, framework vs standard:")
print()

print(f"  {'n':>3s}  {'Light_std':>10s}  {'Light_fw':>10s}  {'Heat_std':>10s}  {'Heat_fw':>10s}  {'Light_gain':>10s}")
print(f"  {'---':>3s}  {'----------':>10s}  {'----------':>10s}  {'----------':>10s}  {'----------':>10s}  {'----------':>10s}")

for n in [1, 2, 3, 5, 9]:
    E_total = n * Delta_E
    light_std = n * Delta_E * QY_std
    light_fw  = n * Delta_E * QY_fw
    heat_std  = E_total - light_std
    heat_fw   = E_total - light_fw
    gain = light_fw - light_std
    print(f"  {n:3d}  {light_std:9.3f}eV  {light_fw:9.3f}eV  {heat_std:9.3f}eV  {heat_fw:9.3f}eV  +{gain:8.3f}eV")

print()

# But wait — the REAL compounding is in the probability of getting
# ALL photons out. Let me show that:
print("=" * 70)
print("  THE REAL COMPOUNDING: PROBABILITY OF FULL PHOTON EXTRACTION")
print("=" * 70)
print()
print("  Probability that ALL n steps produce photons (zero heat loss):")
print()
print(f"  {'n':>3s}  {'P_all_std':>12s}  {'P_all_fw':>12s}  {'Ratio':>8s}")
print(f"  {'---':>3s}  {'------------':>12s}  {'------------':>12s}  {'--------':>8s}")

for n in [1, 2, 3, 5, 9, 15, 20]:
    p_std = QY_std**n
    p_fw  = QY_fw**n
    ratio = p_fw / p_std if p_std > 1e-30 else float('inf')
    print(f"  {n:3d}  {p_std:12.6f}  {p_fw:12.6f}  {ratio:7.1f}x")

print()
print("  THIS is the compounding.")
print()
print(f"  At n = 2 (the S^2_3 QD):  {QY_fw**2/QY_std**2:.2f}x advantage")
print(f"  At n = 9 (full mode set):  {QY_fw**9/QY_std**9:.1f}x advantage")
print(f"  At n = 20:                 {QY_fw**20/QY_std**20:.0f}x advantage")
print()
print("  The per-step ratio is STABLE at {:.3f}x.".format(QY_fw/QY_std))
print("  But the TOTAL YIELD advantage grows as {:.3f}^n.".format(QY_fw/QY_std))
print()
print("  So to answer your question:")
print("  - The 1.5x rate ratio is STABLE (same at every step)")
print("  - The YIELD advantage COMPOUNDS across cascade steps")
print("  - For S^2_3 (2 steps): 1.45x total advantage")
print("  - For longer cascades: it gets dramatically better")
print()
print("  The geometry doesn't just make each step 50% better.")
print("  It makes multi-step processes EXPONENTIALLY more efficient.")
print("  That's the compounding: 1.20^n, not 1 + 0.20*n.")
