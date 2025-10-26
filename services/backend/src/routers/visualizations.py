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
from src.utils.data_loader import load_surveys_data, load_faculties_data, df_to_json_safe
import logging

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
        **metric_means,             # knowledge_score, uses_score, perceptions_score, training_needs_score
        "total_score": total_score, # mean(row_means) — matches /spike-map when category=All
    }


@router.get("/treemap-data")
def get_treemap_data(gender: str | None = None, teaching_experience: str | None = None, ub_profile: str | None = None):
    df = surveys_df.copy()

    if gender:
        df = df[df["gender"] == gender]
    if teaching_experience:
        df = df[df["teaching_experience"] == teaching_experience]
    if ub_profile:
        df = df[df["ub_profile"] == ub_profile]

    df["overall_score"] = df[
        ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]
    ].sum(axis=1)
    df = df.merge(faculties_df, on="faculty_name", how="left")

    faculty_aggregates = df.groupby("faculty_name")["overall_score"].sum()

    treemap_data = pd.DataFrame({
        "parent": np.repeat(df["faculty_name"].values, 4),
        "label": ["Knowledge", "Uses", "Perceptions", "Training"] * len(df),
        "value": df[["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]].values.flatten(),
        "overall_faculty_score": np.repeat(df["faculty_name"].map(faculty_aggregates).values, 4)
    })

    return treemap_data.to_dict(orient="records")


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
    # we need both the means of the scores AND the counts per faculty
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
            # count of raw rows in this faculty after filters
            "faculty_name": "count",
        }
    )

    agg = agg.rename(columns={"faculty_name": "n_responses"}).reset_index()

    # ----- convert rgb tuple back to list for JSON -----
    agg["color_rgb"] = agg["color_rgb_tuple"].apply(list)
    agg.drop(columns=["color_rgb_tuple"], inplace=True)

    # df_to_json_safe should turn it into something FastAPI can serialize cleanly,
    # and also handle NaNs -> None, etc.
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
    # 1) avg per (main, sub) + counts
    g = (
        df.groupby([col1, col2])["knowledge_num"]
        .agg(mean_sub="mean", n_sub="size")
        .reset_index()
        .rename(columns={col1: "main", col2: "sub"})
    )

    # 2) total respondents per main group
    g["n_main"] = g.groupby("main")["n_sub"].transform("sum")

    # 3) main-group average
    main_avg_map = df.groupby(col1)["knowledge_num"].mean().astype(float).to_dict()
    g["main_avg"] = g["main"].map(main_avg_map)

    # 4) weighted contribution so that sum_sub(contribution) == main_avg
    # contribution = (mean_sub * n_sub) / n_main
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

    # Define labels for nodes
    labels = (
            ["Knowledge", "Uses", "Perceptions", "Training Needs"]  # First layer
            + ["Gender", "Teaching Experience", "UB Profile"]  # Second layer
            + list(df["gender"].unique())  # Third layer: Gender types
            + list(df["teaching_experience"].unique())  # Third layer: Teaching experience types
            + list(df["ub_profile"].unique())  # Third layer: UB profile types
            + faculties_df["faculty_name"].tolist()  # Final layer: Faculties
    )

    # Indexing nodes
    first_layer_indices = {score: i for i, score in
                           enumerate(["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"])}
    second_layer_indices = {category: i + 4 for i, category in
                            enumerate(["gender", "teaching_experience", "ub_profile"])}
    third_layer_indices = {
        **{gender: labels.index(gender) for gender in df["gender"].unique()},
        **{teaching_exp: labels.index(teaching_exp) for teaching_exp in df["teaching_experience"].unique()},
        **{ub_profile: labels.index(ub_profile) for ub_profile in df["ub_profile"].unique()},
    }
    faculty_indices = {faculty: labels.index(faculty) for faculty in faculties_df["faculty_name"]}

    # Initialize sources, targets, and values
    sources = []
    targets = []
    values = []

    # Flow from first layer to second layer
    for score in ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]:
        for category in second_layer_indices.keys():
            category_score = df.groupby(category)[score].sum().sum()  # Total score for the category
            sources.append(first_layer_indices[score])
            targets.append(second_layer_indices[category])
            values.append(category_score)  # Total score assigned as value

    # Flow from second layer to third layer (filter types)
    for category, category_idx in second_layer_indices.items():
        # Group by the filter type and compute the sum of the relevant scores
        grouped_scores = df.groupby(category)[
            ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]].sum()
        for filter_type, scores in grouped_scores.iterrows():
            if pd.notnull(filter_type):  # Ensure valid filter type
                sources.append(category_idx)
                targets.append(third_layer_indices[filter_type])
                # Total contribution score for this filter type
                total_score = scores.sum()
                values.append(total_score)

    # Flow from third layer to faculties
    for _, row in df.iterrows():
        faculty = row["faculty_name"]
        if pd.notnull(faculty):
            for category in ["gender", "teaching_experience", "ub_profile"]:
                filter_type = row[category]
                if pd.notnull(filter_type):
                    sources.append(third_layer_indices[filter_type])
                    targets.append(faculty_indices[faculty])
                    # Sum the contribution of the filter type to this faculty
                    faculty_score = row["knowledge_score"] + row["uses_score"] + row["perceptions_score"] + row[
                        "training_needs_score"]
                    values.append(faculty_score)

    # Faculty colors
    faculty_colors = {
        faculty: faculties_df.loc[faculties_df["faculty_name"] == faculty, "color"].values[0]
        for faculty in faculties_df["faculty_name"]
    }

    return {
        "sources": [int(x) for x in sources],
        "targets": [int(x) for x in targets],
        "values": [float(x) for x in values],
        "labels": [str(x) for x in labels],
        "faculty_colors": {str(k): str(v) for k, v in faculty_colors.items()},
    }


@router.get("/sankey-data")
def sankey_data():
    """Return data for Sankey chart (faculty, gender, experience, etc.)."""
    data = get_sankey_chart_data()
    return data


@router.get("/faculty/{faculty_name}/normative-distribution")
def get_normative_distribution(faculty_name: str):
    df = surveys_df[surveys_df["faculty_name"] == faculty_name]

    # The column that contains the normative responses
    column = "ia_normative_ub"

    distribution = df["ia_normative_ub"].value_counts().to_dict()

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

    # --- 13 application columns ---
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

    # Map responses (so we can compute means)
    app_map = {
        "I don't know any": 1,
        "I know a few": 2,
        "I know several": 3,
        "I know many": 4,
    }

    for col in app_cols:
        df[col] = df[col].map(app_map)

    # --- Group by the textual IA knowledge labels ---
    grouped = (
        df.groupby("ia_knowledge")[app_cols]
        .mean()
        .reset_index()
    )

    grouped.rename(columns={"ia_knowledge": "knowledge_label"}, inplace=True)
    grouped = grouped.replace([float("inf"), float("-inf")], None).fillna(0)

    # Return the actual textual label
    return grouped.to_dict(orient="records")


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

    # Amplify differences with a mild gamma > 1
    gamma = 1.25  # try
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
        # Note: `colormap` works for SVG too
        colormap="inferno",
    ).generate_from_frequencies(freqs)

    svg = wc.to_svg(embed_font=True)
    # Make it responsive + add hover styling
    svg = svg.replace(
        "<svg ",
        "<svg style='max-width:100%;height:auto' "
    )
    svg = svg.replace(
        "</svg>",
        "<style>text{transition:opacity .15s, filter .15s} text:hover{opacity:.9; filter:drop-shadow(0 0 2px rgba(0,0,0,.25)); cursor:pointer}</style></svg>"
    )
    return Response(content=svg, media_type="image/svg+xml")

# --- NEW: distribution per application (for the radar chart)
@router.get("/faculty/{faculty_name}/knowledge-applications-distribution-count")
def knowledge_app_distribution(
    faculty_name: str,
    app_label: str = Query(..., description="Label from name_map, e.g. 'Text', 'Media', ..."),
    gender: Optional[str] = Query(None),
    experience: Optional[str] = Query(None),
    profile: Optional[str] = Query(None),
):
    # IMPORTANT: use the *raw* survey values (not mapped to 1..4), so we can count categories.
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

    # Categories in a fixed order
    levels = ["I don't know any", "I know a few", "I know several", "I know many"]

    # Count raw strings
    counts = {lvl: int((df[col] == lvl).sum()) for lvl in levels}
    total = int(sum(counts.values()))

    return {"label": app_label, "levels": levels, "counts": counts, "total": total}
