from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException, Response
from fastapi.responses import FileResponse
from typing import Optional, Dict, Any
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
import numpy as np
import math
import pandas as pd
import os
import numpy as np
import logging
from matplotlib import cm, colors

from src.utils.data_loader import load_surveys_data, load_faculties_data, df_to_json_safe

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/api", tags=["Visualizations"])

# Load once at startup
faculties_df = load_faculties_data()
surveys_df = load_surveys_data()

SCORE_COLS = ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]


def safe_float(v: Any) -> Optional[float]:
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except Exception:
        return None


def mean_ignore_none(values):
    vals = [v for v in values if isinstance(v, (int, float))]
    if not vals:
        return None
    return sum(vals) / len(vals)


@router.get("/faculty/{faculty_name}/scores")
def faculty_scores(
        faculty_name: str,
        gender: str | None = None,
        teaching_experience: str | None = None,
        ub_profile: str | None = None,
) -> Dict[str, Any]:
    df = surveys_df.copy()

    # Apply the same optional filters used by /spike-map
    if gender:
        df = df[df["gender"] == gender]
    if teaching_experience:
        df = df[df["teaching_experience"] == teaching_experience]
    if ub_profile:
        df = df[df["ub_profile"] == ub_profile]

    # Case/space-insensitive faculty match over ALL rows for that faculty
    fac_key = (faculty_name or "").strip().lower()
    mask = df["faculty_name"].astype(str).str.strip().str.lower() == fac_key
    if not mask.any():
        raise HTTPException(status_code=404, detail=f"Faculty '{faculty_name}' not found")

    fdf = df.loc[mask].copy()

    # Match /spike-map math for "All":
    # 1) per-row mean across the 4 columns
    fdf["row_mean"] = fdf[SCORE_COLS].mean(axis=1, skipna=True)
    # 2) overall faculty score = mean of those per-row means
    total_score = float(fdf["row_mean"].mean(skipna=True))

    # Per-metric means across all rows for this faculty
    metric_means = fdf[SCORE_COLS].mean(numeric_only=True, skipna=True).to_dict()
    metric_means = {k: (float(v) if v is not None else None) for k, v in metric_means.items()}

    # Color: prefer faculties_df if present; otherwise take first non-null in fdf
    color = None
    if "faculties_df" in globals():
        meta = faculties_df[
            faculties_df["faculty_name"].astype(str).str.strip().str.lower() == fac_key
            ]
        if not meta.empty and "color" in meta.columns:
            color = meta["color"].dropna().iloc[0] if not meta["color"].dropna().empty else None

    if color is None and "color" in fdf.columns and not fdf["color"].dropna().empty:
        color = fdf["color"].dropna().iloc[0]

    return {
        "faculty_name": fdf["faculty_name"].iloc[0],
        "color": color,
        **metric_means,  # knowledge_score, uses_score, perceptions_score, training_needs_score
        "total_score": total_score,  # mean(row_means) — matches /spike-map when category=All
    }


@router.get("/treemap-data")
def get_treemap_data(
        gender: str | None = None,
        teaching_experience: str | None = None,
        ub_profile: str | None = None,
):
    """
    Clean aggregated dataset for the treemap / bubble chart.

    We return one row per faculty x dimension ("Knowledge", "Uses", "Perceptions", "Training"),
    with:
      - value: that faculty's mean score for that dimension
      - overall_faculty_score: mean of all 4 dims for that faculty (for coloring, etc.)

    IMPORTANT:
    We DROP faculties where all four dim scores are 0.0.
    That prevents Plotly treemap from crashing when it tries to
    compute weighted averages with zero total weight.
    """
    df = surveys_df.copy()

    # ----- apply optional demographic filters -----
    if gender:
        df = df[df["gender"] == gender]
    if teaching_experience:
        df = df[df["teaching_experience"] == teaching_experience]
    if ub_profile:
        df = df[df["ub_profile"] == ub_profile]

    # if after filters no rows, just return empty list
    if df.empty:
        return []

    # ----- compute mean scores per faculty -----
    score_cols = [
        "knowledge_score",
        "uses_score",
        "perceptions_score",
        "training_needs_score",
    ]

    fac_means = (
        df.groupby("faculty_name")[score_cols]
        .mean(numeric_only=True)
        .reset_index()
    )

    # replace NaN/inf with 0.0 so we can reason about "has data vs no data"
    fac_means = fac_means.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    # compute per-faculty overall avg (across the 4 dims)
    fac_means["overall_faculty_score"] = fac_means[
        ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]
    ].mean(axis=1)

    # bring metadata (color, etc.) from faculties_df
    fac_means = fac_means.merge(
        faculties_df[["faculty_name", "color", "color_rgb", "short_name"]],
        on="faculty_name",
        how="left",
    )

    rows = []

    for _, row in fac_means.iterrows():
        faculty = row["faculty_name"]

        k = float(row["knowledge_score"])
        u = float(row["uses_score"])
        p = float(row["perceptions_score"])
        t = float(row["training_needs_score"])

        # detect "no data at all for this faculty after filters"
        # note: true scores should NEVER be literally 0
        # (your scoring is on a positive scale),
        # so 0 basically means "missing → filled with 0"
        if (k == 0.0) and (u == 0.0) and (p == 0.0) and (t == 0.0):
            # skip this faculty entirely so Plotly doesn't freak out
            continue

        overall_val = float(row["overall_faculty_score"])
        if not np.isfinite(overall_val):
            overall_val = 0.0

        dim_map = [
            ("Knowledge", k),
            ("Uses", u),
            ("Perceptions", p),
            ("Training", t),
        ]

        for dim_label, dim_val in dim_map:
            # if for some reason this specific dim is still weird, coerce
            if (not np.isfinite(dim_val)) or pd.isna(dim_val):
                dim_val = 0.0

            rows.append({
                # hierarchy info for the treemap
                "faculty_name": faculty,  # parent node in px.treemap path[0]
                "label": dim_label,  # child node name (path[1])
                "value": float(dim_val),  # size of the child block

                # extra stuff frontend can use for color / hover
                "overall_faculty_score": overall_val,
                "short_name": row.get("short_name", faculty),
                "color": row.get("color", None),
                "color_rgb": row.get("color_rgb", None),
            })

    # if all faculties got skipped, return empty clean array
    if not rows:
        return []

    out_df = pd.DataFrame(rows)

    # sanitize: ensure no NaN/inf in final JSON
    out_df = out_df.replace([np.inf, -np.inf], np.nan)
    out_df = out_df.fillna(0.0)

    return df_to_json_safe(out_df)


@router.get("/spike-map")
def get_spike_map_data(
        category: str = "All",
        gender: str | None = None,
        teaching_experience: str | None = None,
        ub_profile: str | None = None,
):
    df = surveys_df.copy()

    # ----- filters -----
    if gender:
        df = df[df["gender"] == gender]
    if teaching_experience:
        df = df[df["teaching_experience"] == teaching_experience]
    if ub_profile:
        df = df[df["ub_profile"] == ub_profile]

    # ----- pick/compute category_score for each row -----
    if category == "All":
        df["category_score"] = df[
            ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]
        ].mean(axis=1)
    else:
        category_column = {
            "knowledge": "knowledge_score",
            "uses": "uses_score",
            "perceptions": "perceptions_score",
            "training": "training_needs_score",
        }.get(category, "knowledge_score")
        df["category_score"] = df[category_column]

    # ----- attach faculty metadata (lat/lon/color/etc) -----
    faculties_df["color_rgb_tuple"] = faculties_df["color_rgb"].apply(tuple)
    df = df.merge(faculties_df, on="faculty_name", how="left")

    # ----- aggregate by faculty -----
    agg = df.groupby(
        ["faculty_name", "latitude", "longitude", "color", "short_name", "color_rgb_tuple"],
        dropna=False,
    ).agg(
        {
            "category_score": "mean",
            "knowledge_score": "mean",
            "uses_score": "mean",
            "perceptions_score": "mean",
            "training_needs_score": "mean",
            "faculty_name": "count",
        }
    )

    agg = agg.rename(columns={"faculty_name": "n_responses"}).reset_index()

    # ----- convert rgb tuple back to list for JSON -----
    agg["color_rgb"] = agg["color_rgb_tuple"].apply(list)
    agg.drop(columns=["color_rgb_tuple"], inplace=True)

    return df_to_json_safe(agg)


@router.get("/faculty/{faculty_name}/knowledge-distribution")
def knowledge_distribution(
        faculty_name: str,
        demographic1: str = "gender",
        demographic2: str | None = None,
):
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    # Map textual knowledge → numeric 1–4
    knowledge_map = {
        "No knowledge": 1,
        "Little knowledge": 2,
        "Good knowledge": 3,
        "Expert knowledge": 4,
    }
    df["knowledge_num"] = df["ia_knowledge"].map(knowledge_map)

    col_map = {
        "gender": "gender",
        "experience": "teaching_experience",
        "profile": "ub_profile",
    }
    if demographic1 not in col_map:
        return {"error": f"Invalid demographic: {demographic1}"}

    col1 = col_map[demographic1]
    col2 = col_map.get(demographic2) if demographic2 else None

    # Single demographic → mean per category (normalized)
    if not col2:
        grouped = (
            df.groupby(col1)["knowledge_num"]
            .mean()
            .reset_index()
            .rename(columns={col1: "category", "knowledge_num": "average_score"})
        )
        grouped["average_score"] = grouped["average_score"].astype(float).round(3)
        return {
            "mode": "single",
            "demographics": [demographic1],
            "categories": grouped["category"].tolist(),
            "values": grouped["average_score"].tolist(),
        }

    # Dual demographic:
    g = (
        df.groupby([col1, col2])["knowledge_num"]
        .agg(mean_sub="mean", n_sub="size")
        .reset_index()
        .rename(columns={col1: "main", col2: "sub"})
    )

    # total respondents per main group
    g["n_main"] = g.groupby("main")["n_sub"].transform("sum")

    # main-group average
    main_avg_map = df.groupby(col1)["knowledge_num"].mean().astype(float).to_dict()
    g["main_avg"] = g["main"].map(main_avg_map)

    # weighted contribution so sum_sub(contrib)==main_avg
    g["contribution"] = (g["mean_sub"] * g["n_sub"]) / g["n_main"]
    g = g.fillna(0.0)

    for c in ["mean_sub", "main_avg", "contribution"]:
        g[c] = g[c].astype(float)

    return {
        "mode": "dual",
        "demographics": [demographic1, demographic2],
        "data": g[["main", "sub", "mean_sub", "n_sub", "n_main", "main_avg", "contribution"]]
        .to_dict(orient="records"),
    }


def get_sankey_chart_data():
    df = surveys_df.copy()

    # All node labels (layers of the Sankey)
    labels = (
            ["Knowledge", "Uses", "Perceptions", "Training Needs"]  # first layer
            + ["Gender", "Teaching Experience", "UB Profile"]  # second layer
            + list(df["gender"].unique())  # third layer
            + list(df["teaching_experience"].unique())
            + list(df["ub_profile"].unique())
            + faculties_df["faculty_name"].tolist()  # last layer
    )

    # Map node name -> index in `labels`
    first_layer_indices = {
        score: i
        for i, score in enumerate(
            ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]
        )
    }
    second_layer_indices = {
        category: i + 4
        for i, category in enumerate(["gender", "teaching_experience", "ub_profile"])
    }
    third_layer_indices = {
        **{gender: labels.index(gender) for gender in df["gender"].unique()},
        **{
            teaching_exp: labels.index(teaching_exp)
            for teaching_exp in df["teaching_experience"].unique()
        },
        **{ub_prof: labels.index(ub_prof) for ub_prof in df["ub_profile"].unique()},
    }
    faculty_indices = {
        faculty: labels.index(faculty)
        for faculty in faculties_df["faculty_name"]
    }

    sources = []
    targets = []
    values = []

    # (1) score dimension -> demographic category block ("Gender", etc.)
    for score in ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]:
        for category in second_layer_indices.keys():
            # sum of that score grouped by that category, then sum across categories
            category_score = df.groupby(category)[score].sum().sum()
            sources.append(first_layer_indices[score])
            targets.append(second_layer_indices[category])
            values.append(category_score)

    # (2) demographic category block -> specific subgroup (e.g. "Female", "More than 20", "Professor")
    for category, category_idx in second_layer_indices.items():
        grouped_scores = df.groupby(category)[
            ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]
        ].sum()
        for subgroup_value, scores in grouped_scores.iterrows():
            if pd.notnull(subgroup_value):
                sources.append(category_idx)
                targets.append(third_layer_indices[subgroup_value])
                total_score = scores.sum()
                values.append(total_score)

    # (3) subgroup -> faculty
    for _, row in df.iterrows():
        faculty = row["faculty_name"]
        if pd.notnull(faculty):
            for category in ["gender", "teaching_experience", "ub_profile"]:
                subgroup_value = row[category]
                if pd.notnull(subgroup_value):
                    sources.append(third_layer_indices[subgroup_value])
                    targets.append(faculty_indices[faculty])
                    faculty_score = (
                            (row["knowledge_score"] or 0)
                            + (row["uses_score"] or 0)
                            + (row["perceptions_score"] or 0)
                            + (row["training_needs_score"] or 0)
                    )
                    values.append(faculty_score)

    # faculty color mapping for Plotly coloring (strings are fine)
    faculty_colors = {
        faculty: faculties_df.loc[
            faculties_df["faculty_name"] == faculty, "color"
        ].values[0]
        for faculty in faculties_df["faculty_name"]
    }

    # --- sanitize numeric lists so FastAPI won't choke on NaN / inf ---
    def _sanitize_num_list(seq):
        out = []
        for x in seq:
            # Convert numpy types
            if isinstance(x, (np.integer,)):
                x = int(x)
            elif isinstance(x, (np.floating,)):
                x = float(x)
            # Replace NaN / inf with 0
            if isinstance(x, float) and (not math.isfinite(x)):
                x = 0.0
            out.append(x)
        return out

    safe_sources = _sanitize_num_list(sources)
    safe_targets = _sanitize_num_list(targets)
    safe_values = _sanitize_num_list(values)

    return {
        "sources": safe_sources,
        "targets": safe_targets,
        "values": safe_values,
        "labels": [str(x) for x in labels],
        "faculty_colors": {str(k): str(v) for k, v in faculty_colors.items()},
    }


@router.get("/sankey-data")
def sankey_data():
    """
    Return data for Sankey chart (faculty, gender, experience, etc.),
    with NaN/Inf already cleaned.
    """
    data = get_sankey_chart_data()
    # Nothing fancy here because we already sanitized in get_sankey_chart_data()
    return data


@router.get("/sankey-data")
def sankey_data():
    """Return data for Sankey chart (faculty, gender, experience, etc.)."""
    data = get_sankey_chart_data()
    return data


@router.get("/faculty/{faculty_name}/normative-distribution")
def get_normative_distribution(faculty_name: str):
    df = surveys_df[surveys_df["faculty_name"] == faculty_name]

    column = "ia_normative_ub"
    distribution = df[column].value_counts().to_dict()

    return {
        "categories": list(distribution.keys()),
        "values": list(distribution.values())
    }


@router.get("/faculty/{faculty_name}/knowledge-functionality-correlation")
def get_knowledge_functionality_correlation(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    # Apply demographic filters
    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    # 13 application columns (knowledge familiarity)
    app_cols = [
        "ia_knowledge_text_creation",
        "ia_knowledge_multimedia_creation",
        "ia_knowledge_class_planning",
        "ia_knowledge_material_design",
        "ia_knowledge_activity_design",
        "ia_knowledge_evaluation",
        "ia_knowledge_research_management",
        "ia_knowledge_data_collection",
        "ia_knowledge_transcription_translation",
        "ia_knowledge_data_analysis",
        "ia_knowledge_technical_support",
        "ia_knowledge_ai_experiments",
        "ia_knowledge_inclusion_support",
    ]

    app_map = {
        "I don't know any": 1,
        "I know a few": 2,
        "I know several": 3,
        "I know many": 4,
    }

    for col in app_cols:
        df[col] = df[col].map(app_map)

    grouped = (
        df.groupby("ia_knowledge")[app_cols]
        .mean()
        .reset_index()
    )

    grouped.rename(columns={"ia_knowledge": "knowledge_label"}, inplace=True)
    grouped = grouped.replace([float("inf"), float("-inf")], None).fillna(0)

    return grouped.to_dict(orient="records")


def truncate_colormap(cmap_name: str, minval=0.4, maxval=1.0, n=256):
    """
    Take an existing matplotlib colormap (e.g. "Purples") and
    return a new one that only spans [minval, maxval] of it.
    minval closer to 0 = include more of the light pastels
    minval closer to 1 = only deep, dark end.
    """
    base = cm.get_cmap(cmap_name)
    new_colors = base(np.linspace(minval, maxval, n))
    return colors.LinearSegmentedColormap.from_list(
        f"{cmap_name}_trunc_{minval}_{maxval}",
        new_colors
    )

purples_trunc = truncate_colormap("Purples", minval=0.4, maxval=1.0)
reds_trunc = truncate_colormap("Reds", minval=0.4, maxval=1.0)

@router.get("/faculty/{faculty_name}/knowledge-applications-wordcloud-svg")
def knowledge_concept_cloud_image(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    app_map = {
        "I don't know any": 1,
        "I know a few": 2,
        "I know several": 3,
        "I know many": 4,
    }

    app_columns = [
        "ia_knowledge_text_creation",
        "ia_knowledge_multimedia_creation",
        "ia_knowledge_class_planning",
        "ia_knowledge_material_design",
        "ia_knowledge_activity_design",
        "ia_knowledge_evaluation",
        "ia_knowledge_research_management",
        "ia_knowledge_data_collection",
        "ia_knowledge_transcription_translation",
        "ia_knowledge_data_analysis",
        "ia_knowledge_technical_support",
        "ia_knowledge_ai_experiments",
        "ia_knowledge_inclusion_support",
    ]

    name_map = {
        "ia_knowledge_text_creation": "Text",
        "ia_knowledge_multimedia_creation": "Media",
        "ia_knowledge_class_planning": "Planning",
        "ia_knowledge_material_design": "Design",
        "ia_knowledge_activity_design": "Activity",
        "ia_knowledge_evaluation": "Evaluation",
        "ia_knowledge_research_management": "Research",
        "ia_knowledge_data_collection": "Data",
        "ia_knowledge_transcription_translation": "Translation",
        "ia_knowledge_data_analysis": "Analysis",
        "ia_knowledge_technical_support": "Support",
        "ia_knowledge_ai_experiments": "Experiments",
        "ia_knowledge_inclusion_support": "Inclusion",
    }

    for col in app_columns:
        df[col] = df[col].map(app_map).fillna(0)

    total_scores = df[app_columns].sum().to_dict()

    # Visual boost
    gamma = 1.25
    freqs = {name_map[c]: float(v) ** gamma for c, v in total_scores.items()}

    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(base_dir, "..", "img")
    os.makedirs(img_dir, exist_ok=True)
    output_path = os.path.join(img_dir, f"{faculty_name}_wordcloud.png")

    wc = WordCloud(
        background_color="white",
        width=1000,
        height=420,
        max_words=50,
        prefer_horizontal=0.92,
        relative_scaling=1.0,
        repeat=False,
        scale=1,
        margin=2,
        collocations=False,
        normalize_plurals=False,
        colormap=reds_trunc,
    ).generate_from_frequencies(freqs)

    svg = wc.to_svg(embed_font=True)
    svg = svg.replace(
        "<svg ",
        "<svg style='max-width:100%;height:auto' "
    )
    svg = svg.replace(
        "</svg>",
        "<style>text{transition:opacity .15s, filter .15s} text:hover{opacity:.9; filter:drop-shadow(0 0 2px rgba(0,0,0,.25)); cursor:pointer}</style></svg>"
    )
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/faculty/{faculty_name}/knowledge-applications-distribution-count")
def knowledge_app_distribution(
        faculty_name: str,
        app_label: str = Query(..., description="Label from name_map, e.g. 'Text', 'Media', ..."),
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    name_map = {
        "ia_knowledge_text_creation": "Text",
        "ia_knowledge_multimedia_creation": "Media",
        "ia_knowledge_class_planning": "Planning",
        "ia_knowledge_material_design": "Design",
        "ia_knowledge_activity_design": "Activity",
        "ia_knowledge_evaluation": "Evaluation",
        "ia_knowledge_research_management": "Research",
        "ia_knowledge_data_collection": "Data",
        "ia_knowledge_transcription_translation": "Translation",
        "ia_knowledge_data_analysis": "Analysis",
        "ia_knowledge_technical_support": "Support",
        "ia_knowledge_ai_experiments": "Experiments",
        "ia_knowledge_inclusion_support": "Inclusion",
    }
    reverse_name_map = {v: k for k, v in name_map.items()}
    col = reverse_name_map.get(app_label)
    if not col:
        raise HTTPException(status_code=400, detail=f"Unknown app_label '{app_label}'")

    levels = ["I don't know any", "I know a few", "I know several", "I know many"]

    counts = {lvl: int((df[col] == lvl).sum()) for lvl in levels}
    total = int(sum(counts.values()))

    return {"label": app_label, "levels": levels, "counts": counts, "total": total}


# ---------------------------------------------------------------------------------
# NEW ENDPOINTS FOR THE "USES" SECTION
# ---------------------------------------------------------------------------------

@router.get("/faculty/{faculty_name}/uses-distribution")
def uses_distribution(
        faculty_name: str,
        demographic1: str = "gender",
        demographic2: str | None = None,
):
    """
    Same shape/logic as /knowledge-distribution but for AI usage.
    We treat self-reported global usage level (ia_uses) as 1..4.
    """
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    # Map textual usage → numeric 1–4
    uses_map = {
        "No use": 1,
        "Low use": 2,
        "Moderate use": 3,
        "Advanced use": 4,
    }
    df["uses_num"] = df["ia_uses"].map(uses_map)

    col_map = {
        "gender": "gender",
        "experience": "teaching_experience",
        "profile": "ub_profile",
    }
    if demographic1 not in col_map:
        return {"error": f"Invalid demographic: {demographic1}"}

    col1 = col_map[demographic1]
    col2 = col_map.get(demographic2) if demographic2 else None

    # Single demographic
    if not col2:
        grouped = (
            df.groupby(col1)["uses_num"]
            .mean()
            .reset_index()
            .rename(columns={col1: "category", "uses_num": "average_score"})
        )
        grouped["average_score"] = grouped["average_score"].astype(float).round(3)
        return {
            "mode": "single",
            "demographics": [demographic1],
            "categories": grouped["category"].tolist(),
            "values": grouped["average_score"].tolist(),
        }

    # Two demographics
    g = (
        df.groupby([col1, col2])["uses_num"]
        .agg(mean_sub="mean", n_sub="size")
        .reset_index()
        .rename(columns={col1: "main", col2: "sub"})
    )

    g["n_main"] = g.groupby("main")["n_sub"].transform("sum")

    main_avg_map = df.groupby(col1)["uses_num"].mean().astype(float).to_dict()
    g["main_avg"] = g["main"].map(main_avg_map)

    # Weighted contribution so sum_sub(contribution) == main_avg
    g["contribution"] = (g["mean_sub"] * g["n_sub"]) / g["n_main"]
    g = g.fillna(0.0)

    for c in ["mean_sub", "main_avg", "contribution"]:
        g[c] = g[c].astype(float)

    return {
        "mode": "dual",
        "demographics": [demographic1, demographic2],
        "data": g[
            ["main", "sub", "mean_sub", "n_sub", "n_main", "main_avg", "contribution"]
        ].to_dict(orient="records"),
    }


@router.get("/faculty/{faculty_name}/proposes-distribution")
def get_proposes_distribution(faculty_name: str):
    """
    Pie chart for: 'Do they propose AI use to students?'
    We look at ia_proposes_students which is already mapped to:
    "Never", "Sometimes", "Often", "Very often".
    """
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    column = "ia_proposes_students"
    order = ["Never", "Sometimes", "Often", "Very often"]

    counts_raw = df[column].value_counts().to_dict()
    counts = [int(counts_raw.get(level, 0)) for level in order]

    return {
        "categories": order,
        "values": counts,
    }


@router.get("/faculty/{faculty_name}/uses-functionality-correlation")
def get_uses_functionality_correlation(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    Mirror of /knowledge-functionality-correlation but for usage frequency.
    Bucket rows by global 'ia_uses' level (No use / Low use / ...).
    For each bucket, compute mean usage frequency (1..4) for each task.
    Return array of dicts:
      {
        "usage_label": "Low use",
        "Text Creation": <float>,
        ...
      }
    """
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    # Filters
    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    # task columns (do NOT include ia_proposes_students here)
    task_cols = [
        "ia_uses_text_creation",
        "ia_uses_multimedia_creation",
        "ia_uses_class_planning",
        "ia_uses_material_design",
        "ia_uses_activity_design",
        "ia_uses_evaluation",
        "ia_uses_research_management",
        "ia_uses_data_collection",
        "ia_uses_transcription_translation",
        "ia_uses_data_analysis",
        "ia_uses_technical_support",
        "ia_uses_ai_experiments",
        "ia_uses_inclusion_support",
    ]

    # map frequency to 1..4 numeric
    task_freq_to_1to4 = {
        "Never": 1.0,
        "Sometimes": 2.0,
        "Often": 3.0,
        "Very often": 4.0,
    }

    for col in task_cols:
        df[col] = df[col].map(task_freq_to_1to4)

    # Group by global usage label
    grouped = df.groupby("ia_uses")[task_cols].mean().reset_index()

    # nice display names for each task col
    nice_names = {
        "ia_uses_text_creation": "Text Creation",
        "ia_uses_multimedia_creation": "Multimedia Creation",
        "ia_uses_class_planning": "Class Planning",
        "ia_uses_material_design": "Material Design",
        "ia_uses_activity_design": "Activity Design",
        "ia_uses_evaluation": "Evaluation",
        "ia_uses_research_management": "Research Management",
        "ia_uses_data_collection": "Data Collection",
        "ia_uses_transcription_translation": "Transcription / Translation",
        "ia_uses_data_analysis": "Data Analysis",
        "ia_uses_technical_support": "Technical Support",
        "ia_uses_ai_experiments": "AI Experiments",
        "ia_uses_inclusion_support": "Inclusion Support",
    }

    grouped = grouped.rename(columns=nice_names)
    grouped = grouped.rename(columns={"ia_uses": "usage_label"})
    grouped = grouped.replace([float("inf"), float("-inf")], None).fillna(0)

    # Return array[ { usage_label, "Text Creation": avg, ... }, ... ]
    return grouped.to_dict(orient="records")


@router.get("/faculty/{faculty_name}/uses-applications-wordcloud-svg")
def uses_applications_wordcloud_svg(
        faculty_name: str,
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    Wordcloud for "Where is AI actually being used?"
    We look at usage frequency for each task column, map it to 1..4,
    sum across respondents, and feed that to a WordCloud.
    """
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    # task columns (usage), excluding proposes-to-students
    app_columns = [
        "ia_uses_text_creation",
        "ia_uses_multimedia_creation",
        "ia_uses_class_planning",
        "ia_uses_material_design",
        "ia_uses_activity_design",
        "ia_uses_evaluation",
        "ia_uses_research_management",
        "ia_uses_data_collection",
        "ia_uses_transcription_translation",
        "ia_uses_data_analysis",
        "ia_uses_technical_support",
        "ia_uses_ai_experiments",
        "ia_uses_inclusion_support",
    ]

    # short display names for each task in the cloud
    name_map = {
        "ia_uses_text_creation": "Text",
        "ia_uses_multimedia_creation": "Media",
        "ia_uses_class_planning": "Planning",
        "ia_uses_material_design": "Design",
        "ia_uses_activity_design": "Activity",
        "ia_uses_evaluation": "Evaluation",
        "ia_uses_research_management": "Research",
        "ia_uses_data_collection": "Data",
        "ia_uses_transcription_translation": "Translation",
        "ia_uses_data_analysis": "Analysis",
        "ia_uses_technical_support": "Support",
        "ia_uses_ai_experiments": "Experiments",
        "ia_uses_inclusion_support": "Inclusion",
    }

    freq_map = {
        "Never": 1,
        "Sometimes": 2,
        "Often": 3,
        "Very often": 4,
    }

    for col in app_columns:
        df[col] = df[col].map(freq_map).fillna(0)

    total_scores = df[app_columns].sum().to_dict()

    # amplify a bit so differences pop visually
    gamma = 1.25
    freqs = {name_map[c]: float(v) ** gamma for c, v in total_scores.items()}

    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(base_dir, "..", "img")
    os.makedirs(img_dir, exist_ok=True)
    output_path = os.path.join(img_dir, f"{faculty_name}_uses_wordcloud.png")

    wc = WordCloud(
        background_color="white",
        width=1000,
        height=420,
        max_words=50,
        prefer_horizontal=0.92,
        relative_scaling=1.0,
        repeat=False,
        scale=1,
        margin=2,
        collocations=False,
        normalize_plurals=False,
        colormap=purples_trunc,  # purple theme for Uses
    ).generate_from_frequencies(freqs)

    svg = wc.to_svg(embed_font=True)
    svg = svg.replace(
        "<svg ",
        "<svg style='max-width:100%;height:auto' "
    )
    svg = svg.replace(
        "</svg>",
        "<style>text{transition:opacity .15s, filter .15s} text:hover{opacity:.9; filter:drop-shadow(0 0 2px rgba(0,0,0,.25)); cursor:pointer}</style></svg>"
    )
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/faculty/{faculty_name}/uses-applications-distribution-count")
def uses_applications_distribution_count(
        faculty_name: str,
        app_label: str = Query(..., description="Short label from name_map (e.g. 'Text', 'Media', etc.)"),
        gender: Optional[str] = Query(None),
        experience: Optional[str] = Query(None),
        profile: Optional[str] = Query(None),
):
    """
    Tooltip spiderchart for Uses wordcloud.
    Given a task label like 'Text', return how many respondents said
    Never / Sometimes / Often / Very often for that task.
    """
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    if gender and gender != "All":
        df = df[df["gender"] == gender]
    if experience:
        df = df[df["teaching_experience"] == experience]
    if profile:
        df = df[df["ub_profile"] == profile]

    # same map we used in the wordcloud endpoint above
    name_map = {
        "ia_uses_text_creation": "Text",
        "ia_uses_multimedia_creation": "Media",
        "ia_uses_class_planning": "Planning",
        "ia_uses_material_design": "Design",
        "ia_uses_activity_design": "Activity",
        "ia_uses_evaluation": "Evaluation",
        "ia_uses_research_management": "Research",
        "ia_uses_data_collection": "Data",
        "ia_uses_transcription_translation": "Translation",
        "ia_uses_data_analysis": "Analysis",
        "ia_uses_technical_support": "Support",
        "ia_uses_ai_experiments": "Experiments",
        "ia_uses_inclusion_support": "Inclusion",
    }
    reverse_name_map = {v: k for k, v in name_map.items()}
    col = reverse_name_map.get(app_label)
    if not col:
        raise HTTPException(status_code=400, detail=f"Unknown app_label '{app_label}'")

    # fixed order so front-end spider chart can trust it
    levels = ["Never", "Very often", "Sometimes", "Often"]
    # NOTE: our tooltip spider in UsesApplicationsWordCloud
    # plots POLAR_ORDER = ["Never", "Very often", "Sometimes", "Often"]
    # so we match that exact set here. We'll still count using canonical 4 buckets.

    canonical_levels = ["Never", "Sometimes", "Often", "Very often"]
    raw_counts = df[col].value_counts().to_dict()

    # Build counts dict covering all 4 canonical levels
    counts_dict = {lvl: int(raw_counts.get(lvl, 0)) for lvl in canonical_levels}
    total = int(sum(counts_dict.values()))

    return {
        "label": app_label,
        "levels": canonical_levels,
        "counts": counts_dict,
        "total": total,
    }
