"""Exercise the real Tk event loop and exports on a Windows runner.

Enable explicitly; ordinary headless test discovery skips this test.
"""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd


@unittest.skipUnless(sys.platform=='win32' and os.environ.get('BEAMSEC2_GUI_TESTS')=='1',
                     'Windows Tk integration enabled only in the GUI CI step')
class WindowsGUIIntegrationTests(unittest.TestCase):
    def test_import_calculate_els_and_exports(self):
        from beams_ec2.release import BeamsEC2App
        app=BeamsEC2App()
        app.withdraw()
        failures=[]
        completed=[]
        def error(*args,**kwargs):
            failures.append(str(args))
            app.quit()
        app.report_callback_exception=lambda *args: error(*args)
        rows=[]
        for case,factor in [('101 (C)',1.0),('201 ELS QP',0.6)]:
            for index,x in enumerate([0,1.5,3,4.5,6]):
                rows.append({'Member/Node/Case':f'1/{index+1}/{case}',
                             'Station (m)':x,'Length (m)':6,'HY (cm)':30,'HZ (cm)':60,
                             'Material':'C30/37','MY (kNm)':factor*100*(1-((x-3)/3)**2),
                             'FZ (kN)':factor*(50-x*100/6),'MX (kNm)':0,
                             'Support Condition':'Entre apoios (y0=yL=0)'})
        def start():
            try:
                app.load_df(pd.DataFrame(rows),'CI integration')
                app.run_design()
                app.after(50,poll)
            except Exception as exc:
                error(exc)
        def poll():
            if app.status_var.get().startswith('Cálculo concluído'):
                completed.append(True)
                app.quit()
            else:
                app.after(50,poll)
        def timeout():
            error('Timeout waiting for calculation: '+app.status_var.get())
        try:
            with patch('tkinter.messagebox.showerror',error), patch('tkinter.messagebox.showwarning',error):
                app.after(10,start)
                watchdog=app.after(30000,timeout)
                app.mainloop()
                app.after_cancel(watchdog)
                self.assertFalse(failures, failures)
                self.assertTrue(completed,'Calculation did not complete')
                self.assertEqual(len(app.df_results),1)
                self.assertIn('service_wk_est_mm',app.df_results)
                self.assertEqual(app.df_results.iloc[0]['service_combinations_checked'],1)
                with tempfile.TemporaryDirectory() as folder:
                    xlsx=Path(folder)/'result.xlsx'
                    app._write_excel(str(xlsx))
                    self.assertGreater(xlsx.stat().st_size,1000)
                    for index,scope in enumerate(['Resumo executivo','Relatório técnico','Memória de cálculo']):
                        app.var_pdf_scope.set(scope)
                        pdf=Path(folder)/f'report{index}.pdf'
                        app._write_pdf(str(pdf))
                        self.assertTrue(pdf.read_bytes().startswith(b'%PDF-'))
                        self.assertGreater(pdf.stat().st_size,1000)
        finally:
            app.destroy()


if __name__=='__main__':
    unittest.main()
