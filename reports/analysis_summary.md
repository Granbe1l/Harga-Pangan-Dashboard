# Analisis Harga Pangan dan Simulasi Anggaran Bahan Baku UMKM Kuliner

Provinsi: **Jawa Barat**. Bulan laporan: **2025-10**.
Jendela volatilitas: 2024-11–2025-10 (12 bulan).

Data masukan: **32,480 observasi**, **25 komoditas**, **40 seri geografis** termasuk seri historis; periode 2021-01–2025-10.
Pada bulan/provinsi terpilih tersedia **25 komoditas**; **24** memiliki pembanding bulan kalender sebelumnya.
Ada **2 komoditas** dengan kenaikan MoM ≥ 10%. Ambang ini adalah parameter analisis, bukan batas resmi.

## Kenaikan harga bulanan yang teramati

- **Cabai Merah Keriting**: naik **11.16%**, dari Rp50,999 menjadi Rp56,690 per kg (satuan asumsi; tidak tercantum pada ekspor).
- **Cabai Merah Besar**: naik **10.52%**, dari Rp51,727 menjadi Rp57,169 per kg (satuan asumsi; tidak tercantum pada ekspor).
- **Telur Ayam Ras**: naik **5.95%**, dari Rp28,418 menjadi Rp30,109 per kg (satuan asumsi; tidak tercantum pada ekspor).
- **Bawang Merah**: naik **2.60%**, dari Rp37,552 menjadi Rp38,527 per kg (satuan asumsi; tidak tercantum pada ekspor).
- **Jagung Tingkat Peternak**: naik **2.13%**, dari Rp5,971 menjadi Rp6,098 per kg (satuan asumsi; tidak tercantum pada ekspor).

## Variasi harga dalam jendela analisis

- **Cabai Rawit Merah**: CV **36.85%**, 12/12 bulan teramati (cakupan 100.0%).
- **Cabai Merah Keriting**: CV **22.14%**, 12/12 bulan teramati (cakupan 100.0%).
- **Bawang Merah**: CV **12.88%**, 12/12 bulan teramati (cakupan 100.0%).
- **Bawang Putih (Bonggol)**: CV **7.88%**, 12/12 bulan teramati (cakupan 100.0%).
- **Jagung Tingkat Peternak**: CV **5.20%**, 12/12 bulan teramati (cakupan 100.0%).

## Cakupan dan estimasi latihan

Keranjang contoh lengkap pada 22 dari 58 bulan; perubahan bulanan lengkap pada 21 bulan. Kuantitas dan satuan masih asumsi; nilai rupiah bukan hasil usaha nyata.

## Implikasi dan batas penggunaan

Komoditas dengan kenaikan atau variasi tinggi dapat diprioritaskan untuk evaluasi anggaran. Uji skenario kuantitas dan harga di simulator sebelum menyusun rekomendasi pembelian. Data ini belum cukup untuk membuktikan penghematan, menentukan pemasok termurah, atau memprediksi kenaikan berikutnya.

- Snapshot historis harga konsumen bulanan; bukan harga real-time, transaksi, atau penawaran pemasok.
- Dataset aktif berasal dari ekspor CSV/XLSX BPN yang diberikan pengguna. Kecocokan kedua format diperiksa; pengambilan langsung dari server dan keaslian independen belum diverifikasi.
- Satuan kg/liter merupakan asumsi kerja per komoditas; CSV asli tidak menyediakan kolom satuan. Verifikasi sebelum penggunaan operasional.
- MoM membandingkan bulan kalender sebelumnya; YoY membandingkan bulan yang sama tahun sebelumnya. Bulan kosong tidak dilewati dan tidak diimputasi.
- Peringkat variasi tingkat harga memakai bulan pengamatan bersama untuk seri yang lolos cakupan; perubahan bulanan memakai pasangan bulan kalender yang sama. Tabel penyaringan bukan peringkat akhir.
- Volatilitas adalah koefisien variasi harga (simpangan baku sampel/mean × 100), minimal tiga observasi; bukan probabilitas kenaikan atau prediksi.
- Median antarwilayah tidak berbobot dan hanya mencakup wilayah dengan data pada bulan/komoditas terpilih; bukan harga nasional resmi atau inflasi IHK.
- Seri Papua dan Papua Barat sebelum perubahan skema 2024 dipisahkan dari seri sesudahnya. Jumlah seri geografis tidak sama dengan jumlah provinsi Indonesia pada satu waktu.
- Simulasi menggunakan harga tepat pada bulan yang dipilih. Harga tidak tersedia tidak diganti harga bulan lain. Total lengkap tidak diterbitkan bila harga komoditas aktif belum lengkap.
- Skenario anggaran berasal dari kuantitas dan perubahan harga yang dimasukkan pengguna; bukan penghematan atau dampak bisnis yang sudah terealisasi.
- Lisensi redistribusi snapshot belum terkonfirmasi; periksa ketentuan sumber asal dan penyedia salinan sebelum redistribusi atau penggunaan komersial.
