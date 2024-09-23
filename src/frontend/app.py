import sys
import os
from dash import Dash, html, dcc, Input, Output
from dash.dash_table import DataTable

# Add the root directory of the project to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.backend.data_functions import (
    get_all_semesters,
    get_berufe_for_semester,
    get_dataframe,
)

app = Dash(__name__)

app.layout = html.Div(
    children=[
        html.H1(children="IHK Berufsstatistik Dashboard"),
        dcc.Dropdown(
            id="semester-dropdown",
            options=[
                {"label": semester, "value": semester}
                for semester in get_all_semesters()
            ],
            value=get_all_semesters()[0],
        ),
        dcc.Dropdown(
            id="beruf-dropdown",
        ),
        DataTable(
            id="beruf-table",
            sort_action="native",
            sort_mode="multi",
        ),
    ]
)


@app.callback(
    Output("beruf-table", "data"),
    Input("semester-dropdown", "value"),
    Input("beruf-dropdown", "value"),
)
def update_table(selected_semester, selected_beruf):
    df = get_dataframe(selected_semester, selected_beruf)
    return df.to_dict("records")


@app.callback(Output("beruf-dropdown", "options"), Input("semester-dropdown", "value"))
def set_beruf_options(selected_semester):
    return [
        {"label": beruf, "value": beruf}
        for beruf in get_berufe_for_semester(selected_semester)
    ]


@app.callback(Output("beruf-dropdown", "value"), Input("beruf-dropdown", "options"))
def set_beruf_value(available_options):
    return available_options[0]["value"] if available_options else None


if __name__ == "__main__":
    app.run_server(debug=True)
