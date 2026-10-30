# Studi kasus: perubahan harga dan anggaran bahan baku

Analisis ini menelusuri bahan dengan kenaikan harga terbesar dan membandingkan dampak biayanya pada beberapa contoh kebutuhan belanja.

**Ruang lingkup:** snapshot harga konsumen provinsi Januari 2021–Oktober 2025. Fokus awal Jawa Barat, dengan tiga komposisi keranjang contoh.

**Sumber:** berkas CSV/XLSX yang diterima sebagai ekspor publikasi BPN. Seluruh 33.422 baris cocok antardua format. Rincian penerimaan dan batas pemeriksaan tersedia di [Sumber data](SOURCES.md).

## Hasil

| Analisis | Hasil pada Jawa Barat |
| --- | --- |
| Temuan harga Oktober 2025 | Dua dari 24 pembanding naik ≥10%; cabai merah keriting tertinggi +11,16% |
| Konteks kenaikan cabai merah keriting | Naik ≥10% pada 4 dari 12 pasangan bulan, November 2024–Oktober 2025; frekuensi historis, bukan peluang masa depan |
| Data mentah → valid | 33.422 → 32.480 observasi |
| Keranjang enam bahan lengkap | 22 dari 58 bulan; pertama Januari 2024 |
| Perubahan total bulanan lengkap, profil A/B | 21 dari 58 bulan |
| Alternatif profil C (tanpa minyak) | Harga lengkap 58/58 bulan; komposisi berbeda, dipilih eksplisit |
| Profil latihan A, Oktober 2025 | Estimasi Rp1.118.460, bertambah Rp10.687 terhadap September |
| Kontributor profil A | Telur ayam ras, tambahan Rp8.455 pada asumsi kebutuhan 5 kg |
| Sensitivitas profil B | Telur diubah menjadi 1 kg, bahan lain tetap; kontributor terbesar bergeser ke ayam ras Rp3.890, perubahan total Rp3.923 |

Nilai rupiah tersebut bersifat **latihan**, karena satuan sumber belum terverifikasi dan kebutuhan bukan hasil survei usaha. Pada contoh ini, perubahan jumlah telur menggeser bahan penyumbang biaya terbesar. Hasilnya bergantung pada komposisi belanja.

## Pengolahan dan analisis

1. Memisahkan harga kosong/nonpositif dan mempertahankan jejak sumber.
2. Membandingkan dua bulan kalender secara tepat, termasuk ketika salah satu bulan tidak memiliki harga.
3. Memisahkan total lengkap dan subtotal; menunjukkan periode yang benar-benar mendukung analisis.
4. Menguji sensitivitas komposisi, mengedit harga/satuan dengan asal per baris, serta membandingkan skenario dengan batas anggaran.
5. Membandingkan fluktuasi pada bulan harga dan pasangan bulanan yang sama, bukan hanya mencampurkan seri dengan cakupan berbeda.
6. Menyediakan pengujian otomatis lokal, workflow CI, laporan CSV/Excel, dan pemeriksaan browser desktop/mobile.

## Keterbatasan

- CSV/XLSX unggahan cocok isinya. Pengambilan langsung dari server, satuan sumber, dan izin redistribusi belum terkonfirmasi.
- Belum ada catatan kebutuhan satu usaha atau hasil uji pengguna manusia yang dikumpulkan.
- Belum ada bukti peningkatan laba, penghematan, atau kinerja prediksi.
- Hosting publik dan sleep hosting membutuhkan URL deployment untuk diverifikasi.

## Membaca dashboard

Tab **Temuan harga** menampilkan perubahan tanpa asumsi jumlah belanja. Tab **Dampak keranjang latihan** membandingkan biaya dan komposisi contoh. Jumlah, harga, dan skenario dapat diubah pada **Simulator anggaran**.

**Sumber & cara menghitung** tersedia sebagai bagian yang bisa dibuka di bawah setiap halaman, termasuk unduhan laporan. **Tren & fluktuasi** memuat riwayat bahan pilihan dengan bulan kosong tetap kosong.
