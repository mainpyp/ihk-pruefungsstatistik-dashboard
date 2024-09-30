from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from src.backend.data_functions import (
    get_all_semesters,
    get_berufe_for_semester,
    get_dataframe,
)


def create_data_layout():
    all_semesters = get_all_semesters()
    default_semester = all_semesters[0] if all_semesters else None
    default_beruf = (
        get_berufe_for_semester(default_semester)[0] if default_semester else None
    )
    default_df = (
        get_dataframe(default_semester, default_beruf)
        if default_semester and default_beruf
        else None
    )
    default_column = (
        default_df.columns[1]
        if default_df is not None and len(default_df.columns) > 1
        else None
    )

    return dbc.Container(
        [
            html.H1("IHK Berufsstatistik Dashboard", className="my-4"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Semester auswählen", className="form-label"),
                            dcc.Dropdown(
                                id="semester-dropdown",
                                options=[
                                    {"label": semester, "value": semester}
                                    for semester in all_semesters
                                ],
                                value=default_semester,
                                className="mb-3",
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.Label("Umschulung auswählen", className="form-label"),
                            dcc.Dropdown(
                                id="beruf-dropdown",
                                options=[
                                    {"label": beruf, "value": beruf}
                                    for beruf in get_berufe_for_semester(
                                        default_semester
                                    )
                                ]
                                if default_semester
                                else [],
                                value=default_beruf,
                                className="mb-3",
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.Label("Datenreihe auswählen", className="form-label"),
                            dcc.Dropdown(
                                id="column-dropdown",
                                options=[
                                    {"label": col, "value": col}
                                    for col in default_df.columns
                                    if col != "Standort"
                                ]
                                if default_df is not None
                                else [],
                                value=default_column,
                                className="mb-3",
                            ),
                        ],
                        md=4,
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dcc.Graph(
                                id="standort-barplot",
                                config={
                                    "displayModeBar": True,
                                    "modeBarButtonsToAdd": ["select2d", "lasso2d"],
                                    "displaylogo": False,
                                },
                                className="mb-4",
                            ),
                        ],
                        width=12,
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    dash_table.DataTable(
                                        id="beruf-table",
                                        sort_action="native",
                                        sort_mode="single",
                                        row_selectable="multi",
                                        style_table={"overflowX": "auto"},
                                        style_cell={"textAlign": "left"},
                                        style_data_conditional=[
                                            {
                                                "if": {"column_id": "Standort"},
                                                "textAlign": "left",
                                            }
                                        ],
                                    )
                                ],
                                className="mb-4",
                            ),
                        ],
                        width=12,
                    ),
                ]
            ),
        ],
        fluid=True,
    )
