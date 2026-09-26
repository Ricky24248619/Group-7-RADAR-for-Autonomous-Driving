"""CPU-only STONE paired geometric-support pilot, with explicit frame sensitivity.

No detector accuracy or hole inference. Reference voxels are LiDAR-derived and
occlusion is not resolved. Angular eligibility is a declared conservative ROI.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation, Slerp
from compare_truckscenes_raw import write_csv

BANDS=((2,10),(10,20),(20,30),(30,40))
TOLERANCES=(.4,.8,1.2)


def matrix(rotation_xyzw,translation):
    t=np.eye(4);t[:3,:3]=Rotation.from_quat(rotation_xyzw).as_matrix();t[:3,3]=translation;return t


def transform(points,t):return points@t[:3,:3].T+t[:3,3]


def clean(points):return points[np.isfinite(points).all(axis=1)&(np.linalg.norm(points,axis=1)>.01)]


def reference_groups(labels):
    """Ground-relative geometric groups only where local traversable-plane fit exists."""
    if labels.shape!=(200,200,16) or not np.isin(labels,[0,1,2,3,255]).all():raise ValueError('Unexpected label grid')
    ix=np.argwhere((labels>=1)&(labels<=3));xyz=ix*.4+[-39.8,-39.8,-.8];classes=labels[tuple(ix.T)]
    # Lowest traversable reference in each xy column anchors the local surface.
    ground=xyz[classes==1];columns=np.floor(ground[:,:2]/.4).astype(int)
    order=np.argsort(ground[:,2]);_,unique=np.unique(columns[order],axis=0,return_index=True);ground=ground[order[unique]]
    height=np.full(len(xyz),np.nan)
    if len(ground)>=6:
        dist,indices=cKDTree(ground[:,:2]).query(xyz[:,:2],k=min(12,len(ground)),distance_upper_bound=3)
        for i in range(len(xyz)):
            valid=np.isfinite(dist[i]);near=ground[indices[i][valid]]
            if len(near)<6:continue
            xy=near[:,:2]-xyz[i,:2]
            # Do not extrapolate a plane from a line or far outside sampled ground.
            centered=xy-xy.mean(axis=0)
            covariance=np.linalg.eigvalsh(centered.T@centered/len(xy))
            if covariance[0]<.02 or np.linalg.norm(xy.mean(axis=0))>1.5:continue
            a=np.column_stack((xy,np.ones(len(xy))));fit=np.linalg.lstsq(a,near[:,2],rcond=None)[0]
            if np.sqrt(np.mean((a@fit-near[:,2])**2))>.2 or np.linalg.norm(fit[:2])>1:continue
            height[i]=xyz[i,2]-fit[2]
    groups={'traversable_label':classes==1,'potential_label':classes==2,'nontraversable_label':classes==3,
            'near_ground_geometry':np.abs(height)<=.3,'raised_geometry':(height>=.6)&(height<=3)}
    return xyz,groups,height


def angular_roi(points,sensors,elevation=10):
    eligible=np.zeros(len(points),dtype=bool)
    for t in sensors:
        local=transform(points,np.linalg.inv(t));horizontal=np.hypot(local[:,0],local[:,1]);distance=np.linalg.norm(local,axis=1)
        eligible|=(np.abs(np.degrees(np.arctan2(local[:,1],local[:,0])))<=60)&(np.abs(np.degrees(np.arctan2(local[:,2],horizontal)))<=elevation)&(distance>=.2)&(distance<=40)
    return eligible


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,required=True);ap.add_argument('--output-dir',type=Path,default=Path('docs/evidence/stone-pilot'));args=ap.parse_args()
    root=args.root;p=root/'paired-pilot';out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    selection=json.loads((p/'selection.json').read_text());acq=json.loads((p/'manifest.json').read_text())
    if len(selection)!=acq['frames'] or len({s['token'] for s in selection})!=len(selection):raise ValueError('Invalid selection')
    for f in acq['files']:
        if hashlib.sha256((p/f['file']).read_bytes()).hexdigest()!=f['sha256']:raise ValueError('Input hash mismatch: '+f['file'])
    transforms=json.loads((p/'transforms.json').read_text());tf={}
    for v in transforms:
        q=v['transform']['rotation'];tr=v['transform']['translation'];tf[v['child_frame_id']]=matrix([q[k] for k in 'xyzw'],[tr[k] for k in 'xyz'])
    lidar_cal=next(r for r in json.loads((root/'extracted/calibrated_sensor.json').read_text()) if r['token']=='79007574b35f57109832178a9945f9df')
    q=lidar_cal['rotation'];lidar_t=matrix(q[1:]+q[:1],lidar_cal['translation']);bridge=lidar_t@np.linalg.inv(tf['hesai_lidar'])
    radar_frames=['ARS_548_240','ARS_548_0','ARS_548_120'];radar_t=[bridge@tf[f] for f in radar_frames]
    motion=json.loads((p/'odometry.json').read_text());times=np.array([r['timestamp_ns'] for r in motion],dtype=np.int64);t0=int(times[0]);seconds=(times-t0)/1e9
    positions=np.array([r['position'] for r in motion]);slerp=Slerp(seconds,Rotation.from_quat([r['quaternion_xyzw'] for r in motion]))
    def pose(ns):
        t=(ns-t0)/1e9
        if t<seconds[0] or t>seconds[-1]:raise ValueError('Pose extrapolation forbidden')
        tr=[np.interp(t,seconds,positions[:,j]) for j in range(3)];return matrix(slerp(t).as_quat(),tr)
    radar_meta={(r['sample_token'],r['sensor']):r for r in acq['inputs'] if r['sensor'].startswith('radar')}
    rows=[];frame_stats=[];inputs=[];reference_summary=[]
    for frame,s in enumerate(selection):
        token=s['token'];data=np.fromfile(p/(token+'_lidar.bin'),dtype='<f4').reshape(-1,5);lidar=transform(clean(data[:,:3]),lidar_t)
        refs,groups,height=reference_groups(np.load(p/(token+'_labels.npz'),allow_pickle=False)['label']);ranges=np.hypot(refs[:,0],refs[:,1]);radars=np.load(p/(token+'_radar.npz'),allow_pickle=False)
        meta=json.loads((p/(token+'_metadata.json')).read_text());bag_ns=radar_meta[token,'radar1']['bag_ns'];target_pose=pose(bag_ns)
        if meta['lidar']['calibrated_sensor_token']!=lidar_cal['token']:raise ValueError('Changed LiDAR calibration')
        if bag_ns//1000!=s['timestamp'] or any(radar_meta[token,'radar'+str(i)]['bag_ns']!=bag_ns for i in (2,3)):raise ValueError('Unmatched sensor bag timestamps')
        # Check the exported ego pose against the independently decoded odometry.
        export=meta['ego_pose'];q=export['rotation'];export_pose=matrix(q[1:]+q[:1],export['translation'])
        if not np.allclose(export_pose,target_pose,atol=1e-7,rtol=0):raise ValueError('Export and bag pose disagree')
        static=[];aligned=[];deltas=[]
        for i,t in enumerate(radar_t,1):
            raw=clean(radars['radar'+str(i)]);points=transform(raw,t);static.append(points)
            timing=radar_meta[token,'radar'+str(i)];deltas.append((timing['header_ns']-bag_ns)/1e6)
            aligned.append(transform(points,np.linalg.inv(target_pose)@pose(timing['header_ns'])))
        variants={'static':np.concatenate(static),'aligned':np.concatenate(aligned)}
        # Sensitivity only: released ROS transforms omit physical sensor translations.
        variants['ros_origin']=np.concatenate([transform(clean(radars['radar'+str(i+1)]),tf[f]) for i,f in enumerate(radar_frames)])
        reference_summary.append(dict(frame=token,total_occupied=len(refs),local_height_resolved=int(np.isfinite(height).sum()),near_ground=int(groups['near_ground_geometry'].sum()),raised=int(groups['raised_geometry'].sum())))
        lidar_dist=cKDTree(lidar).query(refs,workers=2)[0]
        for variant,radar in variants.items():
            radar_dist=cKDTree(radar).query(refs,workers=2)[0] if len(radar) else np.full(len(refs),np.inf)
            for elevation in (10,20):
                fov=angular_roi(refs,radar_t,elevation)
                for low,high in BANDS:
                    band=(ranges>=low)&(ranges<high)&fov
                    for group,mask in groups.items():
                        selected=band&mask;n=int(selected.sum())
                        if not n:continue
                        for tolerance in TOLERANCES:
                            l=lidar_dist[selected]<=tolerance;r=radar_dist[selected]<=tolerance
                            rows.append(dict(frame=token,scene=meta['scene'],variant=variant,elevation_deg=elevation,band_m=f'{low}-{high}',group=group,tolerance_m=tolerance,reference_voxels=n,lidar_supported=int(l.sum()),radar_supported=int(r.sum()),both=int((l&r).sum()),neither=int((~l&~r).sum())))
        frame_stats.append(dict(frame=token,scene=meta['scene'],lidar_valid=len(lidar),radar_valid=len(variants['static']),radar_header_delta_min_ms=min(deltas),radar_header_delta_max_ms=max(deltas)))
        for suffix in ('_lidar.bin','_labels.npz','_radar.npz'):
            path=p/(token+suffix);inputs.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        if frame==0:
            diagnostic=p/'diagnostics';diagnostic.mkdir(exist_ok=True)
            plot(refs,groups,lidar,variants['static'],diagnostic)
    aggregated=defaultdict(list)
    for r in rows:aggregated[tuple(r[k] for k in ('variant','elevation_deg','band_m','group','tolerance_m'))].append(r)
    summaries=[]
    for key,rs in sorted(aggregated.items()):
        n=sum(r['reference_voxels'] for r in rs);entry=dict(zip(('variant','elevation_deg','band_m','group','tolerance_m'),key),frames=len(rs),reference_voxels=n)
        for sensor in ('lidar','radar'):
            hits=sum(r[sensor+'_supported'] for r in rs);entry[sensor+'_supported']=hits;entry[sensor+'_percent']=100*hits/n
            entry[sensor+'_equal_frame_percent']=float(np.mean([100*r[sensor+'_supported']/r['reference_voxels'] for r in rs]))
        summaries.append(entry)
    for name,data in [('support_by_frame',rows),('support_summary',summaries),('frame_stats',frame_stats),('reference_geometry',reference_summary)]:write_csv(out/(name+'.csv'),data)
    plot_summary(summaries,out,len(selection))
    for path in [p/'selection.json',p/'manifest.json',p/'transforms.json',p/'odometry.json',root/'extracted/calibrated_sensor.json']:
        inputs.append(dict(file=path.relative_to(root).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    manifest=dict(frames=len(selection),source_ids=acq['source_ids'],inputs=inputs,grid=dict(shape=[200,200,16],voxel_m=.4,minimum_m=[-40,-40,-1]),
        source_readme_revision='4ba5f700ddeb709a0e645bdd5fda082b0561d282',source_readme_sha256=hashlib.sha256((root/'acquisition/README-pinned.md').read_bytes()).hexdigest(),
        lidar_transform=lidar_t.tolist(),ros_to_export_bridge=bridge.tolist(),radar_transforms=[t.tolist() for t in radar_t],
        methods='Reference voxel centers; Euclidean nearest return within tolerance. Native traversability classes plus local traversable-plane height proxies. Band is planar ego range, lower inclusive.',
        limitations='One recording; repeated correlated voxels; LiDAR-derived reference; no occlusion mask or detector. Radar physical translations unverified: ROS TF rotations, zero translations, bridged to exported ego frame. Static/aligned/ROS-origin and angular-ROI sensitivities, not calibration validation. No holes or safe driving claim.')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Wrote',len(rows),'frame cohorts and',len(summaries),'summaries')


def plot_summary(rows,out,frames):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,5),sharey=True)
    bands=[f'{low}-{high}' for low,high in BANDS]
    for ax,group,title in zip(axes,('near_ground_geometry','raised_geometry'),('Near local ground','0.6-3 m above local ground')):
        selected={ (r['variant'],r['band_m']):r for r in rows if r['group']==group and r['elevation_deg']==10 and r['tolerance_m']==.8 }
        x=np.arange(4)
        for sensor,color in [('lidar','#2878b5'),('radar','#d65f00')]:
            ax.plot(x,[selected.get(('aligned',b),{}).get(sensor+'_percent',np.nan) for b in bands],marker='o',color=color,label=sensor.title()+' (aligned hypothesis)')
        ax.plot(x,[selected.get(('ros_origin',b),{}).get('radar_percent',np.nan) for b in bands],marker='s',ls='--',color='#7851a9',label='Radar (ROS origin sensitivity)')
        ax.set(xticks=x,xticklabels=bands,xlim=(-.4,3.4),xlabel='Planar distance (m)',title=title,ylim=(0,105),ylabel='Reference voxels with a return within 0.8 m (%)')
        ax.grid(alpha=.2)
        for i,b in enumerate(bands):
            r=selected.get(('aligned',b))
            label=f"n={r['reference_voxels']}\n{r['frames']} frames" if r else 'No eligible\nreferences'
            ax.text(i,4,label,ha='center',fontsize=8)
    axes[0].legend(fontsize=8,loc='center left')
    fig.suptitle('STONE: paired terrain support, not detection accuracy')
    fig.text(.02,.02,f'{frames} frames / one recording. LiDAR-derived reference; unresolved radar translations; no occlusion mask. Curves join different scene content.',fontsize=9)
    fig.tight_layout(rect=(0,.07,1,.94));fig.savefig(out/'terrain_support.png',dpi=150);plt.close(fig)


def plot(refs,groups,lidar,radar,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,5),sharex=True,sharey=True)
    for ax,points,title in zip(axes,(lidar,radar),('LiDAR','Three radars')):
        for name,color in [('near_ground_geometry','#2c7bb6'),('raised_geometry','#fdae61')]:
            g=refs[groups[name]];ax.scatter(g[:,0],g[:,1],s=8,c=color,alpha=.5,label=name.replace('_',' '))
        ps=points[np.hypot(points[:,0],points[:,1])<40];ps=ps[::max(1,len(ps)//15000)]
        ax.scatter(ps[:,0],ps[:,1],s=2,c='black',alpha=.5,label='recorded returns');ax.set(title=title,xlabel='Ego x (m)',ylabel='Ego y (m)',xlim=(-40,40),ylim=(-40,40));ax.set_aspect('equal')
    axes[0].legend(fontsize=7,loc='upper right');fig.suptitle('STONE paired pilot: reference geometry and recorded returns')
    fig.text(.02,.02,'One frame, top projection. Height distinction is lost in projection. Released-transform hypothesis; no detector predictions.',fontsize=9)
    fig.tight_layout(rect=(0,.06,1,.94));fig.savefig(out/'paired_geometry.png',dpi=150);plt.close(fig)


if __name__=='__main__':main()
