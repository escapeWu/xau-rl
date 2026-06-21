#!/usr/bin/env python3
"""Local dashboard API for XAUUSD RL training artifacts.

Serves a built React dashboard plus JSON/file endpoints that read only local
project artifacts under outputs/, models/, notebooks/, and logs/. No trading
credentials or arbitrary filesystem paths are exposed.
"""
from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import os
import posixpath
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WEB_ROOT = ROOT / "dashboard" / "dist"
ARTIFACT_DIRS = ["outputs", "models", "notebooks", "logs"]
TEXT_EXTENSIONS = {".csv", ".json", ".txt", ".log", ".md"}
VIEW_EXTENSIONS = TEXT_EXTENSIONS | {".html", ".htm", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
MAX_CSV_ROWS = 200
MAX_TEXT_BYTES = 1_000_000


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def relpath(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def safe_artifact_path(raw: str) -> Path:
    decoded = urllib.parse.unquote(raw)
    # Normalize as a POSIX path regardless of platform separators from URL.
    norm = posixpath.normpath(decoded.replace("\\", "/")).lstrip("/")
    if norm.startswith("../") or norm == "..":
        raise ValueError("Path traversal is not allowed")
    path = (ROOT / norm).resolve()
    allowed_roots = [(ROOT / d).resolve() for d in ARTIFACT_DIRS]
    if not any(path == base or base in path.parents for base in allowed_roots):
        raise ValueError("Only artifact directories are readable")
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(norm)
    if path.suffix.lower() not in VIEW_EXTENSIONS:
        raise ValueError(f"Unsupported artifact extension: {path.suffix}")
    return path


def read_csv_preview(path: Path, max_rows: int = MAX_CSV_ROWS) -> dict[str, Any]:
    rows: list[dict[str, str]] = []
    columns: list[str] = []
    total_rows = 0
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        for row in reader:
            total_rows += 1
            if len(rows) < max_rows:
                rows.append({k: v for k, v in row.items()})
    return {"columns": columns, "rows": rows, "totalRows": total_rows, "previewRows": len(rows)}


def read_text_preview(path: Path) -> str:
    data = path.read_bytes()[:MAX_TEXT_BYTES]
    return data.decode("utf-8", "replace")


def file_meta(path: Path) -> dict[str, Any]:
    st = path.stat()
    suffix = path.suffix.lower()
    kind = "other"
    if suffix == ".csv":
        kind = "csv"
    elif suffix == ".json":
        kind = "json"
    elif suffix in {".html", ".htm"}:
        kind = "html"
    elif suffix in IMAGE_EXTENSIONS:
        kind = "image"
    elif suffix in {".txt", ".log", ".md"}:
        kind = "text"
    return {
        "path": relpath(path),
        "name": path.name,
        "kind": kind,
        "extension": suffix,
        "sizeBytes": st.st_size,
        "sizeLabel": format_bytes(st.st_size),
        "modifiedAt": utc_iso(st.st_mtime),
        "url": f"/api/file?path={urllib.parse.quote(relpath(path))}",
    }


def format_bytes(n: int) -> str:
    value = float(n)
    for unit in ["B", "KiB", "MiB", "GiB"]:
        if value < 1024 or unit == "GiB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{n} B"


def collect_artifacts() -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for dirname in ARTIFACT_DIRS:
        base = ROOT / dirname
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in VIEW_EXTENSIONS:
                artifacts.append(file_meta(path))
    artifacts.sort(key=lambda x: x["modifiedAt"], reverse=True)
    return artifacts


def csv_metric_map(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    return {"path": relpath(path), "rows": rows, "updatedAt": utc_iso(path.stat().st_mtime)}


def load_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "path": relpath(path)}


def to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def max_drawdown_pct(equity_values: list[float]) -> float | None:
    if not equity_values:
        return None
    peak = equity_values[0]
    max_dd = 0.0
    for value in equity_values:
        peak = max(peak, value)
        if peak:
            max_dd = min(max_dd, (value / peak - 1.0) * 100.0)
    return max_dd


def sliding_walk_forward_summary(run_info: Any | None) -> dict[str, Any] | None:
    summary_path = ROOT / "models" / "sliding_walk_forward_summary.csv"
    if not summary_path.exists():
        return None
    metric_block = csv_metric_map(summary_path)
    rows = metric_block.get("rows", []) if isinstance(metric_block, dict) else []
    if not rows:
        return {"status": "empty", "path": relpath(summary_path)}

    fold_count = len(rows)
    returns = [to_float(row.get("test_return_pct")) for row in rows]
    pfs = [to_float(row.get("test_profit_factor")) for row in rows]
    drawdowns = [to_float(row.get("test_max_dd_pct")) for row in rows]
    sharpes = [to_float(row.get("test_sharpe")) for row in rows]
    trades = [to_float(row.get("test_n_trades")) for row in rows]

    equity_path = ROOT / "models" / "sliding_oos_equity.csv"
    equity_values: list[float] = []
    equity_first_time = None
    equity_last_time = None
    if equity_path.exists():
        try:
            with equity_path.open(newline="", encoding="utf-8", errors="replace") as f:
                for row in csv.DictReader(f):
                    equity = to_float(row.get("equity"))
                    if equity is None:
                        continue
                    if equity_first_time is None:
                        equity_first_time = row.get("time")
                    equity_last_time = row.get("time")
                    equity_values.append(equity)
        except Exception:  # noqa: BLE001 - summary should not break dashboard
            equity_values = []

    stitched_return = None
    if len(equity_values) >= 2 and equity_values[0]:
        stitched_return = (equity_values[-1] / equity_values[0] - 1.0) * 100.0

    gate_passed = None
    promoted_from_fold = None
    if isinstance(run_info, dict):
        gate_passed = run_info.get("gate_passed")
        promoted_from_fold = run_info.get("promoted_from_fold")

    return {
        "status": "complete",
        "path": relpath(summary_path),
        "foldCount": fold_count,
        "positiveReturnFolds": sum(1 for value in returns if value is not None and value > 0),
        "profitFactorGtOneFolds": sum(1 for value in pfs if value is not None and value > 1),
        "testStart": rows[0].get("test_start"),
        "testEnd": rows[-1].get("test_end"),
        "worstReturnPct": min((value for value in returns if value is not None), default=None),
        "worstProfitFactor": min((value for value in pfs if value is not None), default=None),
        "worstMaxDrawdownPct": min((value for value in drawdowns if value is not None), default=None),
        "meanSharpe": (
            sum(value for value in sharpes if value is not None)
            / len([value for value in sharpes if value is not None])
            if any(value is not None for value in sharpes)
            else None
        ),
        "totalTrades": sum(value for value in trades if value is not None),
        "stitchedOos": {
            "path": relpath(equity_path) if equity_path.exists() else None,
            "rows": len(equity_values),
            "firstTime": equity_first_time,
            "lastTime": equity_last_time,
            "totalReturnPct": stitched_return,
            "maxDrawdownPct": max_drawdown_pct(equity_values),
        },
        "gatePassed": gate_passed,
        "promotedFromFold": promoted_from_fold,
    }


def status_payload() -> dict[str, Any]:
    artifacts = collect_artifacts()
    models_dir = ROOT / "models"
    outputs_dir = ROOT / "outputs"
    no_deploy = ROOT / "models" / "NO_DEPLOY.txt"
    run_info = load_json(ROOT / "models" / "run_info.json")
    gate_status = "pending"
    if no_deploy.exists():
        gate_status = "blocked"
    elif isinstance(run_info, dict) and run_info.get("gate_passed") is True:
        gate_status = "passed"
    elif isinstance(run_info, dict) and run_info.get("gate_passed") is False:
        gate_status = "failed"
    elif run_info:
        gate_status = "passed_or_pending"
    latest_model = None
    model_files = sorted(models_dir.rglob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True) if models_dir.exists() else []
    if model_files:
        latest_model = file_meta(model_files[0])
    return {
        "projectRoot": str(ROOT),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "hasOutputs": outputs_dir.exists(),
        "hasModels": models_dir.exists(),
        "gate": {
            "status": gate_status,
            "noDeployPath": relpath(no_deploy) if no_deploy.exists() else None,
            "message": read_text_preview(no_deploy) if no_deploy.exists() else None,
        },
        "runInfo": run_info,
        "latestModel": latest_model,
        "summary": {
            "slidingWalkForward": sliding_walk_forward_summary(run_info),
            "sealedHoldout": {
                "status": "not_revealed" if not (ROOT / "outputs" / "final_holdout" / "holdout_report.csv").exists() else "revealed",
                "reportPath": "outputs/final_holdout/holdout_report.csv" if (ROOT / "outputs" / "final_holdout" / "holdout_report.csv").exists() else None,
            },
        },
        "artifactCount": len(artifacts),
        "artifacts": artifacts,
        "metrics": {
            "performanceReport": csv_metric_map(ROOT / "outputs" / "performance_report.csv"),
            "selectedPolicy": csv_metric_map(ROOT / "outputs" / "selected_policy.csv"),
            "walkForwardBaseline": csv_metric_map(ROOT / "outputs" / "walk_forward_baseline.csv"),
            "slidingWalkForwardSummary": csv_metric_map(ROOT / "models" / "sliding_walk_forward_summary.csv"),
        },
    }


@dataclass
class DashboardConfig:
    web_root: Path


class DashboardHandler(SimpleHTTPRequestHandler):
    config: DashboardConfig

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib override name
        print(f"[{self.log_date_time_string()}] {format % args}")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/status":
            return self.send_json(status_payload())
        if parsed.path == "/api/file":
            params = urllib.parse.parse_qs(parsed.query)
            target = params.get("path", [""])[0]
            return self.send_artifact(target)
        if parsed.path == "/api/preview":
            params = urllib.parse.parse_qs(parsed.query)
            target = params.get("path", [""])[0]
            return self.send_preview(target)
        return self.serve_static(parsed.path)

    def send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_error_json(self, status: HTTPStatus, message: str) -> None:
        self.send_json({"error": message, "status": status.value}, status)

    def send_artifact(self, raw_path: str) -> None:
        try:
            path = safe_artifact_path(raw_path)
        except FileNotFoundError as exc:
            return self.send_error_json(HTTPStatus.NOT_FOUND, str(exc))
        except ValueError as exc:
            return self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if path.suffix.lower() in {".html", ".htm"}:
            self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: https:; img-src 'self' data: blob: https:;")
        self.end_headers()
        self.wfile.write(data)

    def send_preview(self, raw_path: str) -> None:
        try:
            path = safe_artifact_path(raw_path)
        except FileNotFoundError as exc:
            return self.send_error_json(HTTPStatus.NOT_FOUND, str(exc))
        except ValueError as exc:
            return self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
        suffix = path.suffix.lower()
        try:
            if suffix == ".csv":
                return self.send_json({"meta": file_meta(path), "csv": read_csv_preview(path)})
            if suffix == ".json":
                return self.send_json({"meta": file_meta(path), "json": load_json(path)})
            if suffix in TEXT_EXTENSIONS:
                return self.send_json({"meta": file_meta(path), "text": read_text_preview(path)})
            return self.send_json({"meta": file_meta(path)})
        except Exception as exc:  # noqa: BLE001
            return self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def serve_static(self, path: str) -> None:
        web_root = self.config.web_root
        if path in ("", "/"):
            path = "/index.html"
        requested = (web_root / path.lstrip("/")).resolve()
        if not requested.exists() or not requested.is_file() or web_root.resolve() not in requested.parents and requested != web_root.resolve():
            requested = web_root / "index.html"
        if not requested.exists():
            return self.send_error_json(
                HTTPStatus.NOT_FOUND,
                "Dashboard build not found. Run: cd dashboard && npm install && npm run build",
            )
        ctype = mimetypes.guess_type(requested.name)[0] or "application/octet-stream"
        data = requested.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=5180)
    ap.add_argument("--web-root", type=Path, default=DEFAULT_WEB_ROOT)
    args = ap.parse_args(argv)

    handler = DashboardHandler
    handler.config = DashboardConfig(web_root=args.web_root.resolve())
    httpd = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Dashboard API serving {ROOT} at http://{args.host}:{args.port}")
    print(f"Web root: {handler.config.web_root}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
