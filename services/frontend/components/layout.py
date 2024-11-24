from dash import dcc, html
import dash_bootstrap_components as dbc

layout = html.Div(
    id="app-container",
    style={
        'display': 'flex',
        'flex-direction': 'column',
        'min-height': '100vh',  # Ensure it spans the viewport height
        'background-color': '#f8f9fa',  # Optional: set a background color
    },
    children=[
        # Main Section: Introductory Content
        dbc.Container(
            className='d-flex align-items-center gap-6 my-5',  # Flexbox container for alignment and spacing
            children=[
                # Left Section: Text
                html.Div(
                    className='d-flex flex-column gap-3',
                    style={
                        'flex': '1 0 69%',  # Allow text to occupy 60% of the space
                        'max-width': '69%'  # Prevent the text container from growing too large
                    },
                    children=[
                        html.H2(
                            [
                                "Exploring ",
                                html.Span("AI", style={"color": "#3E85EE"}),  # Replace with your button's blue color
                                " at the University of ",
                                html.Span("Barcelona", style={"color": "#3E85EE"}),  # Same color
                                "."
                            ],
                            className='text-dark display-2 fw-bold lh-tight'
                        ),
                        html.P(
                            "Discover how AI is revolutionizing education at the UB. Dive into the latest data-driven visualizations "
                            "gathered by the researchers of MapAI.",
                            className='text-muted fw-large'
                        ),
                        html.Div(
                            html.Button(
                                "Let's Explore!",
                                className='btn btn-primary rounded px-4 py-3 fw-bold',
                                style={
                                    'background-color': '#6ea8fe',
                                    'color': '#f7f7f7',
                                    'border': 'none'
                                }
                            )
                        ),
                        html.P(
                            [
                                "Already exploring AI? ",
                                html.A(
                                    "Sign In",
                                    href='#',
                                    className='text-primary fw-bold'
                                )
                            ],
                            className='text-muted fw-medium'
                        )
                    ]
                ),
                # Right Section: Illustration
                html.Div(
                    className='position-relative',
                    style={
                        'flex': '1 1 40%',  # Allow image to occupy 40% of the space
                        'max-width': '40%'  # Prevent the image container from growing too large
                    },
                    children=[
                        html.Img(
                            src='/assets/img/robots_help.PNG',
                            alt='illustration',
                            className='img-fluid',
                            style={
                                'width': '100%',  # Ensures image scales to container width
                                'height': 'auto',  # Maintain aspect ratio
                                'object-fit': 'contain',  # Fit within the container bounds
                                'border-radius': '10%'
                            }
                        )
                    ]
                )
            ],
            style={
                'display': 'flex',
                'gap': '2px',
                'align-items': 'center',
                'justify-content': 'space-between',
                'width': '100%',  # Stretch the main section across the entire width
                'margin-left': '0',  # No extra margin
                'margin-right': '20px',  # Slight margin for spacing
                'padding': '0px 0px 0px 40px'
            }
        ),
        html.Div(
            id="cards",
            children=[
                html.Div(
                    className="bg-gradient-to-r from-blue-100 via-blue-50 to-blue-100 rounded-lg p-8",
                    children=[
                        html.H1(
                            "How do we visualize AI in Education?",
                            className="text-5xl font-title text-neutral-950",
                            style={
                                'text-align': 'left',
                                'font-weight': '800'
                            }
                        ),
                        html.P(
                            "This visualization is based on survey data collected from the teaching staff at the "
                            "University of Barcelona. For the development of the research, the results have been "
                            "categorized into the following areas.",
                            className="text-neutral-800 mt-4 leading-7 text-lg",
                            style={
                                'text-align': 'justify'
                            }
                        ),
                        html.Div(
                            className="mt-8 grid grid-cols-4 gap-4",
                            children=[
                                html.Div(
                                    className="bg-gradient-to-b from-red-100 to-red-200 rounded-md p-6 shadow-sm "
                                              "hover:shadow-lg transition duration-200",
                                    children=[
                                        html.H2(
                                            "Knowledge of AI",
                                            className="text-center font-semibold text-red-700 text-lg"
                                        ),
                                        html.P(
                                            "Understanding of AI concepts and technologies.",
                                            className="text-center mt-3 text-neutral-950"
                                        )
                                    ]
                                ),
                                html.Div(
                                    className="bg-gradient-to-b from-purple-100 to-purple-200 rounded-md p-6 "
                                              "shadow-sm hover:shadow-lg transition duration-200",
                                    children=[
                                        html.H2(
                                            "Uses of AI",
                                            className="text-center font-semibold text-purple-700 text-lg"
                                        ),
                                        html.P(
                                            "Applications and integration of AI tools in teaching practices.",
                                            className="text-center mt-3 text-neutral-950"
                                        )
                                    ]
                                ),
                                html.Div(
                                    className="bg-gradient-to-b from-green-100 to-green-200 rounded-md p-6 shadow-sm "
                                              "hover:shadow-lg transition duration-200",
                                    children=[
                                        html.H2(
                                            "Perceptions",
                                            className="text-center font-semibold text-green-700 text-lg"
                                        ),
                                        html.P(
                                            "Opinions and beliefs regarding AI's impact on education.",
                                            className="text-center mt-3 text-neutral-950"
                                        )
                                    ]
                                ),
                                html.Div(
                                    className="bg-gradient-to-b from-yellow-100 to-yellow-200 rounded-md p-6 "
                                              "shadow-sm hover:shadow-lg transition duration-200",
                                    children=[
                                        html.H2(
                                            "Training Needs",
                                            className="text-center font-semibold text-yellow-700 text-lg"
                                        ),
                                        html.P(
                                            "Self-assessment and suggestions for AI-related professional development.",
                                            className="text-center mt-3 text-neutral-950"
                                        )
                                    ]
                                )
                            ],
                            style={
                                'display': 'flex'
                            }
                        ),
                        html.P(
                            "To generate the visualizations, numerical values were assigned to the survey responses. "
                            "Using these values, an average score for each category related to artificial "
                            "intelligence was calculated. These scores represent the extent to which AI tools "
                            "are being adopted and used across various dimensions within the context of higher "
                            "education. They provide an aggregated overview, which may simplify the variability "
                            "in responses but allows for comparative insights across faculties and individuals.",
                            className="text-neutral-800 mt-8 leading-7 text-lg",
                            style={
                                'text-align': 'justify'
                            }
                        ),
                        html.P(
                            "Below you will find graphics that will help you explore the impact of each category "
                            "across the faculties of the University of Barcelona.",
                            className="text-neutral-800 mt-8 leading-7 text-lg",
                            style={
                                'text-align': 'justify'
                            }
                        ),
                        html.P(
                            "Data can also be filtered based on sociographic variables such as demographics or "
                            "professional profiles, allowing for deeper insights within each specific category.",
                            className="text-neutral-800 mt-4 leading-7 text-lg",
                            style={
                                'text-align': 'justify'
                            }
                        )
                    ]
                )
            ],
            style={
                'margin-top': '76px'
            }
        ),

        # Header with Title
        dbc.Container([
            dbc.Row([
                dbc.Col(html.H3("General Overview", className="text-center my-4 display-3"),style={'margin-top': '80px'}, width=10)
            ], justify="left"),
        ]),

        # Interval Component
        dcc.Interval(
            id='interval-component',
            interval=60 * 50000,  # Update every 50 minutes
            n_intervals=0,  # Initialize to 0
            disabled=False
        ),

        # Spike Map (scattermapbox) Visualization
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.H3("AI Spike Map Distribution", className="text-center my-3"),
                    html.P("Where is the AI implemented?", className="text-center lead"),
                    html.Div(id="spike-map"),  # Container for the Pydeck map
                    dcc.Interval(id="interval-component", interval=60000, n_intervals=0)  # Update every minute
                ], className="graph-container"), width=12
            )
        ], justify="center"),

        # Scatter3D Visualization
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.H3("3D Scatter Map AI Distribution", className="text-center my-3"),
                    html.P("3D representation of AI integration", className="text-center lead"),
                    dcc.Graph(id='scatter3d', config={'displayModeBar': False}, className="dash-graph")
                ], className="graph-container"), width=12
            )
        ], justify="center"),

        # Line Chart Race Visualization for all faculties
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.H3("Visualization of UB Faculties Historical Data", className="text-center my-3"),
                    html.P("Below is a dynamic line chart illustrating the evolution of AI in teaching",
                           className="text-center lead"),
                    dcc.Graph(id='historical-graph', config={'displayModeBar': False}, className="dash-graph")
                ], className="graph-container"), width=12
            )
        ], justify="center"),

        # Historical Records Data Table and Sunburst Chart Side-by-Side
        dbc.Row([
            # Historical Records Data Table (6 columns)
            dbc.Col(
                html.Div([
                    html.H3("Historical Records for All Faculties", className="text-center my-3"),
                    dcc.Loading(
                        id="loading-icon",
                        type="circle",
                        children=[
                            html.P('Compare different faculties of your choosing over time.',
                                   className="text-center lead"),
                            html.Div(id='historical-table', className="dash-graph")
                        ]
                    )
                ], className="graph-container h-100"), width=6
            ),
            # Sunburst Chart (6 columns)
            dbc.Col(
                html.Div([
                    html.H3("AI Usage by Faculty (Sunburst Chart)", className="text-center my-3"),
                    html.P("Visual comparison of the AI integration", className="text-center lead"),
                    dcc.Graph(id='sunburst-graph', config={'displayModeBar': False}, className="dash-graph"),
                ], className="graph-container h-100"), width=6
            )
        ], className="align-items-stretch",
            style={"margin-bottom": "30px"})
    ], )
