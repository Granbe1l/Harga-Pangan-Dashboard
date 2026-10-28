# Menjelaskan studi harga pangan dalam CV

Gunakan bagian ini setelah menjalankan proyek dan memeriksa hasilnya. Contoh di bawah mengikuti laporan yang disertakan. Pakai dalam CV setelah dapat menjelaskan perhitungan dan menunjukkan kode terkait; perbarui angka bila input datanya berubah.

## Judul proyek

**Studi Deskriptif Harga Pangan Indonesia dan Simulasi Anggaran UMKM**

Python · Pandas · SQL/SQLite · Streamlit · Excel

## Contoh dua butir CV

- Mengolah **33.422 baris mentah** harga pangan bulanan menjadi **32.480 observasi valid** melalui normalisasi wilayah dan validasi harga; memisahkan **942 observasi tanpa harga valid** tanpa mengisi harga buatan.
- Menyusun analisis deskriptif berbasis SQL/Python dan laporan interaktif Streamlit; mengidentifikasi **dua komoditas dengan kenaikan harga bulanan ≥10% di Jawa Barat pada Oktober 2025**, serta menghitung skenario perubahan anggaran bahan pangan.

Angka di atas mengikuti snapshot yang disertakan. Pada butir kedua, komoditasnya adalah **Cabai Merah Keriting (11,16%)** dan **Cabai Merah Besar (10,52%)**. Pembandingnya September 2025 dan ambang 10% merupakan parameter analisis. Rinciannya dapat diperiksa pada [laporan analisis](../reports/analysis_summary.md). Jika menulis jumlah wilayah, jangan menyebut 40 seri historis sebagai 40 provinsi pada satu waktu.

Temuan lain yang dapat dibahas saat wawancara: harga **Cabai Rawit Merah di Jawa Barat memiliki CV 36,85%** selama November 2024–Oktober 2025, dengan cakupan **12/12 bulan**. Angka ini mengukur variasi harga historis, bukan peluang harga naik atau besarnya penghematan.

## Kalimat ringkas untuk portofolio

> Studi ini mendeskripsikan perubahan dan variasi harga pangan historis, kemudian menghitung skenario anggaran belanja untuk kuantitas tetap. Pengolahan meliputi pembersihan data, analisis SQL/Python, dan penyajian laporan interaktif serta Excel. Hasil skenario merupakan perkiraan, bukan pengeluaran atau penghematan bisnis yang telah diamati.

## Klaim yang perlu dihindari

| Klaim | Alasan | Bentuk yang dapat dipertanggungjawabkan |
|---|---|---|
| "Menghemat biaya UMKM sebesar 20%" | Belum ada implementasi dan bukti pengeluaran usaha. | "Menyediakan simulasi perubahan anggaran pada skenario harga yang ditentukan pengguna." |
| "Memantau harga real-time" | Dataset observasi bulanan dan berjalan dari salinan lokal. | "Memantau pola harga historis bulanan." |
| "Memprediksi harga bulan depan" | Modul skenario bukan model prediksi teruji. | "Menguji skenario kenaikan/penurunan harga terhadap anggaran." |
| "Menghitung inflasi nasional" | Tidak menggunakan metodologi indeks dan bobot resmi. | "Menghitung perubahan harga komoditas dan median provinsi dengan data." |
| "Mengoptimalkan stok" | Tidak tersedia stok, permintaan, atau lead time pemasok. | "Membantu menentukan prioritas pemantauan harga dan evaluasi anggaran." |

## Urutan tampilan saat reviewer membuka proyek

1. Judul dan pertanyaan analisis yang jelas.
2. Desain deskriptif, unit observasi, dan asal data.
3. Satu tabel atau gambar yang menjawab pertanyaan dan dilengkapi periode serta cakupan.
4. Satu skenario anggaran dengan asumsi dan perhitungan yang bisa diperiksa.
5. Kesimpulan, keterbatasan, dan akses ke kode serta tabel hasil.

Nama perusahaan atau lowongan tujuan dapat mengubah bagian yang lebih dulu ditekankan. Proyek ini menunjukkan kemampuan analisis; tidak menjamin hasil seleksi magang.

## Bahan penjelasan saat wawancara

- **Rancangan studinya apa?** Analisis deskriptif dan eksploratif menggunakan data sekunder harga konsumen bulanan. Kajian menggambarkan pola, tanpa menguji penyebab atau dampak kebijakan.
- **Kasusnya apa?** Anggaran belanja warung makan di Jawa Barat merupakan contoh latihan. Kuantitas kebutuhan dimasukkan pengguna; tidak ada klaim bahwa proyek dikerjakan untuk klien nyata.
- **Apa yang dibersihkan?** Tunjukkan contoh format harga, variasi penulisan wilayah, 938 harga kosong, dan empat harga tidak positif. Jelaskan mengapa harga kosong tidak diganti dengan nol.
- **Mengapa MoM tidak memakai baris sebelumnya saja?** Jika Februari kosong, Maret tidak boleh dibandingkan dengan Januari sebagai perubahan satu bulan. Tunjukkan query pembanding kalendernya.
- **Mengapa CV dan median?** CV membandingkan variasi relatif pada seri sejenis; median membandingkan provinsi pada komoditas dan bulan yang sama. Keduanya bukan probabilitas kenaikan harga atau angka nasional resmi.
- **Apa hasil simulator?** Perkiraan selisih anggaran dari kuantitas dan skenario harga, dengan satuan asumsi yang terlihat. Bukan bukti penghematan aktual.
- **Apa yang akan diperbaiki?** Konfirmasi sumber primer dan satuannya, lalu tambahkan data pembelian usaha yang sah jika tersedia. Fitur stok atau prediksi memerlukan data dan validasi tersendiri.

Saat demo, cocokkan satu MoM dan satu simulasi satu bahan dengan hitungan manual. Lalu tunjukkan keadaan ketika harga bulan tertentu tidak tersedia. Kalau memakai bantuan alat atau AI dalam pengembangan, jelaskan penggunaannya dengan jujur dan pastikan dapat menerangkan serta mengubah kode yang ditampilkan.
