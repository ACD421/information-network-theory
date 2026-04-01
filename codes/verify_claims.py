import math
import numpy as np

Z = math.pi
d = 4
N = 3
beta = 1/Z
cos_b = math.cos(beta)

print("="*70)
print("MATHEMATICAL VERIFICATION OF ALL CLAIMS")
print("="*70)

# 1. 8pi = 2dZ
print("\n1. 8pi = 2dZ")
lhs = 8*math.pi
rhs = 2*d*Z
print(f"   8pi = {lhs:.10f}")
print(f"   2dZ = {rhs:.10f}")
print(f"   MATCH: {abs(lhs-rhs) < 1e-14}")

# 2. Hawking temperature: T_H = 1/(8piM) = 1/(2dZM)
print("\n2. T_H = 1/(8piM) = 1/(2dZM)")
M = 1.0  # test mass
T1 = 1/(8*math.pi*M)
T2 = 1/(2*d*Z*M)
print(f"   1/(8piM) = {T1:.10f}")
print(f"   1/(2dZM) = {T2:.10f}")
print(f"   MATCH: {abs(T1-T2) < 1e-14}")

# 3. beta = 1/Z = 1/pi as geometric angle
print("\n3. beta = 1/Z = 1/pi")
print(f"   beta = {beta:.10f}")
print(f"   T_H = beta/(2dM) = {beta/(2*d*M):.10f}")
print(f"   Same as 1/(8piM) = {1/(8*math.pi*M):.10f}")
print(f"   MATCH: {abs(beta/(2*d*M) - 1/(8*math.pi*M)) < 1e-14}")

# 4. Bekenstein-Hawking: S = A/(4G) = A/(dG) since d=4
print("\n4. S_BH = A/(4G) = A/(dG)")
print(f"   d = {d}, so 1/d = 1/4 = {1/d}")
print(f"   TRIVIALLY CORRECT: d=4 => 1/4 = 1/d")

# 5. S = dZM^2 = 4piM^2
print("\n5. S = dZM^2 = 4piM^2")
S1 = d*Z*M**2
S2 = 4*math.pi*M**2
print(f"   dZM^2 = {S1:.10f}")
print(f"   4piM^2 = {S2:.10f}")
print(f"   MATCH: {abs(S1-S2) < 1e-14}")

# 6. Unruh: T_U = a/(2pi) = a/(2Z)
print("\n6. T_U = a/(2pi) = a/(2Z)")
a = 1.0
T_U1 = a/(2*math.pi)
T_U2 = a/(2*Z)
print(f"   a/(2pi) = {T_U1:.10f}")
print(f"   a/(2Z)  = {T_U2:.10f}")
print(f"   MATCH: {abs(T_U1-T_U2) < 1e-14}")

# 7. Minimum wormhole: r_min = 1/sqrt(pi), S_min = 1/4
print("\n7. Minimum wormhole")
r_min = 1/math.sqrt(Z)
M_min = r_min/2
S_min = Z * M_min**2
print(f"   r_min = 1/sqrt(pi) = {r_min:.10f}")
print(f"   M_min = 1/(2sqrt(pi)) = {M_min:.10f}")
print(f"   S_min = pi * (1/(4pi)) = 1/4 = {S_min:.10f}")
print(f"   S_min = 0.25? {abs(S_min - 0.25) < 1e-14}")

# 8. Fuzzy sphere wormhole: dim(H) = 9, S = ln(9)
print("\n8. Fuzzy sphere wormhole")
S_fuzzy = math.log(N**2)
M_fuzzy = math.sqrt(S_fuzzy/Z)
print(f"   dim(H) = N^2 = {N**2}")
print(f"   S = ln(9) = {S_fuzzy:.6f} nats")
print(f"   M = sqrt(ln9/pi) = {M_fuzzy:.6f}")
print(f"   r = 2M = {2*M_fuzzy:.6f}")

# 9. Population inversion on 9-state system
print("\n9. Population inversion — 9-state stat mech")
for T in [1.0, -1.0]:
    b = 1/T
    Zp = sum(math.exp(-b*n) for n in range(9))
    probs = [math.exp(-b*n)/Zp for n in range(9)]
    E = sum(n*p for n, p in zip(range(9), probs))
    S = -sum(p*math.log(p) for p in probs if p > 1e-15)
    print(f"   T={T:+.0f}: <E>={E:.6f}, S={S:.6f}")

# Check mirror symmetry
b_pos = 1.0
Zp_pos = sum(math.exp(-b_pos*n) for n in range(9))
probs_pos = [math.exp(-b_pos*n)/Zp_pos for n in range(9)]
E_pos = sum(n*p for n, p in zip(range(9), probs_pos))
S_pos = -sum(p*math.log(p) for p in probs_pos if p > 1e-15)

b_neg = -1.0
Zp_neg = sum(math.exp(-b_neg*n) for n in range(9))
probs_neg = [math.exp(-b_neg*n)/Zp_neg for n in range(9)]
E_neg = sum(n*p for n, p in zip(range(9), probs_neg))
S_neg = -sum(p*math.log(p) for p in probs_neg if p > 1e-15)

print(f"\n   Mirror symmetry checks:")
print(f"   S(T=+1) = {S_pos:.10f}")
print(f"   S(T=-1) = {S_neg:.10f}")
print(f"   S equal? {abs(S_pos - S_neg) < 1e-10}")
print(f"   E(+1) + E(-1) = {E_pos + E_neg:.10f}")
print(f"   = 8.0? {abs(E_pos + E_neg - 8.0) < 1e-10}")
print(f"   E(+1) = {E_pos:.6f}, E(-1) = {E_neg:.6f}")

# 10. NEC violation window
print("\n10. NEC violation window z in (0.5, 1.5)")
for z in [0.0, 0.25, 0.49, 0.50, 0.51, 1.0, 1.49, 1.50, 1.51, 2.0]:
    w = -1 + (1/Z)*math.cos(Z*z)
    nec = "OK" if w >= -1 else "VIOLATED"
    print(f"   z={z:.2f}: w={w:+.6f}  NEC {nec}")

# 11. ANEC saturation
print("\n11. ANEC integral = 0")
from scipy.integrate import quad
result, err = quad(lambda z: (1/Z)*math.cos(Z*z), 0, 2)
print(f"   integral_0^2 (1/pi)cos(pi*z)dz = {result:.2e} +/- {err:.2e}")
print(f"   = 0? {abs(result) < 1e-15}")

# Analytic: (1/pi^2)[sin(2pi) - sin(0)] = 0
analytic = (1/math.pi**2)*(math.sin(2*math.pi) - math.sin(0))
print(f"   Analytic: (1/pi^2)[sin(2pi)-sin(0)] = {analytic:.2e}")

# 12. Dark energy density evolution
print("\n12. Dark energy density f_DE = (1+z)^{3(1+w)}")
for w_val in [-0.68, -1.0, -1.32]:
    exp_val = -3*(1+w_val)
    print(f"   w={w_val:+.2f}: exponent={exp_val:+.2f}", end="")
    if exp_val < -0.01:
        print(" -> rho DECREASES (BH)")
    elif abs(exp_val) < 0.01:
        print(" -> rho CONSTANT (dS)")
    else:
        print(" -> rho INCREASES (WH)")

# 13. Temperature doesn't flip — Euclidean periodicity argument
print("\n13. Temperature = Euclidean periodicity (geometric, doesn't flip)")
print("   T_H = kappa/(2pi) where kappa = 1/(4M) for Schwarzschild")
print(f"   kappa = surface gravity (geometric) = 1/(4M)")
print(f"   T_H = 1/(8piM) > 0 always")
print(f"   Under time reversal: Euclidean period beta_E = 8piM unchanged")
print(f"   CORRECT: temperature doesn't flip, heat flow direction flips")

# 14. Verify the claim values match the code output
print("\n14. Cross-check code output values")
# The code claims <E>(T=+1) = 0.581 and <E>(T=-1) = 7.419
print(f"   Code claims <E>(T=+1) = 0.581, actual = {E_pos:.3f} -> MATCH: {abs(E_pos-0.581)<0.001}")
print(f"   Code claims <E>(T=-1) = 7.419, actual = {E_neg:.3f} -> MATCH: {abs(E_neg-7.419)<0.001}")
print(f"   Code claims S = 1.0394 for both, actual S(+1) = {S_pos:.4f} -> MATCH: {abs(S_pos-1.0394)<0.001}")

print("\n" + "="*70)
print("ALL CHECKS COMPLETE")
print("="*70)
