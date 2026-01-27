import os
import shutil
import glob
import pandas as pd
from pathlib import Path
from datetime import datetime

from services.df_styler import StylerService

# ue = user exercise
# uer = user exercise rating
# uev = user exercise video

class ExerciseService():
    def __init__(self, store_path: str):
        self.store_path = store_path
        self.rating_path = f"{store_path}/ratings"
        self.videos_path = f"{store_path}/videos"
        os.makedirs(self.store_path, exist_ok=True)
        os.makedirs(self.rating_path, exist_ok=True)
        os.makedirs(self.videos_path, exist_ok=True)

    ### helpers
    
    def get_video(self, ue: str):
        matching_files = glob.glob(f"{self.videos_path}/{ue}.*")
        return matching_files[0] if matching_files else None
    
    def get_rating(self, ue: str):
        dataframe = pd.read_csv(f"{self.rating_path}/{ue}.csv")
        return StylerService.style_t_dataframe(dataframe)
    
    def get_items_with_prefix(self, prefix: str, parts_lb: int, parts_ub):
        prefix += "-"
        items = []
        rating_files = os.listdir(self.rating_path)
        all_exercises = [Path(rating_file).stem for rating_file in rating_files]
        filtered_exercises = [ue for ue in all_exercises if ue.startswith(prefix)]
        for exercise in filtered_exercises:
            parts = exercise.split("-")
            item = "-".join(parts[parts_lb:parts_ub])
            if item not in items:
                items.append(item)
        return items
    
    def create_rating(self, ue: str, data: pd.DataFrame):
        data.to_csv(f"{self.rating_path}/{ue}.csv", index=False)

    def create_video(self, ue: str, tmp_path: str):
        video_extension = Path(tmp_path).suffix
        full_video_path = f"{self.videos_path}/{ue}{video_extension}"
        shutil.copy2(tmp_path, full_video_path)

    ### main

    def get_performance(self, exercise: str, student: str, performance: str):
        ue = f"{exercise}-{student}-{performance}"
        return self.get_video(ue), self.get_rating(ue)
    
    def get_students_by_exercise(self, exercise: str):
        return self.get_items_with_prefix(exercise, 1, 3)

    def get_performances_by_student(self, exercise: str, student: str):
        return self.get_items_with_prefix(f"{exercise}-{student}", 3, 9)

    def create(self, exercise: str, first_name: str, last_name: str, data: pd.DataFrame, video_path: str):
        now = datetime.now()
        ue = f"{exercise}-{first_name}-{last_name}-{now.strftime("%Y-%m-%d-%H-%M-%S")}"
        self.create_rating(ue, data)
        self.create_video(ue, video_path)

    def delete(self, ue: str):
        rating_file = f"{self.rating_path}/{ue}.csv"
        video_file = self.get_video(ue)
        for file in [rating_file, video_file]:
            if os.path.exists(file):
                os.remove(file)
        

    