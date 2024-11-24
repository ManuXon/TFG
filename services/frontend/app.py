import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from components.callbacks import register_callbacks
from components.layout import layout  # Import the layout from layout.py

# Load external stylesheets (Bootstrap and custom CSS)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, "custom.css",
                                                "https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/3.4.11/tailwind.min.css"], suppress_callback_exceptions=True)

# Header
# Header with logo on the right

header = html.Header(
    className='d-flex align-items-center justify-content-between py-3 px-4',
    children=[
        # Left Section: Logo and Title
        html.Div(
            className='d-flex align-items-center gap-2',
            children=[
                html.Img(
                    src='/assets/img/logomap.png',
                    alt='logo',
                    className='rounded-circle',
                    style={'width': '40px', 'height': '40px', 'object-fit': 'contain'}
                ),
                html.H1(
                    "MapAI Insights",
                    className='text-dark fw-bold',
                    style={'font-size': '1.25rem'}  # Font size for "text-lg"
                )
            ]
        ),
        # Right Section: Navigation Links and Button
        html.Nav(
            className='d-flex align-items-center gap-4',
            children=[
                html.A(
                    "Faculties",
                    href="#",
                    className='text-dark font-medium-h text-decoration-none'
                ),
                html.A(
                    "Teachers",
                    href="#",
                    className='text-dark font-medium-h text-decoration-none'
                ),
                dbc.Button(
                    "Analist mode",
                    className='rounded px-3 py-2 fw-bold',
                    style={
                        'background-color': '#6ea8fe',
                        'color': '#f7f7f7',
                        'border': 'none'
                    }
                )
            ]
        )
    ]
)

footer = html.Footer(
    children=[
        html.Div("University of Barcelona - Teaching & AI", style={"text-align": "center", "color": "white"}),
        html.Div("Data collected and analyzed by a Teaching Innovation Project (mapAI-UB)",
                 style={"text-align": "center", "color": "white"})
    ],
    style={"background-color": "#343a40", "padding": "10px 0", "margin-top": "auto", "position": "sticky",
           "bottom": "0"}
)

# Layout setup
app.layout = html.Div(
    className="container-wrapper",
    children=[
        html.Div(
            className="bg-light rounded shadow mx-auto",
            style={
                "background-color": "#f7f7f7",
                "border-radius": "10px",
                "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
                "margin": "0px auto",
                "width": "100%",
                "padding": "5px"
            },
            children=[
                header,  # Header component
                layout,  # Main content (imported from layout.py)
                footer   # Footer component
            ]
        )
    ],
    style={
        "background-color": "#f8f9fa",  # Optional outer background
        "min-height": "100vh",          # Ensures the container spans the viewport
        "display": "flex",
        "flex-direction": "column",
    }
)

# Register Callbacks
register_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
