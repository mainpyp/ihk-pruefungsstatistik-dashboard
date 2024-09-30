import sys
import os
from dash import Dash, html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import traceback
import plotly.express as px
import pandas as pd

# Add the root directory of the project to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.backend.data_functions import (
    get_all_semesters,
    get_berufe_for_semester,
    get_dataframe,
)

from pages.home_page import create_home_layout
from pages.data_page import create_data_layout

# Initialize the Dash app with Bootstrap CSS and Font Awesome
app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME,
        "/assets/custom.css",
    ],
    suppress_callback_exceptions=True,
)

# Sidebar layout
sidebar = html.Div(
    [
        html.Div(
            [
                html.H2("Navigation", className="sidebar-title"),
                html.I(className="fas fa-chevron-left", id="sidebar-toggle"),
            ],
            className="sidebar-header",
        ),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(
                    [html.I(className="fas fa-home me-2"), html.Span("Home")],
                    href="/",
                    id="home-link",
                    active="exact",
                ),
                dbc.NavLink(
                    [
                        html.I(className="fas fa-chart-bar me-2"),
                        html.Span("Berufsdaten"),
                    ],
                    href="/data",
                    id="data-link",
                    active="exact",
                ),
                dbc.NavLink(
                    [
                        html.I(className="fas fa-clock me-2"),
                        html.Span("Semestervergleich"),
                    ],
                    href="/semestervergleich",
                    id="semestervergleich-link",
                    active="exact",
                ),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    id="sidebar",
    className="sidebar",
)

# Main app layout
app.layout = html.Div(
    [
        dcc.Location(id="url"),
        html.Div(
            [
                html.Div(sidebar, id="sidebar-container"),
                html.Div(id="page-content", className="content-container"),
            ],
            className="app-container",
        ),
    ],
    className="main-container",
)


@app.callback(
    Output("sidebar", "className"),
    Output(
        "page-content", "className"
    ),  # Changed from "content-container" to "page-content"
    Output("sidebar-toggle", "className"),
    Input("sidebar-toggle", "n_clicks"),
    State("sidebar", "className"),
)
def toggle_sidebar(n_clicks, sidebar_class):
    if n_clicks and "collapsed" not in sidebar_class:
        return "sidebar collapsed", "content-container expanded", "fas fa-chevron-right"
    return "sidebar", "content-container", "fas fa-chevron-left"


@app.callback(
    Output("page-content", "children"),
    Output("home-link", "active"),
    Output("data-link", "active"),
    Input("url", "pathname"),
)
def render_page_content(pathname):
    if pathname == "/" or pathname == "":
        return create_home_layout(), True, False
    elif pathname == "/data":
        return create_data_layout(), False, True
    return html.Div("404 - Not found", className="error-message"), False, False


@app.callback(
    Output("beruf-table", "data"),
    Output("beruf-table", "columns"),
    Output("beruf-table", "selected_rows"),
    Output("standort-barplot", "figure"),
    Input("semester-dropdown", "value"),
    Input("beruf-dropdown", "value"),
    Input("column-dropdown", "value"),
    Input("beruf-table", "sort_by"),
    Input("beruf-table", "derived_virtual_selected_rows"),
    Input("beruf-table", "derived_virtual_data"),
)
def update_table_and_plot(
    selected_semester,
    selected_beruf,
    selected_column,
    sort_by,
    selected_rows,
    virtual_data,
):
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    print(
        f"Callback triggered. Semester: {selected_semester}, Beruf: {selected_beruf}, Column: {selected_column}"
    )

    try:
        if not all([selected_semester, selected_beruf, selected_column]):
            print("Not all required inputs are available. Raising PreventUpdate.")
            raise PreventUpdate

        df = get_dataframe(selected_semester, selected_beruf)
        print(f"Dataframe loaded. Shape: {df.shape}")

        if df.empty:
            print("Dataframe is empty. Raising PreventUpdate.")
            raise PreventUpdate

        # Sort the dataframe based on the selected column in descending order
        df = df.sort_values(by=selected_column, ascending=False)

        # Apply table sorting if it exists
        if sort_by:
            df = df.sort_values(
                by=sort_by[0]["column_id"], ascending=sort_by[0]["direction"] == "asc"
            )

        # Set all rows as selected by default
        if selected_rows is None or len(selected_rows) == 0:
            selected_rows = list(range(len(df)))

        # Filter rows based on selection
        df_filtered = df.iloc[selected_rows] if selected_rows else df

        # Ensure the order of Standorte in the plot matches the table
        standort_order = df_filtered["Standort"].tolist()

        # Update table
        table_data = df.to_dict("records")
        table_columns = [{"name": i, "id": i} for i in df.columns]

        # Update plot
        fig = px.bar(
            df_filtered,
            x="Standort",
            y=selected_column,
            category_orders={"Standort": standort_order},
        )
        fig.update_layout(
            xaxis_title="Standort",
            yaxis_title=selected_column,
            xaxis_tickangle=-45,
            margin=dict(b=150),  # Increase bottom margin to accommodate rotated labels
        )
        fig.update_traces(texttemplate="%{y}", textposition="outside")

        # Cut x-axis labels to first 10 characters and add "..." if longer
        fig.update_xaxes(
            ticktext=[
                standort[:10] + "..." if len(standort) > 10 else standort
                for standort in standort_order
            ],
            tickvals=standort_order,
        )

        print("Table and plot updated successfully.")
        return table_data, table_columns, selected_rows, fig
    except Exception as e:
        print(f"Error in update_table_and_plot: {str(e)}")
        print(traceback.format_exc())
        raise


@app.callback(
    Output("column-dropdown", "options"),
    Input("semester-dropdown", "value"),
    Input("beruf-dropdown", "value"),
)
def set_column_options(selected_semester, selected_beruf):
    if not selected_semester or not selected_beruf:
        raise PreventUpdate
    df = get_dataframe(selected_semester, selected_beruf)
    return [
        {"label": column, "value": column}
        for column in df.columns
        if column != "Standort"
    ]


@app.callback(Output("beruf-dropdown", "options"), Input("semester-dropdown", "value"))
def set_beruf_options(selected_semester):
    if not selected_semester:
        raise PreventUpdate
    return [
        {"label": beruf, "value": beruf}
        for beruf in get_berufe_for_semester(selected_semester)
    ]


@app.callback(Output("beruf-dropdown", "value"), Input("beruf-dropdown", "options"))
def set_beruf_value(available_options):
    return available_options[0]["value"] if available_options else None


if __name__ == "__main__":
    app.run_server(debug=True)
