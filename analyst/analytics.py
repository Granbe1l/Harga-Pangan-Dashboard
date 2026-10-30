"""Monthly price analytics for the analyst dashboard.

Prices are provincial consumer-price observations, not transaction or supplier
quotes. Missing months stay missing. No function treats an unweighted median as
an official national price or claims that a scenario is a realised saving.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any

import numpy as np
import pandas as pd


def _month(value: Any) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    if pd.isna(stamp):
        raise ValueError("Periode tidak boleh kosong.")
    return stamp.to_period("M").to_timestamp()


def _prices(df: pd.DataFrame) -> pd.DataFrame:
    required = {"province", "commodity", "date", "price"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Kolom harga tidak lengkap: {', '.join(sorted(missing))}")
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"], errors="raise").dt.to_period("M").dt.to_timestamp()
    data["price"] = pd.to_numeric(data["price"], errors="raise")
    if data["date"].isna().any() or data[["province", "commodity"]].isna().any().any():
        raise ValueError("Kunci observasi tidak boleh kosong.")
    if not np.isfinite(data["price"].to_numpy(dtype=float)).all() or (data["price"] <= 0).any():
        raise ValueError("Harga harus berupa angka positif dan terbatas.")
    keys = ["province_code" if "province_code" in data else "province", "commodity", "date"]
    if data.duplicated(keys).any():
        raise ValueError("Data memiliki kunci provinsi-komoditas-bulan duplikat.")
    return data


def comparison_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Add exact-calendar MoM/YoY comparisons before applying display filters.

    January and March observations without February do not produce a March MoM
    value. A missing denominator remains NaN rather than becoming zero.
    """
    data = _prices(df)
    group_keys = ["province_code" if "province_code" in data else "province", "commodity"]
    lookup = data[group_keys + ["date", "price"]]
    for months, column in [(1, "previous_price"), (12, "year_ago_price")]:
        previous = lookup.rename(columns={"price": column}).copy()
        previous["date"] = previous["date"] + pd.DateOffset(months=months)
        data = data.merge(previous, on=group_keys + ["date"], how="left", validate="one_to_one")
    data["mom_pct"] = (data["price"] / data["previous_price"] - 1.0) * 100.0
    data["yoy_pct"] = (data["price"] / data["year_ago_price"] - 1.0) * 100.0
    return data.sort_values(group_keys + ["date"]).reset_index(drop=True)


def volatility_summary(
    df: pd.DataFrame,
    start: Any | None = None,
    end: Any | None = None,
    min_observations: int = 3,
) -> pd.DataFrame:
    """Describe variation per province/commodity in one common date window.

    CV uses sample standard deviation (ddof=1) divided by the mean, in percent.
    It measures variation of price levels, not a probability of future rises.
    Expected months include missing calendar months. Series with fewer than
    ``min_observations`` never receive a CV ranking value.
    """
    if min_observations < 2:
        raise ValueError("Minimal observasi harus sekurangnya dua bulan.")
    data = _prices(df)
    group = (["province_code"] if "province_code" in data else []) + ["province", "commodity"]
    if "unit" in data:
        group += ["unit"]
    columns = group + ["observations", "expected_months", "coverage_pct", "mean_price", "std_price", "cv_pct", "min_price", "max_price", "latest_date", "latest_price"]
    if data.empty:
        return pd.DataFrame(columns=columns)
    first = _month(start) if start is not None else data["date"].min()
    last = _month(end) if end is not None else data["date"].max()
    if first > last:
        raise ValueError("Awal periode tidak boleh setelah akhir periode.")
    data = data[data["date"].between(first, last)]
    if data.empty:
        return pd.DataFrame(columns=columns)
    expected = (last.year - first.year) * 12 + last.month - first.month + 1
    result = data.groupby(group, dropna=False).agg(
        observations=("price", "size"),
        mean_price=("price", "mean"),
        std_price=("price", "std"),
        min_price=("price", "min"),
        max_price=("price", "max"),
        latest_date=("date", "max"),
    ).reset_index()
    latest = data.sort_values("date").groupby(group, dropna=False).tail(1)[group + ["price"]]
    result = result.merge(latest.rename(columns={"price": "latest_price"}), on=group, validate="one_to_one")
    result["expected_months"] = expected
    result["coverage_pct"] = result["observations"] / expected * 100.0
    result["cv_pct"] = (result["std_price"] / result["mean_price"] * 100.0).where(result["observations"] >= min_observations)
    return result[columns].sort_values(["cv_pct", "commodity"], ascending=[False, True], na_position="last").reset_index(drop=True)


def province_comparison(df: pd.DataFrame, commodity: str, as_of: Any) -> pd.DataFrame:
    """Compare one commodity in one month with its observed-province median.

    ``median_price`` is an unweighted descriptive median, not Bapanas' official
    national average. Absent provinces are not imputed.
    """
    data = _prices(df)
    result = data[(data["commodity"] == commodity) & (data["date"] == _month(as_of))].copy()
    median = float(result["price"].median()) if not result.empty else np.nan
    result["median_price"] = median
    result["deviation_pct"] = (result["price"] / median - 1.0) * 100.0
    return result.sort_values("price", ascending=False).reset_index(drop=True)


def basket_simulation(
    df: pd.DataFrame,
    province: str,
    as_of: Any,
    basket: pd.DataFrame,
) -> dict[str, Any]:
    """Apply user-selected quantities and price shocks to exact-month prices.

    ``basket`` requires commodity, quantity, shock_pct. Quantity uses the unit
    attached to each commodity in the prepared data; unit assignments originate
    from documented assumptions rather than a unit column in the raw CSV.
    A missing price for a positive quantity makes complete totals None; known
    subtotals remain available and are explicitly labelled as incomplete.
    """
    data = _prices(df)
    required = {"commodity", "quantity", "shock_pct"}
    missing = required.difference(basket.columns)
    if missing:
        raise ValueError(f"Kolom keranjang tidak lengkap: {', '.join(sorted(missing))}")
    lines = basket[list(required)].copy()
    if lines.empty:
        raise ValueError("Keranjang harus berisi minimal satu komoditas.")
    if lines["commodity"].isna().any() or lines["commodity"].duplicated().any():
        raise ValueError("Setiap komoditas harus terisi dan hanya muncul sekali di keranjang.")
    for column in ["quantity", "shock_pct"]:
        lines[column] = pd.to_numeric(lines[column], errors="raise")
        if not np.isfinite(lines[column].to_numpy(dtype=float)).all():
            raise ValueError("Kuantitas dan skenario harga harus berupa angka terbatas.")
    if (lines["quantity"] < 0).any():
        raise ValueError("Kuantitas tidak boleh negatif.")
    if (lines["shock_pct"] < -100).any():
        raise ValueError("Penurunan harga tidak boleh melebihi 100%.")
    month = _month(as_of)
    selected = data[(data["province"] == province) & (data["date"] == month)]
    columns = ["commodity", "price"] + (["unit"] if "unit" in selected else [])
    lines = lines.merge(selected[columns], on="commodity", how="left", validate="one_to_one")
    if "unit" not in lines:
        lines["unit"] = "satuan komoditas"
    lines["price_available"] = lines["price"].notna()
    lines["baseline_cost"] = lines["quantity"] * lines["price"]
    lines["scenario_price"] = lines["price"] * (1.0 + lines["shock_pct"] / 100.0)
    lines["scenario_cost"] = lines["quantity"] * lines["scenario_price"]
    lines.loc[lines["quantity"] == 0, ["baseline_cost", "scenario_cost"]] = 0.0
    lines["cost_change"] = lines["scenario_cost"] - lines["baseline_cost"]
    absent = lines.loc[(lines["quantity"] > 0) & ~lines["price_available"], "commodity"].tolist()
    active = bool((lines["quantity"] > 0).any())
    complete = not absent and active
    base = float(lines["baseline_cost"].sum())
    scenario = float(lines["scenario_cost"].sum())
    return {
        "lines": lines[["commodity", "quantity", "unit", "price", "shock_pct", "scenario_price", "baseline_cost", "scenario_cost", "cost_change", "price_available"]],
        "as_of": month,
        "complete": complete,
        "missing_commodities": absent,
        "baseline_total": base if complete else None,
        "scenario_total": scenario if complete else None,
        "difference": scenario - base if complete else None,
        "difference_pct": (scenario / base - 1.0) * 100.0 if complete and base > 0 else None,
        "known_baseline_total": base,
        "known_scenario_total": scenario,
    }


def create_sql_views(connection: sqlite3.Connection, sql_path: str | Path | None = None) -> None:
    """Register the reviewable SQL views in an existing prepared database."""
    path = Path(sql_path) if sql_path is not None else Path(__file__).resolve().parents[1] / "sql" / "analytics.sql"
    connection.executescript(path.read_text(encoding="utf-8"))


def matched_fluctuation(df, start, end, minimum_coverage=80):
    """Rank on identical observed months, using exact-month price changes as well as levels."""
    if not 0 <= minimum_coverage <= 100:
        raise ValueError("Cakupan harus antara 0 dan 100.")
    data = _prices(df)
    if data.province.nunique() > 1:
        raise ValueError("Pilih satu wilayah untuk perbandingan fluktuasi.")
    first, last = _month(start), _month(end)
    screening = volatility_summary(data, first, last)
    eligible = screening[(screening.observations >= 3) & (screening.coverage_pct >= minimum_coverage)]
    selected = data[data.commodity.isin(eligible.commodity) & data.date.between(first, last)]
    pivot = selected.pivot(index="date", columns="commodity", values="price").sort_index()
    common = pivot.dropna().index if len(pivot.columns) else pd.DatetimeIndex([])
    columns = ["commodity","common_observations","cv_pct","monthly_abs_pct","monthly_std_pct","monthly_pairs"]
    result = pd.DataFrame(columns=columns)
    monthly_dates = pd.DatetimeIndex([])
    if len(common) >= 3:
        raw_columns = ["province","commodity","date","price"] + [c for c in ["province_code","unit"] if c in data]
        change = comparison_frame(data[raw_columns])
        monthly = change[change.commodity.isin(eligible.commodity) & change.date.isin(common)].pivot(index="date",columns="commodity",values="mom_pct").dropna()
        monthly_dates = monthly.index
        aligned = pivot.loc[common]
        rows = []
        for name in aligned.columns:
            prices = aligned[name]
            movements = monthly[name]
            rows.append({"commodity":name,"common_observations":len(common),"cv_pct":prices.std()/prices.mean()*100,
                "monthly_abs_pct":float(movements.abs().mean()) if len(movements)>=2 else None,
                "monthly_std_pct":float(movements.std()) if len(movements)>=2 else None,
                "monthly_pairs":len(movements)})
        result = pd.DataFrame(rows).sort_values("monthly_abs_pct",ascending=False,na_position="last")
    return {"summary":result,"screening":screening,"common_months":list(common),"monthly_months":list(monthly_dates),"eligible_count":len(eligible)}
