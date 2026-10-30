"""Executive price analysis and explicit budget scenarios for a culinary SME case."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import html
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analyst.analytics import comparison_frame, province_comparison, volatility_summary, matched_fluctuation, monthly_findings
from analyst.pipeline import load_clean_data, load_quality_report
from analyst.planning import (DEFAULT_BASKET, historical_budget, scenario,
    apply_edits, complete_months, scenario_table, scenario_workbook, basket_coverage, sensitivity_cases, apply_budget_limit)
from analyst.presentation import (TEAL, RED, NAVY, AMBER, rupiah, percent, month_label,
    table, chart, finding, csv_bytes)

ROOT = Path(__file__).resolve().parent
TITLE = "Analisis Harga Pangan dan Simulasi Anggaran Bahan Baku UMKM Kuliner"
PAGES = ["Ringkasan", "Tren & fluktuasi", "Perbandingan wilayah", "Simulator anggaran"]
REPO = "https://github.com/Granbe1l/Harga-Pangan-Dashboard"
st.set_page_config(page_title=TITLE, page_icon="📊", layout="wide", initial_sidebar_state="auto")
st.html('<style>' + (ROOT / "assets/dashboard.css").read_text() + '</style>')


@st.cache_data(show_spinner=False)
def read_assets():
    data = load_clean_data(ROOT)
    return data, comparison_frame(data), load_quality_report(ROOT), json.loads((ROOT / "data/source.json").read_text())


def save_filter(name):
    st.session_state["filters"][name] = st.session_state["filter_" + name]


def select_filter(name, label, options, formatter=None):
    key = "filter_" + name
    if key not in st.session_state:
        st.session_state[key] = st.session_state["filters"][name]
    return st.selectbox(label, options, key=key, format_func=formatter or str, on_change=save_filter, args=(name,))


def navigate(page):
    st.session_state.page = page


def change_month(month):
    st.session_state["filters"]["as_of"] = month
    st.session_state["filter_as_of"] = month


def initialize(data):
    defaults = {"province":"Jawa Barat","as_of":data.date.max(),"commodity":"Beras Medium","window":12,"threshold":10,"coverage":80,"all_regions":False,"basket_profile":"Latihan A"}
    if "filters" not in st.session_state: st.session_state.filters = {}
    for key, value in defaults.items(): st.session_state.filters.setdefault(key,value)
    if "spending_limit" not in st.session_state: st.session_state.spending_limit = 0.0
    if "plan" not in st.session_state:
        st.session_state.plan = {name: {"quantity": DEFAULT_BASKET.get(name, 1.0), "shock_pct": 10.0} for name in sorted(data.commodity.unique())}
        st.session_state.chosen = list(DEFAULT_BASKET)
        st.session_state.manual_mode = False
        st.session_state.editor_version = 0
        st.session_state.period = "Satu kali belanja"


def persist_chosen():
    st.session_state.chosen = st.session_state.basket_commodities
    st.session_state.editor_version += 1


def toggle_manual():
    st.session_state.manual_mode = st.session_state.manual_prices
    st.session_state.editor_version += 1


def persist_limit():
    st.session_state.spending_limit = st.session_state.budget_limit


def persist_period():
    st.session_state.period = st.session_state.budget_period


def commit_editor():
    key = 'budget_editor_' + str(st.session_state.editor_version)
    st.session_state.plan = apply_edits(st.session_state.plan, st.session_state.chosen, st.session_state[key])
    st.session_state.editor_version += 1


def apply_bulk(value=None):
    value = st.session_state.bulk_shock if value is None else value
    for name in st.session_state.chosen:
        st.session_state.plan[name]["shock_pct"] = float(value)
    st.session_state.editor_version += 1


def reset_budget():
    for name in st.session_state.plan:
        st.session_state.plan[name] = {"quantity": DEFAULT_BASKET.get(name, 1.0), "shock_pct": 10.0}
    st.session_state.chosen = list(DEFAULT_BASKET)
    st.session_state.basket_commodities = list(DEFAULT_BASKET)
    st.session_state.manual_mode = False
    st.session_state.manual_prices = False
    st.session_state.period = "Satu kali belanja"
    st.session_state.budget_period = "Satu kali belanja"
    st.session_state.bulk_shock = 10
    st.session_state.budget_limit = 0.0
    st.session_state.spending_limit = 0.0
    st.session_state.editor_version += 1


def price_overview(data, changes, province, commodity, as_of, start, threshold):
    observed=monthly_findings(changes,province,as_of,threshold)
    st.html('<div class="section-tag">01 / TEMUAN HARGA · TANPA ASUMSI JUMLAH BELANJA</div>')
    cols=st.columns(3)
    cols[0].metric("Komoditas dengan harga",f"{observed['available']} / {observed['universe']}")
    cols[1].metric(f"Naik ≥{threshold}% bulanan",str(observed['alert_count']) if observed['alert_count'] is not None else "—")
    top=observed['top_rise']
    cols[2].metric("Kenaikan tertinggi",percent(top['mom_pct'],digits=2) if top else "—")
    if observed['comparable_count']:
        message=f"<b>{observed['alert_count']} dari {observed['comparable_count']} komoditas</b> dengan pembanding naik setidaknya {threshold}%."
        if top: message+=f" Tertinggi: <b>{html.escape(top['commodity'])} {percent(top['mom_pct'],digits=2)}</b>."
        finding(message,"HASIL BERDASARKAN HARGA TERCATAT")
    else:
        finding("Harga bulan pembanding belum tersedia; kenaikan bulanan belum dapat dihitung." if observed['available'] else "Belum ada harga pada bulan ini. Pilih bulan lain atau wilayah lain.","KELENGKAPAN DATA")
    left,right=st.columns([1.6,1],gap="large")
    with left,st.container(border=True):
        st.subheader("Perubahan harga bulan ini")
        ranked=observed['comparable'].copy()
        if ranked.empty: st.info("Belum ada pasangan bulan yang dapat dibandingkan.")
        else:
            ranked['absolute']=ranked.mom_pct.abs()
            ranked=ranked.nlargest(8,'absolute').sort_values('mom_pct')
            fig=go.Figure(go.Bar(x=ranked.mom_pct,y=ranked.commodity,orientation='h',
                marker_color=[RED if n>0 else TEAL for n in ranked.mom_pct],text=[percent(n) for n in ranked.mom_pct],textposition='auto',
                hovertemplate='%{y}<br>Perubahan: %{x:.2f}%<extra></extra>'))
            fig.add_vline(x=0,line_color='#879bae',line_width=1)
            fig.update_layout(xaxis_title='Perubahan bulanan (%)')
            chart(fig,'price_movements',275)
        st.caption(f"Pembanding tersedia untuk {observed['comparable_count']} dari {observed['available']} bahan bulan pilihan. Delapan perubahan absolut terbesar; merah naik, teal turun.")
    with right,st.container(border=True):
        st.subheader("Apa arti temuan ini?")
        if top:
            st.write(f"**{top['commodity']}** mencatat kenaikan tertinggi pada wilayah dan bulan pilihan. Besarnya dampak belanja bergantung jumlah kebutuhan.")
        else:st.write("Kenaikan belum terlihat atau belum bisa dihitung dari pasangan bulan yang tersedia.")
        st.write("Buka tab **Dampak keranjang latihan** untuk melihat perubahan biaya dan sensitivitas komposisi, atau coba kebutuhanmu di simulator.")
        st.button("Coba simulasi belanja →",type="primary",width="stretch",on_click=navigate,args=("Simulator anggaran",),key="price_cta")
    if top:
        history_changes=changes[(changes.province==province)&(changes.commodity==top['commodity'])&changes.date.between(start,as_of)].dropna(subset=['mom_pct'])
        if len(history_changes)>=2:
            repeats=int((history_changes.mom_pct>=threshold).sum())
            st.write(f"**Apakah kenaikan ini berulang?** {top['commodity']} naik ≥{threshold}% pada **{repeats} dari {len(history_changes)} pasangan bulan** dengan pembanding, dalam rentang {month_label(start)}–{month_label(as_of)}. Ini frekuensi historis pada data tersedia, bukan peluang kenaikan berikutnya.")
    st.caption("Persentase membandingkan seri bahan yang sama pada dua bulan. File sumber tidak mencantumkan satuan; angka biaya pada tab latihan memakai asumsi yang dinyatakan.")
    with st.expander("Detail bahan pilihan & riwayat"):
        selected=observed['snapshot'][observed['snapshot'].commodity==commodity]
        row=selected.iloc[0] if len(selected) else None
        st.write(f"**{commodity}** · Harga sumber: **{rupiah(row.price if row is not None else None)}** · Bulanan: **{percent(row.mom_pct if row is not None else None)}** · Tahunan: **{percent(row.yoy_pct if row is not None else None)}**")
        st.caption(f"{province} · {month_label(start)}–{month_label(as_of)}. Angka harga mengikuti file; satuan tidak dinyatakan pada ekspor.")
        history=data[(data.province==province)&(data.commodity==commodity)&data.date.between(start,as_of)][['date','price']].rename(columns={'date':'Bulan','price':'Harga sumber (Rp)'})
        if history.empty:st.info("Tidak ada harga bahan pilihan pada rentang ini.")
        else:table(history,height=250)



def overview(data, changes, province, commodity, as_of, start, threshold):
    observed,training=st.tabs(["Temuan harga","Dampak keranjang latihan"])
    with observed:price_overview(data,changes,province,commodity,as_of,start,threshold)
    with training:budget_overview(data,changes,province,commodity,as_of,start,threshold)


def budget_overview(data, changes, province, commodity, as_of, start, threshold):
    quantities = dict(DEFAULT_BASKET)
    profile = st.session_state.filters.get("basket_profile", "Latihan A")
    if profile == "Latihan B": quantities["Telur Ayam Ras"] = 1.0
    if profile == "Latihan C": quantities.pop("Minyak Goreng Curah")
    budget = historical_budget(changes, province, as_of, quantities)
    coverage = basket_coverage(data, province, quantities)
    st.html('<div class="section-tag">01 / DAMPAK HARGA · KERANJANG LATIHAN</div>')
    cols = st.columns(3)
    cols[0].metric("Estimasi biaya keranjang latihan", rupiah(budget["total"]), help="Keranjang latihan yang dipilih dengan kuantitas tetap; bukan catatan pembelian usaha.")
    cols[1].metric("Perubahan estimasi vs bulan lalu", rupiah(budget["delta"]), percent(budget["delta_pct"]), delta_color="inverse")
    cols[2].metric("Kelengkapan harga keranjang", f"{budget['available']} / {budget['count']} bahan")
    first = month_label(coverage["first_complete"]) if coverage["first_complete"] is not None else "belum tersedia"
    st.caption(f"{profile} · Keranjang lengkap {coverage['complete_months']}/{coverage['months']} bulan; pertama {first}. Satuan sumber belum terverifikasi: angka rupiah di sini adalah estimasi latihan.")
    if budget["delta"] is not None:
        movement = "bertambah" if budget["delta"] > 0 else "berkurang" if budget["delta"] < 0 else "tetap"
        finding(f"Untuk komposisi latihan dan jumlah tetap, estimasi biaya keranjang <b>{movement} {rupiah(abs(budget['delta']))}</b> dibanding {month_label(as_of - pd.DateOffset(months=1))}. Harga kedua bulan tersedia untuk seluruh {budget['count']} bahan.")
    elif budget["available"] == 0:
        finding("Belum ada harga pada bulan ini. Pilih bulan lain untuk melihat anggaran; harga lama tidak dipakai sebagai pengganti.", "DATA BELUM TERSEDIA")
    else:
        finding(f"Perubahan biaya belum bisa dihitung untuk seluruh keranjang. Pembanding tersedia untuk <b>{budget['comparable']} dari {budget['count']} bahan</b>; total yang belum lengkap ditampilkan sebagai —.", "KELENGKAPAN DATA")
        if budget["total"] is None:
            st.caption(f"Subtotal {budget['available']} bahan dengan harga tersedia: {rupiah(budget['known_total'])}. Ini bukan total keranjang lengkap.")
    left, right = st.columns([1.65, 1], gap="large")
    with left, st.container(border=True):
        st.subheader("Kontributor perubahan biaya")
        lines = budget["lines"].dropna(subset=["impact"]).sort_values("impact")
        if lines.empty:
            st.info("Bulan pembanding belum tersedia. Pilih bulan yang lebih akhir.")
        else:
            fig = go.Figure(go.Bar(x=lines.impact, y=lines.commodity, orientation="h", marker_color=[RED if v > 0 else TEAL for v in lines.impact],
                text=[rupiah(v) for v in lines.impact], textposition="auto", hovertemplate="%{y}<br>Perubahan biaya: Rp %{x:,.0f}<extra></extra>"))
            fig.add_vline(x=0, line_color="#879bae", line_width=1)
            fig.update_layout(xaxis_title="Perubahan biaya (Rp)", yaxis_title=None)
            chart(fig, "historical_impact", height=265)
            st.caption(f"{len(lines)} dari {budget['count']} bahan memiliki pembanding. Positif = tambahan biaya; negatif = pengurangan biaya.")
    with right, st.container(border=True):
        st.subheader("Mengapa komposisi penting?")
        positive = lines[lines.impact > 0] if not lines.empty else lines
        if not positive.empty:
            top = positive.iloc[-1]
            st.markdown(f"**{top.commodity}** memberi tambahan biaya terbesar: **{rupiah(top.impact)}**.")
            st.write("Coba Profil A dan B: perubahan jumlah telur saja dapat mengubah peringkat. Buka panel profil untuk membandingkan, lalu uji kebutuhan sendiri.")
        elif not lines.empty:
            st.write("Tidak ada tambahan biaya pada bahan yang memiliki pembanding. Periksa rincian sebelum mengubah anggaran.")
        else:
            st.write("Mulai dari bulan dengan data pembanding yang tersedia untuk membaca perubahan biaya.")
        st.button("Coba simulasi belanja →", type="primary", width="stretch", on_click=navigate, args=("Simulator anggaran",),key="training_cta")
        with st.expander("Profil latihan, sensitivitas, dan cakupan"):
            select_filter("basket_profile", "Pilih komposisi latihan", ["Latihan A", "Latihan B", "Latihan C"])
            st.caption("A: enam bahan, telur 5 kg. B: telur 1 kg, bahan lain tetap. C: lima bahan tanpa minyak untuk riwayat yang lebih panjang. Profil tidak diganti otomatis antarbulan; semuanya contoh buatan, bukan data usaha.")
            table(sensitivity_cases(changes,province,as_of))
            st.metric("Estimasi bulan sebelumnya",rupiah(budget["previous_total"]))
            st.caption(f"Perubahan total lengkap tersedia {coverage['comparison_months']}/{coverage['months']} bulan pada profil ini.")
            st.write("Contoh kebutuhan untuk satu kali belanja; bukan hasil survei atau transaksi. Satuan kg/liter adalah asumsi. Tanpa ongkir, susut bahan, atau biaya operasional.")
            table(budget["lines"][["commodity", "quantity", "unit"]].rename(columns={"commodity":"Bahan","quantity":"Jumlah","unit":"Satuan asumsi"}))
    with st.expander("Detail bahan, tren, dan pemantauan harga"):
        snapshot = changes[(changes.province == province) & (changes.date == as_of)]
        current = snapshot[snapshot.commodity == commodity]
        row = current.iloc[0] if len(current) else None
        unit = data.loc[data.commodity == commodity, "unit"].iloc[0]
        st.subheader(f"Harga {commodity}")
        cols = st.columns(3)
        cols[0].metric("Harga per " + unit, rupiah(row.price if row is not None else None))
        cols[1].metric("Perubahan bulanan", percent(row.mom_pct if row is not None else None))
        cols[2].metric("Perubahan tahunan", percent(row.yoy_pct if row is not None else None))
        selected = data[(data.province == province) & (data.commodity == commodity) & data.date.between(start, as_of)]
        if len(selected) < 2:
            st.info("Riwayat belum cukup untuk menampilkan tren. Minimal dua harga bulanan diperlukan.")
        else:
            timeline = selected.set_index("date").price.reindex(pd.date_range(start, as_of, freq="MS")).rename_axis("date").reset_index(name="price")
            fig = px.line(timeline,x="date",y="price",markers=True,color_discrete_sequence=[TEAL],labels={"date":"Bulan","price":f"Harga (Rp/{unit})"})
            fig.update_traces(connectgaps=False, hovertemplate="%{x|%b %Y}<br>Rp %{y:,.0f}<extra></extra>")
            chart(fig,"overview_trend",260)
        comparable = snapshot.dropna(subset=["mom_pct"])
        alerts = comparable[comparable.mom_pct >= threshold].sort_values("mom_pct",ascending=False)
        if comparable.empty:
            st.info("Perubahan bulanan belum bisa dihitung: bulan kalender sebelumnya tidak tersedia.")
        elif len(alerts):
            top = alerts.iloc[0]
            st.write(f"**{len(alerts)} dari {len(comparable)} komoditas** naik setidaknya {threshold}%. Tertinggi: **{top.commodity} {percent(top.mom_pct,digits=2)}**.")
        else:
            st.write(f"Tidak ada komoditas yang naik setidaknya {threshold}% dari {len(comparable)} pasangan bulan yang tersedia.")
        clean = snapshot[["commodity","price","unit","mom_pct","yoy_pct"]].rename(columns={"commodity":"Bahan","price":"Harga (Rp)","unit":"Satuan asumsi","mom_pct":"Bulanan (%)","yoy_pct":"Tahunan (%)"})
        table(clean.head(10))
        st.download_button("Unduh seluruh ringkasan CSV",csv_bytes(clean),"ringkasan_harga.csv","text/csv")


def budget_page(data, changes, province, commodity, as_of, start, threshold):
    st.html('<div class="section-tag">02 / SIMULATOR ANGGARAN</div><div class="simulation-banner"><b>SKENARIO ASUMSI</b> · Hasil mengikuti jumlah, harga acuan, dan perubahan harga yang kamu isi. Bukan perubahan biaya historis atau pengeluaran terealisasi.</div>')
    controls, results = st.columns([1.2,1],gap="large")
    with controls:
        st.subheader("Atur kebutuhan belanja")
        if "basket_commodities" not in st.session_state: st.session_state.basket_commodities = st.session_state.chosen
        chosen = st.multiselect("Bahan dalam keranjang",sorted(data.commodity.unique()),key="basket_commodities",on_change=persist_chosen)
        if "budget_period" not in st.session_state: st.session_state.budget_period = st.session_state.period
        st.selectbox("Kebutuhan per periode belanja",["Satu kali belanja","Per hari","Per minggu","Per bulan"],key="budget_period",on_change=persist_period)
        st.caption("Periode ini menjelaskan jumlah yang kamu isi; aplikasi tidak mengonversi kuantitas secara otomatis.")
        with st.expander("Terapkan perubahan ke semua bahan",expanded=False):
            st.caption("Hanya berlaku setelah tombol ditekan. Jumlah dan harga acuan tetap dipertahankan.")
            a,b,c = st.columns(3)
            for col,value in zip([a,b,c],[0,10,20]):
                col.button(f"{value:+d}%",on_click=apply_bulk,args=(value,),width="stretch",key=f"quick_{value}")
            if "bulk_shock" not in st.session_state: st.session_state.bulk_shock = 10
            st.number_input("Perubahan seragam (%)",min_value=-100,max_value=500,step=5,key="bulk_shock")
            st.button("Terapkan ke semua bahan",on_click=apply_bulk,width="stretch")
        if "manual_prices" not in st.session_state: st.session_state.manual_prices = st.session_state.manual_mode
        st.checkbox("Edit harga pembelian sendiri",key="manual_prices",on_change=toggle_manual)
        if "budget_limit" not in st.session_state: st.session_state.budget_limit = st.session_state.spending_limit
        st.number_input("Batas anggaran (Rp, 0 = tanpa batas)",min_value=0.0,step=50000.0,key="budget_limit",on_change=persist_limit)
        st.button("Kembalikan contoh awal",on_click=reset_budget,key="reset_budget")
    if not chosen:
        with results: st.info("Pilih minimal satu bahan untuk mulai menghitung.")
        return
    manual = st.session_state.manual_mode
    units = data.drop_duplicates("commodity").set_index("commodity").unit.to_dict()
    prices = data[(data.province==province)&(data.date==as_of)].set_index("commodity").price.to_dict()
    rows = []
    for name in chosen:
        row = st.session_state.plan[name]
        overridden = manual and "override" in row
        price = row.get("override") if overridden else prices.get(name)
        source = "Belum tersedia" if price is None or pd.isna(price) else "Diubah pengguna" if overridden else "Snapshot historis"
        unit = row.get("unit_override", units[name]) if manual else units[name]
        rows.append({"Bahan":name,"Satuan":unit,"Jumlah":row["quantity"],"Perubahan (%)":row["shock_pct"],"Harga acuan (Rp)":price,"Sumber":source})
    entry = pd.DataFrame(rows)
    st.subheader("Rincian kebutuhan")
    st.caption("Klik sel Jumlah atau Perubahan (%) untuk mengedit. Harga yang kamu ubah disimpan selama sesi, termasuk saat berpindah menu atau bulan.")
    if manual:
        st.caption("Satuan dapat dipilih per bahan (kg/liter/satuan). Pilihan ini adalah pernyataan pengguna, bukan verifikasi sumber. Harga simulasi dapat diedit; nilai awal dari snapshot. Sumber per bahan berubah hanya ketika harga pada baris tersebut diedit. Nilai kosong tetap dianggap belum tersedia.")
    key = 'budget_editor_' + str(st.session_state.editor_version)
    st.data_editor(entry,hide_index=True,width="stretch",disabled=["Bahan","Sumber"] + ([] if manual else ["Harga acuan (Rp)","Satuan"]),
        column_config={"Satuan":st.column_config.SelectboxColumn(options=["kg","liter","satuan"],required=True),"Jumlah":st.column_config.NumberColumn(min_value=0.0,step=.5,format="%.2f"),"Perubahan (%)":st.column_config.NumberColumn(min_value=-100.0,max_value=500.0,step=1.0,format="%.1f"),"Harga acuan (Rp)":st.column_config.NumberColumn(min_value=1.0,format="localized")},
        key=key,on_change=commit_editor)
    # Also consume editor deltas on programmatic reruns; real browser edits use the callback.
    if key in st.session_state and st.session_state[key].get("edited_rows"):
        st.session_state.plan = apply_edits(st.session_state.plan,chosen,st.session_state[key])
    try:
        result = apply_budget_limit(scenario(data,province,as_of,st.session_state.plan,chosen,manual),st.session_state.budget_limit)
    except (ValueError, TypeError) as exc:
        st.warning(f"Periksa isian keranjang: {exc}")
        return
    with results, st.container(border=True):
        st.subheader("Hasil skenario")
        st.metric("Anggaran acuan",rupiah(result["baseline_total"]))
        st.metric("Anggaran skenario",rupiah(result["scenario_total"]))
        st.metric("Selisih anggaran",rupiah(result["difference"]),percent(result["difference_pct"]),delta_color="inverse")
    lines = result["lines"]
    st.caption("Dasar perhitungan: " + result["basis"] + ". Tidak menyatakan hasil usaha nyata.")
    if result.get("headroom") is not None:
        if result["headroom"] >= 0: st.success(f"Sisa anggaran setelah skenario: {rupiah(result['headroom'])}.")
        else: st.warning(f"Skenario melewati batas anggaran sebesar {rupiah(-result['headroom'])}.")
    elif result.get("budget_limit") is not None:
        st.info("Batas anggaran belum dapat dibandingkan karena total keranjang tidak lengkap.")
    if result["missing_commodities"]:
        active = lines[lines.quantity>0]
        st.warning("Total belum lengkap. Harga tidak tersedia untuk: " + ", ".join(result["missing_commodities"]) + ". Isi harga sendiri atau hapus bahan dari keranjang.")
        st.caption(f"Harga tersedia untuk {int(active.price_available.sum())} dari {len(active)} bahan aktif. Subtotal bahan tersedia: {rupiah(result['known_baseline_total'])} → {rupiah(result['known_scenario_total'])}; bukan total lengkap.")
        months = complete_months(data,province,active.commodity)
        if months and not manual:
            st.button(f"Gunakan {month_label(months[0])} — harga lengkap",key="complete_basket_month",on_click=change_month,args=(months[0],))
    elif not result["complete"]:
        st.info("Isi jumlah lebih dari nol untuk minimal satu bahan.")
    valid = lines[(lines.quantity>0)&lines.price_available].sort_values("cost_change")
    if not valid.empty:
        top = valid.loc[valid.cost_change.idxmax()]
        if top.cost_change>0:
            finding(f"Tambahan biaya terbesar berasal dari <b>{html.escape(top.commodity)}</b>: <b>{rupiah(top.cost_change)}</b> untuk jumlah belanja yang kamu isi.","DAMPAK SKENARIO")
        fig = go.Figure()
        fig.add_bar(name="Acuan",y=valid.commodity,x=valid.baseline_cost,orientation="h",marker_color="#bbcedb")
        fig.add_bar(name="Skenario",y=valid.commodity,x=valid.scenario_cost,orientation="h",marker_color=TEAL)
        fig.update_layout(barmode="group",xaxis_title="Biaya per periode belanja (Rp)")
        chart(fig,"budget_costs",330)
    export = scenario_table(result,province,as_of,st.session_state.period)
    with st.expander("Rincian hasil dan asal harga per bahan"):
        table(export.drop(columns=["Wilayah","Bulan referensi","Periode belanja"]))
    a,b = st.columns(2)
    a.download_button("Unduh skenario CSV",csv_bytes(export),"skenario_belanja.csv","text/csv",width="stretch")
    b.download_button("Unduh skenario Excel",scenario_workbook(result,province,as_of,st.session_state.period),"skenario_belanja.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",width="stretch")
    with st.expander("Rumus dan asumsi simulasi"):
        st.markdown("**Biaya acuan** = jumlah × harga acuan yang digunakan. **Harga skenario** = harga acuan × (1 + perubahan / 100). **Selisih** = biaya skenario − biaya acuan. Satuan kg/liter merupakan asumsi; tanpa ongkir, susut, stok, margin, dan biaya operasional. Periode belanja adalah label kebutuhan pengguna, bukan frekuensi dari dataset bulanan.")


def risk_page(data, changes, province, commodity, as_of, start, threshold):
    st.html('<div class="section-tag">03 / FLUKTUASI HARGA HISTORIS</div>')
    st.subheader("Tren bahan pilihan")
    history = data[(data.province==province)&(data.commodity==commodity)&data.date.between(start,as_of)][["date","price"]].sort_values("date")
    st.caption(f"{commodity} · harga mengikuti file sumber; satuan belum dikonfirmasi.")
    if len(history)>=2:
        calendar=pd.date_range(start,as_of,freq="MS")
        series=history.set_index("date").reindex(calendar).rename_axis("date").reset_index()
        fig=px.line(series,x="date",y="price",markers=True,labels={"date":"Bulan","price":"Harga sumber (Rp)"},color_discrete_sequence=[TEAL])
        fig.update_traces(connectgaps=False)
        chart(fig,"selected_price_trend",260)
    else:
        st.info("Minimal dua bulan harga diperlukan untuk menampilkan tren. Harga kosong tidak diisi.")
    st.subheader("Bahan mana yang paling berubah-ubah?")
    st.caption(f"{month_label(start)}–{month_label(as_of)} · Seluruh bahan di {province}")
    if "filter_coverage" not in st.session_state: st.session_state.filter_coverage = st.session_state.filters["coverage"]
    coverage = st.select_slider("Minimum cakupan data (%)",options=[0,50,80,100],key="filter_coverage",on_change=save_filter,args=("coverage",),help="CV memerlukan minimal tiga observasi; cakupan adalah bagian bulan dengan harga tersedia dalam rentang efektif.")
    aligned = matched_fluctuation(data[data.province==province],start,as_of,coverage)
    summary, valid = aligned["screening"], aligned["summary"]
    cols = st.columns(3)
    cols[0].metric("Bahan memenuhi kriteria",str(len(valid)))
    cols[1].metric("Minimum cakupan",f"{coverage}%")
    cols[2].metric("Bulan bersama",str(len(aligned["common_months"])))
    measure = st.radio("Ukuran yang dibandingkan",["Perubahan bulanan absolut","Variasi tingkat harga (CV)"],horizontal=True,key="risk_measure")
    column = "monthly_abs_pct" if measure == "Perubahan bulanan absolut" else "cv_pct"
    ranked = valid.dropna(subset=[column]).sort_values(column,ascending=False)
    if ranked.empty:
        st.info("Riwayat belum cukup untuk perbandingan setara: minimal tiga bulan harga bersama dan dua pasangan bulanan diperlukan untuk ukuran perubahan. Pilih bulan lebih akhir atau ubah cakupan.")
    else:
        top = ranked.iloc[0]
        finding(f"<b>{html.escape(top.commodity)}</b> tertinggi pada ukuran pilihan: <b>{percent(top[column],signed=False)}</b>. Semua bahan di grafik memakai <b>{len(aligned['common_months'])} bulan harga bersama</b> dan {len(aligned['monthly_months'])} pasangan bulanan yang sama.","PERBANDINGAN PADA BULAN YANG SAMA")
        shown = ranked.head(10).sort_values(column)
        fig = px.bar(shown,x=column,y="commodity",orientation="h",color_discrete_sequence=[TEAL],custom_data=["common_observations","monthly_pairs"],labels={column:"Perubahan absolut rata-rata (%)" if column=="monthly_abs_pct" else "CV tingkat harga (%)","commodity":""})
        fig.update_traces(hovertemplate="%{y}<br>%{x:.1f}%<br>%{customdata[0]} bulan harga bersama<br>%{customdata[1]} pasangan bulanan<extra></extra>")
        chart(fig,"risk_cv",max(280,len(shown)*30))
    st.caption("Ukuran perubahan bulanan membaca besar pergerakan tanpa arah, bukan peluang kenaikan berikutnya. CV tingkat harga belum memisahkan tren dan musiman. Keduanya tidak menjadi peringkat risiko usaha.")
    with st.expander("Bulan pembanding, tabel kelengkapan, dan unduhan"):
        st.write("Bulan harga bersama: " + (", ".join(month_label(d) for d in aligned["common_months"]) or "belum tersedia"))
        st.write("Pasangan bulanan sama (bulan akhir): " + (", ".join(month_label(d) for d in aligned["monthly_months"]) or "belum tersedia"))
        if len(valid):
            export = valid.rename(columns={"commodity":"Bahan","common_observations":"Bulan bersama","cv_pct":"CV bulan bersama (%)","monthly_abs_pct":"Perubahan absolut rata-rata (%)","monthly_std_pct":"Simpangan perubahan bulanan (%)","monthly_pairs":"Pasangan bulanan"})
            table(export)
            st.download_button("Unduh perbandingan bulan bersama",csv_bytes(export),"fluktuasi_bulan_bersama.csv","text/csv")
        clean = summary[["commodity","observations","expected_months","coverage_pct"]].rename(columns={"commodity":"Bahan","observations":"Bulan tersedia","expected_months":"Bulan rentang","coverage_pct":"Cakupan (%)"})
        clean["Status"] = ["Riwayat <3 bulan" if r.observations<3 else "Cakupan rendah" if r.coverage_pct<coverage else "Lolos penyaringan awal" for r in summary.itertuples()]
        table(clean)
        st.download_button("Unduh kelengkapan seluruh seri",csv_bytes(clean),"cakupan_fluktuasi.csv","text/csv")


def regions_page(data, changes, province, commodity, as_of, start, threshold):
    st.html('<div class="section-tag">04 / KONTEKS ANTARWILAYAH</div>')
    st.subheader(f"Posisi harga {commodity}")
    compared = province_comparison(data,commodity,as_of)
    if compared.empty:
        st.info("Harga komoditas ini belum tersedia pada bulan pilihan. Pilih bulan atau bahan lain.")
        return
    median = compared.median_price.iloc[0]
    selected = compared[compared.province==province]
    cols = st.columns(3)
    cols[0].metric(f"Harga di {province}",rupiah(selected.price.iloc[0] if len(selected) else None))
    cols[1].metric("Median wilayah tersedia",rupiah(median))
    cols[2].metric("Selisih terhadap median",percent(selected.deviation_pct.iloc[0] if len(selected) else None),help="Median tanpa bobot dari wilayah dengan harga tersedia; bukan harga nasional resmi.")
    if selected.empty: st.info("Wilayah pilihan belum memiliki harga bulan ini; wilayah lain tetap dapat dibandingkan.")
    if "filter_all_regions" not in st.session_state: st.session_state.filter_all_regions = st.session_state.filters["all_regions"]
    all_regions = st.toggle("Lihat seluruh wilayah",key="filter_all_regions",on_change=save_filter,args=("all_regions",))
    displayed = compared if all_regions else pd.concat([compared.nlargest(4,"price"),compared.nsmallest(4,"price"),selected]).drop_duplicates("province")
    displayed = displayed.sort_values("price")
    fig = go.Figure(go.Bar(x=displayed.price,y=displayed.province,orientation="h",marker_color=[TEAL if n==province else "#becfdc" for n in displayed.province],hovertemplate="%{y}<br>Rp %{x:,.0f}<extra></extra>"))
    fig.add_vline(x=median,line_dash="dot",line_color=AMBER,annotation_text="Median",annotation_position="top right")
    fig.update_layout(xaxis_title="Harga per satuan asumsi (Rp)")
    chart(fig,"region_prices",max(310,len(displayed)*26))
    st.caption(f"Menampilkan {len(displayed)} dari {len(compared)} wilayah: empat harga tertinggi, empat terendah, dan wilayah pilihan. Warna teal menandai wilayah pilihan." if not all_regions else f"Seluruh {len(compared)} wilayah dengan data bulan pilihan.")
    st.caption("Konteks harga konsumen provinsi; belum mencakup ongkir, kualitas, atau ketersediaan pemasok. Tidak cukup untuk merekomendasikan lokasi pembelian.")
    with st.expander("Tabel seluruh wilayah dan unduhan"):
        clean = compared[["province","price","unit","deviation_pct"]].rename(columns={"province":"Wilayah","price":"Harga (Rp)","unit":"Satuan asumsi","deviation_pct":"Selisih median (%)"})
        table(clean)
        st.download_button("Unduh perbandingan wilayah",csv_bytes(clean),"perbandingan_wilayah.csv","text/csv")


def source_panel(data, changes, province, commodity, as_of, start, threshold, quality, source):
    with st.expander("Sumber & cara menghitung", expanded=False):
        st.markdown(f"**Sumber:** [Badan Pangan Nasional]({source['original_url_cited']}). Ekspor CSV dan XLSX diberikan pengguna; seluruh 33.422 baris cocok. Pengambilan langsung dari server belum diverifikasi independen.")
        recorded = datetime.fromisoformat(source["snapshot_recorded_at_utc"]).astimezone(ZoneInfo("Asia/Jakarta"))
        st.write(f"**Periode harga:** {month_label(data.date.min())}–{month_label(data.date.max())}. **Snapshot dicatat:** {recorded.strftime('%d/%m/%Y %H:%M')} WIB; berbeda dari bulan harga terakhir. Tidak diperbarui otomatis.")
        st.write(f"**Pembersihan:** {quality['raw_rows']:,} baris mentah → {quality['clean_rows']:,} observasi valid; {quality['rejected_rows']:,} baris dipisahkan. Harga kosong tidak diisi; harga nol tidak dianggap gratis. Tanda — berarti belum dapat dihitung.")
        st.markdown("**Cara menghitung:** perubahan bulanan = (harga bulan pilihan ÷ harga bulan kalender sebelumnya − 1) × 100%. Bulan kosong tidak dilewati. Median wilayah tidak berbobot. Fluktuasi membandingkan bulan pengamatan bersama; bukan prediksi harga.")
        st.info("Harga konsumen provinsi dapat berbeda dari harga pemasok. File tidak memuat satuan: kg/liter pada simulasi adalah asumsi atau pernyataan pengguna. Keranjang contoh bukan transaksi nyata; total hanya lengkap jika seluruh bahan aktif memiliki harga.")
        st.markdown(f"[Metode lengkap]({REPO}/blob/main/docs/METHODOLOGY.md) · [Jejak sumber & lisensi]({REPO}/blob/main/docs/SOURCES.md) · [Studi kasus]({REPO}/blob/main/docs/CASE_STUDY.md) · [Kode & pengujian]({REPO})")
        st.caption(f"Laporan: {province} · {commodity} · {month_label(start)}–{month_label(as_of)}; ambang {threshold}%, minimum cakupan {st.session_state.filters['coverage']}%. Skenario belanja diunduh terpisah dari Simulator anggaran.")
        signature = (province,commodity,str(as_of),str(start),threshold,st.session_state.filters["coverage"])
        if st.button("Siapkan laporan Excel",type="primary",key="prepare_excel"):
            from analyst.reporting import workbook_bytes
            with st.spinner("Menyusun laporan…"):
                months = (as_of.year-start.year)*12+as_of.month-start.month+1
                st.session_state.excel_report = (signature,workbook_bytes(data,province,as_of,months,threshold_pct=threshold,commodity=commodity,minimum_coverage=st.session_state.filters["coverage"]))
        saved = st.session_state.get("excel_report")
        if saved and saved[0]==signature:
            st.download_button("Unduh laporan Excel",saved[1],"laporan_analyst.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Unduh seluruh dataset bersih", (ROOT/"data/processed/prices.csv").read_bytes(), "harga_pangan_bersih.csv", "text/csv")
        st.download_button("Unduh baris yang dipisahkan", (ROOT/"data/processed/rejected.csv").read_bytes(), "harga_dipisahkan.csv", "text/csv")


def main():
    try:
        data, changes, quality, source = read_assets()
    except (FileNotFoundError, ValueError) as exc:
        st.error(f"Data belum siap: {exc}")
        st.stop()
    initialize(data)
    with st.sidebar:
        st.html('<div class="brand">Analyst<span>.</span></div><div class="brand-sub">Harga pangan & anggaran usaha</div>')
        st.divider()
        page = st.radio("Navigasi",PAGES,key="page",label_visibility="collapsed")
        st.divider()
        st.caption("KONTEKS ANALISIS")
        province = select_filter("province","Wilayah acuan",sorted(data.province.unique()))
        as_of = select_filter("as_of","Bulan referensi",list(pd.date_range(data.date.min(),data.date.max(),freq="MS")),month_label)
        if page in ["Ringkasan","Perbandingan wilayah","Tren & fluktuasi"]:
            select_filter("commodity","Bahan untuk detail" if page=="Ringkasan" else "Bahan pilihan",sorted(data.commodity.unique()))
        if page in ["Ringkasan","Tren & fluktuasi"]:
            select_filter("window","Rentang analisis",[6,12,24,36],lambda v:f"{v} bulan")
        if page=="Ringkasan":
            if "filter_threshold" not in st.session_state: st.session_state.filter_threshold=st.session_state.filters["threshold"]
            st.slider("Ambang pemantauan (%)",1,40,key="filter_threshold",on_change=save_filter,args=("threshold",),help="Pilihan pengguna; bukan ambang resmi pemerintah.")
        st.divider()
        st.caption(f"HARGA TERAKHIR\n\n{month_label(data.date.max())}\n\nDataset historis · bukan harga hari ini")
        st.markdown(f"[Kode sumber ↗]({REPO})")
        st.caption("Sumber & cara menghitung tersedia di bawah setiap halaman.")
    filters = st.session_state.filters
    commodity, window, threshold = filters["commodity"],filters["window"],filters["threshold"]
    start = max(as_of-pd.DateOffset(months=window-1),data.date.min())
    st.title(TITLE)
    st.caption("33.422 baris ekspor harga pangan BPN → temuan perubahan harga → simulasi dampak biaya. Jelajahi hasilnya dalam satu menit.")
    st.html(f'<div class="context"><span class="chip">{html.escape(province)}</span><span class="chip">{month_label(as_of)}</span><span class="chip">Ekspor BPN · unggahan pengguna</span><span class="chip accent">{"Skenario asumsi" if page=="Simulator anggaran" else "Data historis"}</span></div>')
    if page in ["Ringkasan","Tren & fluktuasi"] and start>as_of-pd.DateOffset(months=window-1):
        st.caption(f"Rentang efektif dimulai {month_label(start)} sesuai awal dataset; riwayat sebelumnya tidak tersedia.")
    {"Ringkasan":overview,"Simulator anggaran":budget_page,"Tren & fluktuasi":risk_page,"Perbandingan wilayah":regions_page}[page](data,changes,province,commodity,as_of,start,threshold)
    source_panel(data,changes,province,commodity,as_of,start,threshold,quality,source)
    st.html(f'<div class="footer"><span>Studi kasus portofolio · Satuan kg/liter asumsi · Harga terakhir {month_label(data.date.max())}</span><span><a href="{REPO}" target="_blank" rel="noopener noreferrer">Kode sumber ↗</a> · <a href="{REPO}/blob/main/docs/METHODOLOGY.md" target="_blank" rel="noopener noreferrer">Metodologi ↗</a></span></div>')


if __name__=="__main__":
    main()
