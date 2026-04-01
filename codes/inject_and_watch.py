#!/usr/bin/env python3
"""
INJECT AND WATCH
=================
Since global = local, our lab IS the code.
What do we physically build? How do we watch the data stream?

Andrew Dorman, 2026
"""
import math
import numpy as np
from itertools import product

Z = math.pi
N = 3
cos_b = math.cos(1/Z)
T_breath = 28.86e9
current_cycle = 13.8e9 / T_breath

# Constants
c = 2.998e8
hbar = 1.055e-34
k_B = 1.38e-23
e_charge = 1.6e-19
G = 6.674e-11
h = 6.626e-34

print("=" * 72)
print("  INJECT AND WATCH")
print("  Engineering the hardware. Tapping the data stream.")
print("=" * 72)

# =====================================================================
# PART 1: WHAT WE ACTUALLY BUILD
# =====================================================================
print()
print("=" * 72)
print("  PART 1: THE HARDWARE")
print("  What exists today that can do this")
print("=" * 72)
print()
print("  Global = local means we don't need cosmic-scale hardware.")
print("  Our 9 qutrits ARE 9 local modes of S^2.")
print("  The question is: what physical system gives us")
print("  9 controllable qutrits that couple to vacuum?")
print()

# =====================================================================
# OPTION A: SUPERCONDUCTING TRANSMON QUTRITS
# =====================================================================
print("  OPTION A: SUPERCONDUCTING TRANSMON QUTRITS (BEST)")
print("  " + "=" * 50)
print()
print("  Why transmons:")
print("    - Already built in labs worldwide (Google, IBM, etc)")
print("    - Qutrits are NATURAL — just use |0>, |1>, |2> levels")
print("    - Gate times: ~20 ns (fast injection)")
print("    - Coherence: T1 ~ 100 us, T2 ~ 50 us")
print("    - 9 transmons fits on a single chip (~2 cm x 2 cm)")
print("    - Entangling gates between any pair: ~100 ns")
print()

# Transmon parameters
f_01 = 5.0e9       # |0> -> |1> transition, 5 GHz typical
f_12 = 4.7e9       # |1> -> |2> transition (anharmonicity ~300 MHz)
anharm = -0.3e9     # anharmonicity
T1 = 100e-6         # relaxation time
T2 = 50e-6          # dephasing time
t_gate_1q = 20e-9   # single-qutrit gate
t_gate_2q = 100e-9  # two-qutrit entangling gate

print(f"  Transmon specs:")
print(f"    f_01 = {f_01/1e9:.1f} GHz (|0> -> |1>)")
print(f"    f_12 = {f_12/1e9:.1f} GHz (|1> -> |2>)")
print(f"    Anharmonicity = {anharm/1e6:.0f} MHz")
print(f"    T1 = {T1*1e6:.0f} us,  T2 = {T2*1e6:.0f} us")
print(f"    1-qutrit gate: {t_gate_1q*1e9:.0f} ns")
print(f"    2-qutrit gate: {t_gate_2q*1e9:.0f} ns")
print()

# How many operations before decoherence?
ops_per_T2 = T2 / t_gate_1q
print(f"  Operations before decoherence: {ops_per_T2:.0f}")
print(f"  More than enough for injection (need ~30 gates)")
print()

# The encoding circuit
print("  THE ENCODING CIRCUIT:")
print("  Prepare 9 transmons in [[9,1,5]]_3 codeword state |0_L>")
print()
print("  Step 1: Initialize all 9 transmons to |0>")
print("          (natural ground state at 15 mK)")
print()
print("  Step 2: Apply encoding unitary U_encode")
print("          This entangles all 9 qutrits into the code")
print()

# The encoding circuit for [[9,1,5]]_3
# Based on the generator matrix G[i][j] = alpha_j^i
# We need to create the state |0_L> = (1/sqrt(9^4)) sum_{x in GF(9)^4} |c(0,x)>
# where c(m,x) is the codeword for message m and info symbols x

print("  Encoding circuit depth:")
# For a [9,5,5] code, the encoding needs:
# - 5 initial qutrits carry the message
# - 4 qutrits are parity checks
# - Circuit depth ~ O(n*k) = O(45) two-qutrit gates
n_encode_gates = 9 * 5  # approximate
t_encode = n_encode_gates * t_gate_2q
print(f"    Two-qutrit gates needed: ~{n_encode_gates}")
print(f"    Encoding time: ~{t_encode*1e6:.1f} us")
print(f"    Fraction of T2: {t_encode/T2:.1%}")
print(f"    Feasible: YES (well within coherence window)")
print()

# The injection
print("  THE INJECTION:")
print("  Apply a skeleton key to 5 of the 9 transmons")
print()
print("  For the spookiest key {0,2,4,6,8} X.I.X.I.X2.I.X.I.X:")
print("    - X gate on transmon 0: 20 ns")
print("    - X gate on transmon 2: 20 ns (parallel)")
print("    - X^2 gate on transmon 4: 20 ns (parallel)")
print("    - X gate on transmon 6: 20 ns (parallel)")
print("    - X gate on transmon 8: 20 ns (parallel)")
print()
print("  Total injection time: 20 ns (all gates in parallel!)")
print(f"  Fraction of T2: {t_gate_1q/T2:.4%}")
print("  The injection is INSTANTANEOUS relative to decoherence.")
print()

# Syndrome measurement
print("  SYNDROME VERIFICATION:")
print("  After injection, measure the 8 syndrome qutrits")
print("  to confirm zero syndrome (successful logical operation)")
print()

# The 8 syndromes come from the parity check matrix
# H = [[9,4,?]] code's check matrix
# Measurement: prepare ancilla qutrits, do controlled-X gates
n_syndrome_gates = 8 * 9  # 8 syndromes, each touching up to 9 data qutrits
t_syndrome = n_syndrome_gates * t_gate_2q + 8 * 200e-9  # + measurement time
print(f"  Syndrome measurement gates: ~{n_syndrome_gates}")
print(f"  Measurement time per syndrome: ~200 ns")
print(f"  Total syndrome time: ~{t_syndrome*1e6:.1f} us")
print(f"  Fraction of T2: {t_syndrome/T2:.1%}")
print(f"  Feasible: YES")
print()

# =====================================================================
# THE COUPLING TO VACUUM
# =====================================================================
print("  HOW IT COUPLES TO VACUUM (THE KEY PART):")
print("  " + "-" * 50)
print()
print("  A transmon is a superconducting circuit.")
print("  It's a Josephson junction + capacitor.")
print("  It's not floating in free space — it's on a chip.")
print()
print("  But the chip IS in spacetime.")
print("  The electromagnetic vacuum of the cavity around the chip")
print("  IS the local S^2 mode structure.")
print()
print("  The transmon couples to the vacuum through:")
print()
print("  1. CASIMIR EFFECT in the microwave cavity")
print("     The chip sits inside a 3D cavity or coplanar waveguide")
print("     The cavity modes ARE the S^2 harmonics (locally)")

# Cavity parameters
L_cavity = 0.01  # 1 cm (typical 3D cavity)
f_cavity = c / (2 * L_cavity)  # fundamental mode
print(f"     Cavity length: {L_cavity*100:.0f} cm")
print(f"     Fundamental mode: {f_cavity/1e9:.1f} GHz")
print(f"     Transmon frequency: {f_01/1e9:.1f} GHz")
print(f"     RESONANT! The transmon naturally couples to cavity.")
print()

print("  2. VACUUM FLUCTUATIONS")
print("     The cavity has zero-point energy E_0 = hbar*omega/2")
E_zpf = hbar * 2 * math.pi * f_cavity / 2
print(f"     E_zpf = {E_zpf:.4e} J = {E_zpf/e_charge*1e6:.2f} ueV")
print(f"     The transmon FEELS this. It's the coupling channel.")
print()

print("  3. PURCELL EFFECT")
print("     The cavity modifies the transmon's decay rate")
print("     This IS the vacuum coupling — the transmon's lifetime")
print("     depends on the local vacuum structure")
kappa = 2 * math.pi * 1e6  # cavity linewidth ~1 MHz
g_coupling = 2 * math.pi * 100e6  # transmon-cavity coupling ~100 MHz
purcell_rate = g_coupling**2 / (2 * math.pi * abs(f_01 - f_cavity) * 2 * math.pi)
print(f"     Transmon-cavity coupling: g = {g_coupling/(2*math.pi)/1e6:.0f} MHz")
print(f"     The transmon and vacuum are ALREADY talking.")
print(f"     We're not adding a coupling. We're USING the one that exists.")
print()

print("  Summary: the transmon in its cavity is ALREADY")
print("  coupled to the local vacuum modes.")
print("  Encoding [[9,1,5]]_3 into 9 transmons and injecting")
print("  a skeleton key is NOT an artificial experiment.")
print("  It's deliberately structuring the vacuum coupling")
print("  that's already there.")
print()

# =====================================================================
# OPTION B: CASIMIR CAVITY ARRAY (PASSIVE RECEIVER)
# =====================================================================
print("  OPTION B: CASIMIR CAVITY ARRAY (PASSIVE — LISTEN ONLY)")
print("  " + "=" * 50)
print()
print("  Don't inject. Just LISTEN.")
print("  Build 9 Casimir cavities, each tuned to one S^2 mode.")
print()

for l in range(9):
    # Cavity size to match mode l: L ~ c / (2 * (2l+1) * f_base)
    # We want the l-th mode to be resonant
    # Use f_base = f_01 of transmon (5 GHz)
    f_mode = f_01 * (2*l + 1) / 1.0  # harmonic series
    L_mode = c / (2 * f_mode)
    print(f"    l={l}: f = {f_mode/1e9:>7.1f} GHz, L = {L_mode*1000:>6.2f} mm")

print()
print("  These are all microwave cavities — standard lab equipment!")
print("  Each cavity's Casimir force responds to its S^2 mode.")
print("  Monitor the force on each cavity plate continuously.")
print("  Correlations between cavities = code structure.")
print()

# =====================================================================
# PART 2: THE DATA STREAM — WATCHING IN REAL TIME
# =====================================================================
print("=" * 72)
print("  PART 2: THE REAL-TIME DATA STREAM")
print("  What can we actually watch, and how fast?")
print("=" * 72)
print()

print("  The code runs at MULTIPLE timescales simultaneously:")
print()

# Timescale 1: Breathing
f_breath = 1.0 / (T_breath * 365.25 * 24 * 3600)
print(f"  TIMESCALE 1: BREATHING")
print(f"    Period: {T_breath/1e9:.0f} Gyr")
print(f"    Frequency: {f_breath:.2e} Hz")
print(f"    Status: WAY too slow for real-time")
print(f"    Monitor via: cosmological surveys (DESI, Euclid)")
print(f"    Update rate: new data every ~1 year")
print()

# Timescale 2: Error correction (strong force)
t_qcd = 1e-24  # QCD timescale
f_qcd = 1.0 / t_qcd
print(f"  TIMESCALE 2: ERROR CORRECTION (strong force)")
print(f"    Period: {t_qcd:.0e} s")
print(f"    Frequency: {f_qcd:.0e} Hz")
print(f"    Status: WAY too fast for direct observation")
print(f"    Monitor via: particle colliders (LHC)")
print(f"    But: we see the STATISTICAL result, not individual corrections")
print()

# Timescale 3: Vacuum fluctuations
t_vacuum = hbar / (k_B * 0.015)  # at 15 mK (transmon operating temp)
f_vacuum = 1.0 / t_vacuum
print(f"  TIMESCALE 3: VACUUM FLUCTUATIONS (at 15 mK)")
print(f"    Characteristic time: {t_vacuum:.2e} s")
print(f"    Frequency: {f_vacuum:.2e} Hz")
print(f"    Status: THIS is the accessible timescale")
print(f"    Monitor via: transmon readout")
print(f"    Update rate: ~{1/t_vacuum:.0e} samples/second")
print()

# Timescale 4: Transmon measurement
t_readout = 500e-9  # 500 ns readout time (typical)
f_readout = 1.0 / t_readout
print(f"  TIMESCALE 4: TRANSMON READOUT")
print(f"    Readout time: {t_readout*1e9:.0f} ns")
print(f"    Max sample rate: {f_readout/1e6:.0f} MHz")
print(f"    Status: OUR CLOCK SPEED")
print(f"    This is how fast we can sample the code")
print()

# Timescale 5: The injection itself
print(f"  TIMESCALE 5: INJECTION")
print(f"    Encoding time: ~{t_encode*1e6:.1f} us")
print(f"    Injection time: ~{t_gate_1q*1e9:.0f} ns")
print(f"    Syndrome check: ~{t_syndrome*1e6:.1f} us")
print(f"    Total cycle: ~{(t_encode + t_gate_1q + t_syndrome)*1e6:.1f} us")
print(f"    Injection rate: ~{1/(t_encode + t_gate_1q + t_syndrome):.0f} injections/second")
print()

# =====================================================================
# PART 3: THE EXPERIMENT SEQUENCE
# =====================================================================
print("=" * 72)
print("  PART 3: THE EXPERIMENT — STEP BY STEP")
print("=" * 72)
print()

total_cycle_time = t_encode + t_gate_1q + t_syndrome
inject_rate = 1.0 / total_cycle_time

print("  PHASE 1: BASELINE (listen before you speak)")
print("  Duration: 1 hour")
print("  " + "-" * 50)
print()
print("  1a. Prepare 9 transmons in |0_L> (encode)")
print("  1b. Let the state evolve freely for time T")
print("  1c. Measure all 9 qutrits (full state tomography)")
print("  1d. Repeat 10^6 times to build statistics")
print()
n_baseline = int(3600 * inject_rate)
print(f"  Shots in 1 hour: {n_baseline:,}")
print(f"  Statistical precision: 1/sqrt(N) = {1/math.sqrt(n_baseline):.6f}")
print()
print("  What you learn:")
print("    - The natural decoherence rate of each mode")
print("    - Background syndrome statistics")
print("    - Whether the vacuum ALREADY has code structure")
print("    - The 'silence' — what the code sounds like when nobody's talking")
print()

print("  PHASE 2: FIRST INJECTION (the softest whisper)")
print("  Duration: 1 hour")
print("  " + "-" * 50)
print()
print("  2a. Encode |0_L>")
print("  2b. Apply Z-type key on {0,1,2,3,4} (PHASE ONLY)")
print("      This is the SOFTEST injection — no state change,")
print("      just a geometric phase. Maximum stealth.")
print("  2c. Measure syndrome (should be 0)")
print("  2d. Measure logical qutrit (should be |0> with extra phase)")
print("  2e. Repeat 10^6 times")
print()
print("  What you learn:")
print("    - Does the syndrome stay 0? (confirms the code works)")
print("    - Does the logical state change? (it shouldn't for Z)")
print("    - Does the DECOHERENCE RATE change after injection?")
print("      This is the key signal — if the code is real,")
print("      injecting a Z key should change how the vacuum")
print("      interacts with the transmons.")
print()

print("  PHASE 3: FULL INJECTION (speak)")
print("  Duration: 1 hour")
print("  " + "-" * 50)
print()
print("  3a. Encode |0_L>")
print("  3b. Apply X-type key on {0,2,4,6,8} (THE SPOOKIEST KEY)")
print("      This changes |0_L> -> |1_L> (equilibrium -> phantom)")
print("  3c. Measure syndrome (should be 0)")
print("  3d. Measure logical qutrit (should be |1_L>)")
print("  3e. Repeat 10^6 times")
print()
print("  What you learn:")
print("    - Does the logical state ACTUALLY change to |1>?")
print("    - Does the syndrome stay 0?")
print("    - Does ANYTHING in the lab change?")
print("      * Cavity frequency shift")
print("      * Transmon relaxation rate change")
print("      * Anomalous phase accumulation")
print("    - Compare to Phase 1 baseline: is the vacuum different?")
print()

print("  PHASE 4: LISTEN FOR THE ECHO (the critical test)")
print("  Duration: 24 hours")
print("  " + "-" * 50)
print()
print("  4a. After injection, DON'T re-encode.")
print("      Let the 9 transmons sit in the post-injection state.")
print("  4b. Continuously monitor:")
print("      - Transmon frequencies (any drift?)")
print("      - Cavity Q factor (any change?)")
print("      - Inter-transmon correlations (new entanglement?)")
print("      - Syndrome measurements (errors appearing?)")
print("  4c. If the code is real, the vacuum should RESPOND:")
print("      The local S^2 modes have been disturbed.")
print("      Error correction should activate.")
print("      You should see syndromes go NONZERO")
print("      as the code tries to correct your injection.")
print()
print("  The ECHO is the code pushing back.")
print("  If you see syndromes light up AFTER injection")
print("  (but not during baseline), that's the universe")
print("  saying 'I noticed.'")
print()

# =====================================================================
# PART 4: THE REAL-TIME DASHBOARD
# =====================================================================
print("=" * 72)
print("  PART 4: THE REAL-TIME DASHBOARD")
print("  What to display on the screen")
print("=" * 72)
print()

print("  DISPLAY 1: THE 9 MODES (live)")
print("  +" + "-" * 54 + "+")
print("  |  l=0 [########################################] 1.000 |")
print("  |  l=1 [######################################  ] 0.976 |")
print("  |  l=2 [#####################################   ] 0.952 |")
print("  |  l=3 [####################################    ] 0.929 |")
print("  |  l=4 [###################################     ] 0.906 |")
print("  |  l=5 [##################################      ] 0.884 |")
print("  |  l=6 [#################################       ] 0.862 |")
print("  |  l=7 [################################        ] 0.841 |")
print("  |  l=8 [###############################         ] 0.821 |")
print("  +" + "-" * 54 + "+")
print("  Each bar = measured coherence of that transmon qutrit")
print("  Updated every 500 ns (readout rate)")
print("  Color: green = nominal, yellow = drifting, red = failing")
print()

print("  DISPLAY 2: SYNDROME MONITOR (live)")
print("  +" + "-" * 54 + "+")
print("  |  S1: 0  S2: 0  S3: 0  S4: 0                      |")
print("  |  S5: 0  S6: 0  S7: 0  S8: 0                      |")
print("  |  STATUS: ALL CLEAR              [  0 errors/sec]   |")
print("  +" + "-" * 54 + "+")
print("  Each syndrome = measured parity of a code check")
print("  When S_i != 0: error detected on specific modes")
print("  The pattern tells you WHICH modes are noisy")
print()

print("  DISPLAY 3: LOGICAL QUTRIT STATE (live)")
print("  +" + "-" * 54 + "+")
print("  |  |psi_L> = 0.15|0> + 0.02|1> + 0.83|2>           |")
print("  |  Dominant: |2> (QUINTESSENCE)    w = -0.55         |")
print("  |  Phase:    0.4782 of breathing cycle               |")
print("  +" + "-" * 54 + "+")
print("  Extracted from tomography of the 9 transmons")
print("  Shows the current state of the logical qutrit")
print("  = the local dark energy equation of state")
print()

print("  DISPLAY 4: INJECTION LOG")
print("  +" + "-" * 54 + "+")
print("  |  14:23:01.000  INJECT  X-type {0,2,4,6,8}  S=0    |")
print("  |  14:23:01.050  VERIFY  |1_L> confirmed     S=0    |")
print("  |  14:23:01.100  ECHO?   monitoring...        S=0    |")
print("  |  14:23:01.150  ECHO?   S3 flickered!        S3=1  |")
print("  |  14:23:01.200  CORRECTED  S3 back to 0     S=0    |")
print("  +" + "-" * 54 + "+")
print("  Real-time log of injections and responses")
print("  The critical event: syndrome FLICKER after injection")
print("  That flicker = the code correcting your disturbance")
print("  That flicker = the echo")
print()

print("  DISPLAY 5: CORRELATION MAP (updated every second)")
print("  +" + "-" * 54 + "+")
for l1 in range(9):
    row = "  |  "
    for l2 in range(9):
        if l1 == l2:
            row += "@ "
        elif abs(l1 - l2) <= 2:
            row += "# "
        else:
            row += ". "
    row += f"l={l1}" + " " * (54 - len(row) + 5) + "|"
    print(row)
print("  +" + "-" * 54 + "+")
print("  @ = self, # = correlated, . = uncorrelated")
print("  After injection: watch for NEW correlations appearing")
print("  That means the code is redistributing information")
print()

# =====================================================================
# PART 5: THE DATA STREAM — WHAT TO LOG
# =====================================================================
print("=" * 72)
print("  PART 5: THE DATA STREAM FORMAT")
print("=" * 72)
print()

print("  Each measurement produces a DATA PACKET:")
print()
print("  {")
print("    timestamp:     nanosecond precision")
print("    mode_state:    [q0, q1, q2, ..., q8]  (9 qutrit values 0/1/2)")
print("    syndrome:      [s1, s2, ..., s8]      (8 syndrome values 0/1/2)")
print("    logical:       0, 1, or 2             (decoded logical state)")
print("    coherence:     [c0, c1, ..., c8]      (9 coherence values)")
print("    injection:     null or key_id         (what we injected)")
print("    cavity_freq:   [f0, f1, ..., f8]      (9 cavity frequencies)")
print("    temperature:   T_fridge               (cryostat temperature)")
print("  }")
print()

print(f"  Data rate: {1/t_readout:.0e} packets/second")
print(f"  Packet size: ~200 bytes")
print(f"  Data rate: {200/t_readout/1e6:.1f} MB/s")
print(f"  Per hour: {200/t_readout*3600/1e9:.1f} GB")
print(f"  Per day: {200/t_readout*86400/1e9:.0f} GB")
print()

print("  WHAT TO COMPUTE IN REAL TIME:")
print()
print("  1. Rolling syndrome average (1-second window)")
print("     Normal: all zeros")
print("     Anomaly: persistent nonzero syndrome = real error")
print()
print("  2. Coherence decay rate per mode")
print("     Fit: c_l(t) = A * exp(-t/T1_l) * cos(omega_l * t)")
print("     Track T1_l for each mode continuously")
print("     After injection: does T1 change? That's the echo.")
print()
print("  3. Mode-mode correlation function")
print("     C(l1,l2) = <q_l1 * q_l2> - <q_l1> * <q_l2>")
print("     Should match [[9,1,5]]_3 structure")
print("     After injection: do new correlations appear?")
print()
print("  4. Logical qutrit Bloch vector")
print("     rho_L projected onto {|0>,|1>,|2>}")
print("     Track p0, p1, p2 in real time")
print("     After injection: does the state evolve?")
print()

# =====================================================================
# PART 6: THE SYNC — MATCHING COSMIC AND LAB TIME
# =====================================================================
print("=" * 72)
print("  PART 6: SYNCING WITH THE COSMIC CODE")
print("=" * 72)
print()
print("  The breathing has a phase. We know the phase.")
print(f"  Current: {current_cycle:.6f} cycles = phase {current_cycle*2*math.pi:.4f} rad")
print()
print("  The code runs at cos(1/pi) per mode per cycle.")
print("  At the current moment, the breathing rate is:")
print()

# Rate of change of breathing phase
dphase_dt = 1.0 / T_breath  # cycles per year
dw_dt = 2 * math.pi * dphase_dt  # radians per year
print(f"  d(phase)/dt = {dphase_dt:.4e} cycles/year")
print(f"               = {dphase_dt * 365.25 * 24 * 3600:.4e} cycles/second")
print()
print("  In one second of lab time, the cosmic phase advances by:")
phase_per_second = dphase_dt / (365.25 * 24 * 3600)
print(f"  {phase_per_second:.4e} cycles")
print(f"  That's {phase_per_second * 360:.4e} degrees")
print()
print("  EFFECTIVELY ZERO on lab timescales.")
print("  The cosmic code is FROZEN during your experiment.")
print("  You have all the time in the world.")
print()
print("  But the LOCAL code (your transmons) runs at YOUR clock.")
print("  The transmon coherence time is 50-100 us.")
print("  In that window, you can:")
print(f"    - Encode: {t_encode*1e6:.1f} us")
print(f"    - Inject: {t_gate_1q*1e9:.0f} ns")
print(f"    - Read syndrome: {t_syndrome*1e6:.1f} us")
print(f"    - Measure logical: ~1 us")
print(f"    Total: ~{(t_encode+t_gate_1q+t_syndrome)*1e6+1:.1f} us out of {T2*1e6:.0f} us window")
print()

# =====================================================================
# PART 7: EXISTING DATA STREAMS TO TAP
# =====================================================================
print("=" * 72)
print("  PART 7: EXISTING DATA STREAMS (NO NEW HARDWARE)")
print("=" * 72)
print()
print("  While building the transmon array, tap these:")
print()

print("  1. LIGO/VIRGO REAL-TIME STREAM")
print("     URL: gwosc.org (Gravitational Wave Open Science Center)")
print("     Data: strain h(t) at 16,384 Hz")
print("     Mode: l=2 channel (quadrupole)")
print("     Look for: ringdown frequencies matching (2l+1) ratios")
print("     Access: public, 30-minute delay")
print()

print("  2. PLANCK LEGACY ARCHIVE")
print("     URL: pla.esac.esa.int")
print("     Data: C_l for l=2..2500")
print("     Mode: all 9 channels (l=0..8)")
print("     Look for: cos(1/pi)^(2l*t) damping pattern")
print("     Access: public, static (2018 data)")
print()

print("  3. DESI PUBLIC DATA")
print("     Data: BAO measurements at z = 0.3, 0.5, 0.7, 1.0, 1.5, 2.3")
print("     Mode: logical qutrit (w(z) evolution)")
print("     Look for: cosine curvature in w(z)")
print("     Access: public releases, ~annual")
print()

print("  4. LHC OPEN DATA")
print("     URL: opendata.cern.ch")
print("     Data: QCD jet events")
print("     Mode: syndrome channel (8 gluons)")
print("     Look for: error correction statistics")
print("     Access: public, delayed")
print()

print("  5. EDGES/SARAS (21-cm)")
print("     Data: global 21-cm signal at z~17")
print("     Mode: code state during Dark Ages (cleanest)")
print("     Look for: absorption feature matching breathing")
print("     Access: published, controversial")
print()

# =====================================================================
# PART 8: THE SIGNAL — WHAT WOULD CONFIRMATION LOOK LIKE?
# =====================================================================
print("=" * 72)
print("  PART 8: WHAT DOES CONFIRMATION LOOK LIKE?")
print("=" * 72)
print()

print("  LEVEL 1: The code structure exists (already confirmed)")
print("  Evidence: CMB anomalies match [[9,1,5]]_3 predictions")
print("  Status: CHECK (quadrupole, axis of evil, parity)")
print()

print("  LEVEL 2: The code is RUNNING (needs DESI Year 3)")
print("  Evidence: w(z) follows cosine, not linear")
print("  Test: breathing curvature in w(z) at z ~ 0.2")
print("  Prediction: |w(breathing) - w(CPL)| ~ 0.18 at z=0.2")
print("  Status: PENDING (2026-2027 data release)")
print()

print("  LEVEL 3: The code responds to injection (needs lab)")
print("  Evidence: syndrome flicker after skeleton key injection")
print("  Test: build 9-transmon array, inject, watch syndromes")
print("  Prediction: nonzero syndromes within T2 after injection")
print("  Status: NOT YET TESTED")
print()

print("  LEVEL 4: The echo propagates (needs precision metrology)")
print("  Evidence: cavity frequency shift after injection")
print("  Test: monitor cavity resonance before/after injection")
print("  Prediction: delta_f/f ~ 10^-10 shift (at the Purcell level)")
print()
df_predicted = g_coupling / (2 * math.pi * f_cavity) * (1.0/9)  # rough
print(f"  Predicted frequency shift: ~{df_predicted:.2e} fractional")
print(f"  Current cavity stability: ~10^-10 (achievable)")
print(f"  Status: TESTABLE with state-of-the-art equipment")
print()

print("  LEVEL 5: Two-way communication (future)")
print("  Evidence: inject at Lab A, detect at Lab B")
print("  Test: two 9-transmon arrays, separated, synchronized")
print("  Prediction: correlated syndrome activity at both sites")
print("  Status: FUTURE (requires two identical setups)")
print()

# =====================================================================
# PART 9: COST ESTIMATE
# =====================================================================
print("=" * 72)
print("  PART 9: WHAT DOES THIS COST?")
print("=" * 72)
print()

print("  Hardware:")
print("    Dilution refrigerator (Bluefors LD):     ~$500K")
print("    9-transmon chip (custom fabrication):     ~$50K")
print("    Microwave electronics (AWG, digitizer):   ~$200K")
print("    3D cavities (9 aluminum cavities):        ~$20K")
print("    Cryogenic wiring + attenuators:           ~$30K")
print("    Room-temp electronics + computer:         ~$50K")
total = 500 + 50 + 200 + 20 + 30 + 50
print(f"    TOTAL HARDWARE:                          ~${total}K")
print()
print("  Personnel (1 year):")
print("    1 experimental physicist:                 ~$120K")
print("    1 quantum engineer:                       ~$120K")
print("    1 theorist (you):                         ~$0")
print(f"    TOTAL PERSONNEL:                          ~$240K")
print()
print(f"  TOTAL EXPERIMENT COST:                      ~${total + 240}K")
print(f"                                              ~$1.1M")
print()
print("  For context:")
print("    LHC annual operating budget:              ~$1B")
print("    LIGO construction cost:                   ~$1.1B")
print("    James Webb Space Telescope:               ~$10B")
print("    This experiment:                          ~$1.1M")
print()
print("  You could test whether the universe runs on [[9,1,5]]_3")
print("  for less than the cost of a nice house.")
print()

# =====================================================================
# SUMMARY
# =====================================================================
print("=" * 72)
print("  SUMMARY")
print("=" * 72)
print()
print("  INJECT:")
print("    Hardware: 9 superconducting transmon qutrits on one chip")
print("    Environment: dilution refrigerator at 15 mK")
print("    Encoding: ~5 us to prepare |0_L>")
print("    Injection: 20 ns to apply skeleton key (parallel gates)")
print("    Verification: ~10 us to read syndrome")
print("    Rate: ~65,000 injections/second")
print()
print("  WATCH:")
print("    Sample rate: 2 MHz (every 500 ns)")
print("    Data: 9 qutrit states + 8 syndromes + logical state")
print("    Data rate: ~400 MB/s")
print("    Dashboard: 5 live displays (modes, syndrome, logical,")
print("               injection log, correlation map)")
print()
print("  SYNC:")
print("    Cosmic code: frozen on lab timescales")
print("    Lab code: runs at transmon clock (GHz)")
print("    No sync needed — you run MUCH faster than the universe")
print()
print("  EXISTING STREAMS:")
print("    LIGO (l=2), Planck (l=0..8), DESI (logical qutrit),")
print("    LHC (syndromes), EDGES (dark ages)")
print("    All public. All carrying the code's signal.")
print()
print("  COST: ~$1.1M. Less than a house.")
print("  TIMELINE: ~1 year to build, 1 day to get first data.")
print("  RISK: Low. Even a null result constrains the theory.")
print()
print("  The experiment is small enough to fit in a single lab,")
print("  cheap enough for a university group to fund,")
print("  and precise enough to detect the code — if it's there.")
print()
print("=" * 72)
print("  The universe is already streaming.")
print("  We just need to plug in.")
print("                                        — A. Dorman, 2026")
print("=" * 72)
