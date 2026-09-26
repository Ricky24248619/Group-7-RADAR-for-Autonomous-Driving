"""Ground surfaces versus obstacle candidates in existing GOOSE evidence.

Semantic groups are analysis proxies, not measured height or safe-driveability.
Counts describe returned labelled points, not coverage of unseen terrain.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from goose_render_frame import find_frames, load_frame
from analyse_goose_saved_errors import confusion, BANDS, NAMES
from compare_truckscenes_raw import write_csv

GROUPS={
    'ground_surface': 'cobble bikeway pedestrian_crossing road_marking sidewalk asphalt gravel soil'.split(),
    'ground_cover': 'snow leaves moss low_grass'.split(),
    'obstacle_candidate': 'traffic_cone obstacle street_light road_block car bicycle person traffic_light motorcycle boom_barrier tree_trunk rider animal truck bus on_rails caravan trailer building wall rock fence guard_rail pole traffic_sign misc_sign barrier_tape kick_scooter wire heavy_machinery container barrel pipe military_vehicle'.split(),
    'vegetation': 'forest bush crops tree_crown high_grass scenery_vegetation hedge'.split(),
    'geometry_ambiguous': 'curb rail_track debris bridge tunnel tree_root'.split(),
    'water': ['water'],
    'excluded': 'undefined ego_vehicle sky outlier'.split(),
}
LOOKUP={name:group for group,names in GROUPS.items() for name in names}
PRED_GROUP=('other','obstacle_category','ground_category','ground_category','obstacle_category','obstacle_category','vegetation','obstacle_category')


def predicted_groups(counts):
    """Keep vegetation/other unresolved; never infer holes or safe ground."""
    output={g:0 for g in dict.fromkeys(PRED_GROUP)}
    for i,n in enumerate(counts):output[PRED_GROUP[i]]+=int(n)
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--predictions',type=Path,required=True)
    parser.add_argument('--mapping',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,default=Path('docs/evidence/offroad-ground'))
    args=parser.parse_args();out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    source=Path('docs/evidence/goose/range-support/class_ranges.csv')
    with source.open() as f:rows=list(csv.DictReader(f))
    if set(LOOKUP)!={r['class'] for r in rows}:raise ValueError('Taxonomy not fully partitioned')
    inventory=defaultdict(int)
    for r in rows:inventory[r['scenario'],r['band_m'],LOOKUP[r['class']]]+=int(r['points'])
    write_csv(out/'returned_point_inventory.csv',[dict(scenario=s,band_m=b,group=g,points=n) for (s,b,g),n in sorted(inventory.items())])
    with args.mapping.open(encoding='utf-8-sig') as f:mapping={int(r['label_key']):r for r in csv.DictReader(f)}
    pairs=find_frames(args.root);frames={p.name:(p,l) for p,l in pairs}
    if len(frames)!=len(pairs):raise ValueError('Duplicate scan basenames')
    remap=np.full(max(mapping)+1,-1,dtype=int)
    for k,r in mapping.items():remap[k]=int(r['challege_category_id']) if int(r['challege_category_id'])!=8 else 0
    # Reuse exactly the saved subset already verified in the preceding study.
    previous=json.loads(Path('docs/evidence/missing-support/goose-saved/manifest.json').read_text())
    if hashlib.sha256(args.mapping.read_bytes()).hexdigest()!=previous['mapping_sha256']:
        raise ValueError('Challenge taxonomy changed since saved-prediction verification')
    totals=defaultdict(lambda:np.zeros(8,dtype=np.int64));perframe=defaultdict(lambda:np.zeros(8,dtype=np.int64));inputs=[]
    for entry in previous['inputs']:
        name=entry['frame'];scan,label=frames[name];pred_path=args.predictions/(name+'_pred.npy')
        hashes={key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in [('scan',scan),('label',label),('prediction',pred_path)]}
        if any(hashes[k]!=entry['sha256'][k] for k in hashes):raise ValueError('Saved evidence input changed')
        points,raw=load_frame(scan,label);pred=np.load(pred_path,allow_pickle=False)
        if not np.isin(raw,list(mapping)).all():raise ValueError('Unknown semantic ID')
        confusion(remap[raw],pred)
        distance=np.hypot(points[:,0].astype(float),points[:,1].astype(float))
        if not np.isfinite(points[:,:3]).all():raise ValueError('Nonfinite coordinates')
        for low,high in BANDS:
            band=f'{low}-{high}' if np.isfinite(high) else f'{low}+'
            mask=(distance>=low)&(distance<high)
            for k in np.unique(raw[mask]):
                category=mapping[int(k)]['class_name'];counts=np.bincount(pred[mask&(raw==k)].astype(int),minlength=8)
                totals[band,category]+=counts;perframe[name,band,LOOKUP[category]]+=counts
        inputs.append(dict(frame=name,sha256=hashes))
        if len(inputs)==1:plot_frame(points,raw,mapping,out)
    fine=[];grouped=defaultdict(lambda:np.zeros(8,dtype=np.int64))
    for (band,category),counts in sorted(totals.items()):
        group=LOOKUP[category];grouped[band,group]+=counts
        for i,n in enumerate(counts):fine.append(dict(band_m=band,true_class=category,true_group=group,predicted_class=NAMES[i],points=int(n)))
    def summary(keys,counts):
        n=int(counts.sum());buckets=predicted_groups(counts)
        return dict(**keys,points=n,**{g+'_points':v for g,v in buckets.items()},
                    **{g+'_percent':100*v/n if n else None for g,v in buckets.items()})
    write_csv(out/'saved_fine_confusion.csv',fine)
    write_csv(out/'saved_group_confusion.csv',[summary(dict(band_m=b,true_group=g),c) for (b,g),c in sorted(grouped.items())])
    write_csv(out/'saved_frame_group_confusion.csv',[summary(dict(frame=n,band_m=b,true_group=g),c) for (n,b,g),c in sorted(perframe.items())])
    if sum(int(c.sum()) for c in totals.values())!=previous['points']:raise ValueError('Subset point total changed')
    meta=dict(groups=GROUPS,prediction_grouping=PRED_GROUP,frames=len(inputs),points=previous['points'],
              inventory_sha256_lf=hashlib.sha256(source.read_text().encode()).hexdigest(),
              mapping_sha256=hashlib.sha256(args.mapping.read_bytes()).hexdigest(),inputs=inputs,
              limitations='LiDAR-only semantic proxies; no ground-relative height, safe-driveability, radar, hole labels or independent surface-coverage denominator. Model vegetation/other remains unresolved in the binary question.')
    (out/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'frames':len(inputs),'points':previous['points'],'groups':list(GROUPS)},indent=2))


def plot_frame(points,raw,mapping,out):
    import matplotlib.pyplot as plt
    colors={'ground_surface':'#2166ac','ground_cover':'#67a9cf','obstacle_candidate':'#d6604d','vegetation':'#888888','geometry_ambiguous':'#984ea3','water':'#4daf4a'}
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for group,color in colors.items():
        ids=[k for k,v in mapping.items() if LOOKUP[v['class_name']]==group]
        subset=points[np.isin(raw,ids)&(np.hypot(points[:,0],points[:,1])<50)]
        if not len(subset):continue
        subset=subset[::max(1,len(subset)//12000)]
        axes[0].scatter(subset[:,0],subset[:,1],s=.3,c=color,label=group.replace('_',' '))
        axes[1].scatter(subset[:,0],subset[:,2],s=.3,c=color)
    axes[0].set(xlabel='Scan x (m)',ylabel='Scan y (m)',title='Top view, within 50 m');axes[0].set_aspect('equal')
    axes[1].set(xlabel='Scan x (m)',ylabel='Scan z (m)',title='Side projection, same points');axes[1].set_aspect('equal')
    axes[0].legend(markerscale=7,fontsize=7)
    fig.suptitle('GOOSE: ground-surface labels versus obstacle candidates')
    fig.text(.02,.02,'First saved frame; semantic ground truth, not model predictions or measured obstacle height.\nVegetation and ambiguous geometry remain separate. Empty space is not a labelled hole.',fontsize=9)
    fig.tight_layout(rect=(0,.09,1,.94));fig.savefig(out/'ground_obstacle_example.png',dpi=150);plt.close(fig)


if __name__=='__main__':main()
