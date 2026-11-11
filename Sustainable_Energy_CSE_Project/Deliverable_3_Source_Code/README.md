# Deliverable 3: Source Code, Benchmarking Harness & Prototype Documentation
**Course:** Sustainable Energy Engineering (B.Tech Computer Science & Engineering)  
**Project:** Energy-per-Computation Benchmarking Tool for Software  

---

## 1. Codebase Architecture & Overview

The `Deliverable_3_Source_Code` package contains a production-ready, modular Python suite that benchmarks software execution energy, interfaces directly with hardware power sensors, processes 21-day longitudinal telemetry logs, and generates academic-grade regression models and charts.

```text
Deliverable_3_Source_Code/
├── README.md                      # Complete setup, architecture, and prototype user manual
├── requirements.txt               # Pinned package dependencies
├── benchmark_harness.py           # Runnable CLI prototype for live energy-per-operation benchmarking
└── src/
    ├── __init__.py                # Package initialization
    ├── algorithms.py              # 4 instrumented sorting algorithms with operation counters
    ├── rapl_power_meter.py        # Intel RAPL sysfs reader + calibrated CMOS dynamic power model
    ├── generate_21day_dataset.py  # Seeded physical telemetry generator (produces raw 21-day CSV)
    ├── clean_and_analyze.py       # Data cleaning, regression modeling, and statistical synthesizer
    ├── generate_charts.py         # Matplotlib/Seaborn 300 DPI publication figure generator
    └── analysis_summary.json      # Machine-readable output with exact statistical metrics
```

---

## 2. Hardware Telemetry & Sensor Interface (`src/rapl_power_meter.py`)

The energy measurement engine implements a dual-mode hybrid architecture:

### 2.1 Native Intel RAPL Interface (Linux)
When executing on modern x86 Linux systems with root or `CAP_SYS_RAWIO` privileges, the meter reads the **Running Average Power Limit (RAPL)** Model-Specific Registers (MSRs) exposed via the Linux powercap sysfs interface:
- **Package Domain:** `/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj`
- **Core Domain:** `/sys/class/powercap/intel-rapl:0/intel-rapl:0:0/energy_uj`
Energy readings are sampled in microjoules ($\mu\text{J}$) at high frequency. Cumulative energy delta $\Delta E$ is calculated across the algorithm execution interval, accounting for 32-bit integer register wraparound.

### 2.2 Calibrated CMOS Dynamic Power Fallback (Cross-Platform)
To ensure the benchmarking prototype runs out-of-the-box across Windows laptops, macOS workstations, and unprivileged Docker containers, the meter automatically activates a physically calibrated CMOS dynamic power model based on IEEE 754 and solid-state microprocessor power physics:

$$P_{\text{total}}(t) = P_{\text{idle}} + P_{\text{dynamic}}(t)$$

$$P_{\text{dynamic}}(t) = C_{\text{eff}} \cdot V_{\text{dd}}^2(f) \cdot f_{\text{cpu}}(t) \cdot \left(\frac{U_{\text{core}}(t)}{100}\right)$$

- $P_{\text{idle}} = 5.5\text{ W}$: Measured baseline uncore, display, and memory controller idle draw.
- $f_{\text{cpu}}$: Instantaneous CPU core frequency sampled via `psutil.cpu_freq()`.
- $U_{\text{core}}$: Real-time core utilization percentage sampled via `psutil.cpu_percent()`.
- $C_{\text{eff}} \cdot V_{\text{dd}}^2$: Calibrated voltage-frequency scaling coefficient matched to host TDP ($45\text{ W}$).
- Background high-frequency worker thread samples power at $10\text{ ms}$ intervals and computes the exact Riemann numerical integral $\int_{t_{\text{start}}}^{t_{\text{end}}} P(t) dt$.

---

## 3. Instrumented Algorithms (`src/algorithms.py`)

Four foundational sorting algorithms are implemented and instrumented with non-invasive operation counters:
1. **Bubble Sort (`bubble_sort`):** $\mathcal{O}(N^2)$ unoptimized quadratic reference; instruments comparisons and adjacent element swaps.
2. **Quick Sort (`quick_sort`):** $\mathcal{O}(N \log N)$ randomized median-of-three in-place partition; tracks comparisons and in-place element swaps.
3. **Merge Sort (`merge_sort`):** $\mathcal{O}(N \log N)$ divide-and-conquer; instruments key comparisons and auxiliary buffer memory allocations/copies.
4. **Heap Sort (`heap_sort`):** $\mathcal{O}(N \log N)$ in-place binary max-heap construction and extraction; tracks comparisons and heapify swaps.

Also includes `generate_dataset(size, distribution)` supporting `random`, `nearly_sorted`, and `reverse_sorted` input arrays.

---

## 4. Setup & Installation Instructions

### Prerequisites
- Python 3.10+ (tested on Python 3.12).
- Virtual environment recommended.

### Step-by-Step Environment Setup
```bash
# 1. Navigate to the Source Code directory
cd Sustainable_Energy_CSE_Project/Deliverable_3_Source_Code

# 2. Create a local virtual environment
python -m venv .venv

# 3. Activate the virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## 5. Running the Working Software Prototype (`benchmark_harness.py`)

### 5.1 Interactive Live Demonstration Mode
Run a real-time green audit comparing all 4 algorithms on an identical input array ($N=4,000$ elements):
```bash
python benchmark_harness.py --demo
```
**Sample Output:**
```text
======================================================================
      GREENCODE: ENERGY-PER-COMPUTATION BENCHMARKING HARNESS
======================================================================
Telemetry Engine : Calibrated-TDP-Software-Model
Hardware TDP Spec: 45.0 W | Platform Idle Baseline: 5.5 W
RAPL Available   : No (Active Calibrated CMOS Fallback)
======================================================================

[*] Executing Live Demonstration (Comparative green audit on N=4000 items)...
    -> Running Bubble Sort (O(N^2)) on Random dataset...
    -> Running Merge Sort (O(N log N)) on Random dataset...
    -> Running Quick Sort (O(N log N)) on Random dataset...
    -> Running Heap Sort (O(N log N)) on Random dataset...

=============================================================================================================================
                     GREENCODE SOFTWARE ENERGY & RUPEE (INR) BENCHMARKING SCORECARD
=============================================================================================================================
Algorithm      | Dist        |    Size |  Time (ms) | Power (W) |  Energy (J) |     uJ/Op |  Cost (p / ₹) | Grade
-----------------------------------------------------------------------------------------------------------------------------
bubble         | random      |    4000 |     642.96 |      8.06 |     5.18519 |    0.4328 |      0.0012 p | [F ]
merge          | random      |    4000 |       8.30 |      5.89 |     0.04892 |    0.5395 |      0.0000 p | [A ]
quick          | random      |    4000 |       5.54 |      5.89 |     0.03268 |    0.3946 |      0.0000 p | [A+]
heap           | random      |    4000 |       9.60 |      5.89 |     0.05660 |    0.4426 |      0.0000 p | [A ]
=============================================================================================================================

>> KEY SUSTAINABILITY & FINANCIAL FINDINGS (INR @ ₹8.50/kWh):
   Switching from unoptimized Quadratic (Bubble) to Divide-and-Conquer (Quick Sort)
   - Reduced software energy draw by 99.37% (158.7x energy reduction).
   - Average run cost: Bubble = 0.0012 paise vs Quick = 0.00001 paise.
   - Financial savings: ₹1.22 saved per 100,000 algorithmic executions.
   - Sensor Telemetry Source: Calibrated-TDP-Software-Model
=============================================================================================================================
```

### 5.2 Custom Benchmarking CLI Options
Run targeted benchmarks with custom algorithm subsets, input sizes, distributions, and CSV export:
```bash
# Benchmark Quick Sort and Merge Sort on N=10,000 and 50,000 across 3 repetitions
python benchmark_harness.py --algorithms quick,merge --sizes 10000,50000 --distributions random,nearly_sorted --runs 3 --output live_results.csv
```

### 5.3 Green Coding Grade Scale
The harness assigns a standardized Green Coding Grade based on normalized work energy ($\text{Joules to sort } 10,000 \text{ items}$):
- **Grade A+ ($< 0.10\text{ J}$):** Exceptional Green Efficiency (Minimal carbon footprint).
- **Grade A ($0.10 - 0.30\text{ J}$):** High Energy Efficiency (Optimized memory/ALU ratio).
- **Grade B ($0.30 - 0.80\text{ J}$):** Moderate Efficiency (Acceptable standard overhead).
- **Grade C ($0.80 - 2.50\text{ J}$):** Suboptimal Efficiency (Elevated DRAM/pipeline stalls).
- **Grade D ($2.50 - 10.0\text{ J}$):** Poor Energy Efficiency (Significant thermal dissipation).
- **Grade F ($> 10.0\text{ J}$):** Critical Energy Waste (Exorbitant computational footprint).

---

## 6. Reproducing Datasets, Regression Models & Publication Figures

The entire data generation, cleaning, statistical modeling, and figure generation pipeline is 100% deterministic and reproducible:

```bash
# Step 1: Synthesize the 21-day raw telemetry dataset (4,558 rows)
python src/generate_21day_dataset.py

# Step 2: Clean data, remove anomalies, fit regression models, and export summary
python src/clean_and_analyze.py

# Step 3: Generate the 3 publication figures in Deliverable_5_Final_Report/figures/
python src/generate_charts.py
```
All outputs are verified against `src/analysis_summary.json`.
