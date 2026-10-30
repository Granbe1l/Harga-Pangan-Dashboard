# Validasi revisi audit

- **68 tes lulus**, meliputi pipeline, perbandingan harga kalender, anggaran, sumber harga/satuan pengguna, batas anggaran, format, laporan, dan navigasi.
- Bug harga bulan sebelumnya diuji: total bulan lalu tetap tersedia ketika harga bulan berjalan kosong; perubahan total tetap belum diketahui.
- Keranjang A/B Jawa Barat lengkap 22/58 bulan; perubahan total lengkap 21/58 bulan. Profil C lima bahan dipilih eksplisit dan mendukung 58/58 bulan tanpa mengisi harga yang hilang.
- Profil B mengubah kebutuhan telur menjadi 1 kg: perubahan estimasi Rp3.923 dan kontributor terbesar bergeser ke ayam pada Oktober 2025.
- Grafik fluktuasi memakai irisan bulan harga dan pasangan bulanan yang sama. Ekspor analisis mencatat saringan dan bulan pembanding.
- Chromium desktop 1440 × 950: KPI, temuan, grafik, dan tombol simulator terlihat pada layar pembuka.
- Chromium ponsel 390 px: lima menu dan sidebar dapat digunakan tanpa overflow horizontal badan halaman.
- Edit jumlah pecahan/harga manual dengan mouse dan keyboard, penyimpanan input lintas menu, batas anggaran, reset, dan pemulihan bulan lengkap diperiksa melalui browser.
- CSV/Excel skenario memuat sumber harga dan status satuan per baris. Ekspor analisis memuat 32.480 observasi, cakupan, dan sensitivitas profil.
- Tidak ada error JavaScript pada pemeriksaan browser yang tercatat di `browser_validation.json`.
- CI untuk push dan pull request tersedia. Keberadaan workflow bukan bukti bahwa eksekusi GitHub Actions remote sudah lulus.
- Mirror publik diunduh ulang dan hash cocok. Sumber primer gagal diakses melalui proxy; satuan dan hak penggunaan ulang belum terverifikasi.

Verifikasi bersifat lokal. Uji peserta manusia, manfaat finansial, URL hosting publik, dan pemulihan setelah sleep hosting belum dibuktikan. Angka rupiah dari harga/satuan asumsi tetap berlabel estimasi latihan. Data mentah dan hasil pembersihan tidak diubah.
