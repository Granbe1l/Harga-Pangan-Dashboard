# Metode perhitungan PanganWatch

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

Ambang kenaikan adalah parameter pengguna. Data historis tidak membuktikan penyebab perubahan harga, hasil simulator bukan penghematan aktual, dan salinan belum diperiksa terhadap versi resmi terbaru.
