import math
import unittest
import pandas as pd
from tools.preview_reports import harness
from beams_ec2 import advanced
from beams_ec2.release import _prepare_input_frames
from tests.test_robustness import sample

class OptionalDiagramTests(unittest.TestCase):
    def test_unpositioned_labels_accepted(self):
        f=sample().drop(columns='Station (m)')
        f['Member/Node/Case']='1/Point A/101 (C)'
        clean, env=_prepare_input_frames(f)
        self.assertTrue(clean.station.isna().all())
        self.assertEqual(len(env),1)

    def test_section_checks_survive_missing_or_conflicting_positions(self):
        app=harness()
        r=app.df_results.iloc[0]
        group=app.df_clean[(app.df_clean.member=='1') & (app.df_clean['case']=='201 ELS QP')].copy()
        params=advanced.SLSParametersAdvanced()
        baseline,_=advanced._calculate_member_sls_advanced(app,r,group,'201','test',params)
        for x in (float('nan'), 0):
            with self.subTest(x=x):
                sparse=group.assign(station=x)
                result,points=advanced._calculate_member_sls_advanced(app,r,sparse,'201','test',params)
                for key in ('service_wk_est_mm','service_sigma_s_MPa','service_sigma_c_MPa'):
                    self.assertAlmostEqual(result[key],baseline[key],places=8)
                self.assertTrue(math.isnan(result['service_deflection_est_mm']))
                self.assertEqual(result['service_deflection_status'],'Dados insuficientes')
                self.assertTrue(all(math.isnan(p['x_m']) for p in points))

    def test_no_fictitious_cutoffs_without_positions(self):
        app=harness()
        app.df_clean['station']=float('nan')
        detail,profile=advanced._longitudinal_detailing_advanced(app,app.df_results)
        self.assertFalse(detail.empty)
        self.assertTrue(profile.empty)
        self.assertTrue(detail.detailing_basis.str.contains('sem perfil').all())

    def test_sparse_policy_keeps_characteristic_stresses_and_qp_incomplete(self):
        from beams_ec2.combinations import apply_check_policy
        source=dict(service_status="Dados insuficientes", service_crack_status="OK",
                    service_stress_status="OK", service_concrete_status="OK",
                    service_deflection_status="Dados insuficientes")
        self.assertEqual(apply_check_policy(source,"ELS_CAR")["service_status"],"OK")
        self.assertEqual(apply_check_policy(source,"ELS_QP")["service_status"],"Dados insuficientes")

    def test_two_positions_do_not_validate_deflection_or_axial_checks(self):
        from beams_ec2.combinations import apply_check_policy
        app=harness();r=app.df_results.iloc[0]
        g=app.df_clean[(app.df_clean.member=='1') & (app.df_clean['case']=='201 ELS QP')].iloc[[0,-1]].copy()
        raw,_=advanced._calculate_member_sls_advanced(app,r,g,'201','test',advanced.SLSParametersAdvanced())
        self.assertEqual(apply_check_policy(raw,'ELS_QP')['service_status'],'Dados insuficientes')
        g=app.df_clean[(app.df_clean.member=='1') & (app.df_clean['case']=='201 ELS QP')].assign(fx=10000)
        raw,_=advanced._calculate_member_sls_advanced(app,r,g,'201','test',advanced.SLSParametersAdvanced())
        self.assertEqual(apply_check_policy(raw,'ELS_CAR')['service_status'],'Dados insuficientes')
