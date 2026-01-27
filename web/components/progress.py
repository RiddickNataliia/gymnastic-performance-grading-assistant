import gradio as gr

from components.buttons import active_download_button, inactive_download_button, active_delete_button, inactive_delete_button
from components.modals import modal_visible, modal_invisible
from components.dropdown import get_exercise_dropdown, get_student_dropdown, get_performance_dropdown

from services.evaluation import EvaluationService
from services.exercise import ExerciseService
from services.zip import ZipService

def create_progress_tab(evaluation_service: EvaluationService, exercise_service: ExerciseService, zip_service: ZipService):    
    initial_exercises = evaluation_service.get_exercises()
    initial_exercises_value = initial_exercises[0]
    initial_students = exercise_service.get_students_by_exercise(initial_exercises_value)

    def on_exercise_dropdown_select(exercise: str):
        del_button = inactive_delete_button()
        down_button = inactive_download_button()
        video_path = None
        data = evaluation_service.get_criteria(exercise)
        students = exercise_service.get_students_by_exercise(exercise)
        students_dropdown_component = get_student_dropdown(students, None)
        performance_dropdown_component = get_performance_dropdown([], None, False)
        return del_button, down_button, video_path, data, performance_dropdown_component, students_dropdown_component
    
    def on_student_dropdown_select(exercise: str, student: str):
        del_button = inactive_delete_button()
        down_button = inactive_download_button()
        video_path = None
        data = evaluation_service.get_criteria(exercise)
        performances = exercise_service.get_performances_by_student(exercise, student)
        performance_dropdown_component = get_performance_dropdown(performances, None, True)
        return del_button, down_button, video_path, data, performance_dropdown_component
    
    def on_performance_dropdown_select(exercise: str, student: str, performance: str):
        del_button = active_delete_button()
        down_button = active_download_button()
        video_path, data = exercise_service.get_performance(exercise, student, performance)
        return del_button, down_button, video_path, data

    def on_download_button_click(exercise: str, student: str, performance: str, video_path:str):
        zip_path = zip_service.create_zip(f"{exercise}-{student}-{performance}", video_path)        
        return modal_visible(), zip_path, zip_path

    def on_delete_button_click(exercise: str, student: str, performance: str):
        base_name = f"{exercise}-{student}-{performance}"
        return modal_visible(), base_name

    def on_delete_modal_accept_button_click(exercise: str, ue: str):
        exercise_service.delete(ue)

        exercise_dropdown_component = get_exercise_dropdown(initial_exercises, exercise)
        student_dropdown_component = get_student_dropdown(initial_students, None)
        performance_dropdown_component = get_performance_dropdown([], None, False)

        data = evaluation_service.get_criteria(exercise)

        del_button = inactive_delete_button()
        down_button = inactive_download_button()
        video_path = None

        return modal_invisible(), "", exercise_dropdown_component, student_dropdown_component, performance_dropdown_component, data, video_path, down_button, del_button

    def after_zip_modal_close(zip_file: str):
        evaluation_service.delete_results_zip(zip_file)

    with gr.Tab("Progress"):
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
                exercise_dropdown = get_exercise_dropdown(initial_exercises, initial_exercises_value)
                student_dropdown = get_student_dropdown(initial_students, None)
                performance_dropdown = get_performance_dropdown([], None, False)
            with gr.Column(scale=2):
                video_component = gr.Video(
                    label="Video",
                    interactive=False
                )
            with gr.Column(scale=2):
                pass
        
        with gr.Row(equal_height=True):
            with gr.Column(scale=1):
                pass
            with gr.Column(scale=2):
                with gr.Row(equal_height=True):
                    download_button = inactive_download_button()
                    delete_button = inactive_delete_button()
            with gr.Column(scale=2):
                pass

        with modal_invisible() as zip_modal:
            zip_modal_textbox = gr.Textbox(visible=False)
            gr.Markdown(f"# Your files are ready for downloading", elem_classes="title-centered")
            with gr.Row():
                with gr.Column():
                    zip_modal_download_button = gr.DownloadButton("Download", variant="primary")
                    zip_modal_cancel_button = gr.Button("Cancel", variant="secondary")

        with modal_invisible() as delete_modal:
            delete_modal_textbox = gr.Textbox(visible=False)
            gr.Markdown(f"# Are you sure you want to delete this performance, it will be gone forever", elem_classes="title-centered")
            with gr.Row():
                with gr.Column():
                    delete_modal_accept_button = gr.Button("Delete", variant="secondary")
                    delete_modal_cancel_button = gr.Button("Cancel", variant="primary")

    exercise_dropdown.select(
        fn=on_exercise_dropdown_select,
        inputs=[exercise_dropdown],
        outputs=[delete_button, download_button, video_component, score_dataframe, performance_dropdown, student_dropdown]
    )

    student_dropdown.select(
        fn=on_student_dropdown_select,
        inputs=[exercise_dropdown, student_dropdown],
        outputs=[delete_button, download_button, video_component, score_dataframe, performance_dropdown]
    )

    performance_dropdown.select(
        fn=on_performance_dropdown_select,
        inputs=[exercise_dropdown, student_dropdown, performance_dropdown],
        outputs=[delete_button, download_button, video_component, score_dataframe]
    )

    download_button.click(
        fn=on_download_button_click,
        inputs=[exercise_dropdown, student_dropdown, performance_dropdown, video_component],
        outputs=[zip_modal, zip_modal_textbox, zip_modal_download_button]
    )

    zip_modal_download_button.click(
        fn=modal_invisible,
        outputs=[zip_modal]
    ).then(
        fn=after_zip_modal_close,
        inputs=[zip_modal_textbox]
    )

    zip_modal_cancel_button.click(
        fn=modal_invisible,
        outputs=[zip_modal]
    ).then(
        fn=after_zip_modal_close,
        inputs=[zip_modal_textbox]
    )

    delete_button.click(
        fn=on_delete_button_click,
        inputs=[exercise_dropdown, student_dropdown, performance_dropdown],
        outputs=[delete_modal, delete_modal_textbox]
    )

    delete_modal_accept_button.click(
        fn=on_delete_modal_accept_button_click,
        inputs=[exercise_dropdown, delete_modal_textbox],
        outputs=[delete_modal, delete_modal_textbox, exercise_dropdown, student_dropdown, performance_dropdown, score_dataframe, video_component, download_button, delete_button]
    )

    delete_modal_cancel_button.click(
        fn=modal_invisible,
        outputs=[delete_modal]
    )