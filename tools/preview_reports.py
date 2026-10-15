"""Generate deterministic QA reports without opening a desktop window.

Run from the repository root: python tools/preview_reports.py
Outputs are disposable under out/pdf_qa (ignored by git).
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace,MethodType
import pandas as pd
from beams_ec2.release import BeamsEC2App,BeamDesigner,_prepare_input_frames
from beams_ec2.base import build_summary_by_member
from beams_ec2.advanced import _apply_serviceability_advanced,_longitudinal_detailing_advanced,_internal_tests_advanced


class Value:
    def __init__(self,value):self.value=value
    def get(self):return self.value


def harness():
    data=[]
    for member,sign in [(1,1),(2,-1)]:
        for case,factor in [('101 (C)',1),('102 (C)',-.7),('201 ELS QP',.6),('202 ELS CARACTERISTICA',.8),('203 ELS FREQ',.7)]:
            for i,x in enumerate([0,1.5,3,4.5,6]):
                data.append({'Member/Node/Case':f'{member}/{i+1}/{case}',
                    'Station (m)':x,'Length (m)':6,'HY (cm)':30,'HZ (cm)':60,
                    'Material':'C30/37','Name':f'V{member} - Sala e corredor','Story':'Piso 01',
                    'MY (kNm)':sign*factor*200*(1-((x-3)/3)**2),'FZ (kN)':factor*(100-x*200/6),
                    'MX (kNm)':5 if member==2 else 0,
                    'Support Condition':'Entre apoios (y0=yL=0)'})
    clean,env=_prepare_input_frames(pd.DataFrame(data))
    from beams_ec2.combinations import classify_combinations
    selection={'ELU':'101-102','ELS_CAR':'202','ELS_FREQ':'203','ELS_QP':'201'}
    clean=classify_combinations(clean,selection)
    env=classify_combinations(env,selection)
    app=SimpleNamespace(df_clean=clean,df_env=env,input_file_path='Caso sintético de validação',
          var_service_case=Value(''),var_ld_limit=Value(250),var_crack_limit=Value(.3),
          var_moment_axis=Value('MY'),var_cover=Value(35),var_fyk=Value(500),
          var_calc_mode=Value('dimensionamento'),var_pdf_scope=Value('Relatório técnico'))
    elu=env[env.limit_state=='ELU']
    app.df_results=_apply_serviceability_advanced(app,BeamDesigner().design_dataframe(elu))
    app.df_summary=build_summary_by_member(app.df_results)
    app.df_failures=app.df_results[app.df_results.status=='Falha']
    app.df_ok=app.df_results[app.df_results.status=='OK']
    app.df_calc_input=elu
    app.df_validation=pd.DataFrame();app.df_notes=pd.DataFrame()
    app.df_longitudinal_detailing,app.df_longitudinal_profile=_longitudinal_detailing_advanced(app,app.df_results)
    app.df_internal_tests=_internal_tests_advanced()
    app._parameters_df=lambda:pd.DataFrame([['Caso','Duas vigas; ELU 101-102; ELS QP 201, CAR 202 e FREQ 203'],['L [m]',6],['Betão','C30/37'],['Recobrimento [mm]',35]],columns=['Parâmetro','Valor'])
    for name in ('_pdf_df_table','_pdf_table_style','_write_pdf'):
        setattr(app,name,MethodType(getattr(BeamsEC2App,name),app))
    return app


if __name__=='__main__':
    app=harness()
    out=Path('out/pdf_qa');out.mkdir(parents=True,exist_ok=True)
    for label,scope in [('summary','Resumo executivo'),('technical','Relatório técnico'),('memory','Memória de cálculo')]:
        app.var_pdf_scope=Value(scope)
        app._write_pdf(str(out/(label+'.pdf')))
        print(out/(label+'.pdf'))
