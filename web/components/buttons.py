import gradio as gr

primary_button_active = lambda interactive, value: gr.Button(value=value, interactive=interactive, variant="primary")
secondary_button_active = lambda interactive, value: gr.Button(value=value, interactive=interactive, variant="secondary")

active_download_button = lambda: primary_button_active(True, "Download Results")
inactive_download_button = lambda: primary_button_active(False, "Download Results")

active_save_button = lambda: primary_button_active(True, "Save Results")
inactive_save_button = lambda: primary_button_active(False, "Save Results")

active_delete_button = lambda: secondary_button_active(True, "Delete Video")
inactive_delete_button = lambda: secondary_button_active(False, "Delete Video")