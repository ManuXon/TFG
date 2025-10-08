import os
import pandas as pd
import ast

short_name_mapping = {
    "Belles Arts": "Fine Arts",
    "Biologia": "Biology",
    "Ciències de la Terra": "Earth Sciences",
    "Dret": "Law",
    "Economia i Empresa": "Economics and Bussines",
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
    "Altres": "Others",
    "Prefereixo no contestar": "No answer"
}

teaching_experience_mapping = {
    "Menys de 5 anys": "Less than 5 years",
    "Entre 5 i 10 anys": "Between 5 and 10 years",
    "Entre 10 i 20 anys": "Between 10 and 20 years",
    "Més de 20 anys": "More than 20 years"
}

ub_profile_mapping = {
    "Associat/da": "Associate",
    "PreDoc": "PreDoc",
    "Col·laborador/a permanent": "Permanent Collaborator",
    "Col·laborador/a permanent doctor/a": "Permanent Doctor Collaborator",
    "Lector/a": "Lecturer",
    "PostDoc": "PostDoc",
    "Agregat/da": "Aggregate",
    "Titular": "Tenured",
    "Catedràtic/a": "Professor"
}

teaching_modes_mapping = {
    "Únicament presencial": "Only in-person",
    "Únicament virtual": "Only virtual",
    "Presencial i virtual": "In-person and virtual"
}

ia_knowledge_mapping = {
    "Cap coneixement": "No knowledge",
    "Poc coneixement": "Little knowledge",
    "Bon coneixement": "Good knowledge",
    "Coneixement expert": "Expert knowledge"
}

ia_normative_ub_mapping = {
    "Sí hi ha una normativa o orientació": "Yes, there is a guide or normative",
    "Desconec si hi ha una normativa o orientació": "I ignore if there's a guide or normative",
    "No hi ha una normativa o orientació": "There is no guide or normative",
}

ia_normative_read_mapping = {"Si": "Yes", "No": "No"}

# Interest in AI knowledge for teaching and research
interest_knowledge_teaching_and_research_mapping = {
    "No vull saber res de la IA": "I don't want to know anything",
    "Tinc molt d'interès": "I have a lot of interest",
    "Tinc poc interès": "I have little interest",
    "Tinc un interès moderat": "I have moderate interest"
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
    surveys_path = os.path.join(base_dir, 'survey_responses.csv')
    surveys_df = pd.read_csv(surveys_path)

    surveys_df['faculty_name'] = surveys_df["faculty_name"].map(short_name_mapping)

    # Compute category-specific scores
    freq_mapping = {
        "Diàriament": 9,
        "Setmanalment": 6.5,
        "Esporàdicament": 4,
        "Mai": 1.5
    }

    surveys_df["knowledge_score"] = surveys_df["ia_knowledge"].map({
        "Cap coneixement": 1,
        "Poc coneixement": 3,
        "Bon coneixement": 6,
        "Coneixement expert": 9
    })
    surveys_df["uses_score"] = (surveys_df["frequency_ia_teaching"].map(freq_mapping) +
                                surveys_df["frequency_ia_research"].map(freq_mapping)) / 2
    surveys_df["perceptions_score"] = (surveys_df["importance_teaching"] + surveys_df["importance_research"]) / 2
    surveys_df["training_needs_score"] = surveys_df["interest_in_ia_training"]

    # Apply mappings to translate column values
    surveys_df["gender"] = surveys_df["gender"].map(gender_mapping)
    surveys_df["teaching_experience"] = surveys_df["teaching_experience"].map(teaching_experience_mapping)
    surveys_df["ub_profile"] = surveys_df["ub_profile"].map(ub_profile_mapping)
    surveys_df["teaching_mode"] = surveys_df["teaching_mode"].map(teaching_modes_mapping)
    surveys_df["ia_knowledge"] = surveys_df["ia_knowledge"].map(ia_knowledge_mapping)
    surveys_df["ia_normative_ub"] = surveys_df["ia_normative_ub"].map(ia_normative_ub_mapping)
    surveys_df["ia_normative_read"] = surveys_df["ia_normative_read"].map(ia_normative_read_mapping)
    surveys_df["interest_knowledge_teaching_and_research"] = surveys_df["interest_knowledge_teaching_and_research"].map(
        interest_knowledge_teaching_and_research_mapping)
    surveys_df["knowledge_in_teaching"] = surveys_df["knowledge_in_teaching"].map(knowledge_in_common_mapping)
    surveys_df["knowledge_in_evaluation"] = surveys_df["knowledge_in_evaluation"].map(knowledge_in_common_mapping)
    surveys_df["knowledge_in_material_creation"] = surveys_df["knowledge_in_material_creation"].map(
        knowledge_in_common_mapping)
    surveys_df["knowledge_in_research"] = surveys_df["knowledge_in_research"].map(knowledge_in_common_mapping)

    surveys_df["uses_ia_in_teaching"] = surveys_df["uses_ia_in_teaching"].map(uses_teaching_mapping)
    surveys_df["uses_ia_in_research"] = surveys_df["uses_ia_in_research"].map(uses_research_mapping)
    surveys_df["uses_ia_in_creation"] = surveys_df["uses_ia_in_creation"].map(uses_creation_mapping)
    surveys_df["frequency_ia_teaching"] = surveys_df["frequency_ia_teaching"].map(frequencies_mapping)
    surveys_df["frequency_ia_research"] = surveys_df["frequency_ia_research"].map(frequencies_mapping)
    surveys_df["feelings_about_ia"] = surveys_df["feelings_about_ia"].map(feelings_about_ia_mapping)
    surveys_df["students_ia_opinions"] = surveys_df["students_ia_opinions"].map(students_opinions_mapping)
    surveys_df["faculty_ia_strategy"] = surveys_df["faculty_ia_strategy"].map(faculty_strategies_mapping)
    surveys_df["perceived_ia_impact"] = surveys_df["perceived_ia_impact"].map(perceived_impact_mapping)
    surveys_df["received_training"] = surveys_df["received_training"].map(training_received_mapping)

    return surveys_df
