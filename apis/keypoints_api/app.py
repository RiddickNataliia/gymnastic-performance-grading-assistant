import cv2
import numpy as np
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Response, status
from services.processor import PoseProcessor

app = FastAPI()

processor = PoseProcessor()

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}

@app.post("/keypoints")
async def extract_keypoints(file: UploadFile = File(...)):
    temp_path = Path(f"temp_{file.filename}")
    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        cap = cv2.VideoCapture(str(temp_path))
        npy_frames = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = processor.pose_detector.process(rgb_frame)
            
            norm_data = np.zeros((33, 4), dtype=np.float32)
            if results.pose_landmarks and processor.is_pose_stable(results.pose_landmarks.landmark):
                norm_list = processor.normalize_landmarks(results.pose_landmarks.landmark)
                norm_data = np.array([[l['x'], l['y'], l['z'], l['v']] for l in norm_list], dtype=np.float32)
            
            npy_frames.append(norm_data)
        
        cap.release()
        
        final_array = np.array(npy_frames, dtype=np.float32)
        array_bytes = final_array.tobytes()
        shape_str = ",".join(map(str, final_array.shape))
        
        return Response(
            content=array_bytes,
            media_type="application/octet-stream",
            headers={"X-Array-Shape": shape_str}
        )
    finally:
        if temp_path.exists():
            temp_path.unlink()
