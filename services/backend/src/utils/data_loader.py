import os
import pandas as pd
import numpy as np
import re
import unicodedata
import ast

from numpy.random import randint


def safe_nanmean(values):
    """
    Like np.nanmean but:
    - filters out None / NaN first
    - returns np.nan if there's nothing left instead of throwing a warning
    """
    clean = [v for v in values if pd.notna(v)]
    if not clean:
        return np.nan
    return float(np.mean(clean))


short_name_mapping = {
    "Belles Arts": "Fine Arts",
    "Biologia": "Biology",
    "Ciències de la Terra": "Earth Sciences",
    "Dret": "Law",
    "Economia i Empresa": "Economics and Business",
    "Educació": "Education",
    "Farmàcia i Ciències de la Alimentació": "Pharmacy",
    "Filologia i Comunicació": "Philology",
    "Filosofia": "Philosophy",
    "Física": "Physics",
    "Geografia i Història": "Geography and History",
    "Informació i Mitjans Audiovisuals": "Audiovisual Media",
    "Infermeria": "Nursing",
    "Matemàtiques i Informàtica": "Maths and CS",
    "Medicina i Ciències de la Salut": "Medicine",
    "Psicologia": "Psychology",
    "Química": "Chemistry"
}

# Translation mappings
gender_mapping = {
    "Femení": "Female",
    "Masculí": "Male",
    "No binari": "Non-binary",
    "Prefereixo no contestar": "No answer"
}

teaching_experience_mapping = {
    "Menys de 5 anys": "Less than 5",
    "Entre 5 i 10 anys": "Between 5 and 10",
    "Entre 11 i 20 anys": "Between 11 and 20",
    "Més de 20 anys": "More than 20"
}

ub_profile_mapping = {
    "Agregat/da o titular": "Senior Lecturer",
    "Associat/da": "Associate",
    "PreDoc": "PreDoc",
    "PostDoc": "PostDoc",
    "Col·laborador/a permanent": "Collab",
    "Lector/a": "Lecturer",
    "Catedràtic/a": "Professor"
}

ia_knowledge_mapping = {
    "Cap coneixement: no conec cap eina, la seva finalitat ni com s'utilitza": "No knowledge",
    "Poc coneixement: conec alguna eina i la seva finalitat, però no tinc coneixement de com s'utilitza": "Little knowledge",
    "Bon coneixement: conec vàries eines i les seves finalitats, tinc coneixement de com s'utilitzen a nivell bàsic": "Good knowledge",
    "Coneixement avançat: conec vàries eines i les seves finalitats, tinc coneixement de com s'utilitzen en profunditat": "Expert knowledge"
}
ia_knowledge_applications_mapping = {
    "En conec algunes": "I know a few",
    "En conec bastantes": "I know several",
    "En conec moltes": "I know many",
    "No en conec cap": "I don't know any"
}

ia_normative_ub_mapping = {
    "Sí hi ha una normativa o orientació": "Yes, there is a guide or normative",
    "Desconec si hi ha una normativa o orientació": "I ignore if there's a guide or normative",
    "No hi ha una normativa o orientació": "There is no guide or normative",
}

# ---------- USES MAPPINGS ----------
# Overall AI use intensity (ia_uses)
ia_uses_mapping = {
    "Cap ús: no utilitzo cap eina": "No use",
    "Poc ús: utilitzo alguna eina": "Low use",
    "Ús moderat: utilitzo bastantes eines": "Moderate use",
    "Ús avançat: utilitzo moltes eines": "Advanced use",
}

# Per-activity frequency
# (all of these: ia_uses_text_creation, ia_uses_multimedia_creation, etc.)
ia_uses_frequency_mapping = {
    "Mai": "Never",
    "Alguna vegada": "Sometimes",
    "Sovint": "Often",
    "Molt sovint": "Very often",
}
# ------------------------------------------------------------------- #
# (this is just to keep English → score conversion easy later)
frequency_points = {
    "Never": 0,
    "Sometimes": 33,
    "Often": 66,
    "Very often": 100,
}

# usage self-eval → score
uses_level_points = {
    "No use": 0,
    "Low use": 33,
    "Moderate use": 66,
    "Advanced use": 100,
}

# knowledge self-eval → score
knowledge_level_points = {
    "No knowledge": 0,
    "Little knowledge": 33,
    "Good knowledge": 66,
    "Expert knowledge": 100,
}

# familiarity with applications (knowledge section “I know ...” answers)
knowledge_app_points = {
    "I don't know any": 0,
    "I know a few": 33,
    "I know several": 66,
    "I know many": 100,
}

# UB normative awareness score (knowledge section)
normative_points = {
    "Yes, there is a guide or normative": 100,
    "I ignore if there's a guide or normative": 50,
    "There is no guide or normative": 0,
}


def compute_row_knowledge_score(row: pd.Series) -> float:
    """
    Build a 0-100 knowledge score for ONE respondent.
    Pieces:
      - self-knowledge level (ia_knowledge)
      - familiarity with AI applications (ia_knowledge_* cols)
      - awareness of UB normative (ia_normative_ub)

    Weight:
      self level            40%
      applications avg      40%
      normative awareness   20%
    """
    # 1. self-reported level
    base_label = row.get("ia_knowledge", None)
    base_score = knowledge_level_points.get(base_label, np.nan)

    # 2. applications familiarity
    knowledge_app_cols = [
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

    app_scores = []
    for col in knowledge_app_cols:
        val = row.get(col, None)
        app_scores.append(knowledge_app_points.get(val, np.nan))

    if len(app_scores):
        apps_avg = safe_nanmean(app_scores)
    else:
        apps_avg = np.nan

    # 3. UB normative awareness
    norm_label = row.get("ia_normative_ub", None)
    norm_score = normative_points.get(norm_label, np.nan)

    # Weighted
    parts = [
        (base_score, 0.4),
        (apps_avg, 0.4),
        (norm_score, 0.2),
    ]

    weighted_scores = []
    weights = []
    for s, w in parts:
        if not (isinstance(s, float) or isinstance(s, int)) or np.isnan(s):
            continue
        weighted_scores.append(s * w)
        weights.append(w)

    if not weights:
        return np.nan

    # normalize so missing parts don't drag it down too unfairly
    total_weight = sum(weights)
    return (sum(weighted_scores) / total_weight)


def compute_row_uses_score(row: pd.Series) -> float:
    """
    Build a 0-100 usage score for ONE respondent.
    Pieces:
      - self-usage level (ia_uses)
      - frequency of using AI for each task (ia_uses_* EXCEPT ia_proposes_students)
      - proposing AI use to students (ia_proposes_students)

    Weight:
      self usage level          40%
      task frequency avg        40%
      proposes_to_students      20%
    """

    # 1. self usage
    use_label = row.get("ia_uses", None)
    use_self_score = uses_level_points.get(use_label, np.nan)

    # 2. tasks frequency
    uses_task_cols = [
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

    task_scores = []
    for col in uses_task_cols:
        freq_label = row.get(col, None)
        task_scores.append(frequency_points.get(freq_label, np.nan))
    tasks_avg = safe_nanmean(task_scores)

    # 3. proposes to students
    prop_label = row.get("ia_proposes_students", None)
    prop_score = frequency_points.get(prop_label, np.nan)

    parts = [
        (use_self_score, 0.4),
        (tasks_avg, 0.4),
        (prop_score, 0.2),
    ]

    weighted_scores = []
    weights = []
    for s, w in parts:
        if not (isinstance(s, float) or isinstance(s, int)) or np.isnan(s):
            continue
        weighted_scores.append(s * w)
        weights.append(w)

    if not weights:
        return np.nan

    total_weight = sum(weights)
    return (sum(weighted_scores) / total_weight)


def df_to_json_safe(df: pd.DataFrame):
    """Convert DataFrame to JSON-safe list of dicts (no NaN/inf, only native Python types)."""
    import numpy as np
    import pandas as pd

    # Replace inf values
    df = df.replace([np.inf, -np.inf], np.nan)
    # Replace all NaN with None
    df = df.where(pd.notnull(df), None)

    # Convert to list of Python-native dicts
    records = df.to_dict(orient="records")
    for row in records:
        for k, v in row.items():
            # Convert NumPy types to Python primitives
            if isinstance(v, (np.generic,)):  # catches np.float64, np.int64, etc.
                row[k] = v.item()
            # Convert NaN-like floats to None
            elif isinstance(v, float) and (v != v or v in [float("inf"), float("-inf")]):
                row[k] = None
    return records


def load_faculties_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of the current script
    faculties_path = os.path.join(base_dir, 'faculties.csv')

    faculties_df = pd.read_csv(faculties_path)

    # Ensure "color" column is converted into RGB values
    def hex_to_rgb(hex_color):
        return [
            int(hex_color[1:3], 16),
            int(hex_color[3:5], 16),
            int(hex_color[5:7], 16),
        ]

    faculties_df["color_rgb"] = faculties_df["color"].apply(hex_to_rgb)
    # Short name mapping

    # Add short names to faculties dataframe
    faculties_df["short_name"] = faculties_df["faculty_name"].map(short_name_mapping)

    faculties_df['faculty_name'] = faculties_df["faculty_name"].map(short_name_mapping)

    return faculties_df


def load_surveys_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    surveys_path = os.path.join(base_dir, 'survey_responses_real.csv')

    surveys_df = pd.read_csv(
        surveys_path,
        sep=";",
        engine="python",
        encoding="latin1",
    )

    def normalize_text(value):
        if not isinstance(value, str):
            return value
        value = value.replace('\xa0', ' ')
        value = value.replace('\x92', "'")
        value = value.replace('\x93', '"').replace('\x94', '"')
        value = value.replace('´', "'")
        value = value.replace("\\'", "'")
        value = unicodedata.normalize("NFC", value)
        value = re.sub(r"\s+", " ", value).strip()
        return value

    surveys_df = surveys_df.applymap(normalize_text)

    drop_cols = [
        "ID", "Hora_d_inici", "Hora_de_finalització", "Correu", "Nom",
        "Hora_de_l_última_modificació", "Consentiment_informat."
    ]
    surveys_df = surveys_df.drop(columns=[c for c in drop_cols if c in surveys_df.columns])

    # Map faculty into English short names
    surveys_df['faculty_name'] = surveys_df["faculty_name"].map(short_name_mapping)

    # Demographics → English
    surveys_df["gender"] = surveys_df["gender"].map(gender_mapping)
    surveys_df["teaching_experience"] = surveys_df["teaching_experience"].map(teaching_experience_mapping)
    surveys_df["ub_profile"] = surveys_df["ub_profile"].map(ub_profile_mapping)

    # Knowledge main question
    surveys_df["ia_knowledge"] = surveys_df["ia_knowledge"].map(ia_knowledge_mapping)

    # Normative
    surveys_df["ia_normative_ub"] = surveys_df["ia_normative_ub"].map(ia_normative_ub_mapping)

    # Knowledge: application familiarity columns
    ia_knowledge_application_columns = [
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
    for col in ia_knowledge_application_columns:
        if col in surveys_df.columns:
            surveys_df[col] = surveys_df[col].map(ia_knowledge_applications_mapping)

    # ---------- USES translation ----------

    # Global AI usage self-report
    if "ia_uses" in surveys_df.columns:
        surveys_df["ia_uses"] = surveys_df["ia_uses"].map(ia_uses_mapping)

    # Per-task usage frequency
    ia_uses_columns = [
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
        "ia_proposes_students",
    ]
    for col in ia_uses_columns:
        if col in surveys_df.columns:
            surveys_df[col] = surveys_df[col].map(ia_uses_frequency_mapping)

    # ---------- Compute scores per row ----------
    surveys_df["knowledge_score"] = surveys_df.apply(compute_row_knowledge_score, axis=1)
    surveys_df["uses_score"] = surveys_df.apply(compute_row_uses_score, axis=1)

    # TODO (later): real logic for these two
    surveys_df["perceptions_score"] = np.random.randint(1, 101, size=len(surveys_df))
    surveys_df["training_needs_score"] = np.random.randint(1, 101, size=len(surveys_df))

    # clean data
    surveys_df.replace(["", " ", "NaN", None], pd.NA, inplace=True)
    surveys_df.dropna(how="all", inplace=True)

    return surveys_df
