"""Describe distance-dependent paired support separately for each dataset."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from audit_long_range_support import describe
from compare_truckscenes_raw import write_csv


EDGES = (0,50,75,100,125,150,175,200,225,250,300,350,400,float('inf'))


def read_rows(path):
    with path.open() as f:
        rows=list(csv.DictReader(f))
    for row in rows:
        for key in ('margin_m','range_m'):
            row[key]=float(row[key])
        for key in ('lidar_points','radar_points'):
            row[key]=int(row[key])
    return rows


def profile(rows):
    """Preserve zero-support boxes in point-count quantiles and denominators."""
    result = describe(rows)
    for mode in ('lidar','radar'):
        counts = np.array([r[mode+'_points'] for r in rows])
        for threshold in (3,5):
            result[f'{mode}_ge_{threshold}_percent'] = float(100*np.mean(counts>=threshold))
        for quantile in (25,50,75,90):
            result[f'{mode}_points_p{quantile}'] = float(np.percentile(counts,quantile))
        tracks = defaultdict(list)
        for row in rows:
            tracks[row['instance_token']].append(row[mode+'_points']>0)
        result[mode+'_equal_track_percent'] = float(100*np.mean([np.mean(v) for v in tracks.values()]))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--truckdrive', type=Path, required=True)
    parser.add_argument('--truckdrive-aligned', type=Path)
    parser.add_argument('--truckscenes', type=Path, default=Path('docs/evidence/truckscenes/paired-point-motion-support/object_counts.csv'))
    parser.add_argument('--output-dir', type=Path, default=Path('docs/evidence/long-range-cross-dataset'))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    summaries, groups, cohorts, source_hashes = [], [], [], {}
    for dataset,path in [('TruckScenes mini',args.truckscenes),('TruckDrive scene_28_1',args.truckdrive)]:
        source_hashes[str(path).replace('\\','/')] = hashlib.sha256(path.read_text().encode()).hexdigest()
        rows = read_rows(path)
        for margin in (0,.5):
            exact = [r for r in rows if r['margin_m']==margin]
            if len({r['annotation_token'] for r in exact}) != len(exact):
                raise ValueError('Duplicate annotation token')
            for low,high in zip(EDGES[:-1],EDGES[1:]):
                cohort = [r for r in exact if low<=r['range_m']<high]
                if cohort:
                    summaries.append(dict(dataset=dataset,margin_m=margin,range_low_m=low,
                        range_high_m=high if np.isfinite(high) else '',
                        band_m=f'{low}-{high}' if np.isfinite(high) else f'{low}+',**profile(cohort)))
            for low,high in [(100,150),(150,200),(200,250),(250,300),(300,400)]:
                classes = defaultdict(list)
                for row in exact:
                    if low<=row['range_m']<high:
                        classes[row['category']].append(row)
                for name,cohort in sorted(classes.items()):
                    groups.append(dict(dataset=dataset,margin_m=margin,band_m=f'{low}-{high}',
                        category=name,**profile(cohort)))
                for name,predicate in [
                    ('all',lambda r:True),
                    ('vehicles',lambda r:r['category'].startswith(('Vehicle','vehicle.')) and 'ego' not in r['category'].lower()),
                    ('passenger_cars',lambda r:r['category'] in ('Vehicle-Passenger','vehicle.car')),
                    ('forward_30deg',lambda r:'azimuth_deg' in r and abs(float(r['azimuth_deg']))<=30)]:
                    cohort=[r for r in exact if low<=r['range_m']<high and predicate(r)]
                    if cohort:
                        cohorts.append(dict(dataset=dataset,margin_m=margin,band_m=f'{low}-{high}',cohort=name,**profile(cohort)))
    write_csv(args.output_dir/'range_profiles.csv',summaries)
    write_csv(args.output_dir/'class_profiles.csv',groups)
    write_csv(args.output_dir/'cohort_profiles.csv',cohorts)
    if args.truckdrive_aligned:
        path=args.truckdrive_aligned
        source_hashes[str(path).replace('\\','/')]=hashlib.sha256(path.read_text().encode()).hexdigest()
        timing=timing_sensitivity(read_rows(args.truckdrive),read_rows(path))
        write_csv(args.output_dir/'timing_sensitivity.csv',timing)
        plot_timing(timing,args.output_dir)
    (args.output_dir/'manifest.json').write_text(json.dumps(dict(input_sha256_lf_normalized=source_hashes,
        band_semantics='lower inclusive, upper exclusive; no empty bands reported',
        point_quantiles='Across every labelled observation, including zero-point boxes',
        interpretation='Separate descriptive datasets, never pooled; different hardware, annotation and processing protocols; no trained detector scores'),indent=2)+'\n')
    plot(summaries,args.output_dir)
    for row in summaries:
        if row['margin_m']==0:
            print(row['dataset'],row['band_m'],row['observations'],round(row['lidar_percent'],2),round(row['radar_percent'],2),
                  'median points',row['lidar_points_p50'],row['radar_points_p50'])


def timing_sensitivity(static,aligned):
    keys={(r['annotation_token'],r['margin_m']) for r in aligned}
    static=[r for r in static if (r['annotation_token'],r['margin_m']) in keys]
    if {(r['annotation_token'],r['margin_m']) for r in static} != keys:
        raise ValueError('Aligned and static annotations must match')
    reference={(r['annotation_token'],r['margin_m']):r for r in static}
    for row in aligned:
        prior=reference[row['annotation_token'],row['margin_m']]
        if any(prior[k]!=row[k] for k in ('range_m','category','instance_token','scene')):
            raise ValueError('Timing comparison must preserve annotation geometry and identity')
    output=[]
    for mode,rows in [('static_same_subset',static),('acquisition_aligned',aligned)]:
        for margin in (0,.5):
            for low,high in [(100,150),(150,200),(200,250),(250,300),(300,400)]:
                for cohort in ('all','vehicles'):
                    group=[r for r in rows if r['margin_m']==margin and low<=r['range_m']<high
                           and (cohort=='all' or r['category'].startswith('Vehicle'))]
                    if group:output.append(dict(mode=mode,margin_m=margin,band_m=f'{low}-{high}',cohort=cohort,**profile(group)))
    return output


def plot_timing(rows,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for column,mode in enumerate(('static_same_subset','acquisition_aligned')):
        for margin,style in [(0,'-o'),(.5,'--s')]:
            subset=[r for r in rows if r['mode']==mode and r['cohort']=='vehicles' and r['margin_m']==margin]
            for sensor,color in [('lidar','#247b91'),('radar','#ce8425')]:
                axes[column].plot([r['band_m'] for r in subset],[r[sensor+'_percent'] for r in subset],style,
                    color=color,label=sensor.title()+(' exact box' if margin==0 else ' +0.5 m faces'))
        axes[column].set(ylim=(0,105),xlabel='Planar object-centre range (m)',ylabel='Vehicle observations with an in-box return (%)',
            title='Static calibration' if column==0 else 'Acquisition-pose correction hypothesis')
        axes[column].grid(alpha=.2);axes[column].legend(fontsize=8)
    fig.suptitle('TruckDrive: does the apparent sensor advantage survive timing and box sensitivity?')
    fig.text(.015,.02,'Same 198 frames in both panels. Repeated tracks; geometric support, not detector accuracy.\n'
             'Expanded boxes can include background. Acquisition correction does not reproduce internal joint-cloud deskew.',fontsize=9)
    fig.tight_layout(rect=(0,.09,1,.93));fig.savefig(output/'truckdrive_vehicle_sensitivity.png',dpi=160);plt.close(fig)


def plot(rows,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(13,9))
    for column,dataset in enumerate(('TruckScenes mini','TruckDrive scene_28_1')):
        cohort=[r for r in rows if r['dataset']==dataset and r['margin_m']==0]
        x=np.arange(len(cohort))
        for mode,color in [('lidar','#247b91'),('radar','#ce8425')]:
            axes[0,column].plot(x,[r[mode+'_percent'] for r in cohort],'-o',color=color,label=mode.title()+' >=1 point')
            axes[0,column].plot(x,[r[mode+'_ge_5_percent'] for r in cohort],'--',color=color,label=mode.title()+' >=5 points')
            axes[1,column].plot(x,[r[mode+'_points_p50'] for r in cohort],'-o',color=color,label=mode.title())
        for ax in axes[:,column]:
            ax.set_xticks(x, [r['band_m'] for r in cohort],rotation=55,ha='right')
            ax.grid(alpha=.2)
        axes[0,column].set(title=dataset,ylabel='Labelled boxes with geometric support (%)',ylim=(-3,105))
        axes[0,column].legend(fontsize=8)
        axes[1,column].set(yscale='symlog',ylim=(0,None),ylabel='Median in-box returns (zeros included)',xlabel='Planar box-centre distance (m)')
        for i,r in enumerate(cohort):
            axes[0,column].text(i,2,str(r['observations']),rotation=90,ha='center',fontsize=7)
    fig.suptitle('Long-range sensing: coverage and shape evidence are different questions',fontsize=15)
    fig.text(.015,.014,'Numbers along lower edge are box observations, not independent trials. Exact boxes; no detector inference.\n'
        'Different sensor configurations and preprocessing; curves are descriptive, not a controlled cross-dataset ranking.',fontsize=10)
    fig.tight_layout(rect=(0,.065,1,.96))
    fig.savefig(output/'distance_profiles.png',dpi=160)
    plt.close(fig)


if __name__=='__main__':
    main()
