"""Inspect rock/building ground-category confusions in a verified saved subset.

Cases are selected after scoring by largest error count, not as typical scenes.
Rock instance IDs are counted within each frame only; they are not unique tracks.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from goose_render_frame import find_frames,load_frame
from analyse_goose_saved_errors import confusion
from analyse_offroad_ground import GROUPS
from compare_truckscenes_raw import write_csv

TARGETS=(('rock',0,25),('rock',100,150),('building',0,25),('building',100,150))


def instance_counts(instance_ids, wrong):
    """Never count unassigned ID zero or join IDs between different frames."""
    ids=np.unique(instance_ids[instance_ids>0])
    return [dict(instance_id=int(i),points=int(np.sum(instance_ids==i)),
                 ground_category_points=int(np.sum((instance_ids==i)&wrong))) for i in ids]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--predictions',type=Path,required=True)
    ap.add_argument('--mapping',type=Path,required=True)
    ap.add_argument('--manifest',type=Path,default=Path('docs/evidence/goose-stratified/semantic/manifest.json'))
    ap.add_argument('--output',type=Path,default=Path('docs/evidence/goose-error-cases'))
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    source=json.loads(args.manifest.read_text())
    with args.mapping.open(encoding='utf-8-sig') as f:mapping={r['class_name']:int(r['label_key']) for r in csv.DictReader(f)}
    if hashlib.sha256(args.mapping.read_bytes()).hexdigest()!=source['mapping_sha256']:
        raise ValueError('Verified challenge mapping changed')
    frames={p.name:(p,l) for p,l in find_frames(args.root)}
    rows=[];instances=[];cases={};class_scenarios=defaultdict(set)
    for entry in source['inputs']:
        scan,label=frames[entry['frame']];pred_path=args.predictions/(scan.name+'_pred.npy')
        for key,path in [('scan',scan),('label',label),('prediction',pred_path)]:
            if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256'][key]:
                raise ValueError('Verified input changed')
        xyz,raw=load_frame(scan,label);pred=np.load(pred_path,allow_pickle=False)
        confusion(np.zeros(len(raw),dtype=int),pred)
        instance=np.fromfile(label,dtype=np.uint32)>>16
        distance=np.hypot(xyz[:,0].astype(float),xyz[:,1].astype(float))
        ground=np.isin(pred,[2,3])
        for category,low,high in TARGETS:
            mask=(raw==mapping[category])&(distance>=low)&(distance<high)
            if not np.any(mask):continue
            errors=mask&ground;band=f'{low}-{high}'
            counts=instance_counts(instance[mask],ground[mask]) if category=='rock' else []
            row=dict(frame=scan.name,scenario=scan.parent.name,true_class=category,band_m=band,
                     points=int(mask.sum()),ground_category_points=int(errors.sum()),
                     ground_category_percent=100*errors.sum()/mask.sum(),
                     frame_local_instances=len(counts) if category=='rock' else '',
                     unassigned_instance_points=int(np.sum(instance[mask]==0)) if category=='rock' else '')
            rows.append(row);class_scenarios[category,band].add(scan.parent.name)
            instances.extend(dict(frame=scan.name,scenario=scan.parent.name,band_m=band,**r) for r in counts)
            if (category,low) not in cases or row['ground_category_points']>cases[category,low][0]['ground_category_points']:
                cases[category,low]=(row,xyz,raw,mask,errors)
    write_csv(args.output/'frame_class_errors.csv',rows)
    write_csv(args.output/'rock_frame_instances.csv',instances)
    summary=[]
    for category,low,high in TARGETS:
        band=f'{low}-{high}';chosen=[r for r in rows if r['true_class']==category and r['band_m']==band]
        if not chosen:continue
        count=sum(r['points'] for r in chosen);wrong=sum(r['ground_category_points'] for r in chosen)
        top=max(chosen,key=lambda r:r['ground_category_points'])
        summary.append(dict(true_class=category,band_m=band,points=count,ground_category_points=wrong,
                            frames=len(chosen),scenarios=len(class_scenarios[category,band]),
                            most_error_frame=top['frame'],most_error_frame_points=top['ground_category_points'],
                            most_error_frame_share_percent=100*top['ground_category_points']/wrong if wrong else None))
    write_csv(args.output/'summary.csv',summary)
    plot_cases([cases['rock',0],cases['building',100]],mapping,args.output)
    (args.output/'manifest.json').write_text(json.dumps(dict(verified_manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        selection='All verified frames scored; illustrations select largest ground-error count for rock 0-25m and building 100-150m; ties retain first manifest frame.',
        selected=[cases['rock',0][0],cases['building',100][0]],
        limits='No new inference. Instance IDs counted only within frames. Buildings have no instance labels. Points, instances and scenarios are correlated; raw scan z is not ground-relative height.'),indent=2)+'\n')
    print(json.dumps(summary,indent=2))


def plot_cases(cases,mapping,out):
    fig,axes=plt.subplots(2,2,figsize=(12,10))
    for axrow,(row,xyz,raw,target,errors) in zip(axes,cases):
        selected=xyz[target]
        lo=selected[:,:2].min(axis=0)-2;hi=selected[:,:2].max(axis=0)+2
        context=np.all((xyz[:,:2]>=lo)&(xyz[:,:2]<=hi),axis=1)
        surface=context&np.isin(raw,[mapping[k] for k in GROUPS['ground_surface']])
        background=xyz[context&~target&~surface][::10]
        for ax,(x,y),view in zip(axrow,((0,1),(0,2)),('Top view','Side projection')):
            ax.scatter(background[:,x],background[:,y],s=.5,c='#aaaaaa',alpha=.25,label='Other context')
            pts=xyz[surface][::3];ax.scatter(pts[:,x],pts[:,y],s=1,c='#2679ac',alpha=.5,label='True ground context')
            pts=xyz[target&~errors];ax.scatter(pts[:,x],pts[:,y],s=3,c='#dc9d31',alpha=.65,label='Target: other prediction')
            pts=xyz[errors];ax.scatter(pts[:,x],pts[:,y],s=5,c='#c82727',alpha=.75,label='Target: predicted ground')
            ax.set(xlabel='Scan x (m)',ylabel='Scan '+('y' if y==1 else 'z')+' (m)',title=view)
            if y==1:
                ax.set_aspect('equal',adjustable='datalim')
            else:
                ax.set_ylim(selected[:,2].min()-2,selected[:,2].max()+2)
                ax.set_ylabel('Scan z (m); unequal axis scales')
            ax.grid(alpha=.2)
        axrow[0].set_title(f"{row['true_class']}, {row['band_m']} m: {row['ground_category_points']:,}/{row['points']:,} points called ground")
        axrow[1].set_title(row['scenario']+' — side projection',fontsize=10)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',ncol=4,fontsize=8)
    fig.suptitle('GOOSE error cases: greatest error-count frame in each selected class/range')
    fig.text(.5,.065,'Post-hoc diagnostic examples, not typical scenes. Scan z is not height above local ground. Red points are not counts of missed objects.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.09,1,.96));fig.savefig(out/'error_cases.png',dpi=150);plt.close(fig)


if __name__=='__main__':main()
