# Pemrosesan data

## Input

`data/source_input.json` memilih CSV pada `data/raw/primary/`. XLSX digunakan sebagai pembanding. Nama asli, hash SHA-256, dan hasil pencocokan tercatat pada `data/raw/primary/receipt.json`.

Pipeline memeriksa hash kedua berkas dan kesamaan isinya sebelum menulis hasil. Header berada pada baris pertama; data dimulai pada baris kedua. Kolom `Tahun` dan `Bulan` digabung menjadi tanggal bulanan.

## Membangun ulang

```bash
python scripts/prepare_data.py
```

Perintah ini menulis ulang data olahan dan metadata. Untuk pemeriksaan terisolasi, panggil `analyst.pipeline.prepare_data()` dengan direktori sementara yang memuat konfigurasi, receipt, dan berkas sumber.

Mode `--download` mirror ditolak selama konfigurasi sumber primer aktif. Berkas mirror sebelumnya beserta metadatanya disimpan pada `data/archive/mirror-20261028/` dan tidak dibaca sebagai input aplikasi.

`scripts/import_primary.py` menyediakan adapter untuk inspeksi dan staging skema lain. Normalisasi generiknya memerlukan satu kolom tanggal; skema BPN dengan tahun/bulan terpisah menggunakan `scripts/prepare_data.py`.

## Hasil

Dari 33.422 baris, 32.480 observasi lolos pembersihan dan 942 dipisahkan. Harga bersih identik dengan snapshot sebelumnya. Nomor `source_row` pada karantina mengacu pada baris CSV asli.

Pencocokan CSV–XLSX membuktikan konsistensi berkas yang diterima. Pemeriksaan tersebut tidak memverifikasi unduhan langsung dari server, satuan harga, atau lisensi publikasi. Rincian tersedia di [Sumber data](SOURCES.md).
