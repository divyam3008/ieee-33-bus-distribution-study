"""Single-bus fixed-P solar injection at conventional Bus 18 (index 17)."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pandapower as pp
import pandapower.networks as pn

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"
SOLAR_MW = [0.0, 0.25, 0.50, 1.0, 1.5]
SOLAR_BUS = 17  # pandapower zero-based index = conventional Bus 18


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    records = []
    profiles = {}

    for p_mw in SOLAR_MW:
        net = pn.case33bw()
        if p_mw > 0:
            pp.create_sgen(net, bus=SOLAR_BUS, p_mw=p_mw, q_mvar=0,
                           name="Fixed active-power solar injection")
        pp.runpp(net, numba=False)
        v = net.res_bus.vm_pu
        profiles[p_mw] = v.copy()
        records.append({
            "solar_generation_mw": p_mw,
            "min_voltage_pu": float(v.min()),
            "weakest_bus_1_based": int(v.idxmin()) + 1,
            "max_voltage_pu": float(v.max()),
            "line_losses_mw": float(net.res_line.pl_mw.sum()),
            "buses_below_095": int((v < 0.95).sum()),
            "buses_above_105": int((v > 1.05).sum()),
            "net_slack_import_mw": float(net.res_ext_grid.p_mw.sum()),
        })

    df = pd.DataFrame(records)
    print("\nSOLAR INTEGRATION RESULTS\n" + df.to_string(index=False))
    baseline = df.loc[df["solar_generation_mw"] == 0, "line_losses_mw"].iloc[0]
    best = df.loc[df["line_losses_mw"].idxmin()]
    print(f"Lowest losses among sampled sizes: {best['solar_generation_mw']:.2f} MW")
    print(f"Loss reduction vs no-solar case: {(1 - best['line_losses_mw']/baseline)*100:.1f}%")
    df.to_csv(RESULTS / "solar_integration_results.csv", index=False)
    pd.DataFrame({f"{p:g}_mw": v for p, v in profiles.items()}).rename_axis(
        "bus_index_0_based"
    ).to_csv(RESULTS / "solar_bus_voltages.csv")

    fig, ax = plt.subplots(figsize=(10, 6))
    for p_mw, v in profiles.items():
        ax.scatter(v.index + 1, v.values, s=21, label=f"{p_mw:g} MW solar")
    ax.axhline(0.95, color="red", linestyle="--", label="0.95 p.u. reference")
    ax.axhline(1.05, color="orange", linestyle="--", label="1.05 p.u. reference")
    ax.set(xlabel="Bus number (1–33)", ylabel="Voltage (p.u.)",
           title="Bus Voltage Profiles vs Solar Injection")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "solar_voltage_profiles_regenerated.png", dpi=200)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df["solar_generation_mw"], df["min_voltage_pu"], marker="o", label="Minimum voltage")
    ax.plot(df["solar_generation_mw"], df["max_voltage_pu"], marker="s", label="Maximum voltage")
    ax.axhline(0.95, color="red", linestyle="--")
    ax.axhline(1.05, color="orange", linestyle="--")
    ax.set(xlabel="Solar injection (MW)", ylabel="Voltage (p.u.)",
           title="Minimum and Maximum Voltage vs Solar Injection")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "solar_voltage_limits_regenerated.png", dpi=200)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df["solar_generation_mw"], df["line_losses_mw"], marker="o")
    ax.set(xlabel="Solar injection (MW)", ylabel="Total active line losses (MW)",
           title="Line Losses vs Solar Injection")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES / "solar_line_losses_regenerated.png", dpi=200)
    plt.show()


if __name__ == "__main__":
    main()
