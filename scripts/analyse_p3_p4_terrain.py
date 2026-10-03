"""Directional terrain errors, map aggregation and independent data eligibility.

Saved predictions only. Semantic screening is not measured physical passability.
"""
import argparse
import ast
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from analyse_goose_saved_errors import confusion
from compare_truckscenes_raw import write_csv
from goose_render_frame import find_frames, load_frame

ROOT = Path(__file__).resolve().parents[1]
BANDS = ((0,25),(25,50),(50,100),(100,float('inf')))


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def policy_groups(policy):
    groups = np.full(64,-1,dtype=int)
    for row in policy:
        k,p = int(row['label_key']),int(row['traversability_id'])
        if not 0<=k<64 or not 0<=p<=3:raise ValueError('Invalid policy')
        # 0 ignored, 1 candidate firm, 2 uncertain surface, 3 rigid/person/vehicle,
        # 4 water, 5 vegetation called blocked by the provisional policy.
        groups[k] = p
        if k==54:groups[k]=4
        if k in (16,17,27,59):groups[k]=5
    if np.any(groups<0):raise ValueError('Incomplete fine-label policy')
    return groups


def cell_counts(xyz, groups, prediction, size):
    if not np.isfinite(xyz).all() or size<=0:raise ValueError('Invalid cells')
    cell_ids = np.floor(xyz[:,:2].astype(float)/size).astype(np.int64)
    _, inverse = np.unique(cell_ids,axis=0,return_inverse=True)
    total = np.bincount(inverse)
    firm = np.bincount(inverse,weights=groups==1,minlength=len(total))
    rigid = np.bincount(inverse,weights=groups==3,minlength=len(total))
    ignored = np.bincount(inverse,weights=groups==0,minlength=len(total))
    ground_pred = np.bincount(inverse,weights=np.isin(prediction,(2,3)),minlength=len(total))
    mixed = (firm>0)&(rigid>0)
    ground_majority = firm>(total-ignored)/2
    predicted_majority = ground_pred>total/2
    # A point-label oracle still loses the hazard under this majority rule.
    return dict(observed_cells=len(total),rigid_hazard_cells=int((rigid>0).sum()),
                mixed_firm_rigid_cells=int(mixed.sum()),
                mixed_true_firm_majority_cells=int((mixed&ground_majority).sum()),
                mixed_predicted_ground_majority_cells=int((mixed&predicted_majority).sum()),
                all_rigid_predicted_ground_majority_cells=int(((rigid>0)&predicted_majority).sum()))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--goose-root',type=Path,required=True)
    p.add_argument('--mapping',type=Path,required=True)
    p.add_argument('--original-predictions',type=Path,required=True)
    p.add_argument('--followup-predictions',type=Path,required=True)
    p.add_argument('--execution',type=Path,required=True)
    p.add_argument('--wildscenes-audit',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    args = p.parse_args()
    original = json.loads((ROOT/'docs/evidence/goose-stratified/semantic/manifest.json').read_text())
    follow = json.loads((ROOT/'results/evidence/sprint-followup-oct01/terrain/selection.json').read_text())
    run_manifest = json.loads((ROOT/'results/evidence/sprint-followup-oct01/terrain/manifest.json').read_text())
    if sha(args.mapping)!=original['mapping_sha256']:raise ValueError('Changed fine-to-model mapping')
    mapping = {int(r['label_key']):r for r in csv.DictReader(args.mapping.open(encoding='utf-8-sig'))}
    remap = np.array([0 if int(mapping[k]['challege_category_id'])==8 else int(mapping[k]['challege_category_id']) for k in range(64)])
    policy_path = ROOT/'GOOSE - Ricky+Damien/traversability_map.csv'
    policy = list(csv.DictReader(policy_path.open(encoding='utf-8-sig')))
    groups_lut = policy_groups(policy)
    files = {scan.name:(scan,label) for scan,label in find_frames(args.goose_root)}
    tasks = [('stratified24',entry,args.original_predictions,entry['sha256']['prediction']) for entry in original['inputs']]
    for variant in ('p64','p128'):
        for entry in follow['inputs']:
            tasks.append((variant,entry,args.followup_predictions/variant/'result',run_manifest['runs'][variant]['prediction_sha256'][entry['frame']]))
    inputs, fine_rows, frames, cells, costs = [], [], [], [], []
    for variant in ('p64','p64repeat','p128'):
        for file,key in [('config.py','config_sha256'),('test.log','log_sha256')]:
            path = args.followup_predictions/variant/file
            if sha(path)!=run_manifest['runs'][variant][key]:raise ValueError('Changed saved run: '+variant+'/'+file)
            inputs.append(dict(kind='saved_run',variant=variant,file=file,sha256=sha(path)))
        # Repeat equivalence is established for every selected prediction, without inference.
        for name,expected in run_manifest['runs'][variant]['prediction_sha256'].items():
            path = args.followup_predictions/variant/'result'/(name+'_pred.npy')
            if sha(path)!=expected:raise ValueError('Changed prediction: '+variant+'/'+name)
    for variant,entry,pred_root,pred_sha in tasks:
        name = entry['frame']
        scan,label = files[name]
        challenge = Path(str(label).replace('labels/','labels_challenge/').replace('labels\\','labels_challenge\\'))
        prediction_path = pred_root/(name+'_pred.npy')
        for key,path in [('scan',scan),('label',label),('challenge_label',challenge),('prediction',prediction_path)]:
            expected = pred_sha if key=='prediction' else entry['sha256'][key]
            if sha(path)!=expected:raise ValueError('Input/prediction changed: '+name+'/'+key)
        points,raw = load_frame(scan,label)
        if not np.isin(raw,range(64)).all() or not np.isfinite(points).all():raise ValueError('Invalid raw scan')
        pred = np.load(prediction_path,allow_pickle=False)
        used = (np.fromfile(challenge,dtype=np.uint32)&0xffff).astype(int);used[used==8]=0
        if not np.array_equal(remap[raw],used):raise ValueError('Challenge label reconciliation failed')
        matrix = confusion(used,pred)
        groups = groups_lut[raw]
        ground,blocked = np.isin(pred,(2,3)),np.isin(pred,(1,4,5,7))
        scenario = scan.parent.name
        base = dict(variant=variant,frame=name,recording=scenario)
        frames.append(dict(**base,points=len(raw),correct_coarse=int(matrix.trace()),
                           candidate_firm_points=int((groups==1).sum()),candidate_called_blocked=int(((groups==1)&blocked).sum()),
                           rigid_hazard_points=int((groups==3).sum()),rigid_called_ground=int(((groups==3)&ground).sum()),
                           uncertain_surface_points=int((groups==2).sum()),uncertain_surface_called_ground=int(((groups==2)&ground).sum()),
                           water_points=int((groups==4).sum()),water_called_ground=int(((groups==4)&ground).sum()),
                           vegetation_hazard_points=int((groups==5).sum()),vegetation_hazard_called_ground=int(((groups==5)&ground).sum()),
                           ignored_points=int((groups==0).sum())))
        distance = np.hypot(points[:,0].astype(float),points[:,1].astype(float))
        for low,high in BANDS:
            mask = (distance>=low)&(distance<high)
            band = f'{low}-{high}' if np.isfinite(high) else '100+'
            for k in np.unique(raw[mask]):
                counts = np.bincount(pred[mask&(raw==k)].astype(int),minlength=8)
                fine_rows.append(dict(**base,band_m=band,raw_id=int(k),raw_class=mapping[int(k)]['class_name'],
                                      coarse_truth=int(remap[k]),policy_group=int(groups_lut[k]),points=int(counts.sum()),
                                      **{'pred_'+str(i):int(c) for i,c in enumerate(counts)}))
        for size in (.5,1):
            cells.append(dict(**base,cell_size_m=size,**cell_counts(points[:,:3],groups,pred,size)))
        inputs.append(dict(kind='paired_frame',variant=variant,frame=name,
                           sha256={**entry['sha256'],'prediction':pred_sha}))
        print('Scored',variant,name,len(raw),flush=True)
    execution = json.loads(args.execution.read_text())
    for run in execution:
        variant = run['variant']
        if run['status']!='success' or run['exit_code']!=0:raise ValueError('Incomplete saved run')
        log = (args.followup_predictions/variant/'test.log').read_text()
        batches = re.findall(r'Test: (\S+) \[\d+/7\]-\d+ Batch ([0-9.]+)',log)
        if len(batches)!=7 or {b[0] for b in batches}!={r['frame'] for r in follow['inputs']}:
            raise ValueError('Saved log lacks exact selected seven frames')
        for frame,seconds in batches:
            costs.append(dict(variant=variant,frame=frame,logged_batch_seconds=float(seconds),
                              complete_seven_frame_run_seconds=run['elapsed_seconds'],
                              observed_global_gpu_memory_max_mib=max(r['gpu_total_memory_mib'] for r in run['samples'])))
    audit = args.wildscenes_audit
    selection = json.loads((audit/'X1-selection.json').read_text())
    acquired = json.loads((audit/'X1-acquisition.json').read_text())
    if sha(audit/'X1-selection.json')!=acquired['selection_sha256']:raise ValueError('Independent selection changed')
    # Parse author's literal metadata, never execute downloaded code.
    utils = ast.parse((audit/'source-audit/wildscenes_utils3d.py').read_text())
    meta = next(ast.literal_eval(n.value) for n in utils.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='METAINFO' for t in n.targets))
    names = dict(zip(meta['cidx'],meta['classes']))
    config = ast.parse((audit/'source-audit/wildscenes_config.txt').read_text())
    benchmark = next(ast.literal_eval(n.value) for n in config.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='labels_map' for t in n.targets))
    input_files = {r['filename']:r for r in acquired['inputs']}
    wild_rows, wild_frames, taxonomy = [], [], []
    shared = {'dirt':'candidate_natural_ground','gravel':'candidate_natural_ground',
              'fence':'rigid_structure','structure':'rigid_structure','tree-trunk':'rigid_obstacle',
              'rock':'rigid_obstacle','log':'rigid_obstacle','tree-foliage':'vegetation','bush':'vegetation',
              'mud':'uncertain_surface','water':'water','sky':'ignored','unlabelled':'ignored',
              'grass':'ambiguous_height','other-terrain':'ambiguous_surface','other-object':'ambiguous_object'}
    for k,name in sorted(names.items()):
        taxonomy.append(dict(native_id=k,native_class=name,benchmark_id=benchmark[k],
                             benchmark_ignored=benchmark[k]==255,proposed_shared_group=shared[name],
                             goose_equivalence='Requires explicit translation; no transfer score'))
    for entry in selection:
        cloud_path = audit/'raw-wildscenes'/entry['lidar_path']
        label_path = audit/'raw-wildscenes'/entry['label_path']
        for path,key in [(cloud_path,'lidar_path'),(label_path,'label_path')]:
            record = input_files[entry[key]]
            if path.stat().st_size!=record['bytes'] or sha(path)!=record['sha256']:raise ValueError('Independent raw changed')
        xyz = np.fromfile(cloud_path,dtype='<f4').reshape(-1,3)
        labels = np.fromfile(label_path,dtype='<i4')
        if len(xyz)!=len(labels) or not np.isfinite(xyz).all() or not np.isin(labels,list(names)).all():
            raise ValueError('Invalid author-decoded independent scan/label pair')
        distance = np.hypot(xyz[:,0].astype(float),xyz[:,1].astype(float))
        base = dict(frame=entry['id'],recording=entry['lidar_path'].split('/')[1],split=entry['split'])
        wild_frames.append(dict(**base,points=len(labels),labelled=int((labels!=255).sum()),
                                rear_half_points=int((xyz[:,0]<0).sum()),planar_range_min_m=float(distance.min()),
                                planar_range_max_m=float(distance.max()),x_min_m=float(xyz[:,0].min()),x_max_m=float(xyz[:,0].max()),
                                y_min_m=float(xyz[:,1].min()),y_max_m=float(xyz[:,1].max()),
                                benchmark_ignored=sum(int((labels==k).sum()) for k,v in benchmark.items() if v==255)))
        for low,high in BANDS:
            mask = (distance>=low)&(distance<high)
            for k in sorted(names):
                count = int((mask&(labels==k)).sum())
                wild_rows.append(dict(**base,band_m=f'{low}-{high}' if np.isfinite(high) else '100+',
                                      native_id=k,native_class=names[k],benchmark_ignored=benchmark[k]==255,points=count))
        print('Independent terrain',base['recording'],len(labels),'points',flush=True)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    output = {'terrain_directional_frames.csv':frames,'terrain_fine_predictions.csv':fine_rows,
              'terrain_cells.csv':cells,'saved_model_cost.csv':costs,'wildscenes_frames.csv':wild_frames,
              'wildscenes_class_range.csv':wild_rows,'wildscenes_taxonomy.csv':taxonomy}
    for name,rows in output.items():write_csv(args.output_dir/name,rows)
    sources = {name:sha(audit/'source-audit'/name) for name in ('wildscenes_view.txt','wildscenes_config.txt','wildscenes_utils3d.py','collection_api.txt')}
    manifest = dict(goose_inputs=inputs,challenge_mapping_sha256=sha(args.mapping),
                    policy_sha256_lf=hashlib.sha256(policy_path.read_text(encoding='utf-8').encode()).hexdigest(),
                    saved_execution_sha256=sha(args.execution),wildscenes_acquisition=acquired,wildscenes_selection=selection,
                    wildscenes_author_commit='9eb4e10b4483a634159e2b371be0437e465fe218',author_sources_sha256=sources,
                    licence='WildScenes: CC BY-NC-SA 4.0; selected raw retained locally, no raw republication',
                    new_gpu_runs=0,outputs_sha256={n:hashlib.sha256((args.output_dir/n).read_text().encode()).hexdigest() for n in output},
                    limits=['GOOSE predictions cover 31 selected frames from eight recordings; variants are matched only on seven',
                            'XY cells are vertical columns, including overhead geometry; no collision or passability ground truth',
                            'Policy and native semantics stay distinct; unseen cells are not free',
                            'WildScenes source XYZ has no intensity; no cross-dataset inference or transfer score',
                            'WildScenes labelled clouds are camera-visible; five first frames are training-split examples',
                            'Desktop logged batch time and sampled global GPU memory are not vehicle latency or process peak memory'])
    (args.output_dir/'terrain_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
