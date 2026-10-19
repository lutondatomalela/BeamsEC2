"""Opt-in test of group selection through the real Windows Tk event loop."""
import os
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import pandas as pd


@unittest.skipUnless(sys.platform=='win32' and os.getenv('BEAMSEC2_GUI_TESTS')=='1',
                     'Real Windows GUI test runs in its dedicated CI step')
class WindowsGroupTests(unittest.TestCase):
    def test_node_input_groups_and_exports(self):
        from beams_ec2.release import BeamsEC2App
        app=BeamsEC2App();app.withdraw()
        failures=[];completed=[]
        def fail(*args,**kwargs):
            failures.append(str(args));app.quit()
        app.report_callback_exception=fail
        rows=[]
        for case,factor in [(201,1),(302,.6),(303,1.5),(304,.8),(999,50)]:
            for node,sign in [(15052,1),(15053,-1)]:
                label=f'{case} (C)' + (' (CQC)' if case==201 else '')
                rows.append({'Member/Node/Case':f'1/{node}/{label}', 'Length (m)':6,
                             'HY (cm)':30,'HZ (cm)':60,'Material':'C30/37',
                             'MY (kNm)':factor*40,'FZ (kN)':sign*factor*20,'MX (kNm)':0})
        def start():
            try:
                app.var_elu_cases.set('201');app.var_sls_qp_cases.set('302')
                app.var_sls_freq_cases.set('303');app.var_sls_char_cases.set('304')
                app.load_df(pd.DataFrame(rows),'node-only group test')
                app.run_design();app.run_design()
                app.var_sls_qp_cases.set('999')  # Running results keep the verified selection.
                app.after(50,poll)
            except Exception as exc:fail(exc)
        def poll():
            if app.status_var.get().startswith('Cálculo concluído'):
                completed.append(True);app.quit()
            else:app.after(50,poll)
        try:
            with patch('tkinter.messagebox.showerror',fail),patch('tkinter.messagebox.showwarning',fail):
                app.after(10,start)
                watchdog=app.after(60000,lambda:fail('Calculation timeout: '+app.status_var.get()))
                app.mainloop();app.after_cancel(watchdog)
                self.assertFalse(failures,failures);self.assertTrue(completed)
                self.assertEqual(len(app.df_results),1)
                self.assertEqual(app.df_results.service_combination_crack.iloc[0],'302 (C)')
                self.assertEqual(app.df_results.service_combination_steel.iloc[0],'304 (C)')
                self.assertEqual(app.df_results.service_status.iloc[0],'Dados insuficientes')
                self.assertFalse(app._calculation_running)
                self.assertTrue(app._program_icon_path.is_file())
                self.assertEqual(app._program_icon.width(),256)
                self.assertTrue(hasattr(app,'_program_icon'))
                self.assertTrue(app.df_clean.station.isna().all())
                groups=app.df_combination_groups.set_index('case').combination_group
                self.assertEqual(groups['201 (C) (CQC)'],'ELU')
                self.assertEqual(groups['999 (C)'],'EXCLUIDA')
                with tempfile.TemporaryDirectory() as folder:
                    xlsx=Path(folder)/'groups.xlsx';app._write_excel(str(xlsx))
                    audit=pd.read_excel(xlsx,sheet_name='11B_Grupos_Combinacoes')
                    self.assertIn('EXCLUIDA',set(audit.combination_group))
                    for index,scope in enumerate(['Resumo executivo','Relatório técnico','Memória de cálculo']):
                        app.var_pdf_scope.set(scope);pdf=Path(folder)/f'{index}.pdf'
                        app._write_pdf(str(pdf))
                        self.assertTrue(pdf.read_bytes().startswith(b'%PDF-'))
                        self.assertGreater(pdf.stat().st_size,1000)
        finally:app.destroy()
