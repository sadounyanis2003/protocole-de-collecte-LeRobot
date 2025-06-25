# utils/video_utils.py

import os
import cv2
import numpy as np

def save_video(frames, episode_id, camera_name, fps):
    video_dir = "videos/chunk-000"
    os.makedirs(video_dir, exist_ok=True)
    path = os.path.join(video_dir, f"{episode_id}_{camera_name}.mp4")
    h, w, _ = frames[0].shape
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for frame in frames:
        writer.write(frame)
    writer.release()

def save_images(frames_by_cam, episode_id):
    base_dir = f"images/chunk-000/{episode_id}"
    for cam_name, frame_list in frames_by_cam.items():
        rgb_dir = os.path.join(base_dir, f"rgb_{cam_name}")
        depth_dir = os.path.join(base_dir, f"depth_{cam_name}")
        os.makedirs(rgb_dir, exist_ok=True)
        os.makedirs(depth_dir, exist_ok=True)
        for i, (rgb, depth) in enumerate(frame_list):
            cv2.imwrite(os.path.join(rgb_dir, f"{i:06d}.png"),
                        cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
            depth_img = (depth * 1000).astype(np.uint16)
            cv2.imwrite(os.path.join(depth_dir, f"{i:06d}.png"), depth_img)
