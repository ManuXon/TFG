from fastapi import APIRouter
import pandas as pd

import numpy as np
from src.utils.data_loader import load_surveys_data, load_faculties_data
import logging

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/api", tags=["Visualizations"])

# Load once at startup
faculties_df = load_faculties_data()
surveys_df = load_surveys_data()

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
def get_spike_map_data(category: str = "All", gender: str | None = None, teaching_experience: str | None = None, ub_profile: str | None = None):
    df = surveys_df.copy()

    if gender:
        df = df[df["gender"] == gender]
    if teaching_experience:
        df = df[df["teaching_experience"] == teaching_experience]
    if ub_profile:
        df = df[df["ub_profile"] == ub_profile]

    if category == "All":
        df["category_score"] = df[["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]].mean(axis=1)
    else:
        category_column = {
            "knowledge": "knowledge_score",
            "uses": "uses_score",
            "perceptions": "perceptions_score",
            "training": "training_needs_score"
        }.get(category, "knowledge_score")
        df["category_score"] = df[category_column]

    faculties_df["color_rgb_tuple"] = faculties_df["color_rgb"].apply(tuple)
    df = df.merge(faculties_df, on="faculty_name", how="left")
    grouped = df.groupby(["faculty_name", "latitude", "longitude", "color", "short_name", "color_rgb_tuple"]).mean(numeric_only=True).reset_index()
    grouped["color_rgb"] = grouped["color_rgb_tuple"].apply(list)
    grouped.drop(columns=["color_rgb_tuple"], inplace=True)

    return grouped.to_dict(orient="records")

@router.get("/faculty/{faculty_name}/knowledge-distribution")
def knowledge_distribution(faculty_name: str):
    df = surveys_df[surveys_df["faculty_name"] == faculty_name]
    levels = ["No knowledge", "Little knowledge", "Good knowledge", "Expert knowledge"]
    counts = [df[df["ia_knowledge"] == lvl].shape[0] for lvl in levels]
    return {"categories": levels, "values": counts}

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

@router.get("/faculty/{faculty_name}/interest-knowledge-link")
def get_interest_knowledge_link(faculty_name: str):
    df = surveys_df[surveys_df["faculty_name"] == faculty_name].copy()

    agreement_map = {
        "Strongly disagree": 1,
        "Disagree": 2,
        "Agree": 3,
        "Strongly agree": 4
    }

    df["interest"] = df["interest_knowledge_teaching_and_research"]
    logger.info(df[["knowledge_in_teaching", "knowledge_in_research"]].head(5).to_string())
    # Normalize + map agreement columns
    for col in [
        "knowledge_in_teaching",
        "knowledge_in_research",
        "knowledge_in_material_creation",
        "knowledge_in_evaluation",
    ]:
        df[col] = df[col].map(agreement_map)

    grouped = (
        df.groupby("interest")[[
            "knowledge_in_teaching",
            "knowledge_in_research",
            "knowledge_in_material_creation",
            "knowledge_in_evaluation"
        ]]
        .mean()
        .reset_index()
    )

    # Clean for JSON serialization
    grouped = grouped.replace([float("inf"), float("-inf")], None).fillna(0)
    grouped = grouped.astype({
        "knowledge_in_teaching": float,
        "knowledge_in_research": float,
        "knowledge_in_material_creation": float,
        "knowledge_in_evaluation": float,
    })

    return grouped.to_dict(orient="records")

