import pandas as pd
from numpy import random

# Full list of faculties with placeholders for latitude, longitude, and colors
faculties = [
    {"faculty_name": "Belles Arts", "latitude": 41.38317132351853, "longitude": 2.1139582777871375, "color": "#FF5733"},
    {"faculty_name": "Biologia", "latitude": 41.38572816632092, "longitude": 2.120980978633925, "color": "#33FF57"},
    {"faculty_name": "Ciències de la Terra", "latitude": 41.3897, "longitude": 2.1714, "color": "#3357FF"},
    {"faculty_name": "Dret", "latitude": 41.387688071393214, "longitude": 2.120833922012323, "color": "#FF33A1"},
    {"faculty_name": "Economia i Empresa", "latitude": 41.3858676155396, "longitude": 2.1145654558597387, "color": "#33FFA1"},
    {"faculty_name": "Educació", "latitude": 41.3920, "longitude": 2.1224852558481526, "color": "#A133FF"},
    {"faculty_name": "Farmàcia i Ciències de la Alimentació", "latitude": 41.3858676155396, "longitude": 2.1224852558481526,
     "color": "#FFA133"},
    {"faculty_name": "Filologia i Comunicació", "latitude": 41.386471868247035, "longitude": 2.164369079100899, "color": "#33A1FF"},
    {"faculty_name": "Filosofia", "latitude": 41.38410817219821, "longitude": 2.1670053931936284, "color": "#FF5733"},
    {"faculty_name": "Física", "latitude": 41.384533220735484, "longitude": 2.117151348951803, "color": "#A1FF33"},
    {"faculty_name": "Geografia i Història", "latitude": 41.38410737220197, "longitude": 2.166920577761075, "color": "#FF3333"},
    {"faculty_name": "Informació i Mitjans Audiovisuals", "latitude": 41.38149458101953, "longitude": 2.1397775502981404, "color": "#33FF33"},
    {"faculty_name": "Infermeria", "latitude": 41.3464106888224, "longitude": 2.107205775410543, "color": "#337FFF"},
    {"faculty_name": "Matemàtiques i Informàtica", "latitude": 41.38682301856918, "longitude": 2.1643495823158907, "color": "#FF33FF"},
    {"faculty_name": "Medicina i Ciències de la Salut", "latitude": 41.38980566631024, "longitude": 2.1527114796931297, "color": "#333FFF"},
    {"faculty_name": "Psicologia", "latitude": 41.43803951598558, "longitude": 2.143254075318287, "color": "#FFFF33"},
    {"faculty_name": "Química", "latitude": 41.385436421078616, "longitude": 2.118028873552333, "color": "#FF6F33"}
]
pd.DataFrame(faculties).to_csv("faculties.csv", index=False)

# Possible values for survey fields

# Sociodemographic
genders = ["Femení", "Masculí", "No binari", "Altres", "Prefereixo no contestar"]
teaching_experience = ["Menys de 5 anys", "Entre 5 i 10 anys", "Entre 10 i 20 anys", "Més de 20 anys"]
ub_profiles = [
    "Associat/da", "PreDoc", "Col·laborador/a permanent", "Col·laborador/a permanent doctor/a",
    "Lector/a", "PostDoc", "Agregat/da", "Titular", "Catedràtic/a"
]
teaching_modes = ["Únicament presencial", "Únicament virtual", "Presencial i virtual"]

# IA Knowledge
ia_knowledge_levels = ["Cap coneixement", "Poc coneixement", "Bon coneixement", "Coneixement expert"]

ia_normative_ub = ["Sí, hi ha una normativa per estudiants i professorat",
                   "Sí, hi ha una guia amb orientacions per al professorat",
                   "No hi ha cap guia ni cap normativa a la UB",
                   "Ho desconec"]
ia_normative_read = ["Si", "No"]

# IA USES
uses_teaching = [
    "Preparar i planificar les classes", "Crear activitats d'aprenentatge",
    "Crear materials docents", "Avaluar tasques", "Avaluar processos", "No en faig servir"
]
uses_research = [
    "Recollir dades", "Transcripcions", "Anàlisi de dades", "Anàlisi de textos",
    "Visualització de dades", "No en faig servir"
]
uses_creation = [
    "Textos", "Imatges", "Presentacions", "Mapes conceptuals o esquemes",
    "Vídeos", "Situacions d'aprenentatge", "Exàmens o qüestionaris", "No en faig servir"
]
frequencies = ["Diàriament", "Setmanalment", "Esporàdicament", "Mai"]

# PERCEPTIONS
feelings_about_ia = [
    "Analfabet/ta", "Abandonat/da, sense suport", "Sobrepassat/da",
    "Motivat/da", "Engrescat/da", "Més productiu/va"
]

students_opinions = [
    "Usen les IA perquè els hi faci treballs o tasques", "Usen les IA per practicar o auto-avaluar-se",
    "Usen les IA com expert a qui preguntar", "Usen les IA per experimentar amb elles",
    "Per fer resums de llibres o articles", "altres ..."
]
faculty_strategies = [
    "Prohibir-les",
    "Evitar-les",
    "Superar-les",
    "Integrar-les",
    "altres ..."
]
perceived_impact = ["Un fet positiu", "Un fet negatiu"]

# FORMATION
training_received = [
    "No tinc cap formació", "M'he autoformat", "He rebut una formació al meu departament o facultat",
    "He rebut una formació del IDP/ICE", "He rebut una formació fora de la UB",
    "He estat o sóc formador/a d'IA"
]

# Generate survey responses
survey_responses = []
for faculty in faculties:
    for _ in range(10):  # Generate between 5 responses per faculty
        survey_responses.append({
            # SOCIODEMOGRAPHIC
            "age": random.randint(25, 70),
            "gender": random.choice(genders),
            "faculty_name": faculty["faculty_name"],
            "teaching_experience": random.choice(teaching_experience),
            "ub_profile": random.choice(ub_profiles),
            "teaching_mode": random.choice(teaching_modes),
            # KNOWLEDGE
            "ia_knowledge": random.choice(ia_knowledge_levels),
            "ia_normative_ub": random.choice(ia_normative_ub),
            "ia_normative_read": random.choice(ia_normative_read),
            # USES
            "uses_ia_in_teaching": random.choice(uses_teaching),
            "uses_ia_in_research": random.choice(uses_research),
            "uses_ia_in_creation": random.choice(uses_creation),
            "frequency_ia_teaching": random.choice(frequencies),
            "frequency_ia_research": random.choice(frequencies),
            "asks_students_to_use_ia": random.choice(["Sí", "No"]),
            # PERCEPTIONS
            "students_usage_purpose": random.choice(students_opinions),
            "detected_inappropriate_ia_use": random.choice(["Sí", "No"]),
            "made_changes_due_to_ia": random.choice(["Sí", "No"]),
            "students_ia_opinions": random.choice(students_opinions),
            "importance_teaching": random.randint(1, 10),
            "importance_research": random.randint(1, 10),
            "ia_student_agreement": random.randint(1, 4),
            "faculty_ia_strategy": random.choice(faculty_strategies),
            "perceived_ia_impact": random.choice(perceived_impact),
            "feelings_about_ia": random.choice(feelings_about_ia),
            # TRAINING
            "received_training": random.choice(training_received),
            "interest_in_ia_training": random.randint(1, 10),
        })

# Save to CSV
pd.DataFrame(survey_responses).to_csv("survey_responses.csv", index=False)
print("Survey responses CSV generated successfully!")

print("CSV files generated successfully.")
