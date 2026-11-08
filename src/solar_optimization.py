"""Experiment 3: compare solar placement at all 32 non-slack buses."""

import pandas as pd
import matplotlib.pyplot as plt
import pandapower as pp
import pandapower.networks as pn
from pathlib import Path

# Conventional bus numbers (1 to 33)
buses_to_test = list(range(2, 34))
solar_sizes = [0.25, 0.5, 1.0, 1.5]  # MW

folder = Path(__file__).resolve().parents[1] / "results"
folder.mkdir(exist_ok=True)
(folder / "figures").mkdir(exist_ok=True)

# Original network without solar
base_net = pn.case33bw()
pp.runpp(base_net, numba=False)
original_losses = base_net.res_line.pl_mw.sum() * 1000

results = []

for bus in buses_to_test:
    for solar_power in solar_sizes:
        # Start with the original network every time
        net = pn.case33bw()

        # Python bus indices start at 0: Bus 18 -> index 17
        pp.create_sgen(net, bus=bus - 1, p_mw=solar_power,
                       q_mvar=0, name="Solar generator")
        pp.runpp(net, numba=False)

        voltages = net.res_bus.vm_pu
        losses = net.res_line.pl_mw.sum() * 1000  # kW
        low_buses = int((voltages < 0.95).sum())
        high_buses = int((voltages > 1.05).sum())

        results.append({
            "Bus": bus,
            "Solar (MW)": solar_power,
            "Losses (kW)": round(losses, 3),
            "Minimum voltage": round(voltages.min(), 4),
            "Maximum voltage": round(voltages.max(), 4),
            "Buses below 0.95": low_buses,
            "Buses above 1.05": high_buses,
        })

df = pd.DataFrame(results)
print(f"\nALL {len(df)} TEST CASES")
print(df.to_string(index=False))

# Find the lowest losses among the combinations we tested
best = df.loc[df["Losses (kW)"].idxmin()]
reduction = 100 * (original_losses - best["Losses (kW)"]) / original_losses

print("\nLowest-loss TESTED combination:")
print(f"Bus {int(best['Bus'])}, {best['Solar (MW)']} MW")
print(f"Losses: {best['Losses (kW)']:.2f} kW (baseline {original_losses:.2f} kW)")
print(f"Loss reduction: {reduction:.1f}%")
print(f"Minimum bus voltage: {best['Minimum voltage']:.4f} p.u.")

# Is the 0.95 to 1.05 p.u. voltage requirement met?
valid = df[(df["Buses below 0.95"] == 0) & (df["Buses above 1.05"] == 0)]
if valid.empty:
    print("\nNo tested combination satisfies the 0.95–1.05 p.u. voltage range.")
else:
    best_valid = valid.loc[valid["Losses (kW)"].idxmin()]
    print(f"Lowest-loss voltage-compliant case: Bus {int(best_valid['Bus'])}, "
          f"{best_valid['Solar (MW)']} MW")

# Simple graph: best tested loss for each of the 32 buses
best_per_bus = df.loc[df.groupby("Bus")["Losses (kW)"].idxmin()].sort_values("Bus")
plt.figure(figsize=(12, 5))
plt.bar(best_per_bus["Bus"].astype(str), best_per_bus["Losses (kW)"])
plt.axhline(original_losses, color="red", linestyle="--", label="No solar")
plt.xlabel("Solar installation bus")
plt.ylabel("Total line losses (kW)")
plt.title("Lowest Tested Line Losses at Each Bus")
plt.legend()
plt.tight_layout()
plt.savefig(folder / "figures" / "solar_placement_comparison.png", dpi=200)

# Save the complete table as well
df.to_csv(folder / "solar_placement_results.csv", index=False)
plt.show()
