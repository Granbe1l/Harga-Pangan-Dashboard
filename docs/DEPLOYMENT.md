# Deployment

Aplikasi dapat dijalankan melalui Streamlit Community Cloud:

1. Masuk ke https://share.streamlit.io/ dengan akun GitHub.
2. Pilih repository `Granbe1l/Harga-Pangan-Dashboard`, branch `main`, dan entrypoint `app.py`.
3. Gunakan Python **3.12**. Dependensi dibaca dari `requirements.txt`; versi lengkap tersedia pada `requirements.lock.txt`.
4. Tentukan alamat aplikasi lalu deploy. Aplikasi tidak memerlukan API key atau secret.

## Pemeriksaan setelah deploy

- Buka URL melalui incognito untuk memeriksa akses tanpa login.
- Periksa ketiga menu, filter wilayah/bulan/bahan, dan unduhan Excel pada desktop serta ponsel.
- Pastikan sesi baru tidak membawa input dari pengunjung lain.
- Catat waktu muat pada kondisi aktif dan setelah aplikasi sleep.
- Periksa tautan sumber data, metode, dan repository.

Pengujian yang tersimpan di repository dilakukan pada server lokal. Akses publik dan perilaku sleep hosting belum diverifikasi.

## Memperbarui aplikasi

Aplikasi yang terhubung ke branch `main` akan menerima perubahan dari push ke branch tersebut. URL dan konfigurasi deployment tetap sama. Jika perubahan belum terlihat, periksa log melalui **Manage app**, lalu gunakan **Reboot app** bila diperlukan.

Alamat aplikasi: https://harga-pangan-dashboard-candy.streamlit.app/. Akses publik dari lingkungan pengujian dibatasi proxy, sehingga status layanan pada alamat tersebut belum diverifikasi secara langsung.
