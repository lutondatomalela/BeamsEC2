"""Independent reference calculations and public-chain regression cases."""
import math
import unittest
from types import SimpleNamespace
import numpy as np
import pandas as pd
from beams_ec2.release import BeamDesigner, _prepare_input_frames
from beams_ec2.geometry import SectionProfileGeometry, _choose_face_rebar_geometry
from beams_ec2.serviceability import (
    _cracked_state_serviceability, _section_sls_states_serviceability,
    _local_sls_response_serviceability,
)
from beams_ec2.advanced import (
    _integrate_curvature_advanced, _calculate_member_sls_advanced, SLSParametersAdvanced,
)


def design(moment=200, height=40, **extra):
    raw = dict({'Member/Node/Case':'1/1/101 (C)', 'Station (m)':0,
                'Length (m)':6, 'HY (cm)':30, 'HZ (cm)':height,
                'Material':'C30/37', 'MY (kNm)':moment, 'FZ (kN)':50,
                'MX (kNm)':0}, **extra)
    _, env = _prepare_input_frames(pd.DataFrame([raw]))
    return BeamDesigner().design_one(env.iloc[0])


class ReinforcementTests(unittest.TestCase):
    def test_real_depth_and_iteration(self):
        r = design(400)
        self.assertEqual(r['status'], 'OK')
        self.assertTrue(r['reinforcement_converged'])
        self.assertGreaterEqual(r['reinforcement_iterations'], 2)
        self.assertLessEqual(r['eta_m_pos'], 1.0+1e-6)
        self.assertEqual(r['phi_st_mm'], r['reinforcement_stirrup_assumed_mm'])

    def test_negative_double_reinforcement(self):
        r = design(-400)
        self.assertEqual(r['status'], 'OK')
        self.assertGreater(r['as_prov_bot_mm2'], r['as_min_bot_mm2'])
        self.assertLessEqual(r['eta_m_neg'], 1.0+1e-6)

    def test_positive_negative_symmetry(self):
        pos, neg = design(400), design(-400)
        self.assertEqual(pos['bot_rebar'], neg['top_rebar'])
        self.assertEqual(pos['top_rebar'], neg['bot_rebar'])
        self.assertAlmostEqual(pos['mrd_pos_kNm'], neg['mrd_neg_kNm'])

    def test_impossible_cage_does_not_pass(self):
        r = design(600, 25)
        self.assertEqual(r['status'], 'Falha')
        self.assertFalse(r['reinforcement_converged'])

    def test_actual_ten_mm_stirrup_depth(self):
        r = design(200,60,**{'FZ (kN)':500,'MX (kNm)':20})
        self.assertEqual(r['phi_st_mm'], 10)
        self.assertEqual(r['bot_layers'], 1)
        phi = float(r['bot_rebar'].split('Ø')[1])
        self.assertAlmostEqual(r['d_bot_mm'], 600-35-10-phi/2)

    def test_selector_stirrup_axis(self):
        section = SectionProfileGeometry(600,300,300,0,300,0)
        r8 = _choose_face_rebar_geometry(BeamDesigner(),600,section,'bottom',8)
        r10 = _choose_face_rebar_geometry(BeamDesigner(),600,section,'bottom',10)
        self.assertEqual(r8.label,r10.label)
        self.assertAlmostEqual(r10.centroid_from_edge_mm-r8.centroid_from_edge_mm,2)

    def test_torsion_cannot_use_extra_shear_legs(self):
        r = BeamDesigner().choose_stirrups(100,300,600,550,True)
        self.assertEqual(r['stirrup_legs'],2)
        self.assertEqual(r['stirrup_status'],'Não cabe')

    def test_t_section_tension_width(self):
        from beams_ec2.reinforcement import mean_tension_width
        p=SectionProfileGeometry(600,300,900,120,300,0,'T')
        self.assertEqual(mean_tension_width(p),300)
        # Inverted T: centroid from top = (300*480*240+900*120*540)/252000.
        centroid=(300*480*240+900*120*540)/252000
        expected=(300*(480-centroid)+900*120)/(600-centroid)
        self.assertAlmostEqual(mean_tension_width(p.flipped()),expected)

    def test_negative_t_flange_minimum_not_web_only(self):
        r=design(-10,60,**{'BF (cm)':90,'HF (cm)':12})
        self.assertGreater(r['as_min_top_mm2'],r['as_min_bot_mm2'])
        self.assertGreaterEqual(r['as_prov_top_mm2'],r['as_min_top_mm2'])

    def test_transverse_spacing_enforced(self):
        d = BeamDesigner()
        r = d.choose_stirrups(0.3,800,600,550,False,phi_st_mm=8)
        self.assertEqual(r['stirrup_status'],'OK')
        pitch = (800-2*d.cover_mm-8)/(r['stirrup_legs']-1)
        self.assertLessEqual(pitch,min(0.75*550,600))


class IndependentSLSTests(unittest.TestCase):
    """Rectangular b=300 h=600, As=1500/600, axes=550/50 mm.

    References use closed-form transformed-section equations; no application
    routine is used to obtain expected neutral axes, inertias or crack widths.
    """
    b,h,at,ac,dt,dc = 300.,600.,1500.,600.,550.,50.
    E,Es,fct = 30000.,200000.,3.

    def setUp(self):
        self.p = SectionProfileGeometry(self.h,self.b,self.b,0,self.b,0)
        self.states = _section_sls_states_serviceability(self.p,self.at,self.ac,550,550,self.E,self.E/2,self.fct,0)

    def ref(self,E):
        n=self.Es/E
        a=self.b/2
        B=n*self.at+(n-1)*self.ac
        C=-(n*self.at*self.dt+(n-1)*self.ac*self.dc)
        x=(-B+math.sqrt(B*B-4*a*C))/(2*a)
        Icr=self.b*x**3/3+n*self.at*(self.dt-x)**2+(n-1)*self.ac*(x-self.dc)**2
        A=self.b*self.h+(n-1)*(self.at+self.ac)
        xu=(self.b*self.h*self.h/2+(n-1)*(self.at*self.dt+self.ac*self.dc))/A
        Iun=self.b*self.h**3/12+self.b*self.h*(self.h/2-xu)**2+(n-1)*(self.at*(self.dt-xu)**2+self.ac*(self.dc-xu)**2)
        return x,Icr,xu,Iun

    def response(self,M,time='short',beta=1,kt=0.6):
        return _local_sls_response_serviceability(M,self.states,time,beta,self.fct,self.E,self.Es,
                    self.p,20,100,35,8,kt,0)

    def test_cracked_neutral_axis_and_inertia(self):
        x,I,_,_=self.ref(self.E)
        got=_cracked_state_serviceability(self.p,self.at,self.dt,self.ac,self.dc,self.Es/self.E)
        self.assertAlmostEqual(got['x_mm'],x,places=8)
        self.assertAlmostEqual(got['I_mm4']/I,1,places=10)

    def test_uncracked_steel_stress(self):
        _,_,x,I=self.ref(self.E)
        expected=self.Es/self.E*10e6*(self.dt-x)/I
        got=self.response(10)
        self.assertEqual(got['zeta'],0)
        self.assertAlmostEqual(got['sigma_s_MPa'],expected,places=8)
        self.assertEqual(got['wk_mm'],0)

    def test_crack_width_and_interpolated_curvature(self):
        M=100e6
        x,Icr,_,Iun=self.ref(self.E)
        sigma=self.Es/self.E*M*(self.dt-x)/Icr
        hceff=min(2.5*(self.h-self.dt),(self.h-x)/3,self.h/2)
        rho=self.at/(self.b*hceff)
        sr=3.4*43+0.8*0.5*0.425*20/rho
        deps=max((sigma-0.6*self.fct/rho*(1+self.Es/self.E*rho))/self.Es,0.6*sigma/self.Es)
        zeta=1-(54/100)**2
        curvature=M/self.E*((1-zeta)/Iun+zeta/Icr)
        got=self.response(100)
        self.assertAlmostEqual(got['wk_mm'],sr*deps,places=10)
        self.assertAlmostEqual(got['curvature_load_1_per_mm']/curvature,1,places=10)

    def test_long_term_curvature(self):
        _,Icr,_,Iun=self.ref(self.E/2)
        zeta=1-0.5*(54/100)**2
        expected=100e6/(self.E/2)*((1-zeta)/Iun+zeta/Icr)
        self.assertAlmostEqual(self.response(100,'long',0.5,0.4)['curvature_load_1_per_mm']/expected,1,places=10)

    def test_reversing_symmetric_section_and_steel(self):
        symmetric=_section_sls_states_serviceability(self.p,1500,1500,550,550,self.E,self.E/2,self.fct,0)
        def calc(m):
            return _local_sls_response_serviceability(m,symmetric,'short',1,self.fct,self.E,self.Es,self.p,20,100,35,8,0.6,0)
        pos,neg=calc(100),calc(-100)
        self.assertAlmostEqual(pos['wk_mm'],neg['wk_mm'])
        self.assertAlmostEqual(pos['curvature_total_1_per_mm'],-neg['curvature_total_1_per_mm'])

    def test_continuous_two_span_moment_integration(self):
        L,q,EI=6000.,0.01,1e14
        x=np.linspace(0,L,2001)
        M=3*q*L*x/8-q*x*x/2  # first span of two equal continuous spans
        _,y,_=_integrate_curvature_advanced(x,M/EI,'Entre apoios (y0=yL=0)')
        t=(1+math.sqrt(33))/16
        reference=abs(q*L**4/EI*(t**3/16-t**4/24-t/48))
        self.assertAlmostEqual(max(abs(y))/reference,1,places=5)

    def test_full_member_constant_bending_reference(self):
        from beams_ec2.base import concrete_props
        cp=concrete_props(30)
        # Engine uses Ecm and fctm from C30/37, so recompute the closed-form
        # section with these material values for this end-to-end comparison.
        r=pd.Series(dict(member='1',case='101',length_m=6,h_cm=60,bw_cm=30,section_type='Rectangular',
              as_prov_bot_mm2=self.at,as_prov_top_mm2=self.ac,d_bot_mm=550,d_top_mm=550,
              bot_rebar='5Ø20',top_rebar='3Ø16',bot_clear_spacing_mm=100,top_clear_spacing_mm=100,
              phi_st_mm=8,cover_mm=35,fck_MPa=30,fyk_MPa=500))
        group=pd.DataFrame({'station':[0,1.5,3,4.5,6],'my':[100]*5,'__row_order':range(5)})
        params=SLSParametersAdvanced(regime='Característica / curta duração',include_shrinkage=False,
                                     support_condition='Entre apoios (y0=yL=0)')
        got,points=_calculate_member_sls_advanced(SimpleNamespace(),r,group,'201 ELS','teste',params)
        _,Icr,_,Iun=self.ref(cp['Ecm'])
        Mcr=cp['fctm']*self.b*self.h**2/6/1e6
        zeta=1-(Mcr/100)**2
        kappa=100e6/cp['Ecm']*((1-zeta)/Iun+zeta/Icr)
        self.assertAlmostEqual(got['service_deflection_instant_mm'],kappa*6000**2/8,places=7)
        self.assertGreater(len(points),100)


if __name__=='__main__':
    unittest.main()
