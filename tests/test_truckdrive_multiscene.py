from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from truckdrive_multiscene_summary import qualify, matched, scene_sensitivity, equal_track_support
from truckdrive_paired_support import select_annotation_syncs


def row(scene,token='a',lidar=1,radar=0):
    return dict(scene=scene,annotation_token=token,instance_token='track1',sample_token=token,
                margin_m=0,range_m=220,category='Vehicle-Passenger',lidar_points=lidar,radar_points=radar)


class MultiSceneTests(unittest.TestCase):
    def test_reused_track_and_annotation_ids_remain_distinct_across_scenes(self):
        rows=qualify([row('s1'),row('s2')])
        self.assertEqual(len({r['instance_token'] for r in rows}),2)
        with self.assertRaises(ValueError):qualify([row('s1'),row('s1')])

    def test_equal_scene_result_does_not_let_long_track_dominate(self):
        rows=[row('s1',str(i)) for i in range(100)]+[row('s2',lidar=0,radar=1)]
        summary=scene_sensitivity(rows)
        self.assertEqual(summary['equal_scene_difference_pp'],0)
        self.assertEqual(summary['leave_one_scene_out_min_pp'],-100)
        self.assertEqual(summary['lidar_wins'],1)
        self.assertEqual(summary['radar_wins'],1)
        tracks=equal_track_support(qualify(rows))
        self.assertEqual(tracks['equal_track_lidar_percent'],50)
        self.assertEqual(tracks['equal_track_radar_percent'],50)

    def test_timing_matching_rejects_missing_or_changed_annotations(self):
        static=qualify([row('s1'),row('s2')]);aligned=qualify([row('s2')])
        self.assertEqual(len(matched(static,aligned)),1)
        with self.assertRaises(ValueError):matched(static,qualify([row('s3')]))
        with self.assertRaises(ValueError):matched(static,[dict(aligned[0],range_m=230)])

    def test_selection_uses_timestamp_order_before_sensor_availability(self):
        annotations={9:(0,None),2:(10,None),7:(20,None),5:(30,None),1:(40,None)}
        self.assertEqual(select_annotation_syncs(annotations,3),[9,7,1])
        self.assertEqual(select_annotation_syncs(annotations,None),[9,2,7,5,1])
        with self.assertRaises(ValueError):select_annotation_syncs(annotations,1)


if __name__=='__main__':unittest.main()
