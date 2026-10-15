import unittest
from unittest.mock import patch
import pandas as pd
from tools.preview_reports import harness
from beams_ec2 import advanced


class CalculationReuseTests(unittest.TestCase):
    def test_els_reuses_identical_cage_but_invalidates_cover(self):
        app=harness()
        row=app.df_results.iloc[[0]].copy()
        duplicate=pd.concat([row,row],ignore_index=True)
        original=advanced._calculate_member_sls_advanced
        with patch.object(advanced,'_calculate_member_sls_advanced',wraps=original) as calculate:
            together=advanced._apply_serviceability_advanced(app,duplicate)
            self.assertEqual(calculate.call_count,3)
            self.assertEqual(len(app.df_sls_combinations),3)
        columns=[c for c in together if c.startswith('service_')]
        pd.testing.assert_series_equal(together.iloc[0][columns],together.iloc[1][columns],check_names=False)
        duplicate.loc[1,'cover_mm']=duplicate.loc[0,'cover_mm']+5
        with patch.object(advanced,'_calculate_member_sls_advanced',wraps=original) as calculate:
            advanced._apply_serviceability_advanced(app,duplicate)
            self.assertEqual(calculate.call_count,6)

    def test_detailing_once_and_excludes_els(self):
        app=harness()
        row=app.df_results.iloc[[0]].copy()
        detail,profile=advanced._longitudinal_detailing_advanced(app,row)
        app.df_clean.loc[app.df_clean.combination_group!='ELU','my']=1000000
        repeated=pd.concat([row,row],ignore_index=True)
        detail2,profile2=advanced._longitudinal_detailing_advanced(app,repeated)
        pd.testing.assert_frame_equal(detail,detail2)
        pd.testing.assert_frame_equal(profile,profile2)
        self.assertEqual(len(detail2),1)
        self.assertEqual(len(profile2),101)
