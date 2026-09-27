"""Prepare the first farmland STONE pilot without downloading whole archives.

Uses the public download-confirmation form and exact HTTP byte ranges. Source
IDs and sizes are fixed to this release; changed files fail the range checks.
"""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.parse
import urllib.request
import zipfile
import zlib
import yaml

from stone_remote import RemoteFile, connect_sqlite

SOURCES = {
    'bag': ('1QImchBEanl1K1mkDW7i25hpOe8YpkZ6q', 84547784704),
    'zip': ('1LdzE-BqZeEr2Vc9_z1CfiY5IjdqvX_CN', 346343831255),
}
REVISION = '4ba5f700ddeb709a0e645bdd5fda082b0561d282'
RECORDINGS = {
    'farmland': ('1QImchBEanl1K1mkDW7i25hpOe8YpkZ6q',84547784704,'1BNEDR2MK7J-zA9hlaU2Fe-5-K1hDF4k9',1781),
    'lake': ('1J1m17ZF-8VQzPF6Vj0PJtxGqwn33o9G5',123495927808,'1KPq8cBU_tWpc8nLssNFblqTB32lC-69s',2601),
    'land': ('1mI_zW9H6W0qlXBN9ROKGH_DerLmplgoL',28632473600,'1MWbZPIWICEJLm6DjQuyzufuyFYy999v5',603),
}


def recording_root(root, name):
    return root if name == 'farmland' else root/'recordings'/name


def inspect_layout(conn, counts):
    # ponytail: these releases group rows by topic. Check boundaries here and
    # every extracted row downstream; a different storage layout needs an index.
    start=1; layout=[]
    for ident, topic in conn.execute('SELECT id,name FROM topics ORDER BY id'):
        count=counts[topic]
        if count<1:raise ValueError('Empty topic is unsupported by this release adapter')
        end=start+count-1
        boundaries=list(conn.execute('SELECT id,topic_id,timestamp FROM messages WHERE id IN (?,?) ORDER BY id',(start,end)))
        if len(boundaries)!=(1 if start==end else 2) or any(r[1]!=ident for r in boundaries):
            raise ValueError('Changed topic-grouped release layout')
        layout.append(dict(topic=topic,topic_id=ident,start=start,end=end,count=count,first_ns=boundaries[0][2],last_ns=boundaries[-1][2]))
        start=end+1
    return layout


class DownloadForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.action = None
        self.fields = {}
        self.active = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            self.active = attrs.get('id') == 'download-form'
            if self.active:
                self.action = attrs.get('action')
        if tag == 'input' and self.active and attrs.get('name'):
            self.fields[attrs['name']] = attrs.get('value', '')

    def handle_endtag(self, tag):
        if tag == 'form':
            self.active = False


def source_url(ident):
    url = 'https://drive.google.com/uc?export=download&id=' + ident
    with urllib.request.urlopen(url, timeout=45) as response:
        if 'text/html' not in response.headers.get('Content-Type', ''):
            return response.url
        parser = DownloadForm()
        parser.feed(response.read(1_000_000).decode('utf-8'))
    if parser.action != 'https://drive.usercontent.google.com/download':
        raise ValueError('Expected public Google Drive download form')
    if parser.fields.get('id') != ident:
        raise ValueError('Unexpected download identity')
    return parser.action + '?' + urllib.parse.urlencode(parser.fields)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--recording',choices=RECORDINGS,default='farmland')
    args = ap.parse_args()
    acquisition = recording_root(args.root,args.recording) / 'acquisition'
    extracted = args.root / 'extracted'
    acquisition.mkdir(parents=True, exist_ok=True)
    extracted.mkdir(parents=True, exist_ok=True)
    remotes = {}
    sources=dict(SOURCES,bag=RECORDINGS[args.recording][:2])
    for name, (ident, size) in sources.items():
        source = dict(id=ident, size=size, url=source_url(ident))
        cache_root=args.root/'acquisition' if name=='zip' else acquisition
        cache_root.mkdir(parents=True,exist_ok=True)
        (cache_root / (name + '_source.json')).write_text(json.dumps(source))
        remotes[name] = RemoteFile(source, cache_root / (name + '-cache'))
    url = f'https://raw.githubusercontent.com/konyul/STONE/{REVISION}/README.md'
    with urllib.request.urlopen(url, timeout=45) as response:
        (args.root / 'acquisition/README-pinned.md').write_bytes(response.read())
    with zipfile.ZipFile(remotes['zip']) as archive:
        for name in ('scene', 'sample', 'sample_data', 'ego_pose', 'calibrated_sensor'):
            member = 'STONE_nus_dataset/v1.0-trainval/' + name + '.json'
            info = archive.getinfo(member)
            path = extracted / (name + '.json')
            data = path.read_bytes() if path.exists() else archive.read(member)
            if len(data) != info.file_size or zlib.crc32(data) != info.CRC:
                raise ValueError('Metadata CRC mismatch: ' + name)
            if not path.exists():
                path.write_bytes(data)
    conn, vfs = connect_sqlite(remotes['bag'])
    metadata_id=RECORDINGS[args.recording][2]
    with urllib.request.urlopen('https://drive.google.com/uc?export=download&id='+metadata_id,timeout=45) as response:
        metadata=response.read(1_000_000)
    (acquisition/'metadata.yaml').write_bytes(metadata)
    info=yaml.safe_load(metadata)['rosbag2_bagfile_information']
    counts={r['topic_metadata']['name']:r['message_count'] for r in info['topics_with_message_count']}
    layout=inspect_layout(conn,counts)
    (acquisition/'layout.json').write_text(json.dumps(layout,indent=2))
    lidar=next(r for r in layout if r['topic']=='/lidar_points')
    samples = json.loads((extracted / 'sample.json').read_text())
    samples = sorted((s for s in samples if lidar['first_ns']//1000 <= s['timestamp'] <= lidar['last_ns']//1000), key=lambda s: s['timestamp'])
    expected=RECORDINGS[args.recording][3]
    if len(samples) != expected or len({s['timestamp'] for s in samples}) != expected:
        raise ValueError('Unexpected recording sample count')
    (acquisition / 'pilot_samples.json').write_text(json.dumps(samples))
    conn.close()
    print(f'Ready: {len(samples)} candidate frames; acquisition selects 20 before scoring.')


if __name__ == '__main__':
    main()
