# Menjelaskan Analisis Harga Pangan dalam CV

## Judul proyek

**Analisis Harga Pangan dan Simulasi Anggaran Bahan Baku UMKM Kuliner**

Python · Pandas · SQL/SQLite · Streamlit · Excel

## Temuan historis dan skenario yang harus dibedakan

Pada Jawa Barat Oktober 2025, keranjang enam bahan contoh berbiaya **Rp1.118.460**, bertambah **Rp10.687** dibanding September pada kuantitas tetap. Itu perbandingan harga historis yang diterapkan pada keranjang contoh, bukan catatan pengeluaran usaha. Skenario harga naik seragam 10% menghasilkan tambahan **Rp111.846**; ini hasil hipotetis terpisah.

Demo singkat: tunjukkan KPI biaya keranjang, baca grafik kontributor biaya, lalu buka simulator. Jelaskan asal harga per bahan dan ubah satu jumlah. Tunjukkan bahwa perhitungan tidak lengkap tidak dianggap nol.

## Contoh butir CV

Gunakan setelah menjalankan proyek, memeriksa hasil, dan memahami perhitungannya.

- Pengolahan **33.422 baris harga pangan** menjadi **32.480 observasi valid** menggunakan Python dan SQL, dengan normalisasi wilayah serta pemisahan **942 baris tanpa harga valid**.
- Dashboard Streamlit untuk perubahan harga, perbandingan wilayah, dan simulasi anggaran; menyoroti **dua dari 24 komoditas pembanding** yang naik ≥10% di Jawa Barat pada Oktober 2025.

Dua komoditas tersebut adalah cabai merah keriting (**11,16%**) dan cabai merah besar (**10,52%**), dengan pembanding September 2025. Ambang 10% adalah parameter pemantauan. Perbarui temuan dan cakupan ketika datanya berubah.

## Cara menjelaskan proyek

Mulai dari kebutuhan sederhana: saat harga bahan berubah, berapa tambahan anggaran untuk jumlah belanja yang sama? Tunjukkan pilihan wilayah dan bulan, jelaskan satu perubahan harga, kemudian coba satu bahan dalam simulator.

Contoh warung makan adalah kasus latihan. Dataset tidak memuat stok, penjualan, laba, atau transaksi pembelian usaha. Satuan kg/liter juga masih berupa asumsi. Hasil simulator adalah perkiraan anggaran, bukan klaim penghematan yang sudah terjadi.

Jika perlu contoh angka saat demo, gunakan keranjang awal pada Jawa Barat, Oktober 2025. Kenaikan harga 10% menghasilkan anggaran Rp1.230.306 dari acuan Rp1.118.460. Jelaskan asal enam jumlah kebutuhan yang dipakai: semuanya parameter contoh yang bisa diubah, bukan hasil observasi suatu warung.

## Persiapan wawancara

- Cocokkan satu MoM dengan hitungan manual dari dua bulan kalender berturut-turut.
- Jelaskan mengapa harga kosong tidak diubah menjadi nol dan mengapa Maret tidak dibandingkan dengan Januari sebagai MoM jika Februari kosong.
- Tunjukkan bagaimana total simulator berubah saat jumlah dan skenario harga diubah.
- Jelaskan CV sebagai ukuran variasi historis dan median wilayah sebagai nilai tengah tanpa bobot.
- Tunjukkan sumber, batas verifikasi salinan, dan perubahan seri Papua.
- Jika memakai bantuan alat dalam pengembangan, jelaskan penggunaannya dan pastikan bisa menerangkan serta mengubah kode yang ditampilkan.
