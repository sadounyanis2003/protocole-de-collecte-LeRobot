# ui/episode_recorder.py

import json
import customtkinter as ctk
import tkinter.messagebox as messagebox
import threading, time, numpy as np, cv2, os
import pyrealsense2 as rs
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32MultiArray
import pandas as pd
from utils.file_utils import read_config
from utils.file_utils import (
    get_next_episode_index,
    append_jsonl,
    update_info,
    write_parquet,
    get_image_path
)
from utils.video_utils import save_video

CAMERA_SERIALS = {
    "cam_gripper": "234322303360",
    "cam_scene": "242422302403"
}

class RealsenseCamera:
    def __init__(self, serial, fps):
        self.serial = serial
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_device(serial)
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, fps)
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, fps)
        self.pipeline.start(self.config)

    def get_frames(self):
        frames = self.pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()
        if not color_frame or not depth_frame:
            return None, None
        color = np.asanyarray(color_frame.get_data())
        depth = np.asanyarray(depth_frame.get_data()) / 1000.0
        return color, depth

    def stop(self):
        self.pipeline.stop()

class RobotListener(Node):
    def __init__(self):
        super().__init__('listener')
        self.joints = None
        self.ee_pose = None
        self.ee_velocity = None
        self.create_subscription(JointState, '/joint_states', self.joints_callback, 10)
        self.create_subscription(PoseStamped, '/tcp_pose_broadcaster/pose', self.pose_callback, 10)
        self.create_subscription(Float32MultiArray, '/ee_velocity', self.vel_callback, 10) # il n'y a pas de topics pour la vitessse de l'effecteur 

    def joints_callback(self, msg):
        self.joints = list(msg.position)

    def pose_callback(self, msg):
        p = msg.pose.position
        o = msg.pose.orientation
        self.ee_pose = [p.x, p.y, p.z, o.x, o.y, o.z, o.w]

    def vel_callback(self, msg):
        self.ee_velocity = list(msg.data)

class EpisodeRecorder(ctk.CTk):
    def __init__(self, task_id):
        super().__init__()
        self.title("Collecte d’un épisode")
        self.geometry("900x600")
        self.task_id = task_id
        self.collecting = False
        self.frames = []
        config = read_config()
        self.fps = config.get("fps", 20)  # 20 par défaut si absent

        self.cameras = {}
        try:
            for name, serial in CAMERA_SERIALS.items():
                self.cameras[name] = RealsenseCamera(serial)
        except Exception as e:
            messagebox.showerror("Erreur caméra", f"Erreur d'initialisation caméra : {e}")
            self.quit()
            return

        rclpy.init()
        self.robot_node = RobotListener()
        threading.Thread(target=rclpy.spin, args=(self.robot_node,), daemon=True).start()

        ctk.CTkLabel(self, text="Collecte d'un épisode").pack(pady=5)
        self.start_btn = ctk.CTkButton(self, text="▶️ Démarrer collecte", command=self.start_collect)
        self.start_btn.pack(pady=10)
        self.stop_btn = ctk.CTkButton(self, text="✅ Fin de trajectoire", command=self.stop_collect)
        self.stop_btn.pack(pady=10)
        self.cancel_btn = ctk.CTkButton(self, text="❌ Annuler collecte", command=self.cancel_collect)
        self.cancel_btn.pack(pady=10)

    def start_collect(self):
        self.collecting = True
        self.frames = []
        self.start_time = time.time()
        threading.Thread(target=self.record_loop, daemon=True).start()
        ctk.CTkLabel(self, text="Collecte en cours...").pack(pady=5)

    def record_loop(self):
        while self.collecting:
            timestamp = time.time() - self.start_time
            action = self.robot_node.joints or [0]*6
            pose = self.robot_node.ee_pose or [0]*7
            vel = self.robot_node.ee_velocity or [0]*6
            cam_data = {}

            for name, cam in self.cameras.items():
                rgb, depth = cam.get_frames()
                if rgb is None:
                    continue
                cam_data[f"rgb_{name}"] = rgb
                cam_data[f"depth_{name}"] = depth

            self.frames.append({
                "timestamp": timestamp,
                "action": action,
                "ee_pose": pose,
                "ee_velocity": vel,
                "gripper_state": [0.0],
                "cameras": cam_data
            })
            time.sleep(1/self.fps)

    def stop_collect(self):
        self.collecting = False
        time.sleep(0.1)

        success = messagebox.askyesno("Succès ?", "Tâche réussie ?")
        eid = get_next_episode_index()
        episode_id = f"{eid:06d}"
        parquet_path = f"data/chunk-000/{episode_id}.parquet"
        image_dir = f"images/chunk-000/{episode_id}"
        os.makedirs(image_dir, exist_ok=True)

        data = {col: [] for col in [
            "timestamp", "action", "ee_pose", "ee_velocity", "gripper_state", "task_id", "robot_obs", "cameras"
        ]}

        for idx, f in enumerate(self.frames):
            robot_obs = f["action"] + f["ee_velocity"] + f["ee_pose"]
            cameras_dict = {}

            for name in self.cameras:
                if f"rgb_{name}" in f["cameras"]:
                    rgb_path = get_image_path(image_dir, name, idx, "rgb")
                    cv2.imwrite(rgb_path, cv2.cvtColor(f["cameras"][f"rgb_{name}"], cv2.COLOR_RGB2BGR))
                    cameras_dict[f"rgb_{name}"] = os.path.relpath(rgb_path, start=".")

                if f"depth_{name}" in f["cameras"]:
                    depth_path = get_image_path(image_dir, name, idx, "depth")
                    depth_uint16 = (f["cameras"][f"depth_{name}"] * 1000).astype(np.uint16)
                    cv2.imwrite(depth_path, depth_uint16)
                    cameras_dict[f"depth_{name}"] = os.path.relpath(depth_path, start=".")

            data["timestamp"].append(f["timestamp"])
            data["action"].append(f["action"])
            data["ee_pose"].append(f["ee_pose"])
            data["ee_velocity"].append(f["ee_velocity"])
            data["gripper_state"].append(f["gripper_state"])
            data["task_id"].append(self.task_id)
            data["robot_obs"].append(robot_obs)
            data["cameras"].append(json.dumps(cameras_dict))

        df = pd.DataFrame(data)
        write_parquet(parquet_path, df)

        append_jsonl("meta/episodes.jsonl", {
            "episode_index": eid,
            "tasks": [self.task_id],
            "length": len(self.frames),
            "success": success,
            "cameras": list(self.cameras.keys())
        })
        update_info(len(self.frames), new_task=False)
        # Enregistrement des vidéos
        for name in self.cameras:
            rgb_frames = [f["cameras"][f"rgb_{name}"] for f in self.frames if f"rgb_{name}" in f["cameras"]]
            if rgb_frames:
                save_video(rgb_frames, episode_id, name,fps=self.fps)


        messagebox.showinfo("Enregistré", f"Épisode {episode_id} sauvegardé.")
        relancer = messagebox.askyesno("Nouvel épisode ?", "Voulez-vous enregistrer un nouvel épisode pour cette tâche ?")
        self.relancer_episode = relancer
        self.destroy()

        for cam in self.cameras.values():
            cam.stop()
        rclpy.shutdown()

    def cancel_collect(self):
        self.collecting = False
        messagebox.showinfo("Annulé", "Collecte abandonnée.")

        for cam in self.cameras.values():
            cam.stop()
        rclpy.shutdown()

        self.relancer_episode = False
        self.quit()
        self.destroy()

        


def lancer_collecteur(task_id):
    app = EpisodeRecorder(task_id)
    app.relancer_episode = False
    app.mainloop()
    return app.relancer_episode
