"""Self-check inside the frozen Windows application, including real Tk calculation."""
import json
from pathlib import Path
import traceback
from unittest.mock import patch


def run_smoke_test(directory):
    output=Path(directory).resolve();output.mkdir(parents=True,exist_ok=True)
    app=None;result={'ok':False}
    try:
        import pandas as pd
        import xlrd
        from .release import BeamsEC2App,APP_VERSION,read_table_file
        app=BeamsEC2App();app.withdraw()
        failures=[];completed=[]
        def fail(*args,**kwargs):
            failures.append(str(args));app.quit()
        app.report_callback_exception=fail
        rows=[]
        for case,factor in [(201,1),(302,.6),(303,1.5),(304,.8),(999,50)]:
            for node,sign in [(15052,1),(15053,-1)]:
                label=f'{case} (C)' + (' (CQC)' if case==201 else '')
                rows.append({'Member/Node/Case':f'1/{node}/{label}','Length (m)':6,
                             'HY (cm)':30,'HZ (cm)':60,'Material':'C30/37',
                             'MY (kNm)':factor*40,'FZ (kN)':sign*factor*20,'MX (kNm)':0})
        source=output/'input.xlsx';pd.DataFrame(rows).to_excel(source,index=False)
        def start():
            try:
                app.var_elu_cases.set('201');app.var_sls_qp_cases.set('302')
                app.var_sls_freq_cases.set('303');app.var_sls_char_cases.set('304')
                frame,_=read_table_file(source);app.load_df(frame,str(source))
                app.run_design();app.after(50,poll)
            except Exception:fail(traceback.format_exc())
        def poll():
            if app.status_var.get().startswith('Cálculo concluído'):
                completed.append(True);app.quit()
            else:app.after(50,poll)
        with patch('tkinter.messagebox.showerror',fail),patch('tkinter.messagebox.showwarning',fail):
            app.after(10,start)
            watchdog=app.after(60000,lambda:fail('Calculation timeout: '+app.status_var.get()))
            app.mainloop();app.after_cancel(watchdog)
            if failures or not completed:raise RuntimeError(str(failures))
            if len(app.df_results)!=1:raise RuntimeError('Expected one selected ELU combination')
            r=app.df_results.iloc[0]
            if r.service_combination_crack!='302 (C)' or r.service_combination_steel!='304 (C)':
                raise RuntimeError('Incorrect service group routing')
            if not app.df_clean.station.isna().all():raise RuntimeError('Node positions were invented')
            if r.service_status!='Dados insuficientes':raise RuntimeError('Missing span diagram not reported')
            if not app.df_longitudinal_profile.empty:raise RuntimeError('Cutoffs generated without positions')
            xlsx=output/'results.xlsx';app._write_excel(str(xlsx))
            audit=pd.read_excel(xlsx,sheet_name='11B_Grupos_Combinacoes')
            if 'EXCLUIDA' not in set(audit.combination_group):raise RuntimeError('Missing exclusion audit')
            for name,scope in [('summary','Resumo executivo'),('technical','Relatório técnico'),('memory','Memória de cálculo')]:
                app.var_pdf_scope.set(scope);pdf=output/f'{name}.pdf';app._write_pdf(str(pdf))
                if pdf.stat().st_size<1000 or not pdf.read_bytes().startswith(b'%PDF-'):
                    raise RuntimeError('Invalid PDF: '+name)
        result={'ok':True,'version':APP_VERSION,'checks':['Tk','XLSX import','xlrd available',
                'node-only input','ELU CQC','ELS CAR/FREQ/QP','excluded case',
                'missing deflection diagram','XLSX export','three PDF exports']}
    except Exception:
        result['error']=traceback.format_exc()
    finally:
        if app is not None:app.destroy()
        (output/'smoke-test.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if result['ok'] else 1
