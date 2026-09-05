#!/usr/bin/env python3
"""Check TruckScenes v1.2.0 box matching/AP on CPU, without dataset or model files.

Run with the isolated environment documented in experiment-log/0006-truckscenes-preflight.md.
Synthetic scores are assertions only, never model benchmark evidence.
"""

import json
from importlib.metadata import version
from math import isclose

from truckscenes.eval.common.data_classes import EvalBoxes
from truckscenes.eval.common.utils import center_distance
from truckscenes.eval.detection.algo import accumulate, calc_ap
from truckscenes.eval.detection.config import config_factory
from truckscenes.eval.detection.data_classes import DetectionBox


def box(x, score=-1.0):
    return DetectionBox(
        sample_token="synthetic-car",
        translation=(x, 0.0, 0.0),
        size=(2.0, 4.0, 1.5),
        rotation=(1.0, 0.0, 0.0, 0.0),
        velocity=(0.0, 0.0),
        num_pts=1,
        detection_name="car",
        detection_score=score,
    )


def boxes(items):
    result = EvalBoxes()
    result.add_boxes("synthetic-car", items)
    result.add_boxes("synthetic-empty", [])
    return EvalBoxes.deserialize(json.loads(json.dumps(result.serialize())), DetectionBox)


def main():
    if version("truckscenes-devkit") != "1.2.0":
        raise SystemExit("This check pins truckscenes-devkit==1.2.0.")
    cfg = config_factory("detection_cvpr_2024")
    assert cfg.dist_ths == [0.5, 1.0, 2.0, 4.0]
    assert cfg.max_boxes_per_sample == 500
    assert len(cfg.class_range) == 12 and set(cfg.class_range.values()) == {75, 150}
    gt = boxes([box(10.0)])

    def ap(pred, threshold):
        assert set(pred.sample_tokens) == set(gt.sample_tokens)
        assert pred["synthetic-empty"] == []
        data = accumulate(gt, pred, "car", center_distance, threshold)
        return calc_ap(data, cfg.min_recall, cfg.min_precision)

    for threshold in cfg.dist_ths:
        assert isclose(ap(boxes([box(10.0, 0.9)]), threshold), 1.0)
        assert ap(boxes([]), threshold) == 0.0
        # A confident false positive before the correct box must reduce AP.
        assert 0.0 < ap(boxes([box(50.0, 1.0), box(10.0, 0.9)]), threshold) < 1.0

    # The official matcher uses distance < threshold, not <= threshold.
    assert ap(boxes([box(11.0, 0.9)]), 1.0) == 0.0
    assert isclose(ap(boxes([box(11.0, 0.9)]), 2.0), 1.0)
    print("PASS: stock config, JSON round trip, empty samples, perfect/missing/false-positive boxes and strict distance boundary.")
    print("CPU synthetic check only; no dataset loading, inference, range filtering or full DetectionEval run.")


if __name__ == "__main__":
    main()
