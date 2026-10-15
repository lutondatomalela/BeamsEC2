"""Opt-in end-to-end check executed by the frozen Windows application."""
import json
from pathlib import Path
import traceback
from unittest.mock import patch


def run_smoke_test(output_directory):
    output = Path(output_directory).resolve()
    output.mkdir(parents=True, exist_ok=True)
    app = None
    result = {'ok': False}
    try:
        import pandas as pd
        from .release import APP_VERSION, BeamsEC2App
        from .table_io import read_table_file

        app = BeamsEC2App()
        app.withdraw()
        failures = []
        completed = []

        def fail(*args, **kwargs):
            failures.append(str(args))
            app.quit()

        app.report_callback_exception = fail
        rows = []
        for case, factor in [(101, 1.0), (201, 0.8), (202, 0.7), (203, 0.6)]:
            for index, x in enumerate([0, 1.5, 3, 4.5, 6]):
                rows.append({'Member/Node/Case': f'1/{index+1}/{case} (C)',
                             'Station (m)': x, 'Length (m)': 6,
                             'HY (cm)': 30, 'HZ (cm)': 60, 'Material': 'C30/37',
                             'MY (kNm)': factor*100*(1-((x-3)/3)**2),
                             'FZ (kN)': factor*(50-x*100/6), 'MX (kNm)': 0,
                             'Support Condition': 'Entre apoios (y0=yL=0)'})
        source = output/'input.xlsx'
        pd.DataFrame(rows).to_excel(source, index=False)

        def start():
            try:
                app.var_elu_cases.set('101')
                app.var_sls_char_cases.set('201')
                app.var_sls_freq_cases.set('202')
                app.var_sls_qp_cases.set('203')
                frame, _ = read_table_file(source)
                app.load_df(frame, str(source))
                app.run_design()
                app.after(50, poll)
            except Exception:
                fail(traceback.format_exc())

        def poll():
            if app.status_var.get().startswith('Cálculo concluído'):
                completed.append(True)
                app.quit()
            else:
                app.after(50, poll)

        with patch('tkinter.messagebox.showerror', fail), patch('tkinter.messagebox.showwarning', fail):
            app.after(10, start)
            watchdog = app.after(60000, lambda: fail('Calculation timeout'))
            app.mainloop()
            app.after_cancel(watchdog)
            if failures or not completed:
                raise RuntimeError(f'GUI calculation failed: {failures}')
            if len(app.df_results) != 1:
                raise RuntimeError('Expected one ELU result')
            row = app.df_results.iloc[0]
            if (row['service_combinations_checked'] != 3 or
                    row['service_group_crack'] != 'ELS_QP' or
                    row['service_group_steel'] != 'ELS_CAR'):
                raise RuntimeError('Incorrect ELS combination routing')
            xlsx = output/'results.xlsx'
            app._write_excel(str(xlsx))
            groups = pd.read_excel(xlsx, sheet_name='04A_Grupos_Combinacoes')
            if set(groups['combination_group']) != {'ELU', 'ELS_CAR', 'ELS_FREQ', 'ELS_QP'}:
                raise RuntimeError('Incorrect XLSX combination groups')
            for name, scope in [('summary', 'Resumo executivo'),
                                ('technical', 'Relatório técnico'),
                                ('calculation', 'Memória de cálculo')]:
                app.var_pdf_scope.set(scope)
                pdf = output/f'{name}.pdf'
                app._write_pdf(str(pdf))
                if pdf.stat().st_size < 1000 or not pdf.read_bytes().startswith(b'%PDF-'):
                    raise RuntimeError(f'Invalid PDF: {name}')
        result = {'ok': True, 'version': APP_VERSION,
                  'checks': ['Tk', 'XLSX import', 'ELU', 'ELS_CAR', 'ELS_FREQ',
                             'ELS_QP', 'XLSX export', 'three PDF reports']}
    except Exception:
        result['error'] = traceback.format_exc()
    finally:
        if app is not None:
            app.destroy()
        (output/'smoke-test.json').write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                              encoding='utf-8')
    return 0 if result['ok'] else 1
