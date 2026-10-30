# Migrasi ekspor primer — selesai melalui unggahan pengguna

Dataset aktif kini memakai CSV yang diberikan pengguna sebagai unduhan dari publikasi BPN:
https://data.badanpangan.go.id/datasetpublications/178/rata-rata-harga-pangan-bulanan-konsumen-provinsi

XLSX unggahan disimpan sebagai pembanding. Seluruh 33.422 baris dan enam kolom cocok setelah normalisasi teks. Kedua berkas dipertahankan tanpa mengubah byte aslinya. Ini bukti konsistensi file yang diterima; bukan klaim pengambilan langsung dari server atau verifikasi satuan/lisensi.

## Input dan pembangunan ulang

- `data/source_input.json` memilih CSV primer dan receipt-nya.
- `data/raw/primary/receipt.json` mencatat kedua nama asli dan hash.
- `analyst.pipeline.read_raw()` mengenali header di baris pertama; tanggal dirangkai dari Tahun dan Bulan Indonesia, harga rupiah diparsing tanpa menebak satuan.
- `python scripts/prepare_data.py` membangun ulang data aktif, memeriksa hash input, dan tidak mengunduh mirror.
- `python scripts/prepare_data.py --download` ditolak dalam mode primer agar sumber tidak berganti secara diam-diam.
- File mirror dan metadata sebelumnya tersedia di arsip untuk audit.

Adapter generik di `scripts/import_primary.py` tetap tersedia untuk inspeksi/unduhan dan staging skema lain. Perintah `normalize` generik mengharuskan satu kolom tanggal; ekspor BPN aktif yang memakai Tahun dan Bulan terpisah diproses oleh `scripts/prepare_data.py`. Jangan memakai contoh mapping sebagai bukti header resmi.

## Hasil pemrosesan

33.422 baris → 32.480 observasi yang lolos aturan pembersihan; 942 dipisahkan. Harga Januari 2021–Oktober 2025, 25 komoditas, 40 seri geografis termasuk dua seri historis. Seluruh harga bersih cocok dengan versi sebelumnya sehingga angka temuan lama yang dihitung benar tetap berlaku.

## Batas yang tetap berlaku

Satuan dan lisensi tidak tercantum di kedua ekspor. Tanggal impor tidak berarti harga diperbarui sampai tanggal tersebut. Analisis harga utama membandingkan persentase pada seri yang sama; keranjang rupiah tetap latihan atau input pengguna. Uji manusia dan dampak finansial belum dilakukan. Tidak ada klaim skor rekrutmen yang dijamin oleh perubahan sumber ini.
