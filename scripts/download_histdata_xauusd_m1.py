#!/usr/bin/env python3
"""Download HistData XAUUSD yearly M1 ASCII zip files and convert to project CSV.

HistData ASCII rows look like:
    YYYYMMDD HHMMSS;Open;High;Low;Close;Volume

Output contract for this repository:
    Time (EET),Open,High,Low,Close,Volume

Note: HistData timestamps are treated as broker/EET-style naive timestamps for
pipeline compatibility. This is a fast pipeline-enablement source; Dukascopy
Bid/Ask tick conversion remains the cleaner source when exact Bid/Ask/spread is
needed.
"""
from __future__ import annotations

import argparse
import csv
import http.cookiejar
import re
from pathlib import Path
import urllib.parse
import urllib.request
import zipfile

BASE = "https://www.histdata.com"
PAIR = "XAUUSD"


def opener():
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def get_form_fields(op, year: int) -> dict[str, str]:
    page = f"{BASE}/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{PAIR}/{year}"
    req = urllib.request.Request(page, headers={"User-Agent": "Mozilla/5.0"})
    html = op.open(req, timeout=45).read().decode("utf-8", "ignore")
    fields = {}
    for name in ["tk", "date", "datemonth", "platform", "timeframe", "fxpair"]:
        m = re.search(rf'name="{name}"[^>]+value="([^"]*)"', html)
        if not m:
            raise RuntimeError(f"Could not find form field {name!r} for {year}")
        fields[name] = m.group(1)
    return fields


def download_year(year: int, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"HISTDATA_COM_ASCII_{PAIR}_M1_{year}.zip"
    if out.exists() and out.stat().st_size > 0:
        return out
    op = opener()
    fields = get_form_fields(op, year)
    page = f"{BASE}/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{PAIR}/{year}"
    body = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(
        f"{BASE}/get.php",
        data=body,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": page,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    data = op.open(req, timeout=180).read()
    if not data.startswith(b"PK"):
        raise RuntimeError(f"Download for {year} did not return a zip; bytes={len(data)}")
    out.write_bytes(data)
    return out


def iter_histdata_rows(zip_path: Path):
    with zipfile.ZipFile(zip_path) as z:
        csv_names = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise RuntimeError(f"No CSV in {zip_path}")
        with z.open(csv_names[0]) as f:
            for raw in f:
                line = raw.decode("ascii", "ignore").strip()
                if not line:
                    continue
                parts = line.split(";")
                if len(parts) < 6:
                    continue
                stamp = parts[0]
                # 20240101 180000 -> 2024.01.01 18:00:00
                date, tod = stamp.split()
                t = f"{date[:4]}.{date[4:6]}.{date[6:8]} {tod[:2]}:{tod[2:4]}:{tod[4:6]}"
                yield [t, parts[1], parts[2], parts[3], parts[4], parts[5]]


def convert(years: list[int], zip_dir: Path, out_csv: Path) -> dict:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_csv.with_suffix(out_csv.suffix + ".tmp")
    rows = 0
    first = None
    last = None
    with tmp.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Time (EET)", "Open", "High", "Low", "Close", "Volume"])
        last_ts = None
        for year in years:
            zp = zip_dir / f"HISTDATA_COM_ASCII_{PAIR}_M1_{year}.zip"
            for row in iter_histdata_rows(zp):
                ts = row[0]
                # remove exact duplicate boundary rows if any
                if ts == last_ts:
                    continue
                w.writerow(row)
                rows += 1
                first = first or ts
                last = ts
                last_ts = ts
    tmp.replace(out_csv)
    return {"rows": rows, "first": first, "last": last, "out_csv": str(out_csv)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-year", type=int, required=True)
    ap.add_argument("--end-year", type=int, required=True, help="inclusive")
    ap.add_argument("--zip-dir", type=Path, default=Path("data/histdata_zips"))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    years = list(range(args.start_year, args.end_year + 1))
    for year in years:
        p = download_year(year, args.zip_dir)
        print(f"downloaded {year}: {p} {p.stat().st_size:,} bytes", flush=True)
    stats = convert(years, args.zip_dir, args.out)
    print("convert_done")
    for k, v in stats.items():
        print(f"{k}={v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
