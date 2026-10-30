"""Auditable preparation of the public monthly food-price snapshot.

No prices are imputed. A source code is not a stable geographic identifier:
the source switches its Papua code/coverage scheme in January 2024. We keep
the two pre-switch series separate instead of constructing an artificial trend.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any
import urllib.request

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://raw.githubusercontent.com/achmadichzan/Prediksi_Harga_Pangan_Nasional/main/harga_pangan.csv"
ORIGINAL_URL = "https://data.badanpangan.go.id/datasetpublications/178/rata-rata-harga-pangan-bulanan-konsumen-provinsi"
MONTHS = {name: index for index, name in enumerate(
    ("januari", "februari", "maret", "april", "mei", "juni", "juli", "agustus", "september", "oktober", "november", "desember"), 1)}
SOURCE_COLUMNS = ("Kode Provinsi", "Nama Provinsi", "Komoditas", "Tahun", "Bulan", "Harga")
CLEAN_COLUMNS = ("province_code", "province", "commodity", "date", "price", "unit", "source_province_code", "geography_note", "unit_assumed")
UNIT_NOTE = "Satuan kg/liter merupakan asumsi kerja menurut jenis komoditas, tidak tersedia dalam CSV sumber; verifikasi sebelum penggunaan operasional."
GEOGRAPHY_NOTE = "Skema wilayah Papua pada snapshot berubah mulai 2024. Seri sebelum perubahan dipisahkan; bukan rekonstruksi batas administratif."


def normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def parse_price(value: Any) -> float | None:
    """Parse whole rupiah; commas/dots must be groups of three, not decimals."""
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) and number.is_integer() else None
    text = normalize_text(value)
    text = re.sub(r"^Rp\s*", "", text, flags=re.I)
    if not re.fullmatch(r"-?(?:\d+|\d{1,3}(?:,\d{3})+|\d{1,3}(?:\.\d{3})+)", text):
        return None
    return float(text.replace(",", "").replace(".", ""))


def parse_month(year: Any, month: Any) -> pd.Timestamp | None:
    try:
        year_text = normalize_text(year)
        if not re.fullmatch(r"\d{4}", year_text):
            return None
        month_number = MONTHS.get(normalize_text(month).casefold())
        if not month_number:
            return None
        return pd.Timestamp(year=int(year_text), month=month_number, day=1)
    except (ValueError, OverflowError):
        return None


def normalize_province(code: Any, name: Any, date: pd.Timestamp) -> tuple[str, str, str]:
    """Return stable internal ID, display name, and geography caveat."""
    source_code = normalize_text(code)
    if re.fullmatch(r"\d+(?:\.0)?", source_code):
        source_code = str(int(float(source_code))).zfill(2)
    province = normalize_text(name)
    if province.casefold().replace(".", "").replace(" ", "") == "diyogyakarta":
        province = "DI Yogyakarta"
    if date < pd.Timestamp("2024-01-01") and province in {"Papua", "Papua Barat"}:
        identifier = "PAPUA_HIST" if province == "Papua" else "PAPUA_BARAT_HIST"
        return identifier, f"{province} (seri historis)", GEOGRAPHY_NOTE
    # Use a name-based internal ID for Papua to avoid the source code changing
    # the identity of a time series. Preserve raw codes in a separate column.
    papua_codes = {"Papua": "91", "Papua Barat": "92", "Papua Selatan": "93", "Papua Tengah": "94", "Papua Pegunungan": "95", "Papua Barat Daya": "96"}
    if province in papua_codes:
        source_code = papua_codes[province]
    return source_code, province, GEOGRAPHY_NOTE if province.startswith("Papua") else ""


def inferred_unit(commodity: str) -> str:
    return "liter" if commodity.casefold().startswith("minyak") else "kg"


def clean_source(source: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Clean a source-shaped frame and return prices, rejected rows, quality report."""
    missing_columns = sorted(set(SOURCE_COLUMNS).difference(source.columns))
    if missing_columns:
        raise ValueError(f"Kolom sumber tidak lengkap: {', '.join(missing_columns)}")
    rows: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    whitespace_changes = 0
    national_codes = {"0", "00", "000", "99", "999"}
    for offset, (_, raw) in enumerate(source.iterrows(), start=int(source.attrs.get("source_row_start", 2))):
        original = {column: None if pd.isna(raw[column]) else str(raw[column]) for column in SOURCE_COLUMNS}
        record = {column: normalize_text(raw[column]) for column in SOURCE_COLUMNS}
        whitespace_changes += sum(original[c] is not None and original[c] != record[c] for c in SOURCE_COLUMNS)
        reason = None
        source_code = record["Kode Provinsi"]
        if source_code in national_codes or record["Nama Provinsi"].casefold() in {"indonesia", "nasional", "rata-rata nasional"}:
            reason = "national_aggregate"
        date = parse_month(record["Tahun"], record["Bulan"])
        if not reason and date is None:
            reason = "invalid_period"
        if not reason and (not source_code or not record["Nama Provinsi"] or not record["Komoditas"]):
            reason = "missing_identifier"
        price = parse_price(raw["Harga"])
        if not reason and price is None:
            reason = "missing_price" if record["Harga"] in {"", "-", "—", "N/A", "NA"} else "invalid_price"
        if not reason and price <= 0:
            reason = "non_positive_price"
        if reason:
            rejected.append({"source_row": offset, **original, "reason": reason})
            continue
        province_code, province, geography_note = normalize_province(source_code, record["Nama Provinsi"], date)
        rows.append({"province_code": province_code, "province": province, "commodity": record["Komoditas"], "date": date,
                     "price": price, "unit": inferred_unit(record["Komoditas"]), "source_province_code": source_code,
                     "geography_note": geography_note, "unit_assumed": True, "_source_row": offset, "_original": original})
    frame = pd.DataFrame(rows)
    keys = ["province_code", "commodity", "date"]
    duplicate_count = 0
    conflict_count = 0
    keep: list[dict[str, Any]] = []
    if not frame.empty:
        for _, group in frame.groupby(keys, sort=False, dropna=False):
            if group["price"].nunique() > 1:
                conflict_count += len(group)
                for record in group.to_dict("records"):
                    rejected.append({"source_row": record["_source_row"], **record["_original"], "reason": "conflicting_duplicate"})
                continue
            records = group.to_dict("records")
            keep.append(records[0])
            for record in records[1:]:
                duplicate_count += 1
                rejected.append({"source_row": record["_source_row"], **record["_original"], "reason": "exact_duplicate"})
    cleaned = pd.DataFrame(keep, columns=[*CLEAN_COLUMNS, "_source_row", "_original"]).loc[:, CLEAN_COLUMNS].copy()
    if not cleaned.empty:
        cleaned["date"] = pd.to_datetime(cleaned["date"])
        cleaned = cleaned.sort_values(["province", "commodity", "date"]).reset_index(drop=True)
    rejected_frame = pd.DataFrame(rejected, columns=["source_row", *SOURCE_COLUMNS, "reason"])
    counts = rejected_frame["reason"].value_counts().to_dict() if not rejected_frame.empty else {}
    expected_observations = 0
    for _, group in cleaned.groupby(["province_code", "commodity"]):
        expected_observations += len(pd.date_range(group["date"].min(), group["date"].max(), freq="MS"))
    report = {
        "raw_rows": len(source), "clean_rows": len(cleaned), "rejected_rows": len(rejected_frame),
        "exact_duplicates_removed": duplicate_count, "conflicting_rows_quarantined": conflict_count,
        "rejected_by_reason": counts, "whitespace_fields_normalized": whitespace_changes,
        "province_count": int(cleaned["province"].nunique()), "commodity_count": int(cleaned["commodity"].nunique()),
        "period_start": cleaned["date"].min().strftime("%Y-%m-%d") if not cleaned.empty else None,
        "period_end": cleaned["date"].max().strftime("%Y-%m-%d") if not cleaned.empty else None,
        "series_count": int(cleaned.groupby(["province_code", "commodity"]).ngroups),
        "expected_observations_within_series_spans": expected_observations,
        "missing_months_within_series_spans": expected_observations - len(cleaned),
        "no_imputation": True, "no_conflicting_price_averaging": True,
        "geographic_series": [
            {"province_code": code, "province": name, "source_codes": sorted(group["source_province_code"].unique().tolist()),
             "period_start": group["date"].min().strftime("%Y-%m-%d"), "period_end": group["date"].max().strftime("%Y-%m-%d"), "rows": len(group)}
            for (code, name), group in cleaned.groupby(["province_code", "province"], sort=True)
        ],
        "unit_note": UNIT_NOTE, "geography_note": GEOGRAPHY_NOTE,
        "province_note": "Jumlah seri wilayah mencakup dua seri Papua historis terpisah; bukan jumlah provinsi Indonesia pada satu waktu.",
        "normalization": ["Baca header CSV aktual; trim/collapse whitespace", "Harga rupiah bulat: pemisah ribuan koma/titik dihapus", "DI Yogyakarta diseragamkan", "Papua/Papua Barat sebelum 2024 dipisahkan dari seri pascaperubahan", "Harga kosong, tanda '-', nol/negatif, periode invalid dikarantina", "Duplikat identik dihapus; seluruh grup harga berkonflik dikarantina", "Tidak mengisi bulan atau harga yang hilang"],
    }
    return cleaned, rejected_frame, report


def read_raw(path: Path | str) -> pd.DataFrame:
    """Locate the actual CSV header while rejecting unexpected schemas."""
    text = Path(path).read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    header_line = next((i for i, line in enumerate(lines[:10]) if line.startswith("Kode Provinsi,Nama Provinsi,")), None)
    if header_line is None:
        raise ValueError("Header dataset tidak dikenali; file sumber tidak diubah.")
    frame = pd.read_csv(io.StringIO("\n".join(lines[header_line:])), dtype=str)
    frame.attrs["source_row_start"] = header_line + 2
    return frame


def prepare_data(root: Path | str | None = None, download: bool = False) -> dict[str, Any]:
    """Build CSV and report artifacts; network only when explicitly requested."""
    root = Path(root) if root is not None else ROOT
    input_config = root / "data/source_input.json"
    config = json.loads(input_config.read_text()) if input_config.exists() else {}
    primary = config.get("dataset_kind") == "primary_export_user_supplied"
    raw_path = root / config.get("raw_path", "data/raw/harga_pangan.csv")
    if primary and download:
        raise ValueError("Dataset aktif memakai ekspor primer pengguna. --download mirror dinonaktifkan; impor ulang file resmi dengan receipt yang baru.")
    receipt = None
    if primary:
        receipt = json.loads((root/config["receipt_path"]).read_text())
        evidence = next((f for f in receipt["files"] if f["path"] == config["raw_path"]), None)
        if evidence is None or hashlib.sha256(raw_path.read_bytes()).hexdigest() != evidence["sha256"]:
            raise ValueError("Hash input primer tidak sesuai receipt; artefak tidak diubah.")
        for item in receipt["files"]:
            path = root / item["path"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                raise ValueError("Hash berkas pembanding primer tidak sesuai receipt; artefak tidak diubah.")
        companion = next((root/f["path"] for f in receipt["files"] if f["format"] == "XLSX"), None)
        if companion is None:
            raise ValueError("Receipt primer memerlukan XLSX pembanding yang diterima bersama CSV.")
        csv_frame = read_raw(raw_path).fillna("").map(normalize_text)
        xlsx_frame = pd.read_excel(companion,dtype=str).fillna("").map(normalize_text)
        if not csv_frame.equals(xlsx_frame):
            raise ValueError("Isi CSV dan XLSX primer berbeda; hasil lama dipertahankan untuk diperiksa.")
    if download:
        with urllib.request.urlopen(SOURCE_URL, timeout=45) as response:
            payload = response.read()
        # Refuse to overwrite a working snapshot with a different schema.
        if b"Kode Provinsi,Nama Provinsi,Komoditas,Tahun,Bulan,Harga" not in payload[:1000]:
            raise ValueError("Skema unduhan berubah; snapshot lokal dipertahankan.")
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(payload)
    if not raw_path.exists():
        raise FileNotFoundError(f"Snapshot mentah tidak ditemukan: {raw_path}. Jalankan scripts/prepare_data.py --download.")
    cleaned, rejected, report = clean_source(read_raw(raw_path))
    if cleaned.empty:
        raise ValueError("Tidak ada harga valid; artefak lama dipertahankan.")
    output = root / "data/processed"
    output.mkdir(parents=True, exist_ok=True)
    serializable = cleaned.copy()
    serializable["date"] = serializable["date"].dt.strftime("%Y-%m-%d")
    serializable.to_csv(output / "prices.csv", index=False)
    rejected.to_csv(output / "rejected.csv", index=False)
    if primary:
        source = {
            "title":"Rata-rata Harga Pangan Bulanan Tingkat Konsumen Provinsi",
            "dataset_kind":"primary_export_user_supplied",
            "original_publisher_cited":receipt["publisher"],"original_url_cited":receipt["publication_url"],
            "acquisition_method":receipt["acquisition_method"],"active_raw_path":config["raw_path"],
            "receipt_path":config["receipt_path"],"raw_sha256":hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            "raw_bytes":raw_path.stat().st_size,"source_header":list(SOURCE_COLUMNS),
            "original_independently_verified":False,"csv_xlsx_consistency_verified":True,
            "source_verification_scope":"File primer yang disediakan pengguna; isi CSV dan XLSX cocok. Pengambilan langsung dari server BPN belum diverifikasi.",
            "license_status":"Ketentuan penggunaan ulang tidak tercantum dalam kedua file; belum terkonfirmasi.",
            "snapshot_note":"Ekspor historis yang diberikan pengguna dari publikasi BPN; bukan harga real-time atau harga pemasok.",
            "unit_note":UNIT_NOTE,"geography_note":GEOGRAPHY_NOTE,
            "snapshot_recorded_at_utc":receipt["imported_at_utc"],
        }
    else:
        source = {
            "title": "Rata-rata Harga Pangan Bulanan Tingkat Konsumen Provinsi (salinan pihak ketiga)",
            "original_publisher_cited": "Badan Pangan Nasional", "original_url_cited": ORIGINAL_URL,
            "mirror_url": SOURCE_URL,
            "mirror_repository": "https://github.com/achmadichzan/Prediksi_Harga_Pangan_Nasional",
            "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            "raw_bytes": raw_path.stat().st_size,
            "source_header": list(SOURCE_COLUMNS),
            "original_independently_verified": False,
            "license_status": "Lisensi redistribusi tidak tercantum pada snapshot; periksa sumber asal sebelum redistribusi/komersialisasi.",
            "snapshot_note": "Snapshot historis yang dibundel, bukan harga real-time atau kutipan pemasok.",
            "unit_note": UNIT_NOTE,
            "geography_note": GEOGRAPHY_NOTE,
        }
    previous_metadata = root / "data/source.json"
    old_source = json.loads(previous_metadata.read_text(encoding="utf-8")) if previous_metadata.exists() else {}
    source["snapshot_recorded_at_utc"] = source.get("snapshot_recorded_at_utc") or (old_source.get("snapshot_recorded_at_utc") if old_source.get("raw_sha256") == source["raw_sha256"] else None)
    source["snapshot_recorded_at_utc"] = source["snapshot_recorded_at_utc"] or datetime.now(timezone.utc).isoformat()
    (root / "data/source.json").write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "quality_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def load_clean_data(root: Path | str | None = None) -> pd.DataFrame:
    root = Path(root) if root is not None else ROOT
    path = root / "data/processed/prices.csv"
    if not path.exists():
        raise FileNotFoundError("Data bersih belum tersedia. Jalankan python scripts/prepare_data.py terlebih dahulu.")
    return pd.read_csv(path, dtype={"province_code": str, "source_province_code": str}, parse_dates=["date"])


def load_quality_report(root: Path | str | None = None) -> dict[str, Any]:
    root = Path(root) if root is not None else ROOT
    return json.loads((root / "data/processed/quality_report.json").read_text(encoding="utf-8"))
