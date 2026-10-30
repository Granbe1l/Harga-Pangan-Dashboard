"""Stage primary-source files without relabeling the bundled mirror or guessing units."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

LANDING_URL = "https://data.badanpangan.go.id/datasetpublications/178/rata-rata-harga-pangan-bulanan-konsumen-provinsi"


def official_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (host == "badanpangan.go.id" or host.endswith(".badanpangan.go.id")) and not parsed.username and not parsed.password and parsed.port in (None,443)


class DownloadLinks(HTMLParser):
    def __init__(self, base):
        super().__init__();self.base=base;self.links=[]

    def handle_starttag(self, tag, attributes):
        if tag != "a": return
        attrs=dict(attributes)
        url=urljoin(self.base,attrs.get("href",""))
        if official_url(url) and urlparse(url).path.lower().endswith((".csv",".xlsx",".xls",".json")):
            self.links.append(url)


def fetch_official(url: str, timeout: int = 30):
    if not official_url(url):
        raise ValueError("Unduhan otomatis hanya menerima HTTPS domain Badan Pangan Nasional.")
    request = Request(url,headers={"User-Agent":"Analyst-Primary-Data-Verification/1.0"})
    # Standard urllib inherits the configured proxy and CA trust; verification stays enabled.
    with urlopen(request,timeout=timeout) as response:
        final = response.geturl()
        if not official_url(final):
            raise ValueError("Redirect keluar domain primer; periksa tautan dan izin akses terlebih dahulu.")
        payload=response.read(32*1024*1024+1)
        if len(payload)>32*1024*1024:
            raise ValueError("File melebihi batas 32 MiB untuk inspeksi ini.")
        return payload,final,response.headers.get("Content-Type","")


def stage_download(url: str, output: Path) -> Path:
    payload,final,content_type=fetch_official(url)
    if "html" in content_type.lower() or payload.lstrip().lower().startswith((b"<!doctype html",b"<html")):
        raise ValueError("URL mengembalikan halaman HTML, bukan file data. Gunakan URL unduhan resmi.")
    suffix=Path(urlparse(final).path).suffix.lower()
    if suffix not in {".csv",".xlsx",".xls",".json"}:
        suffix=".bin"
    digest=hashlib.sha256(payload).hexdigest()
    output.mkdir(parents=True,exist_ok=True)
    path=output/("primary-"+digest[:16]+suffix)
    receipt=path.with_suffix(path.suffix+".receipt.json")
    if path.exists() and path.read_bytes()!=payload:
        raise ValueError("Nama staging sudah ada dengan isi berbeda; file tidak ditimpa.")
    path.write_bytes(payload)
    receipt.write_text(json.dumps({"landing_url":LANDING_URL,"requested_url":url,"final_url":final,
        "retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"raw_sha256":digest,"raw_bytes":len(payload),
        "acquisition":"direct_https_from_primary_domain","content_type":content_type,
        "scope":"Bukti jalur pengambilan file; bukan bukti satuan, lisensi, atau ketepatan setiap observasi."},ensure_ascii=False,indent=2)+'\n')
    return path


def inspect_landing(output: Path):
    payload,final,content_type=fetch_official(LANDING_URL)
    output.mkdir(parents=True,exist_ok=True)
    (output/"landing.html").write_bytes(payload)
    parser=DownloadLinks(final);parser.feed(payload.decode("utf-8",errors="replace"))
    result={"url":final,"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"sha256":hashlib.sha256(payload).hexdigest(),
        "content_type":content_type,"download_candidates":list(dict.fromkeys(parser.links)),
        "note":"Jika daftar kosong, inspeksi halaman/API resmi diperlukan. Tidak ada file mirror yang diganti label."}
    (output/"landing-inspection.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


def read_source(path: Path, *, sheet_name=0, delimiter=",", decimal=".", thousands=None):
    if path.suffix.lower()==".xlsx":
        return pd.read_excel(path,sheet_name=sheet_name,dtype=object)
    if path.suffix.lower()==".csv":
        return pd.read_csv(path,sep=delimiter,dtype=str,encoding="utf-8-sig")
    raise ValueError("Normalisasi saat ini mendukung CSV UTF-8 dan XLSX; format lain perlu adapter yang diperiksa.")


def normalize_primary(frame: pd.DataFrame, mapping: dict, *, date_format="%Y-%m-%d", decimal=".", thousands=None):
    required={"province","commodity","date","price"}
    if not required.issubset(mapping):
        raise ValueError("Mapping wajib menyebut province, commodity, date, dan price dari header file yang sebenarnya.")
    if any(column not in frame.columns for column in mapping.values()):
        raise ValueError("Mapping merujuk kolom yang tidak ada; header tidak ditebak otomatis.")
    result=pd.DataFrame({key:frame[column] for key,column in mapping.items()}).copy()
    for key in ["province","commodity"]:
        result[key]=result[key].fillna("").astype(str).str.replace(r"\s+"," ",regex=True).str.strip()
    result["date"]=pd.to_datetime(result["date"],format=date_format,errors="coerce").dt.to_period("M").dt.to_timestamp()
    # Separators are explicit settings rather than guessed from an ambiguous price string.
    original_prices=result["price"].copy()
    native=original_prices.map(lambda value:isinstance(value,(int,float,np.integer,np.floating)) and not isinstance(value,(bool,np.bool_)))
    prices=original_prices.astype(str).str.strip()
    if thousands:prices=prices.str.replace(thousands,"",regex=False)
    if decimal!=".":prices=prices.str.replace(decimal,".",regex=False)
    result["price"]=pd.to_numeric(prices,errors="coerce").astype(float)
    result.loc[native,"price"]=pd.to_numeric(original_prices.loc[native],errors="coerce")
    result["unit"]=result["unit"].fillna("").astype(str).str.strip() if "unit" in result else ""
    result["unit_status"]=result["unit"].map(lambda u:"Dilaporkan pada file primer; definisi perlu ditinjau" if u else "Tidak tersedia; jangan diasumsikan kg/liter")
    bad_keys=result.province.eq("")|result.commodity.eq("")|result.date.isna()
    bad_price=~np.isfinite(result.price.to_numpy(dtype=float))|result.price.le(0)
    result["rejection_reason"]=pd.NA
    result.loc[bad_keys,"rejection_reason"]="invalid_key_or_date"
    result.loc[~bad_keys & bad_price,"rejection_reason"]="invalid_or_nonpositive_price"
    keys=["province","commodity","date"]
    valid=result[result.rejection_reason.isna()].drop_duplicates(subset=keys+["price","unit"])
    conflicting=valid.duplicated(keys,keep=False)
    conflicts=valid.loc[conflicting].copy();conflicts["rejection_reason"]="conflicting_duplicate"
    clean=valid.loc[~conflicting].drop(columns="rejection_reason").reset_index(drop=True)
    parts=[part for part in [result[result.rejection_reason.notna()],conflicts] if not part.empty]
    rejected=pd.concat(parts,ignore_index=True) if parts else result.iloc[:0].copy()
    report={"input_rows":len(frame),"clean_rows":len(clean),"rejected_rows":len(rejected),
        "exact_duplicates_removed":int(len(result[result.rejection_reason.isna()])-len(valid)),
        "units_missing":int(clean.unit.eq("").sum()),"primary_unit_definitions_verified":False,
        "scope":"Normalisasi di staging. Belum menjadi dataset aktif; tidak ada pengisian harga atau asumsi satuan."}
    return clean,rejected,report


def stage_normalized(path: Path, mapping_path: Path, output: Path, *, date_format="%Y-%m-%d", delimiter=",", decimal=".", thousands=None):
    config=json.loads(mapping_path.read_text())
    frame=read_source(path,delimiter=delimiter,decimal=decimal,thousands=thousands)
    clean,rejected,report=normalize_primary(frame,config,date_format=date_format,decimal=decimal,thousands=thousands)
    if clean.empty:raise ValueError("Tidak ada observasi valid; dataset aktif tidak diubah.")
    output.mkdir(parents=True,exist_ok=True)
    for name in ["prices.csv","rejected.csv","normalization.json"]:
        if (output/name).exists():raise ValueError("Direktori staging sudah berisi hasil; gunakan direktori baru agar bukti lama tidak tertimpa.")
    receipt_path=path.with_suffix(path.suffix+".receipt.json")
    receipt=json.loads(receipt_path.read_text()) if receipt_path.exists() else None
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if receipt and receipt.get("raw_sha256")!=digest:raise ValueError("Checksum file tidak cocok dengan bukti unduhan.")
    clean.to_csv(output/"prices.csv",index=False);rejected.to_csv(output/"rejected.csv",index=False)
    report.update({"raw_sha256":digest,"column_mapping":config,"acquisition_receipt":receipt,
        "acquisition_status":"Receipt unduhan primer cocok" if receipt else "File lokal; asal unduhan belum dibuktikan"})
    (output/"normalization.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report
