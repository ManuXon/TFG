import os
import pandas as pd
import numpy as np
import re
import unicodedata
import ast

from numpy.random import randint

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

# Interest in AI knowledge for teaching and research
interest_knowledge_teaching_and_research_mapping = {
    "No vull saber res de la IA": "No interest",
    "Tinc molt d'interès": "High interest",
    "Tinc poc interès": "Low interest",
    "Tinc un interès moderat": "Medium interest"
}

# Knowledge about AI in teaching
knowledge_in_common_mapping = {
    "D'acord": "Agree",
    "En desacord": "Disagree",
    "Molt d'acord": "Strongly agree",
    "Molt en desacord": "Strongly disagree"
}

uses_teaching_mapping = {
    "Preparar i planificar les classes": "Prepare and plan classes",
    "Crear activitats d'aprenentatge": "Create learning activities",
    "Crear materials docents": "Create teaching materials",
    "Avaluar tasques": "Evaluate tasks",
    "Avaluar processos": "Evaluate processes",
    "No en faig servir": "I don't use it"
}

uses_research_mapping = {
    "Recollir dades": "Collect data",
    "Transcripcions": "Transcriptions",
    "Anàlisi de dades": "Data analysis",
    "Anàlisi de textos": "Text analysis",
    "Visualització de dades": "Data visualization",
    "No en faig servir": "I don't use it"
}

uses_creation_mapping = {
    "Textos": "Texts",
    "Imatges": "Images",
    "Presentacions": "Presentations",
    "Mapes conceptuals o esquemes": "Concept maps or diagrams",
    "Vídeos": "Videos",
    "Situacions d'aprenentatge": "Learning scenarios",
    "Exàmens o qüestionaris": "Exams or quizzes",
    "No en faig servir": "I don't use it"
}

frequencies_mapping = {
    "Diàriament": "Daily",
    "Setmanalment": "Weekly",
    "Esporàdicament": "Occasionally",
    "Mai": "Never"
}

feelings_about_ia_mapping = {
    "Analfabet/ta": "Illiterate",
    "Abandonat/da, sense suport": "Abandoned, without support",
    "Sobrepassat/da": "Overwhelmed",
    "Motivat/da": "Motivated",
    "Engrescat/da": "Encouraged",
    "Més productiu/va": "More productive"
}

students_opinions_mapping = {
    "Usen les IA perquè els hi faci treballs o tasques": "They use AI to do their work or tasks",
    "Usen les IA per practicar o auto-avaluar-se": "They use AI to practice or self-assess",
    "Usen les IA com expert a qui preguntar": "They use AI as an expert to ask questions",
    "Usen les IA per experimentar amb elles": "They use AI to experiment",
    "Per fer resums de llibres o articles": "To summarize books or articles",
    "altres ...": "others ..."
}

faculty_strategies_mapping = {
    "Prohibir-les": "Prohibit them",
    "Evitar-les": "Avoid them",
    "Superar-les": "Surpass them",
    "Integrar-les": "Integrate them",
    "altres ...": "others ..."
}

perceived_impact_mapping = {
    "Un fet positiu": "A positive impact",
    "Un fet negatiu": "A negative impact"
}

training_received_mapping = {
    "No tinc cap formació": "I have no training",
    "M'he autoformat": "I am self-trained",
    "He rebut una formació al meu departament o facultat": "I have received training in my department or faculty",
    "He rebut una formació del IDP/ICE": "I have received training from IDP/ICE",
    "He rebut una formació fora de la UB": "I have received training outside UB",
    "He estat o sóc formador/a d'IA": "I have been or am an AI trainer"
}


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
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of the current script
    surveys_path = os.path.join(base_dir, 'survey_responses_real.csv')
    # --- Read CSV (choose UTF-8-SIG if possible) ---
    surveys_df = pd.read_csv(
        surveys_path,
        sep=";",
        engine="python",
        encoding="latin1",  # try utf-8-sig first
    )

    def normalize_text(value):
        """Normalize encoding, accents, and hidden chars for consistent mappings."""
        if not isinstance(value, str):
            return value

        # Fix common encoding errors
        value = value.replace('\xa0', ' ')  # non-breaking spaces
        value = value.replace('\x92', "'")  # weird apostrophes
        value = value.replace('\x93', '"').replace('\x94', '"')  # quotes
        value = value.replace('´', "'")  # weird accent quote
        value = value.replace("\\'", "'")  # escaped apostrophes

        # Normalize unicode accents (é, è, ç, ñ, etc.)
        value = unicodedata.normalize("NFC", value)

        # Collapse multiple spaces and trim
        value = re.sub(r"\s+", " ", value).strip()
        return value

    # Apply cleaning only to data (not column names)
    surveys_df = surveys_df.applymap(normalize_text)

    # Drop metadata columns if present
    drop_cols = [
        "ID", "Hora_d_inici", "Hora_de_finalització", "Correu", "Nom",
        "Hora_de_l_última_modificació", "Consentiment_informat."
    ]
    surveys_df = surveys_df.drop(columns=[c for c in drop_cols if c in surveys_df.columns])

    # JUST TO CHECK VALUES ON CONSOLE -- REMOVE LATER
    pd.set_option('display.max_columns', None)  # Show all columns
    pd.set_option('display.max_colwidth', None)  # Don't truncate long text cells
    pd.set_option('display.width', None)  # Allow unlimited line width

    print(surveys_df["faculty_name"].value_counts(dropna=False))
    # -- REMOVE TILL HERE.
    surveys_df['faculty_name'] = surveys_df["faculty_name"].map(short_name_mapping)

    surveys_df["uses_score"] = np.random.randint(1, 101, size=len(surveys_df))
    surveys_df["perceptions_score"] = np.random.randint(1, 101, size=len(surveys_df))
    surveys_df["training_needs_score"] = np.random.randint(1, 101, size=len(surveys_df))

    # Apply mappings to translate column values
    surveys_df["gender"] = surveys_df["gender"].map(gender_mapping)
    surveys_df["teaching_experience"] = surveys_df["teaching_experience"].map(teaching_experience_mapping)
    surveys_df["ub_profile"] = surveys_df["ub_profile"].map(ub_profile_mapping)

    # Knowledge
    surveys_df["ia_knowledge"] = surveys_df["ia_knowledge"].map(ia_knowledge_mapping)
    surveys_df["ia_normative_ub"] = surveys_df["ia_normative_ub"].map(ia_normative_ub_mapping)

    # IA Knowledge Applications (apply English mapping to all related columns)
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

    surveys_df["knowledge_score"] = surveys_df["ia_knowledge"].map({
        "No knowledge": 10,
        "Little knowledge": 30,
        "Good knowledge": 60,
        "Expert knowledge": 90
    })

    # Clean data
    surveys_df.replace(["", " ", "NaN", None], pd.NA, inplace=True)
    surveys_df.dropna(how="all", inplace=True)

    return surveys_df
