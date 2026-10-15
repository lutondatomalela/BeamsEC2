import unittest
import pandas as pd
from beams_ec2.release import _prepare_input_frames
from beams_ec2.base import split_member_case
from tests.test_robustness import sample

class RobotPositionsTests(unittest.TestCase):
    def test_point_labels_and_slashes(self):
        labels=['user x= 0,0', '+/- MZ x=0,33', 'auto x=1,20 (-)', 'origin (15)', 'end (16)']
        f=pd.concat([sample().drop(columns='Station (m)').rename(columns={'Member/Node/Case':'Member/Point (m)/Case'}).assign(**{'Member/Point (m)/Case':f'1/{label}/101 (C)'}) for label in labels],ignore_index=True)
        c,_=_prepare_input_frames(f)
        self.assertEqual(c.station.tolist(),[0,.33,1.2,0,6])
        self.assertEqual(set(c['case']),{'101 (C)'})
        self.assertEqual(split_member_case('1/+/- MZ x=0,33/101 (C)')[1],'+/- MZ x=0,33')

    def test_nodes_have_no_invented_positions(self):
        c,_=_prepare_input_frames(sample().drop(columns='Station (m)'))
        self.assertTrue(c.station.isna().all())
        self.assertEqual(c.station_source.iloc[0],'nó sem posição')

    def test_invalid_explicit_position_rejected(self):
        for value in ['bad',float('nan')]:
            with self.assertRaises(ValueError):
                _prepare_input_frames(sample(**{'Station (m)':value}))

    def test_unknown_point_rejected(self):
        f=sample().drop(columns='Station (m)')
        f['Member/Node/Case']='1/user x=bad/101 (C)'
        with self.assertRaises(ValueError):_prepare_input_frames(f)
