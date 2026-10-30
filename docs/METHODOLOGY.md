# Metode perhitungan Analisis Harga Pangan

## Tujuan dan data

Dashboard membantu memantau perubahan harga bahan dan mencoba anggaran belanja warung makan. Jumlah kebutuhan dimasukkan pengguna karena dataset hanya berisi harga.

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

## Perbandingan wilayah

Satu komoditas dibandingkan pada satu bulan yang sama. Median dihitung tanpa bobot dari wilayah yang mempunyai harga valid.

```text
Selisih terhadap median (%) = 100 × (harga_wilayah / median_harga − 1)
```

Median tersebut bukan rata-rata nasional resmi. Ongkir, kualitas, serta ketersediaan pemasok tidak masuk perhitungan, sehingga harga rendah di suatu wilayah belum berarti biaya pembelian dan pengiriman akan lebih rendah.

## Simulator anggaran

```text
Belanja acuan = jumlah × harga bulan pilihan
Harga skenario = harga acuan × (1 + perubahan harga / 100)
Belanja skenario = jumlah × harga skenario
Selisih anggaran = total belanja skenario − total belanja acuan
```

Harga berasal dari bulan dan wilayah yang dipilih. Jika harga bahan dengan jumlah positif tidak tersedia, total lengkap tidak diterbitkan. Harga bulan lain tidak dipakai secara otomatis.

Satuan **kg** dipakai untuk sebagian besar bahan dan **liter** untuk minyak goreng. Ini asumsi kerja; CSV asli tidak menyediakan kolom satuan. Jumlah belanja harus mengikuti satuan yang ditampilkan. Perhitungan belum mencakup ongkir, susut, penyimpanan, pajak, atau biaya operasional lain.

## Memeriksa hasil

Coba satu komoditas dengan dua bulan berurutan dan hitung MoM secara manual. Ulangi pada seri yang mempunyai bulan kosong. Di simulator, gunakan satu bahan dan jumlah sederhana, cocokkan hasil perkalian, lalu coba keadaan saat harga bulan pilihan tidak tersedia.

Ambang kenaikan adalah parameter pengguna. Data historis tidak membuktikan penyebab perubahan harga, hasil simulator bukan penghematan aktual, dan file primer diberikan pengguna dan cocok CSV–XLSX; pengambilan server dan satuan belum diverifikasi independen.

## Ringkasan anggaran historis dan skenario

Ringkasan utama menggunakan enam jumlah contoh tetap: beras medium 25 kg, ayam ras 10 kg, telur ayam ras 5 kg, minyak goreng curah 5 liter, cabai rawit merah 2 kg, dan bawang merah 2 kg. Ini asumsi latihan untuk satu kali belanja, bukan catatan usaha.

Kontribusi perubahan biaya = (harga bulan pilihan − harga bulan kalender sebelumnya) × jumlah contoh. Perubahan total keranjang hanya diberikan jika seluruh bahan aktif memiliki harga pada kedua bulan. Grafik bahan yang memiliki pembanding dapat tersedia saat total belum lengkap; jumlah pembanding dinyatakan secara eksplisit. Biaya keranjang bulan pilihan sendiri hanya diberikan bila semua harga bulan itu tersedia. Perubahan nol dibedakan dari perhitungan yang belum tersedia.

Simulator adalah hasil hipotetis terpisah. Kuantitas dan persentase dapat diubah per bahan. Penerapan persentase massal tidak mengubah kuantitas atau harga acuan. Sumber per baris membedakan snapshot yang belum diedit, harga yang diubah pengguna, dan harga yang belum tersedia. Harga manual hanya digunakan ketika mode edit harga aktif; data historis tidak berubah.

Minimum cakupan CV adalah filter tampilan pengguna (default 80%), bukan aturan resmi atau jaminan kualitas statistik. CV menggunakan tingkat harga dan belum memisahkan tren dari musiman. Seri dengan kurang dari tiga observasi tidak diberi nilai CV; seri yang tidak memenuhi cakupan tetap dapat ditinjau pada tabel lengkap dengan status yang jelas.

## Perbandingan setara dan audit cakupan

Harga bulan kini dan bulan sebelumnya diambil terpisah agar harga lama yang valid tidak hilang saat baris kini kosong. Profil A/B tetap memakai enam bahan. Profil C mengeluarkan minyak secara eksplisit untuk latihan dengan riwayat lebih panjang; tidak ada perubahan komposisi otomatis antarbulan. Profil bukan survei kebutuhan usaha.

Untuk grafik fluktuasi terbaru, seri disaring menurut minimal tiga harga dan cakupan. Perhitungan berikutnya memakai irisan bulan yang memiliki harga untuk seluruh seri yang lolos. Ukuran perubahan memakai bulan akhir yang sama, dan seluruh seri harus memiliki harga pada bulan kalender sebelumnya. CV harga memerlukan minimal tiga bulan bersama; rata-rata perubahan absolut dan simpangan perubahan membutuhkan minimal dua pasangan bersama. Rata-rata perubahan absolut mengabaikan arah; tidak berarti prediksi atau tingkat risiko usaha. Tabel penyaringan dipisahkan dari tabel perbandingan bulan bersama.

Batas anggaran dibandingkan dengan total skenario lengkap saja. Harga/satuan input pengguna dicatat per bahan, belum dianggap hasil verifikasi eksternal. Laporan analisis mencatat cakupan keranjang latihan dan sensitivitas komposisi.

## Ekspor primer aktif

File CSV unggahan adalah input aktif; XLSX dipertahankan sebagai pembanding. Harga bersih cocok dengan versi sebelumnya, sehingga hasil numerik tidak dibuat berubah tanpa alasan. Nomor baris karantina mengikuti ekspor header-pertama. Halaman Ringkasan memisahkan temuan persentase tanpa asumsi jumlah dari estimasi keranjang yang membutuhkan satuan dan kuantitas.
