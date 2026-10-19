import unittest
import pandas as pd
from beams_ec2.case_selection import select_labels, select_elu_frame
from beams_ec2.release import _prepare_input_frames

class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame({'case':['101 (C)','102 (C)','201 (C)','302 (C)','1101 (C)'], 'value':[1,2,3,4,5]})

    def test_explicit_els_is_not_elu(self):
        selected=select_elu_frame(self.frame, '', '302')
        self.assertNotIn('302 (C)',set(selected['case']))
        self.assertEqual(len(selected),4)

    def test_list_ranges_and_exact_numbers(self):
        self.assertEqual(select_labels(self.frame['case'],'101-102 201;302'),set(self.frame['case'])-{'1101 (C)'})
        self.assertEqual(select_labels(self.frame['case'],'101'),{'101 (C)'})
        self.assertEqual(select_labels(self.frame['case'],'101 (C)'),{'101 (C)'})

    def test_elu_selection_preserves_rows(self):
        original=self.frame.copy(deep=True)
        pd.testing.assert_frame_equal(select_elu_frame(self.frame,'101-102','302'),self.frame.iloc[:2])
        pd.testing.assert_frame_equal(self.frame,original)

    def test_invalid_missing_overlap(self):
        for text in ('102-101','0','999','101junk','1-20000'):
            with self.subTest(text=text),self.assertRaises(ValueError):select_labels(self.frame['case'],text)
        with self.assertRaises(ValueError):select_elu_frame(self.frame,'101-102','102')

    def test_legacy_auto(self):
        f=pd.DataFrame({'case':['101 ELU','201 ELS QP']})
        self.assertEqual(select_elu_frame(f)['case'].tolist(),['101 ELU'])
        self.assertEqual(select_labels(f['case'],''),{'201 ELS QP'})

    def test_per_member_missing_case_is_allowed(self):
        self.assertEqual(select_labels(['101 (C)'],'302',False),set())

    def test_original_node_import_does_not_require_positions(self):
        raw=pd.DataFrame([{'Member/Node/Case':'1/15052/101 (C)','FZ (kN)':40,
              'MY (kNm)':60,'MX (kNm)':0,'Length (m)':6,'HY (cm)':30,'HZ (cm)':60,'Material':'C30/37'}])
        clean,env=_prepare_input_frames(raw)
        self.assertEqual(clean.node.iloc[0],'15052')
        self.assertTrue(clean.station.isna().all())
        self.assertEqual(len(select_elu_frame(env,'101','')),1)

    def test_point_labels_do_not_break_member_case_identity(self):
        from beams_ec2.base import split_member_case
        self.assertEqual(split_member_case('1/+/- MY x=0,33/302 (C)'),('1','+/- MY x=0,33','302 (C)'))
        raw=pd.DataFrame([{'Member/Point (m)/Case':'1/+/- MY x=0,33/101 (C)',
              'FZ (kN)':40,'MY (kNm)':60,'MX (kNm)':0,'Length (m)':6,
              'HY (cm)':30,'HZ (cm)':60,'Material':'C30/37'}])
        clean,env=_prepare_input_frames(raw)
        self.assertEqual(clean.member.iloc[0],'1')
        self.assertEqual(clean['case'].iloc[0],'101 (C)')
        self.assertTrue(clean.station.isna().all())
