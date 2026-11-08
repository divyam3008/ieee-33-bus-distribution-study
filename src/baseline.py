"""Base-case AC load-flow analysis on the IEEE 33-bus distribution feeder."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandapower as pp
import pandapower.networks as pn

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    net = pn.case33bw()
    pp.runpp(net, numba=False)
    v = net.res_bus.vm_pu

    print("IEEE 33-bus feeder — baseline")
    print(f"Number of buses: {len(net.bus)}")
    print(f"Minimum voltage: {v.min():.4f} p.u., at bus {int(v.idxmin())+1}")
    print(f"Maximum voltage: {v.max():.4f} p.u.")
    print(f"Buses under 0.95 p.u.: {(v < 0.95).sum()}")
    print(f"Total active line loss: {net.res_line.pl_mw.sum():.4f} MW")

    v.rename("voltage_pu").to_csv(RESULTS / "baseline_bus_voltages.csv", header=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(v.index + 1, v.values, s=26)
    ax.axhline(0.95, color="red", linestyle="--", label="0.95 p.u. study reference")
    ax.set(xlabel="Bus number (1–33)", ylabel="Voltage (p.u.)",
           title="IEEE 33-Bus Distribution Feeder — Baseline Voltages")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "baseline_bus_voltages.png", dpi=200)
    plt.show()


if __name__ == "__main__":
    main()
