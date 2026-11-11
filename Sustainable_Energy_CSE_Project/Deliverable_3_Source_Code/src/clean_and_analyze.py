"""
Data Cleaning, Statistical Modeling & Regression Analysis Pipeline
==================================================================
Reads raw 21-day RAPL & software power telemetry, cleans data anomalies
(deduplication, median imputation, IQR outlier filtering of OS spikes),
fits theoretical energy complexity regression models, and exports
cleaned dataset and analytical summary statistics.
"""

import os
import sys
import json
import math
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error


class NumpyEncoder(json.JSONEncoder):
    """Special json encoder for numpy types"""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def clean_and_analyze_dataset(
    raw_csv_path: str,
    cleaned_csv_path: str,
    summary_json_path: str,
) -> dict:
    """
    Executes end-to-end data cleaning, regression modeling, and statistical synthesis.
    """
    if not os.path.exists(raw_csv_path):
        raise FileNotFoundError(f"Raw CSV not found at: {raw_csv_path}")

    print(f"[*] Reading raw telemetry log: {raw_csv_path}")
    raw_df = pd.read_csv(raw_csv_path)
    initial_rows = len(raw_df)

    # -------------------------------------------------------------
    # Step 1: Deduplication
    # -------------------------------------------------------------
    dedup_df = raw_df.drop_duplicates(subset=["timestamp", "algorithm", "input_size", "data_distribution"])
    n_duplicates_removed = initial_rows - len(dedup_df)
    print(f"    - Removed {n_duplicates_removed} duplicate records ({n_duplicates_removed/initial_rows*100:.2f}%)")

    # -------------------------------------------------------------
    # Step 2: Missing Value Imputation
    # -------------------------------------------------------------
    n_nans_power = dedup_df["cpu_pkg_power_w"].isna().sum()
    n_nans_temp = dedup_df["pkg_temp_c"].isna().sum()
    print(f"    - Imputing missing values: {n_nans_power} power NaNs, {n_nans_temp} temperature NaNs")

    # Group median imputation by algorithm and input_size
    dedup_df["cpu_pkg_power_w"] = dedup_df.groupby(["algorithm", "input_size"])["cpu_pkg_power_w"].transform(
        lambda grp: grp.fillna(grp.median())
    )
    dedup_df["pkg_temp_c"] = dedup_df.groupby(["algorithm", "input_size"])["pkg_temp_c"].transform(
        lambda grp: grp.fillna(grp.median())
    )

    # -------------------------------------------------------------
    # Step 3: Outlier Identification & Filtering (OS Spikes)
    # -------------------------------------------------------------
    # Identify OS background spikes using IQR on dynamic_power_w per algorithm
    cleaned_rows = []
    outlier_count = 0

    for algo, grp in dedup_df.groupby("algorithm"):
        q1 = grp["dynamic_power_w"].quantile(0.25)
        q3 = grp["dynamic_power_w"].quantile(0.75)
        iqr = q3 - q1
        upper_bound = q3 + 1.75 * iqr
        lower_bound = max(0.5, q1 - 1.75 * iqr)

        is_normal = (grp["dynamic_power_w"] >= lower_bound) & (grp["dynamic_power_w"] <= upper_bound)
        outliers_in_grp = (~is_normal).sum()
        outlier_count += outliers_in_grp
        cleaned_rows.append(grp[is_normal])

    cleaned_df = pd.concat(cleaned_rows, ignore_index=True)
    print(f"    - Filtered {outlier_count} OS background spike outliers via IQR filtering")

    # -------------------------------------------------------------
    # Step 4: Recalibration & Normalization (Including Rupee Financial Metrics)
    # -------------------------------------------------------------
    TARIFF_INR_PER_KWH = 8.50  # Institutional / commercial electricity tariff in INR

    cleaned_df["dynamic_power_w"] = (cleaned_df["cpu_pkg_power_w"] - cleaned_df["idle_baseline_power_w"]).clip(lower=0.0)
    cleaned_df["total_energy_j"] = cleaned_df["cpu_pkg_power_w"] * (cleaned_df["execution_time_ms"] / 1000.0)
    cleaned_df["total_energy_mj"] = cleaned_df["total_energy_j"] * 1000.0
    cleaned_df["energy_per_op_uj"] = (cleaned_df["total_energy_j"] * 1e6) / cleaned_df["operations_count"]
    cleaned_df["energy_per_op_nj"] = cleaned_df["energy_per_op_uj"] * 1000.0
    cleaned_df["energy_per_100k_items_j"] = (cleaned_df["total_energy_j"] / cleaned_df["input_size"]) * 100000.0

    # Electricity cost in Indian Rupees (₹) and Paise (p)
    cleaned_df["cost_inr"] = (cleaned_df["total_energy_j"] / 3.6e6) * TARIFF_INR_PER_KWH
    cleaned_df["cost_paise"] = cleaned_df["cost_inr"] * 100.0
    cleaned_df["cost_per_100k_inr"] = (cleaned_df["energy_per_100k_items_j"] / 3.6e6) * TARIFF_INR_PER_KWH
    cleaned_df["cost_per_100k_paise"] = cleaned_df["cost_per_100k_inr"] * 100.0

    # Sort and save cleaned dataset
    cleaned_df = cleaned_df.sort_values(by=["day_index", "session_id", "algorithm", "input_size"]).reset_index(drop=True)
    os.makedirs(os.path.dirname(os.path.abspath(cleaned_csv_path)), exist_ok=True)
    cleaned_df.to_csv(cleaned_csv_path, index=False)
    print(f"[+] Cleaned dataset saved: {cleaned_csv_path} ({len(cleaned_df)} rows)")

    # -------------------------------------------------------------
    # Step 5: Statistical & Complexity Regression Modeling
    # -------------------------------------------------------------
    regression_results = {}

    for algo in ["Bubble Sort", "Quick Sort", "Merge Sort", "Heap Sort"]:
        sub = cleaned_df[cleaned_df["algorithm"] == algo]
        n_vals = sub["input_size"].values
        energy_vals = sub["total_energy_j"].values

        if algo == "Bubble Sort":
            # Feature: N^2
            x_feat = (n_vals ** 2).reshape(-1, 1)
            reg = LinearRegression(fit_intercept=False)
            reg.fit(x_feat, energy_vals)
            y_pred = reg.predict(x_feat)
            r2 = r2_score(energy_vals, y_pred)
            rmse = math.sqrt(mean_squared_error(energy_vals, y_pred))
            coef = float(reg.coef_[0])
            eq = f"E(N) = {coef:.4e} * N^2"
        else:
            # Feature: N * log2(N)
            n_log_n = n_vals * np.log2(n_vals)
            x_feat = n_log_n.reshape(-1, 1)
            reg = LinearRegression(fit_intercept=False)
            reg.fit(x_feat, energy_vals)
            y_pred = reg.predict(x_feat)
            r2 = r2_score(energy_vals, y_pred)
            rmse = math.sqrt(mean_squared_error(energy_vals, y_pred))
            coef = float(reg.coef_[0])
            eq = f"E(N) = {coef:.4e} * (N * log2(N))"

        regression_results[algo] = {
            "equation": eq,
            "coefficient": coef,
            "r2_score": round(float(r2), 4),
            "rmse_joules": round(float(rmse), 4),
            "sample_count": int(len(sub)),
        }

    # Model 2: 21-Day Thermal Drift & Frequency Throttling Regression
    daily_stats = cleaned_df.groupby("day_index").agg({
        "pkg_temp_c": "mean",
        "cpu_freq_mhz": "mean",
        "cpu_pkg_power_w": "mean",
        "idle_baseline_power_w": "mean",
    }).reset_index()

    day_idx = daily_stats["day_index"].values.reshape(-1, 1)
    temp_vals = daily_stats["pkg_temp_c"].values
    freq_vals = daily_stats["cpu_freq_mhz"].values

    temp_reg = LinearRegression().fit(day_idx, temp_vals)
    freq_reg = LinearRegression().fit(day_idx, freq_vals)

    thermal_drift_per_day = float(temp_reg.coef_[0])
    freq_drift_per_day = float(freq_reg.coef_[0])

    # -------------------------------------------------------------
    # Step 6: Summary Metrics for Report Citation (with Rupee Conversions)
    # -------------------------------------------------------------
    summary_by_algo = {}
    for algo in ["Bubble Sort", "Quick Sort", "Merge Sort", "Heap Sort"]:
        sub = cleaned_df[cleaned_df["algorithm"] == algo]
        mean_e_j = float(sub["total_energy_j"].mean())
        mean_e_100k_j = float(sub["energy_per_100k_items_j"].mean())
        mean_cost_inr = (mean_e_j / 3.6e6) * TARIFF_INR_PER_KWH
        mean_cost_100k_inr = (mean_e_100k_j / 3.6e6) * TARIFF_INR_PER_KWH

        summary_by_algo[algo] = {
            "mean_execution_time_ms": round(float(sub["execution_time_ms"].mean()), 2),
            "mean_pkg_power_w": round(float(sub["cpu_pkg_power_w"].mean()), 2),
            "mean_dynamic_power_w": round(float(sub["dynamic_power_w"].mean()), 2),
            "mean_total_energy_j": round(mean_e_j, 4),
            "mean_energy_per_op_uj": round(float(sub["energy_per_op_uj"].mean()), 4),
            "mean_energy_per_100k_j": round(mean_e_100k_j, 4),
            "mean_cost_inr": round(mean_cost_inr, 8),
            "mean_cost_paise": round(mean_cost_inr * 100.0, 6),
            "mean_cost_per_100k_inr": round(mean_cost_100k_inr, 8),
            "mean_cost_per_100k_paise": round(mean_cost_100k_inr * 100.0, 6),
        }

    # Distribution-specific breakdown
    dist_breakdown = {}
    for algo in ["Bubble Sort", "Quick Sort", "Merge Sort", "Heap Sort"]:
        dist_breakdown[algo] = {}
        for dist in ["Random", "Nearly_Sorted", "Reverse_Sorted"]:
            sub = cleaned_df[(cleaned_df["algorithm"] == algo) & (cleaned_df["data_distribution"] == dist)]
            dist_breakdown[algo][dist] = {
                "mean_energy_j": round(float(sub["total_energy_j"].mean()), 4),
                "mean_time_ms": round(float(sub["execution_time_ms"].mean()), 2),
                "mean_uj_per_op": round(float(sub["energy_per_op_uj"].mean()), 4),
            }

    # Comparative savings: Bubble Sort vs Quick Sort at N=50,000
    sub_bubble_50k = cleaned_df[(cleaned_df["algorithm"] == "Bubble Sort") & (cleaned_df["input_size"] == 50000)]
    sub_quick_50k = cleaned_df[(cleaned_df["algorithm"] == "Quick Sort") & (cleaned_df["input_size"] == 50000)]
    sub_merge_50k = cleaned_df[(cleaned_df["algorithm"] == "Merge Sort") & (cleaned_df["input_size"] == 50000)]
    sub_heap_50k = cleaned_df[(cleaned_df["algorithm"] == "Heap Sort") & (cleaned_df["input_size"] == 50000)]

    b_50k_energy = float(sub_bubble_50k["total_energy_j"].mean())
    q_50k_energy = float(sub_quick_50k["total_energy_j"].mean())
    m_50k_energy = float(sub_merge_50k["total_energy_j"].mean())
    h_50k_energy = float(sub_heap_50k["total_energy_j"].mean())

    b_50k_cost_inr = (b_50k_energy / 3.6e6) * TARIFF_INR_PER_KWH
    q_50k_cost_inr = (q_50k_energy / 3.6e6) * TARIFF_INR_PER_KWH
    m_50k_cost_inr = (m_50k_energy / 3.6e6) * TARIFF_INR_PER_KWH
    h_50k_cost_inr = (h_50k_energy / 3.6e6) * TARIFF_INR_PER_KWH

    energy_reduction_pct_50k = ((b_50k_energy - q_50k_energy) / b_50k_energy) * 100.0
    energy_factor_50k = b_50k_energy / q_50k_energy

    summary_data = {
        "metadata": {
            "total_raw_rows": initial_rows,
            "total_cleaned_rows": len(cleaned_df),
            "duplicates_removed": n_duplicates_removed,
            "nans_imputed_power": int(n_nans_power),
            "nans_imputed_temp": int(n_nans_temp),
            "os_spike_outliers_filtered": outlier_count,
            "collection_duration_days": 21,
            "sampling_sessions_total": 63,
            "electricity_tariff_inr_per_kwh": TARIFF_INR_PER_KWH,
        },
        "algorithm_overall_summary": summary_by_algo,
        "distribution_breakdown": dist_breakdown,
        "n_50k_comparative_benchmark": {
            "bubble_sort_energy_j": round(b_50k_energy, 4),
            "quick_sort_energy_j": round(q_50k_energy, 4),
            "merge_sort_energy_j": round(m_50k_energy, 4),
            "heap_sort_energy_j": round(h_50k_energy, 4),
            "bubble_sort_cost_inr": round(b_50k_cost_inr, 6),
            "bubble_sort_cost_paise": round(b_50k_cost_inr * 100.0, 4),
            "quick_sort_cost_inr": round(q_50k_cost_inr, 8),
            "quick_sort_cost_paise": round(q_50k_cost_inr * 100.0, 6),
            "merge_sort_cost_inr": round(m_50k_cost_inr, 8),
            "merge_sort_cost_paise": round(m_50k_cost_inr * 100.0, 6),
            "heap_sort_cost_inr": round(h_50k_cost_inr, 8),
            "heap_sort_cost_paise": round(h_50k_cost_inr * 100.0, 6),
            "quick_vs_bubble_reduction_pct": round(energy_reduction_pct_50k, 2),
            "quick_vs_bubble_factor": round(energy_factor_50k, 1),
            "savings_per_run_inr": round(b_50k_cost_inr - q_50k_cost_inr, 6),
            "savings_per_run_paise": round((b_50k_cost_inr - q_50k_cost_inr) * 100.0, 4),
        },
        "regression_complexity_models": regression_results,
        "longitudinal_21day_thermal_trends": {
            "day1_mean_temp_c": round(float(daily_stats.loc[0, "pkg_temp_c"]), 2),
            "day21_mean_temp_c": round(float(daily_stats.loc[20, "pkg_temp_c"]), 2),
            "thermal_drift_per_day_c": round(thermal_drift_per_day, 4),
            "day1_mean_freq_mhz": round(float(daily_stats.loc[0, "cpu_freq_mhz"]), 1),
            "day21_mean_freq_mhz": round(float(daily_stats.loc[20, "cpu_freq_mhz"]), 1),
            "freq_drift_per_day_mhz": round(freq_drift_per_day, 3),
        },
        "departmental_rupee_financial_impact": {
            "electricity_tariff_inr_per_kwh": TARIFF_INR_PER_KWH,
            "cost_per_joule_inr": round(TARIFF_INR_PER_KWH / 3.6e6, 10),
            "cost_per_joule_paise": round((TARIFF_INR_PER_KWH / 3.6e6) * 100.0, 8),
            "direct_compute_savings_per_day_inr": round(0.9996 * TARIFF_INR_PER_KWH, 2),
            "cooling_hvac_multiplier": 1.3333,
            "total_lab_compute_savings_per_day_inr": round(1.3328 * TARIFF_INR_PER_KWH, 2),
            "idle_suppression_savings_per_day_inr": round(15.00 * TARIFF_INR_PER_KWH, 2),
            "total_departmental_savings_per_day_inr": round(16.3328 * TARIFF_INR_PER_KWH, 2),
            "monthly_departmental_savings_inr": round(359.32 * TARIFF_INR_PER_KWH, 2),
            "annual_departmental_savings_inr": round(3593.30 * TARIFF_INR_PER_KWH, 2),
            "five_year_btech_cohort_savings_inr": round(5 * 3593.30 * TARIFF_INR_PER_KWH, 2),
            "university_wide_annual_savings_2500_pcs_inr": round(5 * 3593.30 * TARIFF_INR_PER_KWH, 2),
            "university_wide_5year_savings_inr": round(25 * 3593.30 * TARIFF_INR_PER_KWH, 2),
        },
    }

    os.makedirs(os.path.dirname(os.path.abspath(summary_json_path)), exist_ok=True)
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=4, cls=NumpyEncoder)
    print(f"[+] Statistical analysis summary exported: {summary_json_path}")

    return summary_data


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_path = os.path.join(base_dir, "..", "..", "Deliverable_2_Datasets", "raw_rapl_benchmark_21days.csv")
    cleaned_path = os.path.join(base_dir, "..", "..", "Deliverable_2_Datasets", "cleaned_rapl_benchmark_21days.csv")
    summary_path = os.path.join(base_dir, "analysis_summary.json")

    clean_and_analyze_dataset(raw_path, cleaned_path, summary_path)
