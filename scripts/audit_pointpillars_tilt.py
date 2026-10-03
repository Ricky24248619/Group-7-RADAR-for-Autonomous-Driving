"""Audit saved PointPillars output vertical axes against TruckScenes mounting pose.

No inference and no correction of saved predictions. This diagnoses a frame
validity problem; it does not establish how much of a zero score it explains.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation


def tilt(rotation_wxyz):
    q=np.asarray(rotation_wxyz)
    up=Rotation.from_quat(q[[1,2,3,0]]).apply([0,0,1])
    return float(np.degrees(np.arccos(np.clip(up[2],-1,1))))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--metadata',type=Path,required=True);ap.add_argument('--predictions',type=Path,required=True)
    ap.add_argument('--output',type=Path,default=Path('docs/evidence/pr63-input-frame-audit.json'));args=ap.parse_args()
    load=lambda name:json.loads((args.metadata/(name+'.json')).read_text())
    sensors={s['token']:s for s in load('sensor')}
    calibrations=[c for c in load('calibrated_sensor') if sensors[c['sensor_token']]['channel']=='LIDAR_TOP_FRONT']
    predictions=json.loads(args.predictions.read_text())['results'];angles=[tilt(b['rotation']) for boxes in predictions.values() for b in boxes]
    gt=[tilt(b['rotation']) for b in load('sample_annotation') if b['sample_token'] in predictions]
    result=dict(prediction_sha256=hashlib.sha256(args.predictions.read_bytes()).hexdigest(),samples=len(predictions),boxes=len(angles),
        predicted_world_up_tilt_deg=dict(min=min(angles),median=float(np.median(angles)),max=max(angles)),
        annotated_world_up_tilt_deg=dict(min=min(gt),median=float(np.median(gt)),max=max(gt)),
        lidar_calibrations=[dict(token=c['token'],rotation_wxyz=c['rotation'],tilt_deg=tilt(c['rotation'])) for c in calibrations],
        conclusion='Tilted native LiDAR is fed directly to an upright-box checkpoint. Saved boxes inherit roughly 56 degree world-up tilt. Rectification and rerun required; nearest-centre matches do not validate input frame or quantify causal score impact.')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
