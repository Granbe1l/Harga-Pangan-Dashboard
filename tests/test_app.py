"""Exercise the PanganWatch dashboard and its interactive calculations."""

from pathlib import Path
import html
import re
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["Ringkasan", "Risiko harga", "Perbandingan wilayah", "Simulator anggaran", "Data & metode"]


class DashboardTests(unittest.TestCase):
    def open_app(self):
        return AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()

    def assert_no_errors(self, app):
        self.assertEqual([e.message for e in app.exception], [])

    def rendered_copy(self, app):
        """Read visible copy even when a finding is rendered in an HTML note."""
        parts = [item.value for item in app.markdown] + [item.value for item in app.caption]
        parts += [item.proto.body for item in app.get("html")]
        text = html.unescape(re.sub(r"<[^>]+>", " ", " ".join(parts)))
        return re.sub(r"\s+", " ", text.replace("**", " ")).strip()

    def test_navigation_renders_all_five_pages(self):
        app = self.open_app()
        for page in PAGES:
            app.sidebar.radio(key="page").set_value(page).run()
            self.assert_no_errors(app)
            self.assertTrue(len(app.metric) >= 3, page)

    def test_opening_dashboard_has_original_name_and_price_metrics(self):
        app = self.open_app()
        self.assert_no_errors(app)
        self.assertEqual(app.title[0].value, "Analisis Harga Pangan dan Simulasi Anggaran Bahan Baku UMKM Kuliner")
        self.assertEqual(len(app.metric), 4)
        self.assertTrue(app.metric[0].value.startswith("Rp "))
        self.assertNotEqual(app.metric[1].value, "—")

    def test_selected_commodity_is_identified_in_the_price_metric(self):
        app = self.open_app()
        self.assertEqual(app.metric[0].label, "Harga Beras Medium")
        app.sidebar.selectbox(key="commodity").set_value("Cabai Rawit Merah").run()
        self.assert_no_errors(app)
        self.assertEqual(app.metric[0].label, "Harga Cabai Rawit Merah")

    def test_monthly_finding_reports_only_comparable_commodities(self):
        app = self.open_app()
        app.sidebar.selectbox(key="as_of").set_value(pd.Timestamp("2025-10-01")).run()
        self.assert_no_errors(app)
        text = self.rendered_copy(app)
        self.assertIn("Temuan bulan ini", text)
        self.assertIn("2 dari 24 komoditas", text)
        self.assertIn("Cabai Merah Keriting +11,16%", text)
        self.assertIn("Jawa Barat", text)
        self.assertIn("Oktober 2025", text)

    def test_monthly_finding_updates_when_threshold_changes(self):
        app = self.open_app()
        app.sidebar.selectbox(key="as_of").set_value(pd.Timestamp("2025-10-01")).run()
        app.sidebar.slider(key="threshold").set_value(40).run()
        self.assert_no_errors(app)
        text = self.rendered_copy(app)
        self.assertIn("Tidak ada komoditas", text)
        self.assertIn("40%", text)
        self.assertIn("24", text)
        self.assertNotIn("2 dari 24 komoditas", text)

    def test_budget_zero_shock_matches_baseline_and_change_updates_it(self):
        app = self.open_app()
        app.sidebar.radio(key="page").set_value("Simulator anggaran").run()
        app.slider(key="basket_shock").set_value(0).run()
        self.assert_no_errors(app)
        self.assertEqual(app.metric[0].value, app.metric[1].value)
        baseline = app.metric[0].value
        app.slider(key="basket_shock").set_value(25).run()
        self.assert_no_errors(app)
        self.assertEqual(app.metric[0].value, baseline)
        self.assertNotEqual(app.metric[0].value, app.metric[1].value)

    def test_empty_basket_gives_guidance(self):
        app = self.open_app()
        app.sidebar.radio(key="page").set_value("Simulator anggaran").run()
        app.multiselect(key="basket_commodities").set_value([]).run()
        self.assert_no_errors(app)
        self.assertTrue(any("Pilih minimal satu" in item.value for item in app.info))

    def test_missing_month_does_not_show_stale_price_or_complete_budget(self):
        app = self.open_app()
        app.sidebar.selectbox(key="province").set_value("Papua Pegunungan").run()
        app.sidebar.selectbox(key="as_of").set_value(pd.Timestamp("2025-10-01")).run()
        self.assert_no_errors(app)
        self.assertEqual(app.metric[0].value, "—")
        self.assertIn("Belum ada harga pada bulan ini", self.rendered_copy(app))
        app.sidebar.radio(key="page").set_value("Simulator anggaran").run()
        self.assert_no_errors(app)
        self.assertEqual(app.metric[0].value, "—")
        self.assertTrue(any("Total belum lengkap" in item.value for item in app.warning))

    def test_first_month_has_no_false_growth(self):
        app = self.open_app()
        app.sidebar.selectbox(key="as_of").set_value(pd.Timestamp("2021-01-01")).run()
        self.assert_no_errors(app)
        self.assertEqual(app.metric[1].value, "—")
        self.assertEqual(app.metric[2].value, "—")
        self.assertIn("Perubahan bulanan belum bisa dihitung", self.rendered_copy(app))

    def test_risk_first_month_has_unknown_growth_and_effective_window(self):
        app = self.open_app()
        app.sidebar.selectbox(key="as_of").set_value(pd.Timestamp("2021-01-01")).run()
        self.assertEqual(len(app.get("plotly_chart")), 0)
        app.sidebar.radio(key="page").set_value("Risiko harga").run()
        self.assert_no_errors(app)
        self.assertEqual(app.metric[0].value, "—")
        self.assertEqual(app.metric[1].value, "—")
        table = app.dataframe[0].value
        self.assertTrue((table["Bulan dalam rentang"] == 1).all())
        self.assertTrue(app.sidebar.selectbox(key="commodity").disabled)

    def test_incomplete_budget_has_subtotal_and_recovery_month(self):
        app = self.open_app()
        app.sidebar.selectbox(key="as_of").set_value(pd.Timestamp("2021-01-01")).run()
        app.sidebar.radio(key="page").set_value("Simulator anggaran").run()
        self.assert_no_errors(app)
        self.assertEqual(app.metric[0].value, "—")
        self.assertIn("Subtotal bahan", self.rendered_copy(app))
        self.assertTrue(any("Harga seluruh bahan aktif tersedia" in i.value for i in app.info))

    def test_manual_prices_are_labelled_and_render_without_exception(self):
        app = self.open_app()
        app.sidebar.radio(key="page").set_value("Simulator anggaran").run()
        app.checkbox(key="manual_prices").check().run()
        self.assert_no_errors(app)
        self.assertTrue(any("input pengguna" in i.value for i in app.info))
        self.assertNotEqual(app.metric[0].value, "—")

    def test_manual_price_changes_budget_without_changing_snapshot(self):
        before = (ROOT / "data/processed/prices.csv").read_bytes()
        app = self.open_app()
        app.sidebar.radio(key="page").set_value("Simulator anggaran").run()
        app.multiselect(key="basket_commodities").set_value(["Beras Medium"]).run()
        app.checkbox(key="manual_prices").check().run()
        app.session_state["basket_editor"] = {"edited_rows": {0: {"Harga input pengguna (Rp)": 20000}}, "added_rows": [], "deleted_rows": []}
        app.run()
        self.assert_no_errors(app)
        self.assertEqual(app.metric[0].value, "Rp 500.000")
        self.assertEqual(app.metric[1].value, "Rp 550.000")
        self.assertEqual((ROOT / "data/processed/prices.csv").read_bytes(), before)

    def test_complete_basket_month_button_recovers_missing_prices(self):
        app = self.open_app()
        app.sidebar.selectbox(key="as_of").set_value(pd.Timestamp("2021-01-01")).run()
        app.sidebar.radio(key="page").set_value("Simulator anggaran").run()
        app.button(key="complete_basket_month").click().run()
        self.assert_no_errors(app)
        self.assertNotEqual(app.metric[0].value, "—")
        self.assertEqual(len(app.warning), 0)

    def test_excel_download_generated_in_data_page(self):
        app = self.open_app()
        app.sidebar.radio(key="page").set_value("Data & metode").run()
        app.button(key="prepare_excel").click().run()
        self.assert_no_errors(app)
        signature, content = app.session_state["excel_report"]
        self.assertTrue(content.startswith(b"PK"))
        self.assertGreater(len(content), 1000)


if __name__ == "__main__":
    unittest.main()
