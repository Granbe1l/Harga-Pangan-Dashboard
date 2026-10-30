import unittest

import pandas as pd

from analyst.pipeline import clean_source, normalize_province, parse_month, parse_price


def row(price="Rp12,072", month="Januari", province=" Jawa Barat ", code="32", year="2025"):
    return {"Kode Provinsi": code, "Nama Provinsi": province, "Komoditas": "Beras Premium", "Tahun": year, "Bulan": month, "Harga": price}


class PipelineTests(unittest.TestCase):
    def test_rupiah_thousands_and_ambiguous_decimals(self):
        self.assertEqual(parse_price("Rp12,072"), 12072)
        self.assertEqual(parse_price("Rp 12.072"), 12072)
        self.assertEqual(parse_price("Rp1,200,000"), 1200000)
        self.assertIsNone(parse_price("Rp12,5"))
        self.assertIsNone(parse_price(12072.5))
        self.assertIsNone(parse_price("-"))
        self.assertIsNone(parse_price(float("nan")))

    def test_month_whitespace_and_invalid_period(self):
        self.assertEqual(parse_month("2025", " Januari "), pd.Timestamp("2025-01-01"))
        self.assertIsNone(parse_month("2025", "Smarch"))
        self.assertIsNone(parse_month("25", "Januari"))

    def test_identical_duplicates_are_removed_without_imputing_missing_price(self):
        cleaned, rejected, report = clean_source(pd.DataFrame([row(), row(), row(None, month="Februari")]))
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(report["raw_rows"], report["clean_rows"] + report["rejected_rows"])
        self.assertEqual(set(rejected.reason), {"exact_duplicate", "missing_price"})
        self.assertEqual(cleaned.iloc[0].province, "Jawa Barat")

    def test_conflicting_key_is_quarantined_in_full(self):
        cleaned, rejected, report = clean_source(pd.DataFrame([row(), row("Rp13,000"), row(month="Februari")]))
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(report["conflicting_rows_quarantined"], 2)
        self.assertEqual(rejected.reason.tolist(), ["conflicting_duplicate", "conflicting_duplicate"])

    def test_zero_negative_and_national_aggregate_are_excluded(self):
        cleaned, rejected, _ = clean_source(pd.DataFrame([row("Rp0"), row("-100"), row(province="Indonesia", code="00")]))
        self.assertTrue(cleaned.empty)
        self.assertEqual(rejected.reason.tolist(), ["non_positive_price", "non_positive_price", "national_aggregate"])

    def test_papua_historical_series_is_not_joined_to_new_coverage(self):
        old = normalize_province("94", "Papua", pd.Timestamp("2023-12-01"))
        new = normalize_province("91", "Papua", pd.Timestamp("2024-01-01"))
        self.assertNotEqual(old[0], new[0])
        self.assertIn("historis", old[1])
        self.assertEqual(new[1], "Papua")

    def test_valid_yogyakarta_names_are_unified(self):
        self.assertEqual(normalize_province("34", " D.I Yogyakarta ", pd.Timestamp("2025-01-01"))[1], "DI Yogyakarta")


if __name__ == "__main__":
    unittest.main()
