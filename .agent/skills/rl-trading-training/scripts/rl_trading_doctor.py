from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[4]


def _status(ok: bool) -> str:
    return "OK" if ok else "MISSING"


def _print_section(title: str) -> None:
    print(f"\n== {title} ==")


def _exists(paths: Iterable[Path]) -> None:
    for path in paths:
        rel = path.relative_to(ROOT)
        print(f"{_status(path.exists()):8} {rel}")


def _load_cfg():
    config_path = ROOT / "config.py"
    if not config_path.exists():
        return None, "config.py not found"

    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("project_config", config_path)
    if spec is None or spec.loader is None:
        return None, "could not load config.py"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "CFG", None), None


def _read_report_value(path: Path, wanted: tuple[str, ...]) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    for row in rows:
        if len(row) >= 2 and row[0] in wanted:
            values[row[0]] = row[1]
    return values


def _count_csv_rows(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


def main() -> int:
    print(f"Project root: {ROOT}")

    _print_section("Required source files")
    _exists(
        [
            ROOT / "config.py",
            ROOT / "data_loader.py",
            ROOT / "features.py",
            ROOT / "env_bracket.py",
            ROOT / "run_pipeline.py",
            ROOT / "train_ppo.py",
            ROOT / "final_holdout_eval.py",
            ROOT / "visualize.py",
            ROOT / "view_results.py",
        ]
    )

    cfg, err = _load_cfg()
    _print_section("Config snapshot")
    if cfg is None:
        print(f"ERROR: {err}")
    else:
        data_path = ROOT / cfg.csv_path
        print(f"csv_path: {cfg.csv_path} [{_status(data_path.exists())}]")
        print(f"time_col: {cfg.time_col}")
        print(f"source_tz: {cfg.source_tz}")
        print(f"timestamp_is_bar_open: {cfg.timestamp_is_bar_open}")
        print(f"execution_timeframe: {cfg.execution_timeframe}")
        print(f"decision_timeframe: {cfg.decision_timeframe} -> {cfg.pandas_tf}")
        print(f"train/val/test: {cfg.train_frac}/{cfg.val_frac}/{cfg.test_frac}")
        print(
            "sliding WF: "
            f"train={cfg.sliding_train_years}y, "
            f"val={cfg.sliding_val_months}m, "
            f"test={cfg.sliding_test_months}m, "
            f"step={cfg.sliding_step_months}m"
        )
        print(
            "costs: "
            f"spread={cfg.spread_price}, "
            f"slippage={cfg.slippage_price}, "
            f"commission={cfg.commission_per_trade}"
        )

    _print_section("Validation artifacts")
    _exists(
        [
            ROOT / "outputs" / "performance_report.csv",
            ROOT / "outputs" / "selected_policy.csv",
            ROOT / "outputs" / "selected_val_trade_log.csv",
            ROOT / "outputs" / "selected_val_equity_curve.csv",
            ROOT / "outputs" / "walk_forward_baseline.csv",
            ROOT / "outputs" / "04_val_trades_on_chart.html",
            ROOT / "outputs" / "05_val_equity_drawdown.html",
        ]
    )

    _print_section("RL walk-forward artifacts")
    _exists(
        [
            ROOT / "models" / "sliding_walk_forward_summary.csv",
            ROOT / "models" / "sliding_oos_equity.csv",
            ROOT / "models" / "best_model" / "best_model.zip",
            ROOT / "models" / "best_model" / "best_model_vecnorm.pkl",
            ROOT / "models" / "run_info.json",
            ROOT / "models" / "NO_DEPLOY.txt",
        ]
    )

    no_deploy = ROOT / "models" / "NO_DEPLOY.txt"
    if no_deploy.exists():
        print("\nWARNING: models/NO_DEPLOY.txt exists. Treat this run as research-only.")

    _print_section("Sealed holdout artifacts")
    _exists(
        [
            ROOT / "outputs" / "final_holdout" / "holdout_report.csv",
            ROOT / "outputs" / "final_holdout" / "rl_test_trade_log.csv",
            ROOT / "outputs" / "final_holdout" / "rl_test_equity_curve.csv",
        ]
    )

    _print_section("Metric snippets")
    metric_names = (
        "total_return_pct",
        "annualized_return_pct",
        "max_drawdown_pct",
        "sharpe_like",
        "profit_factor",
        "n_trades",
    )
    for report in (
        ROOT / "outputs" / "performance_report.csv",
        ROOT / "outputs" / "final_holdout" / "holdout_report.csv",
    ):
        rel = report.relative_to(ROOT)
        values = _read_report_value(report, metric_names)
        if not values:
            print(f"{rel}: no readable summary")
            continue
        print(rel)
        for name in metric_names:
            if name in values:
                print(f"  {name}: {values[name]}")

    for trades in (
        ROOT / "outputs" / "selected_val_trade_log.csv",
        ROOT / "outputs" / "final_holdout" / "rl_test_trade_log.csv",
    ):
        n_rows = _count_csv_rows(trades)
        if n_rows is not None:
            print(f"{trades.relative_to(ROOT)} rows: {n_rows}")

    print("\nDoctor complete. Use validation/walk-forward outputs for iteration; use holdout only after model freeze.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
