"""
Publication-Quality Figure Generation Pipeline
==============================================
Generates three high-resolution (300 DPI) scientific figures for Deliverable 5:
- Fig 1: Energy-per-Operation across Algorithms and Data Distributions
- Fig 2: 21-Day Power, Thermal Accumulation & Frequency Throttling Trends
- Fig 3: Empirical Energy Scaling vs Theoretical Complexity Regression Models
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns


def setup_plotting_style():
    """Configures global academic publication styling."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "axes.edgecolor": "#333333",
        "axes.linewidth": 1.0,
        "grid.color": "#E0E0E0",
        "grid.linestyle": "--",
        "grid.alpha": 0.6,
        "xtick.major.width": 1.0,
        "ytick.major.width": 1.0,
        "figure.titlesize": 14,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
    })


def generate_figure_1(df: pd.DataFrame, output_path: str):
    """
    Fig 1: Energy-per-Operation (uJ/op) and Total Energy by Algorithm & Input Size.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    palette = {"Random": "#1976D2", "Nearly_Sorted": "#388E3C", "Reverse_Sorted": "#D32F2F"}

    # Subplot A: Energy per operation (uJ/op)
    sns.barplot(
        data=df,
        x="algorithm",
        y="energy_per_op_uj",
        hue="data_distribution",
        palette=palette,
        ax=ax1,
        capsize=0.08,
        err_kws={"linewidth": 1.2},
    )
    ax1.set_title("(A) Energy-per-Operation by Algorithm & Distribution", fontweight="bold", pad=10)
    ax1.set_xlabel("Algorithm", fontweight="bold")
    ax1.set_ylabel("Energy per Operation (μJ / op)", fontweight="bold")
    ax1.grid(True, axis="y")
    ax1.legend(title="Data Distribution", frameon=True, loc="upper right")
    ax1.tick_params(axis="x", rotation=10)

    # Annotate key observation
    ax1.text(
        0.05, 0.90,
        "Merge Sort exhibits higher μJ/op\ndue to DRAM memory allocation overhead",
        transform=ax1.transAxes,
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF9C4", edgecolor="#FBC02D", alpha=0.9),
    )

    # Subplot B: Total Energy Consumed (Joules) vs Input Size (Log Scale)
    algo_colors = {
        "Bubble Sort": "#C62828",
        "Merge Sort": "#2E7D32",
        "Quick Sort": "#1565C0",
        "Heap Sort": "#7B1FA2",
    }
    algo_markers = {
        "Bubble Sort": "o",
        "Merge Sort": "s",
        "Quick Sort": "^",
        "Heap Sort": "D",
    }

    random_df = df[df["data_distribution"] == "Random"]
    size_summary = random_df.groupby(["algorithm", "input_size"])["total_energy_j"].mean().reset_index()

    for algo in ["Bubble Sort", "Quick Sort", "Merge Sort", "Heap Sort"]:
        sub = size_summary[size_summary["algorithm"] == algo]
        ax2.plot(
            sub["input_size"],
            sub["total_energy_j"],
            marker=algo_markers[algo],
            linewidth=2.2,
            markersize=7,
            label=algo,
            color=algo_colors[algo],
        )

    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_title("(B) Total Software Energy Scaling vs Input Size N", fontweight="bold", pad=10)
    ax2.set_xlabel("Input Size N (Log Scale)", fontweight="bold")
    ax2.set_ylabel("Mean Energy Consumed (Joules, Log Scale)", fontweight="bold")
    ax2.grid(True, which="both", axis="both")
    ax2.legend(title="Algorithm", frameon=True, loc="upper left")

    # Annotate quadratic gap
    ax2.annotate(
        "Quadratic Energy Gap:\nBubble Sort draws ~325x\nmore energy at N=50k",
        xy=(50000, 395.0),
        xytext=(15000, 15.0),
        arrowprops=dict(facecolor="#C62828", shrink=0.08, width=1.5, headwidth=7),
        fontsize=9,
        fontweight="bold",
        color="#B71C1C",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFEBEE", edgecolor="#EF9A9A"),
    )

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[+] Saved Figure 1: {output_path}")


def generate_figure_2(df: pd.DataFrame, output_path: str):
    """
    Fig 2: 21-Day Power, Thermal Accumulation & Frequency Throttling Trends.
    """
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(13, 10), dpi=300, sharex=True)

    daily_stats = df.groupby(["day_index", "session_period"]).agg({
        "cpu_pkg_power_w": "mean",
        "idle_baseline_power_w": "mean",
        "pkg_temp_c": "mean",
        "cpu_freq_mhz": "mean",
    }).reset_index()

    daily_avg = df.groupby("day_index").agg({
        "cpu_pkg_power_w": "mean",
        "pkg_temp_c": "mean",
        "cpu_freq_mhz": "mean",
    }).reset_index()

    days = daily_avg["day_index"].values

    # Panel 1: Package Power Draw
    ax1.plot(
        days, daily_avg["cpu_pkg_power_w"],
        color="#1565C0", marker="o", linewidth=2.0, markersize=5, label="Daily Mean Package Power (W)"
    )
    # Highlight OS background spike days (Day 7 and Day 14)
    ax1.axvspan(6.5, 7.5, color="#FFE082", alpha=0.45, label="OS Background Spike Event (Day 7)")
    ax1.axvspan(13.5, 14.5, color="#FFCC80", alpha=0.45, label="OS Background Spike Event (Day 14)")
    ax1.set_ylabel("Power Draw (Watts)", fontweight="bold")
    ax1.set_title("21-Day Continuous Longitudinal Telemetry: Power, Temperature & Frequency Dynamics", fontweight="bold", pad=12)
    ax1.grid(True)
    ax1.legend(loc="upper right", frameon=True)
    ax1.set_ylim(bottom=15.0, top=26.0)

    # Panel 2: CPU Package Temperature & Thermal Accumulation Drift
    ax2.plot(
        days, daily_avg["pkg_temp_c"],
        color="#D32F2F", marker="s", linewidth=2.0, markersize=5, label="Daily Mean Temperature (°C)"
    )
    # Trendline for thermal drift
    z_temp = np.polyfit(days, daily_avg["pkg_temp_c"], 1)
    p_temp = np.poly1d(z_temp)
    ax2.plot(days, p_temp(days), "--", color="#B71C1C", linewidth=1.8, label=f"Thermal Drift Fit (+{z_temp[0]:.2f} °C/day)")

    ax2.set_ylabel("Package Temp (°C)", fontweight="bold")
    ax2.grid(True)
    ax2.legend(loc="upper left", frameon=True)
    ax2.set_ylim(bottom=45.0, top=58.0)

    # Panel 3: Operating Frequency & Thermal Throttling
    ax3.plot(
        days, daily_avg["cpu_freq_mhz"],
        color="#2E7D32", marker="^", linewidth=2.0, markersize=5, label="Mean CPU Core Frequency (MHz)"
    )
    z_freq = np.polyfit(days, daily_avg["cpu_freq_mhz"], 1)
    p_freq = np.poly1d(z_freq)
    ax3.plot(days, p_freq(days), "--", color="#1B5E20", linewidth=1.8, label=f"Throttling Slope ({z_freq[0]:.2f} MHz/day)")

    ax3.set_ylabel("Frequency (MHz)", fontweight="bold")
    ax3.set_xlabel("Benchmarking Day Index (Day 1 to Day 21)", fontweight="bold")
    ax3.set_xticks(range(1, 22))
    ax3.grid(True)
    ax3.legend(loc="upper right", frameon=True)
    ax3.set_ylim(bottom=3650.0, top=3950.0)

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[+] Saved Figure 2: {output_path}")


def generate_figure_3(df: pd.DataFrame, output_path: str):
    """
    Fig 3: Empirical Energy Scaling vs Theoretical Complexity Regression Models.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # Subplot A: O(N log N) Algorithms
    n_log_n_algos = ["Quick Sort", "Merge Sort", "Heap Sort"]
    colors = {"Quick Sort": "#1565C0", "Merge Sort": "#2E7D32", "Heap Sort": "#7B1FA2"}
    markers = {"Quick Sort": "^", "Merge Sort": "s", "Heap Sort": "D"}

    for algo in n_log_n_algos:
        sub = df[df["algorithm"] == algo]
        n_vals = sub["input_size"].values
        energy_vals = sub["total_energy_j"].values

        x_feat = n_vals * np.log2(n_vals)
        # Sort for smooth regression line
        sort_idx = np.argsort(x_feat)
        x_sorted = x_feat[sort_idx]
        y_sorted = energy_vals[sort_idx]

        # Fit linear through origin
        coef = np.sum(x_sorted * y_sorted) / np.sum(x_sorted ** 2)
        r2 = 1.0 - (np.sum((y_sorted - coef * x_sorted)**2) / np.sum((y_sorted - np.mean(y_sorted))**2))

        # Sample empirical points for scatter
        sub_sample = sub.sample(n=min(120, len(sub)), random_state=42)
        ax1.scatter(
            sub_sample["input_size"] * np.log2(sub_sample["input_size"]),
            sub_sample["total_energy_j"],
            alpha=0.45,
            color=colors[algo],
            marker=markers[algo],
            s=22,
        )

        ax1.plot(
            x_sorted,
            coef * x_sorted,
            color=colors[algo],
            linewidth=2.2,
            label=f"{algo}: E={coef:.2e}*(N log N) (R²={r2:.3f})",
        )

    ax1.set_title("(A) O(N log N) Algorithms: Energy vs Theoretical Complexity", fontweight="bold", pad=10)
    ax1.set_xlabel("Complexity Metric: N · log₂(N)", fontweight="bold")
    ax1.set_ylabel("Measured Total Energy (Joules)", fontweight="bold")
    ax1.grid(True)
    ax1.legend(loc="upper left", frameon=True, fontsize=8.5)

    # Subplot B: Quadratic Bubble Sort
    bubble_sub = df[df["algorithm"] == "Bubble Sort"]
    b_n = bubble_sub["input_size"].values
    b_energy = bubble_sub["total_energy_j"].values
    b_n2 = b_n ** 2

    sort_b = np.argsort(b_n2)
    b_n2_sorted = b_n2[sort_b]
    b_energy_sorted = b_energy[sort_b]

    coef_b = np.sum(b_n2_sorted * b_energy_sorted) / np.sum(b_n2_sorted ** 2)
    r2_b = 1.0 - (np.sum((b_energy_sorted - coef_b * b_n2_sorted)**2) / np.sum((b_energy_sorted - np.mean(b_energy_sorted))**2))

    bubble_sample = bubble_sub.sample(n=min(120, len(bubble_sub)), random_state=42)
    ax2.scatter(
        bubble_sample["input_size"],
        bubble_sample["total_energy_j"],
        alpha=0.55,
        color="#C62828",
        marker="o",
        s=25,
        label="Measured Trials",
    )

    # Smooth curve for plotting
    n_dense = np.linspace(min(b_n), max(b_n), 100)
    ax2.plot(
        n_dense,
        coef_b * (n_dense ** 2),
        color="#B71C1C",
        linewidth=2.5,
        label=f"Quadratic Regression Fit (R²={r2_b:.3f})\nE(N) = {coef_b:.2e} · N²",
    )

    ax2.set_title("(B) Bubble Sort: Quadratic Energy Explosion E(N) ∝ N²", fontweight="bold", pad=10)
    ax2.set_xlabel("Input Size N", fontweight="bold")
    ax2.set_ylabel("Measured Total Energy (Joules)", fontweight="bold")
    ax2.grid(True)
    ax2.legend(loc="upper left", frameon=True, fontsize=9)

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[+] Saved Figure 3: {output_path}")


def main():
    setup_plotting_style()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cleaned_csv = os.path.join(base_dir, "..", "..", "Deliverable_2_Datasets", "cleaned_rapl_benchmark_21days.csv")
    fig_dir = os.path.join(base_dir, "..", "..", "Deliverable_5_Final_Report", "figures")

    if not os.path.exists(cleaned_csv):
        print(f"[!] Cleaned dataset not found at: {cleaned_csv}")
        return

    print(f"[*] Generating high-resolution figures from: {cleaned_csv}")
    df = pd.read_csv(cleaned_csv)

    fig1_path = os.path.join(fig_dir, "fig1_energy_per_operation_by_algorithm.png")
    fig2_path = os.path.join(fig_dir, "fig2_21day_power_and_thermal_trend.png")
    fig3_path = os.path.join(fig_dir, "fig3_regression_model_energy_scaling.png")

    generate_figure_1(df, fig1_path)
    generate_figure_2(df, fig2_path)
    generate_figure_3(df, fig3_path)
    print("[*] All publication figures successfully generated!")


if __name__ == "__main__":
    main()
