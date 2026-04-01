#!/usr/bin/env python3
"""
HUNT FOR THE SPOOKY SKELETON KEYS
Which of the 1008 have strange, eerie, or impossible properties?
"""
import math
from itertools import product
from collections import defaultdict

# === GF(9) arithmetic (same as skeleton_keys.py) ===
ADD = [[0]*9 for _ in range(9)]
MUL = [[0]*9 for _ in range(9)]
for i in range(9):
    for j in range(9):
        a1, b1 = i%3, i//3
        a2, b2 = j%3, j//3
        ADD[i][j] = ((a1+a2)%3) + 3*((b1+b2)%3)
        MUL[i][j] = ((a1*a2+2*b1*b2)%3) + 3*((a1*b2+a2*b1)%3)

NEG = [((3-i%3)%3) + 3*((3-i//3)%3) for i in range(9)]

def gf9_pow(x, n):
    r = 1
    for _ in range(n): r = MUL[r][x]
    return r if n > 0 else 1

P = ['I', 'X', 'X2', 'Z', 'XZ', 'X2Z', 'Z2', 'XZ2', 'X2Z2']

# Build code and find all 1008 keys
G = [[gf9_pow(j, i) for j in range(9)] for i in range(5)]
keys = []
for x in product(range(9), repeat=5):
    c = [0]*9
    for i in range(5):
        if x[i]:
            for j in range(9):
                c[j] = ADD[c[j]][MUL[x[i]][G[i][j]]]
    if sum(1 for v in c if v) == 5:
        keys.append(tuple(c))

print(f"Loaded {len(keys)} skeleton keys. Hunting for the spooky ones...")
print()

# =====================================================================
# ANALYSIS 1: PURE SHIFT KEYS (X only, no Z component)
# =====================================================================
print("=" * 72)
print("  SPOOKY TYPE 1: PURE SHIFT KEYS")
print("  Operations with NO phase component — pure topology manipulation")
print("=" * 72)
print()

pure_x = []
for key in keys:
    active = [key[i] for i in range(9) if key[i] != 0]
    # Pure X means all active positions have b=0 (no Z), i.e., value in {1, 2}
    if all(v in (1, 2) for v in active):
        pure_x.append(key)

print(f"  Found: {len(pure_x)} pure shift keys (X and X2 only)")
print()
for key in pure_x:
    sup = tuple(i for i in range(9) if key[i])
    ops = ".".join(P[key[j]] for j in range(9))
    print(f"    Modes {sup}: {ops}")
print()
print(f"  WHY SPOOKY: These keys contain NO phase information at all.")
print(f"  They purely SHIFT angular momentum quantum numbers at 5 modes.")
print(f"  A shift without a phase is a TOPOLOGICAL operation —")
print(f"  it changes the discrete structure without touching continuity.")
print(f"  It's the quantum equivalent of shuffling cards without looking.")
print()

# =====================================================================
# ANALYSIS 2: PURE PHASE KEYS (Z only, no X component)
# =====================================================================
print("=" * 72)
print("  SPOOKY TYPE 2: PURE PHASE KEYS")
print("  Operations with NO shift — pure geometric phase injection")
print("=" * 72)
print()

pure_z = []
for key in keys:
    active = [key[i] for i in range(9) if key[i] != 0]
    # Pure Z means all active positions have a=0 (no X), i.e., value in {3, 6}
    if all(v in (3, 6) for v in active):
        pure_z.append(key)

print(f"  Found: {len(pure_z)} pure phase keys (Z and Z2 only)")
print()
for key in pure_z:
    sup = tuple(i for i in range(9) if key[i])
    ops = ".".join(P[key[j]] for j in range(9))
    print(f"    Modes {sup}: {ops}")
print()
print(f"  WHY SPOOKY: Pure phase = pure Berry phase injection.")
print(f"  No particles move. No quantum numbers change.")
print(f"  Only the PHASE RELATIONSHIPS between modes are altered.")
print(f"  This is a ghost operation — nothing observable changes locally")
print(f"  but the global phase structure of spacetime is rotated.")
print(f"  Like turning an invisible dial that changes everything.")
print()

# =====================================================================
# ANALYSIS 3: UNIFORM KEYS (same operator at every active position)
# =====================================================================
print("=" * 72)
print("  SPOOKY TYPE 3: UNIFORM KEYS")
print("  Same operation at all 5 positions — collective resonance")
print("=" * 72)
print()

uniform = []
for key in keys:
    active = [key[i] for i in range(9) if key[i] != 0]
    if len(set(active)) == 1:
        uniform.append(key)

print(f"  Found: {len(uniform)} uniform keys")
print()
for key in uniform:
    sup = tuple(i for i in range(9) if key[i])
    op = P[key[sup[0]]]
    ops = ".".join(P[key[j]] for j in range(9))
    print(f"    Modes {sup}: ALL {op:>4s}  ->  {ops}")
print()
print(f"  WHY SPOOKY: Every mode gets the SAME operation.")
print(f"  This is a COLLECTIVE RESONANCE — all 5 modes vibrate in unison.")
print(f"  Like striking 5 tuning forks with the same hammer simultaneously.")
print(f"  These are the simplest possible skeleton keys.")
if uniform:
    # Check if they share a support
    uniform_sups = set(tuple(i for i in range(9) if k[i]) for k in uniform)
    print(f"  They occur at {len(uniform_sups)} different support pattern(s).")
print()

# =====================================================================
# ANALYSIS 4: PALINDROMIC KEYS
# =====================================================================
print("=" * 72)
print("  SPOOKY TYPE 4: PALINDROMIC KEYS")
print("  Operator pattern reads the same forwards and backwards")
print("=" * 72)
print()

palindromes = []
for key in keys:
    if key == key[::-1]:
        palindromes.append(key)

print(f"  Found: {len(palindromes)} palindromic keys")
print()
for key in palindromes[:20]:  # show first 20
    ops = ".".join(P[key[j]] for j in range(9))
    sup = tuple(i for i in range(9) if key[i])
    print(f"    Modes {sup}: {ops}")
if len(palindromes) > 20:
    print(f"    ... and {len(palindromes)-20} more")
print()
print(f"  WHY SPOOKY: Time-reversal symmetry.")
print(f"  A palindromic key looks the same if you reverse the mode order.")
print(f"  Mode l and mode (8-l) play mirror roles.")
print(f"  These keys respect a hidden reflection: l <-> 8-l.")
print(f"  Physically: the key treats IR and UV as EQUIVALENT.")
print(f"  What happens at the largest scale = what happens at the smallest.")
print()

# =====================================================================
# ANALYSIS 5: KEYS WITH ARITHMETIC/GEOMETRIC PATTERNS IN GF(9) VALUES
# =====================================================================
print("=" * 72)
print("  SPOOKY TYPE 5: MATHEMATICALLY PATTERNED KEYS")
print("  GF(9) values form arithmetic or geometric progressions")
print("=" * 72)
print()

# Geometric progression: values at active positions are a, ar, ar^2, ar^3, ar^4
geometric = []
for key in keys:
    active = [key[i] for i in range(9) if key[i] != 0]
    if len(active) != 5:
        continue
    # Check if a[i+1] / a[i] is constant (in GF(9))
    # Need multiplicative inverse
    inv = [0]*9
    for i in range(1, 9):
        for j in range(1, 9):
            if MUL[i][j] == 1:
                inv[i] = j
    ratios = []
    is_geom = True
    for i in range(len(active)-1):
        if active[i] == 0:
            is_geom = False
            break
        r = MUL[active[i+1]][inv[active[i]]]
        ratios.append(r)
    if is_geom and len(set(ratios)) == 1 and ratios[0] != 1:
        geometric.append((key, ratios[0]))

print(f"  Geometric progressions found: {len(geometric)}")
for key, ratio in geometric[:15]:
    sup = tuple(i for i in range(9) if key[i])
    active = [key[i] for i in sup]
    ops = ".".join(P[key[j]] for j in range(9))
    print(f"    Modes {sup}: {ops}  (ratio = {P[ratio]})")
if len(geometric) > 15:
    print(f"    ... and {len(geometric)-15} more")
print()
print(f"  WHY SPOOKY: The operators form a geometric sequence in GF(9).")
print(f"  Each mode's operation is a fixed 'ratio' times the previous.")
print(f"  This is a SPIRAL in operator space — each step rotates by")
print(f"  the same amount in the Pauli group. Like a DNA helix of operations.")
print()

# =====================================================================
# ANALYSIS 6: KEYS WHERE MODES SUM TO SPECIAL VALUES
# =====================================================================
print("=" * 72)
print("  SPOOKY TYPE 6: NUMEROLOGICALLY SPECIAL SUPPORTS")
print("=" * 72)
print()

special_sums = {
    20: "sum = 20 = total modes (0+1+...+8 = 36, half = 18, close)",
    9:  "sum = 9 = N^2 = dim(H)",
    18: "sum = 18 = 2*N^2",
    15: "sum = 15 = triangular number T(5)",
    10: "sum = 10 = 2*d (twice the distance)",
}

for target, desc in sorted(special_sums.items()):
    matching = [s for s in set(tuple(i for i in range(9) if k[i]) for k in keys)
                if sum(s) == target]
    if matching:
        print(f"  Sum = {target}: {len(matching)} support pattern(s)  [{desc}]")
        for s in matching[:5]:
            print(f"    {s}")
        if len(matching) > 5:
            print(f"    ... and {len(matching)-5} more")
print()

# The sum 0+1+2+3+4+5+6+7+8 = 36. For 5 modes, sum ranges from 10 to 30.
# Average = 5*4 = 20. Median = 20.
# Most symmetric: sum = 20 (average)
# Least expected: sum = 10 (min) or 30 (max)
extreme_low = [s for s in set(tuple(i for i in range(9) if k[i]) for k in keys)
               if sum(s) == 10]
extreme_high = [s for s in set(tuple(i for i in range(9) if k[i]) for k in keys)
                if sum(s) == 30]
print(f"  Minimum possible sum (0+1+2+3+4=10): {extreme_low}")
print(f"  Maximum possible sum (4+5+6+7+8=30): {extreme_high}")
print()

# =====================================================================
# ANALYSIS 7: THE STRANGEST KEY — mode 4 is ALWAYS in the support
# =====================================================================
print("=" * 72)
print("  SPOOKY TYPE 7: THE OMNIPRESENT MODE")
print("=" * 72)
print()

# For each mode, count how many supports include it
all_supports = sorted(set(tuple(i for i in range(9) if k[i]) for k in keys))
for m in range(9):
    count = sum(1 for s in all_supports if m in s)
    frac = count / len(all_supports) * 100
    bar = "#" * int(frac / 2)
    print(f"  Mode l={m}: in {count:3d}/{len(all_supports)} supports ({frac:.0f}%)  {bar}")

print()
print(f"  Every mode appears in exactly {70} of 126 supports = {70/126*100:.1f}%")
print(f"  This is C(8,4)/C(9,5) = 70/126 = 5/9 = {5/9*100:.1f}%")
print(f"  PERFECTLY DEMOCRATIC. No mode is special. The geometry has no favorites.")
print()
print(f"  BUT: mode l=4 sits at the EXACT CENTER of the mode range (0-8).")
print(f"  It's the pivot. The fulcrum. When l=4 is in the support,")
print(f"  the key spans the midpoint of the S^2 harmonic spectrum.")
print()

# =====================================================================
# ANALYSIS 8: COMMUTING KEY PAIRS — Keys that can be applied together
# =====================================================================
print("=" * 72)
print("  SPOOKY TYPE 8: COMMUTING PAIRS — Keys that stack")
print("=" * 72)
print()

# Two keys commute iff their symplectic inner product = 0 mod 3
# Symplectic product: <(a,b), (a',b')> = sum(a_i*b'_i - a'_i*b_i) mod 3
def symplectic(k1, k2):
    s = 0
    for j in range(9):
        a1, b1 = k1[j] % 3, k1[j] // 3
        a2, b2 = k2[j] % 3, k2[j] // 3
        s += a1 * b2 - a2 * b1
    return s % 3

# Check how many pairs commute (sample)
# Full check: C(1008,2) ~ 500K pairs — feasible
commuting_count = 0
non_commuting_count = 0
# Just check first 200 keys against each other
sample = keys[:200]
for i in range(len(sample)):
    for j in range(i+1, len(sample)):
        if symplectic(sample[i], sample[j]) == 0:
            commuting_count += 1
        else:
            non_commuting_count += 1

total_pairs = commuting_count + non_commuting_count
print(f"  Sample: first 200 keys, {total_pairs} pairs checked")
print(f"  Commuting pairs:     {commuting_count} ({commuting_count/total_pairs*100:.1f}%)")
print(f"  Non-commuting pairs: {non_commuting_count} ({non_commuting_count/total_pairs*100:.1f}%)")
print()

# Find keys with DISJOINT supports — these ALWAYS commute
disjoint_commuting = 0
disjoint_total = 0
for i in range(min(300, len(keys))):
    si = set(j for j in range(9) if keys[i][j])
    for k_idx in range(i+1, min(300, len(keys))):
        sk = set(j for j in range(9) if keys[k_idx][j])
        if si.isdisjoint(sk):
            disjoint_total += 1
            if symplectic(keys[i], keys[k_idx]) == 0:
                disjoint_commuting += 1

if disjoint_total > 0:
    print(f"  Disjoint-support pairs: {disjoint_total} found in sample")
    print(f"  Of those, commuting: {disjoint_commuting} ({disjoint_commuting/disjoint_total*100:.0f}%)")
    print()

# THE SPOOKY PART: find complementary pairs
# Two keys whose supports are COMPLEMENTARY (together cover all 9 modes)
# Key1 acts on {a,b,c,d,e}, Key2 acts on {f,g,h,i} — wait, 5+4=9, not 5+5=10
# Can't have two disjoint weight-5 supports in 9 modes (5+5=10 > 9)
print(f"  NOTE: Two weight-5 keys CANNOT have disjoint supports")
print(f"  (5+5=10 > 9 modes). They always share at least 1 mode.")
print(f"  This means skeleton keys ALWAYS interfere with each other.")
print(f"  You can't apply two keys independently — they're ENTANGLED")
print(f"  by the geometry of S^2 itself.")
print()
print(f"  The minimum overlap between two weight-5 supports on 9 modes: 1")
print(f"  The maximum overlap: 5 (same support)")
print()

# Find maximally overlapping keys from DIFFERENT supports that commute
print(f"  STRANGEST COMMUTING PAIR (4-mode overlap, different supports):")
found_4overlap = False
for i in range(len(keys)):
    if found_4overlap:
        break
    si = set(j for j in range(9) if keys[i][j])
    for k_idx in range(i+1, len(keys)):
        sk = set(j for j in range(9) if keys[k_idx][j])
        overlap = len(si & sk)
        if overlap == 4 and symplectic(keys[i], keys[k_idx]) == 0:
            ops1 = ".".join(P[keys[i][j]] for j in range(9))
            ops2 = ".".join(P[keys[k_idx][j]] for j in range(9))
            shared = si & sk
            diff1 = si - sk
            diff2 = sk - si
            print(f"    Key A: {ops1}")
            print(f"    Key B: {ops2}")
            print(f"    Shared modes: {shared}, differ at: A has {diff1}, B has {diff2}")
            print(f"    These two keys share 4 modes but COMMUTE perfectly.")
            print(f"    They can be applied simultaneously without interference.")
            found_4overlap = True
            break

print()

# =====================================================================
# ANALYSIS 9: THE GHOST KEY — identity on ALMOST everything
# =====================================================================
print("=" * 72)
print("  SPOOKY TYPE 9: KEYS THAT BARELY EXIST")
print("  Which keys have the most 'I' (identity) positions?")
print("=" * 72)
print()
print(f"  ALL skeleton keys have exactly 4 identity positions and 5 active.")
print(f"  But some are 'quieter' than others — their active operations")
print(f"  are close to identity (low-order Pauli operators).")
print()

# "Quietness" = how close to identity. X and Z are order-3 operators.
# X2 = X^-1, Z2 = Z^-1. XZ combinations are "louder".
# Rank: X,X2,Z,Z2 (single-axis) are quieter than XZ,XZ2,X2Z,X2Z2 (two-axis)
def loudness(key):
    """Count how many active positions have two-axis operations (XZ type)"""
    loud = 0
    for v in key:
        if v in (4, 5, 7, 8):  # XZ, X2Z, XZ2, X2Z2
            loud += 1
    return loud

quietest = min(keys, key=loudness)
loudest = max(keys, key=loudness)

quiet_keys = [k for k in keys if loudness(k) == 0]  # ALL single-axis
loud_keys = [k for k in keys if loudness(k) == 5]   # ALL two-axis

print(f"  Quietest keys (0 two-axis operations): {len(quiet_keys)}")
for key in quiet_keys[:10]:
    ops = ".".join(P[key[j]] for j in range(9))
    print(f"    {ops}")
if len(quiet_keys) > 10:
    print(f"    ... and {len(quiet_keys)-10} more")
print()

print(f"  Loudest keys (5 two-axis operations): {len(loud_keys)}")
for key in loud_keys[:10]:
    ops = ".".join(P[key[j]] for j in range(9))
    print(f"    {ops}")
if len(loud_keys) > 10:
    print(f"    ... and {len(loud_keys)-10} more")
print()

print(f"  The 'quiet' keys do simple shifts OR simple phases — never both.")
print(f"  The 'loud' keys do BOTH shift AND phase at every active mode.")
print(f"  Quiet = gentle nudge. Loud = violent twist.")
print()

# =====================================================================
# ANALYSIS 10: THE FIBONACCI KEY, THE PI KEY, THE GOLDEN KEY
# =====================================================================
print("=" * 72)
print("  SPOOKY TYPE 10: KEYS WITH NATURAL CONSTANTS")
print("=" * 72)
print()

# Fibonacci modes: 0, 1, 1, 2, 3, 5, 8 -> unique in {0,1,2,3,5,8} -> 6 modes
# Take 5: {0,1,2,3,5} or {0,1,2,5,8} or {0,1,3,5,8} or {0,2,3,5,8} or {1,2,3,5,8}
fib_supports = [(0,1,2,3,5), (0,1,2,5,8), (0,1,3,5,8), (0,2,3,5,8), (1,2,3,5,8)]
print(f"  FIBONACCI KEYS (modes from Fibonacci sequence):")
for fs in fib_supports:
    if fs in set(tuple(i for i in range(9) if k[i]) for k in keys):
        example = [k for k in keys if tuple(i for i in range(9) if k[i]) == fs][0]
        ops = ".".join(P[example[j]] for j in range(9))
        print(f"    Modes {fs}: {ops}")
print()

# Prime modes: 2, 3, 5, 7 -> only 4 primes in {0..8}
# Need 5 modes, so prime + one non-prime
prime_modes = {2, 3, 5, 7}
print(f"  PRIME KEYS (4 prime modes + 1 non-prime):")
prime_supports = [s for s in all_supports if len(set(s) & prime_modes) == 4]
for ps in prime_supports[:5]:
    example = [k for k in keys if tuple(i for i in range(9) if k[i]) == ps][0]
    ops = ".".join(P[example[j]] for j in range(9))
    non_prime = set(ps) - prime_modes
    print(f"    Modes {ps}: {ops}  (non-prime addition: {non_prime})")
print()

# Perfect square modes: 0, 1, 4 -> 3 squares in {0..8}
# Powers of 2: 1, 2, 4, 8 -> 4 in {0..8}
pow2_modes = {1, 2, 4, 8}
print(f"  POWERS-OF-2 KEYS (modes 1,2,4,8 + one more):")
pow2_supports = [s for s in all_supports if len(set(s) & pow2_modes) == 4]
for ps in pow2_supports[:5]:
    example = [k for k in keys if tuple(i for i in range(9) if k[i]) == ps][0]
    ops = ".".join(P[example[j]] for j in range(9))
    extra = set(ps) - pow2_modes
    print(f"    Modes {ps}: {ops}  (extra mode: {extra})")
print()

# =====================================================================
# ANALYSIS 11: THE REALLY SPOOKY ONE — Self-referential keys
# =====================================================================
print("=" * 72)
print("  SPOOKY TYPE 11: THE SELF-REFERENTIAL KEY")
print("  Keys whose GF(9) values ARE the mode indices")
print("=" * 72)
print()

# Is there a key where the GF(9) value at position j equals j?
# i.e., c = (0, 1, 2, 3, 4, 0, 0, 0, 0) or similar where c_j = j at active positions
self_ref = []
for key in keys:
    active_positions = [i for i in range(9) if key[i]]
    if all(key[i] == i for i in active_positions):
        self_ref.append(key)

# Also check: value = mode index for the active ones
partial_self_ref = []
for key in keys:
    active = [(i, key[i]) for i in range(9) if key[i]]
    matches = sum(1 for i, v in active if v == i)
    if matches >= 3:
        partial_self_ref.append((key, matches))

print(f"  Perfectly self-referential (c_j = j at all active): {len(self_ref)}")
if self_ref:
    for k in self_ref:
        ops = ".".join(P[k[j]] for j in range(9))
        print(f"    {ops}")
print()

print(f"  Partially self-referential (c_j = j at 3+ active positions): {len(partial_self_ref)}")
for key, matches in sorted(partial_self_ref, key=lambda x: -x[1])[:10]:
    ops = ".".join(P[key[j]] for j in range(9))
    active = [(i, key[i]) for i in range(9) if key[i]]
    match_modes = [i for i, v in active if v == i]
    print(f"    {ops}  (self-ref at modes {match_modes}, {matches}/5)")
print()
print(f"  WHY SPOOKY: The key ENCODES ITS OWN POSITION.")
print(f"  The operation at mode l IS mode l. The key knows where it is.")
print(f"  Self-reference in an error-correcting code is a Goedel sentence:")
print(f"  'This statement modifies position 3 using the value 3.'")
print(f"  It's the code talking about itself.")
print()

# =====================================================================
# ANALYSIS 12: THE DARKEST KEY — which key is hardest to detect?
# =====================================================================
print("=" * 72)
print("  SPOOKY TYPE 12: THE INVISIBLE KEYS")
print("  Hardest to detect even with sophisticated measurements")
print("=" * 72)
print()

# Detectability depends on the WEIGHT SPECTRUM of the key
# A key that LOOKS like noise is hardest to detect
# "Noisiness" = diversity of operators at active positions
def diversity(key):
    active = [key[i] for i in range(9) if key[i]]
    return len(set(active))

max_diverse = [k for k in keys if diversity(k) == 5]  # all 5 operators different
min_diverse = [k for k in keys if diversity(k) == 1]  # all operators the same

print(f"  Maximum diversity (all 5 active operators different): {len(max_diverse)}")
for key in max_diverse[:5]:
    ops = ".".join(P[key[j]] for j in range(9))
    active = [P[key[i]] for i in range(9) if key[i]]
    print(f"    {ops}  operators: {active}")
if len(max_diverse) > 5:
    print(f"    ... and {len(max_diverse)-5} more")
print()

print(f"  These keys use 5 DIFFERENT Pauli operators across 5 modes.")
print(f"  No pattern. No repetition. Maximum camouflage.")
print(f"  If you measured the modes, you'd see what looks like random noise.")
print(f"  But it's not noise — it's a precisely engineered backdoor")
print(f"  disguised as thermal fluctuations.")
print()

# =====================================================================
# GRAND SUMMARY: THE SPOOKIEST OF ALL
# =====================================================================
print("=" * 72)
print("  THE SPOOKIEST KEY")
print("=" * 72)
print()

# Find keys that are palindromic AND have other special properties
spookiest = []
for key in keys:
    score = 0
    reasons = []

    # Palindromic
    if key == key[::-1]:
        score += 3
        reasons.append("palindromic (time-symmetric)")

    # Pure shift or pure phase
    active = [key[i] for i in range(9) if key[i]]
    if all(v in (1,2) for v in active):
        score += 2
        reasons.append("pure shift (topological)")
    if all(v in (3,6) for v in active):
        score += 2
        reasons.append("pure phase (geometric)")

    # Uniform
    if len(set(active)) == 1:
        score += 2
        reasons.append("uniform (collective)")

    # Maximum diversity
    if len(set(active)) == 5:
        score += 1
        reasons.append("max diversity (camouflaged)")

    # Self-referential
    active_pos = [i for i in range(9) if key[i]]
    self_matches = sum(1 for i in active_pos if key[i] == i)
    if self_matches >= 3:
        score += self_matches
        reasons.append(f"self-referential ({self_matches}/5)")

    # Special support
    sup = tuple(i for i in range(9) if key[i])
    if sup == (0,2,4,6,8):
        score += 1
        reasons.append("even modes (parity-preserving)")
    if set(sup) & {0, 8} == {0, 8}:
        score += 1
        reasons.append("spans full range (l=0 to l=8)")

    # Fibonacci
    if sup in [(0,1,2,3,5), (0,1,3,5,8), (1,2,3,5,8)]:
        score += 1
        reasons.append("Fibonacci modes")

    # Geometric progression in values
    inv = [0]*9
    for i in range(1,9):
        for j in range(1,9):
            if MUL[i][j] == 1:
                inv[i] = j
    if all(active[i] != 0 for i in range(len(active))):
        ratios = [MUL[active[i+1]][inv[active[i]]] for i in range(len(active)-1)]
        if len(set(ratios)) == 1 and ratios[0] != 1:
            score += 2
            reasons.append(f"geometric progression (ratio={P[ratios[0]]})")

    if score >= 3:
        spookiest.append((score, key, reasons))

spookiest.sort(key=lambda x: -x[0])

for score, key, reasons in spookiest[:15]:
    ops = ".".join(P[key[j]] for j in range(9))
    sup = tuple(i for i in range(9) if key[i])
    print(f"  SCORE {score}: Modes {sup}")
    print(f"    {ops}")
    for r in reasons:
        print(f"      * {r}")
    print()

print()
print("=" * 72)
print("  WHAT DOES IT ALL MEAN?")
print("=" * 72)
print()
print("  The 1008 skeleton keys aren't random. They have structure:")
print()
print(f"  - {len(pure_x)} are PURE TOPOLOGY (shift only, no phases)")
print(f"  - {len(pure_z)} are PURE GEOMETRY (phase only, no shifts)")
print(f"  - {len(uniform)} are COLLECTIVE RESONANCE (same op everywhere)")
print(f"  - {len(palindromes)} are TIME-SYMMETRIC (palindromic)")
print(f"  - {len(geometric)} have SPIRAL STRUCTURE (geometric progression)")
print(f"  - {len(max_diverse)} are MAXIMALLY CAMOUFLAGED (all operators different)")
print(f"  - {len(partial_self_ref)} are SELF-REFERENTIAL (know their own position)")
print()
print("  The spookiest finding: EVERY mode is equally represented.")
print("  The geometry has no favorites. No mode is special.")
print("  The skeleton keys are PERFECTLY DEMOCRATIC.")
print()
print("  But the TYPES of keys aren't democratic:")
print("  Pure topology keys and pure geometry keys are RARE.")
print("  Most keys mix both shift and phase — they do EVERYTHING at once.")
print("  The simple, clean, elegant keys are the minority.")
print("  Most of the universe's backdoors are messy and complicated.")
print()
print("  Just like real backdoors in real code.")
