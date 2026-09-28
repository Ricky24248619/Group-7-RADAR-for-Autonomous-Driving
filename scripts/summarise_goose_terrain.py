"""Summarise scenario-stratified ground-category errors, keeping denominators."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from compare_truckscenes_raw import write_csv

BANDS=('0-25','25-50','50-75','75-100','100-150','150+')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('docs/evidence/goose-stratified/ground'))
    args=parser.parse_args()
    def read(name):
        with (args.root/name).open(newline='') as f:return list(csv.DictReader(f))
    scenario=read('scenario_group_confusion.csv')
    pooled=read('saved_group_confusion.csv')
    frames=read('saved_frame_group_confusion.csv')
    fine=read('saved_fine_confusion.csv')
    summary=[]
    for group in ('ground_surface','obstacle_candidate'):
        for band in BANDS:
            rows=[r for r in scenario if r['true_group']==group and r['band_m']==band]
            overall=next((r for r in pooled if r['true_group']==group and r['band_m']==band),None)
            if overall is None:continue
            rates=[float(r['ground_category_percent']) for r in rows]
            summary.append(dict(group=group,band_m=band,points=int(overall['points']),
                                ground_category_percent=float(overall['ground_category_percent']),
                                contributing_scenarios=len(rows),
                                contributing_frames=sum(r['true_group']==group and r['band_m']==band for r in frames),
                                equal_scenario_mean_percent=float(np.mean(rates)),
                                scenario_min_percent=min(rates),scenario_max_percent=max(rates)))
    write_csv(args.root/'range_summary.csv',summary)
    # Keep actual fine-label confusions visible rather than interpreting every
    # obstacle-group point as a car, rock or path-blocking obstacle.
    mistakes=[r for r in fine if int(r['points']) and
              ((r['true_group']=='ground_surface' and r['predicted_class'] not in ('artificial_ground','natural_ground')) or
               (r['true_group']=='obstacle_candidate' and r['predicted_class'] in ('artificial_ground','natural_ground')))]
    write_csv(args.root/'ground_category_mistakes.csv',sorted(mistakes,key=lambda r:(BANDS.index(r['band_m']),-int(r['points']))))
    classes=defaultdict(lambda:[0,0])
    for row in fine:
        key=(row['band_m'],row['true_group'],row['true_class'])
        classes[key][0]+=int(row['points'])
        if row['predicted_class'] in ('artificial_ground','natural_ground'):
            classes[key][1]+=int(row['points'])
    write_csv(args.root/'class_ground_predictions.csv',[
        dict(band_m=b,true_group=g,true_class=c,points=total,ground_category_points=ground,
             ground_category_percent=100*ground/total)
        for (b,g,c),(total,ground) in sorted(classes.items()) if total])
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    scenarios=sorted({r['scenario'] for r in scenario})
    for ax,group,title in zip(axes,('ground_surface','obstacle_candidate'),
                             ('Ground points assigned ground category (higher is better)',
                              'Obstacle points assigned ground category (lower is better)')):
        for name in scenarios:
            chosen={r['band_m']:float(r['ground_category_percent']) for r in scenario if r['scenario']==name and r['true_group']==group}
            ax.plot(range(6),[chosen.get(b,np.nan) for b in BANDS],alpha=.65,linewidth=1,marker='.',label=name)
            for row in scenario:
                endpoint=0 if group=='ground_surface' else 100
                if row['scenario']==name and row['true_group']==group and int(row['points'])<50 and float(row['ground_category_percent'])==endpoint:
                    ax.annotate('n='+row['points'],(BANDS.index(row['band_m']),float(row['ground_category_percent'])),
                                xytext=(4,-12 if float(row['ground_category_percent'])==100 else 6),textcoords='offset points',fontsize=6)
        chosen={r['band_m']:r['ground_category_percent'] for r in summary if r['group']==group}
        ax.plot(range(6),[chosen.get(b,np.nan) for b in BANDS],color='black',linewidth=2,marker='o',label='Pooled returned points')
        ax.set(title=title,ylabel='Percent of labelled returned points',xlabel='Planar distance (m)',ylim=(-2,102))
        ax.set_xticks(range(6),BANDS);ax.grid(alpha=.2)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',ncol=3,fontsize=7)
    count=json.loads((args.root/'manifest.json').read_text())['frames']
    fig.suptitle(f'GOOSE PTv3: {count} verified frames across {len(scenarios)} scenarios')
    fig.text(.5,.16,'Thin lines include sparse scenario/band groups; see CSV denominators. Returned-point classification, not object detection or unseen terrain coverage.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.17,1,.95));fig.savefig(args.root/'scenario_errors.png',dpi=150);plt.close(fig)
    print('Wrote range_summary.csv, ground_category_mistakes.csv and scenario_errors.png')


if __name__=='__main__':main()
