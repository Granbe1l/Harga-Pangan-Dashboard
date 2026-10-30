# Pengujian

## Tes otomatis

Jalankan dari root repository setelah menginstal dependensi:

```bash
python -m unittest discover -s tests -v
```

Tes memeriksa pembersihan dan kecocokan berkas sumber, perbandingan bulan kalender, cakupan data, bulan pengamatan bersama, filter, perpindahan halaman, dan ekspor CSV/Excel. Temuan bulanan juga dibandingkan dengan hitungan `Decimal` dari CSV sumber.

## Pemeriksaan browser

Pemeriksaan ini memerlukan Playwright, Pandas, Openpyxl, dan Chromium di lingkungan pengujian. Dependensi browser tidak diperlukan untuk menjalankan dashboard.

Jalankan aplikasi, kemudian gunakan terminal lain:

```bash
python scripts/verify_browser.py --url http://127.0.0.1:8501 --chromium /usr/bin/chromium --output-dir /tmp/analyst-browser
```

Runner memeriksa tiga menu pada desktop 1440 × 950 dan ponsel lebar 390 px, perubahan filter, kondisi harga kosong, serta unduhan. Hasilnya berupa screenshot dan `browser-validation.json`; proses berhenti dengan status gagal jika pemeriksaan tidak terpenuhi.

[Ringkasan hasil](../reports/validation_summary.md) dan [hasil browser](../reports/browser_validation.json) disimpan bersama rilis. Pemeriksaan lokal tidak mencakup kecepatan koneksi pengguna, hosting publik, atau pemulihan aplikasi setelah sleep. Screenshot hanya mewakili kondisi yang diperiksa.
