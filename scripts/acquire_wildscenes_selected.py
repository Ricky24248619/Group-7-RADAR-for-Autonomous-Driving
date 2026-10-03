"""Download the five selected WildScenes XYZ/label pairs, within explicit limits.

No authentication needed. Signed download URLs stay in memory and are not logged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir',type=Path,required=True,help='External local data/audit directory')
parser.add_argument('--selection',type=Path,default=Path(__file__).resolve().parents[1]/'results/evidence/p3-p4-oct03/wildscenes_selection.json')
args = parser.parse_args()
ROOT = args.output_dir
ROOT.mkdir(parents=True,exist_ok=True)
selection_bytes = args.selection.read_bytes()
target_selection = ROOT/'X1-selection.json'
if target_selection.exists() and target_selection.read_bytes()!=selection_bytes:
    raise ValueError('Output directory contains a different selection')
target_selection.write_bytes(selection_bytes)
BASE = 'https://data.csiro.au/dap/ws/v2/collections/61541/data'
selection = json.loads((ROOT/'X1-selection.json').read_text())
if len(selection)!=5 or len({r['id'] for r in selection})!=5:
    raise ValueError('Expected five unique frozen frame IDs')
for row in selection:
    for key in ('lidar_path','label_path'):
        path = Path(row[key])
        if path.is_absolute() or '..' in path.parts or path.parts[0]!='WildScenes3d':
            raise ValueError('Unsafe selected relative path')
wanted = {'WildScenes/'+r[k] for r in selection for k in ('lidar_path','label_path')}
found = {}
decoder = json.JSONDecoder()
read_bytes = 0
buffer = ''
started = False
with urllib.request.urlopen(BASE, timeout=30) as response:
    while wanted - found.keys():
        chunk = response.read(262144)
        if not chunk:
            break
        read_bytes += len(chunk)
        if read_bytes > 200_000_000:
            raise ValueError('Metadata listing exceeds 200 MB cap')
        buffer += chunk.decode('utf-8')
        if not started:
            match = re.search(r'"file"\s*:\s*\[', buffer)
            if not match:
                continue
            buffer = buffer[match.end():]
            started = True
        while True:
            buffer = buffer.lstrip(' \r\n\t,')
            if not buffer or buffer.startswith(']'):
                break
            try:
                entry, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                break
            buffer = buffer[end:]
            if entry['filename'] in wanted:
                found[entry['filename']] = entry
                print('Resolved', entry['filename'], entry['fileSize'], flush=True)
        if read_bytes % 5_242_880 == 0:
            print('Metadata scanned', read_bytes, 'bytes;', len(found), 'inputs', flush=True)

if found.keys() != wanted:
    raise ValueError('Frozen inputs absent from collection: '+str(sorted(wanted-found.keys())))
total = sum(int(r['fileSize']) for r in found.values())
if total > 50_000_000 or any(not 0 < int(r['fileSize']) <= 10_000_000 for r in found.values()):
    raise ValueError('Frozen selection exceeds raw resource limit')
manifest = {'collection':61541, 'listing_bytes_scanned':read_bytes, 'raw_total_bytes':total,
            'selection_sha256':hashlib.sha256((ROOT/'X1-selection.json').read_bytes()).hexdigest(), 'inputs':[]}
for name, entry in sorted(found.items()):
    target = ROOT/'raw-wildscenes'/name.removeprefix('WildScenes/')
    target.parent.mkdir(parents=True, exist_ok=True)
    size = int(entry['fileSize'])
    if not target.exists():
        with urllib.request.urlopen(entry['presignedLink']['href'], timeout=30) as response:
            data = response.read(size+1)
        if len(data) != size:
            raise ValueError('Incomplete/oversized selected input: '+name)
        target.write_bytes(data)
    if target.stat().st_size != size:
        raise ValueError('Stored size mismatch')
    manifest['inputs'].append({'filename':name.removeprefix('WildScenes/'), 'file_id':entry['id'],
                              'bytes':size, 'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                              'source':entry['link']['href']})
    print('Verified', target.name, size, flush=True)
(ROOT/'X1-acquisition.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('Acquired', total, 'bytes in', len(found), 'files')
commit = '9eb4e10b4483a634159e2b371be0437e465fe218'
sources = {
    'wildscenes_view.txt':f'https://raw.githubusercontent.com/csiro-robotics/WildScenes/{commit}/scripts/visualisation/view_cloud.py',
    'wildscenes_config.txt':f'https://raw.githubusercontent.com/csiro-robotics/WildScenes/{commit}/wildscenes/configs3d/_base_/datasets/wildscenes.py',
    'wildscenes_utils3d.py':f'https://raw.githubusercontent.com/csiro-robotics/WildScenes/{commit}/wildscenes/tools/utils3d.py',
    'collection_api.txt':'https://data.csiro.au/dap/ws/v2/collections/61541'}
audit = ROOT/'source-audit';audit.mkdir(exist_ok=True)
for name,url in sources.items():
    target = audit/name
    if not target.exists():
        with urllib.request.urlopen(url,timeout=30) as response:data=response.read(100001)
        if len(data)>100000:raise ValueError('Oversized author source')
        target.write_bytes(data)
