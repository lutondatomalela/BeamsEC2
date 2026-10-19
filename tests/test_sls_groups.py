from dataclasses import replace
from types import SimpleNamespace
import math
import unittest
import pandas as pd
from beams_ec2.sls_groups import resolve, policy, envelope, parameters
from beams_ec2.advanced import SLSParametersAdvanced, _apply_serviceability_advanced, _case_regime_advanced
from beams_ec2.release import _prepare_input_frames, BeamDesigner

class Value:
    def __init__(self,x):self.x=x
    def get(self):return self.x


def response(group,case,value=1.0,**updates):
    d=dict(service_combination=case,service_group=group,service_sigma_s_MPa=value,
           service_sigma_s_lim_MPa=400.0,service_sigma_c_MPa=value,service_sigma_c_lim_MPa=18.0,
           service_wk_est_mm=value/100,service_wk_lim_mm=.3,service_deflection_est_mm=value,
           service_deflection_lim_mm=24.0,service_crack_status='OK',service_deflection_status='OK',
           service_stress_status='OK',service_concrete_status='OK',service_status='OK',
           service_diagram_quality='Adequado')
    d.update(updates)
    return policy(d,group)


class SLSGroupTests(unittest.TestCase):
    def test_explicit_resolve_excludes_unknown_and_allows_cqc_elu(self):
        m=resolve(['201 (C) (CQC)','302 (C)','303 (C)','304 (C)','999 (C)'],
                  {'ELU':'201','ELS_CAR':'304','ELS_FREQ':'303','ELS_QP':'302'})
        self.assertEqual(m['201 (C) (CQC)'],'ELU')
        self.assertEqual(m['999 (C)'],'EXCLUIDA')

    def test_overlap_and_missing_rejected(self):
        with self.assertRaises(ValueError):resolve(['101 (C)'],{'ELU':'101','ELS_CAR':'101'})
        with self.assertRaises(ValueError):resolve(['101 (C)'],{'ELS_QP':'302'})
        self.assertIsNone(resolve(['101 (C)'],{'ELU':'101'}))

    def test_frequent_does_not_govern(self):
        r=envelope([response('ELS_QP','302',2),response('ELS_CAR','304',3),
                    response('ELS_FREQ','303',100000,service_status='Não verifica')])
        self.assertEqual(r['service_status'],'OK')
        self.assertEqual(r['service_combination_crack'],'302')
        self.assertEqual(r['service_combination_steel'],'304')

    def test_missing_regime_is_incomplete(self):
        r=envelope([response('ELS_QP','302',2)])
        self.assertEqual(r['service_status'],'Dados insuficientes')
        self.assertTrue(math.isnan(r['service_sigma_s_MPa']))

    def test_qp_concrete_limit_requests_nonlinear_creep(self):
        r=response('ELS_QP','302',2,service_concrete_status='Não verifica')
        self.assertEqual(r['service_creep_status'],'Requer fluência não linear')
        self.assertEqual(r['service_status'],'Dados insuficientes')
        self.assertEqual(r['service_concrete_status'],'Informativo')

    def test_axial_and_short_diagram_remain_incomplete(self):
        self.assertEqual(response('ELS_CAR','304',service_axial_ratio=.2)['service_status'],'Dados insuficientes')
        self.assertEqual(response('ELS_QP','302',service_diagram_quality='Insuficiente')['service_status'],'Dados insuficientes')
        self.assertEqual(response('ELS_QP','302',service_diagram_source='ordem das linhas distribuída no vão')['service_status'],'Dados insuficientes')

    def test_non_governing_incomplete_case_is_retained(self):
        r=envelope([response('ELS_QP','302',10),response('ELS_CAR','304',3),
                    response('ELS_QP','305',1,service_diagram_quality='Insuficiente')])
        self.assertEqual(r['service_status'],'Dados insuficientes')

    def test_regime_parameters_are_explicit_and_cqc_is_not_qp(self):
        base=SLSParametersAdvanced()
        self.assertFalse(parameters(base,'ELS_CAR').long_term)
        self.assertTrue(parameters(base,'ELS_QP').long_term)
        self.assertFalse(parameters(base,'ELS_QP').auto_regime)
        self.assertEqual(_case_regime_advanced('201 (CQC)','fallback'),'fallback')

    def test_actual_calculation_routes_three_regimes_without_station(self):
        data=[]
        for case,factor in [(101,1),(302,.6),(303,10),(304,.8)]:
            for node,sign in [(15052,1),(15053,-1)]:
                data.append({'Member/Node/Case':f'1/{node}/{case} (C)',
                    'MY (kNm)':factor*40,'FZ (kN)':sign*factor*20,'MX (kNm)':0,
                    'FX (kN)':0,'Length (m)':6,'HY (cm)':30,'HZ (cm)':60,'Material':'C30/37'})
        clean,env=_prepare_input_frames(pd.DataFrame(data))
        app=SimpleNamespace(df_clean=clean,var_elu_cases=Value('101'),var_sls_char_cases=Value('304'),
                var_sls_freq_cases=Value('303'),var_sls_qp_cases=Value('302'),var_service_case=Value(''),
                var_moment_axis=Value('MY'),var_ld_limit=Value(250),var_crack_limit=Value(.3))
        elu=env[env['case']=='101 (C)']
        results=_apply_serviceability_advanced(app,BeamDesigner().design_dataframe(elu))
        self.assertEqual(results.service_combination_crack.iloc[0],'302 (C)')
        self.assertEqual(results.service_combination_steel.iloc[0],'304 (C)')
        self.assertEqual(results.service_status.iloc[0],'Dados insuficientes')
        self.assertEqual(set(app.df_sls_combinations.service_group),{'ELS_CAR','ELS_FREQ','ELS_QP'})
        self.assertTrue(clean.station.isna().all())
        self.assertNotIn('303 (C)',results.service_governing_combination.iloc[0])
