"""PanganWatch — eksplorasi harga bulanan dan simulasi belanja warung makan."""

from __future__ import annotations

import html
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
GREEN, ORANGE, INK = "#087f5b", "#c16a2c", "#193e30"
PAGES = ["Ringkasan", "Risiko harga", "Perbandingan wilayah", "Simulator anggaran", "Data & metode"]
DEFAULT_BASKET = {"Beras Medium": 25.0, "Daging Ayam Ras": 10.0, "Telur Ayam Ras": 5.0, "Minyak Goreng Curah": 5.0, "Cabai Rawit Merah": 2.0, "Bawang Merah": 2.0}

st.set_page_config(page_title="PanganWatch | Harga & Anggaran", page_icon="🌿", layout="wide")
st.html("""<style>
  .block-container {max-width:1370px;padding-top:4.25rem;padding-bottom:2rem;}
  h1 {font-size:2.15rem!important;letter-spacing:-.04rem;font-weight:700!important;padding-bottom:.35rem!important;}
  h2 {font-size:1.55rem!important;letter-spacing:-.03rem;}
  h3 {font-size:1.13rem!important;}
  [data-testid="stMetric"] {background:#fff;border:1px solid #dfe7df;border-radius:7px;padding:13px 16px;}
  [data-testid="stMetricValue"] {font-size:1.55rem;}
  [data-testid="stSidebar"] {border-right:1px solid #dce5db;}
  .intro {color:#617367;font-size:.95rem;line-height:1.45;margin:0;}
  .note {background:#eaf1e9;border-left:3px solid #087f5b;padding:12px 16px;border-radius:0 5px 5px 0;margin:0 0 4px;line-height:1.55;}
  .sidebar-title {font-size:1.5rem;letter-spacing:-.04rem;color:#087f5b;font-weight:750;}
  footer {visibility:hidden;}
</style>""")


def rupiah(value: float | None) -> str:
    return "—" if value is None or pd.isna(value) else "Rp " + f"{value:,.0f}".replace(",", ".")


def percent(value: float | None, signed: bool = True, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "—"
    number = f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"
    return number.replace(".", ",") + "%"


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
    fig.update_yaxes(gridcolor="#e0e7df", zeroline=False)
    return fig


def plot(fig, key: str):
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False}, key=key)


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
    cols = st.columns(4)
    cols[0].metric(f"Harga {commodity}", rupiah(row.price if row is not None else None), help=f"Harga konsumen {commodity} di {province}, {month_label(as_of)}. Harga pembelian usaha bisa berbeda.")
    cols[0].caption(f"Per {unit} · satuan asumsi")
    cols[1].metric("Perubahan bulanan", percent(row.mom_pct if row is not None else None))
    cols[1].caption(f"{commodity} · vs {month_label(as_of - pd.DateOffset(months=1))}")
    cols[2].metric("Perubahan tahunan", percent(row.yoy_pct if row is not None else None))
    cols[2].caption(f"{commodity} · vs {month_label(as_of - pd.DateOffset(years=1))}")
    cols[3].metric("Komoditas dengan harga tersedia", str(len(snapshot)))
    cols[3].caption(f"Dari {data.commodity.nunique()} jenis · seluruh komoditas")
    if row is None:
        st.info("Harga bahan pilihan tidak tersedia pada bulan ini. Pilih bulan lain untuk melihat harganya; aplikasi tidak mengambil harga bulan sebelumnya secara otomatis.")
    comparable = snapshot[snapshot.mom_pct.notna()]
    rises = comparable[comparable.mom_pct >= threshold].sort_values("mom_pct", ascending=False)
    st.markdown("**Temuan bulan ini**")
    if not rises.empty:
        top = rises.iloc[0]
        message = f"<b>{len(rises)} dari {len(comparable)} komoditas</b> dengan pembanding naik setidaknya <b>{threshold:.0f}%</b>. Kenaikan tertinggi: <b>{html.escape(top.commodity)} {percent(top.mom_pct, digits=2)}</b>, dari {rupiah(top.previous_price)} menjadi {rupiah(top.price)} per {html.escape(top.unit)}."
    elif not comparable.empty:
        message = f"<b>Tidak ada komoditas</b> yang naik setidaknya <b>{threshold:.0f}%</b> dari {len(comparable)} pasangan bulan yang bisa dibandingkan."
        positive = comparable[comparable.mom_pct > 0].sort_values("mom_pct", ascending=False)
        if not positive.empty:
            top = positive.iloc[0]
            message += f" Kenaikan tertinggi tetap tercatat pada <b>{html.escape(top.commodity)} {percent(top.mom_pct, digits=2)}</b>."
    elif snapshot.empty:
        message = "<b>Belum ada harga pada bulan ini.</b> Pilih bulan lain untuk melihat perubahan dan menyusun anggaran."
    else:
        message = "<b>Perubahan bulanan belum bisa dihitung.</b> Harga bulan kalender sebelumnya tidak tersedia sebagai pembanding."
    st.html(f'<div class="note">{message}</div>')
    st.caption(f"Pembanding tersedia untuk {len(comparable)} dari {len(snapshot)} komoditas. Ambang {threshold:.0f}% adalah pilihan pemantauan, bukan batas resmi. Ringkasan mencakup semua bahan.")
    left, right = st.columns([1.3, 1], gap="large")
    with left:
        st.subheader(f"Tren harga {commodity}")
        selected = data[(data.province == province) & (data.commodity == commodity) & data.date.between(start, as_of)]
        if selected.empty:
            st.info("Tidak ada harga untuk bahan dan rentang ini.")
        else:
            timeline = selected.set_index("date")["price"].reindex(pd.date_range(start, as_of, freq="MS")).rename_axis("date").reset_index()
            fig = px.line(timeline, x="date", y="price", markers=True, color_discrete_sequence=[GREEN], labels={"date": "Bulan", "price": f"Harga (Rp/{unit})"})
            fig.update_traces(line_width=2.5, connectgaps=False, hovertemplate="%{x|%b %Y}<br>Rp %{y:,.0f}<extra></extra>")
            plot(tidy_chart(fig, 290), "overview_trend")
        st.caption("Bulan tanpa harga dibiarkan kosong. Grafik ini menunjukkan harga historis, bukan prediksi.")
    with right:
        st.subheader("Kenaikan terbesar bulan ini")
        ranked = comparable[comparable.mom_pct > 0].nlargest(7, "mom_pct").sort_values("mom_pct")
        if ranked.empty:
            st.info("Tidak ada kenaikan positif yang dapat ditampilkan dari pasangan bulan yang tersedia.")
        else:
            fig = px.bar(ranked, x="mom_pct", y="commodity", orientation="h", color_discrete_sequence=[GREEN], labels={"mom_pct": "Perubahan bulanan (%)", "commodity": ""})
            fig.update_traces(hovertemplate="%{y}<br>%{x:.1f}%<extra></extra>")
            plot(tidy_chart(fig, 290), "overview_rises")
        st.caption("Peringkat hanya memakai komoditas dengan harga pada kedua bulan kalender yang dibandingkan.")
    st.subheader("Contoh dampak pada anggaran")
    basket = pd.DataFrame([{"commodity": name, "quantity": quantity, "shock_pct": 10.0} for name, quantity in DEFAULT_BASKET.items()])
    example = basket_simulation(data, province, as_of, basket)
    if example["complete"]:
        st.write(f"Jika seluruh harga dalam contoh keranjang naik **10%**, estimasi belanja berubah dari **{rupiah(example['baseline_total'])}** menjadi **{rupiah(example['scenario_total'])}**. Tambahan anggarannya **{rupiah(example['difference'])}**, dengan jumlah bahan yang sama.")
    else:
        st.write("Contoh anggaran belum lengkap karena harga bulan pilihan tidak tersedia untuk: " + ", ".join(example["missing_commodities"]) + ". Harga dari bulan lain tidak dipakai sebagai pengganti.")
    st.caption("Contoh keranjang: beras medium 25 kg, ayam ras 10 kg, telur 5 kg, minyak goreng curah 5 liter, cabai rawit merah 2 kg, dan bawang merah 2 kg. Kuantitas dan satuan merupakan asumsi contoh; bukan catatan usaha. Belum termasuk ongkir, susut bahan, dan biaya operasional lain.")
    st.write("**Langkah berikutnya:** tinjau kebutuhan bahan yang naik, lalu buka Simulator anggaran untuk memakai jumlah belanjamu sendiri. Pertimbangkan umur simpan dan ruang penyimpanan; data ini tidak memuat stok atau penjualan warung.")
    with st.expander("Lihat harga dan perubahannya"):
        table = snapshot[["commodity", "price", "unit", "mom_pct", "yoy_pct"]].rename(columns={"commodity": "Komoditas", "price": "Harga (Rp)", "unit": "Satuan asumsi", "mom_pct": "Bulanan (%)", "yoy_pct": "Tahunan (%)"})
        show_table(table)
        st.download_button("Unduh ringkasan CSV", csv_bytes(table), "ringkasan_harga.csv", "text/csv")


def page_risk(data, changes, province, commodity, as_of, start, threshold):
    st.header("Fluktuasi harga bahan")
    st.write("Lihat bahan yang harganya paling berubah-ubah pada rentang pilihan. Baca hasilnya bersama jumlah bulan yang tersedia.")
    st.caption(f"{province} · {month_label(start)}–{month_label(as_of)}")
    summary = volatility_summary(data[data.province == province], start=start, end=as_of)
    snapshot = changes[(changes.province == province) & (changes.date == as_of)][["commodity", "mom_pct", "price"]]
    summary = summary.merge(snapshot.rename(columns={"price": "selected_month_price"}), on="commodity", how="left")
    valid = summary.dropna(subset=["cv_pct"]).copy()
    cols = st.columns(3)
    cols[0].metric("Bahan dengan ≥3 observasi", str(len(valid)))
    cols[1].metric(f"Kenaikan ≥{threshold:.0f}%", str(int((snapshot.mom_pct >= threshold).sum())))
    cols[2].metric("Cakupan bulan lengkap", str(int((summary.coverage_pct >= 100).sum())))
    if valid.empty:
        st.info("Minimal tiga observasi dibutuhkan untuk membandingkan volatilitas. Coba rentang yang lebih panjang.")
    else:
        left, right = st.columns([1.35, 1], gap="large")
        with left:
            st.subheader("Fluktuasi relatif harga")
            fig = px.bar(valid.nlargest(12, "cv_pct").sort_values("cv_pct"), x="cv_pct", y="commodity", orientation="h", color_discrete_sequence=[ORANGE], labels={"cv_pct": "Koefisien variasi / CV (%)", "commodity": ""})
            plot(tidy_chart(fig, 450), "risk_cv")
        with right:
            st.subheader("Cara membaca")
            st.write("CV = standar deviasi harga ÷ rata-rata harga × 100%. Nilai lebih besar berarti harga lebih berfluktuasi pada rentang yang dipilih.")
            top = valid.sort_values("cv_pct", ascending=False).iloc[0]
            st.html(f'<div class="note"><b>{html.escape(top.commodity)}</b> memiliki CV tertinggi pada pilihan ini: <b>{top.cv_pct:.1f}%</b>, berdasarkan {int(top.observations)} dari {int(top.expected_months)} bulan.</div>')
            st.write("CV tidak menunjukkan peluang kenaikan berikutnya. Cakupan yang tidak lengkap perlu dipertimbangkan sebelum membandingkan dua bahan.")
            st.caption("Perubahan bulanan tetap dihitung dari bulan kalender sebelumnya, meskipun bulan itu berada di luar rentang grafik.")
    columns = ["commodity", "observations", "expected_months", "coverage_pct", "cv_pct", "mom_pct", "selected_month_price"]
    table = summary[columns].rename(columns={"commodity": "Komoditas", "observations": "Bulan tersedia", "expected_months": "Bulan dalam rentang", "coverage_pct": "Cakupan (%)", "cv_pct": "CV (%)", "mom_pct": "Perubahan bulanan (%)", "selected_month_price": "Harga bulan pilihan (Rp)"})
    show_table(table)
    st.download_button("Unduh analisis risiko", csv_bytes(table), "analisis_risiko_harga.csv", "text/csv")


def page_regions(data, changes, province, commodity, as_of, start, threshold):
    st.header("Perbandingan harga antarwilayah")
    st.caption(f"{commodity} · {month_label(as_of)}")
    compared = province_comparison(data, commodity, as_of)
    if compared.empty:
        st.info("Tidak ada harga pada bulan ini. Pilih komoditas atau bulan lain.")
        return
    median = float(compared.median_price.iloc[0])
    cols = st.columns(3)
    cols[0].metric("Median wilayah tersedia", rupiah(median))
    cols[1].metric("Wilayah dengan data", str(len(compared)))
    cols[2].metric("Rentang harga", f"{rupiah(compared.price.min())} – {rupiah(compared.price.max())}")
    st.info("Median di sini adalah nilai tengah tanpa bobot dari wilayah yang datanya tersedia. Angka ini bukan rata-rata nasional resmi dan bukan harga pemasok.")
    compared["Pilihan"] = compared.province.eq(province).map({True: "Wilayah pilihan", False: "Wilayah lain"})
    fig = px.bar(compared.sort_values("price"), x="price", y="province", color="Pilihan", color_discrete_map={"Wilayah pilihan": GREEN, "Wilayah lain": "#b9cdbd"}, orientation="h", labels={"price": "Harga (Rp per satuan asumsi)", "province": ""})
    fig.add_vline(x=median, line_dash="dot", line_color=ORANGE, annotation_text="Median", annotation_position="top right")
    fig.update_layout(yaxis=dict(categoryorder="total ascending"))
    plot(tidy_chart(fig, max(460, len(compared) * 21)), "region_prices")
    table = compared[["province", "price", "unit", "deviation_pct"]].rename(columns={"province": "Wilayah", "price": "Harga (Rp)", "unit": "Satuan asumsi", "deviation_pct": "Selisih terhadap median (%)"})
    with st.expander("Tabel perbandingan dan unduhan"):
        show_table(table)
        st.download_button("Unduh perbandingan wilayah", csv_bytes(table), "perbandingan_wilayah.csv", "text/csv")
    st.caption("Perbandingan harga belum memperhitungkan ongkir, ketersediaan pemasok, kualitas, dan biaya distribusi. Data ini tidak cukup untuk menentukan lokasi belanja termurah secara operasional.")


def page_budget(data, changes, province, commodity, as_of, start, threshold):
    st.header("Hitung skenario belanja")
    st.write("Contoh awal: belanja bahan untuk warung makan. Ganti jumlah dan perubahan harga sesuai kebutuhanmu; angka awal hanya contoh, bukan hasil survei usaha.")
    st.caption(f"Acuan harga: {province} · {month_label(as_of)} · Tanpa ongkir, susut bahan, dan biaya operasional lain")
    available = sorted(data.commodity.unique())
    defaults = DEFAULT_BASKET
    chosen = st.multiselect("Bahan dalam keranjang", available, default=[c for c in defaults if c in available], key="basket_commodities")
    shock = st.slider("Perubahan harga contoh (%)", -50, 100, 10, 5, key="basket_shock")
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
        st.write(f"Untuk jumlah bahan di atas, estimasi belanja berubah **{percent(result['difference_pct'])}**. Angka ini hasil simulasi, bukan pengeluaran usaha yang sudah terjadi.")
    lines = result["lines"]
    fig = go.Figure()
    fig.add_bar(name="Acuan", x=lines.commodity, y=lines.baseline_cost, marker_color="#b9cdbd")
    fig.add_bar(name="Skenario", x=lines.commodity, y=lines.scenario_cost, marker_color=GREEN)
    fig.update_layout(barmode="group", yaxis_title="Estimasi belanja (Rp)")
    plot(tidy_chart(fig, 330), "budget_costs")
    table = lines.rename(columns={"commodity": "Komoditas", "quantity": "Jumlah", "unit": "Satuan asumsi", "price": "Harga acuan (Rp)", "shock_pct": "Perubahan (%)", "scenario_price": "Harga skenario (Rp)", "baseline_cost": "Belanja acuan (Rp)", "scenario_cost": "Belanja skenario (Rp)", "cost_change": "Selisih (Rp)", "price_available": "Harga tersedia"})
    show_table(table)
    downloaded = table.copy()
    downloaded.insert(0, "Wilayah", province)
    downloaded.insert(1, "Bulan acuan", as_of.strftime("%Y-%m"))
    st.download_button("Unduh skenario belanja", csv_bytes(downloaded), "skenario_belanja.csv", "text/csv")
    with st.expander("Rumus dan asumsi"):
        st.markdown("**Belanja acuan** = jumlah × harga bulan pilihan.\n\n**Harga skenario** = harga acuan × (1 + perubahan harga / 100).\n\n**Selisih anggaran** = belanja skenario − belanja acuan.\n\nHarga rata-rata konsumen provinsi hanya menjadi acuan. Tidak ada prediksi harga, data stok, pesanan pemasok, atau margin keuntungan dalam perhitungan ini.")


def page_data(data, changes, province, commodity, as_of, start, threshold):
    st.header("Data dan cara hitung")
    quality = load_quality_report(ROOT)
    source = json.loads((ROOT / "data/source.json").read_text(encoding="utf-8"))
    cols = st.columns(4)
    for col, key, title in zip(cols, ["raw_rows", "clean_rows", "rejected_rows", "commodity_count"], ["Baris mentah", "Baris untuk analisis", "Baris dikarantina", "Komoditas"]):
        col.metric(title, f"{quality.get(key, 0):,}".replace(",", "."))
    st.write("Harga kosong dan nol dipisahkan ke file karantina. Tidak ada pengisian harga hilang atau perataan harga yang berkonflik secara diam-diam.")
    st.subheader("Sumber dan batas penggunaan")
    st.markdown("Sumber asal yang dicantumkan penyedia salinan: [Badan Pangan Nasional](https://data.badanpangan.go.id/datasetpublications/178/rata-rata-harga-pangan-bulanan-konsumen-provinsi). File yang dipakai adalah [salinan CSV pihak ketiga di GitHub](https://github.com/achmadichzan/Prediksi_Harga_Pangan_Nasional/blob/main/harga_pangan.csv). Kesesuaian dengan versi resmi terbaru serta izin redistribusi belum dikonfirmasi. Kode aplikasi ditulis terpisah dari kode penyedia salinan.")
    st.info("40 seri wilayah dalam seluruh snapshot mencakup 38 seri modern dan 2 seri historis Papua. Angka tersebut bukan jumlah provinsi pada satu bulan. Seri sebelum perubahan skema 2024 dipisahkan agar tren wilayah yang berbeda tidak disambungkan.")
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
    with st.expander("Detail pemeriksaan dan jejak sumber"):
        st.json(quality)
        st.json(source)


def main():
    try:
        data, changes, quality = read_assets()
    except (FileNotFoundError, ValueError) as exc:
        st.error(f"Data belum siap: {exc}")
        st.code("python scripts/prepare_data.py", language="bash")
        st.stop()
    with st.sidebar:
        st.html('<div class="sidebar-title">PanganWatch<span style="color:#95b39b">.</span></div>')
        st.caption("Harga bahan & rencana belanja")
        st.divider()
        page = st.radio("Buka halaman", PAGES, key="page", label_visibility="collapsed")
        st.divider()
        provinces = sorted(data.province.unique())
        province = st.selectbox("Wilayah acuan", provinces, index=provinces.index("Jawa Barat") if "Jawa Barat" in provinces else 0, key="province")
        commodities = sorted(data.commodity.unique())
        commodity = st.selectbox("Bahan yang dipantau", commodities, index=commodities.index("Beras Medium") if "Beras Medium" in commodities else 0, key="commodity")
        dates = list(pd.date_range(data.date.min(), data.date.max(), freq="MS"))
        as_of = st.selectbox("Bulan analisis", dates, index=len(dates) - 1, format_func=month_label, key="as_of")
        window = st.selectbox("Rentang tren & risiko", [6, 12, 24, 36], index=1, format_func=lambda n: f"{n} bulan", key="window")
        threshold = st.slider("Batas kenaikan bulanan (%)", 1, 40, 10, help="Aturan pemantauan pilihan pengguna; bukan ambang resmi.", key="threshold")
        st.divider()
        st.caption(f"Snapshot historis\n\n{month_label(data.date.min())}–{month_label(data.date.max())}\n\nAplikasi memakai file lokal. Tidak menarik harga terbaru secara otomatis.")
    start = as_of - pd.DateOffset(months=window - 1)
    st.title("PanganWatch")
    st.html('<p class="intro">Pemantauan harga bahan dan simulasi anggaran UMKM.</p>')
    st.caption(f"{province} · {month_label(as_of)} · Data bulanan historis")
    render = dict(zip(PAGES, [page_overview, page_risk, page_regions, page_budget, page_data]))
    render[page](data, changes, province, commodity, as_of, start, threshold)
    st.divider()
    st.caption("Studi kasus portofolio · Harga konsumen provinsi sebagai acuan · Asumsi dan keterbatasan tersedia di Data & metode")


if __name__ == "__main__":
    main()
