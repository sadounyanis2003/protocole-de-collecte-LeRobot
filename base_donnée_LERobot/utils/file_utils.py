# utils/file_utils.py

import os
import json
import pandas as pd
from pathlib import Path
import yaml

DATA_DIR = Path("data/chunk-000")
META_DIR = Path("meta")
VIDEO_DIR = Path("videos/chunk-000")
IMAGE_DIR = Path("images/chunk-000")

INFO_PATH = META_DIR / "info.json"
TASKS_PATH = META_DIR / "tasks.jsonl"
EPISODES_PATH = META_DIR / "episodes.jsonl"
CONFIG_PATH = Path("config.yaml")

def read_config():
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Le fichier config.yaml est introuvable à {config_path}.")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)




def read_json(path):
    if not Path(path).exists():
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def append_jsonl(path, entry):
    with open(path, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def read_jsonl(path):
    if not Path(path).exists():
        return []
    with open(path, 'r') as f:
        return [json.loads(line) for line in f if line.strip()]

def write_parquet(path, dataframe):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    dataframe.to_parquet(path, index=False)

def init_directories():
    for path in [DATA_DIR, META_DIR, VIDEO_DIR, IMAGE_DIR]:
        os.makedirs(path, exist_ok=True)

def init_info_json():
    if INFO_PATH.exists():
        return

    config = read_config()

    default_info = {
        "codebase_version": config.get("codebase_version", "v2.1"),
        "robot_type": config.get("robot_type", "UR10"),
        "fps": config.get("fps", 20),
        "control_frequency": config.get("control_frequency", 20),
        "cameras": config.get("cameras", []),
        "total_episodes": 0,
        "total_frames": 0,
        "total_tasks": 0,
        "total_videos": 0,
        "splits": {"train": "0:N"},
        "camera_keys": ["cam_gripper", "cam_scene"],
        "data_path": str(DATA_DIR),
        "video_path": str(VIDEO_DIR),
        "features": {
            "observation.state": {"dtype": "float32", "shape": [6]},
            "action": {"dtype": "float32", "shape": [6]},
            "timestamp": {"dtype": "float64", "shape": []},
            "ee_pose": {"dtype": "float32", "shape": [7]},
            "ee_velocity": {"dtype": "float32", "shape": [6]},
            "gripper_state": {"dtype": "float32", "shape": [1]},
            "robot_obs": {"dtype": "float32", "shape": [18]},
            "cameras": {"dtype": "object", "shape": []}
        }
    }
    write_json(INFO_PATH, default_info)



def update_info(episode_frames, new_task=False):
    info = read_json(INFO_PATH)
    config = read_config()

    info["total_episodes"] += 1
    info["total_frames"] += episode_frames
    info["total_videos"] += 2
    if new_task:
        info["total_tasks"] += 1

    # On remet à jour les champs qui viennent de config.yaml
    info["codebase_version"] = config.get("codebase_version", info.get("codebase_version", "v2.1"))
    info["robot_type"] = config.get("robot_type", info.get("robot_type", "UR10"))
    info["fps"] = config.get("fps", info.get("fps", 20))
    info["control_frequency"] = config.get("control_frequency", info.get("control_frequency", 20))
    info["cameras"] = config.get("cameras", info.get("cameras", []))
    info["data_path"] = str(DATA_DIR)
    info["video_path"] = str(VIDEO_DIR)

    write_json(INFO_PATH, info)



def get_next_task_index():
    tasks = read_jsonl(TASKS_PATH)
    return len(tasks)

def get_next_episode_index():
    episodes = read_jsonl(EPISODES_PATH)
    return len(episodes)

def get_image_path(base_dir, cam_name, frame_idx, img_type):
    return os.path.join(base_dir, f"{img_type}_{cam_name}_{frame_idx:06d}.png")
