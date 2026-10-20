from types import SimpleNamespace
from unittest.mock import patch
import unittest
import pandas as pd
from beams_ec2.release import _prepare_input_frames,BeamDesigner
from beams_ec2 import advanced

class V:
    def __init__(self,x):self.x=x
    def get(self):return self.x


def fixture():
    rows=[]
    for case,factor in [(101,1),(201,2),(302,.6),(303,1.5),(304,.8)]:
        for i,x in enumerate([0,1.5,3,4.5,6]):
            rows.append({'Member/Node/Case':f'1/{i+1}/{case} (C)'+(' (CQC)' if case==201 else ''),
                'Station (m)':x,'Length (m)':6,'HY (cm)':30,'HZ (cm)':60,'Material':'C30/37',
                'MY (kNm)':factor*40*(1-((x-3)/3)**2),'FZ (kN)':factor*(20-x*40/6),'MX (kNm)':0})
    clean,env=_prepare_input_frames(pd.DataFrame(rows))
    app=SimpleNamespace(df_clean=clean,var_elu_cases=V('101 201'),var_sls_qp_cases=V('302'),
        var_sls_char_cases=V('304'),var_sls_freq_cases=V('303'),var_service_case=V(''),
        var_moment_axis=V('MY'),var_ld_limit=V(250),var_crack_limit=V(.3),
        var_cover=V(35),var_fyk=V(500),var_calc_mode=V('dimensionamento'))
    return app,BeamDesigner().design_dataframe(env[env['case']=='101 (C)'])


class ReuseTests(unittest.TestCase):
    def test_duplicate_cage_reuses_results_but_changed_cover_recalculates(self):
        app,row=fixture();r=pd.concat([row,row],ignore_index=True)
        method=advanced._calculate_member_sls_advanced
        with patch.object(advanced,'_calculate_member_sls_advanced',wraps=method) as calculate:
            together=advanced._apply_serviceability_advanced(app,r)
            self.assertEqual(calculate.call_count,3)
            self.assertEqual(len(app.df_sls_combinations),3)
        fields=[c for c in together if c.startswith('service_')]
        pd.testing.assert_series_equal(together.iloc[0][fields],together.iloc[1][fields],check_names=False)
        r.loc[1,'cover_mm']=r.loc[0,'cover_mm']+5
        with patch.object(advanced,'_calculate_member_sls_advanced',wraps=method) as calculate:
            advanced._apply_serviceability_advanced(app,r)
            self.assertEqual(calculate.call_count,6)
            self.assertEqual(app.df_sls_combinations.service_cage_id.nunique(),2)

    def test_cache_does_not_survive_input_changes_between_runs(self):
        app,row=fixture();method=advanced._calculate_member_sls_advanced
        with patch.object(advanced,'_calculate_member_sls_advanced',wraps=method) as calculate:
            before=advanced._apply_serviceability_advanced(app,row)
            app.df_clean.loc[app.df_clean['case']=='304 (C)','my'] *= 2
            after=advanced._apply_serviceability_advanced(app,row)
            self.assertEqual(calculate.call_count,6)
            self.assertGreater(after.service_sigma_s_MPa.iloc[0],before.service_sigma_s_MPa.iloc[0])

    def test_detailing_excludes_els_and_includes_explicit_cqc_elu(self):
        app,row=fixture()
        detail,profile=advanced._longitudinal_detailing_advanced(app,row)
        app.df_clean.loc[app.df_clean['case']=='303 (C)','my']=100000
        repeated=pd.concat([row,row],ignore_index=True)
        detail2,profile2=advanced._longitudinal_detailing_advanced(app,repeated)
        pd.testing.assert_frame_equal(detail,detail2)
        pd.testing.assert_frame_equal(profile,profile2)
        self.assertEqual(len(profile),101)
        app.df_clean.loc[app.df_clean['case'].str.contains('CQC'),'my']=20000
        _,changed=advanced._longitudinal_detailing_advanced(app,row)
        self.assertGreater(changed.Mpos_env_kNm.max(),profile.Mpos_env_kNm.max())

    def test_unpositioned_nodes_have_anchorage_notes_without_cutoff_profile(self):
        app,row=fixture();app.df_clean['station']=float('nan')
        detail,profile=advanced._longitudinal_detailing_advanced(app,row)
        self.assertFalse(detail.empty)
        self.assertTrue(profile.empty)
        self.assertEqual(detail.profile_status.iloc[0],'Dados insuficientes')

    def test_distinct_shear_angles_keep_distinct_detailing(self):
        app,row=fixture();r=pd.concat([row,row],ignore_index=True)
        r.loc[0,'cot_theta_shear']=1;r.loc[1,'cot_theta_shear']=2
        detail,_=advanced._longitudinal_detailing_advanced(app,r)
        self.assertEqual(len(detail),2)
        self.assertAlmostEqual(detail.shift_al_mm.iloc[1],2*detail.shift_al_mm.iloc[0])
