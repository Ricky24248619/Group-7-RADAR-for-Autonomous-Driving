"""Independent full-cloud count cross-check; no tree or inside_box helper."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import numpy as np

from truckdrive_paired_support import frame_index, annotation_pose_interpolator

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root',type=Path,required=True)
    parser.add_argument('--evidence-root',type=Path,default=Path('docs/evidence/truckdrive-multiscene'))
    args=parser.parse_args()
    root=args.dataset_root
    evidence=args.evidence_root
    checks=[]
    for scene in json.loads((evidence/'summary/manifest.json').read_text())['scenes']:
        rawroot=root/scene
        annotations=frame_index(rawroot/'bounding_boxes')
        pose=annotation_pose_interpolator(annotations)
        for variant in ('static','aligned'):
            folder=evidence/scene/variant
            manifest=json.loads((folder/'manifest.json').read_text())
            counts=list(csv.DictReader((folder/'object_counts.csv').open()))
            frames=list(csv.DictReader((folder/'sensor_frames.csv').open()))
            syncs=sorted({int(r['sample_token']) for r in counts})
            selected=[syncs[0],syncs[len(syncs)//2],syncs[-1]]
            comparisons=0
            for sync in selected:
                stamp,path=annotations[sync];boxes=json.loads(path.read_text());clouds={'lidar':[],'radar':[]}
                for frame in [r for r in frames if int(r['sync'])==sync]:
                    sensor=frame['sensor'];timestamp=int(frame['timestamp_ns'])
                    _,path=frame_index(rawroot/sensor)[sync]
                    dtype,columns=('<f8',33) if frame['modality']=='radar' else ('<f8',11) if sensor.startswith('aeva') else ('<f4',7)
                    xyz=np.fromfile(path,dtype=dtype).reshape(-1,columns)[:,:3]
                    transform=np.array(manifest['transforms'][sensor]);xyz=xyz@transform[:3,:3].T+transform[:3,3]
                    if variant=='aligned':
                        transform=np.linalg.inv(pose(stamp))@pose(timestamp);xyz=xyz@transform[:3,:3].T+transform[:3,3]
                    clouds[frame['modality']].append(xyz)
                clouds={k:np.concatenate(v) for k,v in clouds.items()}
                observations=[r for r in counts if int(r['sample_token'])==sync and float(r['margin_m'])==0]
                # First three valid boxes plus first two long-range vehicles, before outcomes.
                chosen={r['annotation_token']:r for r in observations[:3]}
                for r in [r for r in observations if float(r['range_m'])>=200 and r['category'].startswith('Vehicle')][:2]:chosen[r['annotation_token']]=r
                for token,r in chosen.items():
                    box=boxes[int(token.split(':')[1])];center=np.array([box[k] for k in ('x','y','z')]);c,s=np.cos(box['yaw']),np.sin(box['yaw'])
                    for margin in (0,.5):
                        saved=next(q for q in counts if q['annotation_token']==token and float(q['margin_m'])==margin)
                        for modality,xyz in clouds.items():
                            d=xyz-center;local=np.column_stack((c*d[:,0]+s*d[:,1],-s*d[:,0]+c*d[:,1],d[:,2]))
                            count=int((np.abs(local)<=np.array([box['l'],box['w'],box['h']])/2+margin).all(axis=1).sum())
                            assert count==int(saved[modality+'_points']),(scene,variant,token,modality,count,saved)
                            comparisons+=1
            checks.append(dict(scene=scene,variant=variant,independent_counts_matched=comparisons))
            print('VERIFIED',scene,variant,comparisons,flush=True)
        # Check union once; static/aligned source files are substantially shared.
        manifests=[json.loads((evidence/scene/v/'manifest.json').read_text()) for v in ('static','aligned')]
        hashes={k:v for m in manifests for k,v in m['input_sha256'].items()}
        for name,expected in hashes.items():
            with (rawroot/name).open('rb') as handle:actual=hashlib.file_digest(handle,'sha256').hexdigest()
            assert actual==expected,(scene,name)
        print('HASHES',scene,len(hashes),flush=True)
        checks[-1]['source_files_rehashed']=len(hashes)
    (evidence/'verification.json').write_text(json.dumps(dict(checks=checks,total_independent_counts=sum(r['independent_counts_matched'] for r in checks),
        method='Full clouds with explicit sine/cosine box rotation; no KD-tree or inside_box helper. Calibration matrices and ego-pose interpolation shared with producer; not an independent timing validation.'),indent=2)+'\n')


if __name__=='__main__':
    main()
