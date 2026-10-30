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

from analyst.analytics import comparison_frame, province_comparison, volatility_summary
from analyst.pipeline import load_clean_data, load_quality_report
from analyst.planning import (DEFAULT_BASKET, historical_budget, scenario,
    apply_edits, complete_months, scenario_table, scenario_workbook)
from analyst.presentation import (TEAL, RED, NAVY, AMBER, rupiah, percent, month_label,
    table, chart, finding, csv_bytes)

ROOT = Path(__file__).resolve().parent
TITLE = "Analisis Harga Pangan dan Simulasi Anggaran Bahan Baku UMKM Kuliner"
PAGES = ["Ringkasan", "Simulator anggaran", "Fluktuasi historis", "Perbandingan wilayah", "Data & metode"]
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
    if "filters" not in st.session_state:
        st.session_state.filters = {"province": "Jawa Barat", "as_of": data.date.max(), "commodity": "Beras Medium", "window": 12, "threshold": 10, "coverage": 80, "all_regions": False}
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
    st.session_state.editor_version += 1


def overview(data, changes, province, commodity, as_of, start, threshold):
    budget = historical_budget(changes, province, as_of)
    st.html('<div class="section-tag">01 / RINGKASAN ANGGARAN · DATA HISTORIS</div>')
    cols = st.columns(3)
    cols[0].metric("Biaya keranjang bulan pilihan", rupiah(budget["total"]), help="Keranjang contoh enam bahan dengan kuantitas tetap; bukan catatan pembelian usaha.")
    cols[1].metric("Perubahan biaya vs bulan lalu", rupiah(budget["delta"]), percent(budget["delta_pct"]), delta_color="inverse")
    cols[2].metric("Kelengkapan harga keranjang", f"{budget['available']} / {budget['count']} bahan")
    if budget["delta"] is not None:
        movement = "bertambah" if budget["delta"] > 0 else "berkurang" if budget["delta"] < 0 else "tetap"
        finding(f"Dengan jumlah belanja tetap, biaya keranjang <b>{movement} {rupiah(abs(budget['delta']))}</b> dibanding {month_label(as_of - pd.DateOffset(months=1))}. Harga kedua bulan tersedia untuk seluruh {budget['count']} bahan.")
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
        st.subheader("Yang perlu diperhatikan")
        positive = lines[lines.impact > 0] if not lines.empty else lines
        if not positive.empty:
            top = positive.iloc[-1]
            st.markdown(f"**{top.commodity}** memberi tambahan biaya terbesar: **{rupiah(top.impact)}**.")
            st.write("Tinjau jumlah kebutuhan bahan ini saat menyiapkan anggaran berikutnya.")
        elif not lines.empty:
            st.write("Tidak ada tambahan biaya pada bahan yang memiliki pembanding. Periksa rincian sebelum mengubah anggaran.")
        else:
            st.write("Mulai dari bulan dengan data pembanding yang tersedia untuk membaca perubahan biaya.")
        st.button("Coba simulasi belanja →", type="primary", width="stretch", on_click=navigate, args=("Simulator anggaran",))
        with st.expander("Asumsi keranjang contoh"):
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
        if "filter_threshold" not in st.session_state:
            st.session_state.filter_threshold = threshold
        threshold = st.slider("Ambang pemantauan kenaikan (%)",1,40,key="filter_threshold",on_change=save_filter,args=("threshold",),help="Pilihan pemantauan pengguna, bukan ambang pemerintah.")
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
        rows.append({"Bahan":name,"Satuan":units[name],"Jumlah":row["quantity"],"Perubahan (%)":row["shock_pct"],"Harga acuan (Rp)":price,"Sumber":source})
    entry = pd.DataFrame(rows)
    st.subheader("Rincian kebutuhan")
    st.caption("Klik sel Jumlah atau Perubahan (%) untuk mengedit. Harga yang kamu ubah disimpan selama sesi, termasuk saat berpindah menu atau bulan.")
    if manual:
        st.caption("Harga simulasi dapat diedit; nilai awal dari snapshot. Sumber per bahan berubah hanya ketika harga pada baris tersebut diedit. Nilai kosong tetap dianggap belum tersedia.")
    key = 'budget_editor_' + str(st.session_state.editor_version)
    st.data_editor(entry,hide_index=True,width="stretch",disabled=["Bahan","Satuan","Sumber"] + ([] if manual else ["Harga acuan (Rp)"]),
        column_config={"Jumlah":st.column_config.NumberColumn(min_value=0.0,step=.5,format="%.2f"),"Perubahan (%)":st.column_config.NumberColumn(min_value=-100.0,max_value=500.0,step=1.0,format="%.1f"),"Harga acuan (Rp)":st.column_config.NumberColumn(min_value=1.0,format="localized")},
        key=key,on_change=commit_editor)
    # Also consume editor deltas on programmatic reruns; real browser edits use the callback.
    if key in st.session_state and st.session_state[key].get("edited_rows"):
        st.session_state.plan = apply_edits(st.session_state.plan,chosen,st.session_state[key])
    try:
        result = scenario(data,province,as_of,st.session_state.plan,chosen,manual)
    except (ValueError, TypeError) as exc:
        st.warning(f"Periksa isian keranjang: {exc}")
        return
    with results, st.container(border=True):
        st.subheader("Hasil skenario")
        st.metric("Anggaran acuan",rupiah(result["baseline_total"]))
        st.metric("Anggaran skenario",rupiah(result["scenario_total"]))
        st.metric("Selisih anggaran",rupiah(result["difference"]),percent(result["difference_pct"]),delta_color="inverse")
    lines = result["lines"]
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
    st.subheader("Bahan mana yang paling berubah-ubah?")
    st.caption(f"{month_label(start)}–{month_label(as_of)} · Seluruh bahan di {province}")
    if "filter_coverage" not in st.session_state: st.session_state.filter_coverage = st.session_state.filters["coverage"]
    coverage = st.select_slider("Minimum cakupan data (%)",options=[0,50,80,100],key="filter_coverage",on_change=save_filter,args=("coverage",),help="CV memerlukan minimal tiga observasi; cakupan adalah bagian bulan dengan harga tersedia dalam rentang efektif.")
    summary = volatility_summary(data[data.province==province],start,as_of)
    valid = summary[(summary.observations>=3)&(summary.coverage_pct>=coverage)].dropna(subset=["cv_pct"])
    cols = st.columns(3)
    cols[0].metric("Bahan memenuhi kriteria",str(len(valid)))
    cols[1].metric("Minimum cakupan",f"{coverage}%")
    cols[2].metric("Bulan dalam rentang",str((as_of.year-start.year)*12+as_of.month-start.month+1))
    if valid.empty:
        st.info("Riwayat belum cukup atau cakupan tidak memenuhi kriteria. CV memerlukan minimal tiga harga bulanan. Pilih bulan lebih akhir atau turunkan batas cakupan; memperpanjang rentang sebelum awal dataset tidak menambah data.")
    else:
        top = valid.iloc[0]
        finding(f"<b>{html.escape(top.commodity)}</b> memiliki fluktuasi relatif tertinggi: <b>{percent(top.cv_pct,signed=False)}</b>, berdasarkan {int(top.observations)} dari {int(top.expected_months)} bulan.")
        ranked = valid.head(10).sort_values("cv_pct")
        fig = px.bar(ranked,x="cv_pct",y="commodity",orientation="h",color_discrete_sequence=[TEAL],custom_data=["observations","expected_months","coverage_pct"],labels={"cv_pct":"Koefisien variasi (%)","commodity":""})
        fig.update_traces(hovertemplate="%{y}<br>CV: %{x:.1f}%<br>%{customdata[0]} dari %{customdata[1]} bulan<br>Cakupan: %{customdata[2]:.1f}%<extra></extra>")
        chart(fig,"risk_cv",max(280,len(ranked)*30))
    st.caption("CV mengukur variasi tingkat harga historis. Nilai tinggi bukan peluang harga naik; ukuran ini belum memisahkan tren dan pola musiman.")
    with st.expander("Tabel lengkap, seri cakupan rendah, dan unduhan"):
        clean = summary[["commodity","observations","expected_months","coverage_pct","cv_pct"]].rename(columns={"commodity":"Bahan","observations":"Bulan tersedia","expected_months":"Bulan rentang","coverage_pct":"Cakupan (%)","cv_pct":"CV (%)"})
        clean["Status"] = ["Riwayat <3 bulan" if r.observations<3 else "Cakupan rendah" if r.coverage_pct<coverage else "Memenuhi kriteria" for r in summary.itertuples()]
        table(clean)
        st.download_button("Unduh analisis fluktuasi",csv_bytes(clean),"fluktuasi_historis.csv","text/csv")
        st.markdown("**CV** = standar deviasi sampel ÷ rata-rata harga × 100%. Minimum tiga observasi adalah batas perhitungan, bukan jaminan kekuatan analisis. Bandingkan seri pada rentang yang sama dan periksa cakupan datanya.")


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


def data_page(data, changes, province, commodity, as_of, start, threshold, quality, source):
    st.html('<div class="section-tag">05 / SUMBER, METODE & LAPORAN</div>')
    cols = st.columns(3)
    cols[0].metric("Observasi valid",f"{quality['clean_rows']:,}".replace(",","."))
    cols[1].metric("Komoditas",str(quality["commodity_count"]))
    cols[2].metric("Harga terakhir",month_label(data.date.max()))
    recorded = datetime.fromisoformat(source["snapshot_recorded_at_utc"]).astimezone(ZoneInfo("Asia/Jakarta"))
    st.write(f"**Periode harga:** {month_label(data.date.min())}–{month_label(data.date.max())}. **Snapshot dicatat:** {recorded.strftime('%d/%m/%Y %H:%M')} WIB. Tanggal pencatatan bukan bulan harga terbaru.")
    st.markdown(f"**Sumber:** [salinan CSV publik]({source['mirror_repository']}) yang mencantumkan [Badan Pangan Nasional]({source['original_url_cited']}) sebagai sumber asal. Belum diverifikasi terhadap versi resmi terbaru.")
    finding("Harga konsumen provinsi menjadi acuan analisis historis. Satuan kg/liter adalah asumsi; harga usaha dan pemasok dapat berbeda. Aplikasi tidak memperbarui harga secara otomatis.","BATAS PENGGUNAAN")
    st.subheader("Unduh laporan analisis")
    st.caption("Mengikuti wilayah, bahan, bulan, dan rentang pilihan. Skenario yang kamu edit diunduh terpisah dari menu Simulator anggaran.")
    signature = (province,commodity,str(as_of),str(start),threshold)
    if st.button("Siapkan laporan Excel",type="primary",key="prepare_excel"):
        from analyst.reporting import workbook_bytes
        with st.spinner("Menyusun laporan…"):
            months = (as_of.year-start.year)*12+as_of.month-start.month+1
            st.session_state.excel_report = (signature,workbook_bytes(data,province,as_of,months,threshold_pct=threshold,commodity=commodity))
    saved = st.session_state.get("excel_report")
    if saved and saved[0]==signature:
        st.download_button("Unduh laporan Excel",saved[1],"laporan_analyst.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with st.expander("Pratinjau data dan unduhan CSV"):
        filtered = data[(data.province==province)&data.date.between(start,as_of)]
        clean = filtered[["province","commodity","date","price","unit"]].rename(columns={"province":"Wilayah","commodity":"Bahan","date":"Bulan","price":"Harga (Rp)","unit":"Satuan asumsi"})
        table(clean.head(10))
        st.caption(f"Pratinjau 10 dari {len(clean):,} baris sesuai wilayah dan rentang. Unduhan pilihan memuat seluruh baris pada filter ini; unduhan dataset memuat seluruh wilayah.")
        st.download_button("Unduh data sesuai pilihan",csv_bytes(clean),"harga_pilihan.csv","text/csv")
        st.download_button("Unduh seluruh dataset bersih",(ROOT/"data/processed/prices.csv").read_bytes(),"harga_pangan_bersih.csv","text/csv")
    with st.expander("Rumus dan aturan perhitungan"):
        st.markdown("""- **Perubahan bulanan:** harga bulan pilihan ÷ harga bulan kalender sebelumnya − 1. Bulan kosong tidak dilewati.
- **Perubahan tahunan:** perbandingan dengan bulan yang sama tahun sebelumnya.
- **Dampak anggaran historis:** selisih harga dua bulan × jumlah contoh tetap. Ini estimasi pada keranjang contoh, bukan transaksi nyata.
- **Total lengkap:** hanya diterbitkan jika seluruh bahan aktif memiliki harga. Subtotal selalu ditandai.
- **CV:** standar deviasi sampel ÷ rata-rata × 100%; minimal tiga observasi, dengan pilihan cakupan. Belum memisahkan tren dan musiman.
- **Cakupan:** bulan dengan harga ÷ bulan dalam rentang efektif. Awal rentang dibatasi awal dataset.
- **Median wilayah:** nilai tengah tanpa bobot; bukan rata-rata nasional resmi.
- **Satuan:** kg, atau liter untuk minyak goreng, merupakan asumsi karena CSV sumber tidak memiliki kolom satuan.""")
    with st.expander("Pembersihan, kualitas, dan wilayah historis"):
        st.write(f"{quality['raw_rows']:,} baris mentah → {quality['clean_rows']:,} observasi valid; {quality['rejected_rows']:,} baris dipisahkan. Harga hilang tidak diisi dan harga nol tidak menjadi harga belanja.")
        st.write("38 seri modern dan dua seri historis Papua bukan jumlah provinsi pada satu waktu. Seri sebelum perubahan skema 2024 dipisahkan agar wilayah dengan cakupan berbeda tidak disambungkan.")
        st.download_button("Unduh baris yang dipisahkan",(ROOT/"data/processed/rejected.csv").read_bytes(),"harga_dipisahkan.csv","text/csv")
        st.download_button("Unduh laporan kualitas",json.dumps(quality,ensure_ascii=False,indent=2).encode(),"kualitas_data.json","application/json")
    with st.expander("Jejak sumber dan lisensi"):
        st.write(source["license_status"])
        st.code(source["raw_sha256"],language=None)
        st.caption("SHA-256 snapshot CSV mentah; tanggal pencatatan disimpan dalam metadata, tidak mengikuti jam saat dashboard dibuka.")
        st.json(source)
    with st.expander("Tentang proyek dan kode sumber"):
        st.write("Studi kasus portofolio data analyst untuk anggaran warung makan di Jawa Barat; wilayah lain tersedia untuk eksplorasi. Dibangun dengan Python, Pandas, SQL/SQLite, Streamlit, Plotly, dan Excel.")
        st.markdown(f"[Kode sumber]({REPO}) · [Metodologi]({REPO}/blob/main/docs/METHODOLOGY.md) · [Pengujian]({REPO}/tree/main/tests)")
        st.caption("Tampilan bergaya BI dibangun langsung di Streamlit. Proyek ini tidak memerlukan akun atau lisensi Power BI.")


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
        if page in ["Ringkasan","Perbandingan wilayah","Data & metode"]:
            select_filter("commodity","Bahan untuk detail" if page=="Ringkasan" else "Bahan pilihan",sorted(data.commodity.unique()))
        if page in ["Ringkasan","Fluktuasi historis","Data & metode"]:
            select_filter("window","Rentang analisis",[6,12,24,36],lambda v:f"{v} bulan")
        st.divider()
        st.caption(f"HARGA TERAKHIR\n\n{month_label(data.date.max())}\n\nDataset historis · bukan harga hari ini")
        st.markdown(f"[Kode sumber ↗]({REPO})")
        st.button("Tentang proyek",on_click=navigate,args=("Data & metode",),width="stretch")
    filters = st.session_state.filters
    commodity, window, threshold = filters["commodity"],filters["window"],filters["threshold"]
    start = max(as_of-pd.DateOffset(months=window-1),data.date.min())
    st.title(TITLE)
    st.caption("Studi kasus warung makan di Jawa Barat: pahami perubahan biaya bahan, lalu uji anggaran belanjamu.")
    st.html(f'<div class="context"><span class="chip">{html.escape(province)}</span><span class="chip">{month_label(as_of)}</span><span class="chip accent">{"Skenario asumsi" if page=="Simulator anggaran" else "Data historis"}</span></div>')
    if page in ["Ringkasan","Fluktuasi historis","Data & metode"] and start>as_of-pd.DateOffset(months=window-1):
        st.caption(f"Rentang efektif dimulai {month_label(start)} sesuai awal dataset; riwayat sebelumnya tidak tersedia.")
    if page=="Data & metode":
        data_page(data,changes,province,commodity,as_of,start,threshold,quality,source)
    else:
        {"Ringkasan":overview,"Simulator anggaran":budget_page,"Fluktuasi historis":risk_page,"Perbandingan wilayah":regions_page}[page](data,changes,province,commodity,as_of,start,threshold)
    st.html(f'<div class="footer"><span>Studi kasus portofolio · Satuan kg/liter asumsi · Harga terakhir {month_label(data.date.max())}</span><span><a href="{REPO}" target="_blank" rel="noopener noreferrer">Kode sumber ↗</a> · <a href="{REPO}/blob/main/docs/METHODOLOGY.md" target="_blank" rel="noopener noreferrer">Metodologi ↗</a></span></div>')


if __name__=="__main__":
    main()
