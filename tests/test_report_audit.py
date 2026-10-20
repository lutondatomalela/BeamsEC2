import unittest
from tests.test_reuse import fixture
from beams_ec2.release import BeamsEC2App,_prepare_input_frames
from beams_ec2.advanced import _apply_serviceability_advanced

class ReportAuditTests(unittest.TestCase):
    def test_node_labels_are_not_reported_as_metres_and_deflection_is_suppressed(self):
        app,row=fixture()
        raw=app.df_clean.copy();raw['station']=float('nan');raw['node']='15123'
        clean,env=_prepare_input_frames(raw)
        self.assertEqual(env.v_at.iloc[0],'Nó 15123')
        app.df_clean=clean
        result=_apply_serviceability_advanced(app,row)
        for key in ('m_pos_at','m_neg_at','v_at','t_at'):result[key]='Nó 15123'
        memory=BeamsEC2App._memory_for_report(result)
        forces=memory[memory.Etapa=='Esforços']
        self.assertTrue((forces['Estado/Nota']=='Nó 15123').all())
        deflection=memory[memory.Item.str.startswith('Flecha')]
        self.assertTrue((deflection.Valor=='Não verificada').all())
        self.assertIn('Governantes tensões aço / betão',set(memory.Item))
        self.assertIn('304 (C) / 304 (C)',set(memory.Valor))

    def test_station_remains_dimensional(self):
        app,row=fixture()
        self.assertEqual(row.v_at.iloc[0],'0.0')
        memory=BeamsEC2App._memory_for_report(row)
        value=memory.loc[(memory.Etapa=='Esforços') & (memory.Item=='VEd'),'Estado/Nota'].iloc[0]
        self.assertEqual(value,'x=0.0 m')
