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
                        'max-width': '60%',  # Prevent the text container from growing too large
                        'padding-right': '0px',
                        'padding-left': '4px',
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
                            className='text-dark display-1 fw-bold lh-tight',
                            style={
                                'max-width': '942.13px'
                            }
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
                                id="lets-explore-btn",
                                className='btn btn-primary rounded px-4 py-3 fw-bold',
                                style={
                                    'background-color': '#6ea8fe',
                                    'color': '#f7f7f7',
                                    'border': 'none',
                                    'cursor': 'pointer',
                                }
                            )
                        ),
                        html.P(
                            [
                                "Already exploring AI? ",
                                html.A(
                                    "Sign In",
                                    href="#",
                                    id="open-auth-signin",  # <-- add id
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
        # Card with 2x2 grid (left) + "Turning Data into Meaning" (right)
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
                            className="full-below-620",  # <-- NEW
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
                                            "padding-right": "70px",
                                        },
                                    ),
                                ]
                            ),
                            width=6,
                            style={
                                'max-width': '1040px'
                            },
                            className="hide-below-620",  # <-- NEW
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
            html.Div(
                id="mapbox-section",
                children=[
                    dash_dangerously_set_inner_html.DangerouslySetInnerHTML(
                        "<ub-mapbox-dashboard></ub-mapbox-dashboard>"
                    ),
                ],
                style={
                    # just to be nice to scrollIntoView with sticky headers
                    "scrollMarginTop": "80px",
                }
            )
        ]),

        # Sankeys Visualization for all faculties (RESTYLED)
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            html.Div(
                                                [
                                                    html.H3(
                                                        "Distribution of the scores between faculties",
                                                        className="mb-0",
                                                        style={"fontWeight": 600, "fontSize": "22px"},
                                                    ),
                                                    html.Small(
                                                        "Click any node to expand its score flow.",
                                                        className="text-muted",
                                                    ),
                                                ]
                                            ),
                                            className="align-self-center",
                                        ),
                                    ],
                                    className="g-2 align-items-center",
                                ),
                                className="bg-white",
                                style={"borderBottom": "0px solid #e5e7eb", 'margin-top': '10px'},
                            ),
                            dbc.CardBody(
                                dcc.Loading(
                                    dcc.Graph(
                                        id="sankey-chart",
                                        config={"displayModeBar": False},
                                        className="dash-graph",
                                        style={"height": "600px"}  # good balance for Sankey readability
                                    ),
                                    type="circle",
                                    color="#636EFA",
                                ),
                                className="p-3 p-md-4",
                            ),
                        ],
                        className="shadow-sm border-0",
                        style={"border-radius": "16px", "backgroundColor": "#FFFFFF"},
                    ),
                    width=12,
                )
            ],
            justify="center",
            className="my-2",
        )
        ,

        dbc.Row(
            [
                # LEFT: Treemap / filters / nav
                dbc.Col(
                    dbc.Card(
                        [
                            # Header inside the card
                            dbc.CardHeader(
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            html.H3(
                                                "Size comparison",
                                                id="map-title",
                                                className="mb-0",
                                                style={"fontWeight": 600, "fontSize": "22px"},
                                            ),
                                            xs=12,
                                            md="auto",
                                            className="align-self-center",
                                        ),
                                        dbc.Col(
                                            dcc.RadioItems(
                                                id="chart-type-toggle",
                                                options=[
                                                    {"label": "Bubble Chart", "value": "bubble"},
                                                    {"label": "Treemap", "value": "treemap"},
                                                ],
                                                value="treemap",
                                                inline=True,
                                                labelStyle={
                                                    "marginRight": "10px",
                                                    "padding": "6px 12px",
                                                    "borderRadius": "9999px",
                                                    "background": "#F3F4F6",
                                                    "border": "1px solid #E5E7EB",
                                                    "cursor": "pointer",
                                                    "fontWeight": 500,
                                                },
                                                className="ms-md-auto mt-2 mt-md-0",
                                            ),
                                            xs=12,
                                            md=True,
                                        ),
                                    ],
                                    className="g-2 align-items-center justify-content-between",
                                ),
                                className="bg-white",
                                style={
                                    "borderBottom": "0px solid #e5e7eb",
                                    "marginTop": "10px",
                                },
                            ),

                            # Body with filters, graph, nav
                            dbc.CardBody(
                                [
                                    # filter strip
                                    html.Div(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        html.Div(
                                                            [
                                                                html.Small(
                                                                    "Gender",
                                                                    className="text-muted d-block mb-1",
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="gender-dropdown-b",
                                                                    options=[
                                                                        {"label": "Female", "value": "Female"},
                                                                        {"label": "Male", "value": "Male"},
                                                                        {"label": "Non-binary", "value": "Non-binary"},
                                                                        {"label": "No answer", "value": "No answer"},
                                                                    ],
                                                                    placeholder="All genders",
                                                                    value=None,
                                                                    clearable=True,
                                                                    persistence=True,
                                                                    className="mb-0",
                                                                ),
                                                            ]
                                                        ),
                                                        md=4,
                                                        xs=12,
                                                    ),
                                                    dbc.Col(
                                                        html.Div(
                                                            [
                                                                html.Small(
                                                                    "Teaching experience",
                                                                    className="text-muted d-block mb-1",
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="teaching-experience-dropdown-b",
                                                                    options=[
                                                                        {
                                                                            "label": "Less than 5 years",
                                                                            "value": "Less than 5",
                                                                        },
                                                                        {
                                                                            "label": "Between 5 and 10 years",
                                                                            "value": "Between 5 and 10",
                                                                        },
                                                                        {
                                                                            "label": "Between 11 and 20 years",
                                                                            "value": "Between 11 and 20",
                                                                        },
                                                                        {
                                                                            "label": "More than 20 years",
                                                                            "value": "More than 20",
                                                                        },
                                                                    ],
                                                                    placeholder="All experience",
                                                                    value=None,
                                                                    clearable=True,
                                                                    persistence=True,
                                                                    className="mb-0",
                                                                ),
                                                            ]
                                                        ),
                                                        md=4,
                                                        xs=12,
                                                    ),
                                                    dbc.Col(
                                                        html.Div(
                                                            [
                                                                html.Small(
                                                                    "Profile",
                                                                    className="text-muted d-block mb-1",
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="ub-profile-dropdown-b",
                                                                    options=[
                                                                        {
                                                                            "label": "Senior Lecturer",
                                                                            "value": "Senior Lecturer",
                                                                        },
                                                                        {"label": "Associate", "value": "Associate"},
                                                                        {
                                                                            "label": "Permanent Collaborator",
                                                                            "value": "Collab",
                                                                        },
                                                                        {"label": "Lecturer", "value": "Lecturer"},
                                                                        {"label": "PreDoc", "value": "PreDoc"},
                                                                        {"label": "PostDoc", "value": "PostDoc"},
                                                                        {"label": "Professor", "value": "Professor"},
                                                                    ],
                                                                    placeholder="All profiles",
                                                                    value=None,
                                                                    clearable=True,
                                                                    persistence=True,
                                                                    className="mb-0",
                                                                ),
                                                            ]
                                                        ),
                                                        md=4,
                                                        xs=12,
                                                    ),
                                                ],
                                                className="g-2",
                                            ),
                                        ],
                                        style={
                                            "backgroundColor": "#F8FAFC",
                                            "border": "1px solid #E5E7EB",
                                            "borderRadius": "12px",
                                            "padding": "10px 12px",
                                            "marginBottom": "12px",
                                        },
                                        className="mb-2",
                                    ),

                                    # main chart (treemap / bubble)
                                    dcc.Loading(
                                        dcc.Graph(
                                            id="text-map",
                                            config={"displayModeBar": False},
                                            className="dash-graph",
                                            style={"height": "640px"},
                                        ),
                                        type="circle",
                                        color="#636EFA",
                                    ),

                                    # nav arrows
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Button(
                                                    html.I(className="fa fa-arrow-left"),
                                                    id="btn-left",
                                                    disabled=True,
                                                    color="secondary",
                                                    className="rounded-circle px-3 py-2",
                                                ),
                                                width="auto",
                                            ),
                                            dbc.Col(
                                                dbc.Button(
                                                    html.I(className="fa fa-arrow-right"),
                                                    id="btn-right",
                                                    color="primary",
                                                    className="rounded-circle px-3 py-2",
                                                ),
                                                width="auto",
                                            ),
                                        ],
                                        id="nav-buttons-row",
                                        className="justify-content-center mt-2",
                                    ),
                                ],
                                className="p-3 p-md-4",
                            ),
                        ],
                        className="shadow-sm border-0",
                        style={
                            "borderRadius": "16px",
                            "backgroundColor": "#FFFFFF",
                            "marginTop": "19px",
                        },
                    ),

                    # below 1240px: this col takes full width
                    # >= xl breakpoint: this col becomes 8/12
                    width=12,
                    xl=8,

                    className="mb-3 mb-xl-0",
                ),

                # RIGHT: sticky explainer card
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
                                            "borderLeft": "4px solid #636EFA",
                                            "paddingLeft": "10px",
                                        },
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
                                            html.Br(), html.Br(),
                                            "By analyzing these dimensions independently, we can ",
                                            html.Strong(
                                                "design policies and support systems that respond to real needs"
                                            ),
                                            " — whether that means strengthening ",
                                            html.Em("conceptual understanding"),
                                            ", improving ",
                                            html.Em("practical application"),
                                            ", or addressing ",
                                            html.Em("training priorities"),
                                            ". ",
                                            html.Br(), html.Br(),
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
                                            "paddingRight": "35px",
                                            "textAlign": "justify",
                                        },
                                    ),
                                ]
                            )
                        ],
                        className="shadow-sm border-0",
                        style={
                            "borderRadius": "20px",
                            "backgroundColor": "#F9FAFB",
                            "padding": "20px",
                            "marginTop": "20px",
                            "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.05)",
                            "position": "sticky",
                            "top": "84px",
                        },
                    ),


                    # below 1240px: doesn't matter because we hide it with CSS
                    # >= xl breakpoint (>=1200px): this col is 4/12
                    width=12,
                    xl=4,

                    # custom class that hides/shows the column at 1240px breakpoint
                    className="break-ai-col",
                ),
            ],

            # keep them in the same row and same height so sticky works
            justify="center",
            className="d-flex align-items-stretch g-3",
        )

        ,
        html.Div(
            id="faculty-visualization",
            children=[
                dash_dangerously_set_inner_html.DangerouslySetInnerHTML(
                    "<ub-faculty-selector></ub-faculty-selector>"
                ),
                # If/when you mount <FacultyVisualization /> from React (or render its web component),
                # do it in here too so scrolling lands on the whole block.
                # dash_dangerously_set_inner_html.DangerouslySetInnerHTML(
                #     "<ub-faculty-visualization></ub-faculty-visualization>"
                # ),
            ],
            style={
                # helps scrollIntoView land cleanly below sticky headers
                "scrollMarginTop": "100px",
                # optional: a tiny top margin, so it's visually separate
                "marginTop": "40px",
            },
        )

    ])
