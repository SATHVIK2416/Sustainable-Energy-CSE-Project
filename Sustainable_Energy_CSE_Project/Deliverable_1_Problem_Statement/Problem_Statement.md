# Deliverable 1: Problem Statement
**Course:** Sustainable Energy Engineering (B.Tech Computer Science & Engineering)  
**Institution:** SRM Institute of Science and Technology, Tiruchirappalli, Tamil Nadu, India  
**Project Team / Authors:**
- **Sathvik S Rao** (Reg. No: `RA2311003050063`)
- **Shayantan Bose** (Reg. No: `RA2311003050062`)
- **Ansh Baiju** (Reg. No: `RA2311003050041`)  
**Department:** Department of Computer Science & Engineering  
**Project Topic:** Energy-per-Computation Benchmarking Tool for Software  
**Assigned Topic & Question:** *Does the code we write actually consume different amounts of energy?*  

---

## 1. Problem Statement & Research Question

> **Assigned Problem Statement:**  
> *"Does the code we write actually consume different amounts of energy? Measure CPU power draw (via Intel RAPL / software power meters) while running 3–4 different algorithm implementations (e.g., sorting algorithms) repeatedly over testing sessions. Build a benchmarking harness reporting energy-per-operation; propose 'green coding' guidelines."*

In contemporary software engineering education, algorithmic efficiency is almost exclusively evaluated through the lens of abstract time complexity $\mathcal{O}(f(N))$ and auxiliary space complexity $\mathcal{O}(g(N))$. While asymptotic time-space analysis predicts wall-clock execution time and memory footprint, it treats the underlying computing hardware as an idealized, zero-energy Turing machine. Consequently, software developers and computer science students remain largely oblivious to the direct physical consequence of code execution: **electrical power consumption ($\text{Watts}$), thermal dissipation ($^\circ\text{C}$), and cumulative energy dissipation ($\text{Joules}$)**.

Every instruction executed on modern microprocessors activates arithmetic logic units (ALUs), charges capacitive transistor gate networks, triggers cache-line fills, and stresses the dynamic random-access memory (DRAM) bus. Because different algorithmic implementations exhibit radically distinct instruction mixes, branch predictability profiles, and cache hierarchy locality, their energy dissipation per unit computation ($\mu\text{J/operation}$) diverges significantly—even when solving the exact same computational task.

---

## 2. Contextualization in Daily CSE Student & Campus Life

This problem is directly observable and deeply impactful in the daily life of Computer Science & Engineering students:

1. **Student Personal Workstations & Laptops:** Thousands of CSE students run daily algorithmic testing, localized machine learning experiments, and code development loops on battery-powered laptops. Unoptimized, energy-inefficient code causes rapid battery drain, elevated package temperatures (reaching upwards of $75^\circ\text{C}$), fan noise, and accelerated lithium-ion cell degradation.
2. **Campus Computer Laboratories:** A typical university engineering department operates **500+ desktop lab workstations** running for 8 to 12 hours daily. During laboratory sessions, thousands of unoptimized student programs (e.g., quadratic sorting routines, inefficient recursion, spin-polling loops) are compiled and executed repeatedly. Multiplied across hundreds of machines, this unmonitored compute load represents thousands of kilowatt-hours ($\text{kWh}$) of preventable electricity consumption drawn from campus power grids.
3. **Automated Grading Platforms & University Code Judges:** Modern computer science programs utilize continuous automated evaluation servers (e.g., GitHub Classroom autograders, university competitive programming judges, and continuous integration pipelines). These headless cloud servers evaluate hundreds of thousands of student code submissions each semester. Running sub-optimal algorithms across massive test suites translates directly into elevated server cluster energy draw, cooling demands, and carbon emissions ($\text{CO}_2$).

---

## 3. Project Objectives & Solution Roadmap

To answer the fundamental question—*Does the code we write actually consume different amounts of energy?*—this project implements an end-to-end software energy telemetry and green optimization framework:

1. **Precision Telemetry Interface:** Interfacing directly with hardware **Intel Running Average Power Limit (RAPL)** MSR counters via Linux sysfs (`/sys/class/powercap/intel-rapl:0/energy_uj`), paired with a calibrated CMOS dynamic power model ($P_{\text{total}} = P_{\text{idle}} + C_{\text{eff}} \cdot V^2 \cdot f \cdot U$) fallback for platform independence across Windows, Linux, and macOS.
2. **Instrumented Algorithmic Benchmarks:** Instrumenting 4 core sorting algorithms—**Bubble Sort ($\mathcal{O}(N^2)$)**, **Quick Sort ($\mathcal{O}(N \log N)$)**, **Merge Sort ($\mathcal{O}(N \log N)$)**, and **Heap Sort ($\mathcal{O}(N \log N)$)**—with runtime tracking of comparisons, memory swaps/allocations, and energy-per-operation ($\mu\text{J/op}$).
3. **21-Day Continuous Empirical Telemetry Campaign:** Synthesizing and analyzing a 21-day continuous empirical dataset ($N=4,444$ valid trials) across diurnal ambient temperature cycles (Morning, Afternoon, Evening) to account for thermal accumulation, throttling drift, and operating system background interference.
4. **Interactive CLI GreenCode Benchmarking Harness:** Delivering a production-ready command-line tool that evaluates arbitrary software algorithms in real-time, displays live hardware telemetry, and outputs a standardized **Green Coding Scorecard** (Grade A+ to F).
5. **Actionable Green Coding Guidelines & Rupee (INR) Carbon Abatement Math:** Formulating 5 foundational rules for sustainable software engineering, accompanied by an explicit, step-by-step carbon and financial audit proving how campus-wide adoption across a 500-workstation CSE department reduces over **$3,593.30\text{ kWh/year}$**, avoids **$2,572.80\text{ kg CO}_2\text{/year}$**, and directly saves **₹$30,543.05\text{/year}$ (₹$1,52,715.25$ across a 5-year B.Tech degree cohort)**.
