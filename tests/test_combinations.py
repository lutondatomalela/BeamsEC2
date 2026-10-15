import unittest
from types import SimpleNamespace
import pandas as pd
from beams_ec2.combinations import (parse_cases,named_group,classify_combinations,
                                    apply_check_policy,parameters_for_group)
from beams_ec2.release import BeamDesigner,_prepare_input_frames
from beams_ec2.advanced import _apply_serviceability_advanced,SLSParametersAdvanced,_governing_sls_advanced
from beams_ec2.base import classify_limit_state


class Value:
    def __init__(self,v):self.v=v
    def get(self):return self.v


def pipeline(selection=None):
    rows=[]
    for case,m in [(101,100),(201,30),(202,500),(203,20),(204,25),(999,100000)]:
        for i,x in enumerate([0,1.5,3,4.5,6]):
            rows.append({'Member/Node/Case':f'1/{i+1}/{case} (C)',
                         'Station (m)':x,'Length (m)':6,'HY (cm)':30,'HZ (cm)':60,
                         'Material':'C30/37','MY (kNm)':m,'FZ (kN)':40 if case==101 else 0,'MX (kNm)':0})
    clean,env=_prepare_input_frames(pd.DataFrame(rows))
    selection=selection or {'ELU':'101','ELS_CAR':'201','ELS_FREQ':'202','ELS_QP':'203-204'}
    clean=classify_combinations(clean,selection)
    env=classify_combinations(env,selection)
    app=SimpleNamespace(df_clean=clean,var_ld_limit=Value(250),var_crack_limit=Value(.3),
                        var_service_case=Value('999'))  # Legacy selector must not leak.
    results=BeamDesigner().design_dataframe(env[env.combination_group=='ELU'])
    return app,_apply_serviceability_advanced(app,results),env


class SelectionTests(unittest.TestCase):
    def test_ranges_and_lists(self):
        self.assertEqual(parse_cases('101–103 105; 110,112|115'),{101,102,103,105,110,112,115})
        self.assertEqual(parse_cases('101 - 103'),{101,102,103})
        self.assertEqual(parse_cases('101‑103'),{101,102,103})

    def test_invalid_ranges(self):
        for value in ['110-101','abc','1-9999999','0','101/102']:
            with self.subTest(value=value),self.assertRaises(ValueError):parse_cases(value)

    def test_overlap_rejected(self):
        with self.assertRaises(ValueError):
            classify_combinations(pd.DataFrame({'case':['101 (C)']}),{'ELU':'101','ELS_QP':'101'})

    def test_missing_number_rejected(self):
        with self.assertRaises(ValueError):
            classify_combinations(pd.DataFrame({'case':['101 (C)']}),{'ELU':'102'})

    def test_exact_identifiers_no_substring(self):
        out=classify_combinations(pd.DataFrame({'case':['20 (C)','220 (C)']}),{'ELU':'220'})
        self.assertEqual(list(out.combination_group),['NAO_CLASSIFICADA','ELU'])

    def test_combination_marker_is_not_uls(self):
        self.assertEqual(classify_limit_state('101 (C)'),'Não classificada')
        self.assertEqual(named_group('201 ELS'),'NAO_CLASSIFICADA')

    def test_explicit_names_and_conflicts(self):
        for case,group in [('101 ELU','ELU'),('201 ELS CARACT.','ELS_CAR'),
                           ('202 ELS frequente','ELS_FREQ'),('203 ELS QP','ELS_QP'),('203_ELS_QP','ELS_QP'),
                           ('204 ULS QP','NAO_CLASSIFICADA')]:
            with self.subTest(case=case):self.assertEqual(named_group(case),group)

    def test_manual_selection_excludes_unlisted_named_cases(self):
        out=classify_combinations(pd.DataFrame({'case':['101 ELU','202 ELS QP']}),{'ELU':'101'})
        self.assertEqual(out.iloc[1].combination_group,'NAO_CLASSIFICADA')

    def test_import_can_preserve_stale_selection_for_later_edit(self):
        out=classify_combinations(pd.DataFrame({'case':['101 (C)']}),{'ELU':'500'},validate_missing=False)
        self.assertEqual(out.iloc[0].combination_group,'NAO_CLASSIFICADA')


class RegimePolicyTests(unittest.TestCase):
    def test_parameters_follow_group_instead_of_legacy_default(self):
        base=SLSParametersAdvanced(regime='Característica / curta duração',auto_regime=False)
        qp=parameters_for_group(base,'ELS_QP')
        self.assertTrue(qp.long_term)
        self.assertFalse(parameters_for_group(qp,'ELS_CAR').long_term)

    def test_frequent_failures_are_informative(self):
        raw={k:'Não verifica' for k in ['service_crack_status','service_deflection_status',
                                       'service_stress_status','service_concrete_status']}
        raw['service_status']='Não verifica'
        got=apply_check_policy(raw,'ELS_FREQ')
        self.assertEqual(got['service_status'],'Informativo')
        self.assertEqual(got['service_crack_status'],'Informativo')

    def test_qp_requires_nonlinear_creep_is_review_not_strength_failure(self):
        raw={'service_status':'Não verifica','service_crack_status':'OK','service_deflection_status':'OK',
             'service_stress_status':'OK','service_concrete_status':'Não verifica'}
        got=apply_check_policy(raw,'ELS_QP')
        self.assertEqual(got['service_status'],'Dados insuficientes')
        self.assertEqual(got['service_creep_status'],'Requer fluência não linear')


class PipelineTests(unittest.TestCase):
    def test_distinct_groups_and_no_uls_leak(self):
        app,results,env=pipeline()
        self.assertEqual(list(results.case),['101 (C)'])
        self.assertEqual(results.iloc[0].service_combinations_checked,4)
        self.assertEqual(set(app.df_sls_combinations.service_group),{'ELS_CAR','ELS_FREQ','ELS_QP'})
        self.assertNotIn('999 (C)',set(app.df_sls_combinations.service_combination))
        self.assertEqual(env[env.case=='999 (C)'].iloc[0].combination_group,'NAO_CLASSIFICADA')

    def test_correct_governors_even_when_frequency_has_larger_actions(self):
        app,r,_=pipeline()
        self.assertEqual(r.iloc[0].service_group_crack,'ELS_QP')
        self.assertEqual(r.iloc[0].service_group_deflection,'ELS_QP')
        self.assertEqual(r.iloc[0].service_group_steel,'ELS_CAR')
        self.assertEqual(r.iloc[0].service_group_concrete,'ELS_CAR')
        self.assertNotEqual(r.iloc[0].service_combination_crack,'202 (C)')
        self.assertNotEqual(r.iloc[0].service_combination_steel,'202 (C)')
        self.assertEqual(r.iloc[0].service_status,'OK')

    def test_missing_qp_never_uses_characteristic_for_crack(self):
        _,r,_=pipeline({'ELU':'101','ELS_CAR':'201'})
        self.assertEqual(r.iloc[0].service_status,'Dados insuficientes')
        self.assertTrue(pd.isna(r.iloc[0].service_wk_est_mm))
        self.assertEqual(r.iloc[0].status,'Verificar')

    def test_missing_characteristic_never_uses_qp_for_stress(self):
        _,r,_=pipeline({'ELU':'101','ELS_QP':'203'})
        self.assertEqual(r.iloc[0].service_status,'Dados insuficientes')
        self.assertTrue(pd.isna(r.iloc[0].service_sigma_s_MPa))
        self.assertEqual(r.iloc[0].status,'Verificar')

    def test_frequency_optional(self):
        _,r,_=pipeline({'ELU':'101','ELS_CAR':'201','ELS_QP':'203'})
        self.assertEqual(r.iloc[0].service_status,'OK')
        self.assertEqual(r.iloc[0].service_count_ELS_FREQ,0)


if __name__=='__main__':unittest.main()
