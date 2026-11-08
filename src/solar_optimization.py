"""Experiment 3: test single-site solar placement and output on the IEEE 33-bus feeder.

This is a grid search of steady-state load-flow cases, NOT a global optimizer.
The built-in feeder may not contain trustworthy line thermal ratings; if so,
line-loading constraints are explicitly marked as unverified.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"
V_MIN, V_MAX = 0.95, 1.05  # illustrative study limits, not a utility requirement


def line_ratings_usable(net):
    """Only evaluate a 100% line-loading limit if all active lines have valid ratings."""
    active = net.line.loc[net.line.in_service.astype(bool)]
    required = ("max_i_ka", "df", "parallel")
    if any(col not in active.columns for col in required):
        return False
    for col in required:
        values = pd.to_numeric(active[col], errors="coerce")
        if not (np.isfinite(values).all() and (values > 0).all()):
            return False
    return True


def summarize_case(net, bus, solar_mw, has_ratings):
    voltages = net.res_bus.vm_pu
    under = int((voltages < V_MIN).sum())
    over = int((voltages > V_MAX).sum())
    violation_size = float(np.maximum(V_MIN - voltages.to_numpy(), 0).sum()
                           + np.maximum(voltages.to_numpy() - V_MAX, 0).sum())
    voltage_ok = under == 0 and over == 0

    max_loading = float("nan")
    thermal_ok = False
    if has_ratings:
        active_idx = net.line.index[net.line.in_service.astype(bool)]
        loading = net.res_line.loc[active_idx, "loading_percent"].to_numpy(dtype=float)
        if np.isfinite(loading).all():
            max_loading = float(np.max(loading))
            thermal_ok = max_loading <= 100.0

    return {
        "bus_number": int(bus) + 1,  # case33bw uses 0-based indexing
        "solar_mw": float(solar_mw),
        "line_losses_kw": float(net.res_line.pl_mw.sum() * 1000),
        "min_voltage_pu": float(voltages.min()),
        "max_voltage_pu": float(voltages.max()),
        "weakest_bus_number": int(voltages.idxmin()) + 1,
        "buses_below_095": under,
        "buses_above_105": over,
        "voltage_violation_sum_pu": violation_size,
        "violating_buses": under + over,
        "voltage_ok": voltage_ok,
        "max_line_loading_percent": max_loading,
        "thermal_ratings_verified": has_ratings,
        "thermal_ok": bool(thermal_ok) if has_ratings else None,
        "all_constraints_ok": bool(voltage_ok and thermal_ok) if has_ratings else False,
        "slack_import_mw": float(net.res_ext_grid.p_mw.sum()),
    }


def display_case(label, row, baseline_kw):
    if row is None:
        print(f"{label}: NONE in tested cases")
        return
    reduction = 100 * (baseline_kw - row['line_losses_kw']) / baseline_kw
    print(f"{label}: bus {int(row['bus_number'])}, {row['solar_mw']:.2f} MW | "
          f"losses {row['line_losses_kw']:.2f} kW ({reduction:+.1f}% lower than base) | "
          f"Vmin {row['min_voltage_pu']:.4f} p.u. | "
          f"out-of-band buses {int(row['buses_below_095'] + row['buses_above_105'])}")


def make_plots(df, best, show=False):
    # Heatmap: all tested buses and solar outputs, including infeasible cases.
    grid = df.pivot(index="bus_number", columns="solar_mw", values="line_losses_kw")
    fig, ax = plt.subplots(figsize=(11, 7))
    image = ax.imshow(grid.to_numpy(), origin="lower", aspect="auto", cmap="viridis")
    ax.set_xticks(np.arange(0, len(grid.columns), max(1, len(grid.columns)//8)))
    ax.set_xticklabels([f"{grid.columns[i]:g}" for i in ax.get_xticks().astype(int)])
    ax.set_yticks(np.arange(0, len(grid.index), 3))
    ax.set_yticklabels(grid.index[::3])
    ax.set(xlabel="Solar generation (MW)", ylabel="Bus number",
           title="IEEE 33-bus: line losses by solar location and size")
    fig.colorbar(image, ax=ax, label="Total active line losses (kW)")
    fig.text(.5, .01, "Includes cases that may violate voltage or thermal constraints",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .03, 1, 1))
    fig.savefig(FIGURES / "solar_optimization_loss_heatmap.png", dpi=200)

    # Best loss for each bus, selecting the lowest of the TESTED output values.
    per_bus = df.loc[df.groupby("bus_number")["line_losses_kw"].idxmin()].sort_values("bus_number")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(per_bus["bus_number"], per_bus["line_losses_kw"], marker="o", ms=4)
    ax.scatter([best["bus_number"]], [best["line_losses_kw"]],
               marker="*", s=160, color="red", label="Lowest loss among tested cases", zorder=3)
    ax.set(xlabel="Solar installation bus", ylabel="Minimum line loss found (kW)",
           title="Best tested solar size at each bus (ignoring constraints)")
    ax.grid(alpha=.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "solar_optimization_best_by_bus.png", dpi=200)

    # Compare the previous Bus 18 scenario with the bus selected in this study.
    fig, ax = plt.subplots(figsize=(9, 5))
    selected = {18, int(best["bus_number"])}
    for bus in sorted(selected):
        data = df.loc[df.bus_number == bus].sort_values("solar_mw")
        ax.plot(data.solar_mw, data.line_losses_kw, marker=".", label=f"Bus {bus}")
    ax.set(xlabel="Solar generation (MW)", ylabel="Line losses (kW)",
           title="Previous Bus 18 vs lowest-loss bus")
    ax.grid(alpha=.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "solar_optimization_bus_comparison.png", dpi=200)
    if show:
        plt.show()
    else:
        plt.close("all")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", type=float, default=0.05,
                        help="Solar power increment in MW (default: 0.05)")
    parser.add_argument("--max-mw", type=float, default=1.5,
                        help="Maximum solar injection in MW (default: 1.5)")
    parser.add_argument("--show", action="store_true", help="Open plot windows after saving")
    args = parser.parse_args()
    if args.step <= 0 or args.max_mw <= 0:
        parser.error("--step and --max-mw must be positive")
    capacities = np.round(np.arange(args.step, args.max_mw + 1e-9, args.step), 5)
    if len(capacities) == 0:
        parser.error("--max-mw must be at least --step")

    FIGURES.mkdir(parents=True, exist_ok=True)
    net = pn.case33bw()
    has_ratings = line_ratings_usable(net)
    pp.runpp(net, numba=False, init="flat")
    base_kw = float(net.res_line.pl_mw.sum() * 1000)
    base_min_v = float(net.res_bus.vm_pu.min())
    print(f"Base case: {base_kw:.2f} kW line losses, Vmin {base_min_v:.4f} p.u.")
    if not has_ratings:
        print("WARNING: At least one active line has no valid thermal rating. "
              "Do not claim full voltage+thermal feasibility from this feeder data.")

    slack_buses = set(map(int, net.ext_grid.bus))
    buses = [int(b) for b in net.bus.index if int(b) not in slack_buses
             and bool(net.bus.at[b, "in_service"])]
    solar_idx = pp.create_sgen(net, bus=buses[0], p_mw=0, q_mvar=0,
                               name="Trial unity-power-factor solar generator")
    rows = []
    failed = []
    for bus in buses:
        net.sgen.at[solar_idx, "bus"] = bus
        for p_mw in capacities:
            net.sgen.at[solar_idx, "p_mw"] = float(p_mw)
            try:
                pp.runpp(net, numba=False, init="flat", max_iteration=50)
            except pp.LoadflowNotConverged:
                failed.append((bus + 1, float(p_mw)))
                continue
            rows.append(summarize_case(net, bus, p_mw, has_ratings))
        print(f"Finished Bus {bus + 1:2d}/{max(buses)+1}")

    if not rows:
        raise RuntimeError("No converged power-flow cases. Check network and inputs.")
    df = pd.DataFrame(rows)
    df["loss_reduction_percent"] = (base_kw - df.line_losses_kw) / base_kw * 100
    df.to_csv(RESULTS / "solar_optimization_all_cases.csv", index=False)

    best = df.loc[df.line_losses_kw.idxmin()]
    voltage_cases = df.loc[df.voltage_ok]
    best_voltage = (voltage_cases.loc[voltage_cases.line_losses_kw.idxmin()]
                    if len(voltage_cases) else None)
    full_cases = df.loc[df.all_constraints_ok]
    best_full = (full_cases.loc[full_cases.line_losses_kw.idxmin()]
                 if len(full_cases) else None)
    best_quality = df.sort_values(
        ["violating_buses", "voltage_violation_sum_pu", "line_losses_kw"]
    ).iloc[0]
    previous = df.loc[(df.bus_number == 18) & np.isclose(df.solar_mw, 1.0)]

    print(f"\nEvaluated {len(df)} converged cases, {len(failed)} non-converged cases.")
    display_case("Unconstrained lowest-loss case", best, base_kw)
    display_case("Lowest-loss voltage-compliant case", best_voltage, base_kw)
    display_case("Lowest-loss case passing voltage AND line ratings", best_full, base_kw)
    display_case("Fewest under/overvoltage buses (then lowest violation)", best_quality, base_kw)
    display_case("Previous experiment: Bus 18 at 1 MW", previous.iloc[0] if len(previous) else None, base_kw)
    if not has_ratings:
        print("No fully verified optimum is reported: line thermal ratings are incomplete.")
    if best_voltage is None:
        print("No tested combination satisfies the full 0.95–1.05 p.u. voltage band.")

    lines = [f"Base-case losses: {base_kw:.3f} kW", f"Base-case minimum voltage: {base_min_v:.5f} p.u.",
             f"Converged cases: {len(df)}; failed: {len(failed)}", "",
             "Line thermal ratings usable: " + str(has_ratings),
             "Unconstrained best (NOT necessarily feasible):",
             best.to_string(), "", "Voltage-compliant best:",
             best_voltage.to_string() if best_voltage is not None else "None found", "",
             "Fully verified best:",
             best_full.to_string() if best_full is not None else "None found or ratings unavailable", ""]
    (RESULTS / "solar_optimization_summary.txt").write_text("\n".join(lines), encoding="utf-8")
    if failed:
        pd.DataFrame(failed, columns=["bus_number", "solar_mw"]).to_csv(
            RESULTS / "solar_optimization_nonconverged.csv", index=False)

    make_plots(df, best, show=args.show)
    print("\nSaved CSV, summary and three figures in results/.")


if __name__ == "__main__":
    main()
