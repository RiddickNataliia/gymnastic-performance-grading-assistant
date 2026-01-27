import gradio as gr
import pandas as pd
from pathlib import Path
from datetime import datetime
import os
import requests

from services.documents import DocumentService
from services.df_styler import StylerService

def process_path(path: str, extension: str, extract_data: callable):
    data = {}
    filenames = os.listdir(path)
    filenames.sort()
    for filename in filenames:
        if filename.endswith(extension):
            key = os.path.splitext(filename)[0]
            file_path = os.path.join(path, filename)
            data[key] = extract_data(file_path)
    return data

none = lambda file_path: file_path
extract_dataframe = lambda file_path: pd.read_csv(file_path)

# get_score

def get_prediction(video_path: str, prediction_api_url:str, selected_exercise: str):
    try:
        response = requests.post(prediction_api_url, params={"exercise": selected_exercise}, files={'file': open(Path(video_path), 'rb')})
        if response.status_code == 200:
            return response.json().get("score")
        raise Exception()
    except:
        raise gr.Error("something went wrong during video preocessing", duration=10)

class EvaluationService():
    def __init__(self, prediction_api_url: str, criteria_dir: str, example_videos_dir: str):
        os.makedirs("exports", exist_ok=True)

        criteria: dict[str,pd.DataFrame] = process_path(criteria_dir, ".csv", extract_dataframe)
        videos: dict[str,str] = process_path(example_videos_dir, ".MOV", none)

        exercises = list(criteria.keys())
        default_exercise = exercises[0]

        self.prediction_api_url = prediction_api_url
        self.criteria = criteria
        self.videos = videos

        self.exercises = exercises
        self.default_exercise = default_exercise
        self.default_video = videos[default_exercise]

    def get_exercise_video(self, exercise: str):
        return self.videos[exercise]
    
    def get_exercises(self):
        return list(self.criteria.keys())

    def get_criteria_rated(self, video_path: str|None, selected_exercise: str):
        df = self.criteria[selected_exercise].copy()
        if video_path:
            df["Rating"] = get_prediction(video_path, self.prediction_api_url, selected_exercise)
        else:
            df["Rating"] = ["" for _ in range(len(df))]
        df["Rating"] = df["Rating"].map({0: "to improve", 1: "✅"}).fillna("")
        df_t: pd.DataFrame = df.set_index(df.columns[0]).T
        return StylerService.style_t_dataframe(df_t)

    def get_criteria(self, selected_exercise: str):
        return self.get_criteria_rated(None, selected_exercise)
    
    def get_initial_criteria(self):
        return self.get_criteria(self.default_exercise)
    
    def get_zip(self, exercise: str, video_path:str, data: pd.DataFrame, first_name: str, last_name: str):        
        now = datetime.now()
        data = data.replace("✅", "correct")
        elements = DocumentService.generate_pdf_elements(exercise, data, first_name, last_name, now)

        base_name = f"exports/{exercise}-{first_name}-{last_name}"
        csv_filename = f"{base_name}.csv"
        pdf_filename = f"{base_name}.pdf"
        zip_filename = f"{base_name}-{now.strftime("%Y-%m-%d-%H-%M-%S")}.zip"

        DocumentService.create_csv(csv_filename, data)
        DocumentService.create_pdf(pdf_filename, elements)
        DocumentService.create_zipfile(zip_filename, video_path, csv_filename, pdf_filename, base_name)
        DocumentService.remove_files([csv_filename, pdf_filename])

        return zip_filename
    
    def delete_results_zip(self, zip_filename: str):
        DocumentService.remove_files([zip_filename])
        
