from dash import html
import dash_bootstrap_components as dbc


def create_home_layout():
    return dbc.Container(
        [
            html.H1("Welcome to IHK Berufsstatistik Dashboard", className="my-4"),
            html.P(
                "Select 'Data' in the sidebar to view the dashboard.", className="lead"
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H4("About this Dashboard", className="card-title"),
                        html.P(
                            "This dashboard provides insights into IHK Berufsstatistik data. "
                            "Use the 'Data' page to explore various statistics and visualizations.",
                            className="card-text",
                        ),
                    ]
                ),
                className="mt-4",
            ),
        ],
        fluid=True,
    )
