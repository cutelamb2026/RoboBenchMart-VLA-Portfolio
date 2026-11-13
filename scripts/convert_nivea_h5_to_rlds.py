#!/usr/bin/env python3
"""Convert one RoboBenchMart RGB-D trajectory to a readable TFDS/RLDS dataset.

Environment: conda activate rbm_rlds
Expected placement: ~/code/github/RoboBenchMart/scripts/convert_nivea_h5_to_rlds.py
Run from any directory: python ~/code/github/RoboBenchMart/scripts/convert_nivea_h5_to_rlds.py

No pretrained model or GPU needed. Preserves success and language fields from H5.
"""
from pathlib import Path
import os

# Avoid TensorFlow trying to reserve CUDA/GPU memory; this is an offline converter.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import h5py
import numpy as np
import tensorflow as tf
import tensorflow_datasets as tfds

ROOT = Path.home() / "code/github/RoboBenchMart"
SOURCE = (ROOT / "demo_envs/pick_to_basket/demos/motionplanning"
          / "nivea_mp_pipeline_test.rgbd.pd_joint_pos.physx_cpu.h5")
OUTPUT = ROOT / "artifacts/rlds_nivea"
CAMERAS = {
    "right_base_camera_link": (256, 256, 3),
    "left_base_camera_link": (256, 256, 3),
    "fetch_hand": (128, 128, 3),
}


def decode_instruction(traj):
    path = "obs/extra/language_instruction_bytes"
    if path not in traj:
        raise ValueError(
            f"Source H5 is missing {path}. "
            "We will not invent a language instruction. "
            "Please share the H5 'obs/extra' dataset names to adapt this script."
        )
    value = traj[path][0]
    if isinstance(value, (bytes, np.bytes_)):
        raw = bytes(value)
    elif isinstance(value, str):
        raw = value.encode("utf-8")
    else:
        raw = np.asarray(value, dtype=np.uint8).tobytes()
    return raw.rstrip(b"\x00").decode("utf-8")


class RbmNiveaSingle(tfds.core.GeneratorBasedBuilder):
    VERSION = tfds.core.Version("1.0.0")
    RELEASE_NOTES = {"1.0.0": "Single-episode offline H5 to RLDS verification."}

    def _info(self):
        step = tfds.features.FeaturesDict({
            "observation": tfds.features.FeaturesDict({
                **{key: tfds.features.Image(shape=shape,
                                             dtype=np.uint8,
                                             encoding_format="png")
                   for key, shape in CAMERAS.items()},
                "state": tfds.features.FeaturesDict({
                    "qpos": tfds.features.Tensor(shape=(15,), dtype=np.float32),
                    "qvel": tfds.features.Tensor(shape=(15,), dtype=np.float32),
                }),
            }),
            "action": tfds.features.Tensor(shape=(13,), dtype=np.float32),
            "is_first": tfds.features.Scalar(dtype=np.bool_),
            "is_last": tfds.features.Scalar(dtype=np.bool_),
            "is_terminal": tfds.features.Scalar(dtype=np.bool_),
            "is_success": tfds.features.Scalar(dtype=np.bool_),
            "language_instruction": tfds.features.Text(),
        })
        return self.dataset_info_from_configs(
            features=tfds.features.FeaturesDict({
                "steps": tfds.features.Dataset(step),
                "episode_metadata": tfds.features.FeaturesDict({
                    "file_path": tfds.features.Text(),
                }),
            })
        )

    def _split_generators(self, dl_manager):
        return {"train": self._generate_examples()}

    def _generate_examples(self):
        with h5py.File(SOURCE, "r") as f:
            traj = f["traj_0"]
            n = len(traj["actions"])
            obs = traj["obs"]
            cameras = obs["sensor_data"]
            instruction = decode_instruction(traj)

            if n != 336:
                raise ValueError(f"Expected 336 actions in this test, found {n}")
            if traj["actions"].shape != (n, 13):
                raise ValueError(f"Unexpected actions shape: {traj['actions'].shape}")
            for field in ("qpos", "qvel"):
                if obs["agent"][field].shape != (n + 1, 15):
                    raise ValueError(f"Unexpected {field} shape: {obs['agent'][field].shape}")
            for name, shape in CAMERAS.items():
                actual = cameras[name]["rgb"].shape
                if actual != (n + 1, *shape):
                    raise ValueError(f"Unexpected {name} rgb shape: {actual}")
            for field in ("success", "terminated"):
                if traj[field].shape != (n,):
                    raise ValueError(f"Unexpected {field} shape: {traj[field].shape}")

            print("SOURCE:", SOURCE, flush=True)
            print("ACTIONS:", n, flush=True)
            print("LANGUAGE:", repr(instruction), flush=True)
            print("SOURCE FINAL SUCCESS:", bool(traj["success"][-1]), flush=True)

            # H5 contains n actions and n+1 observations. Match RLDS steps to
            # the PRE-action observation at each i, following the original builder.
            steps = []
            for i in range(n):
                steps.append({
                    "observation": {
                        **{name: cameras[name]["rgb"][i] for name in CAMERAS},
                        "state": {
                            "qpos": obs["agent"]["qpos"][i],
                            "qvel": obs["agent"]["qvel"][i],
                        },
                    },
                    "action": traj["actions"][i],
                    "is_first": i == 0,
                    "is_last": i == n - 1,
                    "is_terminal": bool(traj["terminated"][i]),
                    "is_success": bool(traj["success"][i]),
                    "language_instruction": instruction,
                })
            yield "traj_0", {
                "steps": steps,
                "episode_metadata": {"file_path": str(SOURCE)},
            }


def main():
    if not SOURCE.is_file():
        raise FileNotFoundError(f"H5 not found: {SOURCE}")

    builder = RbmNiveaSingle(data_dir=str(OUTPUT))
    builder.download_and_prepare()

    dataset = builder.as_dataset(split="train")
    total_episodes = 0
    for episode in dataset:
        total_episodes += 1
        n = 0
        first = last = None
        for step in episode["steps"]:
            if first is None:
                first = step
            last = step
            n += 1
        assert n == 336, f"Wrong RLDS step count: {n}"
        assert first is not None and last is not None
        assert bool(first["is_first"].numpy())
        assert not bool(first["is_last"].numpy())
        assert bool(last["is_last"].numpy())
        assert not bool(last["is_first"].numpy())
        assert tuple(first["action"].shape) == (13,)
        for field in ("qpos", "qvel"):
            assert tuple(first["observation"]["state"][field].shape) == (15,)
        for name, shape in CAMERAS.items():
            assert tuple(first["observation"][name].shape) == shape
        with h5py.File(SOURCE, "r") as f:
            original = f["traj_0"]
            np.testing.assert_allclose(first["action"].numpy(), original["actions"][0])
            np.testing.assert_allclose(last["action"].numpy(), original["actions"][-1])
            np.testing.assert_array_equal(
                first["observation"]["left_base_camera_link"].numpy(),
                original["obs/sensor_data/left_base_camera_link/rgb"][0],
            )
            assert bool(last["is_success"].numpy()) == bool(original["success"][-1])
            assert bool(last["is_terminal"].numpy()) == bool(original["terminated"][-1])
        print("EPISODES:", total_episodes)
        print("STEPS:", n)
        print("ACTION SHAPE:", tuple(first["action"].shape))
        print("LANGUAGE:", first["language_instruction"].numpy().decode("utf-8"))
        print("FINAL SUCCESS:", bool(last["is_success"].numpy()))
        print("FINAL TERMINAL:", bool(last["is_terminal"].numpy()))

    assert total_episodes == 1, f"Expected 1 episode, found {total_episodes}"
    print("RLDS CONVERSION AND READBACK: PASS")
    print("OUTPUT:", builder.data_path)


if __name__ == "__main__":
    main()
