from dash import dcc, html, clientside_callback
from dash.dependencies import Input, Output, State, ClientsideFunction
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
                html.Div(legend_items, className="legend-content",
                         style={'height': '450px', 'max-height': '450px', 'justify-content': 'start', 'display': 'grid',
                                'justify-items': 'start'}),
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

    def create_sankey_chart(clicked_node=None):
        import plotly.graph_objects as go

        data = get_sankey_chart_data()
        labels = list(data["labels"])
        n = len(labels)

        # -------------------------
        # Column model (fixed x)
        # -------------------------
        SECTIONS = ["Knowledge", "Uses", "Perceptions", "Training Needs"]
        HEADERS = ["Gender", "UB Profile", "Teaching Experience"]

        GENDER = ["Female", "Male", "Non-binary", "No answer"]
        PROFILE = ["Senior Lecturer", "Associate", "PreDoc", "PostDoc", "Collab", "Lecturer", "Professor"]
        EXP = ["Less than 5", "Between 5 and 10", "Between 11 and 20", "More than 20"]

        # 0: sections, 1: headers, 2: filter values, 3: faculties
        def col_of(lab: str) -> int:
            if lab in SECTIONS:
                return 0
            if lab in HEADERS:
                return 1
            if lab in GENDER or lab in PROFILE or lab in EXP:
                return 2
            if lab in data.get("faculty_colors", {}):
                return 3
            return 1

        GROUP_ORDER = [
            ("Gender", GENDER),
            ("UB Profile", PROFILE),
            ("Teaching Experience", EXP),
        ]

        # -------------------------
        # Colors
        # -------------------------
        color = {}
        for lab in labels:
            if lab in data.get("faculty_colors", {}):
                color[lab] = data["faculty_colors"][lab]
            elif lab in SECTIONS:
                color[lab] = {
                    "Knowledge": "#fecaca", "Uses": "#e9d5ff",
                    "Perceptions": "#bbf7d0", "Training Needs": "#fef08a",
                }[lab]
            elif lab in HEADERS:
                color[lab] = {
                    "Gender": "#FCB8F7",
                    "UB Profile": "#4b95f9",
                    "Teaching Experience": "#5CEE58",
                }[lab]
            elif lab in GENDER:
                color[lab] = "#FCB8F7"
            elif lab in PROFILE:
                color[lab] = "#4b95f9"
            elif lab in EXP:
                color[lab] = "#5CEE58"
            else:
                color[lab] = "#008000"

        # -------------------------
        # Stable ordering by column (index remap)
        # -------------------------
        buckets = {0: [], 1: [], 2: [], 3: []}
        for i, lab in enumerate(labels):
            buckets[col_of(lab)].append(i)

        # headers fixed order
        order_head = {name: k for k, name in enumerate(HEADERS)}
        buckets[1].sort(key=lambda idx: order_head.get(labels[idx], 999))

        # filter values: grouped and ordered
        def key_val(idx):
            lab = labels[idx]
            for rank, (_g, vals) in enumerate(GROUP_ORDER):
                if lab in vals:
                    return (rank, vals.index(lab))
            return (999, str(lab))

        buckets[2].sort(key=key_val)

        # faculties alphabetical (reduces crossings)
        buckets[3].sort(key=lambda idx: labels[idx].lower())

        new_order = buckets[0] + buckets[1] + buckets[2] + buckets[3]
        new_idx = {old: new for new, old in enumerate(new_order)}
        old_idx = {new: old for old, new in new_idx.items()}

        # Remap links
        src = [new_idx[s] for s in data["sources"]]
        tgt = [new_idx[t] for t in data["targets"]]
        val = list(data["values"])

        # Final label + color arrays in remapped order
        labs = [labels[old_idx[i]] for i in range(n)]
        cols = [color[labs[i]] for i in range(n)]

        # -------------------------
        # Fixed positions (x) per column, y by EXPLICIT label order
        # (nodes stay as before)
        # -------------------------
        x_by_col = {0: 0.06, 1: 0.30, 2: 0.68, 3: 0.93}
        node_x = [0.0] * n
        node_y = [0.0] * n

        # map label -> index in FINAL labs
        label_to_idx = {lab: i for i, lab in enumerate(labs)}

        # ordered indices per column (this is the single source of truth)
        ordered_col_indices = {0: [], 1: [], 2: [], 3: []}

        # col 0: sections, SECTIONS order
        for lab in SECTIONS:
            i = label_to_idx.get(lab)
            if i is not None:
                ordered_col_indices[0].append(i)

        # col 1: headers, HEADERS order
        for lab in HEADERS:
            i = label_to_idx.get(lab)
            if i is not None:
                ordered_col_indices[1].append(i)

        # col 2: categorical filters, GROUP_ORDER order
        for _, vals in GROUP_ORDER:
            for lab in vals:
                i = label_to_idx.get(lab)
                if i is not None:
                    ordered_col_indices[2].append(i)

        # col 3: faculties, alphabetical
        fac_labs = sorted(
            [lab for lab in data.get("faculty_colors", {}).keys() if lab in label_to_idx]
        )
        for lab in fac_labs:
            ordered_col_indices[3].append(label_to_idx[lab])

        # any leftover labels that weren't picked up: append at their column's end
        used = set(i for col_idxs in ordered_col_indices.values() for i in col_idxs)
        for i in range(n):
            if i in used:
                continue
            c = col_of(labs[i])
            ordered_col_indices.setdefault(c, []).append(i)

        # now assign x,y using THESE explicit ordered lists (unchanged orientation)
        for c in (0, 1, 2, 3):
            idxs = ordered_col_indices.get(c, [])
            m = len(idxs)
            if m == 0:
                continue
            top, bot = 0.04, 0.96
            step = (bot - top) / (m + 1)
            for k, i in enumerate(idxs):
                node_x[i] = x_by_col[c]
                node_y[i] = top + step * (k + 1)

        # Extra gentle spread for faculties (avoid touching)
        fac_ids = ordered_col_indices.get(3, [])
        if len(fac_ids) > 1:
            factor = 1.08
            for i in fac_ids:
                y = node_y[i]
                node_y[i] = max(0.03, min(0.97, 0.5 + (y - 0.5) * factor))

        # -------------------------
        # Node/link hovers
        # -------------------------
        inflow = [0] * n
        outflow = [0] * n
        for s, t, v in zip(src, tgt, val):
            outflow[s] += v
            inflow[t] += v

        # Node tooltip: label + In + Out
        node_hover = [
            f"<b>{labs[i]}</b><br>"
            f"In: <b>{inflow[i]}</b><br>"
            f"Out: <b>{outflow[i]}</b>"
            f"<extra></extra>"
            for i in range(n)
        ]

        # Link tooltip: source → target + flow, using customdata
        link_customdata = [
            f"{labs[s]} → {labs[t]}"
            for s, t in zip(src, tgt)
        ]
        link_hover = (
            "<b>%{customdata}</b><br>"
            "Flow: <b>%{value}</b>"
            "<extra></extra>"
        )

        degree = [inflow[i] + outflow[i] for i in range(n)]

        # No default node text; everything via pills
        node_label_base = ["" for _ in range(n)]

        def rgba_from_hex(hx, a):
            hx = hx.lstrip("#")
            r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
            return f"rgba({r},{g},{b},{a})"

        vmax = max(val) if val else 1
        link_colors_default = [
            rgba_from_hex(cols[t], 0.30 + 0.50 * (v / vmax))
            for t, v in zip(tgt, val)
        ]

        # Click focus: dim unrelated
        alive_nodes = None
        if isinstance(clicked_node, int) and 0 <= clicked_node < n:
            rel_links = [i for i, (s, t) in enumerate(zip(src, tgt)) if s == clicked_node or t == clicked_node]
            alive_nodes = set()
            for i in rel_links:
                alive_nodes.add(src[i])
                alive_nodes.add(tgt[i])

            link_colors = [
                link_colors_default[i] if i in rel_links else "rgba(180,180,180,0.07)"
                for i in range(len(val))
            ]
            node_colors = [
                cols[i] if i in alive_nodes else "rgba(255,255,255,0)"
                for i in range(n)
            ]
            node_labels = [
                node_label_base[i] if i in alive_nodes else ""
                for i in range(n)
            ]
        else:
            link_colors = link_colors_default
            node_colors = cols
            node_labels = node_label_base

        # -------------------------
        # Pill annotations with faculty hack (shift -1 after biology)
        # -------------------------
        EPS = 0.006  # tiny spacing (~1–2px) between pills and nodes

        def build_annotations(visible_nodes=None):
            ann = []

            # Generic pill for non-faculty columns
            def add_pill_general(i, side: str):
                if visible_nodes is not None and i not in visible_nodes:
                    return

                # Sankey y: 0 = top, 1 = bottom
                # Paper y: 0 = bottom, 1 = top
                y_annot = 1.0 - node_y[i]

                if side == "left":
                    x = node_x[i] - EPS
                    xanchor = "right"
                else:
                    x = min(0.995, node_x[i] + EPS)
                    xanchor = "left"

                txt = labs[i] if degree[i] > 0 else ""

                ann.append(dict(
                    x=x, y=y_annot, xref="paper", yref="paper",
                    text=txt, showarrow=False,
                    xanchor=xanchor, yanchor="middle",
                    font=dict(size=10, color="#334155"),
                    bgcolor="rgba(255,255,255,1.0)",
                    bordercolor="rgba(0,0,0,0.18)", borderwidth=1
                ))

            # Col 0 (sections) → RIGHT of node
            for i in ordered_col_indices.get(0, []):
                add_pill_general(i, "right")

            # Col 1 (headers) → LEFT of node
            for i in ordered_col_indices.get(1, []):
                add_pill_general(i, "left")

            # Col 2 (filters: gender/profile/exp) → LEFT of node
            for i in ordered_col_indices.get(2, []):
                add_pill_general(i, "left")

            # Col 3 (faculties) → RIGHT of node, WITH SHIFT AFTER HOLE
            fac_idxs = ordered_col_indices.get(3, [])
            # find the first zero-degree faculty (biology hole)
            hole_pos = None
            for j, idx in enumerate(fac_idxs):
                if degree[idx] == 0:
                    hole_pos = j
                    break

            for j, idx in enumerate(fac_idxs):
                if visible_nodes is not None and idx not in visible_nodes:
                    continue

                # which node's y do we use?
                # default: its own node
                y_source_idx = idx

                # if there is a hole and we're AFTER it, shift one slot up
                if hole_pos is not None and j > hole_pos:
                    prev_idx = fac_idxs[j - 1]
                    y_source_idx = prev_idx

                y_annot = 1.0 - node_y[y_source_idx]
                x = min(0.995, node_x[idx] + EPS)
                xanchor = "left"

                # do NOT show text for the zero-degree node itself (biology), but keep slot
                txt = labs[idx] if degree[idx] > 0 else ""

                ann.append(dict(
                    x=x, y=y_annot, xref="paper", yref="paper",
                    text=txt, showarrow=False,
                    xanchor=xanchor, yanchor="middle",
                    font=dict(size=10, color="#334155"),
                    bgcolor="rgba(255,255,255,1.0)",
                    bordercolor="rgba(0,0,0,0.18)", borderwidth=1
                ))

            return ann

        annotations_full = build_annotations()
        annotations_focus = build_annotations(alive_nodes) if alive_nodes is not None else annotations_full

        # -------------------------
        # Figure
        # -------------------------
        fig = go.Figure(data=[go.Sankey(
            arrangement="fixed",  # lock nodes (non-movable)
            node=dict(
                pad=22,
                thickness=18,
                line=dict(color="rgba(0,0,0,0.3)", width=0.5),
                label=node_labels,
                color=node_colors,
                x=node_x, y=node_y,
                hovertemplate=node_hover,  # tooltip on nodes
                hoverlabel=dict(
                    bgcolor="rgba(255,255,255,1.0)",
                    bordercolor="#64748b",
                    font_size=11
                ),
            ),
            link=dict(
                source=src, target=tgt, value=val,
                color=link_colors,
                customdata=link_customdata,
                hovertemplate=link_hover,
                hoverlabel=dict(
                    bgcolor="rgba(255,255,255,1.0)",
                    bordercolor="#64748b",
                    font_size=11
                ),
            ),
        )])

        fig.update_layout(
            title_text="Interactive Sankey Diagram",
            font_size=10,
            height=640,
            margin=dict(l=48, r=80, t=50, b=40),
            clickmode="event+select",
            annotations=annotations_focus,
            paper_bgcolor="white",
            plot_bgcolor="white",
        )

        # Reset: restore full arrays/colors/positions AND full annotation set
        fig.update_layout(
            updatemenus=[dict(
                type="buttons", showactive=False,
                x=1.0, xanchor="right", y=1.12, yanchor="top",
                buttons=[dict(
                    label="Reset View",
                    method="update",
                    args=[
                        {
                            "node.label": [node_label_base],
                            "node.color": [cols],
                            "node.x": [node_x],
                            "node.y": [node_y],
                            "link.source": [src],
                            "link.target": [tgt],
                            "link.value": [val],
                            "link.color": [link_colors_default],
                        },
                        {"annotations": annotations_full}
                    ],
                )]
            )]
        )

        return fig

    @app.callback(
        Output("sankey-chart", "figure"),
        Input("sankey-chart", "clickData"),
    )
    def update_chart_on_click(click_data):
        """
        - Node click: use node index (pointNumber/pointIndex).
        - Link click: focus on the link's TARGET node (more informative).
        - Background/invalid: reset view.
        """
        node_idx = None
        if click_data and click_data.get("points"):
            p = click_data["points"][0]

            # Link click has 'source' and 'target' ints
            if "source" in p and "target" in p:
                node_idx = p.get("target")

            else:
                # Node click → 'pointNumber' (sometimes 'pointIndex')
                node_idx = p.get("pointNumber")
                if node_idx is None:
                    node_idx = p.get("pointIndex")

                # extra guard: Dash can emit strings in odd cases
                if isinstance(node_idx, str) and node_idx.isdigit():
                    node_idx = int(node_idx)

            # sanity check
            if not isinstance(node_idx, int):
                node_idx = None

        return create_sankey_chart(node_idx)

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

            # --- TREEMAP MODE ---
            title = "Treemap: Sizing faculties"

            raw_rows = get_treemap_data(gender, teaching_experience, ub_profile)
            tdf = pd.DataFrame(raw_rows)

            # Handle "no data" case
            if tdf.empty:
                fig = go.Figure()
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=20, l=20, r=20, b=20),
                )

                disable_left = True
                disable_right = True
                nav_style = {"display": "none"}
                return fig, title, disable_left, disable_right, nav_style

            # soft palette per dimension
            dimension_colors = {
                "Knowledge": "#fecaca",  # light red
                "Uses": "#e9d5ff",  # light violet
                "Perceptions": "#bbf7d0",  # light green
                "Training": "#fef08a",  # light yellow
            }

            # aggregate per faculty so we know each faculty's total (sum of its 4 dims)
            fac_agg = (
                tdf.groupby(["faculty_name", "short_name", "color"], dropna=False)
                .agg(
                    faculty_total_value=("value", "sum"),
                    overall_faculty_score=("overall_faculty_score", "mean"),
                )
                .reset_index()
            )

            # ---- arrays for treemap ----
            ids: list[str] = []
            labels: list[str] = []
            parents: list[str] = []
            values: list[float] = []
            colors: list[str] = []
            hovertexts: list[str] = []
            text_list: list[str] = []  # visible text drawn in each box

            # ---- ROOT NODE ----
            root_label = "All Faculties"
            root_id = "root"  # unique id for the root
            root_total = float(fac_agg["faculty_total_value"].sum())

            ids.append(root_id)
            labels.append(root_label)
            parents.append("")  # root has no parent
            values.append(root_total)
            colors.append("rgba(0,0,0,0)")  # transparent-ish
            hovertexts.append(
                f"<b>{root_label}</b><br>Total score sum: {root_total:.1f}"
            )
            text_list.append(root_label)

            # ---- FACULTY NODES + CHILD DIMENSION NODES ----
            for _, fac_row in fac_agg.iterrows():
                fac_name = fac_row["faculty_name"]  # e.g. "Biology"
                fac_short = fac_row["short_name"]  # short label to show
                fac_color = fac_row["color"] or "#cccccc"
                fac_total = float(fac_row["faculty_total_value"])
                fac_overall = float(fac_row["overall_faculty_score"])

                fac_id = f"fac|{fac_short}"  # UNIQUE faculty id

                # Faculty node points to root_id as parent
                ids.append(fac_id)
                labels.append(fac_short)
                parents.append(root_id)
                values.append(fac_total)
                colors.append(fac_color)
                hovertexts.append(
                    f"<b>{fac_name}</b><br>"
                    f"Total score sum (4 dims): {fac_total:.1f}<br>"
                    f"Overall avg score: {fac_overall:.1f}"
                )
                # display text inside the faculty rectangle (name only, no score)
                text_list.append(fac_short)

                # now add each of its 4 dimension boxes as children of this faculty
                sub_df = tdf[tdf["faculty_name"] == fac_name]
                for _, dim_row in sub_df.iterrows():
                    dim_label = dim_row["label"]  # "Knowledge", "Uses", ...
                    dim_val = float(dim_row["value"])  # that dimension's score
                    dim_color = dimension_colors.get(dim_label, "#999999")

                    child_id = f"{fac_id}|{dim_label}"  # UNIQUE child id

                    ids.append(child_id)
                    labels.append(dim_label)
                    parents.append(fac_id)  # <-- parent is fac_id, not label
                    values.append(dim_val)
                    colors.append(dim_color)
                    hovertexts.append(
                        f"<b>{fac_name} – {dim_label}</b><br>"
                        f"Score: {dim_val:.1f}"
                    )
                    # text drawn in each dimension box, show label + score
                    text_list.append(f"{dim_label}\n{dim_val:.1f}")

            # --- build treemap with unique ids ---
            fig = go.Figure(
                go.Treemap(
                    ids=ids,  # <- unique IDs for EVERY node
                    labels=labels,  # what user sees
                    parents=parents,  # MUST match parent IDs, NOT labels
                    values=values,  # area sizes
                    text=text_list,  # what’s drawn in the rectangles
                    textinfo="text",
                    hovertext=hovertexts,
                    hoverinfo="text",
                    marker=dict(
                        colors=colors,
                        line=dict(width=1, color="black"),
                    ),
                    branchvalues="total",  # parent value = sum(children)
                    maxdepth=3,  # show root -> faculty -> 4 areas
                    tiling=dict(
                        pad=2,
                        packing="squarify",
                    ),
                    pathbar=dict(visible=False),
                )
            )

            fig.update_layout(
                margin=dict(t=20, l=20, r=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )

            # treemap mode: arrows hidden
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
