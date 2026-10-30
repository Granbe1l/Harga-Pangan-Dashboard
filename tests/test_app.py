"""Exercise the complete recruiter journey, editable scenarios, and empty states."""
from pathlib import Path
import unittest
import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
TITLE='Analisis Harga Pangan dan Simulasi Anggaran Bahan Baku UMKM Kuliner'
PAGES=['Ringkasan','Simulator anggaran','Fluktuasi historis','Perbandingan wilayah','Data & metode']


class DashboardTests(unittest.TestCase):
    def open_app(self):
        return AppTest.from_file(str(ROOT/'app.py'),default_timeout=45).run()

    def good(self,app):
        self.assertEqual([e.message for e in app.exception],[])

    def menu(self,app,name):
        app.radio(key='page').set_value(name).run(); self.good(app)

    def edit(self,app,patch):
        key='budget_editor_'+str(app.session_state['editor_version'])
        app.session_state[key]={'edited_rows':{0:patch},'added_rows':[],'deleted_rows':[]}
        app.run(); self.good(app)

    def test_all_pages_render_with_real_data(self):
        app=self.open_app()
        for name in PAGES:
            self.menu(app,name)
            self.assertGreaterEqual(len(app.metric),3)

    def test_opening_metrics_follow_one_historical_budget_story(self):
        app=self.open_app();self.good(app)
        self.assertEqual(app.title[0].value,TITLE)
        self.assertEqual([m.value for m in app.metric[:3]],['Rp 1.118.460','Rp 10.687','6 / 6 bahan'])
        self.assertEqual(app.metric[1].label,'Perubahan biaya vs bulan lalu')
        self.assertNotIn('Jika seluruh', ' '.join(m.value for m in app.markdown))

    def test_first_month_has_unknown_change_and_no_single_point_trend(self):
        app=self.open_app()
        app.selectbox(key='filter_as_of').set_value(pd.Timestamp('2021-01-01')).run()
        self.good(app)
        self.assertEqual(app.metric[0].value,'—')
        self.assertEqual(app.metric[1].value,'—')
        self.assertEqual(len(app.get('plotly_chart')),0)

    def test_missing_region_does_not_reuse_old_price(self):
        app=self.open_app()
        app.selectbox(key='filter_province').set_value('Papua Pegunungan').run()
        self.good(app)
        self.assertEqual(app.metric[0].value,'—')
        self.assertEqual(app.metric[2].value,'0 / 6 bahan')

    def test_detail_commodity_and_threshold_update_without_changing_historical_budget(self):
        app=self.open_app()
        baseline=[m.value for m in app.metric[:3]]
        app.selectbox(key='filter_commodity').set_value('Cabai Rawit Merah').run();self.good(app)
        self.assertTrue(any(h.value=='Harga Cabai Rawit Merah' for h in app.subheader))
        text=' '.join(m.value for m in app.markdown)
        self.assertIn('2 dari 24 komoditas',text)
        app.slider(key='filter_threshold').set_value(40).run();self.good(app)
        self.assertIn('Tidak ada komoditas', ' '.join(m.value for m in app.markdown))
        self.assertEqual([m.value for m in app.metric[:3]],baseline)

    def test_filters_are_contextual_and_preserved_when_hidden(self):
        app=self.open_app()
        app.selectbox(key='filter_commodity').set_value('Cabai Rawit Merah').run()
        app.selectbox(key='filter_window').set_value(36).run()
        self.menu(app,'Simulator anggaran')
        self.assertFalse(any(s.key in ['filter_commodity','filter_window'] for s in app.selectbox))
        self.menu(app,'Ringkasan')
        self.assertEqual(app.selectbox(key='filter_commodity').value,'Cabai Rawit Merah')
        self.assertEqual(app.selectbox(key='filter_window').value,36)

    def test_cta_navigates_to_simulator(self):
        app=self.open_app()
        next(b for b in app.button if b.label=='Coba simulasi belanja →').click().run()
        self.good(app)
        self.assertEqual(app.radio(key='page').value,'Simulator anggaran')

    def test_quick_scenarios_and_reset(self):
        app=self.open_app();self.menu(app,'Simulator anggaran')
        app.button(key='quick_0').click().run();self.good(app)
        self.assertEqual(app.metric[0].value,app.metric[1].value)
        app.button(key='quick_20').click().run();self.good(app)
        self.assertEqual(app.metric[1].value,'Rp 1.342.152')
        app.button(key='reset_budget').click().run();self.good(app)
        self.assertEqual(app.metric[1].value,'Rp 1.230.306')

    def test_bulk_control_only_applies_after_button_and_preserves_quantity(self):
        app=self.open_app();self.menu(app,'Simulator anggaran')
        self.edit(app,{'Jumlah':30.5})
        before=app.metric[1].value
        app.number_input(key='bulk_shock').set_value(30).run()
        self.assertEqual(app.metric[1].value,before)
        next(b for b in app.button if b.label=='Terapkan ke semua bahan').click().run()
        self.good(app)
        self.assertEqual(app.session_state['plan']['Beras Medium']['quantity'],30.5)
        self.assertEqual(app.session_state['plan']['Beras Medium']['shock_pct'],30)

    def test_budget_edits_and_period_survive_page_navigation(self):
        app=self.open_app();self.menu(app,'Simulator anggaran')
        self.edit(app,{'Jumlah':30.5,'Perubahan (%)':25})
        app.selectbox(key='budget_period').set_value('Per minggu').run()
        before=app.metric[1].value
        self.menu(app,'Ringkasan');self.menu(app,'Simulator anggaran')
        self.assertEqual(app.metric[1].value,before)
        self.assertEqual(app.selectbox(key='budget_period').value,'Per minggu')

    def test_empty_and_zero_quantity_baskets(self):
        app=self.open_app();self.menu(app,'Simulator anggaran')
        app.multiselect(key='basket_commodities').set_value([]).run();self.good(app)
        self.assertTrue(any('Pilih minimal satu' in i.value for i in app.info))
        app.multiselect(key='basket_commodities').set_value(['Beras Medium']).run()
        self.edit(app,{'Jumlah':0})
        self.assertEqual(app.metric[0].value,'—')
        self.assertTrue(any('Isi jumlah' in i.value for i in app.info))

    def test_manual_price_preserves_dataset_and_only_changes_edited_row_source(self):
        before=(ROOT/'data/processed/prices.csv').read_bytes()
        app=self.open_app();self.menu(app,'Simulator anggaran')
        app.checkbox(key='manual_prices').check().run()
        self.edit(app,{'Harga acuan (Rp)':20000})
        self.assertEqual(app.session_state['plan']['Beras Medium']['override'],20000)
        self.assertNotIn('override',app.session_state['plan']['Daging Ayam Ras'])
        self.menu(app,'Ringkasan');self.menu(app,'Simulator anggaran')
        self.assertTrue(app.checkbox(key='manual_prices').value)
        self.assertEqual((ROOT/'data/processed/prices.csv').read_bytes(),before)

    def test_missing_month_has_subtotal_and_recovery_button(self):
        app=self.open_app()
        app.selectbox(key='filter_as_of').set_value(pd.Timestamp('2021-01-01')).run()
        self.menu(app,'Simulator anggaran')
        self.assertEqual(app.metric[0].value,'—')
        self.assertTrue(any('Subtotal bahan tersedia' in c.value for c in app.caption))
        app.button(key='complete_basket_month').click().run();self.good(app)
        self.assertNotEqual(app.metric[0].value,'—')
        self.assertFalse(any('Total belum lengkap' in w.value for w in app.warning))

    def test_risk_first_month_and_minimum_coverage(self):
        app=self.open_app();self.menu(app,'Fluktuasi historis')
        app.select_slider(key='filter_coverage').set_value(100).run();self.good(app)
        self.assertEqual(app.metric[1].value,'100%')
        self.menu(app,'Ringkasan');self.menu(app,'Fluktuasi historis')
        self.assertEqual(app.select_slider(key='filter_coverage').value,100)
        app.selectbox(key='filter_as_of').set_value(pd.Timestamp('2021-01-01')).run();self.good(app)
        self.assertEqual(app.metric[0].value,'0')
        self.assertTrue(any('Riwayat belum cukup' in i.value for i in app.info))

    def test_regions_toggle_changes_chart_row_count(self):
        app=self.open_app();self.menu(app,'Perbandingan wilayah')
        first=app.get('plotly_chart')[0].proto.spec
        app.toggle(key='filter_all_regions').set_value(True).run();self.good(app)
        self.assertNotEqual(first,app.get('plotly_chart')[0].proto.spec)

    def test_data_page_distinguishes_recorded_date_and_last_price_and_exports_excel(self):
        app=self.open_app();self.menu(app,'Data & metode')
        text=' '.join(m.value for m in app.markdown)
        self.assertIn('Snapshot dicatat',text)
        self.assertIn('28/10/2026',text)
        app.button(key='prepare_excel').click().run();self.good(app)
        self.assertTrue(app.session_state['excel_report'][1].startswith(b'PK'))


if __name__=='__main__':unittest.main()
