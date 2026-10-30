"""Budget decisions with explicit completeness and price provenance."""
from __future__ import annotations

from copy import deepcopy
from io import BytesIO
import math

import pandas as pd
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from analyst.analytics import basket_simulation

DEFAULT_BASKET = {
    "Beras Medium": 25.0, "Daging Ayam Ras": 10.0, "Telur Ayam Ras": 5.0,
    "Minyak Goreng Curah": 5.0, "Cabai Rawit Merah": 2.0, "Bawang Merah": 2.0,
}


def default_plan() -> dict:
    return {name: {"quantity": quantity, "shock_pct": 10.0} for name, quantity in DEFAULT_BASKET.items()}


def historical_budget(changes: pd.DataFrame, province: str, month, quantities=None) -> dict:
    """Compare fixed quantities on two exact calendar months, never partial totals."""
    quantities = DEFAULT_BASKET if quantities is None else quantities
    if any(not math.isfinite(float(q)) or q < 0 for q in quantities.values()):
        raise ValueError("Kuantitas harus nonnegatif dan terbatas.")
    requested = pd.DataFrame([{"commodity": c, "quantity": q} for c, q in quantities.items() if q > 0], columns=["commodity", "quantity"])
    current = changes[(changes.province == province) & (changes.date == pd.Timestamp(month))]
    lines = requested.merge(current[["commodity", "price", "previous_price", "unit"]], on="commodity", how="left", validate="one_to_one")
    lines["current_cost"] = lines.quantity * lines.price
    lines["previous_cost"] = lines.quantity * lines.previous_price
    lines["impact"] = lines.current_cost - lines.previous_cost
    available = int(lines.price.notna().sum())
    comparable = int(lines.impact.notna().sum())
    count = len(lines)
    current_total = float(lines.current_cost.sum()) if count and available == count else None
    previous_total = float(lines.previous_cost.sum()) if count and lines.previous_price.notna().all() else None
    delta = current_total - previous_total if current_total is not None and previous_total is not None else None
    return {"lines": lines, "total": current_total, "previous_total": previous_total,
            "delta": delta, "delta_pct": delta / previous_total * 100 if delta is not None and previous_total else None,
            "available": available, "comparable": comparable, "count": count,
            "known_total": float(lines.current_cost.sum()),
            "comparable_delta": float(lines.impact.sum()) if comparable else None}


def apply_edits(plan: dict, names: list[str], edits: dict) -> dict:
    """Apply Streamlit editor deltas by commodity, preserving hidden rows and inputs."""
    result = deepcopy(plan)
    columns = {"Jumlah": "quantity", "Perubahan (%)": "shock_pct", "Harga acuan (Rp)": "override"}
    for index, patch in edits.get("edited_rows", {}).items():
        name = names[int(index)]
        for display, value in patch.items():
            if display in columns:
                if value is not None and (not math.isfinite(float(value))):
                    raise ValueError("Isian harus berupa angka terbatas.")
                result[name][columns[display]] = value
    return result


def scenario(data: pd.DataFrame, province: str, month, plan: dict, chosen: list[str], manual=False) -> dict:
    """Use current snapshot unless a row was explicitly edited in manual mode."""
    month = pd.Timestamp(month)
    units = data.drop_duplicates("commodity").set_index("commodity").unit.to_dict()
    snapshot = data[(data.province == province) & (data.date == month)].set_index("commodity").price.to_dict()
    prices, provenance, basket = [], [], []
    for name in chosen:
        row = plan[name]
        overridden = manual and "override" in row
        value = row.get("override") if overridden else snapshot.get(name)
        source = "Belum tersedia" if value is None or pd.isna(value) else ("Diubah pengguna" if overridden else "Snapshot historis")
        provenance.append({"commodity": name, "price_source": source})
        if value is not None and pd.notna(value):
            prices.append({"province": province, "commodity": name, "date": month, "price": value, "unit": units.get(name, "satuan")})
        basket.append({"commodity": name, "quantity": row["quantity"], "shock_pct": row["shock_pct"]})
    reference = pd.DataFrame(prices, columns=["province", "commodity", "date", "price", "unit"])
    result = basket_simulation(reference, province, month, pd.DataFrame(basket))
    result["lines"] = result["lines"].drop(columns="unit").merge(pd.DataFrame(provenance), on="commodity", validate="one_to_one")
    result["lines"]["unit"] = result["lines"].commodity.map(units)
    return result


def complete_months(data, province, names):
    names = list(names)
    if not names:
        return []
    counts = data[(data.province == province) & data.commodity.isin(names)].groupby("date").commodity.nunique()
    return sorted(counts[counts == len(names)].index, reverse=True)


def scenario_table(result, province, month, period):
    frame = result["lines"].rename(columns={"commodity": "Bahan", "quantity": "Jumlah", "unit": "Satuan asumsi",
        "price": "Harga acuan (Rp)", "shock_pct": "Perubahan (%)", "scenario_price": "Harga skenario (Rp)",
        "baseline_cost": "Biaya acuan (Rp)", "scenario_cost": "Biaya skenario (Rp)", "cost_change": "Selisih (Rp)",
        "price_available": "Harga tersedia", "price_source": "Sumber harga"})
    for key, value in reversed([("Wilayah", province), ("Bulan referensi", pd.Timestamp(month).strftime("%Y-%m")), ("Periode belanja", period)]):
        frame.insert(0, key, value)
    return frame


def scenario_workbook(result, province, month, period):
    """Export the actual edited scenario, including row-level sources and missing totals."""
    table = scenario_table(result, province, month, period)
    summary = pd.DataFrame({"Keterangan": ["Jenis hasil", "Wilayah", "Bulan referensi", "Periode belanja", "Status", "Anggaran acuan", "Anggaran skenario", "Selisih", "Subtotal acuan tersedia", "Subtotal skenario tersedia"],
        "Nilai": ["Skenario asumsi, bukan pengeluaran terealisasi", province, pd.Timestamp(month).strftime("%Y-%m"), period,
            "Lengkap" if result["complete"] else "Belum lengkap", result["baseline_total"], result["scenario_total"], result["difference"], result["known_baseline_total"], result["known_scenario_total"]]})
    notes = pd.DataFrame({"Catatan": ["Belanja acuan = jumlah × harga acuan yang digunakan.",
        "Harga skenario = harga acuan × (1 + perubahan / 100).", "Sumber harga dicatat per bahan; harga yang tidak tersedia tetap kosong.",
        "Satuan kg/liter merupakan asumsi. Tanpa ongkir, susut, biaya operasional, stok, atau margin.",
        "Kuantitas ditentukan pengguna per periode belanja; bukan catatan transaksi usaha."]})
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, frame in [("Ringkasan", summary), ("Rincian bahan", table), ("Metode", notes)]:
            frame.to_excel(writer, sheet_name=name, index=False)
            ws = writer.sheets[name]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for cell in ws[1]:
                cell.fill = PatternFill("solid", fgColor="102A43")
                cell.font = Font(color="FFFFFF", bold=True)
            for row in ws.iter_rows(min_row=2):
                for cell in row:
                    if isinstance(cell.value, str):
                        cell.data_type = "s"
                    elif isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool):
                        cell.number_format = '#,##0.00'
            for i, col in enumerate(ws.columns, 1):
                ws.column_dimensions[get_column_letter(i)].width = min(65, max(18, max(len(str(c.value or "")) for c in col) + 2))
    return buffer.getvalue()
