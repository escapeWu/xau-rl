#!/usr/bin/env python3
"""Download Dukascopy XAUUSD tick .bi5 files and aggregate to MT4-style M1 CSV.

Output contract for this repository:
    Time (EET),Open,High,Low,Close,Volume

Dukascopy .bi5 tick record layout is 20 bytes, big-endian:
    ms_from_hour: int32
    ask: int32
    bid: int32
    ask_volume: float32
    bid_volume: float32

For XAUUSD Dukascopy prices are scaled by 1000 in the raw tick integers.
The default output uses Bid OHLC and sums bid_volume as Volume.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import datetime as dt
import io
import lzma
import os
from pathlib import Path
import struct
import sys
import time
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

SYMBOL = "XAUUSD"
BASE_URL = "https://datafeed.dukascopy.com/datafeed"
PRICE_SCALE = 1000.0
RECORD = struct.Struct(">IIIff")
UTC = ZoneInfo("UTC")
EET = ZoneInfo("Europe/Helsinki")


def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def iter_hours(start: dt.date, end: dt.date):
    """Yield UTC hour datetimes for [start, end)."""
    cur = dt.datetime.combine(start, dt.time(0, 0), tzinfo=UTC)
    stop = dt.datetime.combine(end, dt.time(0, 0), tzinfo=UTC)
    one = dt.timedelta(hours=1)
    while cur < stop:
        yield cur
        cur += one


def is_probable_trading_hour(hour_utc: dt.datetime) -> bool:
    """Skip most weekend/maintenance hours to avoid needless 404s.

    XAUUSD generally trades from Sunday evening UTC to Friday evening UTC with
    a short daily maintenance break. The filter is intentionally permissive:
    if an hour might trade, we request it.
    """
    wd = hour_utc.weekday()  # Monday=0
    h = hour_utc.hour
    if wd == 5:  # Saturday
        return False
    if wd == 6 and h < 20:  # Sunday before typical reopen
        return False
    if wd == 4 and h >= 22:  # Friday after typical close
        return False
    return True


def dukascopy_url(symbol: str, hour_utc: dt.datetime) -> str:
    # Dukascopy path uses zero-based month.
    return (
        f"{BASE_URL}/{symbol}/{hour_utc.year}/"
        f"{hour_utc.month - 1:02d}/{hour_utc.day:02d}/{hour_utc.hour:02d}h_ticks.bi5"
    )


def bi5_path(root: Path, symbol: str, hour_utc: dt.datetime) -> Path:
    return (
        root / symbol / f"{hour_utc.year}" / f"{hour_utc.month - 1:02d}" /
        f"{hour_utc.day:02d}" / f"{hour_utc.hour:02d}h_ticks.bi5"
    )


def download_one(args) -> tuple[str, int, str]:
    symbol, root, hour_iso, retries, timeout = args
    hour_utc = dt.datetime.fromisoformat(hour_iso)
    out = bi5_path(root, symbol, hour_utc)
    if out.exists() and out.stat().st_size > 0:
        return (hour_iso, out.stat().st_size, "cached")

    out.parent.mkdir(parents=True, exist_ok=True)
    url = dukascopy_url(symbol, hour_utc)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    last_err = ""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            if not data:
                return (hour_iso, 0, "empty")
            tmp = out.with_suffix(out.suffix + ".tmp")
            tmp.write_bytes(data)
            tmp.replace(out)
            return (hour_iso, len(data), "downloaded")
        except urllib.error.HTTPError as e:
            if e.code in (404, 403):
                return (hour_iso, 0, f"http_{e.code}")
            last_err = f"http_{e.code}"
        except Exception as e:  # noqa: BLE001 - downloader should continue
            last_err = f"{type(e).__name__}:{str(e)[:120]}"
        if attempt < retries:
            time.sleep(0.5 * (2 ** attempt))
    return (hour_iso, 0, "error:" + last_err)


def parse_bi5_ticks(path: Path, hour_utc: dt.datetime, side: str):
    try:
        raw = lzma.decompress(path.read_bytes(), format=lzma.FORMAT_ALONE)
    except Exception:
        return
    base_ms = int(hour_utc.timestamp() * 1000)
    n = len(raw) // RECORD.size
    for i in range(n):
        ms, ask_i, bid_i, ask_vol, bid_vol = RECORD.unpack_from(raw, i * RECORD.size)
        ts_utc = dt.datetime.fromtimestamp((base_ms + ms) / 1000.0, tz=UTC)
        if side == "bid":
            price = bid_i / PRICE_SCALE
            vol = float(bid_vol)
        elif side == "ask":
            price = ask_i / PRICE_SCALE
            vol = float(ask_vol)
        else:
            price = (bid_i + ask_i) / (2.0 * PRICE_SCALE)
            vol = float(bid_vol + ask_vol) / 2.0
        yield ts_utc.astimezone(EET), price, vol


def aggregate_hours_to_m1(symbol: str, root: Path, hours: list[dt.datetime], out_csv: Path, side: str) -> dict:
    """Stream aggregate tick files into M1 OHLCV CSV.

    Keeps only one minute bucket in memory because ticks are chronological by hour.
    Output timestamp is candle OPEN time in EET/EEST, matching ProjectConfig
    timestamp_is_bar_open=True.
    """
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_csv.with_suffix(out_csv.suffix + ".tmp")
    rows = 0
    ticks = 0
    files = 0
    first_ts = None
    last_ts = None
    current_minute = None
    bucket = None

    def flush(writer):
        nonlocal rows, bucket, current_minute
        if bucket is None or current_minute is None:
            return
        writer.writerow([
            current_minute.strftime("%Y.%m.%d %H:%M:%S"),
            f"{bucket['open']:.3f}",
            f"{bucket['high']:.3f}",
            f"{bucket['low']:.3f}",
            f"{bucket['close']:.3f}",
            f"{bucket['volume']:.6f}",
        ])
        rows += 1

    with tmp.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Time (EET)", "Open", "High", "Low", "Close", "Volume"])
        for hour in hours:
            p = bi5_path(root, symbol, hour)
            if not p.exists() or p.stat().st_size == 0:
                continue
            files += 1
            for ts_eet, price, vol in parse_bi5_ticks(p, hour, side) or []:
                ticks += 1
                minute = ts_eet.replace(second=0, microsecond=0)
                if first_ts is None:
                    first_ts = minute
                last_ts = minute
                if current_minute != minute or bucket is None:
                    flush(writer)
                    current_minute = minute
                    bucket = {"open": price, "high": price, "low": price, "close": price, "volume": vol}
                else:
                    bucket["high"] = max(bucket["high"], price)
                    bucket["low"] = min(bucket["low"], price)
                    bucket["close"] = price
                    bucket["volume"] += vol
        flush(writer)
    tmp.replace(out_csv)
    return {
        "rows": rows,
        "ticks": ticks,
        "files": files,
        "first": str(first_ts) if first_ts else None,
        "last": str(last_ts) if last_ts else None,
        "out_csv": str(out_csv),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default=SYMBOL)
    ap.add_argument("--start", required=True, help="inclusive UTC date YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="exclusive UTC date YYYY-MM-DD")
    ap.add_argument("--cache-dir", type=Path, default=Path("data/dukascopy_bi5"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--side", choices=["bid", "ask", "mid"], default="bid")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--skip-download", action="store_true")
    ap.add_argument("--no-trading-hour-filter", action="store_true")
    ap.add_argument("--max-hours", type=int, default=None, help="debug: limit hours")
    args = ap.parse_args(argv)

    start = parse_date(args.start)
    end = parse_date(args.end)
    if end <= start:
        raise SystemExit("--end must be after --start")
    hours = list(iter_hours(start, end))
    if not args.no_trading_hour_filter:
        hours = [h for h in hours if is_probable_trading_hour(h)]
    if args.max_hours is not None:
        hours = hours[: args.max_hours]

    print(f"symbol={args.symbol} start={args.start} end={args.end} hours={len(hours):,} side={args.side}", flush=True)
    print(f"cache_dir={args.cache_dir} out={args.out}", flush=True)

    if not args.skip_download:
        tasks = [(args.symbol, args.cache_dir, h.isoformat(), args.retries, args.timeout) for h in hours]
        counts: dict[str, int] = {}
        bytes_total = 0
        done = 0
        with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = [ex.submit(download_one, t) for t in tasks]
            for fut in cf.as_completed(futs):
                _hour, nbytes, status = fut.result()
                done += 1
                bytes_total += nbytes
                key = status.split(":", 1)[0]
                counts[key] = counts.get(key, 0) + 1
                if done % 500 == 0 or done == len(tasks):
                    print(f"download_progress {done:,}/{len(tasks):,} bytes={bytes_total:,} counts={counts}", flush=True)
        print(f"download_done bytes={bytes_total:,} counts={counts}", flush=True)

    stats = aggregate_hours_to_m1(args.symbol, args.cache_dir, hours, args.out, args.side)
    print("aggregate_done")
    for k, v in stats.items():
        print(f"{k}={v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
