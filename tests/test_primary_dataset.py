"""Verify the actual received exports, active input, row lineage, and independent findings."""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import unittest
import tempfile
import shutil
from unittest.mock import patch
import pandas as pd

from analyst.pipeline import read_raw,normalize_text,prepare_data
from analyst.analytics import monthly_findings,comparison_frame

ROOT=Path(__file__).resolve().parents[1]


class PrimaryDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=json.loads((ROOT/'data/raw/primary/receipt.json').read_text())
        cls.raw=read_raw(ROOT/'data/raw/primary/harga_pangan.csv')

    def test_two_received_formats_match_and_original_bytes_are_preserved(self):
        files=self.receipt['files']
        for f in files:
            path=ROOT/f['path']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),f['sha256'])
            self.assertEqual(path.stat().st_size,f['bytes'])
        other=pd.read_excel(ROOT/'data/raw/primary/harga_pangan.xlsx',dtype=str)
        pd.testing.assert_frame_equal(self.raw.fillna('').map(normalize_text),other.fillna('').map(normalize_text))
        self.assertEqual(len(self.raw),33422)
        self.assertNotIn('Satuan',self.raw.columns)

    def test_active_input_is_primary_export_and_origin_claim_is_precise(self):
        config=json.loads((ROOT/'data/source_input.json').read_text())
        source=json.loads((ROOT/'data/source.json').read_text())
        self.assertEqual(config['dataset_kind'],'primary_export_user_supplied')
        self.assertEqual(config['raw_path'],'data/raw/primary/harga_pangan.csv')
        self.assertEqual(source['raw_sha256'],self.receipt['files'][0]['sha256'])
        self.assertFalse(source['original_independently_verified'])
        self.assertTrue(source['csv_xlsx_consistency_verified'])
        self.assertNotIn('mirror_url',source)
        self.assertTrue((ROOT/'data/archive/mirror-20261028/harga_pangan.csv').exists())

    def test_quarantine_points_to_real_rows_of_header_first_export(self):
        rejected=pd.read_csv(ROOT/'data/processed/rejected.csv',dtype=str)
        self.assertEqual(self.raw.attrs['source_row_start'],2)
        for row in rejected.head(20).itertuples(index=False,name=None):
            source_row=int(row[0]); original=self.raw.iloc[source_row-2]
            self.assertEqual(str(original['Kode Provinsi']),row[1])
            self.assertEqual(str(original['Komoditas']),row[3])

    def test_primary_mode_cannot_silently_download_the_old_mirror(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('Network must not be used')):
            with self.assertRaisesRegex(ValueError,'mirror'):
                prepare_data(ROOT,download=True)

    def test_rebuild_checks_companion_checksum_before_writing_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            shutil.copytree(ROOT/'data/raw/primary',root/'data/raw/primary')
            shutil.copy2(ROOT/'data/source_input.json',root/'data/source_input.json')
            (root/'data/raw/primary/harga_pangan.xlsx').write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'pembanding'):
                prepare_data(root)
            self.assertFalse((root/'data/processed/prices.csv').exists())

    def test_monthly_findings_match_independent_decimal_calculation(self):
        raw=self.raw.copy()
        selected=raw[(raw['Kode Provinsi']=='32')&(raw['Tahun']=='2025')&raw['Bulan'].isin(['September','Oktober'])]
        observed={}
        for _,r in selected.iterrows():
            if pd.isna(r['Harga']):continue
            value=str(r['Harga']).replace('Rp','').replace(',','').strip()
            if not value:continue
            observed[(r['Komoditas'].strip(),r['Bulan'])]=Decimal(value)
        growth={name:(value/observed[(name,'September')]-1)*100 for (name,month),value in observed.items() if month=='Oktober' and (name,'September') in observed and observed[(name,'September')]>0}
        self.assertEqual(len(growth),24)
        self.assertEqual(sum(v>=10 for v in growth.values()),2)
        self.assertEqual(max(growth,key=growth.get),'Cabai Merah Keriting')
        self.assertEqual(round(growth['Cabai Merah Keriting'],2),Decimal('11.16'))
        data=pd.read_csv(ROOT/'data/processed/prices.csv',parse_dates=['date'],dtype={'province_code':str})
        result=monthly_findings(comparison_frame(data),'Jawa Barat','2025-10-01')
        self.assertEqual(result['alert_count'],2)
        first=monthly_findings(comparison_frame(data),'Jawa Barat','2021-01-01')
        self.assertIsNone(first['alert_count'])
