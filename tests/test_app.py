"""Exercise the research report, interactive appendices, and report generation."""

from pathlib import Path
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = [
    "Ringkasan penelitian",
    "Data & metode",
    "Volatilitas harga",
    "Perbandingan wilayah",
    "Analisis skenario",
    "Kesimpulan",
]


class ResearchReportTests(unittest.TestCase):
    def open_app(self):
        return AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()

    def assert_no_errors(self, app):
        self.assertEqual([e.message for e in app.exception], [])

    def indicator_value(self, app, row):
        """Read the displayed evidence table, rather than a metric-card widget."""
        table = app.dataframe[0].value
        self.assertEqual(list(table.columns), ["Indikator", "Nilai"])
        return table.iloc[row]["Nilai"]

    def test_navigation_renders_all_six_sections(self):
        app = self.open_app()
        for page in SECTIONS:
            app.sidebar.radio(key="page").set_value(page).run()
            self.assert_no_errors(app)
            self.assertTrue(len(app.header) >= 1, page)

    def test_opening_report_uses_narrative_and_an_evidence_table(self):
        app = self.open_app()
        self.assert_no_errors(app)
        self.assertEqual(
            app.title[0].value,
            "Analisis Harga Pangan Indonesia & Simulasi Anggaran UMKM (Python & Streamlit)",
        )
        self.assertEqual(len(app.metric), 0)
        self.assertTrue(self.indicator_value(app, 0).startswith("Rp "))
        self.assertNotEqual(self.indicator_value(app, 1), "—")

    def test_budget_zero_shock_matches_baseline_and_change_updates_it(self):
        app = self.open_app()
        app.sidebar.radio(key="page").set_value("Analisis skenario").run()
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
        app.sidebar.radio(key="page").set_value("Analisis skenario").run()
        app.multiselect(key="basket_commodities").set_value([]).run()
        self.assert_no_errors(app)
        self.assertTrue(any("Pilih minimal satu" in i.value for i in app.info))

    def test_missing_month_does_not_show_stale_price_or_complete_budget(self):
        app = self.open_app()
        app.sidebar.selectbox(key="province").set_value("Papua Pegunungan").run()
        app.sidebar.selectbox(key="as_of").set_value(pd.Timestamp("2025-10-01")).run()
        self.assert_no_errors(app)
        self.assertEqual(self.indicator_value(app, 0), "—")
        app.sidebar.radio(key="page").set_value("Analisis skenario").run()
        self.assert_no_errors(app)
        self.assertEqual(app.metric[0].value, "—")
        self.assertTrue(any("Total belum lengkap" in i.value for i in app.warning))

    def test_first_month_has_no_false_growth(self):
        app = self.open_app()
        app.sidebar.selectbox(key="as_of").set_value(pd.Timestamp("2021-01-01")).run()
        self.assert_no_errors(app)
        self.assertEqual(self.indicator_value(app, 1), "—")
        self.assertEqual(self.indicator_value(app, 2), "—")

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
