"""Which annotated object classes have no in-box returns, by distance?

Reuses verified paired counts. Does not run or score a detector. Native class
labels and datasets remain separate; repeated tracks are not independent trials.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np
from compare_long_range_profiles import read_rows, profile
from compare_truckscenes_raw import write_csv
from truckdrive_multiscene_summary import qualify, matched

BANDS = ((0,25),(25,50),(50,75),(75,100),(100,150),(150,200),(200,250),(250,300),(300,400))


def breakdown(rows):
    result = profile(rows)
    for sensor in ('lidar','radar'):
        result[sensor+'_unsupported'] = sum(r[sensor+'_points']==0 for r in rows)
        result[sensor+'_missing_percent'] = 100-result[sensor+'_percent']
    result['sparse_cohort'] = len(rows)<20 or result['instances']<5
    return result


def paired_tracks(rows, near, far):
    """Equal-track means on tracks seen in both bands; not causal range effects."""
    tracks=defaultdict(lambda: [[],[]])
    for row in rows:
        for i,(low,high) in enumerate((near,far)):
            if low<=row['range_m']<high:
                tracks[row['instance_token']][i].append(row)
    output=[]
    for token,(a,b) in sorted(tracks.items()):
        if not a or not b: continue
        classes={r['category'] for r in a+b}
        if len(classes)!=1: continue
        entry=dict(track=token,scene=a[0]['scene'],category=a[0]['category'],near_observations=len(a),far_observations=len(b))
        for sensor in ('lidar','radar'):
            x=float(np.mean([r[sensor+'_points']>0 for r in a]))
            y=float(np.mean([r[sensor+'_points']>0 for r in b]))
            entry.update({sensor+'_near_percent':100*x,sensor+'_far_percent':100*y,sensor+'_far_minus_near_pp':100*(y-x)})
        output.append(entry)
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-root',type=Path,default=Path('docs/evidence'))
    parser.add_argument('--output-dir',type=Path,default=Path('docs/evidence/missing-support'))
    args=parser.parse_args();root=args.evidence_root
    sources={}
    def read(path):
        sources[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_text().encode()).hexdigest()
        return read_rows(path)
    datasets={'TruckScenes':{'paired':qualify(read(root/'truckscenes/paired-point-motion-support/object_counts.csv'))}}
    scenes=json.loads((root/'truckdrive-multiscene/summary/manifest.json').read_text())['scenes']
    variants={v:qualify([r for scene in scenes for r in read(root/'truckdrive-multiscene'/scene/v/'object_counts.csv')]) for v in ('static','aligned')}
    variants['static']=matched(variants['static'],variants['aligned'])
    datasets['TruckDrive']=variants
    classes=[];overall=[];scene_rows=[];track_rows=[];track_summaries=[]
    for dataset,variants in datasets.items():
        for variant,rows in variants.items():
            for margin in (0,.5):
                selected=[r for r in rows if r['margin_m']==margin]
                for low,high in BANDS:
                    group=[r for r in selected if low<=r['range_m']<high]
                    if not group: continue
                    keys=dict(dataset=dataset,variant=variant,margin_m=margin,band_m=f'{low}-{high}')
                    overall.append(dict(**keys,**breakdown(group)))
                    for category in sorted({r['category'] for r in group}):
                        subset=[r for r in group if r['category']==category]
                        entry=dict(**keys,category=category,**breakdown(subset))
                        for sensor in ('lidar','radar'):
                            missing=sum(r[sensor+'_points']==0 for r in group)
                            entry[sensor+'_share_of_missing_percent']=100*entry[sensor+'_unsupported']/missing if missing else None
                        classes.append(entry)
                        for scene in sorted({r['scene'] for r in subset}):
                            scene_rows.append(dict(**keys,category=category,scene=scene,
                                **breakdown([r for r in subset if r['scene']==scene])))
                for near,far in [((0,50),(50,100)),((50,100),(100,150)),((100,150),(150,200)),((100,150),(200,400))]:
                    keys=dict(dataset=dataset,variant=variant,margin_m=margin,near_band=f'{near[0]}-{near[1]}',far_band=f'{far[0]}-{far[1]}')
                    pairs=paired_tracks(selected,near,far)
                    track_rows.extend(dict(**keys,**r) for r in pairs)
                    for category in ['ALL']+sorted({r['category'] for r in pairs}):
                        group=[r for r in pairs if category=='ALL' or r['category']==category]
                        if not group: continue
                        summary=dict(**keys,category=category,tracks=len(group),scenes=len({r['scene'] for r in group}))
                        for sensor in ('lidar','radar'):
                            for key in ('near_percent','far_percent','far_minus_near_pp'):
                                summary[sensor+'_'+key]=float(np.mean([r[sensor+'_'+key] for r in group]))
                            summary[sensor+'_tracks_lower_far']=sum(r[sensor+'_far_minus_near_pp']<0 for r in group)
                        track_summaries.append(summary)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,rows in [('class_support',classes),('overall',overall),('scene_class_support',scene_rows),('matched_tracks',track_rows),('matched_track_summary',track_summaries)]:
        write_csv(args.output_dir/(name+'.csv'),rows)
    manifest=dict(input_sha256_lf_normalized=sources,bands=BANDS,
        semantics='Lower inclusive, upper exclusive planar object-center range. Exact and +0.5 m box counts; >=1 return defines support. No object-box denominator for roads or grass.',
        timing='TruckScenes prior paired per-point ego correction; TruckDrive static and ego-aligned hypotheses on identical 190-frame cohort.',
        tracks='Same native-class tracks in both bands, equal-track mean of per-band support fractions; no causal claim, independence or population confidence intervals.',
        limitations='Annotation-conditioned. Labels may favour LiDAR. Hardware, occlusion, motion, visibility and class composition differ. No detector predictions or false-positive evaluation.')
    (args.output_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    plot(classes,args.output_dir)
    print('Wrote',len(classes),'class cohorts and',len(track_summaries),'matched-track summaries')


def plot(rows,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    configs=[('TruckScenes','paired',['vehicle.car','vehicle.truck','human.pedestrian.adult','vehicle.bicycle','static_object.traffic_sign','movable_object.trafficcone']),
             ('TruckDrive','aligned',['Vehicle-Passenger','Vehicle','Vehicle-SemiTruck-Cab','Vehicle-SemiTruck-Trailer','TrafficSign','RoadObstruction-Barrel'])]
    for dataset,variant,categories in configs:
        bands=[f'{a}-{b}' for a,b in BANDS if dataset!='TruckScenes' or b<=200]
        fig,axes=plt.subplots(1,2,figsize=(16,6),sharey=True)
        for ax,sensor in zip(axes,('lidar','radar')):
            data=np.full((len(categories),len(bands)),np.nan)
            for i,category in enumerate(categories):
                for j,band in enumerate(bands):
                    r=next((r for r in rows if r['dataset']==dataset and r['variant']==variant and r['margin_m']==0 and r['category']==category and r['band_m']==band),None)
                    if r:
                        data[i,j]=r[sensor+'_missing_percent']
                        ax.text(j,i,f"{data[i,j]:.0f}%{'*' if r['sparse_cohort'] else ''}\nn={r['observations']}",ha='center',va='center',fontsize=7,color='white' if data[i,j]>65 else 'black')
            cmap=plt.get_cmap('magma_r').copy();cmap.set_bad('#dddddd')
            im=ax.imshow(data,vmin=0,vmax=100,cmap=cmap,aspect='auto')
            ax.set(xticks=range(len(bands)),xticklabels=bands,yticks=range(len(categories)),yticklabels=categories,title=sensor.title(),xlabel='Box-center distance (m)')
            ax.tick_params(axis='x',rotation=45)
        fig.suptitle(dataset+': which labelled objects have no in-box returns? ('+variant+')')
        caution=('TruckScenes radar has a recorded boundary near 190 m; the last band partly overlaps it.' if dataset=='TruckScenes'
                 else 'TruckDrive alignment is a timing hypothesis; thin signs are highly timing/box-margin sensitive.')
        fig.text(.015,.015,'Exact boxes; rounded unsupported percentages. Darker = more unsupported. Grey = no labelled observations.\n* Fewer than 20 observations or 5 tracks. Repeated observations; selected classes; not detector error rates.\n'+caution,fontsize=9)
        fig.tight_layout(rect=(0,.10,.92,.94));fig.colorbar(im,cax=fig.add_axes([.94,.24,.012,.5]),label='Unsupported observations (%)')
        fig.savefig(output/(dataset.lower()+'_missing_by_class.png'),dpi=150);plt.close(fig)


if __name__=='__main__':main()
