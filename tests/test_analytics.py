"""Meaningful calendar, coverage, and scenario invariants (unittest/pytest)."""
import sqlite3
import unittest

import pandas as pd

from analyst.analytics import (
    basket_simulation,
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

    def test_budget_scenario_uses_quantities_and_item_shocks(self):
        basket = pd.DataFrame({"commodity": ["Beras"], "quantity": [10.0], "shock_pct": [20.0]})
        result = basket_simulation(self.df, "Jawa Barat", "2023-01-01", basket)
        self.assertTrue(result["complete"])
        self.assertEqual(result["baseline_total"], 100000.0)
        self.assertEqual(result["scenario_total"], 120000.0)
        self.assertEqual(result["difference"], 20000.0)

    def test_budget_missing_month_does_not_borrow_price(self):
        basket = pd.DataFrame({"commodity": ["Beras"], "quantity": [10], "shock_pct": [20]})
        result = basket_simulation(self.df, "Jawa Barat", "2023-02-01", basket)
        self.assertFalse(result["complete"])
        self.assertIsNone(result["baseline_total"])
        self.assertEqual(result["missing_commodities"], ["Beras"])

    def test_budget_incomplete_total_is_not_silently_a_subtotal(self):
        basket = pd.DataFrame({"commodity": ["Beras", "Cabai"], "quantity": [10, 2], "shock_pct": [0, 10]})
        result = basket_simulation(self.df, "Jawa Barat", "2023-01-01", basket)
        self.assertFalse(result["complete"])
        self.assertIsNone(result["scenario_total"])
        self.assertEqual(result["known_baseline_total"], 100000.0)

    def test_zero_quantity_missing_commodity_does_not_break_total(self):
        basket = pd.DataFrame({"commodity": ["Beras", "Cabai"], "quantity": [10, 0], "shock_pct": [0, 10]})
        result = basket_simulation(self.df, "Jawa Barat", "2023-01-01", basket)
        self.assertTrue(result["complete"])
        self.assertEqual(result["baseline_total"], 100000.0)

    def test_negative_quantity_and_excessive_price_drop_rejected(self):
        for quantity, shock in [(-1, 0), (1, -101), (float("inf"), 0)]:
            basket = pd.DataFrame({"commodity": ["Beras"], "quantity": [quantity], "shock_pct": [shock]})
            with self.assertRaises(ValueError):
                basket_simulation(self.df, "Jawa Barat", "2023-01-01", basket)

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
