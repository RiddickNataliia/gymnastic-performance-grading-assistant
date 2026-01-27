import gradio as gr

with open("style/style.css") as f:
    css = f.read()

white = "#FFFFFF"
red = "#FF0000"
of_red = "#f87171"

howest_blue = gr.themes.colors.Color(
    name="howest_blue",
    c50="#ecf9fe",
    c100="#d0f1fc",
    c200="#aae6fa",
    c300="#85dbf8",
    c400="#60d0f6",
    c500="#44c8f5",  # Picton Blue, Howest
    c600="#39aad0",
    c700="#2f8cab",
    c800="#256e86",
    c900="#1b5062",
    c950="#11323d",
)

sky = gr.themes.colors.sky

color = sky

custom_theme = gr.themes.Soft(primary_hue=color, radius_size=gr.themes.sizes.radius_lg).set(
    block_background_fill=color.c200,
    block_label_border_color=color.c200,
    
    table_even_background_fill=color.c200,
    table_odd_background_fill=color.c100,
    table_border_color=color.c900,

    background_fill_secondary=color.c200,

    button_secondary_background_fill = red,
    button_secondary_background_fill_dark = red,

    button_secondary_background_fill_hover = of_red,
    button_secondary_background_fill_hover_dark = of_red,

    button_secondary_border_color = red,
    button_secondary_border_color_dark = red,

    button_secondary_text_color = white,
    button_secondary_text_color_dark = white
)
