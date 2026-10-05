"""Make standalone evidence figures from the completed follow-up CSVs."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1] / "results/evidence/sprint-followup-oct01"


def rows(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def main():
    selected = {row["category"]: row for row in rows(ROOT / "class_range_support.csv") if row["band_m"] == "0-25"}
    categories = ("vehicle.truck", "vehicle.car", "human.pedestrian.adult", "vehicle.bicycle",
                  "movable_object.trafficcone", "static_object.traffic_sign")
    labels = ("Trucks", "Cars", "Pedestrians", "Bicycles", "Traffic cones", "Road signs")
    x = np.arange(len(categories))
    fig, ax = plt.subplots(figsize=(10,5.8))
    for shift, sensor, color in ((-.19,"lidar","#316a8a"),(.19,"radar","#b77327")):
        ax.bar(x+shift,[float(selected[c][sensor+"_percent"]) for c in categories],.38,label=sensor.title(),color=color)
    ax.set_xticks(x,labels)
    ax.set(ylabel="Labelled observations with an in-box return (%)",ylim=(0,111),title="Nearby coverage differs across object types")
    for i,c in enumerate(categories):
        row=selected[c]
        ax.text(i,103,f"n={row['observations']}\n{row['tracks']} tracks",ha="center",fontsize=8)
    ax.legend(loc="lower left");ax.grid(axis="y",alpha=.2)
    fig.text(.02,.015,"TruckScenes mini, 0–25 m; six sensors per suite, ego correction, exact boxes.\nGeometric evidence on LiDAR-conditioned labels; repeated observations. This is not detector accuracy.",fontsize=9)
    fig.tight_layout(rect=(0,.09,1,1));fig.savefig(ROOT/"nearby_object_coverage.png",dpi=160);plt.close(fig)

    selected=[row for row in rows(ROOT/"truckdrive_holdout_support.csv") if row["cohort"]=="vehicles" and row["variant"]=="aligned" and row["margin_m"]=="0"]
    fig,ax=plt.subplots(figsize=(10,5))
    x=np.arange(len(selected))
    for sensor,color in (("lidar","#316a8a"),("radar","#b77327")):
        y=[float(row[sensor+"_percent"]) if row[sensor+"_percent"] else np.nan for row in selected]
        ax.plot(x,y,marker="o",label=sensor.title(),color=color)
    ax.set_xticks(x,[row["band_m"] for row in selected]);ax.set(ylim=(0,108),xlabel="Vehicle-centre distance (m)",ylabel="In-box geometric support (%)",title="Vehicle coverage in two newly sampled TruckDrive clips")
    for i,row in enumerate(selected):ax.text(i,103,"n="+row["observations"],ha="center",fontsize=9)
    ax.legend();ax.grid(alpha=.2)
    fig.text(.02,.015,"Clips 28_3 and 28_15; six timing-eligible samples per clip. Acquisition alignment is a sensitivity hypothesis.\nDifferent clips from earlier exploratory sample, same released sensor platform; not recognition accuracy.",fontsize=9)
    fig.tight_layout(rect=(0,.09,1,1));fig.savefig(ROOT/"new_clip_vehicle_coverage.png",dpi=160);plt.close(fig)

    compared=rows(ROOT/"terrain/frame_comparison.csv")
    names=sorted({row["scenario"] for row in compared})
    fig,ax=plt.subplots(figsize=(10,5.8))
    x=np.arange(len(names))
    for shift,variant,label,color in ((-.19,"p64","Patch 64","#316a8a"),(.19,"p128","Patch 128","#77963c")):
        lookup={row["scenario"]:row for row in compared if row["variant"]==variant}
        ax.bar(x+shift,[float(lookup[name]["correct_percent"]) for name in names],.38,label=label,color=color)
    short=("Flight", "Field paths", "Training area", "Hills", "Garching", "Neubiberg rain", "Neubiberg sunny")
    labels=[name.split("_")[0]+"\n"+label for name,label in zip(names,short)]
    ax.set_xticks(x,labels,fontsize=8);ax.set(ylim=(0,105),ylabel="Correct eight-class labels on returned points (%)",title="More model context helps some recordings and harms others")
    ax.legend();ax.grid(axis="y",alpha=.2)
    fig.text(.02,.015,"Seven unseen frames, one per validation recording; January tuning recording excluded.\nSame checkpoint/seed/preprocessing; baseline repeat identical. Frame accuracy is not object recall or safe traversability.",fontsize=9)
    fig.tight_layout(rect=(0,.10,1,1));fig.savefig(ROOT/"terrain_context_by_recording.png",dpi=160);plt.close(fig)


if __name__ == "__main__":
    main()
