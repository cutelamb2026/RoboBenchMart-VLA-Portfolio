import multiprocessing as mp
from functools import partial

import os

from copy import deepcopy
import time
import argparse
import gymnasium as gym
import numpy as np
from tqdm import tqdm
import os.path as osp
from typing import Optional
from pathlib import Path
import json
import csv

from mani_skill.utils.structs.pose import to_sapien_pose
from mani_skill.utils.wrappers.record import RecordEpisode
from mani_skill.trajectory.merge_trajectory import merge_trajectories


import sys
sys.path.append('.')
from dsynth.envs import *
from dsynth.robots import *
from dsynth.web_utils import WebsocketClient


OPEN = 1
CLOSED = -1

def prepare_obs(obs_raw, language_instruction, time_step):
    left_base_camera_link = obs_raw['sensor_data']['left_base_camera_link']['rgb'][0].cpu().numpy()
    fetch_hand = obs_raw['sensor_data']['fetch_hand']['rgb'][0].cpu().numpy()
    right_base_camera_link = obs_raw['sensor_data']['right_base_camera_link']['rgb'][0].cpu().numpy()
    state = obs_raw['agent']['qpos'][0].cpu().numpy()
    observation = {
        "observation/image": left_base_camera_link,
        "observation/extra_image": right_base_camera_link,
        "observation/wrist_image": fetch_hand,
        "observation/state": state,
        "prompt": language_instruction,
        "time_step": time_step
    }
    return observation


def parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene-dir", type=str, help=f"Path to scene directory")

    parser.add_argument("-e", "--env-id", type=str, default=None, help=f"Environment to run motion planning solver on.")
    parser.add_argument("--json-path", type=str, default=None, help=f"Path to json file with parameters of the environment. \
                        --env-id is ignored if specified.")

    parser.add_argument("--eval-subdir", type=str, default='octo_pt')

    parser.add_argument("--start-seed", type=int, default=0)
    parser.add_argument("--robot-init-pose-start-seed", type=int, default=None, help="Controls robot init pose randomization. If None, default seed is used")

    parser.add_argument("-n", "--num-traj", type=int, default=50, help="Number of trajectories to generate.")
    parser.add_argument("-m", "--max-horizon", type=int, default=500)

    parser.add_argument("-b", "--sim-backend", type=str, default="auto", help="Which simulation backend to use. Can be 'auto', 'cpu', 'gpu'")

    parser.add_argument("-r", "--robot-uids", type=str, default="ds_fetch_basket", help=f"Robot id")
    parser.add_argument("--vis", action="store_true", help="whether or not to open a GUI to visualize the solution live")
    parser.add_argument("--save-video", action="store_true", help="whether or not to save videos locally")
    parser.add_argument("--save-traj", action="store_true", help="whether or not to save trajectory locally")
    parser.add_argument("--traj-name", type=str, help="The name of the trajectory .h5 file that will be created.")
    parser.add_argument("--shader", default="default", type=str, help="Change shader used for rendering. Default is 'default' which is very fast. Can also be 'rt' for ray tracing and generating photo-realistic renders. Can also be 'rt-fast' for a faster but lower quality ray-traced renderer")

    parser.add_argument("--host", type=str, default='localhost')
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--max-exec-actions", type=int, default=None,
                        help="Optional client-side cap on actions executed per policy call")

    return parser.parse_args()

def main(args) -> str:
    scene_dir = args.scene_dir
    if args.max_horizon <= 0 or args.num_traj <= 0:
        raise ValueError("--max-horizon and --num-traj must be positive")
    if args.max_exec_actions is not None and args.max_exec_actions <= 0:
        raise ValueError("--max-exec-actions must be positive")
    record_dir = args.scene_dir + '/evaluations'

    json_path = args.json_path
    if json_path is not None:
        with open(str(json_path), 'r') as f:
            scenes_data = json.load(f)

    env_id = scenes_data['env_info']['env_id'] if json_path is not None else args.env_id
    robot_uids=scenes_data['env_info']['env_kwargs']['robot_uids'] if json_path is not None else args.robot_uids
    control_mode=scenes_data['env_info']['env_kwargs']['control_mode'] if json_path is not None else 'pd_joint_pos'
    viewer_camera_configs=scenes_data['env_info']['env_kwargs']['viewer_camera_configs'] if json_path is not None else {'shader_pack': args.shader}
    human_render_camera_configs=scenes_data['env_info']['env_kwargs']['human_render_camera_configs'] if json_path is not None else {'shader_pack': args.shader}
    sensor_configs=scenes_data['env_info']['env_kwargs']['sensor_configs'] if json_path is not None else None
    render_mode=scenes_data['env_info']['env_kwargs']['render_mode'] if json_path is not None else 'rgb_array'
    enable_shadow=scenes_data['env_info']['env_kwargs']['enable_shadow'] if json_path is not None else True
    obs_mode='rgb' #scenes_data['env_info']['env_kwargs']['obs_mode'] if json_path is not None else 'rgb'

    if json_path is None and args.env_id is None:
        raise AttributeError("Either --env-id or --json-path must be specified")

    env = gym.make(env_id,
                    robot_uids=robot_uids,
                    config_dir_path = scene_dir,
                    num_envs=1,
                    control_mode=control_mode,
                    viewer_camera_configs=viewer_camera_configs,
                    human_render_camera_configs=human_render_camera_configs,
                    sensor_configs=sensor_configs,
                    sim_backend=args.sim_backend,
                    render_mode=render_mode,
                    enable_shadow=enable_shadow,
                    obs_mode=obs_mode,
                    parallel_in_single_scene = False,
                    )

    if not args.traj_name:
        new_traj_name = time.strftime("%Y%m%d_%H%M%S")
    else:
        new_traj_name = args.traj_name

    env = RecordEpisode(
        env,
        output_dir=osp.join(record_dir, args.eval_subdir),
        trajectory_name=new_traj_name, save_video=args.save_video,
        source_type="Policy",
        source_desc="Policy evaluation",
        video_fps=30,
        record_reward=False,
        save_on_reset=False
    )

    output_h5_path = env._h5_file.filename

    print(f"Octo evaluation on {env_id}")

    client = WebsocketClient(host=args.host, port=args.port)

    pbar = tqdm(range(args.num_traj))
    successes = []
    solution_episode_lengths = []

    seed = args.start_seed - 1

    init_pose_seed = args.robot_init_pose_start_seed
    if init_pose_seed is not None:
        init_pose_seed -= 1

    reset_options={'reconfigure': True}

    successfull_episodes = []
    episode_rows = []

    for traj_idx in range(args.num_traj):
        if json_path is not None:
            seed = scenes_data['episodes'][traj_idx]['episode_seed']
        else:
            seed += 1

        if init_pose_seed is not None:
            init_pose_seed += 1
            reset_options['robot_init_pose_seed'] = init_pose_seed

        obs, info = env.reset(seed=seed, options=reset_options)
        language_instruction = env.language_instructions[0]

        i = 0
        policy_calls = 0
        inference_seconds = 0.0
        finished = False
        # Time step is the number of environment actions already executed.
        while not finished and i < args.max_horizon:
            obs_prepared = prepare_obs(obs, language_instruction, i)
            t0 = time.perf_counter()
            actions = np.asarray(client.infer(obs_prepared)["actions"])
            inference_seconds += time.perf_counter() - t0
            policy_calls += 1
            if actions.ndim == 1:
                actions = actions[None, :]
            if len(actions) == 0:
                raise RuntimeError("Policy returned an empty action chunk")
            if args.max_exec_actions is not None:
                actions = actions[:args.max_exec_actions]

            for action in actions:
                # Do not mutate a view of the returned model output.
                action = np.array(action, dtype=np.float32, copy=True)
                action[8] = 0
                action[9] = 0
                obs, reward, done, trunc, info = env.step(action)
                i += 1
                # Check within the chunk; do not step after terminal/truncation.
                if bool(np.asarray(done).all()) or bool(np.asarray(trunc).all()) or i >= args.max_horizon:
                    finished = True
                    break

            if args.vis:
                env.render()

        success = info["success"][0].item()
        if success:
            successfull_episodes.append(seed)
        elapsed_steps = info["elapsed_steps"][0].item()
        solution_episode_lengths.append(elapsed_steps)

        successes.append(success)
        episode_rows.append({
            "episode_index": traj_idx,
            "seed": seed,
            "success": int(bool(success)),
            "executed_steps": i,
            "environment_elapsed_steps": elapsed_steps,
            "policy_calls": policy_calls,
            "inference_seconds": round(inference_seconds, 6),
            "max_exec_actions": args.max_exec_actions if args.max_exec_actions is not None else "server_default",
            "max_horizon": args.max_horizon,
            "env_id": env_id,
        })

        if args.save_traj:
            env.flush_trajectory()

        if args.save_video:
            env.flush_video(str(seed))
        pbar.update(1)
        pbar.set_postfix(
            dict(
                success_rate=np.mean(successes),
                avg_episode_length=np.mean(solution_episode_lengths),
                max_episode_length=np.max(solution_episode_lengths),
                # min_episode_length=np.min(solution_episode_lengths)
            )
        )

    csv_path = Path(record_dir) / args.eval_subdir / "episode_metrics.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(episode_rows[0]))
        writer.writeheader()
        writer.writerows(episode_rows)
    print(f"Episode metrics saved: {csv_path}")
    print("Results:", successfull_episodes, len(successfull_episodes), len(successfull_episodes)/len(successes))
    env.close()
    return output_h5_path

if __name__ == "__main__":
    # start = time.time()
    mp.set_start_method("spawn")
    main(parse_args())
    # print(f"Total time taken: {time.time() - start}")
