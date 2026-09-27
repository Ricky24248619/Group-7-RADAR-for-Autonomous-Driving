"""Bounded RADIATE fog diagnostic: LiDAR footprint returns and radar contrast.

These two measurements have different meanings. Neither is detector recall.
The official sample is radar-annotated, covers one short fog sequence, and has
no clear-weather control. No causal weather or general sensor ranking is scored.
"""
import argparse
from collections import defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile
import zlib

import numpy as np
from PIL import Image
from compare_truckscenes_raw import write_csv

URL='https://www.dropbox.com/scl/fi/d1nwbaoh6ea1d68vv6e0b/tiny_foggy.zip?rlkey=n2wb6v1xsmxm98ecxatv2bm6v&dl=1'
ARCHIVE_SHA='395126112a8776bcc8907bc3f754f006351a22d22591b43a751af71d2bbdc486'
RES=100/576


def acquire(root):
    root.mkdir(parents=True,exist_ok=True)
    archive=root/'tiny_foggy.zip'
    if not archive.exists():
        part=archive.with_suffix('.part')
        with urllib.request.urlopen(URL,timeout=45) as response,part.open('wb') as output:
            while chunk:=response.read(1024*1024):output.write(chunk)
        if hashlib.sha256(part.read_bytes()).hexdigest()!=ARCHIVE_SHA:raise ValueError('Archive hash changed')
        part.replace(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=ARCHIVE_SHA:raise ValueError('Archive hash mismatch')
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            path=root/info.filename
            if not path.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe archive path')
            if info.is_dir():path.mkdir(parents=True,exist_ok=True);continue
            data=path.read_bytes() if path.exists() else z.read(info)
            if len(data)!=info.file_size or zlib.crc32(data)!=info.CRC:raise ValueError('Changed extracted input: '+info.filename)
            if not path.exists():path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)


def timestamps(path):
    result=[]
    for line in path.read_text().splitlines():
        fields=line.split();result.append((int(fields[1]),int(Decimal(fields[3])*1_000_000_000)))
    if any(a[1]>=b[1] for a,b in zip(result,result[1:])):raise ValueError('Unordered timestamps')
    return result


def inside(points,box,margin=0):
    x,y,w,h=box['position'];center=np.array([x+w/2,y+h/2])
    theta=np.deg2rad(-box['rotation']);r=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
    local=(points-center)@r
    return (np.abs(local[:,0])<=w/2+margin)&(np.abs(local[:,1])<=h/2+margin)


def lidar_pixels(points):
    # Published LiDAR pose relative to the radar reference. The tiny rotations
    # use degrees, matching the SDK calibration helper; no camera-axis swap.
    a,b,c=np.deg2rad([.0001655,.000213,.000934])
    rx=np.array([[1,0,0],[0,np.cos(a),-np.sin(a)],[0,np.sin(a),np.cos(a)]])
    ry=np.array([[np.cos(b),0,np.sin(b)],[0,1,0],[-np.sin(b),0,np.cos(b)]])
    rz=np.array([[np.cos(c),-np.sin(c),0],[np.sin(c),np.cos(c),0],[0,0,1]])
    p=points[:,:3]@(rx@ry@rz).T+[.6003,-.120102,.250012]
    return np.column_stack((p[:,0]/RES+576,576-p[:,1]/RES))


def radar_contrast(image,box,all_boxes,exclude_target_overlap=False):
    x,y,w,h=box['position'];cx=x+w/2;cy=y+h/2
    radius=np.hypot(w/2+3/RES,h/2+3/RES)
    u=np.arange(max(0,int(cx-radius)),min(1152,int(np.ceil(cx+radius))+1))
    v=np.arange(max(0,int(cy-radius)),min(1152,int(np.ceil(cy+radius))+1))
    uu,vv=np.meshgrid(u,v);points=np.column_stack((uu.ravel(),vv.ravel()))
    target=inside(points,box);background=inside(points,box,3/RES)&~target
    for other in all_boxes:
        overlap=inside(points,other)
        if exclude_target_overlap and np.any(target&overlap):return None
        background&=~overlap
    values=image[vv.ravel(),uu.ravel()]
    if target.sum()<10 or background.sum()<100:return None
    cutoff=float(np.percentile(values[background],99))
    bright=int((values[target]>cutoff).sum())
    p99=float(np.percentile(values[target],99));gap=p99-cutoff
    return dict(target_pixels=int(target.sum()),background_pixels=int(background.sum()),radar_target_p99=p99,radar_background_p99=cutoff,radar_bright_pixels=bright,
        radar_contrast_pass=int(bright>=5 and gap>0),radar_contrast_gap10=int(bright>=5 and gap>10),radar_contrast_gap20=int(bright>=5 and gap>20))


def rotate_control(box,degrees):
    x,y,w,h=box['position'];center=np.array([x+w/2-576,y+h/2-576]);a=np.deg2rad(degrees)
    r=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]]);center=r@center+576
    return dict(position=[float(center[0]-w/2),float(center[1]-h/2),w,h],rotation=box['rotation']-degrees)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--output-dir',type=Path,default=Path('docs/evidence/radiate-fog'));args=ap.parse_args()
    acquire(args.root);root=args.root/'tiny_foggy';out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    annotations=json.loads((root/'annotations/annotations.json').read_text())
    rt=timestamps(root/'Navtech_Cartesian.txt');lt=timestamps(root/'velo_lidar.txt')
    ltimes=np.array([t for _,t in lt],dtype=np.int64);rows=[];frames=[];hashes={};excluded=[];controls=[]
    def hashed(path):
        hashes[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
        return path
    for name in ('Navtech_Cartesian.txt','velo_lidar.txt','annotations/annotations.json','meta.json'):hashed(root/name)
    for index,(frame,time) in enumerate(rt):
        image=np.asarray(Image.open(hashed(root/f'Navtech_Cartesian/{frame:06d}.png')))
        if image.shape!=(1152,1152) or image.dtype!=np.uint8:raise ValueError('Unexpected radar image format')
        nearest=int(np.argmin(np.abs(ltimes-time)));delta=(int(ltimes[nearest])-time)/1e6
        if abs(delta)>50:
            excluded.append(dict(frame=frame,nearest_lidar_delta_ms=delta,reason='Nearest LiDAR exceeds 50 ms gate'));continue
        selected=[a for a in annotations if frame-1<len(a['bboxes']) and a['bboxes'][frame-1]]
        all_boxes=[a['bboxes'][frame-1] for a in selected]
        scans={}
        for j in range(max(0,nearest-1),min(len(lt),nearest+2)):
            cloud=np.loadtxt(hashed(root/f'velo_lidar/{lt[j][0]:06d}.csv'),delimiter=',')
            cloud=cloud[np.isfinite(cloud).all(axis=1)&(np.linalg.norm(cloud[:,:3],axis=1)>.01)]
            scans[j]=(cloud,lidar_pixels(cloud))
        cloud,pixels=scans[nearest];ranges=np.hypot(cloud[:,0],cloud[:,1])
        frames.append(dict(frame=frame,lidar_frame=lt[nearest][0],delta_ms=delta,lidar_returns=len(cloud),lidar_range_p50_m=float(np.percentile(ranges,50)),lidar_range_p90_m=float(np.percentile(ranges,90)),lidar_range_p99_m=float(np.percentile(ranges,99)),lidar_range_max_m=float(ranges.max())))
        for a,box in zip(selected,all_boxes):
            x,y,w,h=box['position'];distance=float(np.hypot(x+w/2-576,y+h/2-576)*RES)
            band=next((f'{lo}-{hi}' for lo,hi in [(0,25),(25,50),(50,75),(75,100)] if lo<=distance<hi),None)
            if band is None:continue
            contrast=radar_contrast(image,box,all_boxes)
            if contrast is None:continue
            for angle in (90,180,270):
                control=radar_contrast(image,rotate_control(box,angle),all_boxes,exclude_target_overlap=True)
                if control is not None:controls.append(dict(frame=frame,parent_track=a['id'],angle_deg=angle,band_m=band,**control))
            for margin in (0,1):
                counts=[]
                for j,(points,uv) in scans.items():
                    mask=inside(uv,box,margin/RES);counts.append(int((mask&(points[:,2]>-1.5)).sum()))
                mask=inside(pixels,box,margin/RES)
                rows.append(dict(frame=frame,track=a['id'],class_name=a['class_name'],band_m=band,distance_m=distance,margin_m=margin,
                    lidar_all_returns=int(mask.sum()),lidar_above_ground_returns=int((mask&(cloud[:,2]>-1.5)).sum()),
                    adjacent_scan_min_returns=min(counts),adjacent_scan_max_returns=max(counts),**contrast))
        if index==0:plot_example(image,cloud,pixels,all_boxes,out)
    grouped=defaultdict(list)
    for row in rows:grouped[row['band_m'],row['margin_m']].append(row)
    summary=[]
    for (band,margin),rs in sorted(grouped.items()):
        summary.append(dict(band_m=band,margin_m=margin,observations=len(rs),tracks=len({r['track'] for r in rs}),frames=len({r['frame'] for r in rs}),
            lidar_any=sum(r['lidar_above_ground_returns']>0 for r in rs),lidar_five=sum(r['lidar_above_ground_returns']>=5 for r in rs),
            lidar_any_adjacent=sum(r['adjacent_scan_max_returns']>0 for r in rs),radar_contrast_pass=sum(r['radar_contrast_pass'] for r in rs),
            radar_contrast_gap10=sum(r['radar_contrast_gap10'] for r in rs),radar_contrast_gap20=sum(r['radar_contrast_gap20'] for r in rs),
            radar_contrast_lidar_empty=sum(r['radar_contrast_pass'] and r['lidar_above_ground_returns']==0 for r in rs)))
    write_csv(out/'observations.csv',rows);write_csv(out/'summary.csv',summary);write_csv(out/'frames.csv',frames);write_csv(out/'unlabelled_controls.csv',controls)
    manifest=dict(dataset='RADIATE tiny_foggy / fog_6_0',archive_url=URL,archive_sha256=ARCHIVE_SHA,available_radar_frames=len(rt),frames=len(frames),excluded=excluded,inputs=hashes,
        lidar_pose_in_radar=dict(translation=[.6003,-.120102,.250012],rotation_degrees=[.0001655,.000213,.000934],order='Rx Ry Rz'),
        metric='LiDAR above-ground returns in annotated BEV footprint; separately radar image contrast against an unannotated 3 m ring. Radar contrast is not a point return or detector prediction.',
        limits='One 18-frame fog sample; radar-derived annotations; no clear-weather control. Native LiDAR z > -1.5 m is only a ground-removal proxy. Static calibration, no ego/object-motion or rolling radar scan correction; nearest scan <=50 ms plus adjacent-scan and 1 m footprint sensitivities. Different modalities/metrics cannot establish accuracy ranking.')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Completed',len(frames),'paired frames;',len(rows)//2,'box observations; excluded',len(excluded))


def plot_example(image,cloud,pixels,boxes,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,7),sharex=True,sharey=True)
    axes[0].imshow(image,cmap='gray',vmin=0,vmax=150,extent=(-100,100,-100,100))
    valid=cloud[:,2]>-1.5
    axes[1].scatter((pixels[valid,0]-576)*RES,(576-pixels[valid,1])*RES,s=1,c='#2878b5')
    for ax,title in zip(axes,('Recorded radar image','LiDAR returns (ground-filter proxy)')):
        for box in boxes:
            x,y,w,h=box['position'];center=np.array([x+w/2,y+h/2]);angle=np.deg2rad(-box['rotation'])
            r=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
            points=np.array([[-w/2,-h/2],[w/2,-h/2],[w/2,h/2],[-w/2,h/2],[-w/2,-h/2]])@r.T+center
            ax.plot((points[:,0]-576)*RES,(576-points[:,1])*RES,color='#e69f00',lw=1)
        ax.set(title=title,xlim=(-25,25),ylim=(0,85),xlabel='Lateral coordinate (m)',ylabel='Forward coordinate (m)');ax.set_aspect('equal')
    fig.suptitle('RADIATE fog sample: first available radar frame and nearest LiDAR scan')
    fig.text(.03,.03,'Orange: radar-annotated footprints. Measurements, not predictions. Static alignment; no weather-control sequence.\nSource: Sheeny et al., RADIATE / Heriot-Watt University. Figure CC BY-NC-SA 4.0.',fontsize=9)
    fig.tight_layout(rect=(0,.09,1,.95));fig.savefig(out/'fog_example.png',dpi=150);plt.close(fig)


if __name__=='__main__':main()
