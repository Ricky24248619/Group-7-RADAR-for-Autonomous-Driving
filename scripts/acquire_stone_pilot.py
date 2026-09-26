"""Extract a bounded, timestamp-matched STONE pilot from official ZIP and ROS DB.

Database row ranges are verified against every returned topic/count and used only
for this named release, whose layout was inspected. No camera payloads are read.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import zipfile
import numpy as np
from stone_remote import RemoteFile,connect_sqlite


def stamp_ns(stamp):return int(stamp.sec)*1_000_000_000+int(stamp.nanosec)


def xyz_cloud(msg):
    endian='>' if msg.is_bigendian else '<'
    fields={f.name:f for f in msg.fields}
    if any(k not in fields or fields[k].count!=1 or fields[k].datatype not in (7,8) for k in ('x','y','z')):
        raise ValueError('Invalid XYZ fields')
    if msg.row_step<msg.width*msg.point_step or len(msg.data)!=msg.height*msg.row_step:raise ValueError('Invalid cloud strides')
    dtype=np.dtype({'names':['x','y','z'],'formats':[endian+('f4' if fields[k].datatype==7 else 'f8') for k in ('x','y','z')],
                    'offsets':[fields[k].offset for k in ('x','y','z')],'itemsize':msg.point_step})
    a=np.ndarray((msg.height,msg.width),dtype=dtype,buffer=msg.data,strides=(msg.row_step,msg.point_step))
    return np.column_stack([a[k].reshape(-1) for k in ('x','y','z')])


def main():
    from rosbags.typesys import get_typestore,Stores
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,required=True);ap.add_argument('--frames',type=int,default=20);args=ap.parse_args()
    root=args.root;b=root/'acquisition';out=root/'paired-pilot';out.mkdir(exist_ok=True)
    samples=json.loads((b/'pilot_samples.json').read_text())
    if not 1<=args.frames<=len(samples)-2:raise ValueError('Frame count must fit unique interior samples')
    selected=[samples[int(i)] for i in np.linspace(1,len(samples)-2,args.frames,dtype=int)]
    scenes={s['token']:s['name'] for s in json.loads((root/'extracted/scene.json').read_text())}
    sd={r['sample_token']:r for r in json.loads((root/'extracted/sample_data.json').read_text()) if '/LIDAR_TOP/' in r['filename']}
    poses={r['token']:r for r in json.loads((root/'extracted/ego_pose.json').read_text())}
    # Fixed selection is saved before inspecting any support scores.
    (out/'selection.json').write_text(json.dumps(selected,indent=2))
    store=get_typestore(Stores.ROS2_HUMBLE);manifest=[]
    bag=RemoteFile(json.loads((b/'bag_source.json').read_text()),b/'bag-cache');conn,vfs=connect_sqlite(bag)
    transforms=[]
    for topic,blob in conn.execute('SELECT topic_id,data FROM messages WHERE id BETWEEN 74739 AND 74744'):
        if topic!=19:raise ValueError('Unexpected transform rows')
        for tr in store.deserialize_cdr(blob,'tf2_msgs/msg/TFMessage').transforms:
            if tr.header.frame_id!='base_link':raise ValueError('Unexpected transform parent')
            transforms.append(dict(child_frame_id=tr.child_frame_id,transform=dict(
                translation={k:float(getattr(tr.transform.translation,k)) for k in 'xyz'},
                rotation={k:float(getattr(tr.transform.rotation,k)) for k in 'xyzw'})))
    (out/'transforms.json').write_text(json.dumps(transforms,indent=2))
    # ponytail: fixed row layout supports only this recording; inspect topic bounds
    # before adapting to another bag instead of pretending this is a general devkit.
    wanted={s['timestamp']:s for s in selected};radars=defaultdict(dict);counts=defaultdict(int)
    for ident,topic,time_ns,blob in conn.execute('SELECT id,topic_id,timestamp,data FROM messages WHERE id BETWEEN 23154 AND 28496'):
        if topic not in (14,15,16):raise ValueError('Unexpected row layout')
        counts[topic]+=1
        key=time_ns//1000
        if key not in wanted:continue
        m=store.deserialize_cdr(blob,'sensor_msgs/msg/PointCloud2');name='radar'+str(topic-13)
        if m.header.frame_id!={14:'ARS_548_240',15:'ARS_548_0',16:'ARS_548_120'}[topic]:raise ValueError('Unexpected radar frame')
        if name in radars[key]:raise ValueError('Duplicate sensor timestamp')
        radars[key][name]=xyz_cloud(m)
        manifest.append(dict(sample_token=wanted[key]['token'],sensor=name,header_frame=m.header.frame_id,
                             header_ns=stamp_ns(m.header.stamp),bag_ns=time_ns,row_id=ident,cdr_sha256=hashlib.sha256(blob).hexdigest()))
    if dict(counts)!={14:1781,15:1781,16:1781}:raise ValueError('Unexpected topic counts')
    if any(set(radars[s['timestamp']])!={'radar1','radar2','radar3'} for s in selected):raise ValueError('Missing paired radar')
    for s in selected:np.savez_compressed(out/(s['token']+'_radar.npz'),**radars[s['timestamp']])
    print('Saved all selected radar scans',flush=True)
    motion=[]
    for topic,time_ns,blob in conn.execute('SELECT topic_id,timestamp,data FROM messages WHERE id BETWEEN 72958 AND 74738'):
        if topic!=18:raise ValueError('Unexpected odometry rows')
        m=store.deserialize_cdr(blob,'nav_msgs/msg/Odometry');p=m.pose.pose
        motion.append(dict(timestamp_ns=stamp_ns(m.header.stamp),bag_ns=time_ns,position=[getattr(p.position,k) for k in 'xyz'],quaternion_xyzw=[getattr(p.orientation,k) for k in 'xyzw']))
    (out/'odometry.json').write_text(json.dumps(motion))
    if len(motion)!=1781 or any(a['timestamp_ns']>=b['timestamp_ns'] for a,b in zip(motion,motion[1:])):raise ValueError('Invalid odometry timeline')
    zremote=RemoteFile(json.loads((b/'zip_source.json').read_text()),b/'zip-cache')
    with zipfile.ZipFile(zremote) as z:
        for s in selected:
            token=s['token'];lidar=sd[token];gt=f'STONE_nus_dataset/gts/{scenes[s["scene_token"]]}/{token}/labels.npz'
            sources={'lidar':'STONE_nus_dataset/'+lidar['filename'],'labels':gt}
            for kind,member in sources.items():
                path=out/(token+('_lidar.bin' if kind=='lidar' else '_labels.npz'))
                if not path.exists():
                    data=z.read(member);path.write_bytes(data) # zipfile verifies CRC before return
                else:data=path.read_bytes()
                info=z.getinfo(member)
                import zlib
                if len(data)!=info.file_size or zlib.crc32(data)!=info.CRC:raise ValueError('Member integrity mismatch')
                manifest.append(dict(sample_token=token,sensor=kind,member=member,bytes=len(data),crc32=info.CRC,sha256=hashlib.sha256(data).hexdigest()))
            (out/(token+'_metadata.json')).write_text(json.dumps(dict(sample=s,lidar=lidar,scene=scenes[s['scene_token']],ego_pose=poses[lidar['ego_pose_token']]),indent=2))
            print('Complete paired frame',token,flush=True)
    files=[]
    for s in selected:
        for suffix in ('_radar.npz','_lidar.bin','_labels.npz','_metadata.json'):
            path=out/(s['token']+suffix);files.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    for name in ('selection.json','transforms.json','odometry.json'):
        files.append(dict(file=name,sha256=hashlib.sha256((out/name).read_bytes()).hexdigest()))
    (out/'manifest.json').write_text(json.dumps(dict(source_ids={'zip':zremote.source['id'],'bag':bag.source['id']},frames=len(selected),selection=f'{len(selected)} uniformly spaced interior frame indices of first listed farmland recording',inputs=manifest,files=files),indent=2))
    conn.close()


if __name__=='__main__':main()
