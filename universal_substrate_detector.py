#!/usr/bin/env python3
"""
UNIVERSAL SUBSTRATE DETECTOR - Atomic GA Engine
Testing if the ~27-bit improvement phenomenon is universal
"""

import time
import random
import math
import hashlib
import struct
import numpy as np
from typing import List, Tuple, Callable, Optional, Dict, Any
from dataclasses import dataclass
from collections import deque
import statistics
import json
from abc import ABC, abstractmethod

@dataclass
class AtomicGAConfig:
    """Core GA configuration - problem agnostic"""
    K_POOL: int = 8000
    ELITE_SIZE: int = 400
    
    MUTATION_STRENGTH: float = 0.6
    MUTATION_DECAY: float = 0.97
    MUTATION_INCREASE: float = 1.3
    MUTATION_MIN: float = 0.15
    MUTATION_MAX: float = 1.2
    
    STAGNATION_ROUNDS: int = 4
    DIVERSITY_INJECTION_RATE: float = 0.4
    
    # Adaptive hex learning parameters
    INITIAL_ACTIVE_BYTES: int = 1
    EXPANSION_THRESHOLD: float = 0.05
    CONTRACTION_THRESHOLD: float = 0.1
    RANGE_ADAPTATION_FREQ: int = 2
    AGGRESSIVE_EXPANSION: bool = True
    
    # Position learning
    POSITION_LEARNING_RATE: float = 0.08
    POSITION_DECAY: float = 0.98
    GLOBAL_WEIGHT_DECAY: float = 0.998
    MIN_POSITION_WEIGHT: float = 0.05
    MAX_POSITION_WEIGHT: float = 0.75
    
    MAX_ROUNDS: int = 50  # More rounds for exploration
    KEY_SIZE: int = 32    # Default 256 bits

class SubstrateProblem(ABC):
    """Abstract base for any problem we want to test"""
    
    @abstractmethod
    def evaluate(self, solution: bytes) -> float:
        """Evaluate fitness - lower is better"""
        pass
    
    @abstractmethod
    def get_random_target(self) -> Any:
        """Generate random target for this problem"""
        pass
    
    @abstractmethod
    def get_max_score(self) -> float:
        """Maximum (worst) possible score"""
        pass
    
    @abstractmethod
    def describe(self) -> str:
        """Human-readable description"""
        pass

class AtomicAdaptiveHexManager:
    """The core learning engine - problem agnostic"""
    
    def __init__(self, config: AtomicGAConfig):
        self.config = config
        self.key_size = config.KEY_SIZE
        self.current_active_bytes = config.INITIAL_ACTIVE_BYTES
        self.max_active_bytes = self.key_size
        
        # Position importance weights
        self.position_weights = np.ones(self.key_size, dtype=np.float32)
        self.position_usage_stats = np.zeros(self.key_size, dtype=np.float32)
        self.position_performance = np.zeros(self.key_size, dtype=np.float32)
        
        # Range performance tracking
        self.range_performance = {}
        self.generation_count = 0
        
        # SUBSTRATE DETECTION - Track everything
        self.mutation_trace = []  # Every mutation and its effect
        self.gradient_samples = []  # Local gradient measurements
        self.transform_effectiveness = {}  # Which transforms work
        self.learning_trajectory = []  # Full path through solution space
        
    def get_active_range(self) -> int:
        """Get current maximum value for active bytes"""
        if self.current_active_bytes <= 0:
            return 1
        max_bits = min(self.current_active_bytes * 8, self.key_size * 8)
        return (2 ** max_bits) - 1
    
    def generate_adaptive_key(self) -> bytes:
        """Generate key using learned patterns"""
        self.generation_count += 1
        
        max_value = self.get_active_range()
        
        # Choose generation strategy
        if random.random() < 0.8:
            key_value = self._generate_position_focused_key(max_value)
        else:
            key_value = self._generate_exploratory_key(max_value)
        
        # Record for substrate analysis
        self.learning_trajectory.append({
            'generation': self.generation_count,
            'active_bytes': self.current_active_bytes,
            'position_weights': self.position_weights.copy(),
            'key_value': key_value
        })
        
        return key_value.to_bytes(self.key_size, 'big')
    
    def _generate_position_focused_key(self, max_value: int) -> int:
        """Generate using learned positions"""
        key_bytes = [0] * self.key_size
        
        for byte_pos in range(min(self.current_active_bytes, self.key_size)):
            weight = self.position_weights[byte_pos]
            
            if random.random() < min(0.9, weight + 0.2):
                if random.random() < 0.4:
                    key_bytes[byte_pos] = random.randint(0, 255)
                else:
                    if random.random() < 0.5:
                        patterns = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0xFF]
                        key_bytes[byte_pos] = random.choice(patterns)
                    else:
                        key_bytes[byte_pos] = random.randint(1, 255)
        
        key_value = 0
        for i, byte_val in enumerate(key_bytes[:self.current_active_bytes]):
            key_value += byte_val * (256 ** i)
        
        return max(1, min(key_value, max_value))
    
    def _generate_exploratory_key(self, max_value: int) -> int:
        """Explore the solution space"""
        exploration_patterns = [
            lambda: random.randint(1, max_value),
            lambda: random.randint(max_value // 2, max_value),
            lambda: random.randint(max_value // 4, max_value // 2),
            lambda: random.randint(1, max_value // 10),
            lambda: int(max_value * (random.random() ** 0.5)),
            lambda: int(max_value * random.random()),
        ]
        
        pattern_func = random.choice(exploration_patterns)
        try:
            return max(1, min(pattern_func(), max_value))
        except:
            return random.randint(1, max_value)
    
    def learn_from_mutation(self, old_key: bytes, new_key: bytes, improvement: float, 
                          mutation_type: str = "unknown"):
        """Learn what works - RECORD EVERYTHING"""
        if improvement <= 0:
            return
        
        # Record successful mutation for substrate analysis
        self.mutation_trace.append({
            'generation': self.generation_count,
            'old_key': int.from_bytes(old_key, 'big'),
            'new_key': int.from_bytes(new_key, 'big'),
            'improvement': improvement,
            'mutation_type': mutation_type,
            'active_bytes': self.current_active_bytes
        })
        
        # Update position learning
        for byte_pos in range(min(self.current_active_bytes, self.key_size)):
            if byte_pos < len(old_key) and byte_pos < len(new_key):
                old_byte = old_key[byte_pos]
                new_byte = new_key[byte_pos]
                
                if old_byte != new_byte:
                    learning_factor = improvement * self.config.POSITION_LEARNING_RATE
                    old_weight = self.position_weights[byte_pos]
                    new_weight = min(self.config.MAX_POSITION_WEIGHT, old_weight + learning_factor)
                    self.position_weights[byte_pos] = new_weight
                    self.position_performance[byte_pos] += improvement
                    self.position_usage_stats[byte_pos] += 1
        
        # Track transform effectiveness
        if mutation_type not in self.transform_effectiveness:
            self.transform_effectiveness[mutation_type] = []
        self.transform_effectiveness[mutation_type].append(improvement)
    
    def analyze_population_ranges(self, population: List[bytes], scores: List[float]):
        """Analyze which key ranges are performing well"""
        if not population:
            return
        
        range_improvements = {}
        
        for key, score in zip(population, scores):
            if score >= self.config.KEY_SIZE * 8:  # Skip terrible scores
                continue
            
            # Find effective byte length
            effective_bytes = 1
            key_int = int.from_bytes(key, 'big')
            if key_int > 0:
                effective_bytes = (key_int.bit_length() + 7) // 8
            
            effective_bytes = max(1, min(effective_bytes, self.key_size))
            
            improvement = self.config.KEY_SIZE * 8 - score  # Higher is better
            if effective_bytes not in range_improvements:
                range_improvements[effective_bytes] = []
            range_improvements[effective_bytes].append(improvement)
        
        # Update range performance history
        for byte_range, improvements in range_improvements.items():
            if improvements:
                avg_improvement = statistics.mean(improvements)
                if byte_range not in self.range_performance:
                    self.range_performance[byte_range] = []
                self.range_performance[byte_range].append(avg_improvement)
                
                # Keep only recent history
                if len(self.range_performance[byte_range]) > 10:
                    self.range_performance[byte_range] = self.range_performance[byte_range][-10:]
    
    def adapt_active_range(self, round_num: int, elite_scores: List[float]):
        """Adaptive range based on performance"""
        if round_num % self.config.RANGE_ADAPTATION_FREQ != 0:
            return
        
        old_range = self.current_active_bytes
        
        # Only expand/contract based on performance data
        if len(self.range_performance) >= 2:
            current_avg_perf = 0
            if self.current_active_bytes in self.range_performance:
                recent_perfs = self.range_performance[self.current_active_bytes]
                current_avg_perf = statistics.mean(recent_perfs) if recent_perfs else 0
            
            # Check if larger ranges are performing better
            larger_ranges = [r for r in self.range_performance.keys() 
                           if r > self.current_active_bytes]
            best_larger_perf = 0
            if larger_ranges:
                larger_perfs = []
                for r in larger_ranges:
                    if self.range_performance[r]:
                        larger_perfs.extend(self.range_performance[r])
                if larger_perfs:
                    best_larger_perf = max(larger_perfs)
            
            # Check if smaller ranges are performing better
            smaller_ranges = [r for r in self.range_performance.keys() 
                            if r < self.current_active_bytes and r >= 1]
            best_smaller_perf = 0
            if smaller_ranges:
                smaller_perfs = []
                for r in smaller_ranges:
                    if self.range_performance[r]:
                        smaller_perfs.extend(self.range_performance[r])
                if smaller_perfs:
                    best_smaller_perf = max(smaller_perfs)
            
            # Performance-based decision
            if (best_larger_perf > current_avg_perf and 
                best_larger_perf > best_smaller_perf and
                self.current_active_bytes < self.max_active_bytes):
                self.current_active_bytes = min(self.current_active_bytes + 1,
                                              self.max_active_bytes)
            
            elif (best_smaller_perf > current_avg_perf and 
                  best_smaller_perf > best_larger_perf and
                  self.current_active_bytes > 1):
                self.current_active_bytes = max(1, self.current_active_bytes - 1)
    
    def apply_global_weight_decay(self):
        """Apply weight decay to prevent lock-in"""
        for byte_pos in range(self.key_size):
            # Apply global decay to all positions
            self.position_weights[byte_pos] *= self.config.GLOBAL_WEIGHT_DECAY
            # Ensure minimum weight
            self.position_weights[byte_pos] = max(self.config.MIN_POSITION_WEIGHT,
                                                self.position_weights[byte_pos])

class UniversalMutationEngine:
    """Problem-agnostic mutation strategies"""
    
    def __init__(self, hex_manager: AtomicAdaptiveHexManager):
        self.hex_manager = hex_manager
        self.mutation_types = [
            ('byte_mutation', self.byte_mutation),
            ('bit_flip', self.bit_flip_mutation),
            ('arithmetic', self.arithmetic_mutation),
            ('xor_pattern', self.xor_pattern_mutation),
            ('multiplicative', self.multiplicative_mutation),
            ('gradient_walk', self.gradient_walk_mutation),
            ('harmonic', self.harmonic_mutation),
            ('galois_trace', self.galois_trace_mutation),
        ]
    
    def mutate(self, key: bytes, strength: float) -> Tuple[bytes, str]:
        """Apply random mutation and return (result, type)"""
        mutation_name, mutation_func = random.choice(self.mutation_types)
        try:
            result = mutation_func(key, strength)
            return result, mutation_name
        except:
            return key, "failed"
    
    def byte_mutation(self, key: bytes, strength: float) -> bytes:
        """Mutate individual bytes"""
        key_bytes = list(key)
        active_bytes = self.hex_manager.current_active_bytes
        
        for byte_pos in range(min(active_bytes, len(key_bytes))):
            if random.random() < strength * 0.3:
                key_bytes[byte_pos] = random.randint(0, 255)
        
        return bytes(key_bytes)
    
    def bit_flip_mutation(self, key: bytes, strength: float) -> bytes:
        """Flip random bits"""
        key_int = int.from_bytes(key, 'big')
        max_value = self.hex_manager.get_active_range()
        
        num_flips = max(1, int(strength * 5))
        for _ in range(num_flips):
            bit_pos = random.randint(0, self.hex_manager.current_active_bytes * 8 - 1)
            key_int ^= (1 << bit_pos)
        
        key_int = max(1, min(key_int, max_value))
        return key_int.to_bytes(len(key), 'big')
    
    def arithmetic_mutation(self, key: bytes, strength: float) -> bytes:
        """Add/subtract values"""
        key_int = int.from_bytes(key, 'big')
        max_value = self.hex_manager.get_active_range()
        
        delta_range = max(1000, int(max_value * strength * 0.1))
        delta = random.randint(-delta_range, delta_range)
        
        key_int = max(1, min(key_int + delta, max_value))
        return key_int.to_bytes(len(key), 'big')
    
    def xor_pattern_mutation(self, key: bytes, strength: float) -> bytes:
        """XOR with patterns"""
        patterns = [0xFF, 0x55, 0xAA, 0x33, 0xCC, 0x0F, 0xF0]
        pattern = random.choice(patterns)
        
        key_bytes = list(key)
        for i in range(min(self.hex_manager.current_active_bytes, len(key_bytes))):
            if random.random() < strength:
                key_bytes[i] ^= pattern
        
        return bytes(key_bytes)
    
    def multiplicative_mutation(self, key: bytes, strength: float) -> bytes:
        """Multiply/divide operations"""
        key_int = int.from_bytes(key, 'big')
        max_value = self.hex_manager.get_active_range()
        
        if random.random() < 0.5:
            factor = random.randint(2, 10)
            key_int = min(key_int * factor, max_value)
        else:
            divisor = random.randint(2, 10)
            key_int = max(1, key_int // divisor)
        
        return key_int.to_bytes(len(key), 'big')
    
    def gradient_walk_mutation(self, key: bytes, strength: float) -> bytes:
        """Small steps - testing for gradients"""
        key_int = int.from_bytes(key, 'big')
        max_value = self.hex_manager.get_active_range()
        
        # Small steps to detect gradients
        steps = [1, 2, 4, 8, 16, 32, 64, 128]
        step = random.choice(steps)
        if random.random() < 0.5:
            step = -step
        
        key_int = max(1, min(key_int + step, max_value))
        return key_int.to_bytes(len(key), 'big')
    
    def harmonic_mutation(self, key: bytes, strength: float) -> bytes:
        """Harmonic divisions that work in ECC"""
        key_int = int.from_bytes(key, 'big')
        if key_int < 2:
            return key
        
        divisors = [3, 5, 7, 11, 13]
        divisor = random.choice(divisors)
        
        if key_int % divisor == 0:
            key_int = key_int // divisor
            return key_int.to_bytes(len(key), 'big')
        return key
    
    def galois_trace_mutation(self, key: bytes, strength: float) -> bytes:
        """Simplified Galois trace operation"""
        key_int = int.from_bytes(key, 'big')
        max_value = self.hex_manager.get_active_range()
        
        # Simplified trace: k + k^2 + k^4 (mod max_value)
        trace = key_int
        temp = key_int
        for i in range(3):
            temp = (temp * temp) % (max_value + 1)
            trace = (trace + temp) % (max_value + 1)
        
        trace = max(1, min(trace, max_value))
        return trace.to_bytes(len(key), 'big')

class SubstrateDetectorEngine:
    """Main engine for detecting the substrate"""
    
    def __init__(self, config: AtomicGAConfig):
        self.config = config
        self.hex_manager = AtomicAdaptiveHexManager(config)
        self.mutation_engine = UniversalMutationEngine(self.hex_manager)
        
        # Population
        self.population = []
        self.scores = []
        self.elite_keys = []
        self.elite_scores = []
        
        # Substrate detection data
        self.improvement_history = []
        self.generation_stats = []
        self.gradient_measurements = []
    
    def sample_local_gradient(self, key: bytes, problem: SubstrateProblem, radius: int = 100):
        """Measure local gradient - THIS SHOULDN'T EXIST"""
        base_score = problem.evaluate(key)
        key_int = int.from_bytes(key, 'big')
        
        gradient_data = {
            'key': key_int,
            'base_score': base_score,
            'local_improvements': [],
            'gradient_exists': False
        }
        
        for delta in range(-radius, radius+1, max(1, radius//20)):
            if delta == 0:
                continue
            
            test_int = max(1, key_int + delta)
            test_key = test_int.to_bytes(len(key), 'big')
            test_score = problem.evaluate(test_key)
            
            if test_score < base_score:
                gradient_data['local_improvements'].append({
                    'delta': delta,
                    'improvement': base_score - test_score
                })
                gradient_data['gradient_exists'] = True
        
        return gradient_data
    
    def update_elite_pool(self):
        """Update elite pool"""
        scored_individuals = list(zip(self.scores, self.population))
        scored_individuals.sort(key=lambda x: x[0])
        
        self.elite_scores = []
        self.elite_keys = []
        
        used_keys = set()
        for score, key in scored_individuals[:self.config.ELITE_SIZE]:
            key_bytes = bytes(key)
            if key_bytes not in used_keys:
                self.elite_scores.append(score)
                self.elite_keys.append(key)
                used_keys.add(key_bytes)
    
    def run_substrate_detection(self, problem: SubstrateProblem, target: Any) -> dict:
        """Run GA and collect substrate evidence"""
        print(f"\n🔬 Testing: {problem.describe()}")
        print(f"🎯 Target: {target}")
        
        # Set problem target
        problem.target = target
        
        # Initialize population
        print(f"Initializing {self.config.K_POOL} solutions...")
        self.population = []
        self.scores = []
        
        for _ in range(self.config.K_POOL):
            key = self.hex_manager.generate_adaptive_key()
            score = problem.evaluate(key)
            self.population.append(key)
            self.scores.append(score)
        
        initial_best = min(self.scores)
        print(f"Initial best: {initial_best}")
        
        # Evolution loop
        for round_num in range(self.config.MAX_ROUNDS):
            round_start = time.time()
            round_start_best = min(self.scores)
            
            # Evolve population
            new_population = []
            new_scores = []
            round_improvements = 0
            
            for i, base_key in enumerate(self.population):
                best_key = base_key
                best_score = self.scores[i]
                
                # Try multiple mutations
                for _ in range(5):
                    mutated, mutation_type = self.mutation_engine.mutate(base_key, 
                                                                       self.config.MUTATION_STRENGTH)
                    score = problem.evaluate(mutated)
                    
                    if score < best_score:
                        improvement = (best_score - score) / problem.get_max_score()
                        self.hex_manager.learn_from_mutation(base_key, mutated, 
                                                           improvement, mutation_type)
                        best_key = mutated
                        best_score = score
                        round_improvements += 1
                
                new_population.append(best_key)
                new_scores.append(best_score)
            
            self.population = new_population
            self.scores = new_scores
            
            # Sample gradients periodically
            if round_num % 10 == 0:
                # Sample gradient from best solution
                best_idx = self.scores.index(min(self.scores))
                gradient_data = self.sample_local_gradient(self.population[best_idx], problem)
                self.gradient_measurements.append({
                    'round': round_num,
                    'gradient_data': gradient_data
                })
                
                if gradient_data['gradient_exists']:
                    print(f"   ⚡ GRADIENT DETECTED at round {round_num}!")
            
            # Update elite pool
            self.update_elite_pool()
            
            # Analyze population ranges
            self.hex_manager.analyze_population_ranges(self.population, self.scores)
            
            # Track progress
            round_end_best = min(self.scores)
            if round_end_best < round_start_best:
                print(f"Round {round_num}: {round_end_best} (improved by {round_start_best - round_end_best})")
            
            # Adapt hex manager
            self.hex_manager.adapt_active_range(round_num, self.elite_scores)
            self.hex_manager.apply_global_weight_decay()
            
            # Record generation stats
            self.generation_stats.append({
                'round': round_num,
                'best_score': round_end_best,
                'mean_score': statistics.mean(self.scores),
                'improvements': round_improvements,
                'active_bytes': self.hex_manager.current_active_bytes,
                'time': time.time() - round_start
            })
        
        # Calculate final improvement
        final_best = min(self.scores)
        random_baseline = problem.get_max_score() / 2  # Assume random gets ~50%
        if final_best > 0:
            improvement_bits = math.log2(random_baseline / final_best)
        else:
            improvement_bits = float('inf')  # Perfect solution
        
        # Analyze mutation effectiveness
        mutation_analysis = {}
        for mutation_type, improvements in self.hex_manager.transform_effectiveness.items():
            if improvements:
                mutation_analysis[mutation_type] = {
                    'count': len(improvements),
                    'mean_improvement': statistics.mean(improvements),
                    'max_improvement': max(improvements)
                }
        
        # Check for gradients
        gradients_found = sum(1 for g in self.gradient_measurements 
                            if g['gradient_data']['gradient_exists'])
        
        results = {
            'problem': problem.describe(),
            'initial_best': initial_best,
            'final_best': final_best,
            'improvement_bits': improvement_bits,
            'rounds': len(self.generation_stats),
            'total_mutations': len(self.hex_manager.mutation_trace),
            'gradients_found': gradients_found,
            'gradient_measurements': len(self.gradient_measurements),
            'mutation_effectiveness': mutation_analysis,
            'active_bytes_final': self.hex_manager.current_active_bytes,
            'position_weights': self.hex_manager.position_weights.tolist(),
            'generation_stats': self.generation_stats,
            'hex_manager_trace': self.hex_manager.learning_trajectory
        }
        
        return results

# Test Problems

class DiscreteLogProblem(SubstrateProblem):
    """Discrete log in multiplicative group mod p"""
    def __init__(self, p=None):
        self.p = p or self._generate_prime()
        self.g = 2  # Generator
        self.target = None
    
    def _generate_prime(self):
        # Use a known large prime
        return 2**127 - 1  # Mersenne prime
    
    def evaluate(self, solution: bytes) -> float:
        x = int.from_bytes(solution, 'big') % (self.p - 1)
        if x == 0:
            x = 1
        
        # Compute g^x mod p
        result = pow(self.g, x, self.p)
        
        # Hamming distance in binary representation
        target_bin = bin(self.target)[2:].zfill(127)
        result_bin = bin(result)[2:].zfill(127)
        
        distance = sum(a != b for a, b in zip(target_bin, result_bin))
        return float(distance)
    
    def get_random_target(self):
        # Random exponent
        secret = random.randint(1, self.p - 2)
        return pow(self.g, secret, self.p)
    
    def get_max_score(self) -> float:
        return 127.0  # Max Hamming distance
    
    def describe(self) -> str:
        return f"Discrete Log mod {self.p}"

class FactorizationProblem(SubstrateProblem):
    """Integer factorization"""
    def __init__(self, bits=100):
        self.bits = bits
        self.target = None
    
    def evaluate(self, solution: bytes) -> float:
        candidate = int.from_bytes(solution, 'big')
        if candidate < 2:
            return float(self.bits)
        
        # Check if divides target
        if self.target % candidate == 0:
            other_factor = self.target // candidate
            if other_factor > 1 and other_factor != self.target:
                return 0.0  # Found a factor!
        
        # Otherwise, distance based on GCD
        g = math.gcd(candidate, self.target)
        if g > 1:
            # Partial credit for sharing factors
            return float(self.bits) * (1 - math.log(g) / math.log(self.target))
        
        # No common factors - use modular distance
        mod_dist = self.target % candidate
        return float(min(mod_dist, candidate - mod_dist)) / max(1, candidate) * self.bits
    
    def get_random_target(self):
        # Generate semiprime
        p = self._random_prime(self.bits // 2)
        q = self._random_prime(self.bits // 2)
        return p * q
    
    def _random_prime(self, bits):
        while True:
            n = random.getrandbits(bits) | 1  # Ensure odd
            if self._is_probable_prime(n):
                return n
    
    def _is_probable_prime(self, n, k=5):
        # Miller-Rabin primality test
        if n < 2:
            return False
        if n == 2 or n == 3:
            return True
        if n % 2 == 0:
            return False
        
        # Write n-1 as 2^r * d
        r, d = 0, n - 1
        while d % 2 == 0:
            r += 1
            d //= 2
        
        # Witness loop
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
    
    def get_max_score(self) -> float:
        return float(self.bits)
    
    def describe(self) -> str:
        return f"Integer Factorization ({self.bits} bits)"

class SATClauseProblem(SubstrateProblem):
    """3-SAT problem"""
    def __init__(self, num_vars=100, num_clauses=430):
        self.num_vars = num_vars
        self.num_clauses = num_clauses
        self.clauses = []
        self.target = None
    
    def evaluate(self, solution: bytes) -> float:
        # Convert bytes to variable assignments
        assignments = []
        for i in range(self.num_vars):
            byte_idx = i // 8
            bit_idx = i % 8
            if byte_idx < len(solution):
                bit = (solution[byte_idx] >> bit_idx) & 1
                assignments.append(bool(bit))
            else:
                assignments.append(False)
        
        # Count unsatisfied clauses
        unsatisfied = 0
        for clause in self.clauses:
            satisfied = False
            for var, negated in clause:
                value = assignments[var] if var < len(assignments) else False
                if negated:
                    value = not value
                if value:
                    satisfied = True
                    break
            if not satisfied:
                unsatisfied += 1
        
        return float(unsatisfied)
    
    def get_random_target(self):
        # Generate random 3-SAT instance
        self.clauses = []
        for _ in range(self.num_clauses):
            clause = []
            vars_in_clause = set()
            for _ in range(3):
                var = random.randint(0, self.num_vars - 1)
                while var in vars_in_clause:
                    var = random.randint(0, self.num_vars - 1)
                vars_in_clause.add(var)
                negated = random.choice([True, False])
                clause.append((var, negated))
            self.clauses.append(clause)
        return self.clauses
    
    def get_max_score(self) -> float:
        return float(self.num_clauses)
    
    def describe(self) -> str:
        return f"3-SAT ({self.num_vars} vars, {self.num_clauses} clauses)"

class HashInversionProblem(SubstrateProblem):
    """Try to invert a hash function"""
    def __init__(self, hash_func='sha256'):
        self.hash_func = hash_func
        self.target = None
    
    def evaluate(self, solution: bytes) -> float:
        if self.hash_func == 'sha256':
            hash_result = hashlib.sha256(solution).digest()
        elif self.hash_func == 'sha1':
            hash_result = hashlib.sha1(solution).digest()
        else:
            hash_result = hashlib.md5(solution).digest()
        
        # Hamming distance
        distance = 0
        for a, b in zip(hash_result, self.target):
            distance += bin(a ^ b).count('1')
        
        return float(distance)
    
    def get_random_target(self):
        random_input = random.randbytes(32)
        if self.hash_func == 'sha256':
            return hashlib.sha256(random_input).digest()
        elif self.hash_func == 'sha1':
            return hashlib.sha1(random_input).digest()
        else:
            return hashlib.md5(random_input).digest()
    
    def get_max_score(self) -> float:
        if self.hash_func == 'sha256':
            return 256.0
        elif self.hash_func == 'sha1':
            return 160.0
        else:
            return 128.0
    
    def describe(self) -> str:
        return f"Hash Inversion ({self.hash_func})"

class RiemannZetaProblem(SubstrateProblem):
    """Find zeros of Riemann zeta function"""
    def __init__(self):
        self.target = None
        self.known_zeros = [14.134725, 21.022040, 25.010858, 30.424876, 32.935062]
    
    def evaluate(self, solution: bytes) -> float:
        # Interpret solution as imaginary part
        t = int.from_bytes(solution, 'big') / 1000000.0  # Scale down
        t = t % 100  # Keep in reasonable range
        
        # Distance to nearest known zero
        min_distance = min(abs(t - zero) for zero in self.known_zeros)
        
        # Approximate zeta function behavior (simplified)
        # Real zeros have Re(zeta(0.5 + it)) = 0
        # We'll use a simplified oscillating function
        approx_real = math.sin(t * math.log(t + 1))
        approx_imag = math.cos(t * math.log(t + 1))
        magnitude = math.sqrt(approx_real**2 + approx_imag**2)
        
        return min_distance + magnitude * 10
    
    def get_random_target(self):
        return random.choice(self.known_zeros)
    
    def get_max_score(self) -> float:
        return 100.0
    
    def describe(self) -> str:
        return "Riemann Zeta Zeros"

def run_universal_substrate_test():
    """Test the GA on multiple problem types"""
    print("="*70)
    print("🌌 UNIVERSAL SUBSTRATE DETECTOR")
    print("Testing if the ~27-bit phenomenon is universal")
    print("="*70)
    
    config = AtomicGAConfig()
    problems = [
        DiscreteLogProblem(),
        FactorizationProblem(bits=100),
        SATClauseProblem(num_vars=50, num_clauses=200),
        HashInversionProblem('sha256'),
        HashInversionProblem('sha1'),
        RiemannZetaProblem(),
    ]
    
    all_results = []
    
    for problem in problems:
        engine = SubstrateDetectorEngine(config)
        target = problem.get_random_target()
        results = engine.run_substrate_detection(problem, target)
        all_results.append(results)
        
        print(f"\n📊 RESULTS for {problem.describe()}:")
        print(f"   Initial: {results['initial_best']:.2f}")
        print(f"   Final: {results['final_best']:.2f}")
        print(f"   Improvement: {results['improvement_bits']:.1f} bits")
        print(f"   Gradients found: {results['gradients_found']}/{results['gradient_measurements']}")
        
        if results['mutation_effectiveness']:
            print(f"   Most effective mutations:")
            sorted_mutations = sorted(results['mutation_effectiveness'].items(), 
                                    key=lambda x: x[1]['mean_improvement'], 
                                    reverse=True)
            for mutation, stats in sorted_mutations[:3]:
                print(f"      {mutation}: {stats['mean_improvement']:.3f} avg improvement")
    
    # Analyze commonalities
    print("\n" + "="*70)
    print("🔬 CROSS-PROBLEM ANALYSIS")
    print("="*70)
    
    improvements = [r['improvement_bits'] for r in all_results if r['improvement_bits'] != float('inf')]
    gradients = [r['gradients_found'] for r in all_results]
    
    print(f"Improvement bits across problems:")
    for i, r in enumerate(all_results):
        print(f"   {r['problem']}: {r['improvement_bits']:.1f} bits")
    
    if improvements:
        print(f"\nStatistics:")
        print(f"   Mean improvement: {statistics.mean(improvements):.1f} bits")
        if len(improvements) > 1:
            print(f"   StdDev: {statistics.stdev(improvements):.1f} bits")
        print(f"   Range: {min(improvements):.1f} - {max(improvements):.1f} bits")
    
    print(f"\nGradient detection:")
    print(f"   Problems with gradients: {sum(1 for g in gradients if g > 0)}/{len(gradients)}")
    print(f"   Total gradients found: {sum(gradients)}")
    
    # Check for the magic ~27-bit constant
    close_to_27 = sum(1 for imp in improvements if 20 <= imp <= 35)
    if close_to_27 >= len(improvements) // 2:
        print(f"\n🚨 SUBSTRATE DETECTED: {close_to_27}/{len(improvements)} problems show ~27-bit improvement!")
    
    # Save detailed results
    with open('substrate_detection_results.json', 'w') as f:
        json.dump({
            'config': config.__dict__,
            'results': all_results,
            'analysis': {
                'mean_improvement_bits': statistics.mean(improvements) if improvements else 0,
                'stdev_improvement_bits': statistics.stdev(improvements) if len(improvements) > 1 else 0,
                'problems_with_gradients': sum(1 for g in gradients if g > 0),
                'close_to_27_bits': close_to_27
            }
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to substrate_detection_results.json")
    
    return all_results

if __name__ == "__main__":
    results = run_universal_substrate_test()