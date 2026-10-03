"""Combine completed STONE recordings without pooling away environment effects."""
import csv
from pathlib import Path
import numpy as np
from compare_truckscenes_raw import write_csv


def main():
    root=Path('docs/evidence');out=root/'stone-environments';out.mkdir(exist_ok=True)
    rows=[]
    for name in ('farmland','lake','land'):
        folder=root/'stone-pilot' if name=='farmland' else out/name
        with (folder/'support_summary.csv').open(newline='') as file:
            for row in csv.DictReader(file):
                if row['elevation_deg']=='10' and row['tolerance_m']=='0.8' and row['group'] in ('near_ground_geometry','raised_geometry'):
                    rows.append(dict(recording=name,**row))
    write_csv(out/'comparison.csv',rows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(13,8),sharey=True,sharex=True)
    bands=['2-10','10-20','20-30','30-40'];x=np.arange(4)
    for column,name in enumerate(('farmland','lake','land')):
        for line,group in enumerate(('near_ground_geometry','raised_geometry')):
            ax=axes[line,column];lookup={(r['variant'],r['band_m']):r for r in rows if r['recording']==name and r['group']==group}
            for variant,sensor,label,color,style in [('aligned','lidar','LiDAR','#2878b5','-'),('aligned','radar','Radar: bridged + timing','#d65f00','-'),('ros_origin','radar','Radar: ROS origin','#7851a9','--')]:
                ax.plot(x,[float(lookup[variant,b][sensor+'_percent']) for b in bands],marker='o',ls=style,color=color,label=label)
            ax.set(title=name+' / '+('near ground' if line==0 else 'raised'),xticks=x,xticklabels=bands,ylim=(0,105),xlim=(-.3,3.3))
            ax.grid(alpha=.2)
            for i,b in enumerate(bands):ax.text(i,4,'n='+lookup['aligned',b]['reference_voxels'],ha='center',fontsize=7)
    axes[0,0].legend(fontsize=8,loc='center left')
    for ax in axes[1]:ax.set_xlabel('Planar range (m)')
    for ax in axes[:,0]:ax.set_ylabel('Reference voxel support (%)')
    fig.suptitle('STONE: 20 frames per recording, 0.8 m support tolerance')
    fig.text(.02,.02,'LiDAR-derived labels; radar physical translations unresolved; no occlusion mask. Folder names identify recordings. Not detector accuracy.',fontsize=9)
    fig.tight_layout(rect=(0,.06,1,.95));fig.savefig(out/'environment_comparison.png',dpi=150);plt.close(fig)


if __name__=='__main__':main()
