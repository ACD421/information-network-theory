<div align="center">

# Information Network Theory

### Physics Validation Suite

**SDSS | WMAP | LIGO | Bell test | QRNG | Willow quantum processor**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)

</div>

## Overview

Validation suite testing Information Network Theory parameters against real-world physics data. INT proposes a GF(27) Galois field substrate underlying physical interactions. This repo tests that hypothesis against measured datasets from major experiments.

## Validation Targets

| Dataset | Source | What It Tests |
|---------|--------|---------------|
| SDSS | Sloan Digital Sky Survey | Large-scale structure, galaxy distribution |
| WMAP | Wilkinson Microwave Anisotropy Probe | CMB power spectrum, cosmological parameters |
| LIGO | Laser Interferometer Gravitational-Wave Observatory | Gravitational wave signatures |
| Bell test | Loophole-free Bell inequality experiments | Quantum nonlocality bounds |
| QRNG | Quantum random number generators | Randomness structure, bias detection |
| Willow | Google Quantum AI processor | Quantum error correction, syndrome analysis |

## Structure

```
int_physics_validation_suite.py  # Primary 7-test validation suite
gf27_galois_field.py             # GF(27) substrate implementation
gf27_theory_test.py              # Galois field discrimination tests
universal_substrate_detector.py  # Cross-domain substrate detection

cosmos/                          # Cosmological derivations and validation
|-- planck_validation.py         # Planck satellite data comparison
|-- bbn_bao_lss_validation.py   # Big Bang nucleosynthesis + BAO + LSS
|-- h0_scan.py                   # Hubble constant tension analysis
|-- full_validation.py           # Combined cosmological validation
|-- derive_matter.py             # Matter density derivation
|-- derive_universe.py           # Universe-scale parameter derivation
|-- derive_frontier.py           # Frontier physics derivations
|-- derive_abyss.py              # Deep parameter space exploration
+-- (10 more derivation scripts)

quantum/                         # Google Willow quantum processor analysis
|-- willow_syndrome_analysis.py  # Error syndrome pattern analysis
|-- willow_anomaly_hunt.py       # Statistical anomaly detection
|-- willow_candidate_tests.py    # Candidate signature validation
|-- willow_noise_model_test.py   # Noise model discrimination
|-- willow_projection_v2.py      # Projection analysis
|-- willow_rate_matched.py       # Rate-matched comparison
+-- willow_check_matrix_projection.py

results/                         # Visualization outputs from validation suite
```

## Quick Start

```bash
# Run the primary 7-test validation suite
python int_physics_validation_suite.py

# Test GF(27) substrate detection
python gf27_theory_test.py

# Run cosmological validation
python cosmos/full_validation.py

# Analyze Willow quantum data
python quantum/willow_syndrome_analysis.py
```

## Related

- [SGM-Substrate](https://github.com/ACD421/sgm-substrate) -- Same geometric framework applied to AI

## Author

**Andrew C. Dorman** -- [Hollow Point Labs](https://github.com/ACD421)

## License

MIT