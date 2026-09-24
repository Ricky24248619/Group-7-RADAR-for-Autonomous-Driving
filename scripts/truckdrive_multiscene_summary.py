"""Aggregate paired support with scene-qualified identities and equal-scene sensitivity.

This is geometric support for released annotations, not a detector benchmark.
No frame-level independence or population confidence interval is assumed.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np

from audit_long_range_support import describe, one_per_instance
from compare_long_range_profiles import read_rows, profile
from compare_truckscenes_raw import write_csv

BANDS = ((100,150),(150,200),(200,250),(250,300),(300,400),(200,400))


def qualify(rows):
    """Track and sync IDs are only unique within a scene."""
    result=[]
    seen=set()
    for row in rows:
        row=dict(row)
        if row['instance_token'] in ('None','', 'null'):
            raise ValueError('Missing track identity')
        for field in ('annotation_token','instance_token','sample_token'):
            row[field]=row['scene']+':'+row[field]
        key=(row['annotation_token'],row['margin_m'])
        if key in seen:
            raise ValueError('Duplicate scene/annotation/margin')
        seen.add(key)
        result.append(row)
    return result


def matched(static,aligned):
    keys={(r['annotation_token'],r['margin_m']) for r in aligned}
    static=[r for r in static if (r['annotation_token'],r['margin_m']) in keys]
    reference={(r['annotation_token'],r['margin_m']):r for r in static}
    if set(reference)!=keys:
        raise ValueError('Static and aligned identities do not match')
    for row in aligned:
        other=reference[row['annotation_token'],row['margin_m']]
        if any(row[k]!=other[k] for k in ('scene','instance_token','range_m','category')):
            raise ValueError('Timing variants change annotation identity or geometry')
    return static


def scene_sensitivity(rows,threshold=1):
    groups=defaultdict(list)
    for row in rows:
        groups[row['scene']].append(row)
    summaries=[describe(group,threshold) for group in groups.values()]
    differences=[s['difference_pp'] for s in summaries]
    return dict(eligible_scenes=len(groups),
        lidar_wins=sum(d>0 for d in differences),radar_wins=sum(d<0 for d in differences),
        tied_scenes=sum(d==0 for d in differences),
        equal_scene_lidar_percent=float(np.mean([s['lidar_percent'] for s in summaries])),
        equal_scene_radar_percent=float(np.mean([s['radar_percent'] for s in summaries])),
        equal_scene_difference_pp=float(np.mean(differences)),
        min_scene_difference_pp=min(differences),max_scene_difference_pp=max(differences),
        leave_one_scene_out_min_pp=min(float(np.mean([d for j,d in enumerate(differences) if j!=i]))
            for i in range(len(differences))) if len(differences)>1 else None)


def equal_track_support(rows,threshold=1):
    groups=defaultdict(list)
    for row in rows:
        groups[row['instance_token']].append(row)
    summaries=[describe(group,threshold) for group in groups.values()]
    return {f'equal_track_{sensor}_percent':float(np.mean([s[f'{sensor}_percent'] for s in summaries]))
            for sensor in ('lidar','radar')}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-root',type=Path,required=True)
    parser.add_argument('--scenes',nargs='+',required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    output=args.output_dir;output.mkdir(parents=True,exist_ok=True)
    sources={};variants=defaultdict(list);scene_manifest=[]
    for scene in args.scenes:
        for variant in ('static','aligned'):
            folder=args.evidence_root/scene/variant
            path=folder/'object_counts.csv'
            sources[f'{scene}/{variant}/object_counts.csv']=hashlib.sha256(path.read_bytes()).hexdigest()
            rows=read_rows(path)
            if {r['scene'] for r in rows}!={scene}:
                raise ValueError('Scene labels do not match folder')
            variants[variant].extend(rows)
            manifest=json.loads((folder/'manifest.json').read_text())
            scene_manifest.append(dict(scene=scene,variant=variant,paired_frames=manifest['paired_frames'],
                observations=manifest['valid_object_observations'],min_range_m=manifest['min_range_m'],
                max_range_m=manifest['max_range_m'],max_abs_offset_ms=manifest['max_abs_timestamp_offset_ms']))
    variants={k:qualify(v) for k,v in variants.items()}
    variants['static']=matched(variants['static'],variants['aligned'])
    aggregates=[];by_scene=[];classes=[];first_tracks=[]
    predicates={'vehicles':lambda r:r['category'].startswith('Vehicle'),
        'passenger_cars':lambda r:r['category']=='Vehicle-Passenger',
        'forward_vehicles':lambda r:r['category'].startswith('Vehicle') and abs(float(r['azimuth_deg']))<=30,
        'all':lambda r:True}
    for variant,rows in variants.items():
        for margin in (0,.5):
            for low,high in BANDS:
                band=[r for r in rows if r['margin_m']==margin and low<=r['range_m']<high]
                for cohort,predicate in predicates.items():
                    group=[r for r in band if predicate(r)]
                    if not group:continue
                    keys=dict(variant=variant,margin_m=margin,band_m=f'{low}-{high}',cohort=cohort)
                    for threshold in (1,3,5):
                        aggregates.append(dict(**keys,threshold=threshold,**describe(group,threshold),
                            **scene_sensitivity(group,threshold),**equal_track_support(group,threshold)))
                        first_tracks.append(dict(**keys,threshold=threshold,**describe(one_per_instance(group),threshold)))
                    for scene in args.scenes:
                        subset=[r for r in group if r['scene']==scene]
                        if subset:by_scene.append(dict(**keys,scene=scene,**profile(subset)))
                for category in sorted({r['category'] for r in band}):
                    group=[r for r in band if r['category']==category]
                    classes.append(dict(variant=variant,margin_m=margin,band_m=f'{low}-{high}',category=category,**profile(group)))
    for name,rows in [('summary',aggregates),('by_scene',by_scene),('by_class',classes),('first_per_track',first_tracks),('scene_manifest',scene_manifest)]:
        write_csv(output/f'{name}.csv',rows)
    (output/'manifest.json').write_text(json.dumps(dict(scenes=args.scenes,input_sha256=sources,
        selection='Scene 1 retained from pilot, plus 6, 12, 18, 24 fixed before inspecting outcomes; not random or representative.',
        counting='Unique scene-qualified track and annotation IDs; static restricted to aligned annotation set; >= lower and < upper range.',
        unit='Percentage of released annotated object observations with at least the specified count of geometric in-box returns.',
        uncertainty='Scene ranges and leave-one-scene-out sensitivity, not population confidence intervals. Shared scene_28 prefix does not establish independent drives.',
        limitation='LiDAR-informed labels, unmatched hardware/FOV, unresolved joint-cloud deskew and no trained detectors.'),indent=2)+'\n')
    plot(by_scene,aggregates,output)
    for row in aggregates:
        if row['cohort']=='vehicles' and row['threshold']==1 and row['margin_m']==0:
            print(row['variant'],row['band_m'],row['observations'],row['instances'],row['eligible_scenes'],
                round(row['lidar_percent'],2),round(row['radar_percent'],2),
                'scene wins',row['lidar_wins'],row['radar_wins'],flush=True)


def plot(by_scene,aggregates,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    bands=[f'{a}-{b}' for a,b in BANDS[:-1]]
    for ax,variant in zip(axes,('static','aligned')):
        for scene in sorted({r['scene'] for r in by_scene}):
            rows=[r for r in by_scene if r['scene']==scene and r['variant']==variant and r['margin_m']==0
                  and r['cohort']=='vehicles' and r['band_m']!='200-400']
            if not rows:
                continue
            ax.plot([bands.index(r['band_m']) for r in rows],[r['difference_pp'] for r in rows],'-o',label=scene)
        ax.axhline(0,color='black',linewidth=1)
        ax.set(xticks=range(len(bands)),xticklabels=bands,ylabel='LiDAR minus radar support (percentage points)',
               xlabel='Vehicle box-centre planar distance (m)',title='Static calibration' if variant=='static' else 'Acquisition alignment hypothesis')
        ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Does greater LiDAR geometric support hold in each selected TruckDrive scene?')
    fig.text(.01,.015,'Exact boxes, >=1 return; same annotations for both timing variants. Positive favours LiDAR support.\n'
        'Scene 28_24: no eligible vehicles. Repeated observations; selected mini scenes; not detector accuracy.',fontsize=9)
    fig.tight_layout(rect=(0,.09,1,.94));fig.savefig(output/'scene_differences.png',dpi=160);plt.close(fig)


if __name__=='__main__':main()
