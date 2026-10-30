# Validasi rilis ekspor primer pengguna

- **83 tes lulus**: pipeline, analitik, sumber input aktif, normalisasi primer, laporan, state antarmuka, kuantitas/satuan pengguna, dan batas anggaran.
- **Dua berkas asli dipertahankan:** CSV aktif dan XLSX pembanding dari unggahan pengguna. SHA-256 kedua file diperiksa; seluruh 33.422 baris dan enam kolom cocok setelah normalisasi teks.
- **32.480 observasi** lolos aturan pembersihan. Harga bersih sama dengan versi sebelumnya: tidak ada observasi harga berubah. 942 baris dipisahkan; rujukan baris karantina kini mengikuti ekspor header-pertama.
- **Perhitungan independen dari CSV:** Decimal menghasilkan 24 pembanding, dua kenaikan ≥10%, dan cabai merah keriting +11,16% untuk Jawa Barat Oktober 2025.
- **Perlindungan input:** hash CSV dan XLSX serta kesamaan isinya diperiksa sebelum pembangunan ulang. File pembanding yang diubah ditolak sebelum output ditulis. Unduhan mirror ditolak pada mode primer.
- **Halaman depan:** temuan harga tanpa asumsi kuantitas/satuan. Tab terpisah mempertahankan estimasi keranjang latihan, profil, dan sensitivitas.
- **Chromium desktop 1440 × 950 dan ponsel 390 px:** lima menu, kedua tab Ringkasan, perubahan profil, edit tabel mouse/keyboard, sumber harga/satuan, batas anggaran, reset, dan pemulihan bulan diperiksa. Tidak ada error JavaScript atau overflow badan halaman pada rangkaian pemeriksaan.
- **Unduhan browser:** CSV/Excel skenario sesuai input. Excel analisis memuat 32.480 observasi, hash CSV primer aktif, cakupan, dan sensitivitas.
- **Reproduksibilitas:** konfigurasi input, receipt, file asli, pembersihan, arsip mirror, dependency lock, workflow CI, dan screenshot tersedia. `.gitattributes` mempertahankan byte asli ekspor lintas sistem operasi.

Pemeriksaan tidak membuktikan pengambilan langsung dari server BPN: file disediakan pengguna sebagai unduhan dari publikasi tersebut. Satuan dan lisensi tidak tercantum di kedua file; biaya tetap latihan/input pengguna. Uji manusia, manfaat usaha, akses URL hosting publik, dan pemulihan sleep hosting belum dibuktikan. Kelulusan lokal tidak otomatis membuktikan eksekusi CI remote terbaru atau skor rekrutmen tertentu.
