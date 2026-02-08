# Information Network Theory

Physics validation suite testing INT parameters against real-world data (SDSS, WMAP, LIGO, Bell test, QRNG).

## Structure

- **int_physics_validation_suite.py** - Full INT physics validation against empirical datasets
- **universal_substrate_detector.py** - Universal substrate detection via information geometry
- **gf27_galois_field.py** - GF(27) Galois field implementation
- **gf27_theory_test.py** - GF(27) theory validation tests
- **data/** - Input datasets (SDSS, WMAP, LIGO, Bell, QRNG)
- **results/** - Output plots: degree histograms, persistent homology, phase locking, GW classicality, Bell residuals, decay memory, RNG bias

## Results

Validation produces 7 diagnostic plots:
1. Degree distribution histogram
2. Persistent homology analysis
3. Phase locking patterns
4. Gravitational wave classicality
5. Bell test residuals
6. Decay memory analysis
7. RNG bias detection

## Requirements

- Python 3.10+
- NumPy, SciPy, matplotlib
- astropy (for SDSS/WMAP data)

## License

MIT
