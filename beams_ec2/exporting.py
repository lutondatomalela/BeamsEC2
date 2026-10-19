"""Single-pass workbook export; no intermediate workbook reloads."""
import os
import tempfile
from pathlib import Path

import pandas as pd
import xlsxwriter


def workbook_frames(app):
    from . import design as d, serviceability as s
    results = app.df_results if app.df_results is not None else pd.DataFrame()
    summary = app.df_summary if app.df_summary is not None else pd.DataFrame()
    geometry = results if not results.empty else app.df_env
    cols = 'member name story case section_type section_geometry_summary section_geometry_source section_geometry_confidence section_fit_error_pct section_orientation_note bw_cm h_cm b_top_cm tf_top_cm b_bottom_cm tf_bottom_cm web_height_cm ax_import_cm2 ax_calc_cm2 iy_import_cm4 iy_calc_cm4 iz_import_cm4 iz_calc_cm4'.split()
    geometry = geometry[[c for c in cols if c in geometry.columns]] if geometry is not None else pd.DataFrame()
    yield '00_Info', app._metadata_df()
    yield '01_Parametros', app._parameters_df()
    yield '02_Resumo_Executivo', d._executive_summary_df_report_base(results, summary)
    for name, frame in [('03_Entrada_Dados', app.df_clean), ('04_Envelopes', app.df_env), ('05_Casos_Calculo', app.df_calc_input), ('05A_Geometria', geometry), ('06_Resultados_Completos', results), ('07_Resumo_Vigas', summary)]:
        yield name, frame
    yield '08_Memoria_Calculo', app._memory_for_report(results)
    yield '09_Flexao', d._flexure_audit_df_report_base(results)
    yield '10_Corte_Torcao', d._vt_audit_df_report_base(results)
    yield '11_ELS', s._sls_audit_df_serviceability(results)
    for name, attr in [('11A_ELS_Pontos','df_sls_points'), ('11B_ELS_Parametros','df_sls_parameters'), ('11B_Grupos_Combinacoes','df_combination_groups'), ('11C_ELS_Combinacoes','df_sls_combinations')]:
        yield name, getattr(app, attr, None)
    yield '12_Pormenorizacao', d._detailing_audit_df_report_base(results)
    for name, attr in [('12A_Porm_Longitudinal','df_longitudinal_detailing'), ('12B_Perfil_Armadura','df_longitudinal_profile'), ('13_Falhas','df_failures'), ('14_OK','df_ok')]:
        yield name, getattr(app, attr, None)
    yield '15_Shortlists', app.build_shortlists_df()
    for name, attr in [('16_Validacao','df_validation'), ('16A_Testes_Internos','df_internal_tests'), ('17_Notas_EC2','df_notes')]:
        yield name, getattr(app, attr, None)


def _excel_value(value):
    if value is None or pd.isna(value):
        return None
    if hasattr(value, 'item'):
        value = value.item()
    if isinstance(value, float) and not __import__('math').isfinite(value):
        return str(value)
    return value


def write_excel(app, path):
    from . import release as r
    target = Path(path)
    fd, temporary = tempfile.mkstemp(suffix='.xlsx', dir=target.parent)
    os.close(fd)
    try:
        with xlsxwriter.Workbook(temporary, {'constant_memory': True, 'strings_to_formulas': False, 'strings_to_urls': False}) as book:
            book.set_properties({'title': r.APP_NAME, 'subject': r.APP_SUBJECT, 'author': '', 'keywords': r.APP_KEYWORDS, 'category': r.APP_CATEGORY, 'comments': r.APP_TABLE_DESCRIPTION})
            header = book.add_format({'bold': True, 'font_color':'white', 'bg_color':'#1F4E5F', 'text_wrap':True, 'valign':'vcenter'})
            body = book.add_format({'num_format':'0.00', 'valign':'top', 'text_wrap':True})
            link = book.add_format({'font_color':'#1F4E5F','underline':True,'bold':True})
            for name, df in workbook_frames(app):
                df = df if df is not None else pd.DataFrame()
                if len(df.columns) > 16384:
                    raise ValueError(f'A folha {name} excede o limite de colunas do Excel.')
                # Split at Excel's row limit rather than silently dropping records.
                for part, start in enumerate(range(0, max(len(df), 1), 1048575)):
                    sheet_name = name if not part else name[:25] + f'_{part+1}'
                    ws = book.add_worksheet(sheet_name)
                    ws.hide_gridlines(2)
                    ws.freeze_panes(1, 0)
                    for j, col in enumerate(df.columns):
                        sample = [str(col)] + [str(v) for v in df.iloc[start:start+249, j] if pd.notna(v)]
                        ws.set_column(j, j, min(max(map(len, sample), default=10)+2, 48), body)
                        ws.write(0, j, str(col), header)
                    count = min(1048575, len(df)-start)
                    for i, values in enumerate(df.iloc[start:start+count].itertuples(index=False, name=None), 1):
                        row = [_excel_value(v) for v in values]
                        ws.write_row(i, 0, row)
                        if name in ('00_Info', '01_Parametros') and len(row) > 1 and str(row[0]).strip().lower() == 'programa':
                            ws.write_url(i, 1, r.GITHUB_URL, link, r.APP_NAME)
                    if len(df.columns):
                        ws.autofilter(0, 0, count, len(df.columns)-1)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class FrozenValue:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


def export_snapshot(app):
    """Read Tk values on the UI thread; workers receive only plain data."""
    from types import SimpleNamespace, MethodType
    from .release import BeamsEC2App
    snapshot = SimpleNamespace(input_file_path=app.input_file_path)
    for name, value in vars(app).items():
        if name.startswith('df_'):
            setattr(snapshot, name, value.copy(deep=True) if isinstance(value, pd.DataFrame) else value)
        elif name.startswith('var_') and hasattr(value, 'get'):
            setattr(snapshot, name, FrozenValue(value.get()))
    metadata = app._metadata_df().copy(deep=True)
    parameters = app._parameters_df().copy(deep=True)
    shortlists = app.build_shortlists_df().copy(deep=True)
    snapshot._metadata_df = lambda: metadata
    snapshot._parameters_df = lambda: parameters
    snapshot.build_shortlists_df = lambda: shortlists
    snapshot._memory_for_report = BeamsEC2App._memory_for_report
    for name in ('_pdf_df_table', '_pdf_table_style', '_write_pdf', '_write_excel'):
        setattr(snapshot, name, MethodType(getattr(BeamsEC2App, name), snapshot))
    return snapshot


def start_export(app, path, kind):
    from queue import Queue, Empty
    from threading import Thread
    from time import perf_counter
    from tkinter import messagebox
    if getattr(app, '_export_running', False):
        return
    snapshot = export_snapshot(app)
    completed = Queue()
    app._export_running = True
    started = perf_counter()
    app.status_var.set(f'A exportar {kind.upper()}…')

    def worker():
        temporary = None
        try:
            if kind == 'xlsx':
                snapshot._write_excel(path)
            else:
                fd, temporary = tempfile.mkstemp(suffix='.pdf', dir=Path(path).parent)
                os.close(fd)
                snapshot._write_pdf(temporary)
                os.replace(temporary, path)
            completed.put(None)
        except Exception as error:
            completed.put(error)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    def poll():
        try:
            error = completed.get_nowait()
        except Empty:
            app.status_var.set(f'A exportar {kind.upper()}… {perf_counter()-started:.0f} s')
            app.after(150, poll)
            return
        app._export_running = False
        if error is None:
            app.status_var.set(f'{kind.upper()} exportado em {perf_counter()-started:.1f} s: {path}')
        else:
            app.status_var.set('A exportação falhou.')
            messagebox.showerror('Erro', f'Não foi possível exportar {kind.upper()}.\n\n{error}')

    Thread(target=worker, daemon=True, name='BeamsEC2-export').start()
    app.after(150, poll)


def export_dialog(app, kind):
    from tkinter import filedialog, messagebox
    if getattr(app, '_export_running', False):
        return
    if app.df_results is None or app.df_results.empty:
        messagebox.showwarning('Aviso', 'Não há resultados para exportar.')
        return
    path = filedialog.asksaveasfilename(title='Exportar relatório', defaultextension='.'+kind, filetypes=[(kind.upper(), '*.'+kind)])
    if path:
        if not path.lower().endswith('.'+kind):
            path += '.'+kind
        try:
            start_export(app, path, kind)
        except Exception as error:
            messagebox.showerror('Erro', f'Não foi possível preparar a exportação.\n\n{error}')
