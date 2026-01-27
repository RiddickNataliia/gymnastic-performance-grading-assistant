from gradio_modal import Modal

modal_visible = lambda: Modal(visible=True, allow_user_close=False)
modal_invisible = lambda: Modal(visible=False)