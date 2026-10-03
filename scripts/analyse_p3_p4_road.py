"""Temporal paired sensor evidence and descriptive weather controls; no detection score."""
import argparse
from collections import defaultdict
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import statistics

from compare_truckscenes_raw import write_csv
from analyse_findings_oct01 import support

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    data = gzip.decompress(path.read_bytes()).decode('utf-8').replace('\r\n','\n') if path.suffix=='.gz' else path.read_text(encoding='utf-8')
    return hashlib.sha256(data.encode()).hexdigest()


def episodes(rows, flag, median_interval):
    """Runs stop at every failed flag, missing scene sample, or long time gap."""
    result, run = [], []
    for row in sorted(rows, key=lambda r:r['position']):
        if run and (row['position'] != run[-1]['position']+1 or
                    row['time_s']-run[-1]['time_s'] > 1.5*median_interval):
            result.append(run)
            run = []
        if flag(row):
            run.append(row)
        elif run:
            result.append(run)
            run = []
    if run:
        result.append(run)
    return result


def support_counts(rows, threshold):
    support(rows,threshold)  # Existing validation rejects invalid counts and thresholds.
    l = sum(int(r['lidar_points']) >= threshold for r in rows)
    r = sum(int(r['radar_points']) >= threshold for r in rows)
    only = sum(int(r['radar_points']) >= threshold and int(r['lidar_points']) < threshold for r in rows)
    return dict(observations=len(rows), tracks=len({(r['scene'],r['instance_token']) for r in rows}),
                scenes=len({r['scene'] for r in rows}), lidar=l, radar=r, radar_only=only, union=l+only)


def temporal(rows, dataset, variant, margin, threshold, sector, intervals):
    cohort = [r for r in rows if float(r['margin_m']) == margin and
              (sector == 180 or abs(float(r['azimuth_deg'])) <= sector)]
    groups = defaultdict(list)
    for row in cohort:
        groups[row['scene'],row['instance_token']].append(row)
    tracks, run_rows = [], []
    for (scene, track), group in sorted(groups.items()):
        group.sort(key=lambda r:r['position'])
        for sensor in ('lidar','radar','union','radar_only','neither'):
            def flag(row):
                l = int(row['lidar_points']) >= threshold
                r = int(row['radar_points']) >= threshold
                return {'lidar':l,'radar':r,'union':l or r,'radar_only':r and not l,'neither':not(l or r)}[sensor]
            runs = episodes(group, flag, intervals[scene])
            confirmed = [run for run in runs if len(run)>=3]
            first = confirmed[0] if confirmed else None
            base = dict(dataset=dataset,variant=variant,margin_m=margin,threshold=threshold,sector_deg=sector,
                        scene=scene,track=track,category=group[0]['category'],sensor=sensor)
            tracks.append(dict(**base,observations=len(group),supported=sum(map(flag,group)),episodes=len(runs),
                               persistent_episodes=len(confirmed),first_support_range_m=runs[0][0]['range_m'] if runs else '',
                               confirmation_range_m=first[2]['range_m'] if first else '',
                               confirmation_time_s=first[2]['time_s'] if first else '',
                               confirmation_delay_s=first[2]['time_s']-first[0]['time_s'] if first else '',
                               track_start_to_confirmation_s=first[2]['time_s']-group[0]['time_s'] if first else ''))
            for index, run in enumerate(runs):
                run_rows.append(dict(**base,episode=index,samples=len(run),start_time_s=run[0]['time_s'],
                                     end_time_s=run[-1]['time_s'],duration_s=run[-1]['time_s']-run[0]['time_s'],
                                     start_range_m=run[0]['range_m'],end_range_m=run[-1]['range_m']))
    summary = dict(dataset=dataset,variant=variant,margin_m=margin,threshold=threshold,sector_deg=sector,
                   **support_counts(cohort,threshold))
    for sensor in ('lidar','radar','union','radar_only','neither'):
        chosen = [r for r in tracks if r['sensor']==sensor]
        summary[sensor+'_persistent_tracks'] = sum(r['persistent_episodes']>0 for r in chosen)
        summary[sensor+'_episodes'] = sum(r['episodes'] for r in chosen)
        summary[sensor+'_persistent_episodes'] = sum(r['persistent_episodes'] for r in chosen)
    far = [r for r in cohort if 200<=float(r['range_m'])<400]
    summary.update({'far_'+k:v for k,v in support_counts(far,threshold).items()})
    return tracks, run_rows, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--truckscenes-root',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args = parser.parse_args()
    sources = {}
    def load(relative):
        path = ROOT/relative
        sources[relative] = digest(path)
        return list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')))
    old = json.loads((ROOT/'docs/evidence/truckdrive-multiscene/summary/manifest.json').read_text())
    expected = {'docs/evidence/truckdrive-multiscene/'+k:v for k,v in old['input_sha256'].items()}
    expected.update(json.loads((ROOT/'results/evidence/sprint-followup-oct01/sensor_manifest.json').read_text())['sources_sha256'])
    td = defaultdict(list)
    intervals = {}
    td_key_audit = []
    for scene in ('scene_28_1','scene_28_6','scene_28_12','scene_28_18','scene_28_24','scene_28_3','scene_28_15'):
        parent = ('docs/evidence/truckdrive-multiscene' if scene in old['scenes'] else
                  'results/evidence/sprint-followup-oct01/truckdrive')
        frames = load(f'{parent}/{scene}/static/sensor_frames.csv')
        times = sorted({int(r['annotation_timestamp_ns']) for r in frames})
        positions = {t:i for i,t in enumerate(times)}
        intervals[scene] = statistics.median(b-a for a,b in zip(times,times[1:]))/1e9
        tables = {}
        for variant in ('static','aligned'):
            relative = f'{parent}/{scene}/{variant}/object_counts.csv'
            rows = load(relative)
            if sources[relative] != expected[relative]:
                raise ValueError('Changed paired table: '+relative)
            tables[variant] = {(r['annotation_token'],r['margin_m']):r for r in rows}
            if len(tables[variant])!=len(rows):
                raise ValueError('Duplicate observation')
        common = tables['static'].keys() & tables['aligned'].keys()
        td_key_audit.append(dict(scene=scene,static_keys=len(tables['static']),aligned_keys=len(tables['aligned']),shared_keys=len(common)))
        if not common:
            raise ValueError('No paired observations')
        for variant, table in tables.items():
            for key in sorted(common):
                row = table[key]
                other = tables['aligned' if variant=='static' else 'static'][key]
                if any(row[k]!=other[k] for k in ('category','instance_token','sample_token','timestamp','range_m','azimuth_deg')):
                    raise ValueError('Paired identity/geometry changed')
                if row['category'].startswith('Vehicle'):
                    row.update(position=positions[int(row['timestamp'])],time_s=int(row['timestamp'])/1e9)
                    td[variant].append(row)
    meta = args.truckscenes_root/'v1.2-mini'
    prior = json.loads((ROOT/'docs/evidence/truckscenes/paired-point-motion-support/manifest.json').read_text())
    metadata = {}
    for name in ('sample','sample_annotation','scene','visibility','attribute','ego_pose'):
        path = meta/(name+'.json')
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if sha != prior['metadata_sha256'][name+'.json']:
            raise ValueError('Changed TruckScenes metadata: '+name)
        sources['external:TruckScenes/v1.2-mini/'+path.name] = sha
        metadata[name] = {r['token']:r for r in json.loads(path.read_text())}
    scene_names = {k:v['name'] for k,v in metadata['scene'].items()}
    scene_times = defaultdict(list)
    for sample in metadata['sample'].values():
        scene_times[scene_names[sample['scene_token']]].append(sample['timestamp'])
    ts_positions = {}
    for scene,times in scene_times.items():
        times.sort()
        ts_positions[scene] = {t:i for i,t in enumerate(times)}
        intervals[scene] = statistics.median(b-a for a,b in zip(times,times[1:]))/1e6
    ts = {}
    for variant,path in [('rigid','paired-all-sensor-support'),('point','paired-point-motion-support')]:
        rows = load(f'docs/evidence/truckscenes/{path}/object_counts.csv')
        ts[variant] = {}
        for row in rows:
            sample = metadata['sample'][row['sample_token']]
            annotation = metadata['sample_annotation'][row['annotation_token']]
            if (annotation['sample_token'],annotation['instance_token'])!=(row['sample_token'],row['instance_token']):
                raise ValueError('Invalid metadata join')
            if scene_names[sample['scene_token']] != row['scene']:
                raise ValueError('Scene mismatch')
            row.update(position=ts_positions[row['scene']][sample['timestamp']],time_s=sample['timestamp']/1e6,
                       visibility=metadata['visibility'][annotation['visibility_token']]['level'])
            ts[variant][row['annotation_token'],row['margin_m']] = row
        if len(ts[variant])!=len(rows):
            raise ValueError('Duplicate TruckScenes observation')
    # Rigid acquisition has more eligible samples; comparison retains point-corrected keys only.
    ts['rigid'] = {k:ts['rigid'][k] for k in ts['point']}
    if sources['docs/evidence/truckscenes/paired-point-motion-support/object_counts.csv']!=expected['docs/evidence/truckscenes/paired-point-motion-support/object_counts.csv']:
        raise ValueError('Changed corrected TruckScenes counts')
    tracks, runs, summaries, survival = [], [], [], []
    for dataset, variants, sectors in [('TruckDrive',td,(15,30,180)),('TruckScenes',ts,(180,))]:
        for variant, table in variants.items():
            rows = list(table.values()) if isinstance(table,dict) else table
            for margin in (0,.5):
                for threshold in (1,3):
                    for sector in sectors:
                        t,e,s = temporal(rows,dataset,variant,margin,threshold,sector,intervals)
                        tracks.extend(t); runs.extend(e); summaries.append(s)
        by_variant = {v:{(r['scene'],r['annotation_token'],float(r['margin_m'])):r for r in
                         (table.values() if isinstance(table,dict) else table)} for v,table in variants.items()}
        a,b = list(by_variant)
        for threshold in (1,3):
            def only(row):return int(row['radar_points'])>=threshold and int(row['lidar_points'])<threshold
            exact = {k[:2] for k,r in by_variant[a].items() if k[2]==0 and only(r)}
            sets = {(v,m):{k[:2] for k,r in table.items() if k[2]==m and only(r)}
                    for v,table in by_variant.items() for m in (0,.5)}
            for (v,m), keys in sets.items():
                survival.append(dict(dataset=dataset,threshold=threshold,baseline_variant=a,comparison_variant=v,
                                     comparison_margin_m=m,baseline_radar_only=len(exact),comparison_radar_only=len(keys),
                                     baseline_cases_surviving=len(exact&keys)))
    weather = []
    weather_groups = defaultdict(list)
    selected_classes = ('vehicle.car','vehicle.truck','human.pedestrian.adult','movable_object.trafficcone')
    for row in ts['point'].values():
        if float(row['margin_m'])!=0 or row['category'] not in selected_classes:
            continue
        distance = float(row['range_m'])
        band = next((f'{lo}-{hi}' for lo,hi in ((0,25),(25,50),(50,100)) if lo<=distance<hi),None)
        if band:
            weather_groups[row['scene'],row['category'],band,row['visibility']].append(row)
    for (scene,category,band,visibility), group in sorted(weather_groups.items()):
        description = prior['scene_descriptions'][scene]
        weather_name = next((w for w in ('rain','snow','overcast','clear') if w in description.lower()),'unspecified')
        weather.append(dict(scene=scene,description=description,weather=weather_name,category=category,
                            band_m=band,camera_visibility_level=visibility,**support_counts(group,1)))
    matched = []
    for key in sorted({(r['category'],r['band_m'],r['camera_visibility_level']) for r in weather}):
        chosen = [r for r in weather if (r['category'],r['band_m'],r['camera_visibility_level'])==key]
        names = {r['weather'] for r in chosen}
        if 'clear' in names and names&{'rain','snow','overcast'}:
            for row in chosen:
                matched.append(dict(**row,matched_condition_stratum=True))
    fog_frames = load('docs/evidence/radiate-fog/frames.csv')
    frame_ids = {int(r['frame']) for r in fog_frames}
    if frame_ids!=set(range(1,18)):
        raise ValueError('Unexpected fog eligibility')
    fog = []
    for kind,path,group_fields,margin in [('target','observations.csv',('track',),0),
                                          ('target','observations.csv',('track',),1),
                                          ('rotated_control','unlabelled_controls.csv',('parent_track','angle_deg'),0)]:
        rows = load('docs/evidence/radiate-fog/'+path)
        if kind=='target':rows = [r for r in rows if float(r['margin_m'])==margin]
        groups = defaultdict(list)
        for row in rows:
            if int(row['frame']) not in frame_ids:
                raise ValueError('Excluded fog frame scored')
            row.update(position=int(row['frame']),time_s=int(row['frame']))
            if not int(row['radar_contrast_gap20'])<=int(row['radar_contrast_gap10'])<=int(row['radar_contrast_pass']):
                raise ValueError('Contrast thresholds not nested')
            groups[tuple(row[k] for k in group_fields)].append(row)
        for group, rows in sorted(groups.items()):
            if len({r['frame'] for r in rows})!=len(rows):
                raise ValueError('Duplicate fog footprint frame')
            for gap,field in [(0,'radar_contrast_pass'),(10,'radar_contrast_gap10'),(20,'radar_contrast_gap20')]:
                eruns = episodes(rows,lambda r:int(r[field])==1,1)
                fog.append(dict(kind=kind,margin_m=margin,track=group[0],angle_deg=group[1] if len(group)>1 else 0,
                                contrast_gap=gap,observations=len(rows),positive=sum(int(r[field]) for r in rows),
                                episodes=len(eruns),persistent_episodes=sum(len(e)>=3 for e in eruns),
                                max_run_samples=max(map(len,eruns),default=0)))
    outputs = {'road_summary.csv':summaries,'road_tracks.csv':tracks,'road_episodes.csv':runs,
               'radar_only_sensitivity.csv':survival,'weather_strata.csv':weather,'weather_matched_strata.csv':matched,
               'fog_persistence.csv':fog}
    args.output_dir.mkdir(parents=True,exist_ok=True)
    saved_names = []
    for name,rows in outputs.items():
        path = args.output_dir/name
        write_csv(path,rows)
        if name in ('road_tracks.csv','road_episodes.csv'):
            buffer = io.BytesIO()
            with gzip.GzipFile(filename='',mode='wb',fileobj=buffer,mtime=0) as stream:
                stream.write(path.read_text(encoding='utf-8').encode())
            target = path.with_suffix('.csv.gz')
            target.write_bytes(buffer.getvalue())
            path.unlink()
            saved_names.append(target.name)
        else:saved_names.append(name)
    (args.output_dir/'road_manifest.json').write_text(json.dumps(dict(source_sha256=sources,
        scene_median_sample_interval_s=intervals,truckdrive_key_audit=td_key_audit,
        outputs_sha256_lf_uncompressed={n:digest(args.output_dir/n) for n in saved_names},
        limits=['Sampled support, not recognition or stopping','Missing scene sample breaks persistence',
                'TruckScenes rigid restricted to identical corrected keys','Publisher LiDAR mismatch unresolved',
                'Weather/class/visibility strata are descriptive; controls are not confirmed empty']),indent=2)+'\n')
    print('Executed R1/R2/W1:',len(tracks),'track-setting-sensor rows;',len(weather),'weather strata;',len(fog),'fog rows')


if __name__=='__main__':main()
