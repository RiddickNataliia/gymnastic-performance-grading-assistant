import gradio as gr
import pandas as pd
from components.buttons import active_download_button, inactive_download_button, active_save_button, inactive_save_button
from components.modals import modal_visible, modal_invisible
from services.evaluation import EvaluationService
from services.exercise import ExerciseService
from services.name import NameService

def create_evaluation_tab(evaluation_service: EvaluationService, exercise_service: ExerciseService):
    def on_exercise_dropdown_select(exercise: str):
        example_video_path = evaluation_service.get_exercise_video(exercise)
        dataframe = evaluation_service.get_criteria(exercise)
        return example_video_path, dataframe, None, inactive_download_button(), inactive_save_button()

    def on_video_component_upload(video_path: str, exercise: str):
        dataframe = evaluation_service.get_criteria_rated(video_path, exercise)
        return dataframe, active_download_button(), active_save_button()

    def on_download_button_click(exercise: str, first_name: str, last_name: str, data: pd.DataFrame, video_path:str):
        warnings = NameService.get_warnings(first_name, last_name)

        if len(warnings):
            for warning in warnings:
                gr.Warning(warning)
            return modal_invisible(), None, None
        
        zip_path = evaluation_service.get_zip(exercise, video_path, data, first_name, last_name)
        
        return modal_visible(), zip_path, zip_path
    
    def on_save_button_click(exercise: str, first_name: str, last_name: str, data: pd.DataFrame, video_path: str):
        warnings = NameService.get_warnings(first_name, last_name)

        if len(warnings):
            for warning in warnings:
                gr.Warning(warning)     
            return data, video_path, active_download_button(), active_save_button()       

        exercise_service.create(exercise, first_name, last_name, data, video_path)

        return evaluation_service.get_criteria(exercise), None, inactive_download_button(), inactive_save_button()

    def on_video_clear(exercise: str):
        dataframe = evaluation_service.get_criteria(exercise)
        return dataframe, None, inactive_download_button(), inactive_save_button()

    def after_zip_modal_close(zip_file: str):
        evaluation_service.delete_results_zip(zip_file)

    with gr.Tab("Evaluation"):
        with gr.Row(equal_height=True):
            with gr.Column(scale=1):
                gr.Image("icons/howest-loso-transparent.png", container=False, show_fullscreen_button=False, show_download_button=False, height=100)
            with gr.Column(scale=4):
                score_dataframe = gr.Dataframe(
                    value=evaluation_service.get_initial_criteria(),
                    interactive=False,
                    wrap=True,
                    column_widths=["200px" for i in range(5)],
                )        
        with gr.Row(equal_height=True):
            with gr.Column(scale=1):
                firstname_textbox = gr.Textbox(placeholder="first name", label="First Name")
                lastname_textbox = gr.Textbox(placeholder="last name", label="Last Name")
                exercise_dropdown = gr.Dropdown(
                    label="Exercise",
                    choices=evaluation_service.get_exercises(),
                    interactive=True,
                )
            with gr.Column(scale=2):
                video_component = gr.Video(
                    label="Upload Video",
                    sources=["upload"],
                )
            with gr.Column(scale=2):
                example_video_component = gr.Video(
                    value=evaluation_service.default_video,
                    label="Example",
                    interactive=False,
                    show_download_button=False,
                )

        with gr.Row():
            with gr.Column(scale=1):
                pass
            with gr.Column(scale=2):
                with gr.Row():
                    download_button = inactive_download_button()
                    save_button = inactive_save_button()
            with gr.Column(scale=2):
                pass

        with modal_invisible() as zip_modal:
            modal_zipfile_textbox = gr.Textbox(visible=False)
            gr.Markdown(f"# Your files are ready for downloading", elem_classes="title-centered")
            with gr.Row():
                with gr.Column():
                    modal_download_button = gr.DownloadButton("Download", variant="primary")
                    modal_cancel_button = gr.Button("Cancel", variant="secondary")

    exercise_dropdown.select(
        fn=on_exercise_dropdown_select,
        inputs=[exercise_dropdown],
        outputs=[example_video_component, score_dataframe, video_component, download_button, save_button]
    )

    video_component.upload(
        fn=on_video_component_upload,
        inputs=[video_component, exercise_dropdown],
        outputs=[score_dataframe, download_button, save_button]
    )

    video_component.clear(
        fn=on_video_clear,
        inputs=[exercise_dropdown],
        outputs=[score_dataframe, video_component, download_button, save_button]
    )

    download_button.click(
        fn=on_download_button_click,
        inputs=[exercise_dropdown, firstname_textbox, lastname_textbox, score_dataframe, video_component],
        outputs=[zip_modal, modal_zipfile_textbox, modal_download_button]
    )

    save_button.click(
        fn=on_save_button_click,
        inputs=[exercise_dropdown, firstname_textbox, lastname_textbox, score_dataframe, video_component],
        outputs=[score_dataframe, video_component, download_button, save_button]
    )

    modal_download_button.click(
        fn=modal_invisible,
        outputs=[zip_modal]
    ).then(
        fn=after_zip_modal_close,
        inputs=[modal_zipfile_textbox]
    )

    modal_cancel_button.click(
        fn=modal_invisible,
        outputs=[zip_modal]
    ).then(
        fn=after_zip_modal_close,
        inputs=[modal_zipfile_textbox]
    )
