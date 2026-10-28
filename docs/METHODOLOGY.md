# Rancangan dan metode analisis

## Rancangan kajian

Kajian menggunakan analisis deskriptif dan eksploratif terhadap data sekunder harga konsumen bulanan. Tujuannya menggambarkan perubahan harga, variasi relatif, dan perbedaan antarwilayah, lalu menghitung implikasi skenario harga pada anggaran belanja tetap. Tidak ada rancangan eksperimen, pengujian kausal, atau estimasi dampak kebijakan dalam kajian ini.

Snapshot mencakup Januari 2021–Oktober 2025 dengan kelengkapan berbeda menurut seri. Hasil yang tampil mengikuti fokus wilayah, komoditas, bulan, dan rentang pengamatan yang dipilih. Perubahan pilihan menghasilkan subanalisis, bukan sampel acak baru dari populasi. Statistik deskriptif tidak disertai klaim signifikansi atau generalisasi ke seluruh usaha.

## Pertanyaan dan unit analisis

Pertanyaan yang diperiksa adalah perubahan harga bulanan/tahunan, variasi relatif per komoditas, perbedaan harga antarwilayah pada bulan yang sama, dan perubahan anggaran dalam skenario harga tertentu.

Contoh penerapannya adalah anggaran bahan warung makan di Jawa Barat. Jumlah kebutuhan dimasukkan sendiri karena dataset hanya berisi harga. Contoh ini tidak berasal dari survei pemilik usaha. Perhitungan membantu mencoba skenario belanja; pembelian nyata tetap memerlukan harga pemasok, mutu, dan kondisi usaha yang tidak tersedia di sini.

Unit observasi adalah **satu provinsi × satu komoditas × satu bulan**. Nilainya merupakan rata-rata harga konsumen yang tercatat pada sumber, bukan harga setiap toko, transaksi, atau pelanggan.

## Pembersihan dan kualitas

File mentah dipertahankan sebagai bukti input. Pembersihan memisahkan baris pembuka dari header, mengubah tipe data, menyeragamkan label wilayah, serta memeriksa kunci observasi dan harga. Harga kosong atau tidak valid tidak diubah menjadi nol dan tidak diisi dengan harga rata-rata.

Duplikat identik dapat disatukan. Apabila satu kunci observasi memiliki lebih dari satu harga yang saling bertentangan, konflik harus terlihat pada catatan kualitas; harga tidak dipilih secara sewenang-wenang atau dirata-ratakan tanpa dasar sumber.

Kode provinsi dipakai untuk membantu konsistensi label. Perubahan wilayah administrasi tidak boleh dianggap sekadar perbedaan ejaan: provinsi hasil pemekaran dan cakupan wilayah historis perlu dipertahankan sesuai observasi sumber. Rekaman agregat nasional tidak boleh ikut dihitung sebagai sebuah provinsi.

Laporan kualitas harus dibaca bersama hasil analisis. Jumlah baris bersih, harga yang ditolak, duplikasi, rentang waktu, dan cakupan wilayah dapat berubah ketika input diperbarui.

## Perubahan harga bulanan dan tahunan

Untuk harga `P` dari provinsi dan komoditas yang sama:

```text
MoM (%) = 100 × (P_bulan_ini / P_bulan_sebelumnya − 1)
YoY (%) = 100 × (P_bulan_ini / P_bulan_sama_tahun_lalu − 1)
```

Perbandingan menggunakan bulan kalender yang tepat. Misalnya, jika Februari tidak ada, harga Maret tidak dibandingkan dengan Januari sebagai MoM. Hasil MoM Maret tetap kosong. Perubahan dihitung menggunakan seri lengkap sebelum filter periode tampilan diterapkan, agar awal periode tampilan tidak kehilangan pembanding yang sebenarnya tersedia.

Harga pangan di sini tidak boleh disebut sebagai indeks inflasi resmi. Persentase perubahan satu harga komoditas berbeda dari penghitungan indeks harga konsumen dengan keranjang dan bobot resmi.

## Volatilitas dan cakupan

Koefisien variasi mengukur besar simpangan harga relatif terhadap rata-ratanya:

```text
CV (%) = 100 × simpangan_baku_harga / rata_rata_harga
```

CV memakai simpangan baku sampel (`ddof=1`) dan dihitung terpisah untuk setiap pasangan provinsi–komoditas di periode terpilih. Pilihan ini membuat perbandingan relatif dapat dibaca tanpa membandingkan nominal rupiah beras dengan nominal rupiah cabai. Setidaknya tiga observasi diperlukan untuk menampilkan indikator ini. Nilai dengan tiga bulan observasi belum memiliki kekuatan bukti yang sama dengan seri panjang yang lengkap.

Cakupan dihitung dari jumlah bulan dengan harga valid dibandingkan jumlah bulan kalender yang diharapkan dalam periode analisis. Gunakan cakupan dan jumlah observasi ketika membandingkan volatilitas. Bulan yang kosong tidak dianggap sebagai harga nol atau harga stabil.

## Perbandingan antarprovinsi

Bandingkan satu komoditas pada satu bulan yang sama. Pembanding median dihitung dari provinsi yang memiliki harga valid pada bulan itu:

```text
Selisih terhadap median (%) = 100 × (harga_provinsi / median_harga_provinsi − 1)
```

Median ini tidak diberi bobot jumlah penduduk, volume penjualan, atau konsumsi. Cakupan provinsi juga dapat berubah. Tampilkan sebagai **median provinsi dengan data**, bukan harga nasional resmi. Harga rendah di suatu provinsi belum membuktikan bahwa membeli dan mengirim barang dari wilayah tersebut lebih murah, sebab ongkir dan spesifikasi barang tidak tersedia.

## Analisis skenario anggaran

Pengguna memasukkan kuantitas kebutuhan dan skenario perubahan harga setiap bahan. Perhitungan dasarnya:

```text
Biaya dasar per bahan = kuantitas × harga bulan terpilih
Biaya skenario = kuantitas × harga bulan terpilih × (1 + perubahan_harga / 100)
Selisih anggaran = total biaya skenario − total biaya dasar
```

Harga harus tersedia untuk provinsi dan bulan yang dipilih. Jika ada bahan tanpa harga, hasil harus menunjukkan bahwa keranjang belum lengkap; subtotal bahan yang tersedia tidak boleh ditampilkan seolah-olah merupakan total keranjang lengkap. Harga bulan lama tidak dipakai secara diam-diam.

Kolom satuan tidak tersedia pada CSV mentah. Jika aplikasi menggunakan kg untuk sebagian besar bahan dan liter untuk minyak goreng, hal tersebut adalah **asumsi satuan yang perlu dikonfirmasi**, bukan metadata yang berhasil dibuktikan dari file asal. Kuantitas harus mengikuti satuan asumsi yang ditampilkan. Simulasi tidak mencakup ongkos pengiriman, susut, biaya penyimpanan, pajak, atau pembelian nyata.

## Penyajian dan interpretasi hasil

Laporan menyajikan hasil sebagai narasi, tabel, dan gambar yang merujuk pada fokus analisis yang sama. Catatan di dekat tabel atau gambar menjelaskan periode, unit, sumber, dan keadaan data kosong. Kesimpulan merangkum hasil yang terhitung; rekomendasi operasional dipisahkan dari temuan yang benar-benar teramati.

## Keterbatasan

- Ambang peringatan adalah aturan pengguna untuk pemantauan, bukan batas resmi pemerintah atau hasil model prediksi.
- Data historis menunjukkan pola; tidak membuktikan penyebab kenaikan harga.
- Perkiraan biaya bukan transaksi atau penghematan yang telah diwujudkan.
- Tidak ada data persediaan, jumlah penjualan, laba, atau biaya pemasok. Hindari menyimpulkan optimalisasi stok atau peningkatan profit dari tabel ini saja.
- Sumber adalah salinan pihak ketiga yang dikaitkan dengan sumber pemerintah. Pembaruan, revisi, dan hak penggunaan ulang perlu diperiksa pada sumber primer.

## Cara memeriksa hasil

Pilih satu pasangan provinsi–komoditas, periksa harga dua bulan berturut-turut di tabel bersih, lalu hitung MoM secara manual. Ulangi pada seri yang mempunyai bulan kosong untuk memastikan hasil tidak memakai bulan sebelumnya yang salah. Untuk simulasi, gunakan satu bahan dan kuantitas sederhana, cocokkan perkalian dasar dan skenarionya, lalu tambahkan satu bahan yang tidak memiliki harga pada bulan tersebut.
