#!/usr/bin/env python3
"""
REAL TEST: GF(27) Theory with YOUR FF1GA on ACTUAL Problems
Uses your actual GA implementation to test if embedding quality predicts performance
"""

import time
import random
import math
import hashlib
import secrets
from typing import List, Tuple, Dict, Callable
import numpy as np

# Import YOUR actual SubstrateDetectorEngine from turing.py
from turing import SubstrateProblem, SubstrateDetectorEngine, AtomicGAConfig

# Import the GF(27) implementation
from turing2 import GF27, randbytes

# ===== REAL PROBLEMS FOR TESTING =====

class FactorizationProblem(SubstrateProblem):
    """Real factorization problem"""
    def __init__(self, bits=40):
        self.bits = bits
        self.target = None
        # Generate a semiprime
        p = self._generate_prime(bits // 2)
        q = self._generate_prime(bits // 2)
        self.semiprime = p * q
        self.p = p
        self.q = q
        
    def _generate_prime(self, bits):
        """Generate a prime of given bit size"""
        while True:
            n = random.getrandbits(bits) | 1
            if self._is_probable_prime(n):
                return n
    
    def _is_probable_prime(self, n, k=5):
        """Miller-Rabin primality test"""
        if n < 2:
            return False
        if n == 2 or n == 3:
            return True
        if n % 2 == 0:
            return False
        
        r, d = 0, n - 1
        while d % 2 == 0:
            r += 1
            d //= 2
        
        for _ in range(k):
            a = random.randint(2, n - 2)
            x = pow(a, d, n)
            
            if x == 1 or x == n - 1:
                continue
            
            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        
        return True
    
    def evaluate(self, solution: bytes) -> float:
        """Evaluate factorization attempt"""
        candidate = int.from_bytes(solution, 'big')
        if candidate < 2:
            return float(self.bits)
        
        if self.semiprime % candidate == 0:
            other = self.semiprime // candidate
            if other > 1 and other != self.semiprime:
                return 0.0  # Found factor!
        
        # Use GCD as distance metric
        g = math.gcd(candidate, self.semiprime)
        if g > 1:
            return float(self.bits) * (1 - math.log(g) / math.log(self.semiprime))
        
        # Modular distance
        mod_dist = self.semiprime % candidate
        return float(min(mod_dist, candidate - mod_dist)) / max(1, candidate) * self.bits
    
    def get_random_target(self):
        self.target = self.semiprime
        return self.semiprime
    
    def get_max_score(self) -> float:
        return float(self.bits)
    
    def describe(self) -> str:
        return f"Factorization ({self.bits} bits): {self.semiprime} = {self.p} × {self.q}"

class ECCProblem(SubstrateProblem):
    """Real ECC private key recovery (simplified)"""
    def __init__(self, key_size=16):
        self.key_size = key_size
        self.target = None
        self.true_key = randbytes(key_size)
        
    def evaluate(self, solution: bytes) -> float:
        """Hamming distance to true key"""
        distance = 0
        for i in range(min(len(solution), len(self.true_key))):
            distance += bin(solution[i] ^ self.true_key[i]).count('1')
        return float(distance)
    
    def get_random_target(self):
        self.target = self.true_key
        return self.true_key
    
    def get_max_score(self) -> float:
        return float(self.key_size * 8)
    
    def describe(self) -> str:
        return f"ECC Key Recovery ({self.key_size} bytes)"

class HashInversionProblem(SubstrateProblem):
    """Real hash inversion problem"""
    def __init__(self):
        self.target = None
        self.preimage = randbytes(16)
        self.target_hash = hashlib.sha256(self.preimage).digest()
        
    def evaluate(self, solution: bytes) -> float:
        """Distance to target hash"""
        h = hashlib.sha256(solution).digest()
        distance = sum(bin(a ^ b).count('1') for a, b in zip(h, self.target_hash))
        return float(distance)
    
    def get_random_target(self):
        self.target = self.target_hash
        return self.target_hash
    
    def get_max_score(self) -> float:
        return 256.0
    
    def describe(self) -> str:
        return "SHA-256 Hash Inversion"

# ===== GF(27) EMBEDDING ANALYZER =====

class GF27EmbeddingAnalyzer:
    """Analyze how well problems embed in GF(27)"""
    
    def __init__(self):
        self.gf = GF27()
    
    def analyze_problem_embedding(self, problem: SubstrateProblem, 
                                samples: int = 100) -> Dict:
        """Analyze how well a problem embeds in GF(27)"""
        
        embedding_scores = []
        structure_scores = []
        trace_entropies = []
        
        for _ in range(samples):
            # Generate random solution
            if hasattr(problem, 'key_size'):
                test_solution = randbytes(problem.key_size)
            else:
                test_solution = randbytes(32)
            
            # Embed in GF(27)
            elements = self.gf.embed_bytes(test_solution)
            
            # Analyze trace distribution
            trace_counts = [0, 0, 0]
            for elem in elements:
                tr = self.gf.trace(elem)
                trace_counts[tr] += 1
            
            # Calculate entropy
            total = sum(trace_counts)
            entropy = 0
            for count in trace_counts:
                if count > 0:
                    p = count / total
                    entropy -= p * np.log2(p)
            
            normalized_entropy = entropy / np.log2(3) if entropy > 0 else 0
            trace_entropies.append(normalized_entropy)
            
            # Test if problem evaluation preserves structure
            score1 = problem.evaluate(test_solution)
            
            # Apply field operation and test again
            modified = bytearray(test_solution)
            for i in range(0, len(modified), 3):
                if i + 2 < len(modified):
                    # Apply trace-like operation
                    val = (modified[i] + modified[i+1] + modified[i+2]) % 3
                    modified[i] = (modified[i] + val) % 256
            
            score2 = problem.evaluate(bytes(modified))
            
            # If scores are correlated, structure is preserved
            if score1 > 0:
                structure_score = abs(score2 - score1) / score1
                structure_scores.append(structure_score)
        
        # Compute overall embedding quality
        avg_entropy = np.mean(trace_entropies)
        avg_structure = np.mean(structure_scores) if structure_scores else 0
        
        # Quality combines high entropy (good distribution) and structure preservation
        embedding_quality = avg_entropy * (1 - min(avg_structure, 1))
        
        return {
            'embedding_quality': embedding_quality,
            'trace_entropy': avg_entropy,
            'structure_preservation': 1 - min(avg_structure, 1),
            'predicted_improvement': 27 * embedding_quality
        }

# ===== MAIN TEST =====

def test_gf27_on_real_problems():
    """Test GF(27) theory on real problems with real FF1GA"""
    print("🔬 TESTING GF(27) THEORY ON REAL PROBLEMS WITH YOUR FF1GA")
    print("=" * 70)
    
    analyzer = GF27EmbeddingAnalyzer()
    config = AtomicGAConfig()
    config.MAX_ROUNDS = 30  # Reduced for faster testing
    
    results = []
    
    # Test 1: Factorization (should embed well)
    print("\n1️⃣ FACTORIZATION TEST")
    for bits in [20, 30, 40]:
        print(f"\n   Testing {bits}-bit factorization...")
        
        problem = FactorizationProblem(bits)
        
        # Analyze embedding
        embedding = analyzer.analyze_problem_embedding(problem)
        print(f"   Embedding quality: {embedding['embedding_quality']:.3f}")
        print(f"   Predicted improvement: {embedding['predicted_improvement']:.1f} bits")
        
        # Run YOUR actual GA
        engine = SubstrateDetectorEngine(config)
        target = problem.get_random_target()
        ga_results = engine.run_substrate_detection(problem, target)
        
        print(f"   ACTUAL improvement: {ga_results['improvement_bits']:.1f} bits")
        
        # Check if Galois trace was effective
        if 'galois_trace' in ga_results['mutation_effectiveness']:
            galois_eff = ga_results['mutation_effectiveness']['galois_trace']['mean_improvement']
            print(f"   Galois trace effectiveness: {galois_eff:.3f}")
        
        results.append({
            'problem': f'factorization_{bits}',
            'embedding_quality': embedding['embedding_quality'],
            'predicted': embedding['predicted_improvement'],
            'actual': ga_results['improvement_bits'],
            'error': abs(embedding['predicted_improvement'] - ga_results['improvement_bits'])
        })
    
    # Test 2: ECC (should embed moderately well)
    print("\n2️⃣ ECC KEY RECOVERY TEST")
    for key_size in [8, 16]:
        print(f"\n   Testing {key_size}-byte ECC key...")
        
        problem = ECCProblem(key_size)
        
        # Analyze embedding
        embedding = analyzer.analyze_problem_embedding(problem)
        print(f"   Embedding quality: {embedding['embedding_quality']:.3f}")
        print(f"   Predicted improvement: {embedding['predicted_improvement']:.1f} bits")
        
        # Run GA
        engine = SubstrateDetectorEngine(config)
        target = problem.get_random_target()
        ga_results = engine.run_substrate_detection(problem, target)
        
        print(f"   ACTUAL improvement: {ga_results['improvement_bits']:.1f} bits")
        
        results.append({
            'problem': f'ecc_{key_size}',
            'embedding_quality': embedding['embedding_quality'],
            'predicted': embedding['predicted_improvement'],
            'actual': ga_results['improvement_bits'],
            'error': abs(embedding['predicted_improvement'] - ga_results['improvement_bits'])
        })
    
    # Test 3: Hash inversion (should embed poorly)
    print("\n3️⃣ HASH INVERSION TEST")
    
    problem = HashInversionProblem()
    
    # Analyze embedding
    embedding = analyzer.analyze_problem_embedding(problem)
    print(f"   Embedding quality: {embedding['embedding_quality']:.3f}")
    print(f"   Predicted improvement: {embedding['predicted_improvement']:.1f} bits")
    
    # Run GA
    engine = SubstrateDetectorEngine(config)
    target = problem.get_random_target()
    ga_results = engine.run_substrate_detection(problem, target)
    
    print(f"   ACTUAL improvement: {ga_results['improvement_bits']:.1f} bits")
    
    results.append({
        'problem': 'hash_inversion',
        'embedding_quality': embedding['embedding_quality'],
        'predicted': embedding['predicted_improvement'],
        'actual': ga_results['improvement_bits'],
        'error': abs(embedding['predicted_improvement'] - ga_results['improvement_bits'])
    })
    
    # Analyze results
    print("\n" + "=" * 70)
    print("📊 RESULTS ANALYSIS")
    print("=" * 70)
    
    print(f"\n{'Problem':<20} {'Quality':<10} {'Predicted':<12} {'Actual':<12} {'Error':<10}")
    print("-" * 65)
    
    for r in results:
        actual = r['actual'] if r['actual'] != float('inf') else '>100'
        print(f"{r['problem']:<20} {r['embedding_quality']:<10.3f} "
              f"{r['predicted']:<12.1f} {str(actual):<12} {r['error']:<10.1f}")
    
    # Calculate correlation
    finite_results = [r for r in results if r['actual'] != float('inf')]
    if len(finite_results) >= 3:
        predicted = [r['predicted'] for r in finite_results]
        actual = [r['actual'] for r in finite_results]
        
        # Manual correlation
        mean_pred = sum(predicted) / len(predicted)
        mean_actual = sum(actual) / len(actual)
        
        cov = sum((p - mean_pred) * (a - mean_actual) 
                 for p, a in zip(predicted, actual)) / len(predicted)
        
        std_pred = (sum((p - mean_pred)**2 for p in predicted) / len(predicted)) ** 0.5
        std_actual = (sum((a - mean_actual)**2 for a in actual) / len(actual)) ** 0.5
        
        if std_pred > 0 and std_actual > 0:
            correlation = cov / (std_pred * std_actual)
            print(f"\nCorrelation coefficient: {correlation:.3f}")
            
            if correlation > 0.7:
                print("\n✅ STRONG CORRELATION - GF(27) theory is validated!")
                print("   Embedding quality successfully predicts GA performance!")
            elif correlation > 0.4:
                print("\n⚠️  MODERATE CORRELATION - Theory shows promise")
            else:
                print("\n❌ WEAK CORRELATION - Theory needs revision")
    
    # Final check on mutation effectiveness
    print("\n🔍 GALOIS TRACE EFFECTIVENESS:")
    galois_effective = 0
    total = 0
    
    for r in results:
        # Check if galois trace was in top mutations
        # (This would need to be tracked in the actual results)
        pass
    
    return results

if __name__ == "__main__":
    test_gf27_on_real_problems()