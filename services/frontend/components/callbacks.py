from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import pydeck as pdk


from utils.data_fetcher import get_latest_ia_usages, get_all_historical_data


def register_callbacks(app):
    # Update spike map based on the latest IA usage percentages (scattermapbox)
    @app.callback(
        Output('spike-map', 'children'),  # Output now targets children of a container (e.g., Div)
        Input('interval-component', 'n_intervals')
    )
    def update_spike_map(_):
        data = get_latest_ia_usages()
        df = pd.DataFrame(data)

        if not df.empty and 'latitude' in df.columns and 'longitude' in df.columns:
            # Pydeck setup
            latitude = 41.3851,
            longitude = 2.1734,
            zoom = 14,
            view_state = pdk.ViewState(
                latitude=41.381294,
                longitude=2.167793,
                zoom=13.53,
                pitch=48.06,
                bearing=-12.81
            )

            spike_layer = pdk.Layer(
                "ColumnLayer",
                data=df,
                get_position=["longitude", "latitude"],
                get_elevation="usage_percentage*1.1",  # Scale spike height
                elevation_scale=10,
                radius=120,
                get_fill_color="[usage_percentage * 2, 100, 200]",
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
                map_style="mapbox://styles/mapbox/satellite-streets-v12",
                tooltip={"text": "{faculty}: {usage_percentage}%"},
                api_keys={"mapbox": "pk.eyJ1IjoibWFudS11YiIsImEiOiJjbTN0M2E4bDcwNTdjMmxzZjUxZzEwd3YwIn0.nP8eJ0etV09R51KoBC47FA"}  # Add your token here
            )

            # Save to an HTML file
            output_path = "assets/pydeck_spike_map.html"
            r.to_html(output_path)

            # Return the Iframe component to display the map
            return html.Iframe(
                src=f"/{output_path}",
                style={"width": "100%", "height": "600px", "border": "none"}
            )

        # Default case for no data
        return html.Div("No Data Available for Spike Map", style={"text-align": "center", "color": "red"})

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