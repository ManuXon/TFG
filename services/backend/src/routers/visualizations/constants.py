from __future__ import annotations

# Shared router constants

FACULTY_KEY_COL = "_faculty_key"

SCORE_COLS = [
    "knowledge_score",
    "uses_score",
    "perceptions_score",
    "training_needs_score",
]

LEVELS_ORDER = ["Not at all", "A little", "Quite a bit", "A lot", "Don't know"]
AGREE4_ORDER = ["Strongly disagree", "Disagree", "Agree", "Strongly agree"]
PROF_ATT_ORDER = ["Prohibit", "Avoid", "Overcome", "Integrate"]

GENDER_ORDER = ["Female", "Male", "Non-binary", "No answer"]
PROFILE_ORDER = ["Senior Lecturer", "Associate", "PreDoc", "PostDoc", "Collab", "Lecturer", "Professor"]
EXPERIENCE_ORDER = ["Less than 5", "Between 5 and 10", "Between 11 and 20", "More than 20"]
MODE_ORDER = ["In-person", "Online", "Hybrid", "In-person+Online", "In-person+Hybrid", "All modes"]


# -------------------------
# Knowledge/Uses task blocks
# (needed by wordclouds + later routes)
# -------------------------

KNOW_APP_COLS = [
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

USES_TASK_COLS = [
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

USES_STUDENT_TASK_COLS = [
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

TASK_SHORT_LABELS = {
    "Text": "Text",
    "Media": "Media",
    "Planning": "Planning",
    "Design": "Design",
    "Activity": "Activity",
    "Evaluation": "Evaluation",
    "Research": "Research",
    "Data": "Data",
    "Translation": "Translation",
    "Analysis": "Analysis",
    "Support": "Support",
    "Experiments": "Experiments",
    "Inclusion": "Inclusion",
}

KNOW_NAME_MAP = {
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

USES_NAME_MAP = {
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

KNOW_APP_MAP_1TO4 = {
    "I don't know any": 1.0,
    "I know a few": 2.0,
    "I know several": 3.0,
    "I know many": 4.0,
}

USES_FREQ_MAP_1TO4 = {
    "Never": 1.0,
    "Sometimes": 2.0,
    "Often": 3.0,
    "Very often": 4.0,
}
