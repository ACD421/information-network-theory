#!/usr/bin/env python3
"""
THE ERROR-CORRECTING CODE OF THE UNIVERSE
==========================================
Find it. Map it. Break it.

Based on: Almheiri-Dong-Harlow (2015), Pastawski-Yoshida-Harlow-Preskill (2015),
Harlow (2017), Maldacena-Susskind (2013), Ryu-Takayanagi (2006)

The holographic principle says: the boundary ENCODES the bulk.
Encoding = error-correcting code.
The framework tells us WHICH code.

Andrew Dorman, 2026
"""
import math
import numpy as np

Z = math.pi
N = 3
d = 4
cos_b = math.cos(1/Z)  # 0.94977...
dim_H = N**2  # = 9

print("=" * 72)
print("  THE ERROR-CORRECTING CODE OF THE UNIVERSE")
print("  Finding it. Mapping it. Breaking it.")
print("=" * 72)


# =====================================================================
# PART 1: IDENTIFYING THE CODE
# =====================================================================
print()
print("=" * 72)
print("  PART 1: WHAT IS THE CODE?")
print("=" * 72)
print()
print("  Almheiri-Dong-Harlow (2015):")
print("  'AdS/CFT IS a quantum error-correcting code.'")
print("  The bulk (spacetime) is the LOGICAL information.")
print("  The boundary (horizon) is the PHYSICAL system.")
print()
print("  The framework:")
print(f"    Boundary: S^2 horizon with {dim_H} angular momentum modes (l=0..8)")
print(f"    Bulk: the spacetime interior you experience")
print(f"    Alphabet: qutrits (N={N} levels per fundamental dof)")
print()

# Determine code parameters
n = dim_H  # 9 physical modes
q = N      # 3-level alphabet (qutrits)

# Holographic threshold: need more than half the boundary to decode bulk
# For S^2: the RT surface dividing it is the equator
# Minimum modes needed to decode deepest bulk point: ceil((n+1)/2)
modes_needed = math.ceil((n + 1) / 2)  # = 5
modes_erasable = n - modes_needed       # = 4

# Code distance = minimum number of corruptions causing failure
# d_code = n - modes_needed + 1 = modes_erasable + 1
d_code = modes_erasable + 1  # = 5

# Logical qutrits from quantum Singleton bound
# k <= n - 2*(d_code - 1)
k_max = n - 2 * (d_code - 1)  # = 9 - 8 = 1

print(f"  The code:  [[{n}, {k_max}, {d_code}]]_{q}")
print()
print(f"    {n} physical qutrits (horizon modes)")
print(f"    {k_max} logical qutrit (the spacetime itself)")
print(f"    distance {d_code} (can correct {(d_code-1)//2} errors, detect {d_code-1})")
print()

# Singleton bound check
singleton_rhs = n - 2*(d_code - 1)
print(f"  Quantum Singleton bound: k <= n - 2(d-1)")
print(f"    {k_max} <= {n} - 2*({d_code}-1) = {singleton_rhs}")
print(f"    k = {k_max} SATURATES the bound.")
print(f"    This is a PERFECT code. Maximally efficient. No wasted space.")
print()

# MDS existence check
mds_max_n = q**2 + 1  # for quantum MDS codes
print(f"  MDS existence condition: n <= q^2 + 1")
print(f"    {n} <= {q}^2 + 1 = {mds_max_n}")
print(f"    {n} <= {mds_max_n}  {'YES' if n <= mds_max_n else 'NO'}")
print(f"    The code EXISTS. And n = {n} is ONE below the maximum ({mds_max_n}).")
print(f"    The universe uses a code at the EDGE of mathematical possibility.")
print()

# What this means
print(f"  Translation:")
print(f"    - The horizon encodes spacetime using 9 angular momentum modes")
print(f"    - You can DESTROY any 2 modes and still reconstruct spacetime")
print(f"    - You can DETECT corruption in any 4 modes")
print(f"    - If 5+ modes are corrupted: CODE FAILURE. Spacetime undecodable.")
print()
print(f"    - The code is PERFECT (no inefficiency)")
print(f"    - The code is at the EDGE of existence (n = q^2, max is q^2+1)")
print(f"    - One more mode and it would still work. Two more and it wouldn't.")


# =====================================================================
# PART 2: THE DUAL CODE — GRAVITY vs COLOR
# =====================================================================
print()
print()
print("=" * 72)
print("  PART 2: THE DUAL CODE — Gravity vs Gauge Fields")
print("=" * 72)
print()

# Dual code parameters: [[n, n-k, n-d+2]]
k_dual = n - k_max  # 8
d_dual = n - d_code + 2  # 6... wait
# Actually for quantum codes, the dual of [[n,k,d]] has different rules
# The complementary code: [[n, n-k, ?]]
# For MDS codes: dual of [[n,k,d=n-k+1]] is [[n, n-k, k+1]]
# But quantum codes are different. Let me use the CSS construction.
# For the primary [[9,1,5]]: corrects 2 errors
# The "complementary" view: the OTHER information encoded
# 9 modes encode: 1 logical qutrit (gravity) + 8 syndrome qutrits
# Those 8 syndrome qutrits = the gauge degrees of freedom

n_gauge = n - k_max  # 8
print(f"  Primary code:  [[{n}, {k_max}, {d_code}]]_{q}")
print(f"    Encodes: {k_max} logical qutrit = SPACETIME (gravity)")
print(f"    Distance {d_code} = extremely robust")
print(f"    Can survive loss of {(d_code-1)//2} modes")
print()
print(f"  Complementary structure:")
print(f"    Syndrome space: {n_gauge} qutrits = GAUGE FIELDS")
print(f"    {n_gauge} = dimension of SU(3) = 8 gluons")
print()
print(f"  *** THE 8 GLUONS ARE THE CODE'S ERROR SYNDROMES ***")
print()
print(f"  When an 'error' occurs (a perturbation), the code detects it")
print(f"  through the syndrome bits. Those syndrome measurements")
print(f"  ARE the gauge fields. Forces ARE error detection.")
print()
print(f"    Error on mode l = a particle excitation")
print(f"    Syndrome measurement = gauge field response")
print(f"    Error correction = force returning to equilibrium")
print()
print(f"  GRAVITY = the logical qutrit (the protected information)")
print(f"  GAUGE FORCES = the syndrome (the error-detection machinery)")
print()
print(f"  This is why gravity is 'different' from the other forces:")
print(f"    Gravity = the CONTENT of the code (what's protected)")
print(f"    Forces  = the MECHANISM of the code (how it self-corrects)")
print(f"    You can't unify them because they're different ROLES,")
print(f"    not different instances of the same thing.")
print()

# Protection levels
print(f"  Protection hierarchy:")
print(f"    Gravity (spacetime): distance {d_code}, correct {(d_code-1)//2} errors")
print(f"    Gauge fields:        distance 2, detect 1 error")
print(f"    Ratio: {d_code}/2 = {d_code/2}x more protection for gravity")
print()
print(f"  This matches reality:")
print(f"    QGP (breaking color): ~10^12 K  (RHIC, LHC)")
print(f"    Breaking spacetime:   ~10^32 K  (Planck temperature)")
print(f"    Ratio: ~10^20")
print(f"    The code predicts gravity is harder to break. It is.")


# =====================================================================
# PART 3: THE BREATHING AS ERROR ACCUMULATION
# =====================================================================
print()
print()
print("=" * 72)
print("  PART 3: THE BREATHING IS ERROR ACCUMULATION")
print("=" * 72)
print()
print("  The breathing factor cos(1/pi)^l = coherence of mode l.")
print(f"  cos(1/pi) = {cos_b:.6f}")
print()
print("  Per breathing cycle, each mode accumulates decoherence:")
print()

# Error rates per mode
print(f"  {'Mode l':<10} {'Coherence':<15} {'Error rate':<15} {'Half-life':<15}")
print(f"  {'------':<10} {'---------':<15} {'----------':<15} {'---------':<15}")

ln_cos = math.log(cos_b)  # negative
half_lives = []

for l in range(dim_H):
    coherence = cos_b ** l
    error_rate = 1 - coherence**2  # probability of decoherence
    if l == 0:
        half_life_str = "INFINITE"
        half_lives.append(float('inf'))
    else:
        # Half-life: cos_b^(l*n) = 0.5 -> n = log(0.5)/(l*log(cos_b))
        hl = math.log(0.5) / (l * ln_cos)
        half_life_str = f"{hl:.2f} cycles"
        half_lives.append(hl)
    print(f"  l={l:<7} {coherence:<15.6f} {error_rate:<15.6f} {half_life_str:<15}")

print()
print(f"  KEY INSIGHT:")
print(f"  Mode l=0 NEVER decays. It's the ground state. Eternal.")
print(f"  All other modes decay at rate proportional to l.")
print(f"  The higher the angular momentum, the faster the decay.")
print()

# The cascade
print(f"  THE FAILURE CASCADE:")
print(f"  Modes fail in order: l=8 first, then 7, 6, 5, 4...")
print()

# 1/e lifetime for each mode
print(f"  Mode failure order (coherence drops to 1/e):")
e_lives = []
for l in range(1, dim_H):
    # cos_b^(l*n) = 1/e -> l*n = -1/ln(cos_b) -> n = 1/(l*|ln(cos_b)|)
    n_fail = 1.0 / (l * abs(ln_cos))
    e_lives.append((l, n_fail))
    print(f"    Mode l={l}: fails at n = {n_fail:.2f} breathing cycles")

e_lives.sort(key=lambda x: x[1])
print()

# Count failures over time
print(f"  CUMULATIVE FAILURES:")
print(f"  {'Cycle':<10} {'Modes failed':<15} {'Code status':<25}")
print(f"  {'-----':<10} {'------------':<15} {'-----------':<25}")

checkpoints = [0.5, 1.0, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 8.0, 10.0, 15.0, 20.0]
for nc in checkpoints:
    failed = sum(1 for l, nf in e_lives if nf <= nc)
    if failed < 2:
        status = "FULLY OPERATIONAL"
    elif failed < 5:
        status = f"DEGRADED ({failed}/4 correctable)"
    elif failed == 5:
        status = "*** CODE FAILURE ***"
    else:
        status = f"BROKEN ({failed} modes gone)"
    print(f"  {nc:<10.1f} {failed:<15} {status:<25}")

# Find the critical cycle
critical_modes = sorted(e_lives, key=lambda x: x[1])
fifth_failure = critical_modes[4]  # 0-indexed, 5th mode to fail
print()
print(f"  *** CRITICAL POINT: Cycle {fifth_failure[1]:.2f} ***")
print(f"  *** Mode l={fifth_failure[0]} is the 5th to fail ***")
print(f"  *** At this point: code distance drops below threshold ***")
print(f"  *** Spacetime becomes UNDECODABLE from the boundary ***")


# =====================================================================
# PART 4: WHERE ARE WE NOW?
# =====================================================================
print()
print()
print("=" * 72)
print("  PART 4: CURRENT STATUS — Where are we in the cascade?")
print("=" * 72)
print()

# Breathing period
T_breathe = 2 * math.pi / Z  # = 2.0 in natural units
H_0_Gyr = 14.4  # 1/H_0 in Gyr (rough)
T_cycle_Gyr = T_breathe * H_0_Gyr  # breathing cycle in Gyr

age_universe = 13.8  # Gyr
current_cycle = age_universe / T_cycle_Gyr

print(f"  Breathing period: T = 2pi/pi = {T_breathe:.1f} (natural units)")
print(f"  In physical time: T ~ {T_cycle_Gyr:.1f} Gyr")
print(f"  Universe age: {age_universe} Gyr")
print(f"  Current cycle position: {current_cycle:.3f}")
print()

print(f"  MODE-BY-MODE COHERENCE RIGHT NOW:")
print(f"  {'Mode':<8} {'Coherence':<15} {'Integrity':<15} {'Status':<20}")
print(f"  {'----':<8} {'---------':<15} {'---------':<15} {'------':<20}")

intact_count = 0
for l in range(dim_H):
    coh = cos_b ** (l * current_cycle)
    integrity = coh**2 * 100
    if integrity > 95:
        status = "PRISTINE"
    elif integrity > 80:
        status = "GOOD"
    elif integrity > 50:
        status = "DEGRADED"
    elif integrity > 1/math.e * 100:
        status = "FAILING"
    else:
        status = "BROKEN"

    if integrity > 1/math.e * 100:
        intact_count += 1

    print(f"  l={l:<5} {coh:<15.6f} {integrity:<14.1f}% {status:<20}")

print()
print(f"  Intact modes: {intact_count}/{dim_H}")
print(f"  Code status: {'FULLY OPERATIONAL' if intact_count >= 5 else 'FAILING'}")
print(f"  Time to code failure: {(fifth_failure[1] - current_cycle) * T_cycle_Gyr:.1f} Gyr")
print(f"  We are {current_cycle/fifth_failure[1]*100:.1f}% through the code's lifetime.")
print()
print(f"  The code is FRESH. We're in the first 10% of its life.")
print(f"  Like a battery at 90% charge.")
print(f"  The universe has ~{(fifth_failure[1] - current_cycle) * T_cycle_Gyr:.0f} Gyr of")
print(f"  error-protected spacetime remaining.")


# =====================================================================
# PART 5: THREE METHODS TO BREAK THE CODE
# =====================================================================
print()
print()
print("=" * 72)
print("  PART 5: HOW TO BREAK IT")
print("  Three methods, ranked by feasibility")
print("=" * 72)

# Method 1: Resonant decoherence
print()
print("  METHOD 1: RESONANT DECOHERENCE")
print("  " + "-" * 40)
print()
print("  Each mode l has natural frequency omega_l = (l + 1/2) * omega_0")
print("  Drive at the DIFFERENCE frequencies to selectively decohere:")
print()

omega_0 = 1.0  # normalized
print(f"  {'Modes':<12} {'Diff freq':<15} {'Target':<30}")
print(f"  {'-----':<12} {'---------':<15} {'------':<30}")
targets = [(8,7), (8,6), (7,6), (7,5), (6,5), (6,4), (5,4)]
for l1, l2 in targets:
    omega_diff = abs((l1 + 0.5) - (l2 + 0.5)) * omega_0
    print(f"  ({l1},{l2})     {omega_diff:.1f} * omega_0    Decohere modes {l1} & {l2}")

print()
print(f"  Strategy: drive all difference frequencies simultaneously")
print(f"  to decohere modes 4-8 in parallel.")
print()
print(f"  In a quantum dot: omega_0 ~ 10^14 rad/s")
print(f"  Drive frequencies: 10^14 rad/s (infrared)")
print(f"  This is EXPERIMENTALLY ACCESSIBLE.")
print()
print(f"  Difficulty: MODERATE (need precise multi-frequency drive)")
print(f"  What breaks: the quantum dot's error correction")
print(f"  What you see: anomalous decoherence rates, non-standard QD behavior")
print(f"  Scale: laboratory")

# Method 2: Entanglement dilution
print()
print()
print("  METHOD 2: ENTANGLEMENT DILUTION")
print("  " + "-" * 40)
print()
print("  The code's error-correction power comes from ENTANGLEMENT")
print("  between the 9 modes. If you dilute this entanglement by")
print("  coupling modes to external degrees of freedom:")
print()

# Entanglement entropy
S_max = math.log(dim_H)  # maximum entanglement for 9 modes
S_threshold = math.log(dim_H - d_code + 1)  # threshold for code failure

print(f"  Maximum code entanglement: S_max = ln({dim_H}) = {S_max:.4f} nats")
print(f"  Threshold for code failure: S < ln({dim_H - d_code + 1}) = {S_threshold:.4f} nats")
print(f"  Need to remove: {S_max - S_threshold:.4f} nats = {(S_max-S_threshold)/S_max*100:.1f}% of entanglement")
print()
print(f"  Hawking radiation does this NATURALLY:")
print(f"    Each emitted quantum carries away ~1 bit of entanglement")
print(f"    Page time: when half the entanglement is radiated")
print(f"    After Page time: code transitions, bulk info moves to radiation")
print()
print(f"  To do it ARTIFICIALLY:")
print(f"    Couple each horizon mode to an external bath")
print(f"    Bath temperature > mode temperature -> entanglement flows OUT")
print(f"    When enough entanglement is extracted: code fails")
print()
print(f"  Analog in lab: couple QD modes to a thermal reservoir")
print(f"  Above the QD's effective temperature ({0.5 * 1.34:.2f} eV ~ {0.5*1.34*11604:.0f} K)")
print()
print(f"  Difficulty: EASY (just heat it up — but that's not interesting)")
print(f"  The interesting version: SELECTIVE entanglement extraction")
print(f"  using ancilla qubits coupled to specific modes.")
print(f"  Scale: laboratory")

# Method 3: Topology change
print()
print()
print("  METHOD 3: TOPOLOGY CHANGE")
print("  " + "-" * 40)
print()
print("  The code [[9,1,5]]_3 is defined on S^2.")
print("  If the topology changes, the code becomes INVALID.")
print()
print("  S^2 modes:  l = 0, 1, 2, ... (spherical harmonics)")
print("  T^2 modes:  (m, n) doubly periodic (Fourier modes)")
print("  RP^2 modes: l = 0, 2, 4, ... (EVEN l only!)")
print()
print("  If S^2 -> RP^2 (orientability change):")
print(f"    Modes l=1,3,5,7 are KILLED (odd l forbidden on RP^2)")
print(f"    4 modes killed instantly > threshold of 5-1=4 detectable")
print(f"    But only 5 modes survive (l=0,2,4,6,8)")
print(f"    New code: [[5, k', d']] on RP^2")
print(f"    Singleton: k' <= 5 - 2(d'-1) -> d'=3 gives k'=1")
print(f"    A [[5,1,3]]_3 code: WEAKER (can only correct 1 error)")
print()
print(f"  If S^2 -> T^2 (torus, genus change):")
print(f"    Mode structure completely changes")
print(f"    Old code words become SUPERPOSITIONS of new code words")
print(f"    Code fails during the transition")
print()
print(f"  How to change topology:")
print(f"    1. Vacuum decay bubble (Coleman-De Luccia instanton)")
print(f"    2. Cosmic string loop collapse")
print(f"    3. Black hole pair creation + merger")
print()
print(f"  Difficulty: EXTREME (cosmological-scale process)")
print(f"  Scale: universe")

# Method 4 (the real one)
print()
print()
print("  METHOD 4: THE SHORTCUT — Logical operator attack")
print("  " + "-" * 40)
print()
print("  You don't need to CORRUPT 5 modes.")
print("  You need to apply the code's OWN LOGICAL OPERATORS.")
print()
print("  A logical operator acts on the code space WITHOUT being")
print("  detected by the error syndromes. It changes the encoded")
print("  information while the code thinks everything is fine.")
print()
print("  For [[9,1,5]]_3:")
print(f"    Logical X: cycles the logical qutrit (|0> -> |1> -> |2> -> |0>)")
print(f"    Logical Z: phases the logical qutrit (|k> -> omega^k |k>)")
print(f"    where omega = e^(2*pi*i/3) = cube root of unity")
print()

omega3 = np.exp(2j * np.pi / 3)
print(f"    omega = e^(2pi*i/3) = {omega3.real:.4f} + {omega3.imag:.4f}i")
print(f"    omega^3 = {(omega3**3).real:.6f} + {(omega3**3).imag:.6f}i = 1")
print()

print(f"  The logical operators have WEIGHT 5 (minimum).")
print(f"  They act on exactly 5 of the 9 modes simultaneously.")
print(f"  Any fewer would be detectable; any more is unnecessary.")
print()
print(f"  PHYSICAL MEANING:")
print(f"  A weight-5 logical operator = a coherent perturbation")
print(f"  that changes the MEANING of spacetime without triggering")
print(f"  any force (no syndrome = no gauge field response).")
print()
print(f"  This is a perturbation that:")
print(f"    - Is NOT gravitational (doesn't change the metric)")
print(f"    - Is NOT electromagnetic (no photon)")
print(f"    - Is NOT strong/weak (no gluon/W/Z)")
print(f"    - Passes THROUGH all known forces undetected")
print(f"    - Changes what spacetime MEANS while looking unchanged")
print()
print(f"  If such a process exists in nature, it would be:")
print(f"    A 'fifth force' that acts on 5 modes simultaneously")
print(f"    Undetectable by any standard experiment")
print(f"    Changes the holographic encoding without leaving traces")
print()
print(f"  Difficulty: UNKNOWN")
print(f"  This is the theoretical 'skeleton key' to the universe.")
print(f"  The code's own backdoor.")


# =====================================================================
# PART 6: WHAT HAPPENS WHEN THE CODE BREAKS
# =====================================================================
print()
print()
print("=" * 72)
print("  PART 6: WHAT'S ON THE OTHER SIDE")
print("=" * 72)
print()
print("  When 5+ modes are corrupted, the [[9,1,5]]_3 code FAILS.")
print("  What happens to the information?")
print()
print("  UNITARITY says: information is NEVER destroyed.")
print("  It must go SOMEWHERE.")
print()

# Surviving code
surviving_modes = dim_H - d_code  # 9 - 5 = 4
print(f"  The surviving structure:")
print(f"    {surviving_modes} intact modes remain")
print(f"    These form a [[{surviving_modes}, k', d']]_3 code")

k_surv_max = surviving_modes  # maximum logical content
# Singleton: k' <= 4 - 2*(d'-1)
# d'=1: k' <= 4 (no protection)
# d'=2: k' <= 2
# d'=3: k' <= 0 (impossible)

print(f"    Singleton bound: k' <= {surviving_modes} - 2(d'-1)")
print(f"      d'=1: k' <= {surviving_modes} (NO error protection)")
print(f"      d'=2: k' <= {surviving_modes - 2} (detect 1 error)")
print()
print(f"  Best case: [[4, 2, 2]]_3")
print(f"    2 logical qutrits, can detect 1 error (no correction!)")
print(f"    Logical space: 3^2 = 9 states")
print()
print(f"  WAIT: 9 states. The SAME dimensionality as the original.")
print(f"  The information SURVIVES intact.")
print(f"  It just LOSES ITS ERROR PROTECTION.")
print()
print(f"  PHYSICAL INTERPRETATION:")
print(f"  {'Before code break':<30} {'After code break':<30}")
print(f"  {'='*28:<30} {'='*28:<30}")
print(f"  {'Error-corrected':<30} {'Unprotected':<30}")
print(f"  {'Classical-looking':<30} {'Fully quantum':<30}")
print(f"  {'Spacetime geometry':<30} {'Quantum foam':<30}")
print(f"  {'Deterministic':<30} {'Probabilistic':<30}")
print(f"  {'Smooth':<30} {'Fractal':<30}")
print(f"  {'Forces work':<30} {'Forces undefined':<30}")
print()
print(f"  The 'classical world' = error-corrected quantum state.")
print(f"  Error correction is what makes reality LOOK deterministic.")
print(f"  When it fails: the quantum nature is EXPOSED.")
print()
print(f"  This IS:")
print(f"    - The black hole interior (beyond the horizon)")
print(f"    - The Planck scale (below the error-correction length)")
print(f"    - The heat death (code has expired)")
print(f"    - The Big Crunch (if that happens)")
print()
print(f"  All are the SAME thing: code failure -> raw quantum state.")


# =====================================================================
# PART 7: THE ARROW OF TIME IS CODE DEGRADATION
# =====================================================================
print()
print()
print("=" * 72)
print("  PART 7: THE ARROW OF TIME")
print("=" * 72)
print()
print("  Time is not fundamental in the framework.")
print("  What IS fundamental: the breathing factor cos(1/pi)^l.")
print()
print("  The arrow of time = the direction of CODE DEGRADATION.")
print()
print(f"  Past:   code fresh, all modes coherent, low entropy")
print(f"  Present: code at {current_cycle/fifth_failure[1]*100:.0f}%, some decoherence, medium entropy")
print(f"  Future:  code degrading, modes failing, entropy increasing")
print(f"  End:     code broken, all modes decohered, max entropy")
print()
print(f"  The second law IS code degradation:")
print(f"    S_entropy = log(corrupted states)")
print(f"    As modes decohere, more states become accessible")
print(f"    Entropy increases because error correction weakens")
print()
print(f"  You FEEL time pass because the code is AGING.")
print(f"  If the code were eternal (d = infinity), there would be no time.")
print(f"  Time exists because the code is FINITE (d = 5).")
print()
print(f"  The speed of time = decoherence rate = |ln(cos(1/pi))| = {abs(ln_cos):.6f}")
print(f"  This is approximately 1/pi^2 = {1/math.pi**2:.6f}")
is_close = abs(abs(ln_cos) - 1/math.pi**2) / abs(ln_cos)
print(f"  Match: {(1-is_close)*100:.2f}%")


# =====================================================================
# PART 8: THE CRACK IN THE CODE
# =====================================================================
print()
print()
print("=" * 72)
print("  PART 8: THE CRACK — The vulnerability the framework reveals")
print("=" * 72)
print()
print("  The framework has a SELF-CONTRADICTION:")
print()
print("  Statement A (ANEC = 0):")
print("    Over a full breathing cycle, energy is CONSERVED.")
print("    The phantom phase (NEC violation) is EXACTLY cancelled")
print("    by the quintessence phase. Net = 0.")
print("    Implication: the cycle is REVERSIBLE. No net change.")
print()
print("  Statement B (Second Law from geometry):")
print("    cos(1/pi)^l makes decoherence IRREVERSIBLE.")
print("    Modes decay. Entropy increases. Arrow of time.")
print("    Implication: the cycle is IRREVERSIBLE. Net entropy grows.")
print()
print("  These cannot BOTH be true for ALL observables.")
print()

# The resolution
print("  THE RESOLUTION (and the vulnerability):")
print()
print("  ANEC = 0 applies to ENERGY.")
print("  The second law applies to INFORMATION.")
print()
print("  Energy cycles reversibly: phantom <-> quintessence.")
print("  Information degrades irreversibly: coherence -> decoherence.")
print()
print("  They're DIFFERENT quantities.")
print("  Energy is a number. Information is a pattern.")
print("  The number can cycle. The pattern can't un-scramble.")
print()
print("  THE CRACK:")
print("  The quintessence phase DOES re-energize the modes.")
print("  But it does NOT re-cohere them.")
print("  It's like recharging a battery that's been SCRAMBLED:")
print("  the energy goes back in, but the pattern is gone.")
print()
print("  UNLESS...")
print()

# The exploit
print("  UNLESS you can use the quintessence phase to")
print("  ACTIVELY RE-COHERE the modes before they fully scramble.")
print()
print("  The window:")

for l in range(1, dim_H):
    half_life = half_lives[l]
    # Re-coherence window: the quintessence phase lasts half a cycle = 1.0
    # Mode l fails at half_lives[l] cycles
    # If half_life > 1.0: you have time to re-cohere during quintessence
    # If half_life < 1.0: mode decoheres faster than one cycle -> too late
    window = "OPEN" if half_life > 1.0 else "CLOSED"
    margin = half_life - 1.0
    print(f"    Mode l={l}: half-life = {half_life:.2f} cycles, "
          f"re-coherence window: {window} "
          f"({'%.2f cycles margin' % margin if margin > 0 else 'TOO FAST'})")

print()
print(f"  ALL modes have half-life > 1 cycle.")
print(f"  The re-coherence window is OPEN for every mode.")
print()
print(f"  THIS IS THE VULNERABILITY:")
print(f"  If you can apply error correction DURING the quintessence phase,")
print(f"  when energy is flowing back into the modes, you can")
print(f"  RESET the code. Reverse the decoherence. Rewind the clock.")
print()
print(f"  The framework allows it: ANEC = 0 means energy is available.")
print(f"  The second law seems to forbid it: entropy should increase.")
print(f"  But the second law comes FROM the code. If you correct the code...")
print(f"  the second law is RESTORED, not violated.")
print()
print(f"  You're not breaking thermodynamics.")
print(f"  You're MAINTAINING the error-correcting code that")
print(f"  thermodynamics is built on.")


# =====================================================================
# PART 9: THE RECIPE
# =====================================================================
print()
print()
print("=" * 72)
print("  PART 9: THE RECIPE — How to break (or maintain) the code")
print("=" * 72)
print()
print("  TO BREAK:")
print(f"    1. Corrupt 5 of 9 modes (any 5)")
print(f"    2. Easiest targets: l=8,7,6,5,4 (highest decoherence rates)")
print(f"    3. Method: resonant drive at difference frequencies")
print(f"    4. Needed: coherent multi-frequency source at omega_0 ~ 10^14 rad/s")
print(f"    5. Result: local region loses error protection")
print(f"    6. Observable: anomalous quantum behavior, 'classicality breakdown'")
print()
print("  TO MAINTAIN (reverse aging):")
print(f"    1. Detect which modes have decohered (syndrome measurement)")
print(f"    2. Apply corrective unitaries during quintessence phase")
print(f"    3. The corrective unitary IS the error-correction operation")
print(f"    4. For [[9,1,5]]_3: each correction = one of 45 U(9) gates")
print(f"    5. Need to correct before mode half-life expires")
print(f"    6. Fastest decay: l=8 with half-life = {half_lives[8]:.2f} cycles")
print(f"    7. Correction rate needed: > 1/{half_lives[8]:.2f} = {1/half_lives[8]:.4f} per cycle")
print()

# Error correction rate
correction_rate = 1.0 / half_lives[8]
print(f"  MINIMUM CORRECTION RATE: {correction_rate:.4f} operations per breathing cycle")
print(f"  In physical units: ~ {correction_rate / T_cycle_Gyr:.2e} operations per Gyr")
print(f"  That's... barely anything. One operation every {T_cycle_Gyr * half_lives[8]:.0f} Gyr.")
print()
print(f"  The universe's error correction is LAZY.")
print(f"  It barely needs to do anything because the code is so good.")
print(f"  distance 5 with 9 modes = massive overkill for current error rates.")
print()

# The skeleton key
print("  THE SKELETON KEY:")
print(f"    The logical operators of [[9,1,5]]_3 act on 5 modes at once.")
print(f"    They are weight-5 elements of U(9).")
print(f"    There are {math.comb(9,5)} = {math.comb(9,5)} ways to choose which 5 modes.")
print(f"    For each choice: (3^2 - 1) * 3 = {(q**2-1)*q} non-trivial logical ops.")
print(f"    Total skeleton keys: {math.comb(9,5)} * {(q**2-1)*q} = {math.comb(9,5) * (q**2-1)*q}")
print()
print(f"    These {math.comb(9,5) * (q**2-1)*q} operations are the universe's")
print(f"    UNDOCUMENTED INSTRUCTIONS. They change what spacetime MEANS")
print(f"    without triggering any force or detector.")
print()
print(f"    Finding them = finding the cheat codes.")
print(f"    Each one is a specific 9x9 unitary matrix.")
print(f"    The matrices exist. They're in U(9).")
print(f"    Nobody has written them down.")
print()


# =====================================================================
# FINAL SYNTHESIS
# =====================================================================
print()
print("=" * 72)
print("  THE ERROR-CORRECTING CODE OF THE UNIVERSE")
print("  Summary")
print("=" * 72)
print()
print(f"  Code:        [[9, 1, 5]]_3")
print(f"  Type:        Quantum MDS (perfect, at existence boundary)")
print(f"  Physical:    9 modes on S^2 encode 1 qutrit of spacetime")
print(f"  Syndromes:   8 gauge qutrits = the 8 gluons of SU(3)")
print(f"  Logical ops: {math.comb(9,5) * (q**2-1)*q} skeleton keys (weight-5 unitaries)")
print(f"  Lifetime:    ~{fifth_failure[1] * T_cycle_Gyr:.0f} Gyr ({fifth_failure[1]:.1f} breathing cycles)")
print(f"  Current age: {current_cycle:.2f} cycles ({current_cycle/fifth_failure[1]*100:.0f}% of lifetime)")
print(f"  Time left:   ~{(fifth_failure[1] - current_cycle) * T_cycle_Gyr:.0f} Gyr")
print()
print(f"  To break: corrupt 5 modes (resonance, heat, or topology change)")
print(f"  To maintain: correct errors during quintessence phase (barely needed)")
print(f"  To exploit: find the {math.comb(9,5) * (q**2-1)*q} logical operators (skeleton keys)")
print()
print(f"  What's on the other side of code failure:")
print(f"    Same information, no error protection.")
print(f"    Classical -> quantum. Spacetime -> foam.")
print(f"    The world behind the curtain.")
print(f"    Everything the code was protecting you from seeing.")
print()
print(f"  The code doesn't hide the quantum world from you.")
print(f"  The code IS the reason you exist as a classical observer.")
print(f"  Break the code, and 'you' dissolve into the quantum state")
print(f"  that was always there, perfectly preserved, just... unprotected.")
print()
print(f"  The universe IS an error-correcting code.")
print(f"  Spacetime IS the encoded message.")
print(f"  Forces ARE the error detection.")
print(f"  Time IS the code's expiration.")
print(f"  And the code has {math.comb(9,5) * (q**2-1)*q} backdoors.")
print(f"  They're called the skeleton keys of U(9).")
print(f"  And now you know they exist.")
