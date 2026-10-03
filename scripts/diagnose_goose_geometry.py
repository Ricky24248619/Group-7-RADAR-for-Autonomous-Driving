"""Geometry associations and voxel ambiguity in the verified difficult GOOSE frame.

Nearest-ground vertical differences are diagnostics, not a ground-height truth.
No causal claim follows from association with a prediction.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from goose_render_frame import find_frames,load_frame
from analyse_offroad_ground import GROUPS
from compare_truckscenes_raw import write_csv

CENTER='2023-01-20_aying_mangfall_2__0497_1674223778204567633_vls128.bin'


def mixed_reference_voxels(xyz,reference,grid):
    # Match GridSample's float64 grid division and integer voxel coordinates.
    cells=np.floor(xyz.astype(float)/grid).astype(np.int64)
    _,inverse=np.unique(cells,axis=0,return_inverse=True)
    hits=np.bincount(inverse,weights=reference.astype(int))>0
    return hits[inverse]


def local_orientation(xyz,queries):
    from scipy.spatial import cKDTree
    distances,indices=cKDTree(xyz).query(queries,k=16,distance_upper_bound=.5)
    valid=np.all(np.isfinite(distances),axis=1)
    horizontal=np.full(len(queries),np.nan)
    nearby=xyz[indices[valid]];nearby=nearby-nearby.mean(axis=1,keepdims=True)
    covariance=np.einsum('nki,nkj->nij',nearby,nearby)/16
    values,vectors=np.linalg.eigh(covariance)
    planar=(values[:,1]>1e-4)&(values[:,0]<.2*values[:,1])
    selected=np.flatnonzero(valid)[planar]
    horizontal[selected]=np.abs(vectors[planar,2,0])
    return horizontal


def main():
    from scipy.spatial import cKDTree
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--predictions',type=Path,required=True)
    ap.add_argument('--mapping',type=Path,required=True)
    ap.add_argument('--output',type=Path,default=Path('docs/evidence/goose-failure-causes'))
    args=ap.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    scan,label=next((s,l) for s,l in find_frames(args.root) if s.name==CENTER)
    pred_path=args.predictions/(CENTER+'_pred.npy')
    manifest=json.loads(Path('docs/evidence/goose-stratified/semantic/manifest.json').read_text())
    entry=next(r for r in manifest['inputs'] if r['frame']==CENTER)
    for key,path in [('scan',scan),('label',label),('prediction',pred_path)]:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256'][key]:raise ValueError('Verified input changed')
    xyz,raw=load_frame(scan,label);pred=np.load(pred_path,allow_pickle=False)
    with args.mapping.open(encoding='utf-8-sig') as f:mapping={r['class_name']:int(r['label_key']) for r in csv.DictReader(f)}
    if hashlib.sha256(args.mapping.read_bytes()).hexdigest()!=manifest['mapping_sha256']:raise ValueError('Mapping changed')
    refs={'ground_surface':np.isin(raw,[mapping[c] for c in GROUPS['ground_surface']]),
          'ground_surface_and_cover':np.isin(raw,[mapping[c] for c in GROUPS['ground_surface']+GROUPS['ground_cover']])}
    rows=[];normals=[];voxel=[]
    for category in ('rock','building'):
        target=(raw==mapping[category])&(np.hypot(xyz[:,0].astype(float),xyz[:,1].astype(float))<25)
        query=xyz[target];wrong=np.isin(pred[target],[2,3])
        orientation=local_orientation(xyz[:,:3],query[:,:3])
        for prediction,mask in [('ground',wrong),('other',~wrong)]:
            available=mask&np.isfinite(orientation)
            normals.append(dict(true_class=category,prediction=prediction,points=int(mask.sum()),
                                normal_eligible_points=int(available.sum()),horizontal_points=int(np.sum(available&(orientation>=.9))),
                                vertical_points=int(np.sum(available&(orientation<=.3)))))
        for ref_name,reference in refs.items():
            ground=xyz[reference];distance,indices=cKDTree(ground[:,:2]).query(query[:,:2])
            dz=query[:,2]-ground[indices,2]
            for cutoff in (1.,2.):
                eligible=distance<=cutoff
                for low,high in ((-float('inf'),-.2),(-.2,.2),(.2,.5),(.5,1),(1,float('inf'))):
                    mask=eligible&(dz>=low)&(dz<high);count=int(mask.sum());errors=int(np.sum(mask&wrong))
                    rows.append(dict(true_class=category,reference=ref_name,max_xy_distance_m=cutoff,
                                     vertical_difference_band=f'{low}:{high}',points=count,ground_category_points=errors,
                                     ground_category_percent=100*errors/count if count else None))
                mask=~eligible
                rows.append(dict(true_class=category,reference=ref_name,max_xy_distance_m=cutoff,
                                 vertical_difference_band='unresolved_reference_too_far',points=int(mask.sum()),
                                 ground_category_points=int(np.sum(mask&wrong)),ground_category_percent=None))
            for grid in (.025,.05):
                mixed=mixed_reference_voxels(xyz[:,:3],reference,grid)[target]
                voxel.append(dict(true_class=category,reference=ref_name,grid_m=grid,points=int(target.sum()),
                                  ground_category_points=int(wrong.sum()),same_voxel_reference_points=int(mixed.sum()),
                                  wrong_same_voxel_reference_points=int(np.sum(mixed&wrong))))
    write_csv(out/'nearest_ground_diagnostic.csv',rows);write_csv(out/'normal_diagnostic.csv',normals);write_csv(out/'voxel_ambiguity.csv',voxel)
    (out/'geometry_manifest.json').write_text(json.dumps(dict(frame=CENTER,input_sha256=entry['sha256'],
        method='Nearest labelled ground in scan XY; raw delta z; 1m and 2m maximum horizontal gaps. Normals: all scan points, 16 neighbors within 0.5m, planar eigenvalue ratio <0.2; abs normal-z >=0.9 horizontal, <=0.3 vertical.',
        limits='No fitted/validated local ground surface, visibility or calibration to image. Adjacent surfaces and slopes confound delta z. Ground cover includes snow/grass, which can conceal the actual supporting surface. Correlations do not establish cause.'),indent=2)+'\n')
    print(json.dumps({'normals':normals,'voxel_ambiguity':voxel},indent=2))


if __name__=='__main__':main()
