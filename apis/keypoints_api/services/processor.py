import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import os
import datetime
from typing import List

class PoseProcessor:
    def __init__(self, params=None):
        print(f"[{datetime.datetime.now().isoformat()}] PoseProcessor.__init__ starting")
        
        self.using_solutions = hasattr(mp, 'solutions')
        if self.using_solutions:
            self.mp_pose = mp.solutions.pose
        else:
            self.mp_pose = None
        
        # hyperparameters
        self.params = params or {
            'min_detection_confidence': 0.5, 
            'min_tracking_confidence': 0.3,
            'model_complexity': 2,
            'landmark_visibility_threshold': 0.3, 
            'history_size': 1,
            'stability_ratio': 0.5,
            'key_parts_threshold': 1
        }
        
        self.pose_history = []

        if self.using_solutions:
            self.pose_detector = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=self.params['model_complexity'],
                smooth_landmarks=True,
                min_detection_confidence=self.params['min_detection_confidence'],
                min_tracking_confidence=self.params['min_tracking_confidence']
            )
            print(f"[{datetime.datetime.now().isoformat()}] Pose detector created")
        else:
            self.pose_detector = None

    def is_pose_stable(self, landmarks) -> bool:
        if not landmarks:
            self.pose_history.append(False)
        else:
            key_parts = [11, 12, 23, 24]
            key_parts_visible = sum(1 for i in key_parts if landmarks[i].visibility > self.params['landmark_visibility_threshold'])
            current_stable = key_parts_visible >= self.params['key_parts_threshold']
            self.pose_history.append(current_stable)
        
        if len(self.pose_history) > self.params['history_size']:
            self.pose_history.pop(0)
            
        return (sum(self.pose_history) / len(self.pose_history)) >= self.params['stability_ratio'] if self.pose_history else False

    def normalize_landmarks(self, landmarks) -> List[dict]:
        pts = {i: np.array([landmarks[i].x, landmarks[i].y, landmarks[i].z]) for i in [11, 12, 23, 24]}
        hip_center = (pts[23] + pts[24]) / 2
        shoulder_center = (pts[11] + pts[12]) / 2
        
        torso_size = np.linalg.norm(shoulder_center - hip_center)
        if torso_size == 0: torso_size = 1.0

        normalized = []
        for lm in landmarks:
            norm_x = (lm.x - hip_center[0]) / torso_size
            norm_y = (lm.y - hip_center[1]) / torso_size
            norm_z = (lm.z - hip_center[2]) / torso_size
            normalized.append({'x': norm_x, 'y': norm_y, 'z': norm_z, 'v': lm.visibility})
        return normalized

    def process_folder(self, input_dir: str, output_parent_dir: str):
        print(f"[{datetime.datetime.now().isoformat()}] Processing: {input_dir}")
        
        # Directories for data saving
        npy_dir = os.path.join(output_parent_dir, "numpy_data")
        csv_dir = os.path.join(output_parent_dir, "csv_data")
        
        for d in [npy_dir, csv_dir]:
            os.makedirs(d, exist_ok=True)

        valid_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.webm')
        video_files = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_extensions)]

        for filename in video_files:
            video_path = os.path.join(input_dir, filename)
            base_name = os.path.splitext(filename)[0]
            self.pose_history = []
            
            cap = cv2.VideoCapture(video_path)
            out_npy_path = os.path.join(npy_dir, f"{base_name}.npy")
            out_csv_path = os.path.join(csv_dir, f"{base_name}.csv")

            npy_frames = []
            csv_rows = []
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret: break

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.pose_detector.process(rgb_frame)
                norm_data = np.zeros((33, 4)) 

                if results.pose_landmarks and self.is_pose_stable(results.pose_landmarks.landmark):
                    norm_list = self.normalize_landmarks(results.pose_landmarks.landmark)
                    norm_data = np.array([[l['x'], l['y'], l['z'], l['v']] for l in norm_list])
                
                # Append data to lists
                npy_frames.append(norm_data)
                csv_rows.append([frame_idx] + norm_data.flatten().tolist())
                frame_idx += 1

            # Save to disk
            np.save(out_npy_path, np.array(npy_frames))
            cols = ['frame'] + [f'{ax}{i}' for i in range(33) for ax in ['x','y','z','v']]
            pd.DataFrame(csv_rows, columns=cols).to_csv(out_csv_path, index=False)

            cap.release()
            print(f"[{datetime.datetime.now().isoformat()}] Completed: {filename} ({frame_idx} frames)")