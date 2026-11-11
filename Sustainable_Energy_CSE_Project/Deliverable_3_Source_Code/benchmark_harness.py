#!/usr/bin/env python3
"""
GreenCode Benchmarking Harness - Software Energy-per-Operation CLI Prototype
=============================================================================
Course: Sustainable Energy Engineering (B.Tech CSE)
Topic: Energy-per-Computation Benchmarking Tool for Software

Executes live algorithmic benchmarking trials, measures hardware power draw
via Intel RAPL or calibrated CMOS thermal/frequency model, calculates energy
per operation (microjoules/op), and outputs a Green Coding Scorecard.
"""

import sys
import os
import argparse
import time
import csv
from typing import List, Dict, Any, Tuple

# Ensure local package import works
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from src.algorithms import ALGORITHMS, ALGORITHM_LABELS, generate_dataset
from src.rapl_power_meter import RAPLPowerMeter


def calculate_green_grade(energy_per_10k_j: float) -> Tuple[str, str]:
    """
    Assigns an energy sustainability letter grade based on energy consumed
    to sort 10,000 items.
    """
    if energy_per_10k_j < 0.10:
        return "A+", "Exceptional Green Efficiency (Minimal Carbon Footprint)"
    elif energy_per_10k_j < 0.30:
        return "A ", "High Energy Efficiency (Optimized Compute/Memory Access)"
    elif energy_per_10k_j < 0.80:
        return "B ", "Moderate Efficiency (Standard Algorithmic Overhead)"
    elif energy_per_10k_j < 2.50:
        return "C ", "Suboptimal Efficiency (Elevated Memory Pressure/ALU Cycles)"
    elif energy_per_10k_j < 10.0:
        return "D ", "Poor Energy Efficiency (High Thermal Dissipation)"
    else:
        return "F ", "Critical Energy Waste (Quadratic/Exorbitant Resource Draw)"


def run_benchmark_trial(
    algo_name: str,
    size: int,
    distribution: str,
    meter: RAPLPowerMeter,
) -> Dict[str, Any]:
    """Runs a single live trial for an algorithm and returns measured metrics."""
    data = generate_dataset(size, distribution)
    sort_func = ALGORITHMS[algo_name]

    # Pre-trial stabilization
    time.sleep(0.05)

    meter.start()
    sorted_arr, comparisons, swaps, total_ops = sort_func(data)
    telemetry = meter.stop()

    # Prevent division by zero
    safe_ops = max(1, total_ops)
    energy_uj = telemetry["total_energy_j"] * 1e6
    energy_per_op_uj = energy_uj / safe_ops
    energy_per_op_nj = energy_per_op_uj * 1000.0

    # Normalized metric: Joules per 10,000 items
    energy_per_10k_j = (telemetry["total_energy_j"] / max(1, size)) * 10000.0
    grade, grade_desc = calculate_green_grade(energy_per_10k_j)

    # Financial Cost Calculation in Indian Rupees (INR - ₹) at ₹8.50 / kWh
    TARIFF_INR_PER_KWH = 8.50
    cost_inr = (telemetry["total_energy_j"] / 3.6e6) * TARIFF_INR_PER_KWH
    cost_paise = cost_inr * 100.0

    return {
        "algorithm": algo_name,
        "algorithm_label": ALGORITHM_LABELS.get(algo_name, algo_name),
        "input_size": size,
        "distribution": distribution,
        "comparisons": comparisons,
        "swaps": swaps,
        "total_operations": total_ops,
        "execution_time_ms": telemetry["execution_time_ms"],
        "cpu_pkg_power_w": telemetry["cpu_pkg_power_w"],
        "idle_baseline_power_w": telemetry["idle_baseline_power_w"],
        "dynamic_power_w": telemetry["dynamic_power_w"],
        "total_energy_j": telemetry["total_energy_j"],
        "total_energy_mj": telemetry["total_energy_mj"],
        "energy_per_op_uj": round(energy_per_op_uj, 4),
        "energy_per_op_nj": round(energy_per_op_nj, 2),
        "energy_per_10k_j": round(energy_per_10k_j, 4),
        "cost_inr": round(cost_inr, 8),
        "cost_paise": round(cost_paise, 6),
        "green_grade": grade,
        "grade_desc": grade_desc,
        "cpu_freq_mhz": telemetry["cpu_freq_mhz"],
        "cpu_util_pct": telemetry["cpu_util_pct"],
        "pkg_temp_c": telemetry["pkg_temp_c"],
        "sensor_source": telemetry["sensor_source"],
    }


def print_scorecard(results: List[Dict[str, Any]]):
    """Prints a structured ASCII terminal scorecard with energy & Rupee cost metrics."""
    print("\n" + "=" * 125)
    print("                     GREENCODE SOFTWARE ENERGY & RUPEE (INR) BENCHMARKING SCORECARD")
    print("=" * 125)
    header = (
        f"{'Algorithm':<14} | {'Dist':<11} | {'Size':>7} | {'Time (ms)':>10} | "
        f"{'Power (W)':>9} | {'Energy (J)':>11} | {'uJ/Op':>9} | {'Cost (p / ₹)':>13} | {'Grade':<5}"
    )
    print(header)
    print("-" * 125)

    for r in results:
        # Format cost nicely in paise if small, or rupees
        if r["cost_inr"] < 0.01:
            cost_str = f"{r['cost_paise']:>9.4f} p"
        else:
            cost_str = f"₹{r['cost_inr']:>8.4f}"

        line = (
            f"{r['algorithm']:<14} | "
            f"{r['distribution']:<11} | "
            f"{r['input_size']:>7} | "
            f"{r['execution_time_ms']:>10.2f} | "
            f"{r['cpu_pkg_power_w']:>9.2f} | "
            f"{r['total_energy_j']:>11.5f} | "
            f"{r['energy_per_op_uj']:>9.4f} | "
            f"{cost_str:>13} | "
            f"[{r['green_grade']}]"
        )
        print(line)

    print("=" * 125)
    
    # Calculate comparative savings
    bubble_runs = [r for r in results if r["algorithm"] == "bubble"]
    quick_runs = [r for r in results if r["algorithm"] == "quick"]

    if bubble_runs and quick_runs:
        b_energy = sum(r["total_energy_j"] for r in bubble_runs) / len(bubble_runs)
        q_energy = sum(r["total_energy_j"] for r in quick_runs) / len(quick_runs)
        b_cost = sum(r["cost_inr"] for r in bubble_runs) / len(bubble_runs)
        q_cost = sum(r["cost_inr"] for r in quick_runs) / len(quick_runs)
        reduction_pct = ((b_energy - q_energy) / b_energy) * 100.0 if b_energy > 0 else 0
        factor = b_energy / q_energy if q_energy > 0 else 0
        savings_per_100k_runs_inr = (b_cost - q_cost) * 100000.0
        print(f"\n>> KEY SUSTAINABILITY & FINANCIAL FINDINGS (INR @ ₹8.50/kWh):")
        print(f"   Switching from unoptimized Quadratic (Bubble) to Divide-and-Conquer (Quick Sort)")
        print(f"   - Reduced software energy draw by {reduction_pct:.2f}% ({factor:.1f}x energy reduction).")
        print(f"   - Average run cost: Bubble = {b_cost*100:.4f} paise vs Quick = {q_cost*100:.5f} paise.")
        print(f"   - Financial savings: ₹{savings_per_100k_runs_inr:.2f} saved per 100,000 algorithmic executions.")
        print(f"   - Sensor Telemetry Source: {results[0]['sensor_source']}")
    print("=" * 125 + "\n")


def export_csv(results: List[Dict[str, Any]], filepath: str):
    """Exports benchmark results to a CSV file."""
    if not results:
        return
    fieldnames = list(results[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"[+] Benchmark results exported to: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="GreenCode: Software Energy-per-Computation Benchmarking Harness"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a quick comparative live demonstration across 4 algorithms.",
    )
    parser.add_argument(
        "--algorithms",
        type=str,
        default="quick,merge,heap,bubble",
        help="Comma-separated algorithms to benchmark (choices: bubble, quick, merge, heap, all).",
    )
    parser.add_argument(
        "--sizes",
        type=str,
        default="1000,3000,6000",
        help="Comma-separated input sizes (e.g. 1000,5000,10000).",
    )
    parser.add_argument(
        "--distributions",
        type=str,
        default="random,nearly_sorted,reverse_sorted",
        help="Comma-separated distributions (random, nearly_sorted, reverse_sorted).",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=2,
        help="Number of trial repetitions per configuration.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to output CSV file.",
    )
    args = parser.parse_args()

    meter = RAPLPowerMeter()
    print("\n" + "=" * 70)
    print("      GREENCODE: ENERGY-PER-COMPUTATION BENCHMARKING HARNESS")
    print("=" * 70)
    print(f"Telemetry Engine : {meter.sensor_source}")
    print(f"Hardware TDP Spec: {meter.tdp_w:.1f} W | Platform Idle Baseline: {meter.idle_baseline_w:.1f} W")
    print(f"RAPL Available   : {'Yes (Direct MSR /sys/class/powercap)' if meter.is_rapl_available else 'No (Active Calibrated CMOS Fallback)'}")
    print("=" * 70)

    if args.demo:
        print("\n[*] Executing Live Demonstration (Comparative green audit on N=4000 items)...")
        demo_algos = ["bubble", "merge", "quick", "heap"]
        demo_results = []
        for algo in demo_algos:
            print(f"    -> Running {ALGORITHM_LABELS[algo]} on Random dataset...")
            res = run_benchmark_trial(algo, size=4000, distribution="random", meter=meter)
            demo_results.append(res)
        print_scorecard(demo_results)
        if args.output:
            export_csv(demo_results, args.output)
        return

    # Parse arguments
    if args.algorithms.strip().lower() == "all":
        algos = list(ALGORITHMS.keys())
    else:
        algos = [a.strip().lower() for a in args.algorithms.split(",") if a.strip().lower() in ALGORITHMS]

    sizes = [int(s.strip()) for s in args.sizes.split(",") if s.strip().isdigit()]
    dists = [d.strip().lower() for d in args.distributions.split(",") if d.strip().lower() in ["random", "nearly_sorted", "reverse_sorted"]]

    all_results = []
    total_configs = len(algos) * len(sizes) * len(dists) * args.runs
    current_idx = 0

    print(f"[*] Starting benchmark matrix ({total_configs} total trials across {len(algos)} algorithms)...")

    for algo in algos:
        for size in sizes:
            # Guard against excessive wait on quadratic bubble sort for very large N in interactive mode
            if algo == "bubble" and size > 25000:
                print(f"[!] Warning: Skipping Bubble Sort for N={size} to avoid non-responsive terminal execution.")
                continue

            for dist in dists:
                for rep in range(args.runs):
                    current_idx += 1
                    print(f"    [{current_idx}/{total_configs}] Benchmarking {algo} | N={size} | Dist={dist} (Run {rep+1}/{args.runs})...", end="\r")
                    res = run_benchmark_trial(algo, size, dist, meter)
                    all_results.append(res)

    print("\n[*] Benchmarking complete!")
    print_scorecard(all_results)

    if args.output:
        export_csv(all_results, args.output)


if __name__ == "__main__":
    from typing import Tuple
    main()
