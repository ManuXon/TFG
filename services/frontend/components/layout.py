from dash import dcc, html
import dash_bootstrap_components as dbc
import dash_dangerously_set_inner_html

layout = html.Div(
    id="app-container",
    style={
        'display': 'flex',
        'flex-direction': 'column',
        'min-height': '100vh',  # Ensure it spans the viewport height
        'background-color': '#f8f9fa',  # Optional: set a background color
        'overflow-x': 'clip',
    },
    children=[
        # Main Section: Introductory Content
        dbc.Container(
            className='d-flex align-items-center gap-6 my-5 mx-7',  # Flexbox container for alignment and spacing
            children=[
                # Left Section: Text
                html.Div(
                    className='d-flex flex-column gap-3',
                    style={
                        'flex': '1 0 60%',  # Allow text to occupy 60% of the space
                        'max-width': '60%'  # Prevent the text container from growing too large
                        'padding-right:' '0px',
                        'padding-left': '4px'
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
                            className='text-dark display-1 fw-bold lh-tight'
                        ),
                        html.P(
                            "Discover how AI is revolutionizing education at the UB. Dive into the latest data-driven visualizations "
                            "gathered by the researchers of MapAI.",
                            className='text-muted fw-large',
                            style={'padding-right': '10px'}
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
                        'flex': '1 1 72%',  # Allow image to occupy 40% of the space
                        'max-width': '72%'  # Prevent the image container from growing too large
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
                                'border-radius': '13%'
                            }
                        )
                    ]
                )
            ],
            style={
                'display': 'flex',
                'gap': '11px',
                'align-items': 'center',
                'justify-content': 'space-between',
                'max-width': '100%',  # Stretch the main section across the entire width
                'margin-right': '0px',  # Slight margin for spacing
                'padding': '0px 24px 0px 70px'
            }
        ),
        dbc.Card(
            dbc.CardBody(
                dbc.Row(
                    [
                        # LEFT COLUMN - 2x2 Grid of Dimensions
                        dbc.Col(
                            html.Div(
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "1fr 1fr",
                                    "gridTemplateRows": "1fr 1fr",
                                    "gap": "8px",
                                    "height": "100%",
                                    "paddingRight": "20px",
                                    "padding-left": "7px",
                                },
                                children=[
                                    # Knowledge
                                    html.Div(
                                        style={
                                            "background": "linear-gradient(to bottom, #fee2e2, #fecaca)",
                                            "borderRadius": "12px",
                                            "padding": "20px",
                                            "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                                            "cursor": "default",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "justifyContent": "center",
                                            "textAlign": "center",
                                        },
                                        children=[
                                            html.H2(
                                                "Knowledge",
                                                style={
                                                    "color": "#b91c1c",
                                                    "fontWeight": "700",
                                                    "fontSize": "1.3rem",
                                                    "marginBottom": "10px",
                                                },
                                            ),
                                            html.P(
                                                "Understanding of AI concepts and technologies.",
                                                style={"margin": "0", "color": "#1a1a1a", "fontSize": "1rem"},
                                            ),
                                        ],
                                    ),

                                    # Uses
                                    html.Div(
                                        style={
                                            "background": "linear-gradient(to bottom, #ede9fe, #ddd6fe)",
                                            "borderRadius": "12px",
                                            "padding": "20px",
                                            "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                                            "cursor": "default",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "justifyContent": "center",
                                            "textAlign": "center",
                                        },
                                        children=[
                                            html.H2(
                                                "Uses",
                                                style={
                                                    "color": "#6b21a8",
                                                    "fontWeight": "700",
                                                    "fontSize": "1.3rem",
                                                    "marginBottom": "10px",
                                                },
                                            ),
                                            html.P(
                                                "Applications and integration of AI tools in teaching practices.",
                                                style={"margin": "0", "color": "#1a1a1a", "fontSize": "1rem"},
                                            ),
                                        ],
                                    ),

                                    # Perceptions
                                    html.Div(
                                        style={
                                            "background": "linear-gradient(to bottom, #dcfce7, #bbf7d0)",
                                            "borderRadius": "12px",
                                            "padding": "20px",
                                            "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                                            "cursor": "default",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "justifyContent": "center",
                                            "textAlign": "center",
                                        },
                                        children=[
                                            html.H2(
                                                "Perceptions",
                                                style={
                                                    "color": "#15803d",
                                                    "fontWeight": "700",
                                                    "fontSize": "1.3rem",
                                                    "marginBottom": "10px",
                                                },
                                            ),
                                            html.P(
                                                "Opinions and beliefs regarding AI's impact on education.",
                                                style={"margin": "0", "color": "#1a1a1a", "fontSize": "1rem"},
                                            ),
                                        ],
                                    ),

                                    # Training
                                    html.Div(
                                        style={
                                            "background": "linear-gradient(to bottom, #fef9c3, #fef08a)",
                                            "borderRadius": "12px",
                                            "padding": "20px",
                                            "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                                            "cursor": "default",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "justifyContent": "center",
                                            "textAlign": "center",
                                        },
                                        children=[
                                            html.H2(
                                                "Training",
                                                style={
                                                    "color": "#b45309",
                                                    "fontWeight": "700",
                                                    "fontSize": "1.3rem",
                                                    "marginBottom": "10px",
                                                },
                                            ),
                                            html.P(
                                                "Self-assessment and suggestions for AI-related professional development.",
                                                style={"margin": "0", "color": "#1a1a1a", "fontSize": "1rem"},
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            width=6,
                        ),

                        # RIGHT COLUMN - Explanation Text
                        dbc.Col(
                            dbc.CardBody(
                                [
                                    html.H4(
                                        "From Survey to Insight: Turning Data into Meaning",
                                        style={
                                            "fontSize": "1.8rem",
                                            "fontWeight": "600",
                                            "color": "#1A1A1A",
                                            "fontFamily": "'Segoe UI', 'Helvetica Neue', sans-serif",
                                            "letterSpacing": "0.5px",
                                            "marginBottom": "15px",
                                            "textAlign": "left",
                                            "borderLeft": "4px solid #636EFA",
                                            "paddingLeft": "10px",
                                        },
                                    ),
                                    html.P(
                                        [
                                            "The survey conducted with faculty members provides a structured way of capturing ",
                                            html.Strong("how educators understand, use, and perceive AI"),
                                            " while also assessing their needs for further training. ",
                                            html.Br(),
                                            html.Br(),
                                            "Responses are transformed into ",
                                            html.Strong("numerical values"),
                                            " and aggregated into the four key dimensions. This allows us to move from raw answers to ",
                                            html.Strong("comparable scores"),
                                            " across faculties and categories. ",
                                            html.Br(),
                                            html.Br(),
                                            "Through this process, the data becomes ",
                                            html.Em("meaningful insight"),
                                            " — highlighting strengths, gaps, and opportunities. These results are then visualized in an ",
                                            html.Strong("interactive dashboard"),
                                            ", enabling exploration of differences between faculties, trends across dimensions, and the role of sociographic variables. ",
                                            html.Br(),
                                            html.Br(),
                                            "Ultimately, this approach helps transform scattered survey responses into a ",
                                            html.Strong("clear picture of AI adoption in higher education"),
                                            ", making it easier to support decision-making and strategy building.",
                                        ],
                                        className="text-justify",
                                        style={
                                            "fontSize": "1.05rem",
                                            "lineHeight": "1.7",
                                            "color": "#4A4A4A",
                                            "whiteSpace": "pre-line",
                                            "padding": "0 5px",
                                            "text-align": "justify",
                                            "padding-right":"70px"
                                        },
                                    ),
                                ]
                            ),
                            width=6,
                        ),
                    ]
                )
            ),
            style={
                "height": "100%",
                "boxShadow": "0 4px 10px rgba(0,0,0,0.05)",
                "borderRadius": "12px",
                "border": "1px solid #e5e7eb",
                "marginBottom": "30px",
            },
        ),
        dbc.Col([
            html.Div([
                dash_dangerously_set_inner_html.DangerouslySetInnerHTML(
                    "<ub-mapbox-dashboard></ub-mapbox-dashboard>"
                ),
            ])
        ]),

        # Sankeys Visualization for all faculties
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.H3("Distribution of the scores between faculties", className="text-center my-3", style={'font-size': "25px"}),
                    html.P("Click on any given node to expand the flow of each score.",
                           className="text-center lead"),
                    dcc.Graph(id='sankey-chart', config={'displayModeBar': False}, className="dash-graph")
                ], className="graph-container", id="sankey-chart-container"), width=12
            )
        ], justify="center"),

        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            # Title
                            html.H3(
                                "Size comparison",
                                id="map-title",
                                className="text-center my-3",
                                style={'font-size': '25px'}
                            ),

                            # Chart type toggle (Radio buttons)
                            dbc.Row(
                                dbc.Col(
                                    dcc.RadioItems(
                                        id="chart-type-toggle",
                                        options=[
                                            {"label": "Bubble Chart", "value": "bubble"},
                                            {"label": "Treemap", "value": "treemap"}
                                        ],
                                        value="treemap",
                                        inline=True,
                                        labelStyle={"margin-right": "20px", "padding-left": "8px"},
                                        className="mb-3"
                                    ),
                                    width=12
                                ),
                                className="justify-content-center"
                            ),

                            # Dropdown filters
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="gender-dropdown-b",
                                            options=[
                                                {"label": "Female", "value": "Female"},
                                                {"label": "Male", "value": "Male"},
                                                {"label": "Non-binary", "value": "Non-binary"},
                                                {"label": "No answer", "value": "No answer"}
                                            ],
                                            placeholder="Select gender",
                                            value=None,
                                            className="mb-2",
                                            style={"padding-left": "8px"}
                                        ),
                                        width=4
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="teaching-experience-dropdown-b",
                                            options=[
                                                {"label": "Less than 5 years", "value": "Less than 5"},
                                                {"label": "Between 5 and 10 years", "value": "Between 5 and 10"},
                                                {"label": "Between 11 and 20 years",
                                                 "value": "Between 11 and 20"},
                                                {"label": "More than 20 years", "value": "More than 20"}
                                            ],
                                            placeholder="Select teaching experience",
                                            value=None,
                                            className="mb-2"
                                        ),
                                        width=4
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="ub-profile-dropdown-b",
                                            options=[
                                                {"label": "Senior Lecturer", "value": "Senior Lecturer"},
                                                {"label": "Associate", "value": "Associate"},
                                                {"label": "Permanent Collaborator", "value": "Collab"},
                                                {"label": "Lecturer", "value": "Lecturer"},
                                                {"label": "PreDoc", "value": "PreDoc"},
                                                {"label": "PostDoc", "value": "PostDoc"},
                                                {"label": "Professor", "value": "Professor"}
                                            ],
                                            placeholder="Select profile",
                                            value=None,
                                            className="mb-2"
                                        ),
                                        width=4
                                    ),
                                ],
                                className="mb-3"
                            ),

                            # Treemap visualization
                            dcc.Graph(
                                id="text-map",
                                config={"displayModeBar": False},
                                className="dash-graph"
                            ),

                            # Navigation buttons
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Button(
                                            html.I(className="fa fa-arrow-left"),  # Font Awesome left arrow
                                            id="btn-left",
                                            disabled=True,
                                            className="btn btn-secondary rounded-circle px-3 py-2",
                                        ),
                                        width="auto"
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            html.I(className="fa fa-arrow-right"),  # Font Awesome right arrow
                                            id="btn-right",
                                            className="btn btn-primary rounded-circle px-3 py-2",
                                        ),
                                        width="auto"
                                    ),
                                ],
                                id="nav-buttons-row",
                                className="justify-content-center my-3"
                            )
                        ],
                        className="graph-container"
                    ),
                    width=8  # Left column with graph occupies 70% space
                ),

                # Right column with text block
                # Right column with explanation
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4(
                                        "Breaking AI Apart",
                                        style={
                                            "fontSize": "1.8rem",
                                            "fontWeight": "600",
                                            "color": "#1A1A1A",
                                            "fontFamily": "'Segoe UI', 'Helvetica Neue', sans-serif",
                                            "letterSpacing": "0.5px",
                                            "marginBottom": "15px",
                                            "textAlign": "left",
                                            "borderLeft": "4px solid #636EFA",  # subtle accent line
                                            "paddingLeft": "10px"
                                        }
                                    ),
                                    html.P(
                                        [
                                            "Dividing AI integration into ",
                                            html.Strong("four dimensions: "),
                                            html.Span("Knowledge", style={"color": "#b91c1c", "fontWeight": "bold"}),
                                            ", ",
                                            html.Span("Uses", style={"color": "#6b21a8", "fontWeight": "bold"}),
                                            ", ",
                                            html.Span("Perceptions", style={"color": "#15803d", "fontWeight": "bold"}),
                                            ", and ",
                                            html.Span("Training", style={"color": "#b45309", "fontWeight": "bold"}),
                                            " provides a ",
                                            html.Strong("clearer and more strategic perspective"),
                                            " on how educators engage with emerging technologies. ",
                                            "Instead of relying on a single overall score that can obscure critical nuances, this multidimensional view ",
                                            ", exposes hidden gaps, and ",
                                            html.Strong("pinpoints where interventions will have the greatest impact"),
                                            ". ",
                                            html.Br(),
                                            html.Br(),
                                            "By analyzing these dimensions independently, we can ",
                                            html.Strong(
                                                "design policies and support systems that respond to real needs"),
                                            " — whether that means strengthening ",
                                            html.Em("conceptual understanding"),
                                            ", improving ",
                                            html.Em("practical application"),
                                            ", or addressing ",
                                            html.Em("training priorities"),
                                            ". ",
                                            html.Br(),
                                            html.Br(),
                                            "The result is a more ",
                                            html.Strong("targeted, equitable, and effective approach"),
                                            " to fostering meaningful AI adoption in higher education.",
                                        ],
                                        className="text-justify",
                                        style={
                                            "fontSize": "1.05rem",
                                            "lineHeight": "1.7",
                                            "color": "#4A4A4A",
                                            "whiteSpace": "pre-line",
                                            "padding": "0 5px",
                                            "padding-right": "35px",
                                            "text-align": "justify",
                                        },
                                    )

                                ]
                            )
                        ],
                        className="shadow-sm border-0",
                        style={
                            "borderRadius": "20px",
                            "backgroundColor": "#F9FAFB",
                            "padding": "20px",
                            "margin-top": "20px",
                            "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.05)"
                        }
                    ),
                    width=4
                )
            ],
            justify="center",
            className="d-flex align-items-stretch"
        ),
        html.Div([
            dash_dangerously_set_inner_html.DangerouslySetInnerHTML(
                "<ub-faculty-selector></ub-faculty-selector>"
            ),
            ])
        ])
