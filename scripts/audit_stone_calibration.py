"""Record the inspected STONE calibration evidence without inventing transforms."""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_stone_pilot import RECORDINGS, recording_root


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('docs/evidence/stone-environments/calibration_audit.json'))
    args=parser.parse_args();root=args.root;hashes={}
    def read(relative):
        path=root/relative
        data=path.read_bytes();hashes[str(relative).replace('\\','/')]=hashlib.sha256(data).hexdigest()
        return json.loads(data)
    index=read(Path('acquisition/zip_index.json'))
    candidates=[r['name'] for r in index if any(k in r['name'].lower() for k in ('radar','calib','extrin','yaml','urdf','config'))]
    sensors=read(Path('extracted/sensor.json'))
    calibrated=read(Path('extracted/calibrated_sensor.json'))
    channels={r['token']:r['channel'] for r in sensors}
    calibrations=[dict(channel=channels[r['sensor_token']],translation=r['translation'],rotation=r['rotation']) for r in calibrated]
    bag_transforms={}
    for name in RECORDINGS:
        path=(recording_root(root,name)/'paired-pilot/transforms.json').relative_to(root)
        bag_transforms[name]=[r for r in read(path) if r['child_frame_id'].startswith('ARS_')]
    audit=dict(archive_entries=len(index),candidate_calibration_names=candidates,
               exported_calibrations=calibrations,bag_radar_transforms=bag_transforms,input_sha256=hashes,
               conclusion='No physical radar mounting translation found in these inspected sources. Zero ROS translations are not independently validated mounting measurements.',
               paper='https://arxiv.org/html/2603.09175v1#S3.SS2',
               required='Numerical calibrated radar-to-LiDAR rigid transforms for each ARS548, transform direction, axes, units, and whether published detections were already transformed.',
               limits='Filename audit cannot exclude unnamed or external calibration files. This does not claim calibration was never performed.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(dict(archive_entries=len(index),candidate_names=candidates,exported_channels=list(channels.values()))))


if __name__=='__main__':main()
