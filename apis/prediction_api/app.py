import os
import random
import numpy as np
import torch
import httpx
from fastapi import FastAPI, HTTPException, status, File, UploadFile
from pydantic import BaseModel
from typing import List

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Base directory for resolving model paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# External services
KEYPOINTS_API_URL = os.environ.get("KEYPOINTS_API_URL")
timeout = httpx.Timeout(60.0, read=120.0)


# Model paths (absolute by default, overridable via environment)
HANDSTAND_SEGMENTATION_MODEL_PATH = os.environ.get(
    "HANDSTAND_SEGMENTATION_MODEL_PATH",
    os.path.join(BASE_DIR, "Models", "handstand_phase_model_91(hss).pth"),
)
HANDSTAND_GRADING_MODEL_PATH = os.environ.get(
    "HANDSTAND_GRADING_MODEL_PATH",
    os.path.join(BASE_DIR, "Models", "handstand_grade_model_86(hsg).pth"),
)
SPREAD_JUMP_SEGMENTATION_MODEL_PATH = os.environ.get(
    "SPREAD_JUMP_SEGMENTATION_MODEL_PATH",
    os.path.join(BASE_DIR, "Models", "spreadjump_phase_model_86(sjs).pth"),
)
SPREAD_JUMP_GRADING_MODEL_PATH = os.environ.get(
    "SPREAD_JUMP_GRADING_MODEL_PATH",
    os.path.join(BASE_DIR, "Models", "spreadjump_grade_model_85(sjg).pth"),
)

# Model definitions
from services.stage_model_def import StageSegmentationLSTM
from services.grade_model_def import GymnasticsLSTM

# -----------------------------
# Utility functions
# -----------------------------

def load_stage_model(path: str):
    """Load a stage segmentation model from checkpoint"""
    ckpt = torch.load(path, map_location=device)
    sd = ckpt["model_state_dict"]

    hidden_size = sd["lstm.weight_ih_l0"].shape[0] // 4

    model = StageSegmentationLSTM(
        input_size=ckpt["input_size"],
        hidden_size=hidden_size,
        num_layers=ckpt["num_layers"],
        num_classes=ckpt["num_classes"],
        bidirectional=ckpt.get("bidirectional", True)
    ).to(device)

    model.load_state_dict(sd)
    model.eval()
    return model

def load_grade_model(path: str):
    """Load a grading model from checkpoint with scaler"""
    ckpt = torch.load(path, map_location=device)
    sd = ckpt["model_state_dict"]

    hidden_size = sd["lstm.weight_ih_l0"].shape[0] // 4

    model = GymnasticsLSTM(
        input_size=ckpt["input_size"],
        hidden_size=hidden_size,
        num_layers=ckpt["num_layers"],
        bidirectional=ckpt.get("bidirectional", True)
    ).to(device)

    model.load_state_dict(sd)
    model.eval()

    # Load scaler if exists
    scaler = None
    if "input_scaler" in ckpt and ckpt["input_scaler"] is not None:
        scaler_ckpt = ckpt["input_scaler"]
        mean = np.array(scaler_ckpt["mean"], dtype=np.float32)
        std = np.array(scaler_ckpt["std"], dtype=np.float32)
        eps = scaler_ckpt.get("eps", 1e-8)
        scaler = {"mean": mean, "std": std, "eps": eps}

    return model, scaler

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

# -----------------------------
# Load all models
# -----------------------------
MODELS = {
    "handstand": {
        "segmentation": load_stage_model(HANDSTAND_SEGMENTATION_MODEL_PATH),
        "grading": load_grade_model(HANDSTAND_GRADING_MODEL_PATH),
    },
    # Internal key uses underscore; web UI sends "spreadjump"
    "spread_jump": {
        "segmentation": load_stage_model(SPREAD_JUMP_SEGMENTATION_MODEL_PATH),
        "grading": load_grade_model(SPREAD_JUMP_GRADING_MODEL_PATH),
    },
}

# Map incoming exercise names from UI to internal keys
EXERCISE_ALIASES = {
    "handstand": "handstand",
    "spreadjump": "spread_jump",
    "spread_jump": "spread_jump",
    "spread jump": "spread_jump",
}

# -----------------------------
# FastAPI
# -----------------------------
app = FastAPI()

class InferenceRequest(BaseModel):
    exercise: str
    keypoints: List[List[List[float]]]  # (T, 33, 4)

@app.get("/health", status_code=status.HTTP_200_OK)
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict_score(exercise: str, file: UploadFile = File(...)):
    """Endpoint used by the web app.

    1. Sends the uploaded video to the keypoints API.
    2. Runs the same LSTM-based segmentation + grading as /infer.
    3. Returns a list of 5 binary scores (one per phase/criteria).
    """
    if not KEYPOINTS_API_URL:
        raise HTTPException(500, detail="KEYPOINTS_API_URL is not configured")

    exercise_raw = exercise.lower()
    exercise_key = EXERCISE_ALIASES.get(exercise_raw, exercise_raw)
    if exercise_key not in MODELS:
        raise HTTPException(400, detail=f"Unsupported exercise: {exercise}")

    # 1) Call keypoints API to get pose keypoints
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            files = {"file": (file.filename, file.file, file.content_type)}
            response = await client.post(KEYPOINTS_API_URL, files=files)

        if response.status_code != 200:
            raise HTTPException(400, detail="something went wrong during video processing")

        shape = tuple(map(int, response.headers["X-Array-Shape"].split(",")))
        keypoints = np.frombuffer(response.content, dtype=np.float32).reshape(shape)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(500, detail="unexpected error during keypoint extraction")

    # 2) Run segmentation + grading (similar to /infer)
    try:
        T = keypoints.shape[0]
        if T < 5:
            raise HTTPException(400, detail="Video too short for inference")

        features = keypoints.reshape(T, -1)  # (T, 132)
        x = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(device)
        lengths = torch.tensor([T], dtype=torch.long)

        stage_model = MODELS[exercise_key]["segmentation"]
        with torch.no_grad():
            logits = stage_model(x, lengths)  # (1, T, num_classes)
            preds = logits.argmax(dim=-1).squeeze(0).cpu().numpy()  # (T,)

        stage_segments = extract_stages(preds)

        grade_model, scaler = MODELS[exercise_key]["grading"]
        # Collect per-segment pass/fail per predicted stage id
        num_phases = 5
        phase_scores = {i: [] for i in range(num_phases)}

        for stage_id, s, e in stage_segments:
            stage_feats = features[s:e + 1]
            if scaler is not None:
                stage_feats = (stage_feats - scaler["mean"]) / (scaler["std"] + scaler["eps"])

            stage_x = torch.tensor(stage_feats, dtype=torch.float32).unsqueeze(0).to(device)
            stage_len = torch.tensor([stage_feats.shape[0]], dtype=torch.long)

            with torch.no_grad():
                logit = grade_model(stage_x, stage_len)
                prob = torch.sigmoid(logit).item()
                passed = int(prob > 0.5)

            if 0 <= stage_id < num_phases:
                phase_scores[stage_id].append(passed)

        # 3) Reduce to a single binary score per phase (5 values)
        final_scores = []
        for phase_id in range(num_phases):
            scores = phase_scores[phase_id]
            if not scores:
                # If the phase was never predicted, mark as 0 (to improve)
                final_scores.append(0)
            else:
                # Majority vote over segments of that phase
                ones = sum(scores)
                zeros = len(scores) - ones
                final_scores.append(1 if ones >= zeros else 0)

        return {"score": final_scores}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(500, detail="unexpected error during prediction")
