# Studi kasus: tren dan perbandingan harga pangan antarprovinsi

Analisis ini menjawab tiga pertanyaan: komoditas apa yang mengalami kenaikan terbesar, bagaimana pergerakannya sepanjang waktu, dan bagaimana harga suatu wilayah dibandingkan wilayah lain?

Data berasal dari ekspor publikasi BPN untuk Januari 2021–Oktober 2025. Fokus awal dashboard adalah Jawa Barat; wilayah, bulan, dan komoditas dapat diubah. Satu observasi mewakili satu provinsi, komoditas, dan bulan.

## Temuan — Jawa Barat, Oktober 2025

| Analisis | Hasil |
| --- | --- |
| Harga tersedia | 25 komoditas; 24 memiliki pembanding September |
| Kenaikan ≥10% | Dua komoditas: cabai merah keriting dan cabai merah besar |
| Kenaikan tertinggi | Cabai merah keriting, 11,16% |
| Konteks historis cabai merah keriting | Naik ≥10% pada 4 dari 12 pasangan bulan November 2024–Oktober 2025 |
| Data mentah → valid | 33.422 → 32.480 observasi; 942 baris dipisahkan |

Batas kenaikan 10% dipilih sebagai penyaring deskriptif untuk menyoroti kenaikan dua digit. Batas ini tetap, bukan hasil optimasi atau standar resmi pemerintah. Dua dari 24 komoditas dengan pembanding (8,3%) mencapai ambang tersebut; penyebutnya bukan seluruh 25 komoditas.

Daging kerbau segar (lokal) memiliki harga Oktober 2025, tetapi tidak memiliki harga September 2025. Karena perubahan bulanan memerlukan kedua bulan kalender tersebut, komoditas ini tidak masuk hitungan kenaikan. Harga Oktober dan riwayatnya tetap ditampilkan; harga kosong tidak diisi atau diganti dengan bulan lain.

Frekuensi kenaikan menggambarkan riwayat pengamatan, bukan peluang kenaikan berikutnya.

## Proses analisis

1. Memeriksa kecocokan CSV dan XLSX serta menyimpan hash berkas.
2. Memisahkan harga kosong/nol dan mempertahankan nomor baris sumber.
3. Membandingkan bulan kalender yang tepat, tanpa mengisi harga hilang.
4. Membandingkan fluktuasi pada bulan dan pasangan bulanan yang sama.
5. Membandingkan harga antarwilayah dengan median tanpa bobot.
6. Menyediakan dashboard, laporan Excel, dan pengujian otomatis.

## Interpretasi

Kenaikan satu bulan perlu dibaca bersama riwayat dan cakupan pengamatan. Harga yang lebih rendah dari median wilayah tidak otomatis menunjukkan lokasi pembelian yang lebih baik, karena ongkir, kualitas, dan pemasok tidak tersedia dalam data.

Harga konsumen provinsi dapat berbeda dari harga toko. File sumber tidak mencantumkan satuan; angka harga ditampilkan mengikuti sumber. Analisis ini tidak menguji penyebab perubahan atau membuat prediksi.

[Sumber](SOURCES.md) · [Metode](METHODOLOGY.md) · [Pengujian](TESTING.md)
