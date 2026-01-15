# MapAI Survey Dataset Documentation (SURVEYS_DF)

## What this dataset is
This dataset contains survey responses from University of Barcelona (UB) teaching staff about:
- Knowledge of AI tools and applications
- Uses of AI tools in teaching/research
- Uses that professors propose/allow for students
- Perceptions about students' AI usage and broader opportunities/risks
- Training needs and interest in training
- Precomputed section scores (0–100)

Each row is a single respondent.

Important:
- Many columns are categorical strings (Likert-style answers).
- Some columns contain uppercase names with accents (e.g., `PER_IA_ÚSESTUD_1_TREBALLS`). Treat them as exact column names.
- Open-text columns exist in the dataset, but analysis should avoid them unless the user explicitly requests qualitative text analysis.

---

## Key “identity / grouping” columns (commonly used for filtering)
Common filter columns (names may vary depending on your pipeline):
- `faculty_name`: faculty label (e.g., "Medicine", "Biology", etc.)
- `gender`
- `teaching_experience`
- `ub_profile`

Use `faculty_name` for faculty comparisons.

---

## Scores (0–100)
These are numeric columns already computed from their respective sections. This represents the overall numeric value of
that category. When asked about a certain section (knowledge, uses, perceptions and training needs)  always use the scores to
represent the overall computation. Then you can use the different columns for each section to give a more detailed answer.

- `knowledge_score`: higher = more knowledge of AI applications.
- `uses_score`: higher = more frequent/broader use of AI applications.
- `perceptions_score`: higher = more positive perceptions / more agreement with perception items.
- `training_needs_score`: higher = greater training need / interest / expressed need.

When asked “which faculty has higher X”, compute distributions on these columns, optionally filtering by demographics.

---

## Knowledge section columns (`ia_knowledge*`)
These represent knowledge level of AI applications. Higher means “knows more”.

Base/overall:
- `ia_knowledge`

Specific knowledge areas:
- `ia_knowledge_text_creation`
- `ia_knowledge_multimedia_creation`
- `ia_knowledge_class_planning`
- `ia_knowledge_material_design`
- `ia_knowledge_activity_design`
- `ia_knowledge_evaluation`
- `ia_knowledge_research_management`
- `ia_knowledge_data_collection`
- `ia_knowledge_transcription_translation`
- `ia_knowledge_data_analysis`
- `ia_knowledge_technical_support`
- `ia_knowledge_ai_experiments`
- `ia_knowledge_inclusion_support`

---

## Uses section columns (`ia_uses*`)
These represent actual use of AI applications by the professor.

Base/overall:
- `ia_uses`

Specific use areas:
- `ia_uses_text_creation`
- `ia_uses_multimedia_creation`
- `ia_uses_class_planning`
- `ia_uses_material_design`
- `ia_uses_activity_design`
- `ia_uses_evaluation`
- `ia_uses_research_management`
- `ia_uses_data_collection`
- `ia_uses_transcription_translation`
- `ia_uses_data_analysis`
- `ia_uses_technical_support`
- `ia_uses_ai_experiments`
- `ia_uses_inclusion_support`

Tools (if present):
- `ia_uses_tools`

---

## Student-related uses (columns ending with `_student`)
These are NOT “professor uses”, but rather what professors propose/allow/recommend students do with AI.

General:
- `ia_proposes_students`

Specific student uses:
- `ia_uses_text_creation_student`
- `ia_uses_multimedia_creation_student`
- `ia_uses_activity_design_student`
- `ia_uses_evaluation_student`
- `ia_uses_research_management_student`
- `ia_uses_data_collection_student`
- `ia_uses_transcription_translation_student`
- `ia_uses_data_analysis_student`
- `ia_uses_technical_support_student`
- `ia_uses_ai_experiments_student`
- `ia_uses_inclusion_support_student`

Additional student-related items:
- `ia_uses_adequacy_student` (whether professors feel how adequate is the students use of AI)
- `ia_uses_docchange_student` (whether professors changed teaching plan/structure to accommodate AI use)

Rule:
- Always distinguish “professor uses” vs “proposes students use”.

---

## Perceptions section columns (`PER_*` / perception-related)
These capture perceptions about student AI usage and broader implications.

Example column meanings:
- `ia_perceptions_doc_priority`: how the professor prioritizes or views AI relative to teaching.

Student use perceptions:
- `PER_IA_ÚSESTUD_1_TREBALLS` (students use AI for assignments/tasks)
- `PER_IA_ÚSESTUD_2_CONTINGUTS`
- `PER_IA_ÚSESTUD_3_AUTOAVAL`
- `PER_IA_ÚSESTUD_4_BUSCAR`
- `PER_IA_ÚSESTUD_5_PREGEXP`
- `PER_IA_ÚSESTUD_6_EXPER`
- `PER_IA_ÚSESTUD_7_APUNTS`
- `PER_IA_ÚSESTUD_8_RESUMS`
- `PER_IA_ÚSESTUD_9_CODI`

Student outcomes / literacy / ethics:
- `PER_IA_ESTUD_1_XAPROVAR`
- `PER_IA_ESTUD_2_AUTOAPREN`
- `PER_IA_ESTUD_3_ALFAB_IA`
- `PER_IA_ESTUD_4_XAPREN`
- `PER_IA_ESTUD_5_ÈTICA`
- `PER_IA_ESTUD_6_NHPENS`

Tasks and opportunities/risks:
- `PER_IA_TASQUES_1_DOC`
- `PER_IA_TASQUES_2_REC`
- `PER_IA_OPORISCUNI_1_TRANSDIG`
- `PER_IA_OPORISCUNI_2_NOVESCAP`
- `PER_IA_OPORISCUNI_3_CAPCRIT`
- `PER_IA_OPORISCUNI_4_APRFORA`
- `PER_IA_OPORISCUNI_5_AUGCREAT`
- `PER_IA_OPORISCUNI_6_PRODUCTIV`
- `PER_IA_OPORISCUNI_7_PROB_INTEGACAD`
- `PER_IA_OPORISCUNI_8_BIAXOS_MINET`
- `PER_IA_OPORISCUNI_9_AFAVBIGTEC`
- `PER_IA_OPORISCUNI_10_COMPDADSEN`
- `PER_IA_OPORISCUNI_11_RESPNOFUN`
- `PER_IA_OPORISCUNI_12_ATROFCOG`
- `PER_IA_OPORISCUNI_ALTRES`

Positioning / justification:
- `PER_IA_POSICPROF_PROH_EV_SUP_INT`
- `PER_IA_POSICPROF_PERQUE`

---

## Training needs section (`FOR_*`)
Training interest and needs.

- `FOR_IA_FORMACIO_DOCREC`
- `FOR_IA_INTERES`
- `FOR_IA_NECEFORMAT_1_DOC`
- `FOR_IA_NECEFORMAT_2_AVAL`
- `FOR_IA_NECEFORMAT_3_CREAM`
- `FOR_IA_NECEFORMAT_4_REC`
- `FOR_IA_NECEFORMAT_ALTRES`

Interpretation:
- Higher agreement / stronger need -> higher `training_needs_score`.

---

## How the assistant should answer
- If the user asks for ANY number: use dataset analysis (compute it).
- If asked to compare faculties: group by `faculty_name` and report counts + means + (optionally) medians.
- Always handle missing values and report sample sizes (n).
- Do not claim causality from correlation.
