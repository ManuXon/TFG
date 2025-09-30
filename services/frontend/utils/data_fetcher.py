import requests
import pandas as pd
import numpy as np
import os
from typing import List
from utils.data_loader import load_surveys_data, load_faculties_data

BASE_URL = "http://backend:8000"

# Load the faculties and surveys data
faculties_df = load_faculties_data()
surveys_df = load_surveys_data()


def get_treemap_data(gender=None, teaching_experience=None, ub_profile=None):
    # Filter and calculate scores
    df = surveys_df.copy()

    if gender:
        df = df[df["gender"] == gender]
    if teaching_experience:
        df = df[df["teaching_experience"] == teaching_experience]
    if ub_profile:
        df = df[df["ub_profile"] == ub_profile]

    # Calculate overall scores
    df["overall_score"] = df[
        ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]
    ].sum(axis=1)

    df = df.merge(faculties_df, on="faculty_name", how="left")

    # Calculate aggregated faculty scores
    faculty_aggregates = df.groupby("faculty_name")["overall_score"].sum()

    # Create rows for AI dimensions
    treemap_data = pd.DataFrame({
        "parent": np.repeat(df["faculty_name"].values, 4),
        "label": ["Knowledge", "Uses", "Perceptions", "Training"] * len(df),
        "value": df[["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]].values.flatten(),
        "overall_faculty_score": np.repeat(df["faculty_name"].map(faculty_aggregates).values, 4)  # Map and repeat overall scores
    })

    return treemap_data


def get_spike_map_data(category="All", gender=None, teaching_experience=None, ub_profile=None):
    df = surveys_df.copy()

    # Filter based on inputs
    if gender:
        df = df[df["gender"] == gender]

    if teaching_experience:
        df = df[df["teaching_experience"] == teaching_experience]

    if ub_profile:
        df = df[df["ub_profile"] == ub_profile]

    # Default behavior for "All"
    if category == "All":
        df["category_score"] = df[["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]].mean(
            axis=1)
    else:
        category_column = {
            "knowledge": "knowledge_score",
            "uses": "uses_score",
            "perceptions": "perceptions_score",
            "training": "training_needs_score"
        }.get(category, "knowledge_score")
        df["category_score"] = df[category_column]

    # Convert color_rgb list to a tuple for grouping
    faculties_df["color_rgb_tuple"] = faculties_df["color_rgb"].apply(tuple)
    # Merge with faculties data
    df = df.merge(faculties_df, on="faculty_name", how="left")

    # Group by faculty and compute mean scores
    grouped = df.groupby(["faculty_name", "latitude", "longitude", "color", "short_name", "color_rgb_tuple"]).mean(
        numeric_only=True).reset_index()

    # Convert the tuple back to a list after grouping, if needed
    grouped["color_rgb"] = grouped["color_rgb_tuple"].apply(list)
    grouped.drop(columns=["color_rgb_tuple"], inplace=True)

    return grouped


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
        "sources": sources,
        "targets": targets,
        "values": values,
        "labels": labels,
        "faculty_colors": faculty_colors,
    }


def get_all_faculties():
    response = requests.get(f"{BASE_URL}/faculties/")
    if response.status_code == 200:
        return response.json()
    return []


def get_latest_ia_usages():
    response = requests.get(f"{BASE_URL}/ia-usages/")
    if response.status_code == 200:
        return response.json()
    return []


def get_historical_data_by_faculty(faculty_name):
    response = requests.get(f"{BASE_URL}/ia-usage-history/{faculty_name}")
    if response.status_code == 200:
        return response.json()
    return []


def get_all_historical_data():
    response = requests.get(f"{BASE_URL}/ia-usages-history/all")
    if response.status_code == 200:
        response_data = response.json()
        return process_data_for_line_chart_race(response_data)
    return []


def process_data_for_line_chart_race(response_data):
    try:
        flattened_data = [
            {"date": entry['date'], "usage_percentage": entry['usage_percentage'], "faculty": entry['usage']['faculty']}
            for entry in response_data
        ]
        df = pd.DataFrame(flattened_data)
        df['date'] = pd.to_datetime(df['date'])

        # Eliminar filas con valores nulos en las columnas clave
        df.dropna(subset=['faculty', 'usage_percentage', 'date'], inplace=True)
        df = df.sort_values(by=['faculty', 'date']).reset_index(drop=True)
        return df
    except KeyError as e:
        print(f"KeyError encountered: {e}")
        return []
