<div align="center">

# Information Network Theory

### Physics Validation Suite

**Testing INT parameters against SDSS, WMAP, LIGO, Bell test, and QRNG real-world datasets**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)

</div>

## Overview

This repository contains a comprehensive physics validation suite testing Information Network Theory (INT) parameters against real-world observational data from major physics experiments and surveys.

The core hypothesis: information propagation through discrete network substrates produces emergent physical phenomena that match observed data when the network parameters are correctly tuned.

## Validation Datasets

| Dataset | Source | What It Tests |
|---------|--------|---------------|
| **SDSS** | Sloan Digital Sky Survey | Large-scale structure, galaxy clustering |
| **WMAP** | Wilkinson Microwave Anisotropy Probe | CMB power spectrum, cosmological parameters |
| **LIGO** | Laser Interferometer Gravitational-Wave Observatory | Gravitational wave classicality |
| **Bell test** | Experimental quantum mechanics | Non-locality, Bell inequality residuals |
| **QRNG** | Quantum Random Number Generator | True randomness, bias detection |

## Diagnostic Outputs

The validation suite produces 7 diagnostic analyses:

1. **Degree Histogram** -- Network connectivity distribution vs observed structure
2. **Persistent Homology** -- Topological features of the information network
3. **Phase Locking** -- Synchronization behavior across network nodes
4. **Gravitational Wave Classicality** -- LIGO data consistency with INT predictions
5. **Bell Residuals** -- Deviation from quantum mechanical predictions
6. **Decay Memory** -- Information persistence across network propagation
7. **RNG Bias Detection** -- Statistical analysis of quantum randomness

## Components

| File | Description |
|------|-------------|
| `int_physics_validation_suite.py` | Main validation runner -- all 7 diagnostics |
| `gf27_galois_field.py` | GF(27) Galois field implementation for substrate detection |
| `gf27_theory_test.py` | Theoretical validation of GF(27) properties |
| `universal_substrate_detector.py` | Substrate detection across experimental data |
| `results/` | Output plots and analysis results |

## GF(27) Galois Field

A key mathematical tool in this analysis: the Galois field GF(27) = GF(3^3) provides the algebraic substrate for information network nodes. The choice of GF(27) is motivated by:

- **Base 3**: Ternary information (vs binary) captures richer state spaces
- **Dimension 3**: Matches spatial dimensionality
- **Order 27**: Sufficient resolution for physical parameter mapping

## Quick Start

```bash
# Run full validation suite
python int_physics_validation_suite.py

# Test GF(27) properties
python gf27_theory_test.py

# Run substrate detection
python universal_substrate_detector.py
```

## Related

- [SGM-Substrate](https://github.com/ACD421/sgm-substrate) -- Information-geometric principles applied to AI
- [secp256k1-geometric-analysis](https://github.com/ACD421/secp256k1-geometric-analysis) -- Geometric analysis in cryptographic curves

## Author

**Andrew C. Dorman** -- [Hollow Point Labs](https://github.com/ACD421)

## License

MIT
