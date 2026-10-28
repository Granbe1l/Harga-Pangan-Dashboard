"""Kajian deskriptif harga pangan dengan lampiran eksplorasi interaktif."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from panganwatch.analytics import (
    basket_simulation,
    comparison_frame,
    province_comparison,
    volatility_summary,
)
from panganwatch.pipeline import load_clean_data, load_quality_report

ROOT = Path(__file__).resolve().parent
MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
GREEN, ORANGE, INK = "#344f65", "#82735e", "#27343d"
TITLE = "Analisis Harga Pangan Indonesia & Simulasi Anggaran UMKM (Python & Streamlit)"
PAGES = ["Ringkasan penelitian", "Data & metode", "Volatilitas harga", "Perbandingan wilayah", "Analisis skenario", "Kesimpulan"]
CASE_QUANTITIES = {"Beras Medium": 25.0, "Daging Ayam Ras": 10.0, "Telur Ayam Ras": 5.0, "Minyak Goreng Curah": 5.0, "Cabai Rawit Merah": 2.0, "Bawang Merah": 2.0}

st.set_page_config(page_title="Kajian Harga Pangan Indonesia", page_icon="📄", layout="wide")
st.html("""<style>
  .block-container {max-width:1050px;padding:3.2rem 4rem 4rem;background:#fff;margin:1.8rem auto;}
  h1,h2,h3 {font-family:Georgia,'Times New Roman',serif!important;color:#243441!important;}
  h1 {font-size:2.15rem!important;letter-spacing:-.035rem;font-weight:600!important;line-height:1.3!important;padding-bottom:1rem!important;}
  h2 {font-size:1.42rem!important;font-weight:600!important;letter-spacing:0;margin-top:.9rem!important;}
  h3 {font-size:1.12rem!important;font-weight:600!important;}
  [data-testid="stMain"] .stMarkdown p,[data-testid="stMain"] .stMarkdown li {font-family:Georgia,'Times New Roman',serif;line-height:1.85;font-size:1.02rem;color:#303a40;}
  [data-testid="stMetric"] {border-top:1px solid #aeb7bd;padding:14px 0;border-radius:0;}
  [data-testid="stMetricValue"] {font-size:1.4rem;font-family:Georgia,'Times New Roman',serif;}
  [data-testid="stSidebar"] {border-right:1px solid #deded9;background:#f5f4f0;}
  .note {background:transparent;border-top:1px solid #cdd2d5;border-bottom:1px solid #cdd2d5;padding:14px 0;margin:12px 0 22px;line-height:1.8;font-family:Georgia,'Times New Roman',serif;}
  .sidebar-title {font-size:1.1rem;color:#344f65;font-weight:650;}
  [data-testid="stCaptionContainer"] p {font-size:.79rem!important;color:#6b747a!important;line-height:1.65!important;}
  [data-testid="stDataFrame"] {border-radius:0;}
  @media(max-width:900px) {.block-container {padding:2rem 1.25rem;margin:.5rem auto;}h1{font-size:1.8rem!important;}}
  @media print {
    [data-testid="stSidebar"],header,[data-testid="stToolbar"],[data-testid="stDownloadButton"],[data-testid="stExpander"],footer{display:none!important;}
    html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"],[data-testid="stMain"] {height:auto!important;overflow:visible!important;position:static!important;}
    .block-container {max-width:none!important;margin:0!important;padding:0!important;}
    h2,h3{break-after:avoid;}[data-testid="stPlotlyChart"]{break-inside:avoid;}
  }
  footer {visibility:hidden;}
</style>""")


def rupiah(value: float | None) -> str:
    return "—" if value is None or pd.isna(value) else "Rp " + f"{value:,.0f}".replace(",", ".")


def percent(value: float | None, signed: bool = True) -> str:
    return "—" if value is None or pd.isna(value) else f"{value:+.1f}%" if signed else f"{value:.1f}%"


def month_label(value) -> str:
    date = pd.Timestamp(value)
    return f"{MONTHS[date.month - 1]} {date.year}"


def csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8-sig")


def tidy_chart(fig, height: int = 350):
    fig.update_layout(
        template="plotly_white", height=height, margin=dict(l=8, r=15, t=20, b=16),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", size=12, color=INK),
        legend=dict(orientation="h", y=1.12, title_text=""),
        hoverlabel=dict(bgcolor="white"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#e4e6e8", zeroline=False)
    return fig


def plot(fig, key: str):
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "displayModeBar": False}, key=key)


@st.cache_data(show_spinner=False)
def read_assets():
    data = load_clean_data(ROOT)
    return data, comparison_frame(data), load_quality_report(ROOT)


def show_table(frame, key=None):
    st.dataframe(frame, hide_index=True, width="stretch", key=key)


def page_overview(data, changes, province, commodity, as_of, start, threshold):
    snapshot = changes[(changes.province == province) & (changes.date == as_of)].copy()
    current = snapshot[snapshot.commodity == commodity]
    row = current.iloc[0] if not current.empty else None
    unit = row.unit if row is not None else "satuan"
    risk = volatility_summary(data[data.province == province], start=start, end=as_of).dropna(subset=["cv_pct"])
    rises = snapshot[snapshot.mom_pct >= threshold].sort_values("mom_pct", ascending=False)
    comparable = int(snapshot.mom_pct.notna().sum())
    st.header("Abstrak")
    findings = f"Pada {month_label(as_of)}, {len(rises)} dari {comparable} komoditas yang memiliki pembanding mengalami kenaikan bulanan setidaknya {threshold:.0f}%." if comparable else "Perubahan bulanan belum dapat disimpulkan karena pembanding pada bulan kalender sebelumnya tidak tersedia."
    st.write(f"Kajian ini mendeskripsikan perubahan dan variasi harga pangan serta penggunaannya sebagai acuan simulasi anggaran belanja UMKM kuliner. Data yang digunakan merupakan salinan harga konsumen bulanan dengan 32.480 observasi valid, Januari 2021–Oktober 2025. Pembacaan saat ini difokuskan pada {province}, dengan jendela analisis {month_label(start)}–{month_label(as_of)}. Analisis menggunakan perubahan bulanan dan tahunan, koefisien variasi, serta perbandingan antarwilayah pada komoditas yang sama. {findings} Hasilnya menjadi bahan evaluasi anggaran, dengan keterbatasan bahwa harga pembelian usaha dan kuantitas konsumsi tidak tersedia dalam dataset.")
    st.caption("Kata kunci: harga pangan; analisis deskriptif; volatilitas; UMKM; simulasi anggaran.")
    st.header("1. Pendahuluan")
    st.write("Perubahan harga bahan pangan dapat mengubah kebutuhan anggaran warung makan meskipun jumlah bahan yang dibeli tetap. Harga rata-rata bulanan menyediakan konteks untuk meninjau perubahan tersebut. Namun, keputusan pembelian tetap membutuhkan informasi jumlah kebutuhan, umur simpan, dan penawaran pemasok masing-masing usaha.")
    st.markdown("Kajian ini mengajukan tiga pertanyaan:\n1. Bagaimana perubahan harga komoditas pada wilayah dan bulan yang sama?\n2. Komoditas apa yang menunjukkan variasi relatif terbesar selama periode pengamatan?\n3. Bagaimana anggaran pembelian berubah pada skenario harga dan kuantitas tertentu?")
    st.header("2. Rancangan analisis")
    st.write("Pendekatan yang digunakan adalah analisis deskriptif eksploratif atas data sekunder. Unit observasinya adalah satu wilayah–komoditas–bulan. Harga kosong dan nol dikarantina; bulan yang hilang tidak diisi. Perubahan bulanan membandingkan bulan kalender berturut-turut, sedangkan perubahan tahunan membandingkan bulan yang sama pada tahun sebelumnya. Koefisien variasi dihitung dari simpangan baku sampel dibagi rata-rata harga, dengan minimal tiga observasi.")
    st.caption("Sumber data: salinan pihak ketiga yang mencantumkan Badan Pangan Nasional sebagai sumber asal [1–2]. Rincian validasi dan batas cakupan tersedia pada bagian Data & metode.")
    st.header("3. Hasil analisis")
    st.subheader("3.1. Harga komoditas terpilih")
    st.caption(f"Tabel 1. Indikator {commodity} di {province}, {month_label(as_of)}.")
    indicators = pd.DataFrame({"Indikator": ["Harga bulan pilihan", "Perubahan bulanan (MoM)", "Perubahan tahunan (YoY)"], "Nilai": [rupiah(row.price if row is not None else None), percent(row.mom_pct if row is not None else None), percent(row.yoy_pct if row is not None else None)]})
    show_table(indicators)
    st.caption(f"Harga per {unit}; satuan merupakan asumsi kerja. Tanda — menunjukkan harga atau pembanding yang tidak tersedia, bukan nilai nol.")
    if row is None:
        st.info("Harga bahan pilihan tidak tersedia pada bulan ini. Harga dari bulan lain tidak digunakan sebagai pengganti.")

    st.subheader("3.2. Perkembangan harga dalam periode pengamatan")
    selected = data[(data.province == province) & (data.commodity == commodity) & data.date.between(start, as_of)]
    if selected.empty:
        st.info("Tidak ada harga untuk bahan dan rentang ini.")
    else:
        timeline = selected.set_index("date")["price"].reindex(pd.date_range(start, as_of, freq="MS")).rename_axis("date").reset_index()
        fig = px.line(timeline, x="date", y="price", markers=True, color_discrete_sequence=[GREEN], labels={"date": "Bulan", "price": f"Harga (Rp/{unit})"})
        fig.update_traces(line_width=2, marker_size=5, connectgaps=False, hovertemplate="%{x|%b %Y}<br>Rp %{y:,.0f}<extra></extra>")
        plot(tidy_chart(fig, 320), "overview_trend")
    st.caption(f"Gambar 1. Perkembangan harga {commodity} di {province}, {month_label(start)}–{month_label(as_of)}. Sumber: olahan snapshot [2]. Garis terputus menandakan bulan tanpa observasi.")

    st.subheader("3.3. Perubahan harga antarjenis komoditas")
    ranked = snapshot[snapshot.mom_pct > 0].nlargest(7, "mom_pct").sort_values("mom_pct")
    if ranked.empty:
        st.info("Tidak ada kenaikan positif yang dapat ditampilkan dari pasangan bulan yang tersedia.")
    else:
        fig = px.bar(ranked, x="mom_pct", y="commodity", orientation="h", color_discrete_sequence=[GREEN], labels={"mom_pct": "Perubahan bulanan (%)", "commodity": ""})
        fig.update_traces(hovertemplate="%{y}<br>%{x:.1f}%<extra></extra>")
        plot(tidy_chart(fig, 320), "overview_rises")
    st.caption(f"Gambar 2. Maksimal tujuh kenaikan positif tertinggi di {province}, {month_label(as_of)}. Hanya komoditas dengan harga pada kedua bulan kalender yang dibandingkan. Sumber: olahan snapshot [2].")

    st.subheader("3.4. Skenario anggaran pada kuantitas tetap")
    st.write("Sebagai ilustrasi, keranjang terdiri dari beras medium 25 kg, ayam ras 10 kg, telur ayam 5 kg, minyak goreng curah 5 liter, cabai rawit merah 2 kg, dan bawang merah 2 kg. Skenario menaikkan seluruh harga acuan sebesar 10% dengan kuantitas tetap. Kuantitas dan satuan ini adalah asumsi perhitungan, bukan catatan pembelian suatu usaha.")
    basket = pd.DataFrame([{"commodity": name, "quantity": quantity, "shock_pct": 10.0} for name, quantity in CASE_QUANTITIES.items()])
    scenario = basket_simulation(data, province, as_of, basket)
    st.caption(f"Tabel 2. Estimasi anggaran pada skenario kenaikan harga 10%, acuan {province}, {month_label(as_of)}.")
    show_table(pd.DataFrame({"Indikator": ["Anggaran acuan", "Anggaran skenario", "Selisih anggaran"], "Nilai": [rupiah(scenario['baseline_total']), rupiah(scenario['scenario_total']), rupiah(scenario['difference'])]}))
    if scenario['complete']:
        st.write(f"Pada keranjang ilustratif ini, anggaran berubah dari {rupiah(scenario['baseline_total'])} menjadi {rupiah(scenario['scenario_total'])}, atau bertambah {rupiah(scenario['difference'])}. Hasil belum memasukkan ongkir, susut bahan, maupun biaya operasional lainnya. Asumsi per bahan dapat ditinjau ulang pada bagian Analisis skenario.")
    else:
        st.write("Total skenario belum dapat dihitung karena ada harga bahan aktif yang tidak tersedia pada bulan pilihan. Tidak ada penggantian dengan harga bulan lain.")

    st.header("4. Pembahasan")
    if not rises.empty:
        top = rises.iloc[0]
        st.write(f"Dalam pembacaan ini, {top.commodity} mencatat kenaikan bulanan tertinggi, yaitu {percent(top.mom_pct)}. Sebanyak {len(rises)} komoditas melewati ambang eksplorasi {threshold:.0f}%. Ambang tersebut dipilih untuk menyaring bahan yang perlu ditinjau lebih lanjut; ambang ini bukan kategori risiko resmi pemerintah.")
    elif comparable:
        st.write(f"Tidak ada komoditas yang mencapai kenaikan {threshold:.0f}% pada pasangan bulan yang tersedia. Temuan ini terbatas pada {comparable} komoditas dengan pembanding dan tidak menyatakan bahwa seluruh harga stabil.")
    else:
        st.write("Keterbatasan pembanding menghalangi penarikan kesimpulan tentang perubahan bulanan pada pilihan ini.")
    if not risk.empty:
        top = risk.iloc[0]
        st.write(f"Selama jendela pengamatan, {top.commodity} memiliki koefisien variasi tertinggi sebesar {top.cv_pct:.2f}%, berdasarkan {int(top.observations)} dari {int(top.expected_months)} bulan. Variasi historis ini memberi konteks untuk skenario anggaran, tetapi tidak menunjukkan peluang kenaikan harga berikutnya.")
    st.header("5. Kesimpulan dan keterbatasan")
    st.write("Perubahan bulanan dan variasi historis dapat dibaca bersama untuk menentukan bahan yang perlu diperiksa dalam penyusunan anggaran. Implikasi finansialnya bergantung pada jumlah kebutuhan yang dimasukkan dalam analisis skenario. Kajian ini bersifat deskriptif; tidak menguji sebab perubahan harga maupun membuktikan penghematan usaha.")
    st.write("Harga merupakan rata-rata konsumen provinsi, satuan kg/liter masih berupa asumsi kerja, dan kelengkapan pengamatan berbeda antarseri. Temuan perlu ditinjau kembali dengan harga pemasok serta kebutuhan usaha yang sebenarnya.")
    with st.expander("Lampiran: tabel harga pada bulan terpilih"):
        st.caption(f"Tabel 3. Harga dan perubahan komoditas di {province}, {month_label(as_of)}.")
        table = snapshot[["commodity", "price", "unit", "mom_pct", "yoy_pct"]].rename(columns={"commodity": "Komoditas", "price": "Harga (Rp)", "unit": "Satuan asumsi", "mom_pct": "Bulanan (%)", "yoy_pct": "Tahunan (%)"})
        show_table(table)
        st.download_button("Unduh ringkasan CSV", csv_bytes(table), "ringkasan_harga.csv", "text/csv")


def page_risk(data, changes, province, commodity, as_of, start, threshold):
    st.header("Hasil analisis: volatilitas harga")
    st.write("Bagian ini membandingkan variasi relatif harga pada wilayah dan rentang waktu yang sama. Perubahan bulanan tetap dilaporkan terpisah karena mengukur perubahan jangka pendek.")
    st.caption(f"{province} · {month_label(start)}–{month_label(as_of)}")
    summary = volatility_summary(data[data.province == province], start=start, end=as_of)
    snapshot = changes[(changes.province == province) & (changes.date == as_of)][["commodity", "mom_pct", "price"]]
    summary = summary.merge(snapshot.rename(columns={"price": "selected_month_price"}), on="commodity", how="left")
    valid = summary.dropna(subset=["cv_pct"]).copy()
    st.write(f"Terdapat {len(valid)} komoditas dengan minimal tiga observasi; {int((summary.coverage_pct >= 100).sum())} seri memiliki cakupan lengkap pada rentang terpilih.")
    if valid.empty:
        st.info("Minimal tiga observasi dibutuhkan untuk membandingkan volatilitas. Coba rentang yang lebih panjang.")
    else:
        fig = px.bar(valid.nlargest(12, "cv_pct").sort_values("cv_pct"), x="cv_pct", y="commodity", orientation="h", color_discrete_sequence=[GREEN], labels={"cv_pct": "Koefisien variasi / CV (%)", "commodity": ""})
        plot(tidy_chart(fig, 430), "risk_cv")
        st.caption(f"Gambar 3. Dua belas koefisien variasi tertinggi di {province}, {month_label(start)}–{month_label(as_of)}. Sumber: olahan snapshot [2].")
        st.subheader("Interpretasi")
        top = valid.sort_values("cv_pct", ascending=False).iloc[0]
        st.write(f"{top.commodity} memiliki CV tertinggi pada pilihan ini, sebesar {top.cv_pct:.2f}%, berdasarkan {int(top.observations)} dari {int(top.expected_months)} bulan. CV dihitung sebagai simpangan baku sampel dibagi rata-rata harga. Besarnya variasi ini harus dibaca bersama jumlah observasi dan cakupan, terutama ketika periode yang tersedia berbeda antarbarang.")
        st.caption("CV menggambarkan variasi historis, bukan peluang kenaikan berikutnya. MoM tetap menggunakan bulan kalender sebelumnya, meskipun berada di luar rentang grafik.")
    columns = ["commodity", "observations", "expected_months", "coverage_pct", "cv_pct", "mom_pct", "selected_month_price"]
    table = summary[columns].rename(columns={"commodity": "Komoditas", "observations": "Bulan tersedia", "expected_months": "Bulan dalam rentang", "coverage_pct": "Cakupan (%)", "cv_pct": "CV (%)", "mom_pct": "Perubahan bulanan (%)", "selected_month_price": "Harga bulan pilihan (Rp)"})
    st.caption("Tabel 4. Koefisien variasi, cakupan pengamatan, dan perubahan bulanan per komoditas.")
    show_table(table)
    st.download_button("Unduh analisis risiko", csv_bytes(table), "analisis_risiko_harga.csv", "text/csv")


def page_regions(data, changes, province, commodity, as_of, start, threshold):
    st.header("Hasil analisis: perbandingan antarwilayah")
    st.caption(f"{commodity} · {month_label(as_of)}")
    compared = province_comparison(data, commodity, as_of)
    if compared.empty:
        st.info("Tidak ada harga pada bulan ini. Pilih komoditas atau bulan lain.")
        return
    median = float(compared.median_price.iloc[0])
    st.write(f"Pada bulan terpilih, data {commodity} tersedia pada {len(compared)} wilayah, dengan median {rupiah(median)} dan rentang {rupiah(compared.price.min())}–{rupiah(compared.price.max())} per satuan asumsi. Median merupakan nilai tengah tanpa bobot dari wilayah yang diamati, bukan rata-rata nasional resmi.")
    compared["Pilihan"] = compared.province.eq(province).map({True: "Wilayah pilihan", False: "Wilayah lain"})
    fig = px.bar(compared.sort_values("price"), x="price", y="province", color="Pilihan", color_discrete_map={"Wilayah pilihan": GREEN, "Wilayah lain": "#bdc7ce"}, orientation="h", labels={"price": "Harga (Rp per satuan asumsi)", "province": ""})
    fig.add_vline(x=median, line_dash="dot", line_color=ORANGE, annotation_text="Median", annotation_position="top right")
    fig.update_layout(yaxis=dict(categoryorder="total ascending"))
    plot(tidy_chart(fig, max(460, len(compared) * 21)), "region_prices")
    st.caption(f"Gambar 4. Distribusi harga {commodity} antarwilayah, {month_label(as_of)}. Sumber: olahan snapshot [2]. Garis putus-putus menunjukkan median wilayah yang tersedia.")
    table = compared[["province", "price", "unit", "deviation_pct"]].rename(columns={"province": "Wilayah", "price": "Harga (Rp)", "unit": "Satuan asumsi", "deviation_pct": "Selisih terhadap median (%)"})
    with st.expander("Tabel perbandingan dan unduhan"):
        show_table(table)
        st.download_button("Unduh perbandingan wilayah", csv_bytes(table), "perbandingan_wilayah.csv", "text/csv")
    st.caption("Perbandingan harga belum memperhitungkan ongkir, ketersediaan pemasok, kualitas, dan biaya distribusi. Data ini tidak cukup untuk menentukan lokasi belanja termurah secara operasional.")


def page_budget(data, changes, province, commodity, as_of, start, threshold):
    st.header("Analisis skenario anggaran belanja")
    st.write("Analisis ini menguji bagaimana perubahan harga memengaruhi anggaran pada kuantitas pembelian tetap. Keranjang awal merupakan contoh asumsi warung makan, bukan hasil survei usaha. Kuantitas dan persentase perubahan dapat disesuaikan untuk mengeksplorasi skenario lain.")
    st.caption(f"Acuan harga: {province} · {month_label(as_of)} · Tanpa ongkir, susut bahan, dan biaya operasional lain")
    available = sorted(data.commodity.unique())
    defaults = CASE_QUANTITIES
    chosen = st.multiselect("Bahan dalam keranjang", available, default=[c for c in defaults if c in available], key="basket_commodities")
    shock = st.slider("Skenario perubahan harga untuk contoh awal (%)", -50, 100, 10, 5, key="basket_shock")
    st.caption("Setiap baris dapat diubah lagi. Satuan kg/liter merupakan asumsi menurut komoditas karena CSV sumber tidak mencantumkan satuan; cek sebelum dipakai untuk belanja nyata.")
    if not chosen:
        st.info("Pilih minimal satu bahan untuk mulai menghitung.")
        return
    units = data.drop_duplicates("commodity").set_index("commodity").unit
    entry = pd.DataFrame({"Komoditas": chosen, "Satuan asumsi": [units.get(c, "satuan") for c in chosen], "Jumlah": [defaults.get(c, 1.0) for c in chosen], "Perubahan harga (%)": [float(shock)] * len(chosen)})
    edited = st.data_editor(entry, hide_index=True, width="stretch", disabled=["Komoditas", "Satuan asumsi"], column_config={"Jumlah": st.column_config.NumberColumn(min_value=0.0, step=0.5, format="%.2f"), "Perubahan harga (%)": st.column_config.NumberColumn(min_value=-100.0, max_value=500.0, step=1.0, format="%.1f")}, key="basket_editor")
    basket = edited.rename(columns={"Komoditas": "commodity", "Jumlah": "quantity", "Perubahan harga (%)": "shock_pct"})[["commodity", "quantity", "shock_pct"]]
    try:
        result = basket_simulation(data, province, as_of, basket)
    except (ValueError, TypeError) as exc:
        st.warning(f"Periksa isian keranjang: {exc}")
        return
    cols = st.columns(3)
    cols[0].metric("Anggaran acuan", rupiah(result["baseline_total"]))
    cols[1].metric("Anggaran skenario", rupiah(result["scenario_total"]))
    cols[2].metric("Selisih anggaran", rupiah(result["difference"]), percent(result["difference_pct"]), delta_color="inverse")
    if result["missing_commodities"]:
        st.warning("Total belum lengkap. Harga bulan pilihan tidak tersedia untuk: " + ", ".join(result["missing_commodities"]) + ". Pilih bulan/bahan lain atau beri jumlah nol; aplikasi tidak mengambil harga lama sebagai pengganti.")
    elif not result["complete"]:
        st.info("Isi jumlah lebih dari nol untuk minimal satu bahan.")
    else:
        st.write(f"Dengan asumsi kuantitas tetap, skenario menghasilkan perubahan estimasi anggaran {percent(result['difference_pct'])}. Nilai tersebut merupakan hasil simulasi dan belum menunjukkan perubahan biaya usaha yang benar-benar terjadi.")
    lines = result["lines"]
    fig = go.Figure()
    fig.add_bar(name="Acuan", x=lines.commodity, y=lines.baseline_cost, marker_color="#bdc7ce")
    fig.add_bar(name="Skenario", x=lines.commodity, y=lines.scenario_cost, marker_color=GREEN)
    fig.update_layout(barmode="group", yaxis_title="Estimasi belanja (Rp)")
    plot(tidy_chart(fig, 330), "budget_costs")
    st.caption("Gambar 5. Perbandingan anggaran acuan dan anggaran skenario menurut komoditas. Sumber: perhitungan dari harga snapshot dan asumsi kuantitas serta perubahan harga pengguna.")
    table = lines.rename(columns={"commodity": "Komoditas", "quantity": "Jumlah", "unit": "Satuan asumsi", "price": "Harga acuan (Rp)", "shock_pct": "Perubahan (%)", "scenario_price": "Harga skenario (Rp)", "baseline_cost": "Belanja acuan (Rp)", "scenario_cost": "Belanja skenario (Rp)", "cost_change": "Selisih (Rp)", "price_available": "Harga tersedia"})
    st.caption("Tabel 5. Rincian asumsi dan hasil perhitungan skenario anggaran.")
    show_table(table)
    downloaded = table.copy()
    downloaded.insert(0, "Wilayah", province)
    downloaded.insert(1, "Bulan acuan", as_of.strftime("%Y-%m"))
    st.download_button("Unduh skenario belanja", csv_bytes(downloaded), "skenario_belanja.csv", "text/csv")
    with st.expander("Rumus dan asumsi"):
        st.markdown("**Belanja acuan** = jumlah × harga bulan pilihan.\n\n**Harga skenario** = harga acuan × (1 + perubahan harga / 100).\n\n**Selisih anggaran** = belanja skenario − belanja acuan.\n\nHarga rata-rata konsumen provinsi hanya menjadi acuan. Tidak ada prediksi harga, data stok, pesanan pemasok, atau margin keuntungan dalam perhitungan ini.")


def page_data(data, changes, province, commodity, as_of, start, threshold):
    st.header("Data dan metode penelitian")
    quality = load_quality_report(ROOT)
    source = json.loads((ROOT / "data/source.json").read_text(encoding="utf-8"))
    st.write("Penelitian menggunakan pendekatan deskriptif eksploratif berbasis data sekunder. Unit observasinya adalah satu wilayah, satu komoditas, dan satu bulan. Hubungan sebab-akibat dan penghematan aktual tidak diuji dalam desain ini.")
    st.caption("Tabel 6. Ringkasan data dan hasil validasi snapshot.")
    validation = pd.DataFrame({"Keterangan": ["Baris mentah", "Observasi valid", "Baris dikarantina", "Komoditas", "Awal periode", "Akhir periode"], "Hasil": [str(quality['raw_rows']), str(quality['clean_rows']), str(quality['rejected_rows']), str(quality['commodity_count']), month_label(quality['period_start']), month_label(quality['period_end'])]})
    show_table(validation)
    st.write("Harga kosong dan nol dipisahkan ke file karantina. Tidak ada pengisian harga hilang atau perataan harga yang berkonflik secara diam-diam.")
    st.subheader("Sumber dan batas penggunaan")
    st.markdown("Sumber asal yang dicantumkan penyedia salinan: [Badan Pangan Nasional](https://data.badanpangan.go.id/datasetpublications/178/rata-rata-harga-pangan-bulanan-konsumen-provinsi). File yang dipakai adalah [salinan CSV pihak ketiga di GitHub](https://github.com/achmadichzan/Prediksi_Harga_Pangan_Nasional/blob/main/harga_pangan.csv). Kesesuaian dengan versi resmi terbaru serta izin redistribusi belum dikonfirmasi. Kode aplikasi ditulis terpisah dari kode penyedia salinan.")
    st.write("40 seri wilayah dalam seluruh snapshot mencakup 38 seri modern dan dua seri historis Papua. Angka tersebut bukan jumlah provinsi pada satu bulan. Seri sebelum perubahan skema 2024 dipisahkan agar tren wilayah yang berbeda tidak disambungkan.")
    with st.expander("Definisi angka yang dipakai", expanded=True):
        st.markdown("- **Bulanan / MoM:** perubahan terhadap bulan kalender sebelumnya. Jika Februari hilang, Maret tidak dibandingkan dengan Januari.\n- **Tahunan / YoY:** perubahan terhadap bulan yang sama setahun sebelumnya.\n- **CV:** standar deviasi sampel ÷ rata-rata harga × 100%; minimal tiga observasi. Bukan prediksi kenaikan harga.\n- **Cakupan:** jumlah bulan tersedia ÷ jumlah bulan dalam rentang pilihan.\n- **Median wilayah:** nilai tengah tanpa bobot dari wilayah dengan data untuk komoditas dan bulan yang sama. Bukan rata-rata nasional resmi.\n- **Satuan:** kg untuk komoditas selain minyak goreng; liter untuk minyak goreng. Ini asumsi kerja, karena CSV sumber tidak memiliki kolom satuan.\n- **Batas pemantauan:** ambang kenaikan pilihan pengguna, bukan ambang resmi pemerintah.")
    st.subheader("Data hasil pembersihan")
    filtered = data[(data.province == province) & data.date.between(start, as_of)].copy()
    show_table(filtered.head(300))
    st.caption(f"Menampilkan maksimal 300 dari {len(filtered):,} baris sesuai wilayah dan rentang pilihan. File unduhan memuat seluruh baris hasil pembersihan.")
    left, right, extra = st.columns(3)
    left.download_button("Unduh seluruh data bersih", (ROOT / "data/processed/prices.csv").read_bytes(), "harga_pangan_bersih.csv", "text/csv")
    right.download_button("Unduh baris karantina", (ROOT / "data/processed/rejected.csv").read_bytes(), "harga_pangan_karantina.csv", "text/csv")
    extra.download_button("Unduh laporan kualitas", json.dumps(quality, indent=2, ensure_ascii=False).encode(), "laporan_kualitas.json", "application/json")
    st.subheader("Laporan Excel")
    st.write("Workbook berisi data bersih, perubahan harga, risiko, perbandingan wilayah, dan catatan metode. Laporan mengikuti pilihan wilayah, komoditas, bulan, dan rentang di panel kiri.")
    signature = (province, commodity, str(as_of), str(start), threshold)
    if st.button("Siapkan laporan Excel", key="prepare_excel"):
        from panganwatch.reporting import workbook_bytes
        with st.spinner("Menyusun workbook…"):
            months = (as_of.year - start.year) * 12 + as_of.month - start.month + 1
            st.session_state["excel_report"] = (signature, workbook_bytes(data, province=province, as_of=as_of, months=months, commodity=commodity, threshold_pct=threshold))
    saved = st.session_state.get("excel_report")
    if saved and saved[0] == signature:
        st.download_button("Unduh laporan Excel", saved[1], "laporan_panganwatch.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    manuscript = ROOT / "reports/Kajian_Harga_Pangan_Jawa_Barat.pdf"
    if manuscript.exists():
        st.subheader("Naskah contoh")
        st.write("PDF berikut memuat contoh pembacaan Jawa Barat, Oktober 2025, dengan jendela November 2024–Oktober 2025. Dokumen ini tetap; perubahan filter tidak mengubah isi PDF tersebut.")
        st.download_button("Unduh naskah contoh (PDF)", manuscript.read_bytes(), manuscript.name, "application/pdf")
    with st.expander("Detail pemeriksaan dan jejak sumber"):
        st.json(quality)
        st.json(source)


def page_conclusions(data, changes, province, commodity, as_of, start, threshold):
    st.header("Kesimpulan dan implikasi")
    snapshot = changes[(changes.province == province) & (changes.date == as_of)]
    comparable = snapshot[snapshot.mom_pct.notna()]
    rises = comparable[comparable.mom_pct >= threshold].sort_values("mom_pct", ascending=False)
    risk = volatility_summary(data[data.province == province], start=start, end=as_of).dropna(subset=["cv_pct"])
    st.write(f"Kesimpulan berikut dibatasi pada {province}, bulan pembacaan {month_label(as_of)}, serta jendela variasi harga {month_label(start)}–{month_label(as_of)}. Mengubah parameter akan mengubah hasil pembacaan.")
    st.subheader("Temuan utama")
    if comparable.empty:
        st.write("Perubahan bulanan tidak dapat disimpulkan karena tidak ada pasangan harga pada bulan terpilih dan bulan kalender sebelumnya.")
    elif rises.empty:
        st.write(f"Dari {len(comparable)} komoditas yang dapat dibandingkan, tidak ada yang mencapai kenaikan {threshold:.0f}%. Hasil ini tidak mencakup komoditas tanpa pembanding dan bukan bukti bahwa seluruh harga stabil.")
    else:
        top = rises.iloc[0]
        st.write(f"Sebanyak {len(rises)} dari {len(comparable)} komoditas yang dapat dibandingkan naik setidaknya {threshold:.0f}%. Kenaikan terbesar tercatat pada {top.commodity}, dari {rupiah(top.previous_price)} menjadi {rupiah(top.price)} ({percent(top.mom_pct)}).")
    if not risk.empty:
        top = risk.iloc[0]
        st.write(f"Variasi relatif terbesar tercatat pada {top.commodity}: CV {top.cv_pct:.2f}%, berdasarkan {int(top.observations)} dari {int(top.expected_months)} bulan. Penilaian tersebut bersifat historis dan tidak menunjukkan peluang kenaikan pada periode berikutnya.")
    else:
        st.write("Jumlah observasi belum cukup untuk menyusun peringkat variasi relatif harga pada rentang terpilih.")
    st.subheader("Implikasi terhadap perencanaan belanja")
    st.write("Komoditas dengan perubahan dan variasi tinggi dapat ditempatkan sebagai prioritas peninjauan anggaran. Besar dampaknya perlu dihitung menggunakan kuantitas kebutuhan dan skenario harga yang dinyatakan secara terbuka. Temuan ini belum cukup untuk menentukan jumlah stok, mengganti pemasok, atau menyatakan adanya penghematan.")
    st.subheader("Keterbatasan dan pengembangan lanjutan")
    st.markdown("1. Harga konsumen provinsi tidak selalu sama dengan harga pembelian suatu usaha.\n2. Satuan kg/liter masih berupa asumsi karena tidak tercantum dalam CSV sumber.\n3. Kelengkapan periode dan cakupan wilayah berbeda antarseri; skema Papua sebelum 2024 dipisahkan.\n4. Sumber yang diperiksa adalah salinan pihak ketiga, belum diverifikasi terhadap versi resmi terbaru.\n5. Penelitian lanjutan dapat menambahkan catatan pembelian usaha yang diperoleh secara sah, kemudian membandingkan estimasi anggaran dengan pengeluaran aktual.")


def main():
    try:
        data, changes, quality = read_assets()
    except (FileNotFoundError, ValueError) as exc:
        st.error(f"Data belum siap: {exc}")
        st.code("python scripts/prepare_data.py", language="bash")
        st.stop()
    with st.sidebar:
        st.html('<div class="sidebar-title">Dashboard</div>')
        st.caption("Daftar isi kajian")
        st.divider()
        page = st.radio("Bagian kajian", PAGES, key="page", label_visibility="collapsed")
        with st.expander("Parameter eksplorasi", expanded=False):
            provinces = sorted(data.province.unique())
            province = st.selectbox("Wilayah acuan", provinces, index=provinces.index("Jawa Barat") if "Jawa Barat" in provinces else 0, key="province")
            commodities = sorted(data.commodity.unique())
            commodity = st.selectbox("Bahan yang dipantau", commodities, index=commodities.index("Beras Medium") if "Beras Medium" in commodities else 0, key="commodity")
            dates = list(pd.date_range(data.date.min(), data.date.max(), freq="MS"))
            as_of = st.selectbox("Bulan analisis", dates, index=len(dates) - 1, format_func=month_label, key="as_of")
            window = st.selectbox("Rentang tren & risiko", [6, 12, 24, 36], index=1, format_func=lambda n: f"{n} bulan", key="window")
            threshold = st.slider("Batas kenaikan bulanan (%)", 1, 40, 10, help="Aturan eksplorasi pilihan pengguna; bukan ambang resmi.", key="threshold")
        st.divider()
        st.caption(f"Konteks pembacaan\n\n{province}\n\n{month_label(as_of)} · {window} bulan pengamatan\n\nDataset historis, tidak diperbarui secara otomatis.")
    start = as_of - pd.DateOffset(months=window - 1)
    st.caption("KAJIAN DESKRIPTIF · DATA SEKUNDER BULANAN")
    st.title(TITLE)
    st.caption(f"Periode dataset: {month_label(data.date.min())}–{month_label(data.date.max())}\n\nFokus pembacaan: {province} · {month_label(as_of)} · Jendela analisis {window} bulan")
    st.divider()
    render = dict(zip(PAGES, [page_overview, page_data, page_risk, page_regions, page_budget, page_conclusions]))
    render[page](data, changes, province, commodity, as_of, start, threshold)
    st.divider()
    st.subheader("Referensi data")
    st.markdown("[1] Badan Pangan Nasional. [Rata-rata Harga Pangan Bulanan Tingkat Konsumen Provinsi](https://data.badanpangan.go.id/datasetpublications/178/rata-rata-harga-pangan-bulanan-konsumen-provinsi). Sumber asal yang dicantumkan penyedia salinan; belum diperiksa secara independen.\n\n[2] Achmad Ichzan. [Salinan dataset harga pangan](https://github.com/achmadichzan/Prediksi_Harga_Pangan_Nasional/blob/main/harga_pangan.csv). Snapshot yang digunakan dalam pengolahan; asal file dan hash dicatat dalam metadata proyek.")
    st.caption("Kajian deskriptif berbasis data sekunder · Pengolahan dapat ditelusuri melalui dataset, query SQL, dan catatan metode")


if __name__ == "__main__":
    main()
