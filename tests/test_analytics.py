"""Meaningful calendar, and coverage invariants (unittest/pytest)."""
import sqlite3
import unittest

import pandas as pd

from analyst.analytics import (
    comparison_frame,
    create_sql_views,
    province_comparison,
    volatility_summary,
)


def prices(*records):
    return pd.DataFrame([
        {"province_code": code, "province": province, "commodity": commodity,
         "date": date, "price": price, "unit": "kg"}
        for code, province, commodity, date, price in records
    ])


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.df = prices(
            ("32", "Jawa Barat", "Beras", "2023-01-01", 10000.0),
            ("32", "Jawa Barat", "Beras", "2023-03-01", 12000.0),
            ("32", "Jawa Barat", "Beras", "2023-04-01", 15000.0),
            ("32", "Jawa Barat", "Beras", "2024-01-01", 13000.0),
        )

    def test_missing_month_does_not_create_false_mom(self):
        frame = comparison_frame(self.df).set_index("date")
        self.assertTrue(pd.isna(frame.loc[pd.Timestamp("2023-03-01"), "mom_pct"]))
        self.assertAlmostEqual(frame.loc[pd.Timestamp("2023-04-01"), "mom_pct"], 25.0)

    def test_yoy_uses_same_month_previous_year(self):
        frame = comparison_frame(self.df).set_index("date")
        self.assertAlmostEqual(frame.loc[pd.Timestamp("2024-01-01"), "yoy_pct"], 30.0)

    def test_coverage_counts_missing_endpoints(self):
        result = volatility_summary(self.df, "2023-01-01", "2023-06-01").iloc[0]
        self.assertEqual(result["expected_months"], 6)
        self.assertEqual(result["observations"], 3)
        self.assertAlmostEqual(result["coverage_pct"], 50.0)
        self.assertGreater(result["cv_pct"], 0)

    def test_sparse_series_has_no_cv(self):
        result = volatility_summary(self.df, "2023-01-01", "2023-03-01").iloc[0]
        self.assertTrue(pd.isna(result["cv_pct"]))

    def test_duplicate_series_key_is_rejected(self):
        with self.assertRaises(ValueError):
            comparison_frame(pd.concat([self.df, self.df.iloc[:1]], ignore_index=True))

    def test_comparison_uses_selected_commodity_and_month(self):
        extra = prices(
            ("33", "Jawa Tengah", "Beras", "2023-01-01", 20000.0),
            ("33", "Jawa Tengah", "Cabai", "2023-01-01", 90000.0),
        )
        result = province_comparison(pd.concat([self.df, extra]), "Beras", "2023-01-15")
        self.assertEqual(len(result), 2)
        self.assertEqual(result["median_price"].iloc[0], 15000.0)






    def test_sql_and_python_exact_month_calculations_agree(self):
        with sqlite3.connect(":memory:") as connection:
            self.df.to_sql("prices", connection, index=False)
            create_sql_views(connection)
            sql = pd.read_sql_query("SELECT date, mom_pct, yoy_pct FROM monthly_price_changes ORDER BY date", connection)
        python = comparison_frame(self.df)
        pd.testing.assert_series_equal(sql["mom_pct"], python["mom_pct"], check_names=False)
        pd.testing.assert_series_equal(sql["yoy_pct"], python["yoy_pct"], check_names=False)

    def test_sql_ratios_do_not_use_integer_division(self):
        frame = prices(
            ("32", "Jawa Barat", "Beras", "2023-01-01", 10000),
            ("32", "Jawa Barat", "Beras", "2023-02-01", 12500),
        )
        frame["price"] = frame["price"].astype(int)
        with sqlite3.connect(":memory:") as connection:
            frame.to_sql("prices", connection, index=False)
            create_sql_views(connection)
            value = connection.execute("SELECT mom_pct FROM monthly_price_changes WHERE date = '2023-02-01'").fetchone()[0]
        self.assertAlmostEqual(value, 25.0)


if __name__ == "__main__":
    unittest.main()
