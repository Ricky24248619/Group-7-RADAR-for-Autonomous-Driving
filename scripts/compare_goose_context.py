"""Compare fixed-seed attention-patch variants on three post-hoc GOOSE frames."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyse_goose_saved_errors import confusion
from compare_truckscenes_raw import write_csv

def canonical_config(text):
    """Require settings to differ only in save path and attention patch sizes."""
    text,n=re.subn(r"save_path = '[^']+'",'save_path = OUTPUT',text)
    if n!=1:raise ValueError('Expected one save_path')
    for key in ('enc_patch_size','dec_patch_size'):
        text,n=re.subn(key+r'=\[[0-9, ]+\]',key+'=PATCH',text)
        if n!=1:raise ValueError('Expected explicit patch sizes')
    return text


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--runs',type=Path,required=True)
    ap.add_argument('--mapping',type=Path,required=True)
    ap.add_argument('--checkpoint',type=Path,required=True)
    ap.add_argument('--output',type=Path,default=Path('docs/evidence/goose-failure-causes'))
    ap.add_argument('--include-p256',action='store_true',help='Include only after this optional resource probe completes')
    args=ap.parse_args();out=args.output
    checkpoint_sha=hashlib.sha256(args.checkpoint.read_bytes()).hexdigest()
    previous=json.loads(Path('docs/evidence/goose-stratified/runtime.json').read_text())
    if checkpoint_sha!=previous['input_sha256']['checkpoint']:raise ValueError('Checkpoint changed since preceding study')
    variants=('p64','p64repeat','p128')+(('p256',) if args.include_p256 else ())
    selection=json.loads((out/'selection.json').read_text());expected={e['frame'] for e in selection['inputs']}
    with args.mapping.open(encoding='utf-8-sig') as f:labels=list(csv.DictReader(f))
    mapping={r['class_name']:int(r['label_key']) for r in labels}
    remap=np.array([int(next(r for r in labels if int(r['label_key'])==k)['challege_category_id']) for k in range(64)])
    remap[remap==8]=0
    runtime={};base=None;predictions={};rows=[];point_total=0
    for variant in variants:
        run=args.runs/f'goose_case3_{variant}_20260928';config=(run/'config.py').read_text();log=(run/'test.log').read_text()
        if 'End Evaluation' not in log or 'loaded pred and label' in log:raise ValueError('Run incomplete or predictions reused')
        if {p.name.removesuffix('_pred.npy') for p in (run/'result').glob('*_pred.npy')}!=expected:raise ValueError('Wrong prediction cohort')
        canonical=canonical_config(config)
        patch=64 if variant=='p64repeat' else int(variant[1:])
        if f'enc_patch_size=[{", ".join([str(patch)]*5)}]' not in config or f'dec_patch_size=[{", ".join([str(patch)]*4)}]' not in config:
            raise ValueError('Variant patch size disagrees with saved config')
        if base is None:base=canonical
        elif canonical!=base:raise ValueError('Unexpected configuration difference')
        runtime[variant]=dict(config_sha256=hashlib.sha256(config.encode()).hexdigest(),log_sha256=hashlib.sha256(log.encode()).hexdigest(),
                              end_evaluation=True,predictions_sha256={})
    for entry in selection['inputs']:
        name=entry['frame'];scan=args.root/'lidar/val'/entry['scenario']/name
        label=args.root/'labels/val'/entry['scenario']/name.replace('_vls128.bin','_goose.label')
        challenge=args.root/'labels_challenge/val'/entry['scenario']/label.name
        for key,path in [('scan',scan),('label',label),('challenge_label',challenge)]:
            if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256'][key]:raise ValueError('Selected raw input changed')
        xyz=np.fromfile(scan,dtype=np.float32).reshape(-1,4)
        raw=(np.fromfile(label,dtype=np.uint32)&65535).astype(int)
        if len(xyz)!=len(raw) or not np.isfinite(xyz).all() or not np.isin(raw,range(64)).all():
            raise ValueError('Invalid scan coordinates, intensity, pairing or labels')
        used=(np.fromfile(challenge,dtype=np.uint32)&65535).astype(int);used[used==8]=0
        if not np.array_equal(used,remap[raw]):raise ValueError('Challenge/fine label mismatch')
        distance=np.hypot(xyz[:,0].astype(float),xyz[:,1].astype(float));point_total+=len(raw)
        for variant in variants:
            path=args.runs/f'goose_case3_{variant}_20260928'/'result'/(name+'_pred.npy');pred=np.load(path,allow_pickle=False)
            confusion(used,pred);runtime[variant]['predictions_sha256'][name]=hashlib.sha256(path.read_bytes()).hexdigest()
            predictions[variant,name]=pred
            rows.append(dict(frame=name,variant=variant,true_class='all',range_m='all',points=len(raw),
                             ground_category_points=int(np.isin(pred,[2,3]).sum()),correct_coarse_points=int(np.sum(pred==used))))
            for category in ('rock','building'):
                mask=(raw==mapping[category])&(distance<25)
                rows.append(dict(frame=name,variant=variant,true_class=category,range_m='0-25',points=int(mask.sum()),
                                 ground_category_points=int(np.sum(np.isin(pred[mask],[2,3]))),correct_coarse_points=int(np.sum(pred[mask]==used[mask]))))
    if point_total!=selection['points']:raise ValueError('Selected point total changed')
    for name in expected:
        if not np.array_equal(predictions['p64',name],predictions['p64repeat',name]):raise ValueError('Baseline is not prediction-identical on repeat')
    write_csv(out/'context_comparison.csv',rows)
    pooled=[]
    for variant in variants:
        for category in ('all','rock','building'):
            chosen=[r for r in rows if r['variant']==variant and r['true_class']==category]
            total=sum(r['points'] for r in chosen)
            pooled.append(dict(variant=variant,true_class=category,points=total,
                               ground_category_percent=100*sum(r['ground_category_points'] for r in chosen)/total,
                               correct_coarse_percent=100*sum(r['correct_coarse_points'] for r in chosen)/total))
    write_csv(out/'context_pooled.csv',pooled)
    (out/'context_manifest.json').write_text(json.dumps(dict(selection_sha256=hashlib.sha256((out/'selection.json').read_bytes()).hexdigest(),
          mapping_sha256=hashlib.sha256(args.mapping.read_bytes()).hexdigest(),frames=len(expected),points=point_total,
          checkpoint_sha256=checkpoint_sha,
          baseline_repeat_identical=True,only_config_differences='save_path, encoder and decoder attention patch sizes',runs=runtime,
          limits='Post-hoc adjacent frames from one scene; not a held-out accuracy benchmark. Same checkpoint and fixed seed; original 24-frame run used a different frame order and random-sampling state.'),indent=2)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(11,4.5))
    for ax,category in zip(axes,('rock','building')):
        for name in sorted(expected):
            plotted=[v for v in variants if v!='p64repeat'];sizes=[int(v[1:]) for v in plotted]
            selected=[next(r for r in rows if r['frame']==name and r['variant']==v and r['true_class']==category) for v in plotted]
            ax.plot(sizes,[100*r['ground_category_points']/r['points'] for r in selected],marker='o',label=name.split('__')[1][:4]+f" (n={selected[0]['points']:,})")
        ax.set(xlabel='Attention patch size (tokens)',ylabel='Target points called ground (%)',title=category.capitalize()+' within 25 m',ylim=(0,100))
        ax.set_xticks(sizes);ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Same checkpoint and frames: effect of changing attention context')
    fig.text(.5,.015,'Ground confusion only: other predictions may still be wrong. Three correlated frames; patch-64 repeat is identical. See the CSV for coarse correctness.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.06,1,.94));fig.savefig(out/'context_comparison.png',dpi=150);plt.close(fig)
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
