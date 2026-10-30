# Analisis Harga Pangan dan Simulasi Anggaran Bahan Baku UMKM Kuliner

[![Tests](https://github.com/Granbe1l/Harga-Pangan-Dashboard/actions/workflows/tests.yml/badge.svg)](https://github.com/Granbe1l/Harga-Pangan-Dashboard/actions/workflows/tests.yml)

**[Baca studi kasus dalam satu menit](docs/CASE_STUDY.md)** · [Lihat dashboard](reports/screenshots/ringkasan-first-screen.png) · [Bukti pengujian](reports/validation_summary.md)

Studi kasus portofolio **data analyst**: menghubungkan perubahan harga pangan historis dengan estimasi biaya bahan baku warung makan di Jawa Barat. Wilayah lain tersedia sebagai eksplorasi tambahan.

**Python 3.12 · Pandas · SQL/SQLite · Streamlit · Plotly · Excel**

![Ringkasan dashboard](reports/screenshots/ringkasan.png)

## Apa yang dijawab?

1. Berapa biaya keranjang contoh pada bulan pilihan?
2. Bahan mana yang paling memengaruhi perubahan biaya terhadap bulan sebelumnya?
3. Bagaimana anggaran berubah jika kebutuhan, harga pembelian, atau skenario harga diubah?

Halaman **Ringkasan** hanya menyajikan hasil berdasarkan data historis dan kuantitas contoh tetap. Halaman **Simulator anggaran** menyajikan skenario asumsi pengguna. Keduanya bukan catatan transaksi atau klaim dampak bisnis yang sudah terjadi.

Pada Jawa Barat, Oktober 2025, keranjang enam bahan contoh bernilai **Rp1.118.460**, bertambah **Rp10.687** terhadap September dengan jumlah tetap. Seluruh bahan memiliki pembanding. Nilai tersebut adalah **estimasi latihan dengan satuan asumsi**, bukan biaya usaha terverifikasi. Skenario terpisah berupa kenaikan seragam 10% menghasilkan **Rp1.230.306**, tambahan **Rp111.846**. Angka skenario bukan perubahan historis bulan tersebut.

## Apa yang membuat analisis ini menarik?

Mengurangi contoh kebutuhan telur dari 5 kg menjadi 1 kg menggeser kontributor biaya terbesar dari telur ke ayam, pada data harga yang sama. Karena itu, temuan selalu dilekatkan pada komposisi latihan, bukan digeneralisasi untuk semua usaha.

Profil A/B (enam bahan) memiliki harga lengkap pada **22 dari 58 bulan** di Jawa Barat; perubahan bulanan lengkap pada **21 bulan**. Profil C secara eksplisit memakai lima bahan tanpa minyak dan mendukung **58 dari 58 bulan**. Profil tidak pernah diganti otomatis atau disambungkan sebagai satu tren. Harga umum tetap dapat dieksplorasi sejak Januari 2021.

Mirror CSV diambil ulang dan cocok SHA-256. **Satuan sumber, kesesuaian terhadap sumber primer, serta lisensi redistribusi belum terverifikasi.** Pencocokan mirror tidak menyelesaikan tiga hal tersebut. Bukti akses tersedia di [verification.json](data/verification.json).

## Jalankan aplikasi

Dari root checkout, atau folder luar **analyst** setelah mengekstrak [paket unduhan](https://github.com/Granbe1l/Harga-Pangan-Dashboard/raw/refs/heads/main/reports/analyst.zip):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
streamlit run app.py
```

Windows PowerShell: `py -3.12 -m venv .venv`, lalu `.venv\Scripts\Activate.ps1` sebelum instalasi. Dataset lokal sudah disertakan; tidak memerlukan akun, API key, atau unduhan data untuk menjalankan aplikasi. Modul aplikasi berada di `analyst/`, gaya tampilan di `assets/dashboard.css`.

## Menu

| Menu | Kegunaan |
| --- | --- |
| Ringkasan | Biaya keranjang, perubahan historis, kelengkapan, grafik kontribusi biaya; detail bahan dan tren dapat dibuka |
| Simulator anggaran | Kuantitas per periode, harga/satuan per bahan dengan asal input, batas anggaran, penerapan massal, reset, CSV dan Excel |
| Fluktuasi historis | Perbandingan perubahan bulanan dan CV pada bulan pengamatan bersama; filter cakupan, jumlah bulan/pasangan, dan pemeriksaan seri yang dikeluarkan |
| Perbandingan wilayah | Harga wilayah pilihan, median tanpa bobot, selisih terhadap median, grafik ringkas atau seluruh wilayah |
| Data & metode | Sumber, bulan harga terakhir, tanggal pencatatan snapshot, laporan analisis, rumus, pembersihan, dan jejak sumber |

Filter ditampilkan sesuai menu dan pilihan disimpan selama sesi browser. Input keranjang, perubahan harga, harga manual, dan periode belanja bertahan saat berpindah menu. Mengubah bulan memperbarui harga snapshot; harga yang diubah pengguna dipertahankan sampai direset dan hanya digunakan selama mode harga sendiri aktif. Input tidak disimpan permanen di server atau dibagikan ke sesi pengunjung lain.

Pilihan cepat **+0%, +10%, +20%** menerapkan perubahan ke seluruh bahan terpilih. Mengubah angka pada kontrol perubahan seragam baru berlaku setelah menekan **Terapkan ke semua bahan**. Kuantitas dan harga yang sudah diisi tidak diubah. **Kembalikan contoh awal** memulihkan keranjang, kuantitas, skenario 10%, dan sumber snapshot.

## Interpretasi data

- **—** berarti belum dapat dihitung; **0** adalah hasil hitungan atau jumlah yang benar-benar nol.
- Total keranjang hanya ditampilkan jika harga seluruh bahan aktif tersedia. Subtotal bahan tersedia ditandai dan tidak dipresentasikan sebagai total lengkap.
- MoM memakai bulan kalender sebelumnya. Januari dan Maret tanpa Februari tidak menghasilkan MoM Maret.
- CV mengukur variasi tingkat harga historis; bukan probabilitas kenaikan dan belum memisahkan tren dari musiman.
- Sumber harga per bahan: **Snapshot historis**, **Diubah pengguna**, atau **Belum tersedia**. Harga kosong yang diisi pengguna tidak diam-diam diganti snapshot.
- Satuan kg/liter merupakan asumsi, karena CSV mentah tidak memiliki kolom satuan. Belum mencakup ongkir, stok, susut, biaya operasional, atau margin.
- Label periode belanja menjelaskan kuantitas pengguna; tidak mengonversi jumlah berdasarkan frekuensi.

## Dataset dan sumber

Snapshot harga **Januari 2021–Oktober 2025** terdiri dari **33.422 baris mentah**, **32.480 observasi valid**, dan **942 baris yang dipisahkan** (938 harga kosong, empat harga nonpositif). Terdapat 25 komoditas. Sebanyak 38 seri modern dan dua seri historis Papua bukan jumlah provinsi pada satu waktu.

CSV berasal dari [salinan publik Achmad Ichzan](https://github.com/achmadichzan/Prediksi_Harga_Pangan_Nasional/blob/main/harga_pangan.csv), yang mencantumkan Badan Pangan Nasional sebagai sumber asal. Belum diverifikasi terhadap versi resmi terbaru. **Tanggal pencatatan snapshot berbeda dengan bulan harga terakhir.** Aplikasi tidak memperbarui data secara otomatis. Ketentuan sumber dan izin redistribusi perlu diperiksa sebelum pemakaian komersial; lihat [Sumber](docs/SOURCES.md), [Metodologi](docs/METHODOLOGY.md), dan [Kamus data](docs/DATA_DICTIONARY.md).

## Validasi dan laporan

```bash
python -m unittest discover -s tests -v
python scripts/export_report.py --output-dir /tmp/analyst-report
python scripts/package_project.py
```

Tes memeriksa perbandingan bulan kalender, total tidak lengkap, sumber harga per bahan, state lintas halaman, penerapan massal, reset, hasil skenario, keamanan formula Excel, dan navigasi. Screenshot desktop/mobile diperbarui melalui pemeriksaan browser opsional; langkah dan batas pengujiannya tersedia di [checklist revisi](docs/REDESIGN_CHECKLIST.md).

`scripts/prepare_data.py` dapat membangun ulang CSV dan SQLite, tetapi **menulis ulang artefak data**. Untuk pemeriksaan tanpa mengubah snapshot checkout, panggil `analyst.pipeline.prepare_data()` pada direktori sementara dengan salinan `data/raw/harga_pangan.csv` dan `data/source.json`.

Ekspor analisis di menu Data & metode mengikuti filter analisis. Ekspor simulator adalah file terpisah yang memuat kebutuhan dan harga yang sedang digunakan, asal harga per baris, periode, status kelengkapan, dan total/subtotal.

## Tautan publik untuk CV

Lihat [panduan deployment](docs/DEPLOYMENT.md). Antarmuka bergaya BI dibuat langsung dengan Streamlit dan Plotly; tidak memerlukan lisensi Power BI. Link GitHub adalah kode sumber, bukan link aplikasi yang sudah dihosting. Kecepatan dan akses publik perlu diperiksa pada URL deployment sebenarnya.

## Kualitas dan batas bukti

Workflow GitHub Actions menjalankan pengujian pada push/pull request. Hasil browser lokal tetap dibedakan dari uji manusia dan deployment publik. [Rencana uji pengguna](docs/USER_TESTING.md) dan formulir unduhan sukarela tersedia; **belum ada hasil peserta manusia**. Tidak ada klaim aplikasi sudah dipakai UMKM atau meningkatkan laba.

Pada simulator, harga yang diedit dan satuan yang dinyatakan pengguna diberi sumber masing-masing. Semua bahan aktif harus memiliki harga input dan satuan yang dinyatakan agar dasar hasil disebut input pengguna; ini pun belum diaudit. Nilai lain tetap berlabel estimasi latihan. Batas anggaran hanya dibandingkan dengan total lengkap.
