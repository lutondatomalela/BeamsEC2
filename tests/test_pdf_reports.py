import tempfile
from pathlib import Path
import unittest
from pypdf import PdfReader
from tools.preview_reports import harness,Value
from beams_ec2.release import BeamsEC2App


class PDFReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=harness()

    def test_all_scopes_and_no_empty_pages(self):
        with tempfile.TemporaryDirectory() as folder:
            for scope in ['Resumo executivo','Relatório técnico','Memória de cálculo']:
                with self.subTest(scope=scope):
                    self.app.var_pdf_scope=Value(scope)
                    path=Path(folder)/'report.pdf'
                    self.app._write_pdf(str(path))
                    reader=PdfReader(path)
                    self.assertTrue(reader.pages)
                    for page in reader.pages:
                        self.assertGreater(len(page.extract_text().strip()),50)
                    text='\n'.join(page.extract_text() for page in reader.pages)
                    self.assertIn('BeamsEC2',text)
                    self.assertNotIn('m_pos_ed_kNm',text)
                    if scope=='Memória de cálculo':
                        self.assertIn('Combinações da armadura comum',text)
                        self.assertIn('reservada inferior',text)
                        self.assertIn('102 (C)',text)
                    if scope=='Relatório técnico':
                        self.assertIn('η corte/torção',text)
                        self.assertIn('102 (C)',text)

    def test_last_row_of_long_wide_table_is_exported(self):
        import pandas as pd
        from reportlab.lib.pagesizes import A4,landscape
        from reportlab.platypus import SimpleDocTemplate
        from beams_ec2.pdf_layout import flatten_tables
        frame=pd.DataFrame([dict(viga=f'V{i}',case='101',**{f'Campo {j}':f'R{i}C{j}' for j in range(10)}) for i in range(80)])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'table.pdf'
            table=self.app._pdf_df_table(frame,list(frame.columns),max_rows=None)
            SimpleDocTemplate(str(path),pagesize=landscape(A4),leftMargin=34,rightMargin=34).build(flatten_tables([table]))
            text='\n'.join(p.extract_text() for p in PdfReader(path).pages)
            self.assertIn('R79C9',text)
            self.assertIn('R0C0',text)


if __name__=='__main__':
    unittest.main()
