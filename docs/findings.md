# Findings, assumptions, and limitations

## 1. Load growth

The baseline IEEE 33-bus network already has buses under the illustrative 0.95 p.u. lower voltage reference. Scaling both active and reactive demand to 125%, 150%, and 175% reduces the minimum voltage and increases active line losses. A nearly unchanged number of undervoltage buses does not mean the violations have stopped getting worse.

## 2. Fixed solar generation at conventional Bus 18

With a fixed active-power injection at pandapower index 17 (conventional Bus 18), the original plotted results indicate total line losses of roughly 0.203, 0.172, 0.153, 0.146, and 0.172 MW for 0, 0.25, 0.5, 1.0, and 1.5 MW generation. At 1 MW the approximate reduction from baseline is 28%; these are **rounded chart readings** and should be checked with regenerated full-precision output.

Among **these five tested sizes**, the loss minimum occurred at 1 MW. The network still had voltage below 0.95 p.u. in another feeder branch. Larger injection may increase current on some sections even if it reduces upstream import. Reverse power flow in individual lines is different from net export to the grid.

## 3. Boundaries of interpretation

- Balanced steady-state AC power-flow model from `pandapower.networks.case33bw()`.
- Solar is a fixed active-power injection with `q_mvar=0`, not a time-resolved solar PV module or controlled inverter.
- The 0.95–1.05 p.u. band is an illustrative project criterion, not a verified utility grid code.
- The work does **not** claim globally optimal PV placement/capacity, voltage stability analysis, complete line rating validation, or actual grid deployment.
- Original chart values are rounded; reproduce numerical values locally with the scripts before using exact numbers in a CV or report.

## 4. Next development

Test alternative buses and a finer capacity sweep. Define an objective (e.g., lowest line losses) with voltage and loading constraints. If the single-generator feasible set is empty, report that and investigate reactive support or multi-site generation rather than ignoring constraints.
