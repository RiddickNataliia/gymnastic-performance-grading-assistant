import gradio as gr

def get_dropdown(label: str, values: list[str], selected_value: str|None, interactive: bool = True):
    return gr.Dropdown(
        value=selected_value,
        choices=values,
        label=label,
        interactive=interactive,
    )

def get_exercise_dropdown(values: list[str], selected_value: str|None):
    return get_dropdown("Exercise", values, selected_value)

def get_student_dropdown(values: list[str], selected_value: str|None):
    return get_dropdown("Students", values, selected_value)

def get_performance_dropdown(values: list[str], selected_value: str|None, interactive: bool):
    return get_dropdown("Performance", values, selected_value, interactive)