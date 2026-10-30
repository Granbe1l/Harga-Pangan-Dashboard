"""Synthetic adapter fixtures; these tests do not certify any official dataset."""
import json
from pathlib import Path
import tempfile
import unittest
import pandas as pd
from analyst.primary import official_url,normalize_primary,stage_normalized,DownloadLinks


class PrimaryAdapterTests(unittest.TestCase):
    def test_official_origin_check_rejects_lookalikes_and_plain_http(self):
        self.assertTrue(official_url('https://data.badanpangan.go.id/data.csv'))
        for url in ['http://data.badanpangan.go.id/data.csv','https://data.badanpangan.go.id.evil.example/data.csv','https://user:password@data.badanpangan.go.id/data.csv']:
            self.assertFalse(official_url(url))

    def test_missing_units_remain_unknown(self):
        frame=pd.DataFrame({'Wilayah':['Jawa Barat'],'Bahan':['Beras'],'Tanggal':['2025-01-01'],'Nilai':[10000]})
        clean,rejected,report=normalize_primary(frame,{'province':'Wilayah','commodity':'Bahan','date':'Tanggal','price':'Nilai'})
        self.assertEqual(clean.unit.iloc[0],'')
        self.assertEqual(report['units_missing'],1)
        self.assertFalse(report['primary_unit_definitions_verified'])

    def test_explicit_separators_and_conflicts_are_not_averaged(self):
        frame=pd.DataFrame({'p':['X','X','X'],'c':['A','A','B'],'d':['2025-01-01']*3,'v':['10.000,50','11.000,00','5.000,00'],'u':['kg']*3})
        clean,rejected,report=normalize_primary(frame,{'province':'p','commodity':'c','date':'d','price':'v','unit':'u'},decimal=',',thousands='.')
        self.assertEqual(clean.price.tolist(),[5000])
        self.assertEqual(set(rejected.rejection_reason),{'conflicting_duplicate'})
        self.assertEqual(report['rejected_rows'],2)

    def test_native_excel_number_is_not_reparsed_as_formatted_text(self):
        frame=pd.DataFrame({'p':['X'],'c':['A'],'d':['2025-01-01'],'v':[10000.5]})
        clean,_,_=normalize_primary(frame,{'province':'p','commodity':'c','date':'d','price':'v'},decimal=',',thousands='.')
        self.assertEqual(clean.price.iloc[0],10000.5)

    def test_csv_separators_are_applied_once(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'raw.csv';source.write_text('p;c;d;v\nX;A;2025-01-01;10.000,50\n')
            mapping=root/'mapping.json';mapping.write_text(json.dumps({'province':'p','commodity':'c','date':'d','price':'v'}))
            stage_normalized(source,mapping,root/'staged',delimiter=';',decimal=',',thousands='.')
            result=pd.read_csv(root/'staged/prices.csv')
            self.assertEqual(result.price.iloc[0],10000.5)

    def test_mapping_must_match_actual_headers(self):
        with self.assertRaises(ValueError):normalize_primary(pd.DataFrame({'x':[1]}),{'province':'missing'})

    def test_download_link_candidates_stay_on_official_origin(self):
        parser=DownloadLinks('https://data.badanpangan.go.id/catalog')
        parser.feed('<a href="/files/prices.csv">CSV</a><a href="https://elsewhere.example/prices.csv">Mirror</a>')
        self.assertEqual(parser.links,['https://data.badanpangan.go.id/files/prices.csv'])

    def test_local_file_does_not_become_verified_primary_without_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'raw.csv';source.write_text('p,c,d,v\nX,A,2025-01-01,100\n')
            mapping=root/'mapping.json';mapping.write_text(json.dumps({'province':'p','commodity':'c','date':'d','price':'v'}))
            result=stage_normalized(source,mapping,root/'staged')
            self.assertIsNone(result['acquisition_receipt'])
            self.assertIn('belum dibuktikan',result['acquisition_status'])
            with self.assertRaises(ValueError):stage_normalized(source,mapping,root/'staged')

    def test_mismatched_receipt_cannot_certify_a_changed_file(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'raw.csv';source.write_text('p,c,d,v\nX,A,2025-01-01,100\n')
            source.with_suffix('.csv.receipt.json').write_text(json.dumps({'raw_sha256':'wrong'}))
            mapping=root/'mapping.json';mapping.write_text(json.dumps({'province':'p','commodity':'c','date':'d','price':'v'}))
            with self.assertRaises(ValueError):stage_normalized(source,mapping,root/'staged')
