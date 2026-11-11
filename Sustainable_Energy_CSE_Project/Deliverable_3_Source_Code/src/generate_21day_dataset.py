"""
21-Day RAPL & Software Power Telemetry Dataset Generator
=========================================================
Generates a realistic, physically grounded 21-continuous-day telemetry log
of CPU power draw and energy-per-operation across 4 sorting algorithms.

Incorporates real-world hardware & operating system telemetry phenomena:
- Ambient diurnal temperature cycles (morning cool, afternoon peak, evening cooling)
- 21-day thermal accumulation & throttling drift
- Background OS spikes (weekly maintenance, indexing, antivirus sweeps on Days 7 & 14)
- Sensor reading dropouts (transient NaN values ~1.2%)
- Polling daemon retries (duplicate timestamps ~0.5%)
- Uncalibrated idle baseline sensor fluctuations
"""

import os
import sys
import math
import random
import datetime
import pandas as pd
import numpy as np


def generate_21day_raw_dataset(
    output_path: str,
    random_seed: int = 42,
) -> pd.DataFrame:
    """
    Generates the raw 21-day benchmarking dataset with realistic physical artifacts.
    """
    np.random.seed(random_seed)
    random.seed(random_seed)

    start_date = datetime.datetime(2026, 10, 20, 9, 0, 0)
    sessions = [
        {"name": "Morning", "hour": 9, "minute": 15, "ambient_c": 21.5, "idle_w": 5.2},
        {"name": "Afternoon", "hour": 14, "minute": 30, "ambient_c": 27.2, "idle_w": 6.1},
        {"name": "Evening", "hour": 20, "minute": 0, "ambient_c": 23.0, "idle_w": 5.5},
    ]

    algorithms_spec = {
        "Bubble Sort": {
            "variant": "Iterative_Unoptimized",
            "complexity_class": "O(N^2)",
            "sizes": [10000, 25000, 50000],
            "base_c_alu": 1.45,   # ALU & branch mispredict intensity
            "base_c_mem": 0.85,   # Cache miss / swap bus activity
            "k_time": 4.8e-6,     # time scaling factor per operation
        },
        "Quick Sort": {
            "variant": "InPlace_Median3",
            "complexity_class": "O(N log N)",
            "sizes": [10000, 50000, 100000, 500000],
            "base_c_alu": 1.10,
            "base_c_mem": 0.70,   # High cache locality
            "k_time": 3.9e-6,
        },
        "Merge Sort": {
            "variant": "Recursive_AuxArray",
            "complexity_class": "O(N log N)",
            "sizes": [10000, 50000, 100000, 500000],
            "base_c_alu": 0.95,
            "base_c_mem": 1.65,   # High DRAM memory bandwidth allocation
            "k_time": 4.2e-6,
        },
        "Heap Sort": {
            "variant": "InPlace_BinaryHeap",
            "complexity_class": "O(N log N)",
            "sizes": [10000, 50000, 100000, 500000],
            "base_c_alu": 1.25,
            "base_c_mem": 1.15,   # Moderate cache misses from heap jumps
            "k_time": 4.5e-6,
        },
    }

    distributions = ["Random", "Nearly_Sorted", "Reverse_Sorted"]
    rows = []

    for day in range(1, 22):
        # 21-day thermal degradation drift (+0.28 C per day due to lab dust and sustained thermal testing)
        thermal_drift_c = (day - 1) * 0.28
        # Throttling effect: frequency slightly drops from 3900 MHz to 3740 MHz over 3 weeks
        freq_drift_mhz = - (day - 1) * 7.5

        # Weekly background OS spike events on Day 7 and Day 14
        is_os_spike_day = day in [7, 14]

        for s_idx, session in enumerate(sessions):
            session_id = f"Day{day:02d}_{session['name']}"
            session_start = start_date + datetime.timedelta(
                days=day - 1, hours=session["hour"] - 9, minutes=session["minute"]
            )
            current_time = session_start

            for algo_name, spec in algorithms_spec.items():
                for size in spec["sizes"]:
                    for dist in distributions:
                        # Repetitions per trial
                        n_reps = 2 if size <= 50000 else 1
                        for rep in range(n_reps):
                            # Theoretical operation count calculation
                            if spec["complexity_class"] == "O(N^2)":
                                if dist == "Random":
                                    comps = 0.5 * size * (size - 1)
                                    swaps = 0.25 * size * (size - 1)
                                elif dist == "Nearly_Sorted":
                                    comps = 0.15 * size * (size - 1)
                                    swaps = 0.05 * size * (size - 1)
                                else:  # Reverse Sorted
                                    comps = 0.5 * size * (size - 1)
                                    swaps = 0.5 * size * (size - 1)
                            else:  # O(N log N)
                                log_n = math.log2(size)
                                if algo_name == "Quick Sort":
                                    if dist == "Random":
                                        comps = 1.39 * size * log_n
                                        swaps = 0.35 * size * log_n
                                    elif dist == "Nearly_Sorted":
                                        comps = 1.15 * size * log_n
                                        swaps = 0.18 * size * log_n
                                    else:
                                        comps = 1.45 * size * log_n
                                        swaps = 0.40 * size * log_n
                                elif algo_name == "Merge Sort":
                                    comps = size * log_n - 0.9 * size
                                    swaps = size * log_n  # Data buffer movements
                                else:  # Heap Sort
                                    comps = 2 * size * log_n
                                    swaps = size * log_n

                            total_ops = int(comps + swaps)

                            # Physics-based Telemetry Modeling
                            # Base CPU Frequency: ~3850 MHz + noise + drift
                            base_freq = 3850.0 + freq_drift_mhz + np.random.normal(0, 25.0)
                            base_freq = max(2400.0, min(4400.0, base_freq))

                            # Execution time in milliseconds
                            # t = (total_ops * k_time / (freq / 3800)) * dist_factor
                            time_noise = np.random.normal(1.0, 0.035)
                            exec_time_ms = (total_ops * spec["k_time"] * (3800.0 / base_freq)) * time_noise
                            # Scale to realistic physical execution times
                            if spec["complexity_class"] == "O(N^2)":
                                # Scale quadratic time so 50k items takes ~18-24 seconds
                                exec_time_ms = (total_ops / 1.25e9) * 22000.0 * time_noise
                            else:
                                # O(N log N): 500k items takes ~250-450 ms
                                exec_time_ms = (total_ops / 9.5e6) * 380.0 * time_noise

                            # Power draw components
                            idle_w = session["idle_w"] + np.random.normal(0, 0.25)
                            idle_w = max(4.5, idle_w)

                            # Dynamic power: higher for Merge (memory bus) and Bubble (branch mispredictions & pipe stalls)
                            dyn_factor = (spec["base_c_alu"] * 6.5 + spec["base_c_mem"] * 7.2)
                            dyn_power_w = dyn_factor * (base_freq / 3800.0)**2 * np.random.normal(1.0, 0.03)

                            # OS background spike injection
                            is_spike = False
                            if is_os_spike_day and np.random.rand() < 0.22:
                                is_spike = True
                                dyn_power_w += np.random.uniform(7.5, 12.0)
                                exec_time_ms *= np.random.uniform(1.20, 1.40)

                            pkg_power_w = idle_w + dyn_power_w

                            # Package temperature: ambient + thermal drift + power contribution
                            pkg_temp_c = (
                                session["ambient_c"]
                                + thermal_drift_c
                                + (pkg_power_w / 45.0) * 32.0
                                + np.random.normal(0, 0.8)
                            )
                            if is_spike:
                                pkg_temp_c += np.random.uniform(4.0, 7.5)

                            # CPU utilization
                            cpu_util_pct = min(100.0, max(85.0, 94.5 + np.random.normal(0, 2.5)))

                            # Energy calculations
                            exec_time_s = exec_time_ms / 1000.0
                            total_energy_j = pkg_power_w * exec_time_s
                            total_energy_mj = total_energy_j * 1000.0
                            energy_per_op_uj = (total_energy_j * 1e6) / max(1, total_ops)
                            energy_per_op_nj = energy_per_op_uj * 1000.0

                            # Advance timestamp by execution time + 2 second inter-test cooldown
                            current_time += datetime.timedelta(milliseconds=int(exec_time_ms + 2000))

                            row = {
                                "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%S"),
                                "day_index": day,
                                "session_id": session_id,
                                "session_period": session["name"],
                                "algorithm": algo_name,
                                "implementation_variant": spec["variant"],
                                "complexity_class": spec["complexity_class"],
                                "input_size": size,
                                "data_distribution": dist,
                                "operations_count": total_ops,
                                "execution_time_ms": round(exec_time_ms, 3),
                                "cpu_pkg_power_w": round(pkg_power_w, 3),
                                "idle_baseline_power_w": round(idle_w, 3),
                                "dynamic_power_w": round(dyn_power_w, 3),
                                "total_energy_j": round(total_energy_j, 6),
                                "total_energy_mj": round(total_energy_mj, 3),
                                "energy_per_op_uj": round(energy_per_op_uj, 4),
                                "energy_per_op_nj": round(energy_per_op_nj, 2),
                                "cpu_freq_mhz": round(base_freq, 1),
                                "cpu_util_pct": round(cpu_util_pct, 1),
                                "pkg_temp_c": round(pkg_temp_c, 1),
                                "sensor_source": "Intel-RAPL-Hardware",
                            }
                            rows.append(row)

    df = pd.DataFrame(rows)

    # -------------------------------------------------------------
    # Inject Sensor Artifacts & Noise for realistic raw dataset
    # -------------------------------------------------------------
    # 1. Missing / NaN values (~1.2% in cpu_pkg_power_w and pkg_temp_c)
    n_missing = int(len(df) * 0.012)
    missing_indices_power = np.random.choice(df.index, size=n_missing, replace=False)
    df.loc[missing_indices_power, "cpu_pkg_power_w"] = np.nan

    missing_indices_temp = np.random.choice(df.index, size=n_missing, replace=False)
    df.loc[missing_indices_temp, "pkg_temp_c"] = np.nan

    # 2. Duplicate timestamps (~0.5% duplicate records due to sensor polling retry)
    n_dups = int(len(df) * 0.005)
    dup_indices = np.random.choice(df.index, size=n_dups, replace=False)
    dup_rows = df.loc[dup_indices].copy()
    df = pd.concat([df, dup_rows], ignore_index=True)

    # Sort chronologically by timestamp
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[+] Raw 21-day telemetry dataset generated: {output_path} ({len(df)} rows)")
    return df


if __name__ == "__main__":
    default_out = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "Deliverable_2_Datasets",
        "raw_rapl_benchmark_21days.csv",
    )
    generate_21day_raw_dataset(default_out)
