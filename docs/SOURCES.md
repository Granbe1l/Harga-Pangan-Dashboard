# Sumber data

## Publikasi

**Badan Pangan Nasional — Rata-rata Harga Pangan Bulanan Tingkat Konsumen Provinsi**

https://data.badanpangan.go.id/datasetpublications/178/rata-rata-harga-pangan-bulanan-konsumen-provinsi

CSV dan XLSX diterima sebagai ekspor dari publikasi ini. CSV menjadi input aktif dan XLSX digunakan sebagai pembanding. Asal unduhan mengikuti keterangan pemberi berkas; pengambilan langsung dari server BPN tidak diverifikasi secara independen.

## Berkas asli yang dipertahankan

| Peran | Path | SHA-256 |
| --- | --- | --- |
| Input aktif | `data/raw/primary/harga_pangan.csv` | `561054df5d8b36e7d75d92715fe037031a7e9c7c9f513fd178322cce491845d1` |
| Pembanding | `data/raw/primary/harga_pangan.xlsx` | `d3e3575de33c01474ee7ae71faf10d4ee00bd51005aa72746841f67ef4e958c6` |

Nama asli, ukuran, waktu impor, jalur akuisisi, dan hasil pencocokan dicatat di `data/raw/primary/receipt.json`. Konfigurasi input aktif: `data/source_input.json`. Metadata hasil pemrosesan: `data/source.json`. Ringkasan pemeriksaan: `data/verification.json`.

## Pemeriksaan berkas

- Kedua berkas memiliki 33.422 baris data dan enam kolom yang sama.
- Seluruh baris cocok pada urutan yang sama setelah penyeragaman spasi dan nilai kosong.
- 32.480 observasi hasil pembersihan memiliki harga yang sama dengan versi mirror sebelumnya; tidak ada harga berubah.
- Sebanyak 938 harga kosong dan empat harga nol dipisahkan. Nomor baris karantina mengikuti file CSV primer: baris header 1, observasi pertama baris 2.
- Harga tetap kosong bila tidak tersedia, konflik tidak dirata-ratakan, dan tidak ada pemakaian harga lama secara diam-diam.

## Satuan dan penggunaan

CSV dan XLSX **tidak mencantumkan kolom satuan**, definisi rinci satuan harga, atau ketentuan lisensi. Kecocokan dua format bukan tanda tangan digital sumber dan tidak membuktikan pengambilan langsung dari server. Metadata karena itu membedakan penerimaan ekspor pengguna, konsistensi isi, dan verifikasi independen.

Persentase perubahan harga pada halaman depan tidak membutuhkan asumsi jumlah belanja atau satuan kg/liter. Perhitungan rupiah pada keranjang diberi label latihan karena membutuhkan asumsi satuan dan kuantitas. Satuan/harga yang dimasukkan pengguna dicatat sebagai pernyataan pengguna, bukan verifikasi eksternal.

Ketentuan lisensi tidak tercantum pada ekspor yang diterima. Penggunaan ulang mengikuti ketentuan penerbit. Dashboard merupakan proyek analisis independen.

## Arsip versi sebelumnya

Mirror lama dan metadata pemeriksaannya disimpan di `data/archive/mirror-20261028/` untuk jejak perubahan; tidak dibaca sebagai input aktif. `--download` mirror ditolak ketika mode primer aktif. Perubahan berkas sumber memerlukan catatan penerimaan dan pengujian ulang.
