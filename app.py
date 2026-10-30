"""Historical food-price trends, fluctuations, and provincial comparisons."""
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
from analyst.presentation import (TEAL, RED, NAVY, AMBER, rupiah, percent, month_label,
    table, chart, finding, csv_bytes)

ROOT = Path(__file__).resolve().parent
TITLE = "Analisis Tren dan Perbandingan Harga Pangan Antarprovinsi"
PAGES = ["Ringkasan", "Tren & fluktuasi", "Perbandingan wilayah"]
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


def initialize(data):
    defaults = {"province":"Jawa Barat","as_of":data.date.max(),"commodity":"Beras Medium","window":12,"threshold":10,"coverage":80,"all_regions":False}
    if "filters" not in st.session_state: st.session_state.filters = {}
    for key, value in defaults.items(): st.session_state.filters.setdefault(key,value)
    if st.session_state.get("page") not in PAGES:
        st.session_state.page = PAGES[0]


def price_overview(data, changes, province, commodity, as_of, start, threshold):
    observed=monthly_findings(changes,province,as_of,threshold)
    st.html('<div class="section-tag">01 / TEMUAN HARGA BULANAN</div>')
    cols=st.columns(3)
    cols[0].metric("Komoditas dengan harga",f"{observed['available']} / {observed['universe']}")
    cols[1].metric(f"Naik ≥{threshold}% bulanan",str(observed['alert_count']) if observed['alert_count'] is not None else "—")
    top=observed['top_rise']
    cols[2].metric(f"Kenaikan tertinggi · {top['commodity']}" if top else "Kenaikan tertinggi",percent(top['mom_pct'],digits=2) if top else "—")
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
            st.write(f"**{top['commodity']}** mencatat kenaikan tertinggi pada wilayah dan bulan pilihan. Bandingkan dengan riwayatnya untuk melihat apakah kenaikan serupa pernah terjadi.")
        else:st.write("Kenaikan belum terlihat atau belum bisa dihitung dari pasangan bulan yang tersedia.")
        st.write("Gunakan **Tren & fluktuasi** untuk melihat riwayat bahan, atau **Perbandingan wilayah** untuk menempatkan harga dalam konteks antarprovinsi.")
    if top:
        history_changes=changes[(changes.province==province)&(changes.commodity==top['commodity'])&changes.date.between(start,as_of)].dropna(subset=['mom_pct'])
        if len(history_changes)>=2:
            repeats=int((history_changes.mom_pct>=threshold).sum())
            st.write(f"**Apakah kenaikan ini berulang?** {top['commodity']} naik ≥{threshold}% pada **{repeats} dari {len(history_changes)} pasangan bulan** dengan pembanding, dalam rentang {month_label(start)}–{month_label(as_of)}. Ini frekuensi historis pada data tersedia, bukan peluang kenaikan berikutnya.")
    st.caption("Persentase membandingkan seri bahan yang sama pada dua bulan. Harga mengikuti angka sumber; satuannya tidak tercantum pada ekspor.")
    with st.expander("Detail bahan pilihan & riwayat"):
        selected=observed['snapshot'][observed['snapshot'].commodity==commodity]
        row=selected.iloc[0] if len(selected) else None
        st.write(f"**{commodity}** · Harga sumber: **{rupiah(row.price if row is not None else None)}** · Bulanan: **{percent(row.mom_pct if row is not None else None)}** · Tahunan: **{percent(row.yoy_pct if row is not None else None)}**")
        st.caption(f"{province} · {month_label(start)}–{month_label(as_of)}. Angka harga mengikuti file; satuan tidak dinyatakan pada ekspor.")
        history=data[(data.province==province)&(data.commodity==commodity)&data.date.between(start,as_of)][['date','price']].rename(columns={'date':'Bulan','price':'Harga sumber (Rp)'})
        if history.empty:st.info("Tidak ada harga bahan pilihan pada rentang ini.")
        else:table(history,height=250)


def risk_page(data, changes, province, commodity, as_of, start, threshold):
    st.html('<div class="section-tag">02 / TREN & FLUKTUASI HARGA</div>')
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
    st.html('<div class="section-tag">03 / KONTEKS ANTARWILAYAH</div>')
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
    fig.update_layout(xaxis_title="Harga sumber (Rp)")
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
        st.info("Harga konsumen provinsi dapat berbeda dari harga toko atau pemasok. File sumber tidak mencantumkan satuan; angka harga ditampilkan sebagaimana tercatat. Analisis ini bukan prediksi atau rekomendasi lokasi pembelian.")
        st.markdown(f"[Metode lengkap]({REPO}/blob/main/docs/METHODOLOGY.md) · [Jejak sumber & lisensi]({REPO}/blob/main/docs/SOURCES.md) · [Studi kasus]({REPO}/blob/main/docs/CASE_STUDY.md) · [Kode & pengujian]({REPO})")
        st.caption(f"Laporan: {province} · {commodity} · {month_label(start)}–{month_label(as_of)}; ambang {threshold}%, minimum cakupan {st.session_state.filters['coverage']}%.")
        signature = (province,commodity,str(as_of),str(start),threshold,st.session_state.filters["coverage"])
        if st.button("Siapkan laporan Excel",type="primary",key="prepare_excel"):
            from analyst.reporting import workbook_bytes
            with st.spinner("Menyusun laporan…"):
                months = (as_of.year-start.year)*12+as_of.month-start.month+1
                st.session_state.excel_report = (signature,workbook_bytes(data,province,as_of,months,threshold_pct=threshold,commodity=commodity,minimum_coverage=st.session_state.filters["coverage"]))
        saved = st.session_state.get("excel_report")
        if saved and saved[0]==signature:
            st.download_button("Unduh laporan Excel",saved[1],"laporan_analyst.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Unduh seluruh dataset bersih", csv_bytes(data.drop(columns=["unit","unit_assumed"],errors="ignore")), "harga_pangan_bersih.csv", "text/csv")
        st.download_button("Unduh baris yang dipisahkan", (ROOT/"data/processed/rejected.csv").read_bytes(), "harga_dipisahkan.csv", "text/csv")


def main():
    try:
        data, changes, quality, source = read_assets()
    except (FileNotFoundError, ValueError) as exc:
        st.error(f"Data belum siap: {exc}")
        st.stop()
    initialize(data)
    with st.sidebar:
        st.html('<div class="brand">Analyst<span>.</span></div><div class="brand-sub">Tren harga pangan antarprovinsi</div>')
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
    st.caption(f"Studi historis {month_label(data.date.min())}–{month_label(data.date.max())} · Tren, fluktuasi, dan perbandingan harga konsumen provinsi. Data tidak diperbarui otomatis.")
    st.html(f'<div class="context"><span class="chip">{html.escape(province)}</span><span class="chip">{month_label(as_of)}</span><span class="chip">Sumber: BPN</span><span class="chip accent">Data historis</span></div>')
    if page in ["Ringkasan","Tren & fluktuasi"] and start>as_of-pd.DateOffset(months=window-1):
        st.caption(f"Rentang efektif dimulai {month_label(start)} sesuai awal dataset; riwayat sebelumnya tidak tersedia.")
    {"Ringkasan":price_overview,"Tren & fluktuasi":risk_page,"Perbandingan wilayah":regions_page}[page](data,changes,province,commodity,as_of,start,threshold)
    source_panel(data,changes,province,commodity,as_of,start,threshold,quality,source)
    st.html(f'<div class="footer"><span>Studi harga konsumen provinsi · Harga terakhir {month_label(data.date.max())}</span><span><a href="{REPO}" target="_blank" rel="noopener noreferrer">Kode sumber ↗</a> · <a href="{REPO}/blob/main/docs/METHODOLOGY.md" target="_blank" rel="noopener noreferrer">Metodologi ↗</a></span></div>')


if __name__=="__main__":
    main()
