import multiprocessing as mp

import time
import argparse
import gymnasium as gym
import numpy as np
from tqdm import tqdm
import os.path as osp

import json
import csv

import sys
sys.path.append('.')
from dsynth.envs import *
from dsynth.robots import *
from dsynth.web_utils import WebsocketClient
from dsynth.utils import RecordEpisodeSuccLength

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
    parser.add_argument("--traj-name", type=str, help="The name of the trajectory .h5 file that will be created.")
    parser.add_argument("--shader", default="default", type=str, help="Change shader used for rendering. Default is 'default' which is very fast. Can also be 'rt' for ray tracing and generating photo-realistic renders. Can also be 'rt-fast' for a faster but lower quality ray-traced renderer")

    parser.add_argument("--host", type=str, default='localhost')
    parser.add_argument("--port", type=int, default=8000)

    parser.add_argument("--action-chunk-size", type=int, default=0,
                        help="Maximum actions executed per inference; 0 means all returned actions")
    parser.add_argument("--disable-instruction-replan", action="store_true",
                        help="Do not interrupt an action chunk when the task instruction changes")
    return parser.parse_args(args)

def main(args) -> str:
    scene_dir = args.scene_dir
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
    obs_mode=scenes_data['env_info']['env_kwargs']['obs_mode'] if json_path is not None else 'rgb'

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

    env = RecordEpisodeSuccLength(
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

    print(f"Improved composite evaluation on {env_id}")

    client = WebsocketClient(host=args.host, port=args.port)

    pbar = tqdm(range(args.num_traj))
    successes = []
    success_lengths = []
    solution_episode_lengths = []

    seed = args.start_seed - 1

    init_pose_seed = args.robot_init_pose_start_seed
    if init_pose_seed is not None:
        init_pose_seed -= 1

    reset_options={'reconfigure': True}
    metrics_path = osp.join(record_dir, args.eval_subdir, f"{new_traj_name}_metrics.csv")
    metric_fields = ["episode", "seed", "init_pose_seed", "env_id", "success",
                     "success_length", "elapsed_steps", "steps_executed",
                     "policy_calls", "policy_latency_sec", "discarded_actions",
                     "instruction_changes", "stage_changes", "stage_events_json",
                     "action_chunk_size", "instruction_replan_enabled"]

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
        policy_latency_sec = 0.0
        discarded_actions = 0
        instruction_changes = 0
        stage_changes = 0
        stage_events = []
        last_stage = int(env.unwrapped.CUR_TASK_IDX)
        episode_done = False
        if args.action_chunk_size < 0:
            raise ValueError("--action-chunk-size must be >= 0")

        while i < args.max_horizon and not episode_done:
            # This prompt describes the task at the time of inference.
            inference_instruction = env.unwrapped.language_instructions[0]
            obs_prepared = prepare_obs(obs, inference_instruction, i)
            t0 = time.perf_counter()
            actions = client.infer(obs_prepared)["actions"]
            policy_latency_sec += time.perf_counter() - t0
            policy_calls += 1
            if len(actions) == 0:
                raise RuntimeError("Policy returned an empty action chunk")

            allowed = len(actions) if args.action_chunk_size == 0 else min(len(actions), args.action_chunk_size)
            processed = 0
            for action in actions[:allowed]:
                obs, reward, done, trunc, info = env.step(action)
                i += 1
                processed += 1
                current_stage = int(env.unwrapped.CUR_TASK_IDX)
                current_instruction = env.unwrapped.language_instructions[0]
                stage_changed = current_stage != last_stage
                if stage_changed:
                    stage_changes += 1
                    stage_events.append({"step": i, "from": last_stage,
                                         "to": current_stage, "instruction": current_instruction})
                    last_stage = current_stage
                instruction_changed = current_instruction != inference_instruction
                if instruction_changed:
                    # Count once per inference block, not once per subsequent step.
                    instruction_changes += 1
                if args.vis:
                    env.render()
                episode_done = bool(done) or bool(trunc) or i >= args.max_horizon
                if episode_done or (
                    (stage_changed or instruction_changed)
                    and not args.disable_instruction_replan
                ):
                    break
            discarded_actions += len(actions) - processed

        success = info["success"][0].item()
        success_length = info["success_length"][0].item()


        elapsed_steps = info["elapsed_steps"][0].item()
        solution_episode_lengths.append(elapsed_steps)

        successes.append(success)
        success_lengths.append(success_length)
        metrics_row = {
            "episode": traj_idx, "seed": seed,
            "init_pose_seed": init_pose_seed if init_pose_seed is not None else "",
            "env_id": env_id, "success": bool(success),
            "success_length": float(success_length), "elapsed_steps": int(elapsed_steps),
            "steps_executed": i, "policy_calls": policy_calls,
            "policy_latency_sec": round(policy_latency_sec, 6),
            "discarded_actions": discarded_actions,
            "instruction_changes": instruction_changes, "stage_changes": stage_changes,
            "stage_events_json": json.dumps(stage_events, ensure_ascii=False),
            "action_chunk_size": args.action_chunk_size,
            "instruction_replan_enabled": not args.disable_instruction_replan,
        }
        with open(metrics_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=metric_fields)
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(metrics_row)
        print(f"EPISODE_METRICS {json.dumps(metrics_row, ensure_ascii=False)}", flush=True)


        env.flush_trajectory()
        if args.save_video:
            env.flush_video()
        pbar.update(1)
        pbar.set_postfix(
            dict(
                success_rate=np.mean(successes),
                mean_success_length=np.mean(success_lengths),
                avg_episode_length=np.mean(solution_episode_lengths),
                max_episode_length=np.max(solution_episode_lengths),
                # min_episode_length=np.min(solution_episode_lengths)
            )
        )

    env.close()
    return output_h5_path

if __name__ == "__main__":
    # start = time.time()
    mp.set_start_method("spawn")
    main(parse_args())
    # print(f"Total time taken: {time.time() - start}")
