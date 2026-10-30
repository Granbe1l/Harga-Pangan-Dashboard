# Analisis Tren dan Perbandingan Harga Pangan Antarprovinsi

[![Tests](https://github.com/Granbe1l/Harga-Pangan-Dashboard/actions/workflows/tests.yml/badge.svg)](https://github.com/Granbe1l/Harga-Pangan-Dashboard/actions/workflows/tests.yml)

Dashboard untuk menelusuri tren harga pangan bulanan, membandingkan fluktuasi komoditas, dan melihat perbedaan harga antarprovinsi. Analisis awal berfokus pada Jawa Barat; provinsi lain dapat dipilih melalui filter.

Sumber: [Badan Pangan Nasional](https://data.badanpangan.go.id/datasetpublications/178/rata-rata-harga-pangan-bulanan-konsumen-provinsi) · Januari 2021–Oktober 2025. Data historis, tidak diperbarui otomatis.

**Python · Pandas · Streamlit · Plotly · Excel**

[Buka dashboard](https://harga-pangan-dashboard-candy.streamlit.app/) · [Studi kasus](docs/CASE_STUDY.md) · [Sumber data](docs/SOURCES.md) · [Metode](docs/METHODOLOGY.md) · [Hasil pengujian](reports/validation_summary.md)

## Temuan utama

Pada **Jawa Barat, Oktober 2025**:

- Harga tersedia untuk **25 komoditas**; **24** memiliki pembanding September. Daging kerbau segar (lokal) tidak memiliki harga September sehingga perubahan bulanannya tidak dihitung.
- **Dua komoditas naik setidaknya 10%**. Cabai merah keriting mencatat kenaikan tertinggi, **11,16%**.
- Cabai merah keriting naik setidaknya 10% pada **4 dari 12 pasangan bulan** dalam rentang November 2024–Oktober 2025. Angka ini menggambarkan riwayat yang tersedia, bukan peluang kenaikan berikutnya.

Ringkasan kenaikan dua digit memakai batas tetap 10%, bukan batas resmi pemerintah. Perincian hasil dan cakupan pengamatan tersedia dalam [studi kasus](docs/CASE_STUDY.md).

![Ringkasan dashboard](reports/screenshots/ringkasan-first-screen.png)

## Fitur

| Menu | Isi |
| --- | --- |
| Ringkasan | Harga tersedia, kenaikan bulanan, dan konteks historis |
| Tren & fluktuasi | Riwayat komoditas pilihan dan perbandingan fluktuasi pada bulan pengamatan yang sama |
| Perbandingan provinsi | Harga provinsi pilihan, median provinsi tersedia, dan selisih terhadap median |

Bagian **Sumber & cara menghitung** tersedia di bawah setiap halaman. Pilihan filter bertahan selama sesi.

## Data

Sumber: [Badan Pangan Nasional — Rata-rata Harga Pangan Bulanan Tingkat Konsumen Provinsi](https://data.badanpangan.go.id/datasetpublications/178/rata-rata-harga-pangan-bulanan-konsumen-provinsi).

Dataset mencakup **Januari 2021–Oktober 2025**, dengan **33.422 baris mentah**, **32.480 observasi valid**, dan **942 baris yang dipisahkan**: 938 harga kosong dan empat harga nol. CSV digunakan untuk pemrosesan; XLSX disimpan sebagai pembanding. Seluruh baris kedua format cocok setelah normalisasi teks.

Berkas diterima sebagai ekspor dari publikasi tersebut. Pemeriksaan dilakukan pada berkas lokal; unduhan langsung dari server tidak diverifikasi secara independen. Nama berkas, hash, dan hasil pencocokan tersedia pada [catatan penerimaan](data/raw/primary/receipt.json).

### Batas penggunaan

- Data bersifat historis dan tidak diperbarui otomatis.
- Harga konsumen provinsi dapat berbeda dari harga toko atau pemasok.
- File sumber tidak mencantumkan satuan. Harga ditampilkan mengikuti angka sumber; laporan analisis tidak menyertakan kolom satuan asumsi.
- Harga kosong tidak diisi. Tanda **—** berarti belum dapat dihitung; **0** adalah hasil hitungan yang benar-benar nol.
- Analisis tidak menguji penyebab perubahan harga dan tidak memprediksi harga berikutnya. Perbandingan provinsi belum mencakup ongkir, kualitas, atau pemasok.

Rincian pembersihan dan rumus tersedia di [metodologi](docs/METHODOLOGY.md) dan [kamus data](docs/DATA_DICTIONARY.md).

## Menjalankan aplikasi

Gunakan Python **3.12** dan jalankan dari root repository:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
streamlit run app.py
```

Windows PowerShell: aktifkan lingkungan dengan `.venv\Scripts\Activate.ps1`. Data disertakan; API key tidak diperlukan.

[Pengujian](docs/TESTING.md) · [Pemrosesan data](docs/DATA_PIPELINE.md) · [Deployment](docs/DEPLOYMENT.md) · [Paket unduhan](https://github.com/Granbe1l/Harga-Pangan-Dashboard/raw/refs/heads/main/reports/analyst.zip)
