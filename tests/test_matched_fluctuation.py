"""Comparisons must share dates; missing months must not become fabricated returns."""
import unittest
import pandas as pd
from analyst.analytics import matched_fluctuation, comparison_frame


class MatchedFluctuationTests(unittest.TestCase):
    def frame(self):
        rows=[]
        for name,dates in [('A',[1,2,3,4,5]),('B',[1,3,4,5])]:
            for month in dates:
                rows.append({'province':'X','commodity':name,'date':pd.Timestamp(2025,month,1),'price':100+month*10,'unit':'kg'})
        return pd.DataFrame(rows)

    def test_ranked_series_use_identical_observation_months(self):
        r=matched_fluctuation(self.frame(),'2025-01','2025-05',80)
        self.assertEqual(len(r['common_months']),4)
        self.assertTrue((r['summary'].common_observations==4).all())
        self.assertEqual(len(r['monthly_months']),2)
        self.assertTrue((r['summary'].monthly_pairs==2).all())
        self.assertEqual(r['monthly_months'],[pd.Timestamp('2025-04-01'),pd.Timestamp('2025-05-01')])

    def test_screening_does_not_turn_insufficient_overlap_into_a_ranking(self):
        frame=self.frame();frame=frame[~((frame.commodity=='B')&(frame.date>pd.Timestamp('2025-03-01')))]
        r=matched_fluctuation(frame,'2025-01','2025-05',0)
        self.assertEqual(r['eligible_count'],1)
        self.assertEqual(r['summary'].commodity.tolist(),['A'])

    def test_precomputed_changes_do_not_break_aligned_comparison(self):
        r=matched_fluctuation(comparison_frame(self.frame()),'2025-01','2025-05',80)
        self.assertEqual(len(r['summary']),2)
        self.assertEqual(len(r['monthly_months']),2)

    def test_multiple_regions_require_separate_comparison(self):
        frame=self.frame();frame.loc[0,'province']='Y'
        with self.assertRaises(ValueError):matched_fluctuation(frame,'2025-01','2025-05')
