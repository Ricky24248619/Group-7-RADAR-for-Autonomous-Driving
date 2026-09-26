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

from stone_remote import RemoteFile, connect_sqlite

SOURCES = {
    'bag': ('1QImchBEanl1K1mkDW7i25hpOe8YpkZ6q', 84547784704),
    'zip': ('1LdzE-BqZeEr2Vc9_z1CfiY5IjdqvX_CN', 346343831255),
}
REVISION = '4ba5f700ddeb709a0e645bdd5fda082b0561d282'


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
    args = ap.parse_args()
    acquisition = args.root / 'acquisition'
    extracted = args.root / 'extracted'
    acquisition.mkdir(parents=True, exist_ok=True)
    extracted.mkdir(parents=True, exist_ok=True)
    remotes = {}
    for name, (ident, size) in SOURCES.items():
        source = dict(id=ident, size=size, url=source_url(ident))
        (acquisition / (name + '_source.json')).write_text(json.dumps(source))
        remotes[name] = RemoteFile(source, acquisition / (name + '-cache'))
    url = f'https://raw.githubusercontent.com/konyul/STONE/{REVISION}/README.md'
    with urllib.request.urlopen(url, timeout=45) as response:
        (acquisition / 'README-pinned.md').write_bytes(response.read())
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
    first = conn.execute('SELECT topic_id,timestamp FROM messages WHERE id=21373').fetchone()
    last = conn.execute('SELECT topic_id,timestamp FROM messages WHERE id=23153').fetchone()
    if first[0] != 13 or last[0] != 13:
        raise ValueError('Changed release row layout')
    samples = json.loads((extracted / 'sample.json').read_text())
    samples = sorted((s for s in samples if first[1]//1000 <= s['timestamp'] <= last[1]//1000), key=lambda s: s['timestamp'])
    if len(samples) != 1781 or len({s['timestamp'] for s in samples}) != 1781:
        raise ValueError('Unexpected recording sample count')
    (acquisition / 'pilot_samples.json').write_text(json.dumps(samples))
    conn.close()
    print('Ready: 1,781 candidate frames; acquisition selects 20 before scoring.')


if __name__ == '__main__':
    main()
