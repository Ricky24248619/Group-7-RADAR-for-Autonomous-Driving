"""Fetch only matching camera frames from the official GOOSE 2D validation ZIP."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from PIL import Image
from stone_remote import RemoteFile

SOURCE=dict(id='goose-2d-val-20250318',size=2857251081,
            url='https://goose-dataset.de/storage/goose_2d_val.zip?diagnostic=20260928')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--selection',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    selection=json.loads(args.selection.read_text());remote=RemoteFile(SOURCE,args.output/'zip-cache')
    rows=[]
    with zipfile.ZipFile(remote) as archive:
        names=archive.namelist()
        for entry in selection['inputs']:
            # Frame number/scenario pairs link camera and LiDAR frames; retain
            # both timestamps to expose any inter-sensor acquisition difference.
            prefix=entry['frame'].split('_vls128')[0]
            key=prefix.split('__')[1].split('_')[0]
            hits=[n for n in names if entry['scenario']+'__'+key+'_' in n and n.endswith('_windshield_vis.png')]
            if len(hits)!=1:raise ValueError(f'Camera frame not unique: {entry["frame"]}: {hits}')
            name=hits[0];data=archive.read(name) # zipfile verifies member CRC
            target=args.output/Path(name).name;target.write_bytes(data)
            with Image.open(target) as im:
                dimensions=im.size;im.verify()
            rows.append(dict(lidar_frame=entry['frame'],archive_member=name,filename=target.name,
                             sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),dimensions=dimensions))
    (args.output/'manifest.json').write_text(json.dumps(dict(source=SOURCE,selection_sha256=hashlib.sha256(args.selection.read_bytes()).hexdigest(),images=rows),indent=2)+'\n')
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
