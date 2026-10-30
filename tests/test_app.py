"""Navigation, calendar comparisons, empty states, and report exports."""
from pathlib import Path
from io import BytesIO
import unittest
import pandas as pd
from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
TITLE='Analisis Tren dan Perbandingan Harga Pangan Antarprovinsi'
PAGES=['Ringkasan','Tren & fluktuasi','Perbandingan provinsi']

class DashboardTests(unittest.TestCase):
    def open_app(self):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=45).run()
        self.good(app)
        return app

    def good(self,app):
        self.assertEqual([e.message for e in app.exception],[])

    def menu(self,app,name):
        app.radio(key='page').set_value(name).run();self.good(app)

    def test_three_analysis_pages_render_and_have_sources(self):
        app=self.open_app()
        self.assertEqual(app.radio(key='page').options,PAGES)
        for page in PAGES:
            self.menu(app,page)
            self.assertEqual(len(app.metric),3)
            self.assertTrue(any(e.label=='Sumber & cara menghitung' for e in app.expander))
            text=' '.join(m.value for m in app.markdown)
            self.assertNotIn('Keranjang',text)
            self.assertFalse(app.get('data_editor'))

    def test_default_findings_match_observed_prices(self):
        app=self.open_app()
        self.assertEqual(app.title[0].value,TITLE)
        self.assertEqual([m.value for m in app.metric],['25 / 25','2','+11,16%'])
        self.assertIn('Cabai Merah Keriting',app.metric[2].label)
        self.assertTrue(any('Daging Kerbau Segar (Lokal)' in c.value and 'tidak tersedia' in c.value for c in app.caption))
        self.assertFalse(any(s.key=='filter_threshold' for s in app.slider))
        self.assertTrue(any('4 dari 12 pasangan bulan' in m.value for m in app.markdown))
        self.assertTrue(any('Studi historis Januari 2021–Oktober 2025' in c.value for c in app.caption))

    def test_first_month_has_unknown_changes(self):
        app=self.open_app()
        app.selectbox(key='filter_as_of').set_value(pd.Timestamp('2021-01-01')).run();self.good(app)
        self.assertEqual(app.metric[1].value,'—')
        self.assertEqual(app.metric[2].value,'—')
        self.assertEqual(len(app.get('plotly_chart')),0)

    def test_missing_region_does_not_reuse_old_prices(self):
        app=self.open_app()
        app.selectbox(key='filter_province').set_value('Papua Pegunungan').run();self.good(app)
        self.assertEqual(app.metric[0].value,'0 / 25')
        self.assertEqual(app.metric[1].value,'—')

    def test_filters_follow_navigation_without_threshold_control(self):
        app=self.open_app()
        app.selectbox(key='filter_commodity').set_value('Cabai Rawit Merah').run()
        app.selectbox(key='filter_window').set_value(36).run()
        self.menu(app,'Perbandingan provinsi')
        self.assertFalse(any(s.key=='filter_window' for s in app.selectbox))
        self.menu(app,'Ringkasan')
        self.assertEqual(app.selectbox(key='filter_commodity').value,'Cabai Rawit Merah')
        self.assertEqual(app.selectbox(key='filter_window').value,36)
        self.assertFalse(any(s.key=='filter_threshold' for s in app.slider))
        self.assertNotIn('threshold', app.session_state['filters'])
        self.assertEqual(app.metric[1].value,'2')

    def test_selected_trend_changes_and_insufficient_history_is_explained(self):
        app=self.open_app();self.menu(app,'Tren & fluktuasi')
        before=app.get('plotly_chart')[0].proto.spec
        app.selectbox(key='filter_commodity').set_value('Cabai Rawit Merah').run();self.good(app)
        self.assertNotEqual(before,app.get('plotly_chart')[0].proto.spec)
        app.select_slider(key='filter_coverage').set_value(100).run();self.good(app)
        self.assertEqual(app.metric[1].value,'100%')
        app.selectbox(key='filter_as_of').set_value(pd.Timestamp('2021-01-01')).run();self.good(app)
        self.assertEqual(app.metric[0].value,'0')
        self.assertTrue(any('Minimal dua bulan' in i.value for i in app.info))

    def test_regions_toggle_changes_displayed_series(self):
        app=self.open_app();self.menu(app,'Perbandingan provinsi')
        before=app.get('plotly_chart')[0].proto.spec
        app.toggle(key='filter_all_regions').set_value(True).run();self.good(app)
        self.assertNotEqual(before,app.get('plotly_chart')[0].proto.spec)
        columns=[str(c) for df in app.dataframe for c in df.value.columns]
        self.assertNotIn('Satuan asumsi',columns)
        self.assertNotIn('unit',columns)

    def test_report_has_analysis_without_budget_or_assumed_units(self):
        app=self.open_app()
        app.button(key='prepare_excel').click().run();self.good(app)
        book=load_workbook(BytesIO(app.session_state['excel_report'][1]))
        self.assertIn('Bulan pembanding',book.sheetnames)
        self.assertNotIn('Sensitivitas latihan',book.sheetnames)
        self.assertNotIn('Simulasi Anggaran',book.sheetnames)
        self.assertNotIn('Satuan asumsi',[c.value for c in book['Harga Bersih'][1]])
        summary={r[0]:r[1] for r in book['Ringkasan'].iter_rows(min_row=2,values_only=True)}
        self.assertEqual(summary['Judul'],TITLE)
        self.assertFalse(any('keranjang' in str(k).lower() for k in summary))

    def test_old_simulator_session_returns_to_summary(self):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=45)
        app.session_state['page']='Simulator anggaran'
        app.session_state['filters']={'threshold':40}
        app.session_state['filter_threshold']=40
        app.run();self.good(app)
        self.assertEqual(app.radio(key='page').value,'Ringkasan')
        self.assertEqual(app.metric[1].value,'2')
        self.assertNotIn('threshold', app.session_state['filters'])

if __name__=='__main__':unittest.main()
