import io
import csv
from collections import defaultdict
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from stone_remote import RemoteFile
from acquire_stone_pilot import stamp_ns, xyz_cloud
from prepare_stone_pilot import DownloadForm
try:
    from compare_stone_terrain import reference_groups, matrix, transform, angular_roi
    GEOMETRY = True
except ModuleNotFoundError as error:
    if error.name != 'scipy':
        raise
    GEOMETRY = False


class RemoteTests(unittest.TestCase):
    def test_ranges_cache_integrity_and_eof(self):
        payload = b'abcdefghij'
        def open_range(request, timeout):
            start, end = map(int, request.headers['Range'][6:].split('-'))
            response = io.BytesIO(payload[start:end+1])
            response.status = 206
            response.headers = {'Content-Range': f'bytes {start}-{end}/10'}
            return response
        with tempfile.TemporaryDirectory() as directory, patch('urllib.request.urlopen', side_effect=open_range) as fetch:
            source = dict(id='test', size=10, url='https://example.test/?id=test')
            remote = RemoteFile(source, directory, block_size=4)
            remote.seek(3)
            self.assertEqual(remote.read(6), b'defghi')
            self.assertEqual(remote.read(), b'j')
            remote.seek(100)
            self.assertEqual(remote.read(), b'')
            self.assertEqual(fetch.call_count, 3)
            self.assertEqual(remote.read_at(0, 4), b'abcd')
            (Path(directory)/'000000000.bin').write_bytes(b'xxxx')
            with self.assertRaisesRegex(ValueError, 'Corrupt'):
                remote.read_at(0, 1)
            with self.assertRaisesRegex(ValueError, 'different'):
                RemoteFile(dict(source, size=11), directory, block_size=4)

    def test_ignored_range_is_rejected_without_cache_write(self):
        def response(*args, **kwargs):
            result = io.BytesIO(b'abcd')
            result.status = 200
            result.headers = {}
            return result
        with tempfile.TemporaryDirectory() as directory, patch('urllib.request.urlopen', side_effect=response), patch('time.sleep'):
            remote = RemoteFile(dict(id='test', size=4, url='https://example.test/?x=1'), directory, 4)
            with self.assertRaisesRegex(ValueError, 'exact requested'):
                remote.read()
            self.assertFalse(list(Path(directory).glob('*.bin')))

    def test_download_form_does_not_mix_other_forms(self):
        form = DownloadForm()
        form.feed('<form id="other"><input name="id" value="bad"></form><form id="download-form" action="https://drive.usercontent.google.com/download"><input name="id" value="good"><input name="uuid" value="a&amp;b"></form>')
        self.assertEqual(form.fields, {'id':'good', 'uuid':'a&b'})


class CloudTests(unittest.TestCase):
    def test_organized_padded_big_endian_cloud(self):
        data = bytearray(64)
        dtype = np.dtype({'names':['x','y','z'], 'formats':['>f4']*3, 'offsets':[0,4,8], 'itemsize':12})
        view = np.ndarray((2,2), dtype=dtype, buffer=data, strides=(32,12))
        for i, key in enumerate('xyz'):
            view[key] = np.arange(4).reshape(2,2)+i*10
        msg = NS(is_bigendian=True, fields=[NS(name=k,count=1,datatype=7,offset=i*4) for i,k in enumerate('xyz')], row_step=32, width=2, point_step=12, height=2, data=data)
        np.testing.assert_array_equal(xyz_cloud(msg), np.array([[0,10,20],[1,11,21],[2,12,22],[3,13,23]]))
        msg.row_step=23
        with self.assertRaises(ValueError):xyz_cloud(msg)

    def test_timestamp_preserves_nanoseconds(self):
        self.assertEqual(stamp_ns(NS(sec=1756349763,nanosec=912072897)),1756349763912072897)


class EvidenceTests(unittest.TestCase):
    def test_committed_counts_partition_and_reaggregate(self):
        root=Path(__file__).resolve().parents[1]/'docs/evidence/stone-pilot'
        with (root/'support_by_frame.csv').open(newline='') as file:
            rows=list(csv.DictReader(file))
        aggregated=defaultdict(lambda: [0,0,0,0])
        seen=set()
        for row in rows:
            key=tuple(row[k] for k in ('variant','elevation_deg','band_m','group','tolerance_m'))
            self.assertNotIn((row['frame'],key),seen);seen.add((row['frame'],key))
            n,l,r,both,neither=[int(row[k]) for k in ('reference_voxels','lidar_supported','radar_supported','both','neither')]
            self.assertGreater(n,0)
            self.assertTrue(0<=both<=min(l,r)<=max(l,r)<=n)
            self.assertEqual(l+r-both+neither,n)
            for i,value in enumerate((1,n,l,r)):aggregated[key][i]+=value
        with (root/'support_summary.csv').open(newline='') as file:
            summaries=list(csv.DictReader(file))
        self.assertEqual(len(summaries),len(aggregated))
        for row in summaries:
            key=tuple(row[k] for k in ('variant','elevation_deg','band_m','group','tolerance_m'))
            count,n,l,r=aggregated[key]
            self.assertEqual([int(row[k]) for k in ('frames','reference_voxels','lidar_supported','radar_supported')],[count,n,l,r])
            self.assertAlmostEqual(float(row['lidar_percent']),100*l/n)
            self.assertAlmostEqual(float(row['radar_percent']),100*r/n)


@unittest.skipUnless(GEOMETRY, 'Optional STONE scipy dependency')
class GeometryTests(unittest.TestCase):
    def test_collinear_ground_cannot_determine_a_plane(self):
        labels=np.full((200,200,16),255,np.uint8)
        labels[94:107,100,8]=1
        labels[100,102,11]=3
        refs,groups,heights=reference_groups(labels)
        self.assertTrue(np.isnan(heights).all())
        self.assertFalse(groups['raised_geometry'].any())

    def test_local_ground_not_global_height_and_unknown_excluded(self):
        labels = np.full((200,200,16),255,np.uint8)
        labels[94:107,94:107,8]=1  # surface 2.4 m above the grid origin's z=0
        labels[100,100,11]=3       # 1.2 m above that surface
        labels[180,180,11]=3      # no nearby ground: unresolved
        labels[110,110,8]=0       # free space is not ground
        refs, groups, heights = reference_groups(labels)
        self.assertEqual(len(refs),171)
        self.assertEqual(groups['raised_geometry'].sum(),1)
        self.assertEqual(groups['near_ground_geometry'].sum(),169)
        self.assertTrue(np.isnan(heights[-1]))

    def test_transform_inverse_and_angular_exclusions(self):
        t = matrix([0,0,np.sqrt(.5),np.sqrt(.5)],[1,2,3])
        p = np.array([[5,0,0],[5,0,5],[-5,0,0],[50,0,0]])
        world = transform(p,t)
        np.testing.assert_allclose(transform(world,np.linalg.inv(t)),p,atol=1e-12)
        np.testing.assert_array_equal(angular_roi(world,[t],10),[True,False,False,False])


if __name__ == '__main__':unittest.main()
