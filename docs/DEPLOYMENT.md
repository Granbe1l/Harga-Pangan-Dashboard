# Menerbitkan aplikasi untuk CV

Aplikasi disiapkan untuk Streamlit Community Cloud. Publikasi memerlukan akses akun hosting pemilik; commit GitHub tidak otomatis membuktikan aplikasi sudah terbit.

1. Masuk ke https://share.streamlit.io/ dengan GitHub.
2. Pilih repository `Granbe1l/Harga-Pangan-Dashboard`, branch `main`, entrypoint `app.py`.
3. Pilih Python **3.12** pada pengaturan lanjutan. Dependensi utama terdapat di `requirements.txt`; lock lengkap tersedia di `requirements.lock.txt`.
4. Pilih alamat aplikasi yang tersedia, lalu deploy. Tidak ada secret atau API key yang perlu diisi.
5. Buka URL hasil deploy dalam incognito. Pastikan aplikasi dapat digunakan tanpa login, bukan hanya oleh pemilik akun.

## Pemeriksaan pada URL publik

- Buka dari sesi baru dan catat waktu sampai kartu dan grafik dapat digunakan. Bedakan kondisi aktif dan kondisi setelah aplikasi tidur.
- Pastikan menu, filter wilayah/bulan, simulasi, reset, dan file Excel berfungsi.
- Periksa pada laptop dan ponsel; buka sidebar melalui tombol menu pada layar sempit.
- Verifikasi input keranjang bertahan saat berpindah menu, tetapi tidak bocor ke sesi browser lain.
- Uji setelah aplikasi tidak aktif dan dibangunkan kembali. Kebijakan sleep bergantung hosting; jangan menyatakan selalu aktif tanpa bukti.
- Pastikan link kode sumber dan metodologi mengarah ke repository publik yang tepat.

Belum ada URL publik yang diberikan dalam sesi pengembangan. Pemeriksaan browser lokal tidak membuktikan akses publik, performa Internet, atau pemulihan dari sleep pada hosting. Isi URL yang benar pada CV setelah pemeriksaan ini selesai; jangan menggunakan alamat localhost.

Contoh label CV: **Live Dashboard · Source Code**. Hubungkan Live Dashboard ke URL hasil deploy, Source Code ke repository GitHub.
