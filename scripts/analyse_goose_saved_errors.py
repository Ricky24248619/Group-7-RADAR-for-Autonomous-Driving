"""Range/class errors in saved partial PTv3 predictions; no new inference.

Scores the model's eight coarse labels on existing LiDAR points. It does not
measure objects/surfaces with no LiDAR return, or compare LiDAR against radar.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from goose_render_frame import find_frames, load_frame
from compare_truckscenes_raw import write_csv

BANDS=((0,25),(25,50),(50,75),(75,100),(100,150),(150,float('inf')))
NAMES=('other','artificial_structures','artificial_ground','natural_ground','obstacle','vehicle','vegetation','human')


def confusion(truth,prediction):
    if (truth.shape!=prediction.shape or truth.ndim!=1 or
        not np.issubdtype(prediction.dtype,np.integer) or not np.issubdtype(truth.dtype,np.integer) or
        not np.isin(truth,range(8)).all() or not np.isin(prediction,range(8)).all()):
        raise ValueError('Invalid paired eight-class labels')
    return np.bincount(truth.astype(int)*8+prediction.astype(int),minlength=64).reshape(8,8)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--predictions',required=True,type=Path)
    parser.add_argument('--mapping',required=True,type=Path)
    parser.add_argument('--output-dir',type=Path,default=Path('docs/evidence/missing-support/goose-saved'))
    args=parser.parse_args()
    with args.mapping.open(encoding='utf-8-sig') as f: mapping={int(r['label_key']):r for r in csv.DictReader(f)}
    remap=np.full(max(mapping)+1,-1,dtype=int)
    for k,r in mapping.items():
        value=int(r['challege_category_id']);remap[k]=0 if value==8 else value
    pairs=find_frames(args.root)
    frames={p.name:(p,l) for p,l in pairs}
    if len(frames)!=len(pairs):raise ValueError('Ambiguous duplicate scan basenames')
    matrices=defaultdict(lambda:np.zeros((8,8),dtype=np.int64));fine=defaultdict(lambda:np.zeros(8,dtype=np.int64))
    manifest=[];frame_rows=[]
    for path in sorted(args.predictions.glob('*_pred.npy')):
        name=path.name.removesuffix('_pred.npy')
        if name not in frames: raise ValueError('Prediction has no unique scan/label pair')
        scan,label=frames[name];points,raw=load_frame(scan,label)
        if not np.isin(raw,list(mapping)).all():raise ValueError('Unknown raw semantic ID')
        truth=remap[raw];pred=np.load(path,allow_pickle=False)
        matrix=confusion(truth,pred)
        # Prove the 64-to-8 mapping agrees with the labels used by the original run.
        challenge=Path(str(label).replace('labels/','labels_challenge/').replace('labels\\','labels_challenge\\'))
        used=(np.fromfile(challenge,dtype=np.uint32)&0xffff).astype(int);used[used==8]=0
        if not np.array_equal(truth,used):raise ValueError('Challenge labels disagree with taxonomy mapping')
        distance=np.hypot(points[:,0].astype(float),points[:,1].astype(float))
        if not np.isfinite(distance).all():raise ValueError('Nonfinite point coordinates')
        for low,high in BANDS:
            band=f'{low}-{high}' if np.isfinite(high) else f'{low}+'
            mask=(distance>=low)&(distance<high)
            matrices[band]+=confusion(truth[mask],pred[mask])
            for raw_id in np.unique(raw[mask]):
                selection=mask&(raw==raw_id)
                fine[band,int(raw_id)]+=np.bincount(pred[selection].astype(int),minlength=8)
        frame_rows.append(dict(frame=name,scenario=scan.parent.name,points=len(points),correct=int(matrix.trace()),accuracy_percent=100*matrix.trace()/matrix.sum()))
        manifest.append(dict(frame=name,sha256={key:hashlib.sha256(p.read_bytes()).hexdigest() for key,p in [('scan',scan),('label',label),('challenge_label',challenge),('prediction',path)]}))
    if not manifest:raise ValueError('No saved predictions')
    errors=[];summary=[];raw_rows=[]
    for band,m in matrices.items():
        if not m.sum():continue
        summary.append(dict(band_m=band,points=int(m.sum()),correct=int(m.trace()),accuracy_percent=100*m.trace()/m.sum()))
        for i,true in enumerate(NAMES):
            for j,predicted in enumerate(NAMES):
                errors.append(dict(band_m=band,true_class=true,predicted_class=predicted,points=int(m[i,j]),true_class_points=int(m[i].sum())))
    for (band,k),counts in sorted(fine.items()):
        correct=int(counts[remap[k]]);wrong=counts.copy();wrong[remap[k]]=0
        raw_rows.append(dict(band_m=band,raw_class=mapping[k]['class_name'],model_truth=NAMES[remap[k]],points=int(counts.sum()),
            correct_coarse_label=correct,correct_coarse_percent=100*correct/counts.sum(),
            most_common_wrong_prediction=NAMES[int(wrong.argmax())] if wrong.sum() else '',most_common_wrong_points=int(wrong.max())))
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,rows in [('range_accuracy',summary),('confusion',errors),('raw_class_errors',raw_rows),('frame_accuracy',frame_rows)]:write_csv(args.output_dir/(name+'.csv'),rows)
    (args.output_dir/'manifest.json').write_text(json.dumps(dict(frames=len(manifest),points=sum(r['points'] for r in frame_rows),
        scenarios=sorted({r['scenario'] for r in frame_rows}),classes=NAMES,mapping_sha256=hashlib.sha256(args.mapping.read_bytes()).hexdigest(),
        inputs=manifest,scope='Previously saved consecutive partial-run frames, not a representative validation benchmark. Eight coarse model classes, sky mapped to other. No new inference or radar comparison.'),indent=2)+'\n')
    plot(summary,raw_rows,args.output_dir)
    print(json.dumps(summary,indent=2))


def plot(summary,rows,output):
    import matplotlib.pyplot as plt
    bands=[r['band_m'] for r in summary]
    classes=['asphalt','low_grass','high_grass']
    fig,ax=plt.subplots(figsize=(10,5))
    ax.plot(bands,[r['accuracy_percent'] for r in summary],color='black',linestyle='--',label='All returned points')
    for category in classes:
        selected={r['band_m']:r for r in rows if r['raw_class']==category}
        values=[selected[b]['correct_coarse_percent'] if b in selected else np.nan for b in bands]
        line,=ax.plot(bands,values,marker='o',label=category.replace('_',' '))
        for i,b in enumerate(bands):
            if b in selected and i>=4:
                ax.annotate(f"n={selected[b]['points']:,}",(i,values[i]),xytext=(0,-16),textcoords='offset points',ha='center',fontsize=7,color=line.get_color())
    ax.set(ylim=(0,105),xlabel='Planar point distance (m)',ylabel='Correct coarse label (%)',title='GOOSE saved PTv3 predictions: aggregate accuracy hides class errors')
    ax.legend(loc='lower left');ax.grid(axis='y',alpha=.2)
    fig.text(.02,.015,'10 consecutive saved frames from one scene; correlated points. Only existing LiDAR returns.\nEight-class predictions: low grass should map to natural ground; high grass to vegetation. No radar comparison.',fontsize=9)
    fig.tight_layout(rect=(0,.08,1,1));fig.savefig(output/'class_errors_by_range.png',dpi=150);plt.close(fig)


if __name__=='__main__':main()
