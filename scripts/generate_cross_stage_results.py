from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "generated_results" / "cross_stage_demo"


def norm_cdf(x: np.ndarray | float) -> np.ndarray | float:
    return 0.5 * (1.0 + np.vectorize(__import__("math").erf)(np.asarray(x) / np.sqrt(2.0)))


def rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    sorted_values = values[order]
    start = 0
    n = len(values)
    while start < n:
        end = start + 1
        while end < n and sorted_values[end] == sorted_values[start]:
            end += 1
        ranks[order[start:end]] = 0.5 * (start + end - 1) + 1.0
        start = end
    return ranks


def spearman_abs(x: np.ndarray, y: np.ndarray) -> float:
    xr = rankdata(x)
    yr = rankdata(y)
    return float(abs(np.corrcoef(xr, yr)[0, 1]))


def stage_stats(stage: str, samples: pd.DataFrame) -> dict:
    stress = samples[f"{stage}_stress_mpa"].to_numpy()
    beta = samples[f"{stage}_beta"].to_numpy()
    pf = samples[f"{stage}_pf"].to_numpy()
    leak = samples[f"{stage}_leak_ml_min"].to_numpy()
    damage = samples[f"{stage}_damage"].to_numpy()
    return {
        "stage": stage,
        "stress_mean_mpa": np.mean(stress),
        "stress_std_mpa": np.std(stress, ddof=1),
        "stress_p05_mpa": np.percentile(stress, 5),
        "stress_p95_mpa": np.percentile(stress, 95),
        "leak_mean_ml_min": np.mean(leak),
        "leak_p95_ml_min": np.percentile(leak, 95),
        "damage_mean": np.mean(damage),
        "damage_p95": np.percentile(damage, 95),
        "beta_mean": np.mean(beta),
        "beta_p05": np.percentile(beta, 5),
        "pf_mean": np.mean(pf),
        "pf_p95": np.percentile(pf, 95),
    }


def build_samples(n: int = 5000, seed: int = 20260910) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Demonstration case: aircraft electro-hydraulic actuator sealing assembly.
    material_E_gpa = rng.normal(70.5, 1.6, n)
    allowable_stress_mpa = rng.normal(365.0, 15.0, n)
    design_load_kn = rng.normal(18.0, 0.9, n)
    thermal_delta_c = rng.normal(86.0, 7.0, n)
    wall_thickness_mm = rng.normal(2.80, 0.045, n)
    seal_friction = np.clip(rng.normal(0.135, 0.018, n), 0.08, 0.22)

    machining_bias_mm = rng.normal(0.0, 0.026, n)
    assembly_gap_um = np.clip(rng.normal(34.0, 7.5, n), 12.0, 62.0)
    residual_stress_mpa = rng.normal(36.0, 9.0, n)

    test_calibration = rng.normal(0.985, 0.018, n)
    test_noise_mpa = rng.normal(0.0, 3.5, n)

    mission_load_factor = rng.normal(1.08, 0.075, n)
    temperature_factor = rng.normal(1.02, 0.035, n)
    wear_gap_growth_um = np.clip(rng.lognormal(np.log(8.0), 0.32, n), 2.0, 26.0)

    base_stress = (
        185.0
        * (design_load_kn / 18.0) ** 1.08
        * (2.80 / wall_thickness_mm) ** 1.75
        * (70.5 / material_E_gpa) ** 0.18
        + 0.14 * (thermal_delta_c - 80.0)
        + 22.0 * (seal_friction - 0.135)
    )

    design_stress = base_stress
    manufacturing_stress = (
        base_stress
        * (2.80 / (wall_thickness_mm + machining_bias_mm)) ** 0.72
        + 0.24 * residual_stress_mpa
        + 0.11 * (assembly_gap_um - 34.0)
    )
    test_observed = manufacturing_stress * test_calibration + test_noise_mpa
    test_stress = np.mean(test_observed) + 0.78 * (test_observed - np.mean(test_observed))
    service_stress = (
        test_stress * mission_load_factor * temperature_factor
        + 0.19 * wear_gap_growth_um
        + 0.08 * np.maximum(assembly_gap_um - 40.0, 0.0)
    )

    stages = {
        "design": design_stress,
        "manufacturing": manufacturing_stress,
        "test": test_stress,
        "service": service_stress,
    }

    rows = {
        "material_E_gpa": material_E_gpa,
        "allowable_stress_mpa": allowable_stress_mpa,
        "design_load_kn": design_load_kn,
        "thermal_delta_c": thermal_delta_c,
        "wall_thickness_mm": wall_thickness_mm,
        "seal_friction": seal_friction,
        "machining_bias_mm": machining_bias_mm,
        "assembly_gap_um": assembly_gap_um,
        "residual_stress_mpa": residual_stress_mpa,
        "mission_load_factor": mission_load_factor,
        "temperature_factor": temperature_factor,
        "wear_gap_growth_um": wear_gap_growth_um,
    }

    for name, stress in stages.items():
        margin = allowable_stress_mpa - stress
        beta = margin / 45.0
        pf = norm_cdf(-beta)
        leak = 0.018 + 0.00135 * np.maximum(stress - 165.0, 0.0) + 0.0022 * assembly_gap_um
        if name == "service":
            leak = leak + 0.0058 * wear_gap_growth_um
        damage = np.clip((stress / 430.0) ** 6.2 * (1.0 + 0.004 * assembly_gap_um), 0, None)
        if name == "service":
            damage = damage * (1.0 + 0.018 * wear_gap_growth_um)
        rows[f"{name}_stress_mpa"] = stress
        rows[f"{name}_beta"] = beta
        rows[f"{name}_pf"] = pf
        rows[f"{name}_leak_ml_min"] = leak
        rows[f"{name}_damage"] = damage

    return pd.DataFrame(rows)


def build_sensitivity(samples: pd.DataFrame) -> pd.DataFrame:
    drivers = [
        ("设计载荷", "design_load_kn"),
        ("壁厚偏差", "wall_thickness_mm"),
        ("材料弹性模量", "material_E_gpa"),
        ("装配间隙", "assembly_gap_um"),
        ("残余应力", "residual_stress_mpa"),
        ("服役载荷谱", "mission_load_factor"),
        ("磨损间隙增长", "wear_gap_growth_um"),
    ]
    rows = []
    for stage in ["design", "manufacturing", "test", "service"]:
        y = samples[f"{stage}_pf"].to_numpy()
        scores = np.array([spearman_abs(samples[col].to_numpy(), y) for _, col in drivers])
        shares = scores / scores.sum() * 100.0
        for (label, col), score, share in zip(drivers, scores, shares):
            rows.append(
                {
                    "stage": stage,
                    "factor": label,
                    "source_column": col,
                    "spearman_abs": score,
                    "contribution_percent": share,
                }
            )
    return pd.DataFrame(rows)


def set_style() -> None:
    plt.rcParams.update(
        {
            "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.dpi": 140,
            "savefig.dpi": 220,
            "axes.edgecolor": "#444444",
            "axes.labelcolor": "#222222",
            "xtick.color": "#333333",
            "ytick.color": "#333333",
        }
    )


def save_stage_plot(summary: pd.DataFrame) -> None:
    labels = ["设计", "制造", "试验修正", "服役"]
    x = np.arange(len(labels))
    mean = summary["stress_mean_mpa"].to_numpy()
    low = mean - summary["stress_p05_mpa"].to_numpy()
    high = summary["stress_p95_mpa"].to_numpy() - mean

    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    ax.errorbar(x, mean, yerr=[low, high], fmt="o-", color="#2f5d8c", ecolor="#8ca6bf", capsize=5, lw=2)
    ax.axhline(365, color="#9a3f3f", lw=1.2, linestyle="--", label="疲劳/密封校核阈值均值")
    ax.set_xticks(x, labels)
    ax.set_ylabel("最大等效应力 / MPa")
    ax.set_title("跨阶段最大应力传播结果", fontsize=15, pad=12)
    ax.grid(axis="y", color="#e4e7eb", lw=0.8)
    ax.legend(frameon=False, loc="upper left")
    ax.set_ylim(160, 390)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "01_stage_stress_propagation.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    ax.errorbar(x, mean, yerr=[low, high], fmt="o-", color="#2f5d8c", ecolor="#8ca6bf", capsize=4, lw=2.4)
    ax.axhline(365, color="#9a3f3f", lw=1.4, linestyle="--")
    ax.set_xticks(x, labels)
    ax.set_ylabel("MPa", fontsize=12)
    ax.tick_params(labelsize=11)
    ax.grid(axis="y", color="#e4e7eb", lw=0.8)
    ax.set_ylim(160, 390)
    fig.tight_layout(pad=0.35)
    fig.savefig(OUT_DIR / "01_stage_stress_propagation_ppt.png")
    plt.close(fig)


def save_reliability_plot(summary: pd.DataFrame) -> None:
    labels = ["设计", "制造", "试验修正", "服役"]
    x = np.arange(len(labels))

    fig, ax1 = plt.subplots(figsize=(9.0, 4.8))
    ax1.plot(x, summary["beta_mean"], marker="o", color="#315b7d", lw=2, label="可靠度指标 β")
    ax1.fill_between(x, summary["beta_p05"], summary["beta_mean"], color="#315b7d", alpha=0.14, linewidth=0)
    ax1.set_xticks(x, labels)
    ax1.set_ylabel("可靠度指标 β")
    ax1.set_ylim(5.0, 8.6)
    ax1.grid(axis="y", color="#e4e7eb", lw=0.8)

    ax2 = ax1.twinx()
    ax2.plot(x, summary["pf_mean"] * 1e4, marker="s", color="#7b4d3a", lw=1.8, label="平均失效概率")
    ax2.set_ylabel("平均失效概率 / 10^-4")
    ax2.set_ylim(0, max(summary["pf_mean"] * 1e4) * 1.35)
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines], frameon=False, loc="upper right")
    ax1.set_title("跨阶段可靠性指标演化", fontsize=15, pad=12)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "02_reliability_evolution.png")
    plt.close(fig)

    fig, ax1 = plt.subplots(figsize=(5.6, 3.2))
    ax1.plot(x, summary["beta_mean"], marker="o", color="#315b7d", lw=2.4, label="β")
    ax1.set_xticks(x, labels)
    ax1.set_ylabel("β", fontsize=12)
    ax1.set_ylim(3.0, 4.3)
    ax1.tick_params(labelsize=11)
    ax1.grid(axis="y", color="#e4e7eb", lw=0.8)

    ax2 = ax1.twinx()
    ax2.plot(x, summary["pf_mean"] * 1e4, marker="s", color="#7b4d3a", lw=2.0, label="Pf")
    ax2.set_ylabel("Pf / 10^-4", fontsize=12)
    ax2.set_ylim(0, max(summary["pf_mean"] * 1e4) * 1.35)
    ax2.tick_params(labelsize=11)
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines], frameon=False, loc="upper left", fontsize=11)
    fig.tight_layout(pad=0.35)
    fig.savefig(OUT_DIR / "02_reliability_evolution_ppt.png")
    plt.close(fig)


def save_sensitivity_plot(sensitivity: pd.DataFrame) -> None:
    service = sensitivity[sensitivity["stage"] == "service"].sort_values("contribution_percent")
    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    ax.barh(service["factor"], service["contribution_percent"], color="#5d7f71")
    ax.set_xlabel("贡献占比 / %")
    ax.set_title("服役阶段失效概率敏感性贡献", fontsize=15, pad=12)
    ax.grid(axis="x", color="#e4e7eb", lw=0.8)
    ax.set_xlim(0, max(35, service["contribution_percent"].max() * 1.18))
    fig.tight_layout()
    fig.savefig(OUT_DIR / "03_service_sensitivity.png")
    plt.close(fig)


def save_uncertainty_width_plot(summary: pd.DataFrame) -> None:
    labels = ["设计", "制造", "试验修正", "服役"]
    width = summary["stress_p95_mpa"] - summary["stress_p05_mpa"]
    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    ax.bar(labels, width, color=["#6b879f", "#8c7a5b", "#5d7f71", "#7b4d3a"])
    ax.set_ylabel("90% 区间宽度 / MPa")
    ax.set_title("跨阶段应力不确定性区间宽度", fontsize=15, pad=12)
    ax.grid(axis="y", color="#e4e7eb", lw=0.8)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "04_uncertainty_interval_width.png")
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    set_style()

    samples = build_samples()
    summary = pd.DataFrame([stage_stats(stage, samples) for stage in ["design", "manufacturing", "test", "service"]])
    sensitivity = build_sensitivity(samples)

    samples.to_csv(OUT_DIR / "cross_stage_samples.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(OUT_DIR / "stage_summary.csv", index=False, encoding="utf-8-sig")
    sensitivity.to_csv(OUT_DIR / "sensitivity_contribution.csv", index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(OUT_DIR / "cross_stage_demo_results.xlsx", engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="阶段统计", index=False)
        sensitivity.to_excel(writer, sheet_name="敏感性贡献", index=False)
        samples.head(300).to_excel(writer, sheet_name="样本摘录", index=False)

    save_stage_plot(summary)
    save_reliability_plot(summary)
    save_sensitivity_plot(sensitivity)
    save_uncertainty_width_plot(summary)

    notes = OUT_DIR / "slide_copy_suggestion.md"
    notes.write_text(
        "\n".join(
            [
                "# 跨阶段演示算例结果页建议",
                "",
                "标题：跨阶段不确定性传播演示验证",
                "",
                "建议主结论：",
                "基于航空作动机构密封组件演示算例，平台完成设计、制造、试验修正和服役评估四个阶段的参数传递与可靠性指标计算，能够输出应力区间、失效概率和关键不确定性贡献。",
                "",
                "建议页内要点：",
                "- 最大等效应力 90% 区间从设计阶段的 {:.1f}-{:.1f} MPa，传递到服役阶段的 {:.1f}-{:.1f} MPa。".format(
                    summary.loc[0, "stress_p05_mpa"],
                    summary.loc[0, "stress_p95_mpa"],
                    summary.loc[3, "stress_p05_mpa"],
                    summary.loc[3, "stress_p95_mpa"],
                ),
                "- 试验阶段引入校准系数后，应力区间宽度由 {:.1f} MPa 收敛到 {:.1f} MPa。".format(
                    summary.loc[1, "stress_p95_mpa"] - summary.loc[1, "stress_p05_mpa"],
                    summary.loc[2, "stress_p95_mpa"] - summary.loc[2, "stress_p05_mpa"],
                ),
                "- 服役阶段平均失效概率为 {:.2f} x 10^-4，主要受服役载荷谱、设计载荷和壁厚偏差影响。".format(
                    summary.loc[3, "pf_mean"] * 1e4
                ),
                "",
                "备注：以上为平台功能演示算例的仿真数据，不作为型号实测结论。",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Generated results in {OUT_DIR}")


if __name__ == "__main__":
    main()
