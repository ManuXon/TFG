from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import pydeck as pdk
import dash_deck
import circlify


from utils.data_fetcher import get_spike_map_data, get_sankey_chart_data, get_treemap_data

# Store current bar graph pagination index
pagination_index = 0
current_index_map = 0


def register_callbacks(app):
    # Update spike map based on the latest IA usage percentages (scattermapbox)
    @app.callback(
        Output("spike-map", "children"),
        [Input("category-dropdown", "value"),
         Input("gender-dropdown", "value"),
         Input("teaching-experience-dropdown", "value"),
         Input("ub-profile-dropdown", "value")]
    )
    def update_spike_map(category, gender, teaching_experience, ub_profile):
        data = get_spike_map_data(category, gender, teaching_experience, ub_profile)

        if data.empty:
            return html.P("No data available for the selected filters.", className="text-center")

        view_state = pdk.ViewState(
            latitude=41.381294,
            longitude=2.167793,
            zoom=13.53,
            pitch=48.06,
            bearing=-12.81
        )

        spike_layer = pdk.Layer(
            "ColumnLayer",
            data=data,
            get_position=["longitude", "latitude"],
            get_elevation="category_score*1.1",  # Scale spike height
            elevation_scale=10,
            radius=60,
            get_fill_color="color_rgb",
            pickable=True,
            auto_highlight=True
        )
        """
        building_layer = pdk.Layer(
        "MapboxLayer",
            id="3d-buildings",  # Unique layer ID
            type="fill-extrusion",  # Specifies a 3D layer
            data=None,  # Use Mapbox's built-in source
            get_fill_color=[200, 200, 200, 255],  # Light gray color with full opacity
            get_elevation="height",  # Use Mapbox's `height` property for building height
            elevation_scale=1,  # Scale factor for height
            extruded=True,  # Enables 3D extrusio
        )
        """

        r = pdk.Deck(
            layers=[spike_layer],
            initial_view_state=view_state,
            map_provider='mapbox',
            map_style="mapbox://styles/mapbox/outdoors-v12",
            tooltip={"text": "{faculty_name}: {category_score}"},
            api_keys={
                "mapbox": "pk.eyJ1IjoibWFudS11YiIsImEiOiJjbTN0M2E4bDcwNTdjMmxzZjUxZzEwd3YwIn0.nP8eJ0etV09R51KoBC47FA"}
            # Add your token here
        )

        # Return the Dash Deck component
        # Remember to make apikey as os.env
        return dash_deck.DeckGL(r.to_json(), id="deck-map",
                                mapboxKey="pk.eyJ1IjoibWFudS11YiIsImEiOiJjbTN0M2E4bDcwNTdjMmxzZjUxZzEwd3YwIn0.nP8eJ0etV09R51KoBC47FA",
                                style={"width": "100%", "height": "700px"})

    @app.callback(
        Output("map-legend", "children"),
        [Input("category-dropdown", "value"),
         Input("gender-dropdown", "value"),
         Input("teaching-experience-dropdown", "value"),
         Input("ub-profile-dropdown", "value")]
    )
    def update_map_legend(category, gender, teaching_experience, ub_profile):
        data = get_spike_map_data(category, gender, teaching_experience, ub_profile)

        if data.empty:
            return html.P("No data available for the selected filters.", className="text-center")

        # Sort faculties by their score and take the top 5
        top_faculties = data.sort_values(by="category_score", ascending=False).head(10)

        # Create legend items for the top 5 faculties
        legend_items = []
        for _, row in top_faculties.iterrows():
            legend_items.append(
                html.Div([
                    # Color square
                    html.Div(style={
                        "backgroundColor": row["color"],
                        "width": "15px",
                        "height": "15px",
                        "display": "inline-block",
                        "marginRight": "10px"
                    }),
                    # Faculty name and score
                    html.Span(f"{row['short_name']} ({row['category_score']:.2f})", className="legend-text")
                ], className="legend-item")
            )

        return html.Div(
            [
                html.H4("Selected faculties 10/10", className="legend-title"),
                html.Div(legend_items, className="legend-content", style={'height':'450px', 'max-height':'450px', 'justify-content':'start', 'display': 'grid', 'justify-items':'start' }),
            ]
        )

    # Update bar graph based on the current pagination index
    # Callback to update the bar graph and manage pagination buttons
    @app.callback(
        [
            Output("bar-graph", "figure"),  # Update the graph
            Output("prev-button", "disabled"),  # Disable "Prev" button when on the first page
            Output("next-button", "disabled"),  # Disable "Next" button when on the last page
        ],
        [
            Input("prev-button", "n_clicks"),
            Input("next-button", "n_clicks"),
            Input("category-dropdown", "value"),
            Input("gender-dropdown", "value"),
            Input("teaching-experience-dropdown", "value"),
            Input("ub-profile-dropdown", "value"),
        ]
    )
    def update_bar_graph(prev_clicks, next_clicks, category, gender, teaching_experience, ub_profile):
        global pagination_index
        ctx = dash.callback_context

        # Fetch data and sort
        data = get_spike_map_data(category, gender, teaching_experience, ub_profile)
        if data.empty:
            return px.bar(), True, True

        # Calculate the maximum pagination index
        max_index = max((len(data) - 1) // 6, 0)

        # Adjust pagination based on button clicks
        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "prev-button" and pagination_index > 0:
                pagination_index -= 1
            elif button_id == "next-button" and pagination_index < max_index:
                pagination_index += 1

        # Paginate the top faculties
        start_idx = pagination_index * 6
        end_idx = start_idx + 6
        paginated_faculties = data.sort_values(by="category_score", ascending=False).iloc[start_idx:end_idx]

        # Create bar graph
        fig = px.bar(
            paginated_faculties,
            x="category_score",
            y="short_name",
            orientation="h",
            text="category_score",
        )

        # Apply custom colors
        fig.update_traces(
            marker_color=paginated_faculties["color"],
            marker_line_width=1,
            texttemplate="%{text:.2f}",
            textposition="outside",
        )

        # Update layout
        fig.update_layout(
            xaxis_title="Score",
            yaxis_title="Faculties",
            xaxis=dict(range=[1, 10], title="Score"),
            yaxis=dict(title="Faculty", autorange="reversed"),
            plot_bgcolor="white",
            height=250,
        )

        # Disable buttons based on pagination index
        disable_prev = pagination_index == 0
        disable_next = pagination_index == max_index

        return fig, disable_prev, disable_next

    # Define the Sankey chart creation logic
    def create_sankey_chart(clicked_node=None):
        data = get_sankey_chart_data()

        # Generate colors for all layers
        node_colors = []
        for label in data["labels"]:
            if label in data["faculty_colors"]:
                node_colors.append(data["faculty_colors"][label])  # Faculty colors
            else:
                if label in ["Knowledge", "Uses", "Perceptions", "Training Needs"]:
                    layer_colors = {
                        "Knowledge": "#fecaca",
                        "Uses": "#e9d5ff",
                        "Perceptions": "#bbf7d0",
                        "Training Needs": "#fef08a",
                    }
                    node_colors.append(layer_colors[label])
                elif label in ["Gender", "Teaching Experience", "UB Profile"]:
                    layer_colors = {
                        "Gender": "#FCB8F7",
                        "Teaching Experience": "#5CEE58",
                        "UB Profile": "#4b95f9",
                    }
                    node_colors.append(layer_colors[label])
                elif label in ["Female", "Male", "Non-binary", "No answer"]:
                    layer_colors = {
                        "Female": "#FCB8F7",
                        "Male": "#FCB8F7",
                        "Non-binary": "#FCB8F7",
                        "No answer": "#FCB8F7",
                    }
                    node_colors.append(layer_colors[label])
                elif label in ["Less than 5", "Between 5 and 10", "Between 11 and 20",
                               "More than 20"]:
                    layer_colors = {
                        "Less than 5": "#5CEE58",
                        "Between 5 and 10": "#5CEE58",
                        "Between 11 and 20": "#5CEE58",
                        "More than 20": "#5CEE58",
                    }
                    node_colors.append(layer_colors[label])
                elif label in ["Senior Lecturer", "Associate", "PreDoc", "PostDoc",
                               "Collab", "Lecturer", "Professor"]:
                    layer_colors = {
                        "Senior Lecturer": "#4b95f9",
                        "Associate": "#4b95f9",
                        "PreDoc": "#4b95f9",
                        "PostDoc": "#4b95f9",
                        "Collab": "#4b95f9",
                        "Lecturer": "#4b95f9",
                        "Professor": "#4b95f9",
                    }
                    node_colors.append(layer_colors[label])
                else:
                    node_colors.append("#008000")  # Fallback color
        # Filter nodes and links if a node is clicked
        if clicked_node is not None:
            related_links = [
                i for i, (source, target) in enumerate(zip(data["sources"], data["targets"]))
                if source == clicked_node or target == clicked_node
            ]
            filtered_sources = [data["sources"][i] for i in related_links]
            filtered_targets = [data["targets"][i] for i in related_links]
            filtered_values = [data["values"][i] for i in related_links]

            # Identify related nodes
            related_nodes = set(filtered_sources + filtered_targets)
            filtered_labels = [label if i in related_nodes else "" for i, label in enumerate(data["labels"])]
            filtered_colors = [node_colors[i] if i in related_nodes else "rgba(255, 255, 255, 0)"
                               for i in range(len(data["labels"]))]
        else:
            filtered_sources = data["sources"]
            filtered_targets = data["targets"]
            filtered_values = data["values"]
            filtered_labels = data["labels"]
            filtered_colors = node_colors

        # Generate link colors dynamically based on the filtered target node's color
        link_colors = [
            f"rgba({int(filtered_colors[target][1:3], 16)}, {int(filtered_colors[target][3:5], 16)}, {int(filtered_colors[target][5:7], 16)}, 0.5)"
            if filtered_colors[target].startswith("#")
            else "rgba(128, 128, 128, 0.5)"  # Fallback color for undefined targets
            for target in filtered_targets
        ]

        # Create Sankey chart
        fig = go.Figure(data=[go.Sankey(
            arrangement="fixed",  # Fix node positions to enable click events
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=filtered_labels,
                color=filtered_colors
            ),
            link=dict(
                source=filtered_sources,
                target=filtered_targets,
                value=filtered_values,
                color=link_colors
            )
        )])

        # Add interactivity for node selection
        fig.update_layout(
            title_text="Interactive Sankey Diagram",
            font_size=10,
            height=800,
            margin=dict(l=50, r=50, t=50, b=50),
            clickmode="event+select"
        )

        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=False,
                    buttons=[
                        dict(
                            label="Reset View",
                            method="update",
                            args=[{
                                "node.label": [data["labels"]],
                                "node.color": [node_colors],
                                "link.source": [data["sources"]],
                                "link.target": [data["targets"]],
                                "link.value": [data["values"]],
                                "link.color": [[
                                    f"rgba({int(node_colors[target][1:3], 16)}, "
                                    f"{int(node_colors[target][3:5], 16)}, "
                                    f"{int(node_colors[target][5:7], 16)}, 0.5)"
                                    for target in data["targets"]
                                ]]
                            }]
                        )
                    ]
                )
            ]
        )

        return fig

    # Dash callbacks
    @app.callback(
        Output("sankey-chart", "figure"),
        Input("sankey-chart", "clickData"),
    )
    def update_chart_on_click(click_data):
        if click_data:
            # Extract pointNumber for identification
            point_number = click_data["points"][0].get("pointNumber")
            return create_sankey_chart(point_number)

        return create_sankey_chart()

    @app.callback(
        [
            Output("text-map", "figure"),
            Output("map-title", "children"),
            Output("btn-left", "disabled"),
            Output("btn-right", "disabled"),
            Output("nav-buttons-row", "style"),
        ],
        [
            Input("chart-type-toggle", "value"),
            Input("gender-dropdown-b", "value"),
            Input("teaching-experience-dropdown-b", "value"),
            Input("ub-profile-dropdown-b", "value"),
            Input("btn-left", "n_clicks"),
            Input("btn-right", "n_clicks"),
        ]
    )
    def update_bubble_treemap(
            chart_type, gender, teaching_experience, ub_profile, left_clicks, right_clicks
    ):
        ctx = dash.callback_context
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        if chart_type == "bubble":
            # Bubble chart logic
            global current_index_map
            score_categories = [
                ("Faculties, sized by their scores", "All"),
                ("Faculties, sized by IA knowledge", "knowledge"),
                ("Faculties, sized by IA uses", "uses"),
                ("Faculties, sized by IA perceptions", "perceptions"),
                ("Faculties, sized by IA Training", "training"),
            ]

            # Determine which button was clicked
            if triggered_id == "btn-right":
                current_index_map = min(current_index_map + 1, len(score_categories) - 1)
            elif triggered_id == "btn-left":
                current_index_map = max(current_index_map - 1, 0)
            else:
                current_index_map = 0

            title, category = score_categories[current_index_map]

            # Fetch data for bubble chart
            grouped = get_spike_map_data(
                category=category,
                gender=gender,
                ub_profile=ub_profile,
                teaching_experience=teaching_experience,
            )

            grouped = grouped.sort_values(by="category_score", ascending=True).reset_index(drop=True)

            # Generate bubble chart data
            circle_data = circlify.circlify(
                grouped["category_score"].tolist(),
                show_enclosure=False,
            )

            circles = [
                {
                    "x": circle.x,
                    "y": circle.y,
                    "r": circle.r,
                    "faculty_name": grouped.loc[i, "faculty_name"],
                    "short_name": grouped.loc[i, "short_name"],
                    "color": grouped.loc[i, "color"],
                    "category_score": grouped.loc[i, "category_score"],
                }
                for i, circle in enumerate(circle_data)
            ]

            # Create the bubble chart figure
            fig = go.Figure()
            for circle in circles:
                fig.add_shape(
                    type="circle",
                    xref="x",
                    yref="y",
                    x0=circle["x"] - circle["r"],
                    y0=circle["y"] - circle["r"],
                    x1=circle["x"] + circle["r"],
                    y1=circle["y"] + circle["r"],
                    line=dict(color=circle["color"], width=2),
                    fillcolor=circle["color"],
                    label=dict(text=f"{circle['short_name']}", font=dict(color="white", size=13)),
                )
                fig.add_trace(
                    go.Scatter(
                        x=[circle["x"]],
                        y=[circle["y"]],
                        mode="markers",
                        marker=dict(size=10, color=circle["color"], symbol="circle"),
                        name=circle["short_name"],
                        hoverinfo="text",
                        hovertext=f'{circle["short_name"]}: {circle["category_score"]}',
                        showlegend=True,
                    )
                )

            fig.update_layout(
                xaxis=dict(range=[-1.15, 1.15], showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(range=[-1.15, 1.15], showgrid=False, zeroline=False, showticklabels=False),
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=True,
            )

            disable_left = current_index_map == 0
            disable_right = current_index_map == len(score_categories) - 1
            nav_style = {"display": "flex"}

        else:
            # Treemap logic
            title = "Treemap: Sizing faculties"
            data = get_treemap_data(gender, teaching_experience, ub_profile)

            # Define colors for dimensions
            dimension_colors = {
                "Knowledge": "#fecaca",  # Red
                "Uses": "#e9d5ff",
                "Perceptions": "#bbf7d0",
                "Training": "#fef08a",
            }

            # Create treemap
            fig = px.treemap(
                data,
                path=["parent", "label"],  # Specify hierarchy: Overall -> Faculty -> Dimension
                values="value",
                color='overall_faculty_score',  # Use "color" column to differentiate faculty and dimension colors
            )

            # Apply custom color mapping
            fig.for_each_trace(
                lambda t: t.update(
                    marker_colors=[
                        dimension_colors[id.split("/")[1]] if len(id.split("/")) == 2 else c
                        for c, id in zip(t.marker.colors, t.ids)
                    ]
                )
            )

            # Update hover and traces
            fig.update_traces(
                marker=dict(line=dict(width=1, color="black")),
                hovertemplate="<b>%{label}</b><br>Score: %{value}<extra></extra>",
            )

            # Change legend title
            fig.update_layout(
                coloraxis_colorbar=dict(
                    title="Faculty Score"  # Set the legend title
                )
            )

            disable_left = True
            disable_right = True
            nav_style = {"display": "none"}

        return fig, title, disable_left, disable_right, nav_style


"""
    # Update 3D scatter map based on latest IA usage percentages
    @app.callback(
        Output('scatter3d', 'figure'),
        Input('interval-component', 'n_intervals')
    )
    def update_scatter3d(_):
        data = get_latest_ia_usages()
        df = pd.DataFrame(data)

        if not df.empty and 'latitude' in df.columns and 'longitude' in df.columns:
            fig = go.Figure(go.Scatter3d(
                x=df['longitude'],
                y=df['latitude'],
                z=df['usage_percentage'],
                mode='markers',
                marker=dict(
                    size=5,
                    color=df['usage_percentage'],
                    colorscale='viridis',
                    showscale=True
                ),
                hoverinfo='text',
                hovertext=df.apply(lambda row: f"{row['faculty']}: {row['usage_percentage']}%", axis=1)
            ))

            # Layout for 3D map representation
            fig.update_layout(
                scene=dict(
                    xaxis=dict(title='Longitude'),
                    yaxis=dict(title='Latitude'),
                    zaxis=dict(title='Usage %'),
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.5)
                    )
                ),
                margin={"r": 0, "t": 0, "l": 0, "b": 0}
            )
        else:
            fig = go.Figure()  # Return an empty figure if no data

        return fig

    @app.callback(
        Output('historical-graph', 'figure'),
        Input('interval-component', 'n_intervals')
    )
    def update_line_chart_race(_):
        history_data = get_all_historical_data()
        df = pd.DataFrame(history_data)

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.sort_values('date', inplace=True)

            # Create the line chart with a slider and animation
            fig = px.line(
                df, x='date', y='usage_percentage', color='faculty',
                labels={'usage_percentage': 'IA Usage %', 'date': 'Date'},
                animation_frame='date', animation_group='faculty'  # Enables the time-based animation
            )

            fig.update_layout(
                title="AI Adoption Over Time",
                xaxis_title='Date',
                yaxis_title='IA Usage Percentage',
                legend_title_text='Faculty',
                yaxis=dict(range=[0, df['usage_percentage'].max() + 10]),
                transition={'duration': 500}
            )

            fig.update_traces(mode='lines+markers')  # Display markers and lines together
        else:
            fig = px.scatter(title="No Historical Data Available")

        return fig

    # Update historical records for all faculties at once
    @app.callback(
        Output('historical-table', 'children'),
        Input('interval-component', 'n_intervals')  # Using an interval component to trigger updates
    )
    def update_historical_table(_):
        history_data = get_all_historical_data()
        if history_data.empty:
            return html.Div("No Historical Data Available")

        # Revisamos si todas las facultades están representadas
        df = pd.DataFrame(history_data)

        fig = px.bar(
            df,
            x='date',
            y='usage_percentage',
            color='faculty',
            barmode='group',  # Cambiar a 'stack' las barras apiladas
            title="Historical Data for All Faculties",
            labels={'usage_percentage': 'IA Usage Percentage', 'date': 'Date'}
        )

        fig.update_layout(
            xaxis={'title': 'Date'},
            yaxis={'title': 'IA Usage Percentage'},
            legend_title_text='Faculty',
            barmode='group'
        )

        return dcc.Graph(figure=fig)

    # Sunburst Chart
    @app.callback(
        Output('sunburst-graph', 'figure'),
        Input('interval-component', 'n_intervals')  # Using an interval component to trigger updates
    )
    def update_sunburst_visualization(_):
        data = get_latest_ia_usages()
        df = pd.DataFrame(data)

        if not df.empty:
            fig = px.sunburst(
                df, path=['faculty'], values='usage_percentage', title="AI Usage by Faculty",
                color='usage_percentage', color_continuous_scale='Blues', hover_data={'usage_percentage': True}
            )
            fig.update_layout(
                margin=dict(t=0, l=0, r=0, b=0),
                legend_title_text='Select Faculties',
                legend=dict(itemclick='toggleothers')  # Enables filtering by faculty
            )
            fig.update_traces(
                hovertemplate="<b>%{label}</b><br>Usage: %{value}%",
                selector=dict(type='sunburst')
            )
        else:
            fig = px.scatter(title="No Data Available")

        return fig
"""
