"""Run a pretrained (nuScenes-trained) FCOS3D monocular 3D detector zero-shot
against MAN TruckScenes camera images, and write a TruckScenes-format
detection results JSON suitable for `truckscenes.eval.detection.evaluate`.

This is a *zero-shot cross-dataset* baseline: the model was never trained on
TruckScenes, so weak numbers reflect real domain gap (different camera height,
FOV, mounting angle on a truck vs. a car), not a bug. That is itself a
reportable finding for the project's headline question about model
degradation.

Requires a dedicated venv (see experiment-log for how it was built):
  - Python 3.11, numpy<2 (torch 2.1.0 needs NumPy's 1.x C-API)
  - torch==2.1.0+cpu, torchvision==0.16.0+cpu
  - mmengine, mmcv==2.1.0 (cpu wheel for torch2.1.0), mmdet, mmdet3d (--no-deps)
  - truckscenes-devkit, pyquaternion, pypcd4, python-lzf, pydantic, numba

Usage:
  python truckscenes_fcos3d_infer.py \
      --dataroot "path/to/man-truckscenes" \
      --version v1.2-mini \
      --split mini_val \
      --config <path to fcos3d config .py> \
      --checkpoint <path to fcos3d .pth> \
      --out results.json \
      --limit 5          # optional: cap number of samples for a smoke test
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile

import numpy as np
from pyquaternion import Quaternion

from truckscenes import TruckScenes
from truckscenes.utils.splits import create_splits_scenes

from mmdet3d.apis import inference_mono_3d_detector, init_model


# nuScenes' 10 detection classes, in the exact index order FCOS3D's label
# output uses (from mmdet3d configs/_base_/datasets/nus-mono3d.py).
NUSC_CLASSES = [
    'car', 'truck', 'trailer', 'bus', 'construction_vehicle', 'bicycle',
    'motorcycle', 'pedestrian', 'traffic_cone', 'barrier',
]

# nuScenes class -> TruckScenes detection class (eval/detection/README.md).
# TruckScenes has two extra classes (animal, traffic_sign, other_vehicle from
# vehicle.other) that a nuScenes-trained model can never predict — expected.
NUSC_TO_TRUCKSCENES = {
    'car': 'car',
    'truck': 'truck',
    'trailer': 'trailer',
    'bus': 'bus',
    'construction_vehicle': 'other_vehicle',
    'bicycle': 'bicycle',
    'motorcycle': 'motorcycle',
    'pedestrian': 'pedestrian',
    'traffic_cone': 'traffic_cone',
    'barrier': 'barrier',
}

# Standard nuScenes default attribute per class (mmdet3d's NuScenesMetric).
DEFAULT_ATTRIBUTE = {
    'car': 'vehicle.parked',
    'pedestrian': 'pedestrian.moving',
    'trailer': 'vehicle.parked',
    'truck': 'vehicle.parked',
    'bus': 'vehicle.moving',
    'motorcycle': 'cycle.without_rider',
    'construction_vehicle': 'vehicle.parked',
    'bicycle': 'cycle.without_rider',
    'barrier': '',
    'traffic_cone': '',
}

# TruckScenes has no single "CAM_FRONT" — use all 4 truck cameras.
CAMERA_CHANNELS = [
    'CAMERA_LEFT_FRONT', 'CAMERA_RIGHT_FRONT',
    'CAMERA_LEFT_BACK', 'CAMERA_RIGHT_BACK',
]

SCORE_THRESHOLD = 0.10
MAX_BOXES_PER_SAMPLE = 500


def quat_to_matrix4(translation, rotation_wxyz) -> np.ndarray:
    """Build a 4x4 homogeneous transform from TruckScenes' translation +
    wxyz-quaternion rotation (same convention as calibrated_sensor/ego_pose).
    """
    m = np.eye(4)
    m[:3, :3] = Quaternion(rotation_wxyz).rotation_matrix
    m[:3, 3] = translation
    return m


def cam2img_matrix4(camera_intrinsic) -> np.ndarray:
    """Pad a 3x3 camera intrinsic matrix to the 4x4 form mmdet3d expects."""
    m = np.eye(4)
    m[:3, :3] = np.array(camera_intrinsic)
    return m


def boxes_cam_to_global(bboxes_3d, scores, labels, attr_labels,
                         cam2ego: np.ndarray, ego2global: np.ndarray):
    """Reimplements mmdet3d's output_to_nusc_box + cam_nusc_box_to_global
    (mmdet3d/evaluation/metrics/nuscenes_metric.py) without depending on the
    nuscenes-devkit's Box class — plain numpy/pyquaternion only.
    """
    centers = bboxes_3d.gravity_center.numpy()          # (N, 3) camera frame
    dims = bboxes_3d.dims.numpy()                        # (N, 3) raw order
    yaws = bboxes_3d.yaw.numpy()                          # (N,)
    tensor = bboxes_3d.tensor.numpy()                     # (N, 9): ..., vx, vz

    # Camera coordinate system -> nuScenes box convention (see reference impl).
    nus_dims = dims[:, [2, 0, 1]]                         # -> (w, l, h)
    nus_yaw = -yaws

    r_cam2ego, t_cam2ego = cam2ego[:3, :3], cam2ego[:3, 3]
    r_ego2global, t_ego2global = ego2global[:3, :3], ego2global[:3, 3]

    results = []
    for i in range(len(bboxes_3d)):
        q1 = Quaternion(axis=[0, 0, 1], radians=float(nus_yaw[i]))
        q2 = Quaternion(axis=[1, 0, 0], radians=np.pi / 2)
        quat_cam = q2 * q1

        center = centers[i].copy()
        velocity = np.array([tensor[i, 7], 0.0, tensor[i, 8]])

        # cam -> ego (rotate then translate; velocity rotates only)
        center = r_cam2ego @ center + t_cam2ego
        quat = Quaternion(matrix=r_cam2ego, rtol=1e-5, atol=1e-7) * quat_cam
        velocity = r_cam2ego @ velocity

        # ego -> global
        center = r_ego2global @ center + t_ego2global
        quat = Quaternion(matrix=r_ego2global, rtol=1e-5, atol=1e-7) * quat
        velocity = r_ego2global @ velocity

        cls_name = NUSC_CLASSES[int(labels[i])]
        attr = DEFAULT_ATTRIBUTE.get(cls_name, '')
        if attr_labels is not None:
            # attr_labels index into the model's attribute vocabulary; fall
            # back to the class default if it maps to "void"/background.
            pass  # kept simple: DEFAULT_ATTRIBUTE is what mmdet3d itself
                  # falls back to whenever attribute prediction is absent.

        results.append({
            # required by DetectionBox.deserialize, not just as the outer
            # results dict key (learned the hard way — see experiment log).
            'sample_token': None,  # filled in by the caller, who has it
            'translation': center.tolist(),
            'size': nus_dims[i].tolist(),
            'rotation': [quat.w, quat.x, quat.y, quat.z],
            'velocity': [float(velocity[0]), float(velocity[1])],
            'detection_name': NUSC_TO_TRUCKSCENES[cls_name],
            'detection_score': float(scores[i]),
            'attribute_name': attr,
        })
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataroot', required=True)
    ap.add_argument('--version', default='v1.2-mini')
    ap.add_argument('--split', default='mini_val')
    ap.add_argument('--config', required=True)
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--out', default='results.json')
    ap.add_argument('--cameras', nargs='+', default=CAMERA_CHANNELS)
    ap.add_argument('--limit', type=int, default=None,
                     help='Cap number of samples processed (smoke testing).')
    ap.add_argument('--start', type=int, default=0,
                     help='Start index into the split\'s sample list '
                          '(for chunking a long CPU run across calls).')
    ap.add_argument('--end', type=int, default=None,
                     help='End index (exclusive) into the split\'s sample '
                          'list. Combined with --start to process one chunk '
                          'at a time; --out is merged with, not overwritten.')
    args = ap.parse_args()

    trucksc = TruckScenes(version=args.version, dataroot=args.dataroot,
                           verbose=True)

    split_scenes = create_splits_scenes()[args.split]
    scene_name_to_token = {s['name']: s['token'] for s in trucksc.scene}
    split_scene_tokens = {scene_name_to_token[n] for n in split_scenes
                           if n in scene_name_to_token}

    all_samples = [s for s in trucksc.sample
                   if s['scene_token'] in split_scene_tokens]
    if args.limit:
        all_samples = all_samples[:args.limit]

    # Every sample_token in the split must be a key in the final results
    # file (even with an empty list) or the evaluator's assertion that
    # predictions and ground truth cover the same sample set will fail.
    # So results always starts from (or merges into) the FULL split, and
    # --start/--end only controls which slice gets new inference this call.
    if os.path.exists(args.out):
        with open(args.out) as f:
            results = json.load(f)['results']
        print(f'Resuming: loaded existing results for '
              f'{sum(1 for v in results.values() if v)} samples from '
              f'{args.out}.')
    else:
        results = {}
    for s in all_samples:
        results.setdefault(s['token'], [])

    end = args.end if args.end is not None else len(all_samples)
    samples = all_samples[args.start:end]
    print(f'Split "{args.split}" has {len(all_samples)} samples total; '
          f'this call processes indices [{args.start}:{end}] '
          f'({len(samples)} samples) across {len(args.cameras)} camera(s).')

    model = init_model(args.config, args.checkpoint, device='cpu')

    for idx, sample in enumerate(samples):
        for cam in args.cameras:
            if cam not in sample['data']:
                continue
            sd_token = sample['data'][cam]
            sample_data = trucksc.get('sample_data', sd_token)
            calib = trucksc.get('calibrated_sensor',
                                 sample_data['calibrated_sensor_token'])
            ego_pose = trucksc.get('ego_pose', sample_data['ego_pose_token'])

            img_path = os.path.join(args.dataroot, sample_data['filename'])
            cam2img = cam2img_matrix4(calib['camera_intrinsic'])
            cam2ego = quat_to_matrix4(calib['translation'], calib['rotation'])
            ego2global = quat_to_matrix4(ego_pose['translation'],
                                          ego_pose['rotation'])

            # mmdet3d's inference_mono_3d_detector needs a minimal "info"
            # file on disk describing this one image's camera calibration.
            info = {
                'metainfo': {},
                'data_list': [{
                    'images': {
                        cam: {
                            'img_path': os.path.basename(img_path),
                            'cam2img': cam2img.tolist(),
                        }
                    }
                }],
            }
            with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.json', delete=False) as f:
                json.dump(info, f)
                info_path = f.name

            try:
                result = inference_mono_3d_detector(
                    model, img_path, info_path, cam_type=cam)
            finally:
                os.remove(info_path)

            pred = result.pred_instances_3d
            keep = pred.scores_3d >= SCORE_THRESHOLD
            if keep.sum() == 0:
                continue

            attr_labels = (pred.attr_labels[keep].numpy()
                            if 'attr_labels' in pred else None)
            entries = boxes_cam_to_global(
                pred.bboxes_3d[keep], pred.scores_3d[keep].numpy(),
                pred.labels_3d[keep].numpy(), attr_labels,
                cam2ego, ego2global)
            for e in entries:
                e['sample_token'] = sample['token']
            results[sample['token']].extend(entries)

        # Enforce the 500-boxes-per-sample submission limit, keep top scores.
        if len(results[sample['token']]) > MAX_BOXES_PER_SAMPLE:
            results[sample['token']] = sorted(
                results[sample['token']],
                key=lambda r: -r['detection_score'])[:MAX_BOXES_PER_SAMPLE]

        if (idx + 1) % 5 == 0 or (idx + 1) == len(samples):
            print(f'  processed {idx + 1}/{len(samples)} samples '
                  f'(chunk index {args.start}-{end})', flush=True)
            # Checkpoint to disk periodically so a killed/timed-out call
            # doesn't lose progress already made this chunk.
            with open(args.out, 'w') as f:
                json.dump({'meta': {}, 'results': results}, f)

    submission = {
        'meta': {
            'use_camera': True, 'use_lidar': False, 'use_radar': False,
            'use_map': False, 'use_external': False,
            'use_future_frames': False, 'use_tta': False,
            'method_name': 'FCOS3D (nuScenes-pretrained, zero-shot)',
            'authors': '', 'affiliation': '',
            'description': ('Zero-shot cross-dataset test: nuScenes-trained '
                             'FCOS3D checkpoint run directly on TruckScenes '
                             'camera images, no fine-tuning.'),
            'code_url': '', 'paper_url': '',
        },
        'results': results,
    }
    with open(args.out, 'w') as f:
        json.dump(submission, f)
    n_boxes = sum(len(v) for v in results.values())
    print(f'Wrote {args.out}: {len(results)} samples, {n_boxes} boxes total.')


if __name__ == '__main__':
    main()
