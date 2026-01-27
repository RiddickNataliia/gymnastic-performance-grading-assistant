import pandas as pd

class StylerService():

    @classmethod
    def style_t_dataframe(self, df_t: pd.DataFrame):
        color_rating = lambda val: "color: red; font-weight: bold;" if val == "to improve" else ""
        styler: pd.io.formats.style.Styler = df_t.style.map(color_rating, subset=pd.IndexSlice[[df_t.index[-1]], :])
        styler = styler.set_properties(**{"text-align": "center"})
        styler = styler.set_properties(pd.IndexSlice[[df_t.index[-2]], :], **{"text-align": "left", "vertical-align": "top"})
        return styler