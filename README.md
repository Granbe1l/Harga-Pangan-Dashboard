# Analisis Harga Pangan Indonesia & Simulasi Anggaran UMKM (Python & Streamlit)

**Studi deskriptif menggunakan data harga konsumen bulanan, Januari 2021–Oktober 2025.**

Kajian ini mendeskripsikan perubahan harga pangan, variasi historisnya, dan perbedaan harga antarwilayah. Contoh analisis menggunakan Jawa Barat dan anggaran bahan warung makan: jika harga bahan berubah, berapa perubahan anggaran untuk kuantitas yang sama? Skenario warung merupakan contoh perhitungan, bukan hasil survei atau penelitian lapangan.

Penyajian mengikuti alur laporan penelitian: pertanyaan analisis, sumber dan metode, hasil, pembahasan skenario, serta kesimpulan. Streamlit digunakan sebagai pembaca laporan interaktif agar pilihan wilayah dan periode dapat diperiksa ulang. Pengolahan menggunakan Python dan SQL/SQLite; tabel hasil tersedia dalam Excel.

![Tampilan ringkasan penelitian dengan fokus Jawa Barat](reports/screenshots/ringkasan.png)

[Baca naskah contoh dalam PDF](reports/Kajian_Harga_Pangan_Jawa_Barat.pdf). Naskah ini menggunakan fokus Jawa Barat, Oktober 2025, dengan jendela November 2024–Oktober 2025. PDF memuat narasi, grafik, tabel indikator, dan satu skenario anggaran; isinya tidak mengikuti perubahan filter setelah dokumen dibuat. Untuk menyimpan pembacaan lain sebagai PDF, buka bagian **Ringkasan penelitian**, sesuaikan parameter, lalu gunakan menu cetak browser dan pilih **Simpan sebagai PDF**.

## Pertanyaan analisis

1. Bagaimana perubahan harga bulanan dan tahunan pada komoditas dan wilayah yang dipilih?
2. Komoditas mana yang menunjukkan variasi harga relatif paling besar pada rentang pengamatan?
3. Bagaimana harga satu komoditas berbeda antarwilayah pada bulan yang sama?
4. Bagaimana skenario perubahan harga memengaruhi anggaran untuk kuantitas belanja tetap?

Desainnya deskriptif dan eksploratif. Perhitungan ini tidak menguji penyebab perubahan harga atau mengestimasi dampak suatu kebijakan. Cakupan hasil mengikuti wilayah, komoditas, dan periode yang dipilih; contoh Jawa Barat tidak mewakili seluruh UMKM Indonesia.

## Contoh hasil yang sudah dihitung

Untuk Jawa Barat pada Oktober 2025, dua komoditas naik setidaknya 10% terhadap September: **Cabai Merah Keriting 11,16%** dan **Cabai Merah Besar 10,52%**. Ambang 10% dipakai sebagai parameter pemantauan, bukan batas resmi. Dalam jendela November 2024–Oktober 2025, CV **Cabai Rawit Merah 36,85%** dengan 12 dari 12 bulan teramati.

Temuan tersebut dapat dipakai untuk memilih bahan yang lebih dulu diperiksa dalam anggaran. Hasil lengkap beserta batas interpretasinya tersedia di [ringkasan analisis](reports/analysis_summary.md), [hasil terstruktur JSON](reports/analysis_summary.json), dan [laporan Excel](reports/panganwatch_report.xlsx).

## Data yang digunakan

Pipeline menghasilkan **32.480 observasi valid** dari **33.422 baris mentah**. Sebanyak **938 harga kosong dan 4 harga tidak positif** dipisahkan ke data penolakan. Tidak ada pengisian harga buatan. Salinan ini berisi 25 komoditas dari Januari 2021 sampai Oktober 2025; kelengkapan berbeda antarseri.

Ada 40 seri wilayah: 38 label wilayah dan dua seri Papua historis yang dipisahkan agar perubahan kode/cakupan tidak tersambung sebagai satu seri. Ini **bukan berarti Indonesia mempunyai 40 provinsi pada satu waktu**. Rincian ada di `data/processed/quality_report.json`.

## Mulai menjalankan

Gunakan Python 3.12. Jalankan perintah dari direktori proyek ini.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/prepare_data.py
streamlit run app.py
```

Untuk memakai versi seluruh dependensi yang dikunci pada lingkungan pengujian, gunakan `python -m pip install -r requirements.lock.txt` sebagai pengganti instalasi `requirements.txt`.

Pada Windows PowerShell, ganti perintah aktivasi dengan:

```powershell
.venv\Scripts\Activate.ps1
```

Salinan data disertakan dalam proyek. Pembacaan laporan dengan data lokal tidak memerlukan akun, API key, atau panggilan API. Instalasi dependensi pertama kali tetap memerlukan koneksi Internet.

## Susunan laporan interaktif

1. **Ringkasan penelitian:** baca latar belakang, pertanyaan, ringkasan metode, dan temuan yang mengikuti fokus analisis.
2. **Data & metode:** periksa unit observasi, asal data, proses pembersihan, serta definisi indikator.
3. **Volatilitas harga:** bandingkan variasi historis dengan jumlah bulan teramati dan cakupannya.
4. **Perbandingan wilayah:** bandingkan satu komoditas pada satu bulan yang sama.
5. **Analisis skenario:** hitung anggaran dari kuantitas dan perubahan harga yang ditentukan pengguna.
6. **Kesimpulan:** baca rangkuman hasil, implikasi terbatas, dan kebutuhan data lanjutan.

Filter adalah alat untuk meninjau ulang hasil, bukan tambahan observasi. Ambang kenaikan dan parameter skenario merupakan asumsi pengguna. Data bulanan ini menggambarkan harga historis.

## Menyiapkan data dan laporan

```bash
python scripts/prepare_data.py
python scripts/export_report.py
```

Pipeline menyiapkan data bersih dan basis data SQLite. Laporan Excel serta ringkasan analisis disimpan di direktori `reports/`. Gunakan hasil aktual laporan untuk menulis temuan; jangan mengubah hasil simulasi menjadi klaim dampak bisnis yang telah terjadi.

Untuk membuat paket proyek yang dapat dipindahkan ke komputer lain, jalankan `python scripts/package_project.py`. Hasilnya adalah `reports/PanganWatch.zip`; lingkungan virtual dan metadata Git tidak disertakan. Paket ini bukan bukti bahwa aplikasi sudah diterbitkan di Internet.

Definisi view ada di [sql/analytics.sql](sql/analytics.sql). [sql/analysis_queries.sql](sql/analysis_queries.sql) memuat contoh query perubahan harga, cakupan data, dan perbandingan tahunan yang dapat dipelajari atau dijalankan ulang.

Alur proyek:

```text
CSV historis → validasi dan pembersihan → CSV bersih + SQLite
                                             ↓
                                     analisis SQL/Python
                                             ↓
                              laporan interaktif + Excel
```

## Validasi

```bash
python -m unittest discover -s tests -v
```

Pemeriksaan berfokus pada parsing harga, kualitas data, perbandingan bulan kalender, dan perhitungan skenario. Setelah membuka laporan, periksa satu pasangan provinsi–komoditas dengan perubahan yang tersedia, satu kondisi data kosong, dan satu keranjang yang harganya tidak lengkap.

## Prinsip analisis

- MoM membandingkan bulan sebelumnya secara tepat; YoY membandingkan bulan yang sama setahun sebelumnya. Bulan yang tidak tersedia menghasilkan nilai kosong, bukan perubahan 0%.
- Volatilitas dihitung untuk komoditas yang sama pada provinsi yang sama. Harga nominal beberapa komoditas tidak digabung sebagai satu indikator harga.
- Median provinsi adalah pembanding yang tidak diberi bobot. Angka itu bukan rata-rata nasional resmi.
- Harga keranjang harus berasal dari bulan yang dipilih. Harga lama tidak diam-diam menggantikan harga yang hilang.
- Tidak ada pengisian harga buatan atau klaim stok, penjualan, dan keuntungan dari dataset harga ini.

Definisi dan alasan pemilihannya tersedia di [metodologi](docs/METHODOLOGY.md) dan [kamus data](docs/DATA_DICTIONARY.md).

## Asal data

Data mentah yang disertakan berasal dari [salinan CSV publik oleh Achmad Ichzan](https://github.com/achmadichzan/Prediksi_Harga_Pangan_Nasional/blob/main/harga_pangan.csv). Dokumentasi penyedia salinan mengaitkannya dengan [Rata-rata Harga Pangan Bulanan Tingkat Konsumen Provinsi — Badan Pangan Nasional](https://data.badanpangan.go.id/datasetpublications/178/rata-rata-harga-pangan-bulanan-konsumen-provinsi).

Halaman sumber primer belum dapat diperiksa secara independen dalam sesi pembuatan proyek; salinan ini belum dinyatakan sebagai versi terbaru. Hak penggunaan ulang data juga belum dikonfirmasi. Detail atribusi dan versi tersedia di [catatan sumber](docs/SOURCES.md).

## Untuk portofolio

Mulai dengan pertanyaan analisis, jelaskan unit observasi dan proses pembersihan, tunjukkan satu temuan yang dapat dihitung ulang, lalu hubungkan dengan implikasinya untuk perencanaan anggaran. [Catatan untuk CV dan wawancara](docs/CV.md) membantu menyusun penjelasan berdasarkan hasil yang benar-benar diperoleh.
