# Asal data dan penggunaan ulang

## Sumber yang dibaca proyek

- Penyedia salinan: repositori publik [Prediksi_Harga_Pangan_Nasional — Achmad Ichzan](https://github.com/achmadichzan/Prediksi_Harga_Pangan_Nasional).
- Halaman file: [harga_pangan.csv](https://github.com/achmadichzan/Prediksi_Harga_Pangan_Nasional/blob/main/harga_pangan.csv).
- URL file mentah: <https://raw.githubusercontent.com/achmadichzan/Prediksi_Harga_Pangan_Nasional/main/harga_pangan.csv>.
- Sumber primer yang dicantumkan dokumentasi penyedia salinan: [Rata-rata Harga Pangan Bulanan Tingkat Konsumen Provinsi — Badan Pangan Nasional](https://data.badanpangan.go.id/datasetpublications/178/rata-rata-harga-pangan-bulanan-konsumen-provinsi).

Hanya file data dan dokumentasi sumbernya yang dipakai sebagai rujukan. Keberadaan proyek asal tidak menjadi bukti bahwa algoritma, klaim performa, atau temuan di proyek asal juga berlaku pada Analisis Harga Pangan.

## Status verifikasi

Isi salinan CSV diperiksa dalam pembuatan proyek. Halaman sumber primer tidak dapat diperiksa secara independen dalam sesi ini. Karena itu:

1. Atribusi kepada Badan Pangan Nasional didasarkan pada dokumentasi penyedia salinan.
2. Salinan tidak dinyatakan identik dengan versi terbaru sumber primer.
3. Cakupan yang dicantumkan dalam aplikasi mengikuti file yang benar-benar diproses, bukan janji pembaruan pada situs lain.
4. Harga tidak dianggap tersedia langsung atau diperbarui otomatis dari pasar.

Metadata provenance dan checksum file yang disertakan perlu dipertahankan bersama dataset. Ketika memperbarui data, catat URL, waktu pengambilan, checksum, cakupan periode, dan perubahan skema. Baca ulang laporan kualitas sebelum membandingkan hasil lama dengan hasil baru.

## Lisensi dan atribusi

Hak penggunaan ulang dataset belum dikonfirmasi dari sumber primer. Repo publik dan tombol unduh bukan pengganti lisensi. Sebelum menerbitkan ulang dataset, menggunakannya secara komersial, atau memasukkan data ke deployment publik, periksa ketentuan sumber asal dan salinannya. Jangan menyatakan proyek atau salinan data ini sebagai produk resmi pemerintah.

Contoh atribusi pada laporan:

> Data harga konsumen bulanan: salinan publik `harga_pangan.csv` dari repositori Achmad Ichzan, yang mendokumentasikan sumber asal Badan Pangan Nasional. Pengolahan dan analisis dilakukan dalam proyek Analisis Harga Pangan. Versi data mengikuti metadata yang disertakan; kesesuaian dengan versi terbaru sumber primer belum dikonfirmasi.

## Memperbarui data dengan aman

Simpan data pengganti sebagai versi baru dan pertahankan file yang digunakan untuk laporan sebelumnya. Jangan menimpa hasil lama tanpa mencatat perubahan input. Pastikan granularitas, satuan, dan kode wilayah kompatibel; file harian, harga produsen, atau harga grosir tidak boleh dimasukkan sebagai pengganti harga konsumen bulanan tanpa perubahan metodologi yang jelas.

## Pemeriksaan ulang 30 Oktober 2026

- CSV pada mirror publik diunduh ulang melalui HTTPS dengan verifikasi TLS aktif. SHA-256-nya identik dengan snapshot lokal: `c4b206afd027949f1165d4ecc2dd0799108bb0449b6aa16b29fee9d58c165d9d`.
- README mirror berhasil dibaca dan memang merujuk halaman Badan Pangan Nasional yang dicantumkan proyek. Klaim model/prediksi dari README mirror tidak dipakai sebagai hasil proyek ini.
- CSV tidak memiliki kolom satuan. Pencocokan file tidak memverifikasi asumsi kg/liter, akurasi terhadap sumber primer, atau lisensi redistribusi.
- Permintaan ke sumber primer gagal dengan `ProxyError` pada lingkungan pengembangan. Verifikasi primer dan izin penggunaan tetap berstatus belum selesai; kegagalan akses ini tidak membuktikan sumbernya salah atau situsnya tidak tersedia bagi semua orang.
- Bukti terstruktur, waktu pemeriksaan, URL, status permintaan, serta hash tersedia pada `data/verification.json`.

Sebelum mengubah status satuan menjadi terverifikasi, catat bukti per komoditas (URL dokumen primer, satuan, definisi harga, periode, dan tanggal pemeriksaan). Sampai itu tersedia, nilai rupiah dari snapshot dan kuantitas contoh dipresentasikan sebagai **estimasi latihan**. Harga dan satuan yang diisi pengguna dicatat terpisah sebagai pernyataan pengguna, bukan hasil verifikasi sumber.
