import math
import unittest
import numpy as np
import pandas as pd
from beams_ec2.release import BeamDesigner,_prepare_input_frames
from beams_ec2.base import concrete_props
from beams_ec2.serviceability import _ec2_creep_coefficient_serviceability as creep, _ec2_shrinkage_strain_serviceability as shrink
from beams_ec2.advanced import _creep_history_advanced,SLSParametersAdvanced


def frame(actions):
    return pd.DataFrame([dict({'Member/Node/Case':f'1/1/{101+i} (C)',
             'Station (m)':0,'Length (m)':6,'HY (cm)':30,'HZ (cm)':60,
             'Material':'C30/37','MY (kNm)':m,'FZ (kN)':v,'MX (kNm)':t},**extra)
            for i,(m,v,t,extra) in enumerate(actions)])


class CommonCageTests(unittest.TestCase):
    def test_opposite_moments_use_same_cage(self):
        _,env=_prepare_input_frames(frame([(400,40,0,{}),(-300,80,0,{})]))
        r=BeamDesigner().design_dataframe(env)
        for key in ['bot_rebar','top_rebar','phi_st_mm','s_st_mm','skin_rebar']:
            self.assertEqual(r[key].nunique(),1,key)
        self.assertTrue(r.shared_cage_converged.all())
        self.assertTrue((r.eta_m_pos<=1+1e-6).all())
        self.assertTrue((r.eta_m_neg<=1+1e-6).all())
        self.assertEqual(list(r.case),['101 (C)','102 (C)'])

    def test_common_torsion_and_shear_cage(self):
        _,env=_prepare_input_frames(frame([(100,40,20,{}),(-200,200,0,{})]))
        r=BeamDesigner().design_dataframe(env)
        self.assertTrue(r.shared_cage_converged.all())
        self.assertTrue(r.closed_cage.all())
        for key in ['bot_rebar','top_rebar','phi_st_mm','stirrup_legs','s_st_mm','skin_rebar']:
            self.assertEqual(r[key].nunique(),1,key)
        self.assertTrue((r.stirrup_legs>=2).all())
        # Only the two outer legs resist torsion, even with extra shear legs.
        from beams_ec2.base import bar_area_mm2
        self.assertTrue((2*r.phi_st_mm.map(bar_area_mm2)/r.s_st_mm >=
                         r.Asw_s_torsion_req_mm2_per_m/1000 - 1e-9).all())

    def test_mixed_member_geometry_rejected(self):
        _,env=_prepare_input_frames(frame([(100,40,0,{}),(100,40,0,{'HZ (cm)':50})]))
        with self.assertRaises(ValueError):
            BeamDesigner().design_dataframe(env)

    def test_no_combination_dropped(self):
        _,env=_prepare_input_frames(frame([(100,40,0,{}),(-100,50,0,{}),(200,70,0,{})]))
        r=BeamDesigner().design_dataframe(env)
        self.assertEqual(len(r),3)
        self.assertEqual(r.adopted_for_cases.nunique(),1)
        self.assertIn('103 (C)',r.iloc[0].adopted_for_cases)


class TorsionDetailingTests(unittest.TestCase):
    def result(self,moment=100,height=60):
        _,env=_prepare_input_frames(frame([(moment,50,20,{'HZ (cm)':height})]))
        return BeamDesigner().design_one(env.iloc[0])

    def test_reserved_area_matches_perimeter_shares(self):
        r=self.result()
        total=r['torsion_reserved_bot_mm2']+r['torsion_reserved_top_mm2']+2*r['skin_reinf_face_mm2']
        self.assertAlmostEqual(total,r['Asl_torsion_req_mm2'])
        self.assertGreater(r['torsion_reserved_bot_mm2'],0)
        self.assertLessEqual(r['torsion_side_pitch_mm'],350)

    def test_reserved_steel_not_counted_for_bending(self):
        from beams_ec2.geometry import _section_from_row_geometry
        _,env=_prepare_input_frames(frame([(100,50,20,{})]))
        d=BeamDesigner();r=d.design_one(env.iloc[0]);p=_section_from_row_geometry(env.iloc[0])
        reference=d.flexural_capacity(r['as_prov_bot_mm2']-r['torsion_reserved_bot_mm2'],
             r['as_prov_top_mm2']-r['torsion_reserved_top_mm2'],p,
             r['d_bot_mm'],600-r['d_top_mm'],r['fcd_MPa'],r['fyd_MPa'])
        self.assertAlmostEqual(r['mrd_pos_kNm'],reference['MRd_kNm'])

    def test_side_reinforcement_even_for_low_beam(self):
        r=self.result(50,35)
        self.assertGreater(r['skin_reinf_face_mm2'],0)
        self.assertGreater(r['skin_n_per_face'],0)


class DeferredEffectsTests(unittest.TestCase):
    def reference_creep(self,fcm,rh,h0,t0,t,cement='N'):
        if t<=t0:
            return 0
        alpha={'S':-1,'N':0,'R':1}[cement]
        age=max(t0*(9/(2+t0**1.2)+1)**alpha,0.5)
        a1,a2,a3=(35/fcm)**0.7,(35/fcm)**0.2,(35/fcm)**0.5
        H=(1-rh/100)/(0.1*h0**(1/3))
        if fcm<=35:
            prh=1+H
            bh=min(1.5*(1+(0.012*rh)**18)*h0+250,1500)
        else:
            prh=(1+H*a1)*a2
            bh=min(1.5*(1+(0.012*rh)**18)*h0+250*a3,1500*a3)
        return prh*16.8/math.sqrt(fcm)/(0.1+age**0.2)*((t-t0)/(bh+t-t0))**0.3

    def test_creep_against_annex_b_equations(self):
        for fcm in (28,38,58):
            for cement in ('S','N','R'):
                with self.subTest(fcm=fcm,cement=cement):
                    self.assertAlmostEqual(creep(fcm,70,200,28,3650,cement),
                                           self.reference_creep(fcm,70,200,28,3650,cement),places=12)

    def test_zero_creep_before_loading(self):
        self.assertEqual(creep(38,70,200,28,28),0)
        self.assertEqual(creep(38,70,200,28,10),0)

    def test_two_phase_history_matches_weighted_phi(self):
        p=SLSParametersAdvanced(history_mode='Duas fases G+Q',permanent_fraction_pct=70,
                               t0_permanent_days=14,t0_variable_days=365,t_days=3650)
        result=_creep_history_advanced(concrete_props(30),p,200)
        expected=.7*self.reference_creep(38,70,200,14,3650)+.3*self.reference_creep(38,70,200,365,3650)
        self.assertAlmostEqual(result['phi'],expected,places=12)
        self.assertGreater(result['phi_g'],result['phi_q'])

    def test_shrinkage_against_ec2_equations(self):
        t,ts,h0,rh=3650,7,200,70
        beta_rh=1.55*(1-(rh/100)**3)
        eps0=.85*(220+110*4)*math.exp(-.12*38/10)*1e-6*beta_rh
        beta=(t-ts)/(t-ts+.04*h0**1.5)
        dry=beta*.85*eps0
        auto=(1-math.exp(-.2*math.sqrt(t)))*2.5*(30-10)*1e-6
        r=shrink(30,38,rh,h0,t,ts,'N')
        self.assertAlmostEqual(r['eps_cd'],dry,places=14)
        self.assertAlmostEqual(r['eps_cs'],dry+auto,places=14)

    def test_drying_not_before_start(self):
        r=shrink(30,38,70,200,5,7,'N')
        self.assertEqual(r['eps_cd'],0)
        self.assertGreater(r['eps_ca'],0)

    def test_shrinkage_curvature_integral(self):
        from beams_ec2.geometry import SectionProfileGeometry
        from beams_ec2.serviceability import _section_sls_states_serviceability,_local_sls_response_serviceability
        from beams_ec2.advanced import _integrate_curvature_advanced
        p=SectionProfileGeometry(600,300,300,0,300,0)
        Ec,Es,eps=15000,200000,.0003
        n=Es/Ec;At,Ac,d,dc=1500,600,550,50
        area=300*600+(n-1)*(At+Ac)
        x=(300*600*300+(n-1)*(At*d+Ac*dc))/area
        I=300*600**3/12+300*600*(300-x)**2+(n-1)*(At*(d-x)**2+Ac*(dc-x)**2)
        S=At*(d-x)+Ac*(dc-x)
        reference=eps*n*S/I
        states=_section_sls_states_serviceability(p,At,Ac,550,550,30000,Ec,3,eps)
        got=_local_sls_response_serviceability(0,states,'long',.5,3,30000,Es,p,20,100,35,8,.4,eps)
        self.assertAlmostEqual(got['curvature_total_1_per_mm'],reference,places=14)
        xgrid=np.linspace(0,6000,201)
        _,y,_=_integrate_curvature_advanced(xgrid,np.full(201,reference),'Entre apoios (y0=yL=0)')
        self.assertAlmostEqual(max(abs(y)),abs(reference)*6000**2/8,places=9)


class SnapshotTests(unittest.TestCase):
    def test_inputs_frozen(self):
        from types import SimpleNamespace
        from beams_ec2.calculation import snapshot_inputs
        class Mutable:
            def __init__(self,x):self.x=x
            def get(self):return self.x
        app=SimpleNamespace(df_clean=pd.DataFrame({'x':[1]}),df_env=pd.DataFrame({'m':[100]}),var_cover=Mutable(35))
        frozen=snapshot_inputs(app)
        app.var_cover.x=99
        app.df_clean.loc[0,'x']=9
        self.assertEqual(frozen.var_cover.get(),35)
        self.assertEqual(frozen.df_clean.iloc[0].x,1)

    def test_import_rejected_during_calculation(self):
        from types import SimpleNamespace
        from beams_ec2.release import BeamsEC2App
        with self.assertRaises(RuntimeError):
            BeamsEC2App.load_df(SimpleNamespace(_calculation_running=True),pd.DataFrame())


if __name__=='__main__':
    unittest.main()
