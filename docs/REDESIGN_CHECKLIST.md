# Checklist revisi dashboard untuk reviewer rekrutmen

Dokumen ini memetakan seluruh rekomendasi review ke implementasi dan bukti pemeriksaan. Pemeriksaan lokal dibedakan dari hal yang masih memerlukan URL hosting publik.

| Rekomendasi | Implementasi | Bukti / lokasi |
| --- | --- | --- |
| Identitas dan tujuan dipahami dalam 30–60 detik | Judul sesuai permintaan, satu kalimat kasus warung makan Jawa Barat, wilayah lain sebagai eksplorasi | `app.py`, screenshot `ringkasan-first-screen.png` |
| Ringkasan satu layar desktop | Tiga KPI anggaran, satu temuan, grafik kontribusi, tindakan ke simulator | Browser viewport 1440 × 950 memeriksa posisi CTA |
| KPI menceritakan hal yang sama | Biaya keranjang, perubahan biaya terhadap bulan sebelumnya, harga tersedia dari enam bahan | `historical_budget()`, tes angka snapshot dan kelengkapan |
| Hasil historis terpisah dari skenario | Tidak ada skenario +10% pada Ringkasan; simulator memiliki banner asumsi dan ekspor terpisah | Menu Ringkasan dan Simulator anggaran |
| Grafik dampak rupiah | Batang divergen berpusat nol; merah = tambahan, teal = pengurangan; kuantitas contoh tetap | `historical_impact`, teks dan label rupiah |
| Tabel dan penjelasan tidak mendominasi | Detail tren, tabel, pemantauan dan keranjang di expander; tabel pratinjau ringkas | Menu Ringkasan dan Data & metode |
| Nol dibedakan dari belum diketahui | Total dan perubahan yang tidak lengkap tampil —; nol dipakai untuk hasil atau jumlah aktual | Tes `test_planning.py`, keadaan Januari 2021 dan tanpa harga |
| Pengguna diberi jalan keluar | Subtotal bertanda, harga manual, hapus bahan, tombol bulan lengkap, petunjuk riwayat | Browser reset dan recovery bulan |
| Simulator mudah dicoba | Kuantitas per periode, petunjuk klik sel, +0/+10/+20%, reset | Browser mouse/keyboard, tes skenario dan reset |
| Perubahan massal eksplisit | Mengubah angka bulk tidak menerapkan sampai tombol; shortcut menerapkan langsung; kuantitas/harga tetap | Tes `test_bulk_control_only_applies_after_button_and_preserves_quantity` |
| Input tidak menghilang saat berpindah menu | Model keranjang terpisah dari lifecycle widget; filter relevan disimpan terpisah | Tes lintas halaman dan browser editor |
| Asal harga manual akurat | Sumber per bahan: Snapshot historis / Diubah pengguna / Belum tersedia | CSV/Excel browser dan tes per baris |
| Rumus menyesuaikan harga yang dipakai | Biaya acuan = jumlah × harga acuan yang digunakan; label periode bukan konversi kuantitas | Expander simulasi dan workbook skenario |
| Risiko dijelaskan tanpa klaim prediksi | Menu Fluktuasi historis, minimal tiga observasi, minimum cakupan, tooltip jumlah bulan, status cakupan rendah | Tes risk dan screenshot `risiko.png` |
| Tren/musiman tidak disalahartikan | Penjelasan eksplisit bahwa CV belum memisahkan tren dan musiman | Menu fluktuasi dan metodologi |
| Wilayah ringkas dan bermakna | Harga pilihan, median, deviasi; empat tertinggi/terendah + wilayah pilihan; toggle semua | Tes toggle dan screenshot `wilayah.png` |
| Tidak merekomendasikan pemasok tanpa data | Catatan ongkir, kualitas, dan ketersediaan | Menu Perbandingan wilayah |
| Metode tersedia bertingkat | Sumber/masa data/unduhan terlihat; rumus/kualitas/geografi/hash di expander | Menu Data & metode |
| Tanggal snapshot dibedakan dari bulan harga | Oktober 2025 sebagai harga terakhir; pencatatan snapshot 28 Oktober 2026 dari metadata dengan timezone WIB | Tes tanggal pada menu data |
| Format dan hierarki profesional | Navy–teal, kartu konsisten, tema responsif, kontras caption/sidebar, format ID pada tabel hasil | `assets/dashboard.css`, `analyst/presentation.py` |
| Filter sesuai halaman | Global wilayah/bulan; bahan dan window hanya saat relevan; ambang di detail pemantauan | Tes contextual filters dan state preservation |
| Kode sumber mudah ditemukan | Link GitHub di sidebar/footer; metode, pengujian dan penjelasan proyek | Menu data dan footer |
| Unduhan sesuai isi yang dilihat | CSV pilihan berbeda dari dataset penuh; Excel analisis berbeda dari skenario pengguna | Tes workbook dan unduhan browser |
| Tampilan ponsel | Lima menu, sidebar buka/tutup, kartu responsif, tanpa overflow badan pada lebar 390 px | `scripts/verify_browser.py`, screenshot `*-mobile.png` |
| Akses sesi baru | Konteks browser anonim baru memuat contoh awal tanpa input pengunjung lain | Browser acceptance lokal |
| Tautan publik, performa Internet, sleep hosting | **Belum dapat diverifikasi: URL deployment belum diberikan dan akses akun hosting tidak tersedia** | `docs/DEPLOYMENT.md`; jangan menyebutnya sudah terbit |

## Batas verifikasi

- Browser lokal memakai Chromium dan aplikasi Streamlit yang berjalan di mesin pengembangan, bukan URL deployment publik.
- Waktu siap lokal bukan benchmark Internet atau jaminan kecepatan bagi HRD.
- Screenshot merekam kondisi representatif; tidak membuktikan semua kombinasi wilayah × bahan × bulan.
- Tidak ada file `.pbix` atau klaim penggunaan Power BI. Tampilan bergaya BI dibangun dengan Streamlit dan Plotly agar tidak membutuhkan akun BI eksternal.
- Harga/kuantitas manual disimpan dalam sesi, bukan database transaksi atau penyimpanan permanen. Refresh yang membuat sesi baru dapat mengembalikan contoh awal.

## Menjalankan verifikasi

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Pemeriksaan browser opsional membutuhkan Python dengan `playwright`, `pandas`, `openpyxl`, dan executable Chromium. Dependensi browser tidak diperlukan untuk pengguna dashboard. Jalankan server dari root repository, lalu:

```bash
python scripts/verify_browser.py --url http://127.0.0.1:8502 --chromium /usr/bin/chromium --output-dir /tmp/analyst-browser
```

Runner berhenti dengan exit code nonnol bila asersi gagal. Pada keberhasilan, `browser-validation.json` memuat daftar pemeriksaan, status, dan nama screenshot dari eksekusi tersebut.

## Perbaikan audit lanjutan

- Lookup harga dua bulan dilakukan independen; regresi harga bulan lalu tetap tersedia ketika bulan kini kosong diuji.
- Cakupan keranjang dan perubahan total ditampilkan, dengan dua profil latihan serta tabel sensitivitas.
- Label biaya menyatakan estimasi latihan. Harga dan satuan input pengguna dicatat per baris; tanpa pernyataan bahwa sumber telah terverifikasi.
- Batas anggaran dibandingkan hanya dengan total skenario lengkap, tidak dengan subtotal.
- Peringkat fluktuasi memakai bulan bersama dan pasangan perubahan bulanan bersama. Saringan awal tetap dapat diperiksa.
- Pencocokan mirror dilakukan dan direkam. Primer/satuan/lisensi tetap belum terverifikasi.
- CI ditambahkan untuk push dan pull request. Status eksekusi remote tidak diasumsikan dari keberadaan workflow.
- Studi kasus satu halaman dan rencana uji pengguna tersedia. Hasil peserta manusia belum tersedia dan tidak diganti dengan hasil browser otomatis.
