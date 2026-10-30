# Metode perhitungan Analisis Harga Pangan

## Tujuan dan data

Dashboard menelusuri perubahan harga pangan, fluktuasi historis, dan perbedaan harga antarprovinsi.

Satu observasi mewakili **satu wilayah × satu komoditas × satu bulan**. Nilainya adalah rata-rata harga konsumen pada sumber. Harga toko, penawaran pemasok, dan pembelian usaha dapat berbeda.

## Pembersihan

File mentah tetap disimpan. Pipeline membuang baris judul sebelum header, mengubah harga menjadi angka, menyeragamkan label wilayah, dan memeriksa kunci wilayah–komoditas–bulan.

Harga kosong, tanda `-`, serta harga nol atau tidak valid dipisahkan ke file karantina. Tidak ada pengisian harga hilang. Duplikat identik dapat disatukan; bila satu kunci mempunyai harga berbeda, seluruh kelompok konflik dikarantina dan tidak dirata-ratakan.

Skema wilayah Papua pada snapshot berubah mulai 2024. Dua seri sebelum perubahan diberi label historis agar tidak disambungkan dengan cakupan wilayah sesudahnya. Baris agregat nasional tidak dimasukkan sebagai provinsi.

## Perubahan harga

```text
MoM (%) = 100 × (harga_bulan_ini / harga_bulan_sebelumnya − 1)
YoY (%) = 100 × (harga_bulan_ini / harga_bulan_sama_tahun_lalu − 1)
```

Perbandingan memakai bulan kalender yang tepat. Jika Februari kosong, MoM Maret tetap kosong; Januari tidak digunakan sebagai pembanding pengganti. Perubahan dihitung pada seri lengkap sebelum filter tampilan diterapkan.

Persentase ini adalah perubahan harga satu komoditas, bukan indeks inflasi resmi.

## Fluktuasi dan cakupan

```text
CV (%) = 100 × simpangan_baku_sampel / rata_rata_harga
Cakupan (%) = 100 × jumlah_bulan_tersedia / jumlah_bulan_dalam_rentang
```

CV memakai simpangan baku sampel (`ddof=1`) dengan minimal tiga observasi per wilayah–komoditas. Nilai lebih besar menunjukkan harga lebih berfluktuasi dalam rentang tersebut, bukan peluang harga naik pada bulan berikutnya.

Bandingkan CV bersama jumlah observasi dan cakupannya. Bulan kosong tidak dianggap sebagai harga nol atau harga yang stabil.

## Perbandingan provinsi

Satu komoditas dibandingkan pada satu bulan yang sama. Median dihitung tanpa bobot dari wilayah yang mempunyai harga valid.

```text
Selisih terhadap median (%) = 100 × (harga_wilayah / median_harga − 1)
```

Median tersebut bukan rata-rata nasional resmi. Ongkir, kualitas, serta ketersediaan pemasok tidak masuk perhitungan, sehingga harga rendah di suatu wilayah belum berarti biaya pembelian dan pengiriman akan lebih rendah.

## Membaca hasil

Tanda — berarti nilai belum dapat dihitung. Angka nol hanya dipakai jika hasil perhitungan atau jumlah observasinya benar-benar nol. Ambang pemantauan merupakan pilihan pengguna, bukan batas resmi pemerintah.

Frekuensi kenaikan dihitung dari jumlah pasangan bulan yang perubahannya melewati ambang, dibagi jumlah pasangan yang mempunyai pembanding. Rentang mengacu pada bulan akhir pasangan; harga pembanding bulan sebelumnya dapat berada tepat sebelum awal rentang. Frekuensi historis tidak ditafsirkan sebagai probabilitas masa depan.

## Bulan pengamatan bersama

Seri disaring berdasarkan minimal tiga harga dan minimum cakupan (default 80%). Perbandingan fluktuasi berikutnya menggunakan irisan bulan yang memiliki harga pada seluruh seri yang lolos. CV memerlukan minimal tiga bulan bersama. Rata-rata perubahan bulanan absolut menggunakan minimal dua pasangan kalender yang sama pada seluruh seri.

CV tingkat harga belum memisahkan tren dan musiman. Rata-rata perubahan absolut mengabaikan arah perubahan. Keduanya bukan ukuran peluang kenaikan berikutnya. Tabel penyaringan tersedia terpisah dari hasil perbandingan bulan bersama.

## Satuan dan ekspor

Ekspor sumber tidak memuat satuan. Tampilan harga mengikuti angka rupiah yang tercatat. Kolom satuan asumsi pada data olahan lama tidak digunakan untuk analisis atau disertakan dalam laporan harga.

Laporan Excel memuat ringkasan, data bersih, snapshot provinsi, fluktuasi, cakupan, bulan pembanding, perbandingan wilayah, dan catatan sumber/metode. Perubahan harga dihitung sebelum filter periode agar pasangan kalender tetap tepat.

Proses pembangunan ulang tersedia pada [Pemrosesan data](DATA_PIPELINE.md).

## Istilah dan warna

Tampilan menggunakan istilah komoditas dan provinsi. Seri Papua historis tetap ditandai karena cakupannya berbeda. Pada grafik perubahan, merah menunjukkan kenaikan dan teal menunjukkan penurunan. Pada grafik tren/fluktuasi, teal adalah warna seri utama. Pada perbandingan provinsi, teal menandai provinsi pilihan, abu-abu provinsi lain, dan garis amber menunjukkan median.
