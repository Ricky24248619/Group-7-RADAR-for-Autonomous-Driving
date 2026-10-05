"""Acquire bounded ZIP members for two preselected, previously unexamined clips.

Uses the project's existing TruckDrive noncommercial research terms. No full ZIP
download; same eight evenly spaced annotation timestamps selected before scoring.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import struct
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
import zlib

BASE = "https://d3ehgyu1hepsur.cloudfront.net/"
NS = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}
SCENES = ("scene_28_3", "scene_28_15")
MAX_COMPRESSED = 400 * 1024 * 1024


def read(url, headers=None):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=45) as response:
        return response.read()


def fetch(row, start, end):
    if not 0 <= start <= end < row["size"]:
        raise ValueError("Invalid ZIP range")
    for attempt in range(3):
        try:
            request = urllib.request.Request(BASE + row["key"], headers={"Range": f"bytes={start}-{end}"})
            with urllib.request.urlopen(request, timeout=45) as response:
                if response.status != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{row['size']}":
                    raise ValueError("Server did not honour exact bounded range")
                data = response.read(end - start + 2)
            if len(data) != end - start + 1:
                raise ValueError("Incomplete ZIP range")
            return data
        except Exception:
            if attempt == 2:
                raise


class RemoteZip(io.RawIOBase):
    def __init__(self, row):
        self.row, self.position = row, 0
    def seekable(self):
        return True
    def readable(self):
        return True
    def tell(self):
        return self.position
    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.row["size"] + offset
        return self.position
    def read(self, size=-1):
        size = min(self.row["size"] - self.position, self.row["size"] if size < 0 else size)
        if size <= 0:
            return b""
        data = fetch(self.row, self.position, self.position + size - 1)
        self.position += size
        return data


def member(row, info, directory):
    path = (directory / info.filename).resolve()
    if not path.is_relative_to(directory.resolve()):
        raise ValueError("Unsafe ZIP path")
    if path.exists():
        data = path.read_bytes()
        if len(data) != info.file_size or zlib.crc32(data) != info.CRC:
            raise ValueError("Existing input changed")
    else:
        header = fetch(row, info.header_offset, info.header_offset + 29)
        if header[:4] != b"PK\x03\x04":
            raise ValueError("Invalid local ZIP header")
        name_length, extra_length = struct.unpack_from("<HH", header, 26)
        start = info.header_offset + 30 + name_length + extra_length
        payload = fetch(row, start, start + info.compress_size - 1)
        if info.compress_type == zipfile.ZIP_DEFLATED:
            data = zlib.decompress(payload, -15)
        elif info.compress_type == zipfile.ZIP_STORED:
            data = payload
        else:
            raise ValueError("Unsupported ZIP compression")
        if len(data) != info.file_size or zlib.crc32(data) != info.CRC:
            raise ValueError("ZIP member length/CRC mismatch")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return dict(member=info.filename, bytes=len(data), compressed_bytes=info.compress_size,
                crc32=info.CRC, sha256=hashlib.sha256(data).hexdigest())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    repo = Path(__file__).resolve().parents[1]
    if args.root.resolve().is_relative_to(repo):
        raise ValueError("Raw data must remain outside Git")
    record = dict(scenes=SCENES, frames_per_scene=8, archives=[], selected_syncs={},
                  selection="Clips 28_3 and 28_15 fixed before scoring; eight evenly spaced annotation timestamps per clip, rounded interior-inclusive endpoints",
                  source=BASE, max_compressed_member_bytes=MAX_COMPRESSED)
    total = 0
    args.output.mkdir(parents=True, exist_ok=True)
    for scene in SCENES:
        directory = args.root / scene
        listing = read(BASE + "?prefix=TruckDrive/" + scene + "/&delimiter=")
        (args.output / (scene + "-listing.xml")).write_bytes(listing)
        rows = [dict(key=node.find("s:Key", NS).text, size=int(node.find("s:Size", NS).text))
                for node in ET.fromstring(listing).findall("s:Contents", NS)]
        for modality in ("calibrations", "annotations", "radar", "lidar"):
            row = next(row for row in rows if row["key"].endswith("/" + modality + ".zip"))
            with zipfile.ZipFile(RemoteZip(row)) as archive:
                infos = [info for info in archive.infolist() if not info.is_dir()]
            if modality in ("radar", "lidar"):
                annotations = sorted((int(p.stem.split("_")[1]), int(p.stem.split("_")[0]))
                                     for p in (directory / "bounding_boxes").glob("*.json"))
                if len(annotations) < 8:
                    raise ValueError("Insufficient annotation timestamps")
                syncs = {annotations[round(i * (len(annotations)-1)/7)][1] for i in range(8)}
                record["selected_syncs"][scene] = sorted(syncs)
                infos = [info for info in infos if info.filename.endswith(".bin") and int(Path(info.filename).stem.split("_")[0]) in syncs]
            total += sum(info.compress_size for info in infos)
            if total > MAX_COMPRESSED:
                raise ValueError("Predetermined acquisition exceeds 400 MiB cap; no further members downloaded")
            with ThreadPoolExecutor(max_workers=4) as pool:
                verified = list(pool.map(lambda info: member(row, info, directory), infos))
            record["archives"].append(dict(scene=scene, modality=modality, **row, members=verified))
            record["compressed_member_bytes"] = total
            (args.output / "acquisition.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
            print(scene, modality, len(verified), "verified members", "cumulative compressed bytes", total, flush=True)
    record["complete"] = True
    (args.output / "acquisition.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
