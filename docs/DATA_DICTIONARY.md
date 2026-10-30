# Kamus data

## Data mentah

File sumber: `data/raw/primary/harga_pangan.csv`.

Header berada pada baris pertama CSV. Nama kolom sumber:

| Kolom sumber | Makna | Perlakuan |
|---|---|---|
| `Kode Provinsi` | Kode wilayah yang tercatat pada sumber | Diproses sebagai identitas teks; tidak dianggap angka pengukuran. |
| `Nama Provinsi` | Label provinsi | Normalisasi penulisan dengan memperhatikan kode dan perubahan administrasi. |
| `Komoditas` | Jenis komoditas beserta tingkat/spesifikasi yang disebutkan | Pertahankan perbedaan seperti beras premium dan medium. |
| `Tahun` | Tahun observasi | Validasi sebagai tahun kalender. |
| `Bulan` | Nama bulan Indonesia | Dikonversi menjadi bulan kalender. |
| `Harga` | Harga tercatat dengan format rupiah | Ubah menjadi angka positif; pemisah ribuan harus dibaca dengan benar. |

Contoh `Rp12,072` pada file ini dibaca sebagai **12.072 rupiah**, bukan 12,072 rupiah dalam arti desimal. Format tersebut tidak boleh digeneralisasi untuk semua sumber data Indonesia tanpa pemeriksaan terpisah.

## Tabel harga bersih

Satu baris mewakili satu observasi provinsi–komoditas–bulan.

| Kolom | Tipe analitis | Makna |
|---|---|---|
| `province_code` | Teks | Kode provinsi sumber yang dinormalisasi. |
| `province` | Teks | Nama provinsi yang konsisten untuk penayangan. |
| `commodity` | Teks | Nama komoditas sumber. |
| `date` | Tanggal | Hari pertama bulan observasi, format `YYYY-MM-01`. Ini penanda bulan, bukan tanggal survei harian. |
| `price` | Numerik | Harga konsumen tercatat dalam rupiah, harus lebih dari nol. |
| `unit` | Teks | Metadata asumsi dari pemrosesan versi sebelumnya; tidak digunakan dalam analisis dan tidak disertakan pada laporan. |
| `source_province_code` | Teks | Kode wilayah sebelum pemisahan seri historis. Berguna untuk melacak observasi ke file mentah. |
| `geography_note` | Teks | Catatan perubahan seri wilayah, terutama Papua sebelum perubahan skema pada snapshot. |
| `unit_assumed` | Boolean | Penanda bahwa satuan berasal dari asumsi kerja aplikasi, bukan kolom satuan dalam CSV mentah. |

Kunci analitis: `province_code + commodity + date`. Kolom `price` merupakan harga per observasi, bukan nilai penjualan.

`PAPUA_HIST` dan `PAPUA_BARAT_HIST` adalah identitas analitis untuk seri historis sebelum 2024 pada snapshot ini. Keduanya bukan kode provinsi resmi baru. Pemisahan menjaga agar perubahan skema kode pada file tidak menciptakan sambungan seri yang menyesatkan.

## Kolom analisis

| Konsep | Definisi |
|---|---|
| Harga sebelumnya | Harga dari pasangan yang sama pada bulan kalender tepat sebelumnya. |
| MoM | Persentase perubahan terhadap harga sebelumnya; kosong bila pembanding tidak ada. |
| Harga tahun lalu | Harga pasangan yang sama pada bulan yang sama setahun sebelumnya. |
| YoY | Persentase perubahan terhadap harga tahun lalu; kosong bila pembanding tidak ada. |
| CV | Simpangan baku relatif terhadap rata-rata harga pada periode, dihitung per pasangan provinsi–komoditas. |
| Cakupan | Proporsi bulan dengan harga valid terhadap bulan kalender yang diharapkan. |
| Median provinsi | Median harga provinsi yang tersedia untuk satu komoditas dan satu bulan; tidak berbobot dan bukan angka nasional resmi. |

Nama kolom turunan pada hasil ekspor dapat dilihat pada header hasil. Definisi bisnisnya mengikuti [metodologi](METHODOLOGY.md).

## Provenansi input aktif

`data/source_input.json` memilih CSV ekspor primer yang diberikan pengguna. `data/raw/primary/receipt.json` memuat hash kedua file, nama asli, dan kecocokan 33.422 baris. Kolom `source_row` karantina mengikuti CSV header-pertama, sehingga observasi pertama berada di baris 2. Tidak ada kolom satuan pada CSV/XLSX; `unit` pada data olahan tetap asumsi bertanda `unit_assumed=True`; tidak digunakan pada analisis harga.
