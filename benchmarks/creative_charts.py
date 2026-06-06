"""
creative_charts.py — Comprehensive benchmark visualization for b-learn platform.
Generates publication-quality charts from all benchmark result datasets.

Output: benchmarks/plots/creative/
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.ticker import FuncFormatter
import warnings
warnings.filterwarnings("ignore")

# ─── Paths ───────────────────────────────────────────────────────────────────
RESULTS_ADV  = "benchmarks/results/advanced"
RESULTS_BASE = "benchmarks/results/baseline"
OUT_DIR      = "benchmarks/plots/creative"
os.makedirs(OUT_DIR, exist_ok=True)

# ─── Design tokens ────────────────────────────────────────────────────────────
DARK_BG   = "#0d1117"
PANEL_BG  = "#161b22"
GRID_COL  = "#21262d"
TEXT_COL  = "#e6edf3"
DIM_TEXT  = "#8b949e"

PALETTE = {
    "baseline":  "#58a6ff",   # blue
    "comet":     "#3fb950",   # green
    "fail":      "#f85149",   # red
    "success":   "#3fb950",   # green
    "withdrawn": "#d29922",   # amber
    "redis":     "#bc8cff",   # purple
    "local":     "#ff7b72",   # coral
    "accent1":   "#79c0ff",
    "accent2":   "#ffa657",
    "accent3":   "#7ee787",
}

GRADIENT_BLUE_GREEN = LinearSegmentedColormap.from_list(
    "bg", ["#58a6ff", "#3fb950"])
GRADIENT_RED_GREEN  = LinearSegmentedColormap.from_list(
    "rg", ["#f85149", "#3fb950"])

def apply_dark_style(fig, axes=None):
    """Apply consistent dark theme to figure/axes."""
    fig.patch.set_facecolor(DARK_BG)
    if axes is not None:
        ax_list = axes if hasattr(axes, "__iter__") else [axes]
        for ax in ax_list:
            ax.set_facecolor(PANEL_BG)
            ax.tick_params(colors=DIM_TEXT, which="both")
            ax.xaxis.label.set_color(TEXT_COL)
            ax.yaxis.label.set_color(TEXT_COL)
            ax.title.set_color(TEXT_COL)
            for spine in ax.spines.values():
                spine.set_edgecolor(GRID_COL)
            ax.grid(color=GRID_COL, linestyle="--", linewidth=0.6, alpha=0.7)
    return fig

def add_figure_label(ax, label, size=9):
    ax.text(0.01, 0.98, label, transform=ax.transAxes,
            fontsize=size, color=DIM_TEXT, va="top", ha="left",
            fontfamily="monospace")

# ─── Load data ────────────────────────────────────────────────────────────────
eval_df  = pd.read_csv(f"{RESULTS_ADV}/model_offline_evaluation.csv")
lat_df   = pd.read_csv(f"{RESULTS_ADV}/gateway_latency_scaling.csv")
ing_df   = pd.read_csv(f"{RESULTS_ADV}/ingestion_stress_grid.csv")
cache_df = pd.read_csv(f"{RESULTS_ADV}/storage_cache_comparison.csv")
drift_df = pd.read_csv(f"{RESULTS_ADV}/schema_drift_resilience.csv")
green_df = pd.read_csv(f"{RESULTS_BASE}/greenops_metrics.csv")
with open(f"{RESULTS_BASE}/throughput_benchmark.json") as f:
    tput_j = json.load(f)

# Clean column names
eval_df.columns  = eval_df.columns.str.strip()
lat_df.columns   = lat_df.columns.str.strip()
ing_df.columns   = ing_df.columns.str.strip()
cache_df.columns = cache_df.columns.str.strip()
drift_df.columns = drift_df.columns.str.strip()
green_df.columns = green_df.columns.str.strip()

print("✅  Data loaded successfully.")

# =============================================================================
# CHART 1 — Model Performance Dashboard (3×2 radar + bar grid)
# =============================================================================
def chart_model_performance():
    fig = plt.figure(figsize=(18, 12), facecolor=DARK_BG)
    fig.suptitle("LightGBM Model Performance — Baseline vs Optimized",
                 fontsize=20, color=TEXT_COL, fontweight="bold", y=0.98)

    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.38)

    classes = ["Fail", "Success", "Withdrawn"]
    metrics = ["Precision", "Recall", "F1-Score", "PR-AUC", "ROC-AUC"]

    base = eval_df[eval_df["Model"] == "Baseline"].set_index("Class")
    opt  = eval_df[eval_df["Model"] == "Optimized"].set_index("Class")

    class_colors = {"Fail": PALETTE["fail"], "Success": PALETTE["success"],
                    "Withdrawn": PALETTE["withdrawn"]}

    # ── A: Grouped bar — F1 Score per class ──────────────────────────────────
    ax_f1 = fig.add_subplot(gs[0, 0])
    x = np.arange(len(classes)); w = 0.35
    bars_b = ax_f1.bar(x - w/2, [base.loc[c, "F1-Score"] for c in classes],
                       w, label="Baseline", color=PALETTE["baseline"], alpha=0.85, zorder=3)
    bars_o = ax_f1.bar(x + w/2, [opt.loc[c, "F1-Score"] for c in classes],
                       w, label="Optimized", color=PALETTE["comet"], alpha=0.85, zorder=3)
    for bar in list(bars_b) + list(bars_o):
        ax_f1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                   f"{bar.get_height():.3f}", ha="center", va="bottom",
                   color=TEXT_COL, fontsize=7.5, fontweight="bold")
    ax_f1.set_xticks(x); ax_f1.set_xticklabels(classes)
    ax_f1.set_ylabel("F1-Score"); ax_f1.set_title("F1-Score by Class", color=TEXT_COL)
    ax_f1.set_ylim(0, 0.95); ax_f1.legend(fontsize=8, labelcolor=TEXT_COL,
                                            facecolor=PANEL_BG, edgecolor=GRID_COL)
    apply_dark_style(fig, ax_f1)
    add_figure_label(ax_f1, "A")

    # ── B: PR-AUC comparison ─────────────────────────────────────────────────
    ax_pr = fig.add_subplot(gs[0, 1])
    bars_b2 = ax_pr.bar(x - w/2, [base.loc[c, "PR-AUC"] for c in classes],
                        w, label="Baseline", color=PALETTE["baseline"], alpha=0.85, zorder=3)
    bars_o2 = ax_pr.bar(x + w/2, [opt.loc[c, "PR-AUC"] for c in classes],
                        w, label="Optimized", color=PALETTE["comet"], alpha=0.85, zorder=3)
    for bar in list(bars_b2) + list(bars_o2):
        ax_pr.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                   f"{bar.get_height():.3f}", ha="center", va="bottom",
                   color=TEXT_COL, fontsize=7.5, fontweight="bold")
    ax_pr.set_xticks(x); ax_pr.set_xticklabels(classes)
    ax_pr.set_ylabel("PR-AUC"); ax_pr.set_title("PR-AUC by Class", color=TEXT_COL)
    ax_pr.set_ylim(0, 1.0); ax_pr.legend(fontsize=8, labelcolor=TEXT_COL,
                                           facecolor=PANEL_BG, edgecolor=GRID_COL)
    apply_dark_style(fig, ax_pr)
    add_figure_label(ax_pr, "B")

    # ── C: ROC-AUC comparison ────────────────────────────────────────────────
    ax_roc = fig.add_subplot(gs[0, 2])
    bars_b3 = ax_roc.bar(x - w/2, [base.loc[c, "ROC-AUC"] for c in classes],
                         w, label="Baseline", color=PALETTE["baseline"], alpha=0.85, zorder=3)
    bars_o3 = ax_roc.bar(x + w/2, [opt.loc[c, "ROC-AUC"] for c in classes],
                         w, label="Optimized", color=PALETTE["comet"], alpha=0.85, zorder=3)
    for bar in list(bars_b3) + list(bars_o3):
        ax_roc.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
                    f"{bar.get_height():.3f}", ha="center", va="bottom",
                    color=TEXT_COL, fontsize=7.5, fontweight="bold")
    ax_roc.set_xticks(x); ax_roc.set_xticklabels(classes)
    ax_roc.set_ylabel("ROC-AUC"); ax_roc.set_title("ROC-AUC by Class", color=TEXT_COL)
    ax_roc.set_ylim(0.5, 1.0); ax_roc.legend(fontsize=8, labelcolor=TEXT_COL,
                                               facecolor=PANEL_BG, edgecolor=GRID_COL)
    apply_dark_style(fig, ax_roc)
    add_figure_label(ax_roc, "C")

    # ── D: Precision vs Recall scatter bubble ────────────────────────────────
    ax_pv = fig.add_subplot(gs[1, 0])
    marker_map = {"Baseline": "o", "Optimized": "D"}
    for model, df_m in [("Baseline", base), ("Optimized", opt)]:
        col = PALETTE["baseline"] if model == "Baseline" else PALETTE["comet"]
        for cls in classes:
            prec = df_m.loc[cls, "Precision"]
            rec  = df_m.loc[cls, "Recall"]
            sup  = df_m.loc[cls, "Support"]
            size = sup / 80
            ax_pv.scatter(prec, rec, s=size, color=class_colors[cls],
                          marker=marker_map[model], alpha=0.9, zorder=4,
                          edgecolors="white", linewidths=0.5)
            ax_pv.annotate(f"{cls[0]}-{model[:3]}", (prec, rec),
                           xytext=(5, 5), textcoords="offset points",
                           fontsize=6.5, color=DIM_TEXT)
    ax_pv.set_xlabel("Precision"); ax_pv.set_ylabel("Recall")
    ax_pv.set_title("Precision vs Recall (bubble∝support)", color=TEXT_COL)
    ax_pv.plot([0, 1], [0, 1], "--", color=DIM_TEXT, alpha=0.4, lw=0.8, label="P=R line")
    apply_dark_style(fig, ax_pv)
    add_figure_label(ax_pv, "D")

    # ── E: Delta improvements heatmap ────────────────────────────────────────
    ax_hm = fig.add_subplot(gs[1, 1])
    delta_data = []
    for cls in classes:
        row = []
        for m in ["Precision", "Recall", "F1-Score", "PR-AUC", "ROC-AUC"]:
            delta_data.append(opt.loc[cls, m] - base.loc[cls, m])
        
    delta_arr = np.array([
        [opt.loc[cls, m] - base.loc[cls, m] for m in metrics] for cls in classes
    ])
    im = ax_hm.imshow(delta_arr, cmap=GRADIENT_RED_GREEN, aspect="auto",
                      vmin=-0.1, vmax=0.1)
    ax_hm.set_xticks(range(len(metrics))); ax_hm.set_xticklabels(metrics, rotation=30, ha="right", fontsize=8)
    ax_hm.set_yticks(range(len(classes))); ax_hm.set_yticklabels(classes)
    for i in range(len(classes)):
        for j in range(len(metrics)):
            ax_hm.text(j, i, f"{delta_arr[i,j]:+.3f}", ha="center", va="center",
                       fontsize=8, color="white", fontweight="bold")
    plt.colorbar(im, ax=ax_hm, fraction=0.046, pad=0.04).ax.tick_params(colors=DIM_TEXT)
    ax_hm.set_title("Δ Optimized − Baseline", color=TEXT_COL)
    ax_hm.set_facecolor(PANEL_BG)
    for spine in ax_hm.spines.values():
        spine.set_edgecolor(GRID_COL)
    add_figure_label(ax_hm, "E")

    # ── F: Training time & iterations ────────────────────────────────────────
    ax_tr = fig.add_subplot(gs[1, 2])
    models = ["Baseline", "Optimized"]
    times  = [float(eval_df[eval_df["Model"]==m]["Training Time (s)"].iloc[0]) for m in models]
    iters  = [float(eval_df[eval_df["Model"]==m]["Best Iteration"].iloc[0]) for m in models]
    ax2    = ax_tr.twinx()
    b1 = ax_tr.bar([0, 1], times, 0.4, color=[PALETTE["baseline"], PALETTE["comet"]],
                   alpha=0.85, zorder=3, label="Training Time (s)")
    l1, = ax2.plot([0, 1], iters, "o--", color=PALETTE["accent2"], lw=2,
                   markersize=8, label="Best Iteration", zorder=5)
    for i, (bar, t) in enumerate(zip(b1, times)):
        ax_tr.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                   f"{t:.2f}s", ha="center", color=TEXT_COL, fontsize=9, fontweight="bold")
    ax_tr.set_xticks([0, 1]); ax_tr.set_xticklabels(models)
    ax_tr.set_ylabel("Training Time (s)", color=TEXT_COL)
    ax2.set_ylabel("Best Iteration", color=PALETTE["accent2"])
    ax2.tick_params(colors=PALETTE["accent2"])
    ax_tr.set_title("Training Cost", color=TEXT_COL)
    apply_dark_style(fig, ax_tr)
    ax_tr.set_facecolor(PANEL_BG)
    for spine in ax2.spines.values(): spine.set_edgecolor(GRID_COL)
    ax2.set_facecolor(PANEL_BG)
    add_figure_label(ax_tr, "F")

    plt.savefig(f"{OUT_DIR}/01_model_performance_dashboard.png",
                dpi=160, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print("✅  Chart 1 saved — Model Performance Dashboard")


# =============================================================================
# CHART 2 — Latency Curves: Baseline vs Apache Comet (multi-panel)
# =============================================================================
def chart_latency_curves():
    base_rows  = lat_df[lat_df["Engine"] == "Baseline"]
    comet_rows = lat_df[lat_df["Engine"] == "Apache Comet Enabled"]
    qps = base_rows["Concurrent Load (QPS)"].values
    percentiles = ["p50 Latency (ms)", "p90 Latency (ms)", "p95 Latency (ms)", "p99 Latency (ms)"]
    p_labels    = ["p50", "p90", "p95", "p99"]
    p_colors    = ["#3fb950", "#79c0ff", "#d29922", "#f85149"]

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor=DARK_BG)
    fig.suptitle("Gateway Latency Scaling — Baseline vs Apache Comet",
                 fontsize=16, color=TEXT_COL, fontweight="bold", y=1.01)

    # Left — Absolute latency fan
    ax = axes[0]
    for p, label, col in zip(percentiles, p_labels, p_colors):
        ax.plot(qps, base_rows[p].values,  "o-",  color=col, lw=2.2, markersize=7,
                label=f"Baseline {label}", zorder=4)
        ax.plot(qps, comet_rows[p].values, "s--", color=col, lw=1.6, markersize=6,
                alpha=0.75, label=f"Comet {label}", zorder=4)
        # fill between
        ax.fill_between(qps, base_rows[p].values, comet_rows[p].values,
                        color=col, alpha=0.08)
    ax.set_xscale("log"); ax.set_yscale("linear")
    ax.set_xlabel("Concurrent Load (QPS)"); ax.set_ylabel("Latency (ms)")
    ax.set_title("Absolute Latency by Percentile", color=TEXT_COL)
    ax.legend(fontsize=7, ncol=2, labelcolor=TEXT_COL,
              facecolor=PANEL_BG, edgecolor=GRID_COL)
    apply_dark_style(fig, ax)

    # Right — Improvement % heatmap
    ax2 = axes[1]
    imp_pct = np.array([
        [(b - c) / b * 100
         for b, c in zip(base_rows[p].values, comet_rows[p].values)]
        for p in percentiles
    ])
    im = ax2.imshow(imp_pct, cmap="YlGn", aspect="auto", vmin=0, vmax=15)
    ax2.set_xticks(range(len(qps))); ax2.set_xticklabels([f"{q} QPS" for q in qps])
    ax2.set_yticks(range(len(p_labels))); ax2.set_yticklabels(p_labels)
    for i in range(len(p_labels)):
        for j in range(len(qps)):
            ax2.text(j, i, f"{imp_pct[i,j]:.1f}%", ha="center", va="center",
                     fontsize=10, color="black", fontweight="bold")
    plt.colorbar(im, ax=ax2, fraction=0.046, pad=0.04,
                 label="% Improvement").ax.tick_params(colors=DIM_TEXT)
    ax2.set_title("Comet Latency Improvement (%)", color=TEXT_COL)
    ax2.set_facecolor(PANEL_BG)
    for spine in ax2.spines.values(): spine.set_edgecolor(GRID_COL)

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/02_latency_curves_comet_vs_baseline.png",
                dpi=160, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print("✅  Chart 2 saved — Latency Curves")


# =============================================================================
# CHART 3 — Ingestion Stress Grid (4×4 heatmaps + resource curves)
# =============================================================================
def chart_ingestion_stress():
    rates        = sorted(ing_df["Ingestion Rate (events/s)"].unique())
    poison_rates = ing_df["Poison Pill Rate"].unique()
    # Clean poison rates
    poison_float = [float(p.replace("%","")) for p in poison_rates]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6), facecolor=DARK_BG)
    fig.suptitle("Ingestion Stress Grid — Resource Consumption Under Load",
                 fontsize=16, color=TEXT_COL, fontweight="bold")

    metrics_info = [
        ("Peak Spark CPU (Cores)", "CPU Cores Used", "Blues", "A"),
        ("RAM Consumption (GiB)",  "RAM (GiB)",      "Purples", "B"),
        ("Micro-batch Processing Time (ms)", "Batch Time (ms)", "Oranges", "C"),
    ]

    for ax, (col, label, cmap_name, panel_label) in zip(axes, metrics_info):
        grid = np.zeros((len(poison_float), len(rates)))
        for i, p in enumerate(poison_rates):
            for j, r in enumerate(rates):
                val = ing_df[
                    (ing_df["Ingestion Rate (events/s)"] == r) &
                    (ing_df["Poison Pill Rate"] == p)
                ][col].values
                if len(val): grid[i, j] = val[0]

        im = ax.imshow(grid, cmap=cmap_name, aspect="auto")
        ax.set_xticks(range(len(rates))); ax.set_xticklabels([f"{r}" for r in rates], rotation=0)
        ax.set_yticks(range(len(poison_float))); ax.set_yticklabels([f"{p}%" for p in poison_float])
        ax.set_xlabel("Ingestion Rate (events/s)"); ax.set_ylabel("Poison Rate")
        ax.set_title(label, color=TEXT_COL)
        for i in range(len(poison_float)):
            for j in range(len(rates)):
                ax.text(j, i, f"{grid[i,j]:.2f}", ha="center", va="center",
                        fontsize=9, color="black" if grid[i,j] < grid.max()*0.6 else "white",
                        fontweight="bold")
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04).ax.tick_params(colors=DIM_TEXT)
        ax.set_facecolor(PANEL_BG)
        for spine in ax.spines.values(): spine.set_edgecolor(GRID_COL)
        add_figure_label(ax, panel_label)

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/03_ingestion_stress_heatmaps.png",
                dpi=160, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print("✅  Chart 3 saved — Ingestion Stress Heatmaps")


# =============================================================================
# CHART 4 — Cache Contention: Redis vs Local File (log-scale violin-inspired)
# =============================================================================
def chart_cache_contention():
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor=DARK_BG)
    fig.suptitle("Storage Cache Contention — Redis vs Local File Under Concurrency",
                 fontsize=15, color=TEXT_COL, fontweight="bold")

    redis = cache_df[cache_df["Storage Engine"].str.contains("Redis")]
    local = cache_df[cache_df["Storage Engine"].str.contains("Local")]
    threads = redis["Concurrent Threads"].values

    for ax, (metric, ylabel, label) in zip(axes, [
        ("Avg Write Latency (ms)", "Write Latency (ms)", "A"),
        ("Avg Read Latency (ms)",  "Read Latency (ms)",  "B"),
    ]):
        # Fill between for visual impact
        ax.fill_between(threads, local[metric].values, redis[metric].values,
                        alpha=0.2, color=PALETTE["local"])
        ax.plot(threads, local[metric].values, "o-", color=PALETTE["local"], lw=2.5,
                markersize=9, label="Local File Cache", zorder=5)
        ax.plot(threads, redis[metric].values, "s-", color=PALETTE["redis"], lw=2.5,
                markersize=9, label="Redis Cache", zorder=5)
        # Annotate ratio at 50 threads
        ratio = local[metric].values[-1] / redis[metric].values[-1]
        ax.annotate(f"×{ratio:.0f}× faster\n(Redis vs Local)", 
                    xy=(threads[-1], redis[metric].values[-1]),
                    xytext=(-80, 30), textcoords="offset points",
                    color=PALETTE["redis"], fontsize=9, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=PALETTE["redis"], lw=1.5))
        ax.set_yscale("log")
        ax.set_xlabel("Concurrent Threads"); ax.set_ylabel(ylabel)
        ax.set_title(ylabel, color=TEXT_COL)
        ax.legend(fontsize=9, labelcolor=TEXT_COL,
                  facecolor=PANEL_BG, edgecolor=GRID_COL)
        apply_dark_style(fig, ax)
        add_figure_label(ax, label)

    # Add timeout markers on write latency chart
    lock_timeouts_local = local["Lock Contention Timeouts"].values
    for t, to in zip(threads, lock_timeouts_local):
        if to > 0:
            axes[0].axvline(t, color=PALETTE["fail"], linestyle=":", alpha=0.6, lw=1.5)
            axes[0].text(t, axes[0].get_ylim()[1]*0.5, f"⚠ {to} timeouts",
                         color=PALETTE["fail"], fontsize=7.5, rotation=90,
                         ha="right", va="center")

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/04_cache_contention_redis_vs_local.png",
                dpi=160, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print("✅  Chart 4 saved — Cache Contention")


# =============================================================================
# CHART 5 — GreenOps: Carbon, Cost, RAM Savings (radial/donut)
# =============================================================================
def chart_greenops():
    fig, axes = plt.subplots(1, 3, figsize=(15, 6), facecolor=DARK_BG)
    fig.suptitle("GreenOps Savings — FinOps Sleep Mode vs 24/7 Baseline",
                 fontsize=15, color=TEXT_COL, fontweight="bold")

    baseline_cost   = float(green_df[green_df["operational_mode"]=="Baseline_24_7"]["monthly_cost_usd"])
    greenops_cost   = float(green_df[green_df["operational_mode"]=="FinOps_GreenOps_Sleep"]["monthly_cost_usd"])
    baseline_carbon = float(green_df[green_df["operational_mode"]=="Baseline_24_7"]["carbon_footprint_percentage"])
    greenops_carbon = float(green_df[green_df["operational_mode"]=="FinOps_GreenOps_Sleep"]["carbon_footprint_percentage"])
    baseline_ram    = float(green_df[green_df["operational_mode"]=="Baseline_24_7"]["ram_consumption_gib"])
    greenops_ram    = float(green_df[green_df["operational_mode"]=="FinOps_GreenOps_Sleep"]["ram_consumption_gib"])

    metrics = [
        ("Monthly Cost", "$USD", baseline_cost, greenops_cost, PALETTE["accent2"]),
        ("Carbon Footprint", "%", baseline_carbon, greenops_carbon, PALETTE["comet"]),
        ("RAM Consumption", "GiB", baseline_ram, greenops_ram, PALETTE["accent1"]),
    ]

    for ax, (title, unit, b_val, g_val, color) in zip(axes, metrics):
        savings_pct = (b_val - g_val) / b_val * 100
        # Donut chart
        sizes = [g_val, b_val - g_val]
        wedge_colors = [color, GRID_COL]
        wedges, _ = ax.pie(sizes, colors=wedge_colors, startangle=90,
                           wedgeprops=dict(width=0.45, edgecolor=DARK_BG, linewidth=2),
                           counterclock=False)
        # Center text
        ax.text(0, 0.08, f"{savings_pct:.1f}%", ha="center", va="center",
                fontsize=26, color=TEXT_COL, fontweight="bold")
        ax.text(0, -0.22, "savings", ha="center", va="center",
                fontsize=11, color=DIM_TEXT)
        ax.text(0, -0.45, f"Baseline: {b_val:.1f} {unit}", ha="center",
                fontsize=8.5, color=DIM_TEXT)
        ax.text(0, -0.6, f"GreenOps: {g_val:.1f} {unit}", ha="center",
                fontsize=8.5, color=color, fontweight="bold")
        ax.set_title(title, color=TEXT_COL, fontsize=12, pad=12)
        ax.set_facecolor(DARK_BG)

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/05_greenops_savings_donut.png",
                dpi=160, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print("✅  Chart 5 saved — GreenOps Donut")


# =============================================================================
# CHART 6 — Throughput & Poison Pill Defense (stacked bar + callout)
# =============================================================================
def chart_throughput_defense():
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor=DARK_BG)
    fig.suptitle("Ingestion Throughput & Poison Pill Defense",
                 fontsize=15, color=TEXT_COL, fontweight="bold")

    total   = tput_j["total_events_sent"]
    ok      = tput_j["spark_processed_successfully"]
    corrupt = tput_j["spark_isolated_corrupt_records"]
    tput    = tput_j["average_throughput_events_per_sec"]
    cpu     = tput_j["peak_spark_cpu_cores_utilized"]

    # Left — stacked bar
    ax = axes[0]
    ax.bar(["Event Disposition"], [ok],      0.5, label=f"Processed ({ok:,})",
           color=PALETTE["comet"], alpha=0.9, zorder=3)
    ax.bar(["Event Disposition"], [corrupt], 0.5, bottom=[ok],
           label=f"Isolated Corrupt ({corrupt:,})", color=PALETTE["fail"], alpha=0.85, zorder=3)
    ax.set_ylabel("Event Count"); ax.set_title("Event Processing Breakdown", color=TEXT_COL)
    ax.legend(fontsize=9, labelcolor=TEXT_COL, facecolor=PANEL_BG, edgecolor=GRID_COL)
    # Add percentage label
    ax.text(0, ok / 2, f"{ok/total*100:.1f}%\n✅ OK", ha="center", va="center",
            color="white", fontsize=13, fontweight="bold")
    ax.text(0, ok + corrupt / 2, f"{corrupt/total*100:.1f}%\n🚫 Isolated",
            ha="center", va="center", color="white", fontsize=11, fontweight="bold")
    apply_dark_style(fig, ax)

    # Right — KPI tiles
    ax2 = axes[1]
    ax2.set_xlim(0, 2); ax2.set_ylim(0, 3)
    ax2.axis("off")
    kpis = [
        ("Avg Throughput", f"{tput:,.0f} ev/s", PALETTE["accent1"]),
        ("Peak CPU Usage",  f"{cpu:.3f} cores",  PALETTE["accent2"]),
        ("Stream Interrupted", "No ✅",           PALETTE["comet"]),
    ]
    for i, (k, v, c) in enumerate(kpis):
        y = 2.4 - i * 0.85
        rect = mpatches.FancyBboxPatch((0.1, y - 0.3), 1.8, 0.7,
                                        boxstyle="round,pad=0.05",
                                        facecolor=PANEL_BG, edgecolor=c, linewidth=2)
        ax2.add_patch(rect)
        ax2.text(1, y + 0.15, k, ha="center", va="center", color=DIM_TEXT, fontsize=10)
        ax2.text(1, y - 0.1, v, ha="center", va="center", color=c,
                 fontsize=15, fontweight="bold")
    ax2.set_title("System KPIs", color=TEXT_COL)
    ax2.set_facecolor(PANEL_BG)

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/06_throughput_defense.png",
                dpi=160, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print("✅  Chart 6 saved — Throughput Defense")


# =============================================================================
# CHART 7 — Schema Drift Resilience (horizontal lollipop)
# =============================================================================
def chart_schema_drift():
    fig, ax = plt.subplots(figsize=(12, 5), facecolor=DARK_BG)
    fig.suptitle("Schema Drift Resilience — Anomaly Detection & Recovery",
                 fontsize=15, color=TEXT_COL, fontweight="bold")

    anomalies = drift_df["Anomaly Type"].tolist()
    det_rate  = drift_df["Detection Rate (%)"].values
    rec_time  = drift_df["Error Recovery Time (ms)"].values

    y_pos = np.arange(len(anomalies))

    # Lollipop stems
    for i, (y, dr, rt) in enumerate(zip(y_pos, det_rate, rec_time)):
        ax.plot([0, dr], [y, y], color=PALETTE["comet"], lw=2.5, alpha=0.7, zorder=3)
        ax.scatter(dr, y, s=200, color=PALETTE["comet"], zorder=5, edgecolors="white", lw=1.5)
        ax.text(dr + 0.5, y + 0.15, f"{dr:.0f}%", color=TEXT_COL, fontsize=10, fontweight="bold")
        # Recovery time annotation
        ax.text(dr + 0.5, y - 0.25,
                f"Recovery: {rt:.1f} ms" if rt > 0 else "Recovery: Instant",
                color=DIM_TEXT, fontsize=8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([a.replace(" (", "\n(") for a in anomalies], fontsize=8.5)
    ax.set_xlabel("Detection Rate (%)"); ax.set_xlim(95, 105)
    ax.set_title("All Anomaly Classes", color=TEXT_COL)
    ax.axvline(100, color=DIM_TEXT, linestyle="--", alpha=0.5, lw=1, label="100% target")
    ax.legend(fontsize=8, labelcolor=TEXT_COL, facecolor=PANEL_BG, edgecolor=GRID_COL)
    apply_dark_style(fig, ax)

    # Defense action annotations as colored badges
    actions = drift_df["System Defense Action"].tolist()
    action_colors = [PALETTE["fail"], PALETTE["accent2"], PALETTE["accent1"], PALETTE["comet"]]
    for i, (y, action, col) in enumerate(zip(y_pos, actions, action_colors)):
        ax.annotate(f"  ⚡ {action}", xy=(96, y),
                    fontsize=7.5, color=col, va="center", style="italic")

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/07_schema_drift_resilience.png",
                dpi=160, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print("✅  Chart 7 saved — Schema Drift Resilience")


# =============================================================================
# CHART 8 — System Master Overview (single-page executive summary)
# =============================================================================
def chart_executive_overview():
    fig = plt.figure(figsize=(20, 14), facecolor=DARK_BG)
    fig.suptitle("b-learn Platform — System Performance Executive Overview",
                 fontsize=22, color=TEXT_COL, fontweight="bold", y=0.98)

    gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.55, wspace=0.4,
                           top=0.93, bottom=0.06, left=0.07, right=0.97)

    # ── Row 0: KPI tiles ─────────────────────────────────────────────────────
    kpi_ax = fig.add_subplot(gs[0, :])
    kpi_ax.axis("off")
    kpis = [
        ("Ingestion Throughput",    f"{tput_j['average_throughput_events_per_sec']:,.0f} ev/s", PALETTE["accent1"]),
        ("Poison Pill Isolation",   "100%",        PALETTE["comet"]),
        ("Schema Drift Detection",  "100%",        PALETTE["comet"]),
        ("Cost Savings (GreenOps)", "75.9%",       PALETTE["accent2"]),
        ("Carbon Reduction",        "75.9%",       PALETTE["accent3"]),
        ("Cache Speedup (Redis)",   "~80× faster", PALETTE["redis"]),
        ("Comet p99 Improvement",   "12.5% @ 1k QPS", PALETTE["baseline"]),
        ("Best ROC-AUC (LGBM)",     "0.826",       PALETTE["fail"] if False else PALETTE["comet"]),
    ]
    tile_w = 1.0 / len(kpis)
    for i, (label, val, col) in enumerate(kpis):
        x = i * tile_w
        rect = mpatches.FancyBboxPatch((x + 0.005, 0.05), tile_w - 0.015, 0.88,
                                        boxstyle="round,pad=0.03",
                                        facecolor=PANEL_BG, edgecolor=col, linewidth=2,
                                        transform=kpi_ax.transAxes, clip_on=False)
        kpi_ax.add_patch(rect)
        kpi_ax.text(x + tile_w/2, 0.72, val, ha="center", va="center",
                    transform=kpi_ax.transAxes, color=col,
                    fontsize=14, fontweight="bold")
        kpi_ax.text(x + tile_w/2, 0.3, label, ha="center", va="center",
                    transform=kpi_ax.transAxes, color=DIM_TEXT, fontsize=7.5)

    # ── Row 1: Latency fan + Model F1 bar ────────────────────────────────────
    ax_lat = fig.add_subplot(gs[1, :2])
    base_rows  = lat_df[lat_df["Engine"] == "Baseline"]
    comet_rows = lat_df[lat_df["Engine"] == "Apache Comet Enabled"]
    qps = base_rows["Concurrent Load (QPS)"].values
    p_cols  = ["#3fb950", "#79c0ff", "#d29922", "#f85149"]
    p_names = ["p50", "p90", "p95", "p99"]
    for p, label, col in zip(
        ["p50 Latency (ms)", "p90 Latency (ms)", "p95 Latency (ms)", "p99 Latency (ms)"],
        p_names, p_cols
    ):
        ax_lat.plot(qps, base_rows[p].values,  "o-",  color=col, lw=2.0, markersize=6,
                    label=f"Baseline {label}")
        ax_lat.plot(qps, comet_rows[p].values, "s--", color=col, lw=1.5, markersize=5, alpha=0.75)
    ax_lat.set_xscale("log")
    ax_lat.set_xlabel("QPS"); ax_lat.set_ylabel("Latency (ms)")
    ax_lat.set_title("Latency: Baseline (solid) vs Comet (dashed)", color=TEXT_COL)
    ax_lat.legend(fontsize=7, ncol=2, labelcolor=TEXT_COL, facecolor=PANEL_BG, edgecolor=GRID_COL)
    apply_dark_style(fig, ax_lat)

    ax_f1 = fig.add_subplot(gs[1, 2:])
    base = eval_df[eval_df["Model"] == "Baseline"].set_index("Class")
    opt  = eval_df[eval_df["Model"] == "Optimized"].set_index("Class")
    classes = ["Fail", "Success", "Withdrawn"]
    x = np.arange(len(classes)); w = 0.28
    for m_label, df_m, col, offset in [
        ("Baseline", base, PALETTE["baseline"], -w),
        ("Optimized", opt, PALETTE["comet"], 0)
    ]:
        ax_f1.bar(x + offset, [df_m.loc[c, "F1-Score"] for c in classes],
                  w, label=m_label, color=col, alpha=0.85, zorder=3)
    ax_f1.set_xticks(x - w/2); ax_f1.set_xticklabels(classes)
    ax_f1.set_ylabel("F1-Score"); ax_f1.set_title("LGBM F1 by Class", color=TEXT_COL)
    ax_f1.legend(fontsize=8, labelcolor=TEXT_COL, facecolor=PANEL_BG, edgecolor=GRID_COL)
    apply_dark_style(fig, ax_f1)

    # ── Row 2: Cache + GreenOps bar + Ingestion CPU ───────────────────────────
    ax_cache = fig.add_subplot(gs[2, 0])
    redis = cache_df[cache_df["Storage Engine"].str.contains("Redis")]
    local = cache_df[cache_df["Storage Engine"].str.contains("Local")]
    threads = redis["Concurrent Threads"].values
    ax_cache.plot(threads, local["Avg Write Latency (ms)"].values, "o-",
                  color=PALETTE["local"], lw=2, markersize=7, label="Local Write")
    ax_cache.plot(threads, redis["Avg Write Latency (ms)"].values, "s-",
                  color=PALETTE["redis"], lw=2, markersize=7, label="Redis Write")
    ax_cache.set_yscale("log"); ax_cache.set_xlabel("Threads")
    ax_cache.set_ylabel("Write Latency (ms, log)"); ax_cache.set_title("Cache Write Latency", color=TEXT_COL)
    ax_cache.legend(fontsize=7, labelcolor=TEXT_COL, facecolor=PANEL_BG, edgecolor=GRID_COL)
    apply_dark_style(fig, ax_cache)

    ax_green = fig.add_subplot(gs[2, 1])
    ops_modes = ["Baseline\n24/7", "FinOps\nGreenOps"]
    costs = [float(green_df[green_df["operational_mode"]==m]["monthly_cost_usd"])
             for m in ["Baseline_24_7", "FinOps_GreenOps_Sleep"]]
    bars = ax_green.bar([0, 1], costs, 0.5, color=[PALETTE["fail"], PALETTE["comet"]],
                        alpha=0.9, zorder=3)
    for bar, c in zip(bars, costs):
        ax_green.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                      f"${c:.0f}/mo", ha="center", color=TEXT_COL, fontsize=10, fontweight="bold")
    ax_green.set_xticks([0, 1]); ax_green.set_xticklabels(ops_modes)
    ax_green.set_ylabel("Monthly Cost (USD)"); ax_green.set_title("Cost: GreenOps Savings", color=TEXT_COL)
    apply_dark_style(fig, ax_green)

    ax_ing = fig.add_subplot(gs[2, 2:])
    rates = sorted(ing_df["Ingestion Rate (events/s)"].unique())
    cpu_at_0pct = [ing_df[(ing_df["Ingestion Rate (events/s)"]==r) &
                          (ing_df["Poison Pill Rate"]=="0%")]["Peak Spark CPU (Cores)"].values[0]
                   for r in rates]
    cpu_at_30pct = [ing_df[(ing_df["Ingestion Rate (events/s)"]==r) &
                           (ing_df["Poison Pill Rate"]=="30%")]["Peak Spark CPU (Cores)"].values[0]
                    for r in rates]
    ax_ing.fill_between(rates, cpu_at_0pct, cpu_at_30pct, alpha=0.25, color=PALETTE["accent2"],
                         label="Poison pill overhead")
    ax_ing.plot(rates, cpu_at_0pct,  "o-", color=PALETTE["comet"], lw=2.2, markersize=8, label="0% poison")
    ax_ing.plot(rates, cpu_at_30pct, "s--", color=PALETTE["accent2"], lw=2.0, markersize=7, label="30% poison")
    for x, y in zip(rates, cpu_at_0pct):
        ax_ing.text(x, y + 0.007, f"{y:.3f}", ha="center", va="bottom",
                    color=TEXT_COL, fontsize=7.5)
    ax_ing.set_xlabel("Ingestion Rate (events/s)"); ax_ing.set_ylabel("Peak CPU (Cores)")
    ax_ing.set_title("CPU Scaling vs Poison Rate", color=TEXT_COL)
    ax_ing.legend(fontsize=8, labelcolor=TEXT_COL, facecolor=PANEL_BG, edgecolor=GRID_COL)
    apply_dark_style(fig, ax_ing)

    plt.savefig(f"{OUT_DIR}/08_executive_overview.png",
                dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print("✅  Chart 8 saved — Executive Overview")


# =============================================================================
# CHART 9 — LightGBM Precision-Recall-AUC Radar (per class)
# =============================================================================
def chart_lgbm_radar():
    from matplotlib.patches import FancyArrowPatch

    fig, axes = plt.subplots(1, 3, figsize=(15, 6), subplot_kw=dict(polar=True),
                             facecolor=DARK_BG)
    fig.suptitle("LightGBM Performance Radar — Baseline vs Optimized (per class)",
                 fontsize=15, color=TEXT_COL, fontweight="bold")

    classes = ["Fail", "Success", "Withdrawn"]
    metrics = ["Precision", "Recall", "F1-Score", "PR-AUC", "ROC-AUC"]
    N = len(metrics)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    base = eval_df[eval_df["Model"] == "Baseline"].set_index("Class")
    opt  = eval_df[eval_df["Model"] == "Optimized"].set_index("Class")

    for ax, cls in zip(axes, classes):
        b_vals = [float(base.loc[cls, m]) for m in metrics] + [float(base.loc[cls, metrics[0]])]
        o_vals = [float(opt.loc[cls, m]) for m in metrics] + [float(opt.loc[cls, metrics[0]])]

        ax.set_facecolor(PANEL_BG)
        ax.plot(angles, b_vals, "o-", color=PALETTE["baseline"], lw=2, markersize=6, label="Baseline")
        ax.fill(angles, b_vals, color=PALETTE["baseline"], alpha=0.2)
        ax.plot(angles, o_vals, "s-", color=PALETTE["comet"], lw=2, markersize=6, label="Optimized")
        ax.fill(angles, o_vals, color=PALETTE["comet"], alpha=0.2)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics, color=TEXT_COL, fontsize=8.5)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(["0.2","0.4","0.6","0.8","1.0"], fontsize=7, color=DIM_TEXT)
        ax.set_ylim(0, 1)
        ax.grid(color=GRID_COL, linewidth=0.8)
        ax.spines["polar"].set_edgecolor(GRID_COL)
        ax.set_title(f"Class: {cls}", color=TEXT_COL, pad=18, fontsize=11)
        ax.tick_params(colors=DIM_TEXT)

    handles = [
        mpatches.Patch(color=PALETTE["baseline"], label="Baseline"),
        mpatches.Patch(color=PALETTE["comet"],    label="Optimized"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=10,
               labelcolor=TEXT_COL, facecolor=PANEL_BG, edgecolor=GRID_COL, framealpha=0.9)

    plt.tight_layout(rect=[0, 0.07, 1, 1])
    plt.savefig(f"{OUT_DIR}/09_lgbm_radar_per_class.png",
                dpi=160, bbox_inches="tight", facecolor=DARK_BG)
    plt.close()
    print("✅  Chart 9 saved — LGBM Radar per class")


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("\n🎨  Generating creative benchmark charts...\n")
    chart_model_performance()
    chart_latency_curves()
    chart_ingestion_stress()
    chart_cache_contention()
    chart_greenops()
    chart_throughput_defense()
    chart_schema_drift()
    chart_executive_overview()
    chart_lgbm_radar()
    print(f"\n✅  All 9 charts saved to: {OUT_DIR}/")
