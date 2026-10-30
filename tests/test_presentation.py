import unittest
import pandas as pd
from analyst.presentation import display_table, rupiah, percent


class PresentationTests(unittest.TestCase):
    def test_missing_and_zero_are_distinct(self):
        self.assertEqual(rupiah(None),'—')
        self.assertEqual(rupiah(0),'Rp 0')
        self.assertEqual(percent(None),'—')
        self.assertEqual(percent(0),'+0,0%')

    def test_money_quantity_and_percent_have_consistent_indonesian_formats(self):
        original=pd.DataFrame({'Biaya (Rp)':[13228.,None],'Jumlah':[30.5,0],'Cakupan (%)':[83.333,None]})
        displayed=display_table(original)
        self.assertEqual(displayed['Biaya (Rp)'].tolist(),['Rp 13.228','—'])
        self.assertEqual(displayed['Jumlah'].tolist(),['30,50','0,00'])
        self.assertEqual(displayed['Cakupan (%)'].tolist(),['83,3%','—'])
        self.assertEqual(original['Biaya (Rp)'].iloc[0],13228.)
