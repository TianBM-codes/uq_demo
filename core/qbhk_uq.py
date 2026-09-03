import numpy as np

from .qbhk_solver import QbhkParams, solve_qbhk


DEFAULT_UNCERTAIN_SPECS = {
    "E": {"enabled": True, "dist": "Normal", "mean": 2.0e9, "std": 1.0e8},
    "F": {"enabled": True, "dist": "Normal", "mean": -10.0, "std": 1.0},
    "d": {"enabled": False, "dist": "Normal", "mean": 0.02, "std": 0.001},
    "rho": {"enabled": False, "dist": "Normal", "mean": 7850.0, "std": 150.0},
    "m_slider": {"enabled": False, "dist": "Normal", "mean": 0.5, "std": 0.03},
    "omega": {"enabled": False, "dist": "Normal", "mean": float(np.pi), "std": 0.05},
}


def run_qbhk_uq(base_params=None, uncertain_specs=None, sample_count=30, seed=42):
    base = base_params if isinstance(base_params, QbhkParams) else QbhkParams(**(base_params or {}))
    specs = _merge_specs(uncertain_specs)
    enabled = {name: spec for name, spec in specs.items() if spec.get("enabled")}
    if not enabled:
        return {"deterministic": solve_qbhk(base), "samples": [], "statistics": None, "specs": specs}

    rng = np.random.default_rng(seed)
    deterministic = solve_qbhk(base)
    samples = []
    results = []
    for _ in range(max(1, int(sample_count))):
        updates = {}
        for name, spec in enabled.items():
            updates[name] = _draw_value(rng, spec)
        sample_params = base.with_updates(**updates)
        samples.append(updates)
        results.append(solve_qbhk(sample_params))

    slider_x = np.vstack([item["slider"]["x"] for item in results])
    slider_v = np.vstack([item["slider"]["v"] for item in results])
    slider_a = np.vstack([item["slider"]["a"] for item in results])
    max_abs_x = np.array([item["summary"]["max_abs_x"] for item in results])
    max_abs_v = np.array([item["summary"]["max_abs_v"] for item in results])
    max_abs_a = np.array([item["summary"]["max_abs_a"] for item in results])

    stats = {
        "t": results[0]["t"],
        "slider_x_mean": slider_x.mean(axis=0),
        "slider_x_std": slider_x.std(axis=0, ddof=1) if len(results) > 1 else np.zeros(slider_x.shape[1]),
        "slider_v_mean": slider_v.mean(axis=0),
        "slider_v_std": slider_v.std(axis=0, ddof=1) if len(results) > 1 else np.zeros(slider_v.shape[1]),
        "slider_a_mean": slider_a.mean(axis=0),
        "slider_a_std": slider_a.std(axis=0, ddof=1) if len(results) > 1 else np.zeros(slider_a.shape[1]),
        "max_abs_x": max_abs_x,
        "max_abs_v": max_abs_v,
        "max_abs_a": max_abs_a,
        "summary": {
            "max_abs_x_mean": float(max_abs_x.mean()),
            "max_abs_x_std": float(max_abs_x.std(ddof=1)) if len(results) > 1 else 0.0,
            "max_abs_v_mean": float(max_abs_v.mean()),
            "max_abs_v_std": float(max_abs_v.std(ddof=1)) if len(results) > 1 else 0.0,
            "max_abs_a_mean": float(max_abs_a.mean()),
            "max_abs_a_std": float(max_abs_a.std(ddof=1)) if len(results) > 1 else 0.0,
        },
    }
    return {"deterministic": deterministic, "samples": samples, "sample_results": results, "statistics": stats, "specs": specs}


def _merge_specs(specs):
    merged = {key: dict(value) for key, value in DEFAULT_UNCERTAIN_SPECS.items()}
    for key, value in (specs or {}).items():
        if key in merged:
            merged[key].update(value)
    return merged


def _draw_value(rng, spec):
    dist = spec.get("dist", "Normal")
    if dist == "Uniform":
        low = float(spec.get("low", spec.get("mean", 0.0) - spec.get("std", 0.0)))
        high = float(spec.get("high", spec.get("mean", 0.0) + spec.get("std", 0.0)))
        return float(rng.uniform(low, high))
    mean = float(spec.get("mean", 0.0))
    std = abs(float(spec.get("std", 0.0)))
    return float(rng.normal(mean, std))
