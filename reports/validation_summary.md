# Hasil pengujian

- **49 tes lulus:** pembersihan, pencocokan sumber, perbandingan kalender, cakupan bersama, laporan, filter, dan navigasi. Modul serta tes SQL dihapus karena perhitungan dashboard menggunakan Pandas dan CSV.
- **Ringkasan:** tiga KPI dipertahankan. Pada Jawa Barat Oktober 2025, daging kerbau segar (lokal) tidak memiliki harga September; perubahan hanya dihitung untuk 24 dari 25 komoditas.
- **Satuan:** tabel dan unduhan perbandingan provinsi tidak memuat satuan asumsi. Laporan Excel dan unduhan data bersih juga tidak menyertakan kolom tersebut.
- **Browser lokal:** ketiga menu diperiksa pada desktop 1440 × 950 dan ponsel lebar 390 px, termasuk perubahan komoditas, bulan, provinsi, kedua ukuran fluktuasi, dan kondisi harga kosong. Tidak ada exception aplikasi, error JavaScript, atau overflow badan halaman dalam rangkaian pemeriksaan.
- **Unduhan browser:** CSV perbandingan provinsi, fluktuasi, cakupan, dataset bersih (32.480 observasi), karantina (942 baris), serta laporan Excel berhasil diperiksa.
- **Akses publik:** browser baru tanpa login/cookie mencoba URL Streamlit, tetapi koneksi gagal pada proxy dengan `ERR_TUNNEL_CONNECTION_FAILED`. Akses tanpa login, seluruh fungsi deployment, dan screenshot deployment belum terverifikasi. Rincian ada pada `public_deployment_check.json`.

Screenshot pada `reports/screenshots/` berasal dari server lokal, bukan deployment publik. Dataset historis berakhir Oktober 2025 dan tidak diperbarui otomatis. Pencocokan file lokal tidak membuktikan unduhan langsung dari server BPN atau satuan yang tidak tercantum pada ekspor.
