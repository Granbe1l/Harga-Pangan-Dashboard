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

Ambang 10% merupakan parameter analisis. Frekuensi kenaikan menggambarkan riwayat pengamatan, bukan peluang kenaikan berikutnya. Satu komoditas tanpa pembanding tidak dimasukkan dalam jumlah kenaikan.

## Proses analisis

1. Memeriksa kecocokan CSV dan XLSX serta menyimpan hash berkas.
2. Memisahkan harga kosong/nol dan mempertahankan nomor baris sumber.
3. Membandingkan bulan kalender yang tepat, tanpa mengisi harga hilang.
4. Membandingkan fluktuasi pada bulan dan pasangan bulanan yang sama.
5. Membandingkan harga antarwilayah dengan median tanpa bobot.
6. Menyediakan dashboard, laporan Excel, query SQL, dan pengujian otomatis.

## Interpretasi

Kenaikan satu bulan perlu dibaca bersama riwayat dan cakupan pengamatan. Harga yang lebih rendah dari median wilayah tidak otomatis menunjukkan lokasi pembelian yang lebih baik, karena ongkir, kualitas, dan pemasok tidak tersedia dalam data.

Harga konsumen provinsi dapat berbeda dari harga toko. File sumber tidak mencantumkan satuan; angka harga ditampilkan mengikuti sumber. Analisis ini tidak menguji penyebab perubahan atau membuat prediksi.

[Sumber](SOURCES.md) · [Metode](METHODOLOGY.md) · [Pengujian](TESTING.md)
