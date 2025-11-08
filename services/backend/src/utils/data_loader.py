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
    1: "Fine Arts",
    2: "Biology",
    3: "Earth Sciences",
    4: "Law",
    5: "Economics and Business",
    6: "Education",
    7: "Pharmacy",
    8: "Philology",
    9: "Philosophy",
    10: "Physics",
    11: "Geography and History",
    12: "Audiovisual Media",
    13: "Nursing",
    14: "Maths and CS",
    15: "Medicine",
    16: "Psychology",
    17: "Chemistry"
}

# Translation mappings
gender_mapping = {
    1: "Female",
    2: "Male",
    4: "Non-binary",
    3: "No answer"
}

teaching_experience_mapping = {
    1: "Less than 5",
    2: "Between 5 and 10",
    3: "Between 11 and 20",
    4: "More than 20"
}

ub_profile_mapping = {
    6: "Senior Lecturer",
    1: "Associate",
    2: "PreDoc",
    5: "PostDoc",
    3: "Collab",
    4: "Lecturer",
    7: "Professor"
}

teaching_mode_mapping = {
    1: "In-person",
    2: "Online",
    3: "Hybrid",
    4: "In-person+Online",
    6: "In-person+Hybrid",
    5: "All modes"
}

ia_knowledge_mapping = {
    0: "No knowledge",
    1: "Little knowledge",
    2: "Good knowledge",
    3: "Expert knowledge"
}
ia_knowledge_applications_mapping = {
    1: "I know a few",
    2: "I know several",
    3: "I know many",
    0: "I don't know any"
}

ia_normative_ub_mapping = {
    3: "Yes, there is a guide or normative",
    1: "I ignore if there's a guide or normative",
    2: "There is no guide or normative",
}

# ---------- USES MAPPINGS ----------
# Overall AI use intensity (ia_uses)
ia_uses_mapping = {
    0: "No use",
    1: "Low use",
    2: "Moderate use",
    3: "Advanced use",
}

# Per-activity frequency
# (all of these: ia_uses_text_creation, ia_uses_multimedia_creation, etc.)
ia_uses_frequency_mapping = {
    0: "Never",
    1: "Sometimes",
    2: "Often",
    3: "Very often",
}

ia_uses_adequacy_student_map = {
    1: "Unsure",
    2: "No misuse",
    3: "Appropriate use",
    4: "Occasional misuse",
    5: "Frequent misuse",
}

# --- Students' doc-change (multi-select) ---
ia_uses_docchange_student_mapping = {
    "Sí, he adaptat les activitats d’avaluació per evitar l’ús inadequat de la IA": "Adapted assessments",
    "Sí, he incorporat l’ús de la IA en algunes activitats com a eina de suport a l’aprenentatge": "Added AI as support",
    "Sí, he format els alumnes en l’ús ètic i responsable de la IA": "Ethics training",
    "Sí, he creat normes específiques sobre l’ús de la IA a l’assignatura": "Set course rules",
    "Sí, he prohibit explícitament els alumnes que facin servir les eines IA": "Explicit AI ban",
    "No, però estic considerant fer canvis en el futur": "No, considering changes",
    "No he fet cap canvi, ni ho considero necessari": "No changes",
    "Altres": "Other",
}

# --- Perceptions: "Selecciona les tres funcions..." (multi-select) ---
percep_priorities_mapping = {
    "Comunicar efectivament els continguts essencials per a l'aprenentatge a l'estudiantat": "Communicate",
    "Fomentar la capacitat d’autoregulació en l’aprenentatge de l'estudiantat": "Self-reg",
    "Facilitar el desenvolupament d’habilitats de reflexió, crítiques i analítiques": "Critical",
    "Promoure la participació activa i el debat entre el conjunt d'estudiants": "Participation",
    "Orientar l'estudiantat en l’aplicació pràctica dels coneixements apresos": "Practical",
    "Estimular la col·laboració i el treball en equip": "Collaboration",
    "Adaptar el procés d’aprenentatge a les necessitats individuals de l'estudiantat": "Personalize",
    "Avaluar els aprenentatges de l'estudiantat amb un seguiment i acompanyament de manera contínua": "Assessment",
    "Promoure el disseny, la creació i actualització de continguts i materials innovadors i creatius": "Innovation",
    "Proposar reptes d'aprenentatge per treballar els continguts": "Challenges",
    "Altres": "Other",
}

# Stable axis order for the radar
PERCEP_PRIORITIES_ORDER = [
    "Communicate", "Self-reg", "Critical", "Participation", "Practical",
    "Collaboration", "Personalize", "Assessment", "Innovation", "Challenges", "Other",
]

# (Optional) long descriptions for hover/legend if needed on FE
percep_priorities_long_en = {
    "Communicate": "Communicate essential content",
    "Self-reg": "Foster students' self-regulation",
    "Critical": "Develop reflection/critical/analytical skills",
    "Participation": "Promote active participation & debate",
    "Practical": "Guide practical application of knowledge",
    "Collaboration": "Stimulate collaboration & teamwork",
    "Personalize": "Adapt learning to individual needs",
    "Assessment": "Continuous assessment & accompaniment",
    "Innovation": "Create & update innovative/creative materials",
    "Challenges": "Propose learning challenges",
    "Other": "Other",
}

per_students_use_level_mapping = {
    0: "Not at all",  # Gens
    1: "A little",  # Poc
    2: "Quite a bit",  # Bastant
    3: "A lot",  # Molt
    4: "Don't know",  # No ho sé
}

# Column keys (exact CSV column names with accents)
per_students_use_cols = [
    "PER_IA_ÚSESTUD_1_TREBALLS",
    "PER_IA_ÚSESTUD_2_CONTINGUTS",
    "PER_IA_ÚSESTUD_3_AUTOAVAL",
    "PER_IA_ÚSESTUD_4_BUSCAR",
    "PER_IA_ÚSESTUD_5_PREGEXP",
    "PER_IA_ÚSESTUD_6_EXPER",
    "PER_IA_ÚSESTUD_7_APUNTS",
    "PER_IA_ÚSESTUD_8_RESUMS",
    "PER_IA_ÚSESTUD_9_CODI",
]

# Short axis labels (clean, UI-friendly)
per_students_use_axis_short_en = {
    "PER_IA_ÚSESTUD_1_TREBALLS": "Assignments",
    "PER_IA_ÚSESTUD_2_CONTINGUTS": "Understand content",
    "PER_IA_ÚSESTUD_3_AUTOAVAL": "Self-practice",
    "PER_IA_ÚSESTUD_4_BUSCAR": "Search info",
    "PER_IA_ÚSESTUD_5_PREGEXP": "Ask expert",
    "PER_IA_ÚSESTUD_6_EXPER": "Experiment",
    "PER_IA_ÚSESTUD_7_APUNTS": "Note-taking",
    "PER_IA_ÚSESTUD_8_RESUMS": "Summaries",
    "PER_IA_ÚSESTUD_9_CODI": "Code",
}

# Long labels for hover (more descriptive)
per_students_use_axis_long_en = {
    "PER_IA_ÚSESTUD_1_TREBALLS": "Use AI to do assignments or tasks",
    "PER_IA_ÚSESTUD_2_CONTINGUTS": "Use AI to understand course content",
    "PER_IA_ÚSESTUD_3_AUTOAVAL": "Use AI for practice or self-assessment",
    "PER_IA_ÚSESTUD_4_BUSCAR": "Use AI to search for information",
    "PER_IA_ÚSESTUD_5_PREGEXP": "Use AI to ask an expert-like assistant",
    "PER_IA_ÚSESTUD_6_EXPER": "Use AI to experiment with tools/models",
    "PER_IA_ÚSESTUD_7_APUNTS": "Use AI to take notes",
    "PER_IA_ÚSESTUD_8_RESUMS": "Use AI to summarize books or articles",
    "PER_IA_ÚSESTUD_9_CODI": "Use AI to generate and/or test code",
}

# --- NEW: Students' attitudes toward AI (Likert 1-4) -------------------------
per_students_attitudes_map = {
    1: "Strongly disagree",
    2: "Disagree",
    3: "Agree",
    4: "Strongly agree",
}

# CSV columns (keep exact names — including accents)
per_students_attitudes_cols = [
    "PER_IA_ESTUD_1_XAPROVAR",
    "PER_IA_ESTUD_2_AUTOAPREN",
    "PER_IA_ESTUD_3_ALFAB_IA",
    "PER_IA_ESTUD_4_XAPREN",
    "PER_IA_ESTUD_5_ÈTICA",
    "PER_IA_ESTUD_6_NHPENS",
]

# Short axis labels (concise) for x-axis
per_students_attitudes_short_en = {
    "PER_IA_ESTUD_1_XAPROVAR": "Pass the course",
    "PER_IA_ESTUD_2_AUTOAPREN": "Self-learning boost",
    "PER_IA_ESTUD_3_ALFAB_IA": "AI literacy needed",
    "PER_IA_ESTUD_4_XAPREN": "Not ready to learn w/ AI",
    "PER_IA_ESTUD_5_ÈTICA": "Unaware of ethics",
    "PER_IA_ESTUD_6_NHPENS": "AI makes them not think",
}

# Long hover labels in English
per_students_attitudes_long_en = {
    "PER_IA_ESTUD_1_XAPROVAR": "AI is very useful for students to pass the course.",
    "PER_IA_ESTUD_2_AUTOAPREN": "AI enhances students’ self-learning by offering examples or practice questions.",
    "PER_IA_ESTUD_3_ALFAB_IA": "Being literate in AI is a current necessity.",
    "PER_IA_ESTUD_4_XAPREN": "Students are not ready to use AI for learning.",
    "PER_IA_ESTUD_5_ÈTICA": "Students are not aware of ethical issues with AI.",
    "PER_IA_ESTUD_6_NHPENS": "AI makes students avoid thinking.",
}

# ---- PERCEPTIONS: "Does AI enrich/support...?" (teaching vs research) ----
per_ia_tasks_support_map = {
    1: "Strongly disagree",
    2: "Disagree",
    3: "Agree",
    4: "Strongly agree",
}

# ================== PERCEPTIONS: Professor attitude towards AI ==================
# Numeric -> short English label
per_prof_attitude_mapping = {
    1: "Prohibit",
    2: "Avoid",
    3: "Overcome",
    4: "Integrate",
}

# Short -> long English (tooltip-friendly)
per_prof_attitude_long_en = {
    "Prohibit": "Prohibit AI in teaching–learning",
    "Avoid": "Avoid AI in teaching–learning",
    "Overcome": "Overcome/mitigate AI use",
    "Integrate": "Integrate AI into pedagogy",
}

# ================== PERCEPTIONS: Opportunities & Risks in University ==================
# 1..4 Likert to English
per_agreement4_mapping = {
    1: "Strongly disagree",
    2: "Disagree",
    3: "Agree",
    4: "Strongly agree",
}

# Columns in canonical order
PER_OPORISCUNI_COLS = [
    "PER_IA_OPORISCUNI_1_TRANSDIG",
    "PER_IA_OPORISCUNI_2_NOVESCAP",
    "PER_IA_OPORISCUNI_3_CAPCRIT",
    "PER_IA_OPORISCUNI_4_APRFORA",
    "PER_IA_OPORISCUNI_5_AUGCREAT",
    "PER_IA_OPORISCUNI_6_PRODUCTIV",
    "PER_IA_OPORISCUNI_7_PROB_INTEGACAD",
    "PER_IA_OPORISCUNI_8_BIAXOS_MINET",
    "PER_IA_OPORISCUNI_9_AFAVBIGTEC",
    "PER_IA_OPORISCUNI_10_COMPDADSEN",
    "PER_IA_OPORISCUNI_11_RESPNOFUN",
    "PER_IA_OPORISCUNI_12_ATROFCOG",
]

# Short labels for the X axis (compact, readable)
PER_OPORISCUNI_AXIS_SHORT_EN = {
    "PER_IA_OPORISCUNI_1_TRANSDIG": "Digital transform.",
    "PER_IA_OPORISCUNI_2_NOVESCAP": "New skills",
    "PER_IA_OPORISCUNI_3_CAPCRIT": "Critical thinking",
    "PER_IA_OPORISCUNI_4_APRFORA": "Learning beyond uni",
    "PER_IA_OPORISCUNI_5_AUGCREAT": "Creativity",
    "PER_IA_OPORISCUNI_6_PRODUCTIV": "Productivity",
    "PER_IA_OPORISCUNI_7_PROB_INTEGACAD": "Acad. integrity risk",
    "PER_IA_OPORISCUNI_8_BIAXOS_MINET": "Bias & minorities",
    "PER_IA_OPORISCUNI_9_AFAVBIGTEC": "Big tech interests",
    "PER_IA_OPORISCUNI_10_COMPDADSEN": "Sensitive data sharing",
    "PER_IA_OPORISCUNI_11_RESPNOFUN": "Unfounded answers",
    "PER_IA_OPORISCUNI_12_ATROFCOG": "Cognitive atrophy",
}

# Long labels for hover (full English)
PER_OPORISCUNI_AXIS_LONG_EN = {
    "PER_IA_OPORISCUNI_1_TRANSDIG": "AI is a key step for digital transformation at university",
    "PER_IA_OPORISCUNI_2_NOVESCAP": "AI drives the development of new capacities and skills",
    "PER_IA_OPORISCUNI_3_CAPCRIT": "AI helps develop people’s critical thinking",
    "PER_IA_OPORISCUNI_4_APRFORA": "AI facilitates learning outside the academic environment",
    "PER_IA_OPORISCUNI_5_AUGCREAT": "AI will increase people’s creative capacity",
    "PER_IA_OPORISCUNI_6_PRODUCTIV": "AI makes both faculty and students more productive",
    "PER_IA_OPORISCUNI_7_PROB_INTEGACAD": "AI poses problems for academic honesty and integrity",
    "PER_IA_OPORISCUNI_8_BIAXOS_MINET": "AI implies bias risks, disadvantaging minorities and minoritized languages/cultures",
    "PER_IA_OPORISCUNI_9_AFAVBIGTEC": "AI primarily serves the economic interests of big tech corporations",
    "PER_IA_OPORISCUNI_10_COMPDADSEN": "Using AI tools leads us to share sensitive data with tech companies",
    "PER_IA_OPORISCUNI_11_RESPNOFUN": "AI often delivers answers that aren’t grounded or real",
    "PER_IA_OPORISCUNI_12_ATROFCOG": "AI will cause cognitive atrophy, reducing learning ability",
}

AGREEMENT4_LEVELS = ["Strongly disagree", "Disagree", "Agree", "Strongly agree"]

# ================== TRAINING (multi-select) ==================
# Raw Catalan → short English (used in chart axis)
training_received_short_en = {
    "No tinc cap formació": "No training",
    "M'he autoformat": "Self-taught",
    "He après de companys/es": "From colleagues",
    "He rebut una formació al meu departament o facultat": "Dept/Faculty training",
    "He rebut una formació de l'IDP/ICE": "IDP/ICE training",
    "He rebut una formació fora de la UB": "Outside UB training",
    "He estat o soc formador/a d'IA": "AI trainer",
}

# Short → long English (hover tooltip)
training_received_long_en = {
    "No training": "I have received no training",
    "Self-taught": "I have self-trained on AI",
    "From colleagues": "I have learned from colleagues",
    "Dept/Faculty training": "I have received training in my department or faculty",
    "IDP/ICE training": "I have received training from IDP/ICE",
    "Outside UB training": "I have received training outside UB",
    "AI trainer": "I have been / am an AI trainer",
}

# Canonical display order (stable)
TRAINING_RECEIVED_AXIS = [
    "No training",
    "Self-taught",
    "From colleagues",
    "Dept/Faculty training",
    "IDP/ICE training",
    "Outside UB training",
    "AI trainer",
]

TRAINING_INTEREST_MAP = {
    0: "Not interested at all",
    1: "Low interest",
    2: "Moderate interest",
    3: "High interest",
}

TRAINING_INTEREST_ORDER = [
    "Not interested at all",
    "Low interest",
    "Moderate interest",
    "High interest",
]
# ================== TRAINING: Needs (Likert 1..4) ==================
# Reuse the 1..4 → agreement mapping you already defined for perceptions
# (per_agreement4_mapping and AGREEMENT4_LEVELS)

TRAINING_NEEDS_COLS = [
    "FOR_IA_NECEFORMAT_1_DOC",
    "FOR_IA_NECEFORMAT_2_AVAL",
    "FOR_IA_NECEFORMAT_3_CREAM",
    "FOR_IA_NECEFORMAT_4_REC",
]

# Short axis labels for x-axis
TRAINING_NEEDS_AXIS_SHORT_EN = {
    "FOR_IA_NECEFORMAT_1_DOC":  "Teaching",
    "FOR_IA_NECEFORMAT_2_AVAL": "Assessment",
    "FOR_IA_NECEFORMAT_3_CREAM":"Materials",
    "FOR_IA_NECEFORMAT_4_REC":  "Research",
}

# Long labels for hover (tooltips)
TRAINING_NEEDS_AXIS_LONG_EN = {
    "FOR_IA_NECEFORMAT_1_DOC":  "I have training needs about AI for teaching",
    "FOR_IA_NECEFORMAT_2_AVAL": "I have training needs about AI for assessment",
    "FOR_IA_NECEFORMAT_3_CREAM":"I have training needs about AI for creating materials",
    "FOR_IA_NECEFORMAT_4_REC":  "I have training needs about AI for research",
}


def _normalize_training_multiselect(cell):
    """Split by ';', trim, map to short English, deduplicate preserving order."""
    if pd.isna(cell):
        return []
    tokens = [t.strip() for t in str(cell).split(";") if t.strip()]
    mapped = [training_received_short_en.get(t, None) for t in tokens]
    mapped = [m for m in mapped if m]  # drop unknowns
    seen = set()
    out = []
    for m in mapped:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _normalize_percep_priorities_multiselect(cell):
    if pd.isna(cell):
        return []
    # raw entries separated by ';'
    tokens = [t.strip() for t in str(cell).split(";") if t.strip()]
    mapped = [percep_priorities_mapping.get(t, "Other") for t in tokens]
    # de-duplicate while preserving order
    seen = set();
    out = []
    for m in mapped:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _normalize_docchange_multiselect(cell):
    if pd.isna(cell):
        return []
    tokens = [t.strip() for t in str(cell).split(";") if t.strip()]
    mapped = [ia_uses_docchange_student_mapping.get(t, "Other") for t in tokens]
    # de-duplicate while preserving order
    seen = set()
    uniq = []
    for m in mapped:
        if m not in seen:
            seen.add(m)
            uniq.append(m)
    return uniq


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
    faculties_df['faculty_name'] = faculties_df["faculty_name"].map(short_name_mapping)
    faculties_df["short_name"] = faculties_df["faculty_name"]

    return faculties_df


def load_surveys_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    surveys_path = os.path.join(base_dir, 'BD_MAPAI_UB_final299.csv')

    surveys_df = pd.read_csv(
        surveys_path,
        sep=",",
        engine="python",
        encoding="utf-8-sig",
    )

    drop_cols = [
        "ID", "PARTICIPAR"
    ]
    surveys_df = surveys_df.drop(columns=[c for c in drop_cols if c in surveys_df.columns])

    # Map faculty into English short names
    surveys_df['faculty_name'] = surveys_df["faculty_name"].map(short_name_mapping)

    # Demographics → English
    surveys_df["gender"] = surveys_df["gender"].map(gender_mapping).fillna("No answer")
    surveys_df["teaching_experience"] = surveys_df["teaching_experience"].map(teaching_experience_mapping)
    surveys_df["ub_profile"] = surveys_df["ub_profile"].map(ub_profile_mapping)
    surveys_df["teaching_mode"] = surveys_df["teaching_mode"].map(teaching_mode_mapping)

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

    # Students uses
    ia_uses_students_columns = [
        "ia_uses_text_creation_student",
        "ia_uses_multimedia_creation_student",
        "ia_uses_activity_design_student",
        "ia_uses_evaluation_student",
        "ia_uses_research_management_student",
        "ia_uses_data_collection_student",
        "ia_uses_transcription_translation_student",
        "ia_uses_data_analysis_student",
        "ia_uses_technical_support_student",
        "ia_uses_ai_experiments_student",
        "ia_uses_inclusion_support_student",
    ]
    for col in ia_uses_students_columns:
        if col in surveys_df.columns:
            surveys_df[col] = surveys_df[col].map(ia_uses_frequency_mapping)

    surveys_df["ia_uses_adequacy_student"] = surveys_df["ia_uses_adequacy_student"].map(ia_uses_adequacy_student_map)
    # Map the multi-select column into a list of short English labels
    if "ia_uses_docchange_student" in surveys_df.columns:
        surveys_df["ia_uses_docchange_student_list"] = surveys_df["ia_uses_docchange_student"].apply(
            _normalize_docchange_multiselect
        )
    else:
        surveys_df["ia_uses_docchange_student_list"] = [[] for _ in range(len(surveys_df))]

    if "ia_perceptions_doc_priority" in surveys_df.columns:
        surveys_df["ia_perceptions_doc_priority_list"] = surveys_df["ia_perceptions_doc_priority"].apply(
            _normalize_percep_priorities_multiselect)
    else:
        # keep shape consistent even if column missing
        surveys_df["ia_perceptions_doc_priority_list"] = [[] for _ in range(len(surveys_df))]

    # Perceptions: map 0..4 → English level strings
    for col in per_students_use_cols:
        if col in surveys_df.columns:
            surveys_df[col] = surveys_df[col].map(per_students_use_level_mapping)

    # --- Perceptions: students' attitudes (Likert 1..4) ---
    for col in per_students_attitudes_cols:
        if col in surveys_df.columns:
            surveys_df[col] = surveys_df[col].map(per_students_attitudes_map)

    # Map "Creus que la IA enriqueix o dona suport" items (teaching/research)
    # Raw CSV cols: PER_IA_TASQUES_1_DOC, PER_IA_TASQUES_2_REC (values 1..4)
    if "PER_IA_TASQUES_1_DOC" in surveys_df.columns:
        surveys_df["per_ia_tasks_doc"] = surveys_df["PER_IA_TASQUES_1_DOC"].map(per_ia_tasks_support_map)

    if "PER_IA_TASQUES_2_REC" in surveys_df.columns:
        surveys_df["per_ia_tasks_rec"] = surveys_df["PER_IA_TASQUES_2_REC"].map(per_ia_tasks_support_map)

    if "PER_IA_POSICPROF_PROH_EV_SUP_INT":
        surveys_df["PER_IA_POSICPROF_PROH_EV_SUP_INT"] = surveys_df["PER_IA_POSICPROF_PROH_EV_SUP_INT"].map(
            per_prof_attitude_mapping)

    # -------- Perceptions: Opportunities & Risks in University (Likert 1..4) ------
    for col in PER_OPORISCUNI_COLS:
        if col in surveys_df.columns:
            surveys_df[col] = surveys_df[col].map(per_agreement4_mapping)

    # -------- TRAINING: multi-select normalization --------
    if "FOR_IA_FORMACIO_DOCREC" in surveys_df.columns:
        surveys_df["training_received_list"] = surveys_df["FOR_IA_FORMACIO_DOCREC"].apply(_normalize_training_multiselect)

    # -------- TRAINING: Needs (Likert 1..4) → English labels --------
    for col in TRAINING_NEEDS_COLS:
        if col in surveys_df.columns:
            surveys_df[col] = surveys_df[col].map(per_agreement4_mapping)

    # ---------- Compute scores per row ----------
    surveys_df["knowledge_score"] = surveys_df.apply(compute_row_knowledge_score, axis=1)
    surveys_df["uses_score"] = surveys_df.apply(compute_row_uses_score, axis=1)

    # TODO (later): real logic for these two
    surveys_df["perceptions_score"] = np.random.randint(1, 101, size=len(surveys_df))
    surveys_df["training_needs_score"] = np.random.randint(1, 101, size=len(surveys_df))

    # clean data
    surveys_df.replace(["", " ", "NaN", None], pd.NA, inplace=True)
    surveys_df.dropna(how="all", inplace=True)
    col = surveys_df['ia_uses_docchange_student']

    uvals = (col.dropna().astype(str).unique())
    for i, v in enumerate(uvals, 1):
        print(f"{i:2d}. {v}")

    return surveys_df
