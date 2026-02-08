#!/usr/bin/env python3
"""
GF(27) = GF(3^3) Implementation for Galois Field Theory Testing
"""

import random
import os
from typing import List, Tuple

def randbytes(n: int) -> bytes:
    """Generate n random bytes"""
    return os.urandom(n)

class GF27:
    """Galois Field GF(3^3) = GF(27) implementation"""
    
    def __init__(self):
        # GF(27) = GF(3)[x]/(x^3 + 2x + 1)
        # Using irreducible polynomial x^3 + 2x + 1 over GF(3)
        self.order = 27
        self.characteristic = 3
        self.degree = 3
        
        # Represent elements as integers 0-26
        # where element a2*x^2 + a1*x + a0 is stored as 9*a2 + 3*a1 + a0
        
        # Precompute multiplication table
        self._init_multiplication_table()
        
        # Precompute powers of primitive element
        self._init_primitive_element()
        
    def _init_multiplication_table(self):
        """Initialize multiplication table for GF(27)"""
        self.mult_table = {}
        
        # For each pair of elements
        for a in range(27):
            for b in range(27):
                # Convert to polynomial representation
                a_poly = self._int_to_poly(a)
                b_poly = self._int_to_poly(b)
                
                # Multiply polynomials
                prod = self._poly_mult(a_poly, b_poly)
                
                # Reduce modulo irreducible polynomial
                result = self._poly_mod(prod)
                
                # Convert back to integer
                self.mult_table[(a, b)] = self._poly_to_int(result)
    
    def _init_primitive_element(self):
        """Find primitive element and compute its powers"""
        # Try each element until we find one of order 26
        for g in range(1, 27):
            powers = set()
            power = 1
            for i in range(26):
                power = self.mult_table[(power, g)]
                powers.add(power)
            
            if len(powers) == 26:  # Found primitive element
                self.primitive = g
                
                # Store powers
                self.powers = [1]
                for i in range(1, 26):
                    self.powers.append(self.mult_table[(self.powers[-1], g)])
                break
    
    def _int_to_poly(self, n: int) -> List[int]:
        """Convert integer 0-26 to polynomial coefficients"""
        return [n % 3, (n // 3) % 3, (n // 9) % 3]
    
    def _poly_to_int(self, poly: List[int]) -> int:
        """Convert polynomial coefficients to integer 0-26"""
        while len(poly) < 3:
            poly.append(0)
        return poly[0] + 3 * poly[1] + 9 * poly[2]
    
    def _poly_mult(self, a: List[int], b: List[int]) -> List[int]:
        """Multiply two polynomials over GF(3)"""
        result = [0] * (len(a) + len(b) - 1)
        
        for i in range(len(a)):
            for j in range(len(b)):
                result[i + j] = (result[i + j] + a[i] * b[j]) % 3
        
        return result
    
    def _poly_mod(self, poly: List[int]) -> List[int]:
        """Reduce polynomial modulo x^3 + 2x + 1"""
        # x^3 + 2x + 1 = 0  =>  x^3 = -2x - 1 = x + 2 (in GF(3))
        
        while len(poly) > 3:
            if poly[-1] != 0:
                # Reduce highest degree term
                coeff = poly[-1]
                poly[-1] = 0
                poly[-3] = (poly[-3] + coeff) % 3  # x^3 -> x
                poly[-4] = (poly[-4] + 2 * coeff) % 3  # x^3 -> 2
            else:
                poly.pop()
        
        # Ensure we have exactly 3 coefficients
        while len(poly) < 3:
            poly.append(0)
        while len(poly) > 3:
            poly.pop()
            
        return poly[:3]
    
    def multiply(self, a: int, b: int) -> int:
        """Multiply two elements in GF(27)"""
        return self.mult_table[(a, b)]
    
    def add(self, a: int, b: int) -> int:
        """Add two elements in GF(27)"""
        a_poly = self._int_to_poly(a)
        b_poly = self._int_to_poly(b)
        
        result = [(a_poly[i] + b_poly[i]) % 3 for i in range(3)]
        return self._poly_to_int(result)
    
    def trace(self, a: int) -> int:
        """Compute trace of element: Tr(a) = a + a^3 + a^9"""
        a3 = self.multiply(self.multiply(a, a), a)
        a9 = self.multiply(self.multiply(a3, a3), a3)
        
        result = self.add(self.add(a, a3), a9)
        
        # Trace maps to GF(3), so result should be 0, 1, or 2
        return result % 3
    
    def embed_bytes(self, data: bytes) -> List[int]:
        """Embed byte string into GF(27) elements"""
        elements = []
        
        # Process 3 bytes at a time (since 256^3 ~ 27^5)
        for i in range(0, len(data), 3):
            chunk = data[i:i+3]
            
            # Convert 3 bytes to integer
            value = 0
            for j, byte in enumerate(chunk):
                value += byte * (256 ** j)
            
            # Convert to base 27 and take 5 elements
            for _ in range(5):
                elements.append(value % 27)
                value //= 27
                
                if value == 0 and len(elements) % 5 == 0:
                    break
        
        return elements
    
    def extract_bytes(self, elements: List[int], length: int) -> bytes:
        """Extract bytes from GF(27) elements"""
        result = bytearray()
        
        # Process 5 elements at a time
        for i in range(0, len(elements), 5):
            chunk_elems = elements[i:i+5]
            
            # Convert from base 27 to integer
            value = 0
            for j, elem in enumerate(chunk_elems):
                value += elem * (27 ** j)
            
            # Convert to 3 bytes
            for _ in range(3):
                if len(result) < length:
                    result.append(value % 256)
                value //= 256
        
        return bytes(result[:length])
    
    def dimension_reduction_factor(self) -> float:
        """Calculate dimension reduction factor of trace map"""
        # Trace maps 27 elements to 3 values
        return 27 / 3

# Test functions
def test_gf27_basic():
    """Test basic GF(27) operations"""
    gf = GF27()
    
    print("Testing GF(27) implementation...")
    
    # Test that multiplication table is correct
    # Check that every non-zero element has an inverse
    inverses_found = 0
    for a in range(1, 27):
        for b in range(1, 27):
            if gf.multiply(a, b) == 1:
                inverses_found += 1
                break
    
    print(f"Found {inverses_found} inverses (should be 26)")
    
    # Test trace function
    trace_counts = [0, 0, 0]
    for a in range(27):
        tr = gf.trace(a)
        trace_counts[tr] += 1
    
    print(f"Trace distribution: Tr=0: {trace_counts[0]}, Tr=1: {trace_counts[1]}, Tr=2: {trace_counts[2]}")
    
    # Test embedding/extraction
    test_data = b"Hello, GF(27)!"
    embedded = gf.embed_bytes(test_data)
    extracted = gf.extract_bytes(embedded, len(test_data))
    
    print(f"Embedding test: {'PASS' if extracted == test_data else 'FAIL'}")
    
    return gf

if __name__ == "__main__":
    test_gf27_basic()