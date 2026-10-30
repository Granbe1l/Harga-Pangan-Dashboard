#!/usr/bin/env python3
"""Generate Excel + factual JSON/Markdown summaries offline, from any cwd."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from analyst.reporting import build_summary, summary_markdown, workbook_bytes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--province", default="Jawa Barat")
    parser.add_argument("--as-of", default=None, help="Bulan laporan YYYY-MM; default bulan terakhir dalam data")
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--threshold", type=float, default=10)
    parser.add_argument("--commodity", default="Beras Medium")
    parser.add_argument("--minimum-coverage",type=float,default=80)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports")
    args = parser.parse_args()
    path = ROOT / "data" / "processed" / "prices.csv"
    if not path.exists():
        parser.error("Data bersih belum ada. Jalankan python scripts/prepare_data.py terlebih dahulu.")
    frame = pd.read_csv(path, dtype={"province_code": str, "source_province_code": str}, parse_dates=["date"])
    if args.province not in set(frame["province"]):
        parser.error("Provinsi tidak ditemukan dalam data bersih.")
    summary = build_summary(frame, args.province, args.as_of, args.months, args.threshold,args.minimum_coverage)
    report = workbook_bytes(frame, args.province, args.as_of, args.months, threshold_pct=args.threshold, commodity=args.commodity,minimum_coverage=args.minimum_coverage)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "harga_pangan_report.xlsx").write_bytes(report)
    (args.output_dir / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (args.output_dir / "analysis_summary.md").write_text(summary_markdown(summary), encoding="utf-8")
    print(f"Laporan dibuat: {args.output_dir.resolve()}")
    print(f"Pilihan: {args.province}, {summary['as_of'][:7]}, {args.months} bulan; {summary['snapshot']['observed_commodities']} komoditas teramati.")


if __name__ == "__main__":
    main()
