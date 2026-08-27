#!/usr/bin/env python3
"""List the topics in a GOOSE ROS bag, and say whether radar is among them.

Answers the open question in docs/dataset-surveys/goose.md: the paper documents six
Smartmicro radars on MuCAR-3, but the annotated splits ship LiDAR and labels only, so
radar can only be in the raw bags. The maintainers have said the released bags carry a
reduced sensor set (FraunhoferIOSB/goose_dataset#17), so this has to be checked rather
than assumed.

Uses rosbags rather than a ROS installation, so it runs on macOS:
    pip install rosbags

Usage:
    python3 goose_bag_topics.py /path/to/sequence.bag
    python3 goose_bag_topics.py /path/to/bags/          # a directory of bags
"""

import argparse
import pathlib
import sys

from rosbags.highlevel import AnyReader

# Substrings that would indicate a radar stream. GOOSE topics are namespaced like
# /sensor/<modality>/<position>/..., so a bare "radar" match is the reliable signal.
RADAR_HINTS = ("radar", "umrr", "smartmicro")


def report(path):
    with AnyReader([path]) as reader:
        print(f"\n=== {path.name} ===")
        print(f"Bag version : {'ROS 1' if path.suffix == '.bag' else 'ROS 2'}")
        print(f"Messages    : {reader.message_count:,}")
        if reader.duration:
            print(f"Duration    : {reader.duration / 1e9:.1f} s")

        conns = sorted(reader.connections, key=lambda c: c.topic)
        print(f"Topics      : {len(conns)}\n")
        width = max((len(c.topic) for c in conns), default=10)
        for c in conns:
            print(f"  {c.topic:<{width}}  {c.msgtype:<44} {c.msgcount:>8,}")

        radar = [c.topic for c in conns
                 if any(h in c.topic.lower() for h in RADAR_HINTS)]
        print()
        if radar:
            print(f"RADAR PRESENT — {len(radar)} topic(s):")
            for t in radar:
                print(f"    {t}")
        else:
            print("NO RADAR TOPICS in this bag.")
            print("    Consistent with the maintainers' statement that released bags")
            print("    carry a reduced sensor set. Record this in the survey and ask")
            print("    when the full raw data lands.")
        return bool(radar)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="A .bag file, or a directory containing bags")
    args = ap.parse_args()

    path = pathlib.Path(args.path).expanduser()
    if not path.exists():
        sys.exit(f"Not found: {path}")

    bags = sorted(path.glob("*.bag")) if path.is_dir() else [path]
    if not bags:
        sys.exit(f"No .bag files under {path}")

    found = [report(b) for b in bags]
    print(f"\n{'=' * 60}")
    print(f"{len(bags)} bag(s) inspected · radar found in {sum(found)}")


if __name__ == "__main__":
    main()
