"""Shared, accessible chart and Indonesian display conventions."""
import html
import pandas as pd
import streamlit as st

MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
TEAL, RED, NAVY, AMBER = "#087f8c", "#c05247", "#183b56", "#bd811d"


def rupiah(value):
    return "—" if value is None or pd.isna(value) else "Rp " + f"{value:,.0f}".replace(",", ".")


def percent(value, signed=True, digits=1):
    if value is None or pd.isna(value): return "—"
    return f"{value:+.{digits}f}%".replace(".", ",") if signed else f"{value:.{digits}f}%".replace(".", ",")


def month_label(value):
    value = pd.Timestamp(value)
    return f"{MONTHS[value.month-1]} {value.year}"


def display_table(frame):
    result = frame.copy()
    for column in result:
        if "(Rp)" in column:
            result[column] = result[column].map(rupiah)
        elif "(%)" in column:
            result[column] = result[column].map(lambda v: percent(v, signed=False))
        elif pd.api.types.is_datetime64_any_dtype(result[column]):
            result[column] = result[column].map(month_label)
        elif pd.api.types.is_numeric_dtype(result[column]) and not pd.api.types.is_bool_dtype(result[column]):
            result[column] = result[column].map(lambda v: "—" if pd.isna(v) else f"{v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".") if "Jumlah" in column else f"{v:,.0f}".replace(",", "."))
    return result.fillna("—")


def table(frame, height=None):
    st.dataframe(display_table(frame), hide_index=True, width="stretch", height=height or "auto")


def csv_bytes(frame):
    return frame.to_csv(index=False).encode("utf-8-sig")


def chart(fig, key, height=300):
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=5,r=15,t=20,b=10),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif",size=12,color=NAVY), separators=",.",
        legend=dict(orientation="h",y=1.12,title_text=""),hoverlabel=dict(bgcolor="white"))
    fig.update_xaxes(showgrid=False,zeroline=False,automargin=True)
    fig.update_yaxes(gridcolor="#e6edf3",automargin=True)
    st.plotly_chart(fig, use_container_width=True, key=key, config={"displaylogo":False,"displayModeBar":False,"responsive":True,"modeBarButtonsToRemove":["select2d","lasso2d"]})


def finding(text, label="TEMUAN UTAMA"):
    st.html(f'<div class="finding"><span class="label">{html.escape(label)}</span>{text}</div>')
