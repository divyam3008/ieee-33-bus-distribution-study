# Results

The scripts create CSV tables and publication-resolution PNG charts in this directory when run locally. The two SVG figures committed here are **approximate visual summaries digitized from the user's original charts**, not independently validated simulation results.

To regenerate figures and full-precision CSV data, run:

```bash
python src/baseline.py
python src/load_growth_analysis.py
python src/solar_integration.py
```

Run from the repository root. Check results with your installed pandapower version before reporting numerical values externally.
