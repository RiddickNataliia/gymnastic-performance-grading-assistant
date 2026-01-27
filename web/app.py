import os
import gradio as gr

from style.style import css, custom_theme

from services.evaluation import EvaluationService
from services.exercise import ExerciseService
from services.zip import ZipService

from components.evaluation import create_evaluation_tab
from components.progress import create_progress_tab

PREDICTION_API_URL = os.environ.get("PREDICTION_API_URL")
CRITERIA_DIR = "data/criteria"
VIDEOS_DIR = "data/videos"
STORE_PATH = "store"

evaluation_service = EvaluationService(PREDICTION_API_URL, CRITERIA_DIR, VIDEOS_DIR)
exercise_service = ExerciseService(STORE_PATH)
zip_service = ZipService("exports", "store/ratings", "store/videos")

with gr.Blocks(title="trAIner", css=css, theme=custom_theme, fill_height=True, fill_width=True) as demo:
    evaluation_tab = create_evaluation_tab(evaluation_service, exercise_service)
    progress_tab = create_progress_tab(evaluation_service, exercise_service, zip_service)

if __name__ == "__main__":
    demo.queue().launch(favicon_path="./icons/howest-loso-transparent.png")