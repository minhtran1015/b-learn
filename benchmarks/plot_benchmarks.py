#!/usr/bin/env python3
"""Benchmark visualization script.

Loads the raw baseline and Comet metrics from the results subdirectories,
plots three publication-ready charts (Ingestion Ingestion Performance, FastAPI Gateway
Latency Curves, and FinOps/GreenOps Savings), and saves them to a dedicated folder.
"""

import csv
import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Style setup matching chart_style_ref.py style
sns.set_theme(style="whitegrid", font_scale=1.2, rc={"axes.labelsize": "medium"})

def fix_spines(ax):
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor('black')
        spine.set_linewidth(1.0)

# Colors matching the palette in chart_style_ref.py
C_BASE  = '#afd6d7'  # Teal for Baseline
C_COMET = '#ffb482'  # Orange for Comet
C_GREEN = '#8de5a1'  # Green for GreenOps Sleep
C_PUR   = '#d0bbff'  # Purple accent

# Paths
HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HERE, 'results')
PLOTS_DIR = os.path.join(HERE, 'plots')
os.makedirs(PLOTS_DIR, exist_ok=True)

# 1. Load Throughput and CPU Data
with open(os.path.join(RESULTS_DIR, 'baseline', 'throughput_benchmark.json')) as f:
    base_throughput = json.load(f)
with open(os.path.join(RESULTS_DIR, 'comet', 'throughput_benchmark_comet.json')) as f:
    comet_throughput = json.load(f)

# 2. Load Latency CSVs
base_latency = []
with open(os.path.join(RESULTS_DIR, 'baseline', 'latency_stress_test.csv')) as f:
    reader = csv.DictReader(f)
    for row in reader:
        base_latency.append({k: float(v) for k, v in row.items()})

comet_latency = []
with open(os.path.join(RESULTS_DIR, 'comet', 'latency_stress_test_comet.csv')) as f:
    reader = csv.DictReader(f)
    for row in reader:
        comet_latency.append({k: float(v) for k, v in row.items()})

# 3. Load GreenOps CSVs
greenops_data = []
with open(os.path.join(RESULTS_DIR, 'comet', 'greenops_metrics_comet.csv')) as f:
    reader = csv.DictReader(f)
    for row in reader:
        greenops_data.append({
            'mode': row['operational_mode'],
            'ram': float(row['ram_consumption_gib']),
            'cost': float(row['monthly_cost_usd']),
            'carbon': float(row['carbon_footprint_percentage'])
        })

# ==============================================================================
# Plot 1: Ingestion Throughput and CPU Utilization
# ==============================================================================
print("Generating Plot 1: Ingestion Performance...")
fig, ax1 = plt.subplots(figsize=(8.5, 6))
ax2 = ax1.twinx()

labels = ['Baseline (JVM)', 'Apache Comet\n(Native Vectorized)']
cpu_values = [base_throughput['peak_spark_cpu_cores_utilized'], comet_throughput['peak_spark_cpu_cores_utilized']]
throughput_values = [base_throughput['average_throughput_events_per_sec'], comet_throughput['average_throughput_events_per_sec']]

width = 0.35
x = np.arange(len(labels))

rects1 = ax1.bar(x - width/2, cpu_values, width, label='Peak CPU (Cores)', color=C_BASE, edgecolor='black', linewidth=0.8, zorder=3)
rects2 = ax2.bar(x + width/2, throughput_values, width, label='Throughput (events/s)', color=C_COMET, edgecolor='black', linewidth=0.8, zorder=3)

ax1.set_ylabel('Peak Spark Pod CPU Utilization (Cores)', color='teal', fontweight='bold', fontsize=12)
ax1.tick_params(axis='y', labelcolor='teal')
ax1.set_ylim(0, max(cpu_values) * 1.3)

ax2.set_ylabel('Average Ingestion Throughput (events/s)', color='#cc6622', fontweight='bold', fontsize=12)
ax2.tick_params(axis='y', labelcolor='#cc6622')
ax2.set_ylim(0, max(throughput_values) * 1.3)

ax1.set_xticks(x)
ax1.set_xticklabels(labels, fontweight='bold', fontsize=11)
ax1.set_title('Spark Structured Streaming: Ingestion Performance & CPU Efficiency', fontweight='bold', pad=15, fontsize=13)

# Add values above bars
for rect in rects1:
    height = rect.get_height()
    ax1.annotate(f'{height:.3f} Cores',
                 xy=(rect.get_x() + rect.get_width() / 2, height),
                 xytext=(0, 4),
                 textcoords="offset points",
                 ha='center', va='bottom', fontweight='bold', color='teal', fontsize=10)

for rect in rects2:
    height = rect.get_height()
    ax2.annotate(f'{height:.1f} ev/s',
                 xy=(rect.get_x() + rect.get_width() / 2, height),
                 xytext=(0, 4),
                 textcoords="offset points",
                 ha='center', va='bottom', fontweight='bold', color='#cc6622', fontsize=10)

# Combine legends
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=11)

fix_spines(ax1)
ax1.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
out_ingest = os.path.join(PLOTS_DIR, 'ingestion_performance.png')
fig.savefig(out_ingest, dpi=600, bbox_inches='tight')
plt.close()
print(f"  Saved → {out_ingest}")


# ==============================================================================
# Plot 2: API Gateway Latency Curves
# ==============================================================================
print("Generating Plot 2: Gateway Latency Scaling...")
fig, ax = plt.subplots(figsize=(9, 6.5))

qps = [row['concurrent_requests_per_sec'] for row in base_latency]
base_p50 = [row['p50_latency_ms'] for row in base_latency]
base_p95 = [row['p95_latency_ms'] for row in base_latency]
base_p99 = [row['p99_latency_ms'] for row in base_latency]

comet_p50 = [row['p50_latency_ms'] for row in comet_latency]
comet_p95 = [row['p95_latency_ms'] for row in comet_latency]
comet_p99 = [row['p99_latency_ms'] for row in comet_latency]

# Plot lines
ax.plot(qps, base_p50, marker='o', linestyle='-', color='#afd6d7', linewidth=2.5, label='Baseline p50')
ax.plot(qps, base_p95, marker='s', linestyle='-', color='#8de5a1', linewidth=2.5, label='Baseline p95')
ax.plot(qps, base_p99, marker='^', linestyle='-', color='#d0bbff', linewidth=2.5, label='Baseline p99')

ax.plot(qps, comet_p50, marker='o', linestyle='--', color='#ffb482', linewidth=2.5, label='Comet p50')
ax.plot(qps, comet_p95, marker='s', linestyle='--', color='#ff8c42', linewidth=2.5, label='Comet p95')
ax.plot(qps, comet_p99, marker='^', linestyle='--', color='#cc6622', linewidth=2.5, label='Comet p99')

ax.set_xscale('log')
ax.set_xticks(qps)
ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

ax.set_xlabel('Concurrent Load (QPS) - Log Scale', fontweight='bold', fontsize=12)
ax.set_ylabel('API Gateway Response Latency (ms)', fontweight='bold', fontsize=12)
ax.set_title('FastAPI Serving Gateway: Latency Scaling under Stress', fontweight='bold', pad=15, fontsize=13)
ax.set_ylim(0, max(max(base_p99), max(comet_p99)) * 1.25)
ax.legend(loc='upper left', ncol=2, frameon=True, facecolor='white', edgecolor='black', fontsize=10.5)

fix_spines(ax)
ax.grid(True, which="both", linestyle='--', alpha=0.5)

plt.tight_layout()
out_latency = os.path.join(PLOTS_DIR, 'gateway_latency_scaling.png')
fig.savefig(out_latency, dpi=600, bbox_inches='tight')
plt.close()
print(f"  Saved → {out_latency}")


# ==============================================================================
# Plot 3: GreenOps / FinOps Resource Savings
# ==============================================================================
print("Generating Plot 3: GreenOps Savings...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.5))

modes = ['Baseline\n(24/7 Run)', 'FinOps / GreenOps\n(Sleep Schedule)']
cost_vals = [row['cost'] for row in greenops_data]
ram_vals = [row['ram'] for row in greenops_data]

# Bar for cost
bars1 = ax1.bar(modes, cost_vals, color=[C_COMET, C_GREEN], edgecolor='black', linewidth=0.8, width=0.45, zorder=3)
ax1.set_ylabel('Projected Monthly Azure Cost (USD)', fontweight='bold', fontsize=12)
ax1.set_title('(a) Monthly Cloud Resource Cost Comparison', fontweight='bold', fontsize=12)
ax1.set_ylim(0, max(cost_vals) * 1.3)
fix_spines(ax1)
ax1.grid(True, linestyle='--', alpha=0.5)

for bar in bars1:
    height = bar.get_height()
    ax1.annotate(f'${height:.2f}\n/month',
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 4),
                 textcoords="offset points",
                 ha='center', va='bottom', fontweight='bold', fontsize=11)

# Bar for RAM
bars2 = ax2.bar(modes, ram_vals, color=[C_COMET, C_GREEN], edgecolor='black', linewidth=0.8, width=0.45, zorder=3)
ax2.set_ylabel('RAM Consumption (GiB)', fontweight='bold', fontsize=12)
ax2.set_title('(b) Active RAM Footprint Comparison', fontweight='bold', fontsize=12)
ax2.set_ylim(0, max(ram_vals) * 1.3)
fix_spines(ax2)
ax2.grid(True, linestyle='--', alpha=0.5)

for bar in bars2:
    height = bar.get_height()
    ax2.annotate(f'{height:.2f} GiB',
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 4),
                 textcoords="offset points",
                 ha='center', va='bottom', fontweight='bold', fontsize=11)

fig.suptitle('FinOps & GreenOps Architectural Sleep Schedule Optimization Results', fontweight='bold', fontsize=14, y=1.02)
plt.tight_layout()
out_greenops = os.path.join(PLOTS_DIR, 'greenops_savings.png')
fig.savefig(out_greenops, dpi=600, bbox_inches='tight')
plt.close()
print(f"  Saved → {out_greenops}")

print("\nAll 3 charts successfully generated and saved to benchmarks/plots/.")
