import os
import numpy as np
import torch
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List


# Configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

HANDSTAND_SEGMENTATION_MODEL_PATH = os.environ.get(
    "HANDSTAND_SEGMENTATION_MODEL_PATH",
    "Models/handstand_segmentation.pth"
)
HANDSTAND_GRADING_MODEL_PATH = os.environ.get(
    "HANDSTAND_GRADING_MODEL_PATH",
    "Models/handstand_grading.pth"
)

SPREAD_JUMP_SEGMENTATION_MODEL_PATH = os.environ.get(
    "SPREAD_JUMP_SEGMENTATION_MODEL_PATH",
    "Models/spread_jump_segmentation.pth"
)
SPREAD_JUMP_GRADING_MODEL_PATH = os.environ.get(
    "SPREAD_JUMP_GRADING_MODEL_PATH",
    "Models/spread_jump_grading.pth"
)


# Model definitions 
from stage_model_def import StageSegmentationLSTM
from grade_model_def import GymnasticsLSTM


# Utility functions
def load_stage_model(path: str):
    ckpt = torch.load(path, map_location=device)
    model = StageSegmentationLSTM(
        input_size=ckpt["input_size"],
        hidden_size=ckpt["hidden_size"],
        num_layers=ckpt["num_layers"],
        num_classes=ckpt["num_classes"],
        bidirectional=ckpt.get("bidirectional", True)
    ).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    return model


def load_grade_model(path: str):
    ckpt = torch.load(path, map_location=device)
    model = GymnasticsLSTM(
        input_size=ckpt["input_size"],
        hidden_size=ckpt["hidden_size"],
        num_layers=ckpt["num_layers"],
        bidirectional=ckpt.get("bidirectional", True)
    ).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    return model


def extract_stages(preds: np.ndarray):
    """Convert per-frame stage predictions into segments"""
    stages = []
    start = 0
    current = preds[0]

    for i in range(1, len(preds)):
        if preds[i] != current:
            stages.append((int(current), start, i - 1))
            current = preds[i]
            start = i

    stages.append((int(current), start, len(preds) - 1))
    return stages


# Load all models
MODELS = {
    "handstand": {
        "segmentation": load_stage_model(HANDSTAND_SEGMENTATION_MODEL_PATH),
        "grading": load_grade_model(HANDSTAND_GRADING_MODEL_PATH),
    },
    "spread_jump": {
        "segmentation": load_stage_model(SPREAD_JUMP_SEGMENTATION_MODEL_PATH),
        "grading": load_grade_model(SPREAD_JUMP_GRADING_MODEL_PATH),
    },
}


# FastAPI
app = FastAPI()


class InferenceRequest(BaseModel):
    exercise: str
    keypoints: List[List[List[float]]]  # (T, 33, 4)


@app.get("/health", status_code=status.HTTP_200_OK)
def health():
    return {"status": "ok"}


@app.post("/infer")
def infer(req: InferenceRequest):
    exercise = req.exercise.lower()

    if exercise not in MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported exercise: {exercise}"
        )

    keypoints = np.array(req.keypoints, dtype=np.float32)
    T = keypoints.shape[0]

    if T < 5:
        raise HTTPException(
            status_code=400,
            detail="Video too short for inference"
        )

    features = keypoints.reshape(T, -1)  # (T, 132)

    x = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(device)
    lengths = torch.tensor([T], dtype=torch.long)


    # Stage segmentation
    stage_model = MODELS[exercise]["segmentation"]

    with torch.no_grad():
        logits = stage_model(x, lengths)        # (1, T, num_stages)
        preds = logits.argmax(dim=-1).squeeze(0).cpu().numpy()

    stage_segments = extract_stages(preds)

    # Per-stage grading
    grade_model = MODELS[exercise]["grading"]
    results = []

    for stage_id, s, e in stage_segments:
        stage_feats = features[s:e + 1]

        stage_x = torch.tensor(
            stage_feats,
            dtype=torch.float32
        ).unsqueeze(0).to(device)

        stage_len = torch.tensor(
            [stage_feats.shape[0]],
            dtype=torch.long
        )

        with torch.no_grad():
            logit = grade_model(stage_x, stage_len)
            prob = torch.sigmoid(logit).item()

        results.append({
            "stage": stage_id,
            "start_frame": s,
            "end_frame": e,
            "pass": int(prob > 0.5),
            "confidence": round(prob, 4)
        })

    return {
        "exercise": exercise,
        "num_frames": T,
        "stages": results
    }
