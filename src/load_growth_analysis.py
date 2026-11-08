"""Compare 100%, 125%, 150%, and 175% demand with fixed network parameters."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pandapower as pp
import pandapower.networks as pn

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"
FACTORS = [1.0, 1.25, 1.5, 1.75]


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    records = []
    profiles = {}
    for factor in FACTORS:
        net = pn.case33bw()
        net.load["p_mw"] *= factor
        net.load["q_mvar"] *= factor  # preserves load power factor
        pp.runpp(net, numba=False)
        v = net.res_bus.vm_pu
        demand = int(round(factor * 100))
        profiles[demand] = v.copy()
        records.append({
            "demand_percent": demand,
            "min_voltage_pu": float(v.min()),
            "weakest_bus_1_based": int(v.idxmin()) + 1,
            "buses_below_095": int((v < 0.95).sum()),
            "line_losses_mw": float(net.res_line.pl_mw.sum()),
        })

    df = pd.DataFrame(records)
    print("\nLOAD-GROWTH RESULTS\n" + df.to_string(index=False))
    df.to_csv(RESULTS / "load_growth_results.csv", index=False)
    pd.DataFrame({f"{k}_percent": v for k, v in profiles.items()}).rename_axis(
        "bus_index_0_based"
    ).to_csv(RESULTS / "load_growth_bus_voltages.csv")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df["demand_percent"], df["min_voltage_pu"], marker="o")
    ax.axhline(0.95, color="red", linestyle="--", label="0.95 p.u. reference")
    ax.set(xlabel="Demand (% of baseline)", ylabel="Minimum voltage (p.u.)",
           title="Minimum Network Voltage vs Demand")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "minimum_voltage_vs_demand.png", dpi=200)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(df["demand_percent"].astype(str), df["buses_below_095"])
    ax.set(xlabel="Demand (% of baseline)", ylabel="Number of buses below 0.95 p.u.",
           title="Undervoltage Buses vs Demand")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES / "undervoltage_buses_vs_demand.png", dpi=200)

    fig, ax = plt.subplots(figsize=(10, 6))
    for demand, v in profiles.items():
        ax.scatter(v.index + 1, v.values, s=23, label=f"{demand}% demand")
    ax.axhline(0.95, color="red", linestyle="--", label="0.95 p.u. reference")
    ax.set(xlabel="Bus number (1–33)", ylabel="Voltage (p.u.)",
           title="Bus Voltage Profiles under Load Growth")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "load_growth_voltage_profiles.png", dpi=200)
    plt.show()


if __name__ == "__main__":
    main()
