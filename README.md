# IEEE 33-Bus Distribution Network Study

I used Python and [pandapower](https://www.pandapower.org/) to study how changes in electricity demand and local solar generation affect a distribution feeder.

The model is the IEEE 33-bus test system available through `pandapower.networks.case33bw()`.

## What I did

- Ran the base-case power flow and plotted the voltage at each bus.
- Increased the loads to 125%, 150% and 175% of their original values to see how voltages and line losses changed.
- Added a solar generator at Bus 18 and tested outputs of 0.25, 0.5, 1 and 1.5 MW.

For each case, I looked at bus voltages, the lowest-voltage bus and total line losses.

## Results

As demand increased, the minimum bus voltage dropped and line losses increased.

Adding solar at Bus 18 initially reduced line losses. Of the five outputs I tested, **1 MW gave the lowest losses**, from about **203 kW without solar to 146 kW** (roughly 28% lower). At 1.5 MW the losses increased again.

The solar generator improved voltages near Bus 18, but some buses were still below the 0.95 p.u. reference. So reducing losses and fixing low voltage are not necessarily the same problem.

![Line losses at different solar outputs](results/figures/solar_line_losses.svg)

![Minimum and maximum voltages](results/figures/solar_voltage_limits.svg)

*The two charts above use rounded values from my initial simulation plots. The scripts generate plots and full-precision CSV results when run locally.*

## Running the code

Install the packages:

```bash
python -m pip install -r requirements.txt
```

Run the scripts from the main project folder:

```bash
python src/baseline.py
python src/load_growth_analysis.py
python src/solar_integration.py
```

They print the results and save plots and CSV files in `results/`.

## Notes

Solar is represented as a fixed power injection at unity power factor, not as a detailed PV panel and inverter model. I used 0.95–1.05 p.u. as a voltage reference for the comparisons.

Next, I want to compare different buses and solar sizes to see whether another location gives lower losses and a better voltage profile.

More details are in [docs/findings.md](docs/findings.md).
