# services/backend/src/chatbot/agent.py
from __future__ import annotations
import os, logging, re, textwrap, io, contextlib, unicodedata
from typing import Optional, List, Dict, Set, Tuple, Any
import pandas as pd
from openai import OpenAI


try:
    from src.utils.open_text_agent import load_open_text_analysis
except Exception:
    load_open_text_analysis = None

logger = logging.getLogger(__name__)

try:
    import src.utils.tools_normalizer as tn  # your file: tools_normalizer.py

    _TOOLS_NORMALIZER_OK = True
except Exception as _e:
    logger.warning("[chatbot] tools_normalizer not available; falling back to simple splitter: %s", _e)
    _TOOLS_NORMALIZER_OK = False
    tn = None  # sentinel

# =================== POINT MAPS ===================
FREQ_POINTS = {"Never": 0, "Sometimes": 33, "Often": 66, "Very often": 100}
USES_LEVEL_POINTS = {"No use": 0, "Low use": 33, "Moderate use": 66, "Advanced use": 100}
KNOW_LEVEL_POINTS = {"No knowledge": 0, "Little knowledge": 33, "Good knowledge": 66, "Expert knowledge": 100}
KNOW_APP_POINTS = {"I don't know any": 0, "I know a few": 33, "I know several": 66, "I know many": 100}

AGREEMENT4_LEVELS = ["Strongly disagree", "Disagree", "Agree", "Strongly agree"]
AGREEMENT4_POINTS = {"Strongly disagree": 0, "Disagree": 33, "Agree": 66, "Strongly agree": 100}

# Students' self-reported use fixed order
STUDENTS_USE_LEVELS = ["Not at all", "A little", "Quite a bit", "A lot", "Don't know"]

NORMATIVE_POINTS = {
    "Yes, there is a guide or normative": 100,
    "I ignore if there's a guide or normative": 50,
    "There is no guide or normative": 0,
}

DERIVED_COLS = [
    "ia_uses_docchange_student_list",
    "ia_perceptions_doc_priority_list",
    "training_received_list",
    "per_ia_tasks_doc", "per_ia_tasks_rec",
    "knowledge_score", "uses_score", "perceptions_score", "training_needs_score",
    "per_ia_oporiscuni_altres_text", "per_ia_posicprof_perque_text", "for_ia_neceformat_altres_text",
    "comments_text",
    "row_id",
]

KNOW_APP_COLS = [
    "ia_knowledge_text_creation", "ia_knowledge_multimedia_creation", "ia_knowledge_class_planning",
    "ia_knowledge_material_design", "ia_knowledge_activity_design", "ia_knowledge_evaluation",
    "ia_knowledge_research_management", "ia_knowledge_data_collection",
    "ia_knowledge_transcription_translation", "ia_knowledge_data_analysis",
    "ia_knowledge_technical_support", "ia_knowledge_ai_experiments",
    "ia_knowledge_inclusion_support",
]
USES_FREQ_COLS = [
    "ia_uses_text_creation", "ia_uses_multimedia_creation", "ia_uses_class_planning",
    "ia_uses_material_design", "ia_uses_activity_design", "ia_uses_evaluation",
    "ia_uses_research_management", "ia_uses_data_collection", "ia_uses_transcription_translation",
    "ia_uses_data_analysis", "ia_uses_technical_support", "ia_uses_ai_experiments",
    "ia_uses_inclusion_support", "ia_proposes_students",
]

LIKERT_ORDER = ["Molt d'acord", "D'acord", "Ni d'acord ni en desacord", "En desacord", "Molt en desacacord"]
LIKERT_ALT = ["Totalment d'acord", "D'acord", "Neutral", "En desacord", "Totalment en desacacord"]

PER_OPORISCUNI_PREFIX = "PER_IA_OPORISCUNI_"
TRAINING_PREFIX = "FOR_IA_"

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

TRAINING_NEEDS_COLS = [
    "FOR_IA_NECEFORMAT_1_DOC",
    "FOR_IA_NECEFORMAT_2_AVAL",
    "FOR_IA_NECEFORMAT_3_CREAM",
    "FOR_IA_NECEFORMAT_4_REC",
]
TRAINING_NEEDS_AXIS_SHORT_EN = {
    "FOR_IA_NECEFORMAT_1_DOC": "Teaching",
    "FOR_IA_NECEFORMAT_2_AVAL": "Assessment",
    "FOR_IA_NECEFORMAT_3_CREAM": "Materials",
    "FOR_IA_NECEFORMAT_4_REC": "Research",
}

# =================== SMALL UTILS ===================
_CODEBLOCK_RE = re.compile(r"```(?:\s*(?P<lang>[a-zA-Z0-9_+-]+))?\s*\n(?P<body>[\s\S]*?)```", re.MULTILINE)


def _extract_python_code(content: str) -> str:
    if not content: return ""
    m = _CODEBLOCK_RE.search(content)
    if m:
        body = m.group("body") or ""
        lines = body.splitlines()
        while lines and not lines[0].strip(): lines.pop(0)
        if lines and lines[0].strip().lower() in {"python", "py"}: lines = lines[1:]
        return "\n".join(lines).strip()
    raw = (content or "").strip()
    if raw.lstrip().lower().startswith(("python", "py")):
        raw = "\n".join(raw.splitlines()[1:])
    return raw.strip()


def _fold(s: str) -> str:
    if s is None: return ""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
    return s.lower().strip()


def _norm(s: str) -> str:
    import re as _re
    return _re.sub(r"\s+", " ", str(s or "")).strip()


def _group_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
    cols = df.columns
    groups = {
        "core": [c for c in
                 ["ID", "age", "gender", "faculty_name", "teaching_experience", "ub_profile", "teaching_mode"] if
                 c in cols],
        "knowledge_all": [c for c in cols if c.startswith("ia_knowledge")],
        "uses_all": [c for c in cols if c.startswith("ia_uses_")] + (["ia_uses"] if "ia_uses" in cols else []),
        "per_oporisc": [c for c in cols if c.startswith(PER_OPORISCUNI_PREFIX)],
        "for_all": [c for c in cols if c.startswith(TRAINING_PREFIX)],
        "free_text": [c for c in ["CONEIX_IA_ALTRESFUNC", "ÚS_IA_ALTRESUSOS", "PER_IA_OPORISCUNI_ALTRES",
                                  "PER_IA_POSICPROF_PERQUE", "FOR_IA_NECEFORMAT_ALTRES", "COMENTARIS"] if c in cols],
        "policy": [c for c in
                   ["ia_normative_ub", "ia_proposes_students", "ia_uses_tools", "ia_perceptions_doc_priority",
                    "PARTICIPAR"] if c in cols],
    }
    return groups


def _manifest(df: pd.DataFrame) -> str:
    g = _group_columns(df)
    lines = [f"DataFrame present: rows={len(df)}, cols={len(df.columns)}"]
    for name in ["core", "knowledge_all", "uses_all", "per_oporisc", "for_all", "policy", "free_text"]:
        cols = g.get(name, [])
        if cols: lines.append(f"{name}({len(cols)}): {cols[:20]}")
    if "faculty_name" in df.columns:
        lines.append(f"faculty_name sample: {df['faculty_name'].value_counts().head(5).to_dict()}")
    if "gender" in df.columns:
        lines.append(f"gender sample: {df['gender'].value_counts().head(5).to_dict()}")
    derived_existing = [c for c in DERIVED_COLS if c in df.columns]
    if derived_existing:
        lines.append(f"derived_present({len(derived_existing)}): {derived_existing}")
    return "\n".join(lines)


_FRIENDLY = {
    "ia_knowledge": "overall knowledge (0–100)",
    "ia_uses": "overall use (0–100)",
    "knowledge_score": "overall knowledge (0–100)",
    "uses_score": "overall use (0–100)",
    "per_ia_tasks_doc": "AI support for tasks in teaching (0–100)",
    "per_ia_tasks_rec": "AI support for tasks in research (0–100)",
    "ub_profile": "teaching staff profile",
    "faculty_name": "faculty",
    "teaching_experience": "teaching experience",
    "teaching_mode": "teaching mode",
    "gender": "gender",
}
_PREFIX_FRIENDLY = {
    "ia_knowledge_": "knowledge of",
    "ia_uses_": "use of",
    "PER_IA_ESTUD_": "attitudes about AI & students",
    "PER_IA_OPORISCUNI_": "opportunities & risks in university",
    "FOR_IA_NECEFORMAT_": "training needs on",
}


def _humanize_text(s: str) -> str:
    if not s: return s
    out = s
    for k, v in _FRIENDLY.items():
        out = re.sub(rf"\b{k}\b", v, out)
    for pref, label in _PREFIX_FRIENDLY.items():
        out = re.sub(rf"\b{pref}([A-Za-z0-9_]+)", lambda m: f"{label} {m.group(1).lower()}", out)
    out = out.replace("_student", " (student-directed)").replace("_doc", " (teaching)").replace("_rec", " (research)")
    for k, v in PER_OPORISCUNI_AXIS_SHORT_EN.items(): out = out.replace(k, v)
    for k, v in TRAINING_NEEDS_AXIS_SHORT_EN.items(): out = out.replace(k, v)
    return out


# =================== METRIC ROUTING ===================
METRIC_ALIASES: Dict[str, str] = {
    "overall_knowledge": "knowledge_score",
    "general_knowledge": "knowledge_score",
    "knowledge_overall": "knowledge_score",
    "knowledge": "knowledge_score",
    "ai_knowledge": "knowledge_score",
    "gai_knowledge": "knowledge_score",
    "overall_use": "uses_score",
    "general_use": "uses_score",
    "use_overall": "uses_score",
    "usage": "uses_score",
    "uses": "uses_score",
    "ai_use": "uses_score",
    "gai_use": "uses_score",
    "perceptions_overall": "perceptions_score",
    "training_needs_overall": "training_needs_score",
}


def _nan_series_like(df_like: pd.DataFrame | None) -> pd.Series:
    n = len(df_like) if isinstance(df_like, pd.DataFrame) else 0
    return pd.Series([float("nan")] * n, index=(df_like.index if isinstance(df_like, pd.DataFrame) else None),
                     dtype="float64")


def _resolve_metric_impl(metric_hint: str) -> str:
    if not metric_hint: return "knowledge_score"
    key = str(metric_hint).strip().lower().replace(" ", "_")
    return METRIC_ALIASES.get(key, metric_hint)


def _agreement4_to_points_series(s: pd.Series) -> pd.Series:
    return s.map(AGREEMENT4_POINTS).astype("float64")


def _ensure_agreement4_numeric(df: pd.DataFrame, df_num: Optional[pd.DataFrame], col: str) -> pd.Series:
    if df_num is not None and col in df_num.columns:
        ser = pd.to_numeric(df_num[col], errors="coerce")
        if ser.notna().any(): return ser
    if col in df.columns:
        return _agreement4_to_points_series(df[col])
    return pd.Series([], dtype="float64")


def _teach_research_overview_impl(df: pd.DataFrame, df_num: Optional[pd.DataFrame],
                                  mask: Optional[pd.Series] = None) -> dict:
    doc = _ensure_agreement4_numeric(df, df_num, "per_ia_tasks_doc")
    rec = _ensure_agreement4_numeric(df, df_num, "per_ia_tasks_rec")
    m = mask if (isinstance(mask, pd.Series) and len(mask) == len(df)) else slice(None)
    doc = pd.to_numeric(doc[m], errors="coerce");
    rec = pd.to_numeric(rec[m], errors="coerce")
    n_doc = int(doc.notna().sum());
    n_rec = int(rec.notna().sum())
    mean_doc = float(doc.mean()) if n_doc else float("nan")
    mean_rec = float(rec.mean()) if n_rec else float("nan")
    return {"teaching_mean": mean_doc, "teaching_n": n_doc, "research_mean": mean_rec, "research_n": n_rec}


def _teach_research_and_overall_uses(df: pd.DataFrame, df_num: Optional[pd.DataFrame],
                                     mask: Optional[pd.Series] = None) -> dict:
    tr = _teach_research_overview_impl(df, df_num, mask)
    overall_uses = float(
        pd.to_numeric(df_num["uses_score"][mask] if (mask is not None and "uses_score" in df_num.columns)
                      else df_num["uses_score"], errors="coerce").mean()) if (
            df_num is not None and "uses_score" in df_num.columns) else float("nan")
    tr["overall_uses_mean"] = overall_uses
    return tr


# =================== NL MASK (with UB override) ===================
_FILTERABLE_COLS = ["faculty_name", "ub_profile", "gender", "teaching_mode", "teaching_experience"]


def _mentions_ub(q: str) -> bool:
    q = _fold(q)
    return any(pat in q for pat in [
        "universitat de barcelona", "universidad de barcelona", "university of barcelona",
        " ub ", " ub?", " ub.", " ub,", " ub!"
    ])


def _faculty_synonyms(df: pd.DataFrame) -> Dict[str, str]:
    """
    Robust alias map for faculty_name:
      - self-maps for every present value (accent-insensitive)
      - curated multilingual aliases for your 17 faculties
      - substring binding: if alias ⊂ canon OR canon ⊂ alias, we map to that canon
    """
    if "faculty_name" not in df.columns:
        return {}
    present = set(str(x) for x in df["faculty_name"].dropna().unique())

    def fold(s: str) -> str:
        return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii").lower().strip()

    # 0) Start with self-maps (handles whatever exact labels the dataset uses)
    m: Dict[str, str] = {}
    for fac in present:
        m[fold(fac)] = fac

    # 1) Curated aliases for your faculties (extend anytime)
    aliases: Dict[str, list[str]] = {
        # 1
        "Fine Arts": [
            "fine arts", "belles arts", "bellas artes", "faculty of fine arts",
            "facultat de belles arts", "facultad de bellas artes"
        ],
        # 2
        "Biology": [
            "biology", "biologia", "biological sciences", "faculty of biology",
            "facultat de biologia", "facultad de biologia"
        ],
        # 3
        "Earth Sciences": [
            "earth sciences", "ciencies de la terra", "ciencias de la tierra",
            "geology", "geologia", "faculty of earth sciences",
            "facultat de ciencies de la terra", "facultad de ciencias de la tierra"
        ],
        # 4
        "Law": [
            "law", "dret", "derecho", "faculty of law",
            "facultat de dret", "facultad de derecho"
        ],
        # 5
        "Economics and Business": [
            "economics and business", "economics", "business",
            "economia i empresa", "economia y empresa", "economía y empresa",
            "facultat d'economia i empresa", "facultad de economia y empresa",
            "ade", "administracion y direccion de empresas", "administració i direcció d'empreses",
            "economics", "business", "economia", "empresa"
        ],
        # 6
        "Education": [
            "education", "educacio", "educació", "educacion", "educación",
            "ciencies de l'educacio", "ciencias de la educacion",
            "faculty of education", "facultat d'educacio", "facultad de educacion"
        ],
        # 7
        "Pharmacy": [
            "pharmacy", "farmacia", "farmàcia", "faculty of pharmacy",
            "facultat de farmacia", "facultad de farmacia"
        ],
        # 8
        "Philology": [
            "philology", "filologia", "faculty of philology",
            "facultat de filologia", "facultad de filologia"
        ],
        # 9
        "Philosophy": [
            "philosophy", "filosofia", "filosofía", "faculty of philosophy",
            "facultat de filosofia", "facultad de filosofia"
        ],
        # 10
        "Physics": [
            "physics", "fisica", "física", "faculty of physics",
            "facultat de fisica", "facultad de fisica"
        ],
        # 11
        "Geography and History": [
            "geography and history", "geografia i historia", "geografia i història",
            "geografia e historia", "geografia y historia", "geografía e historia",
            "faculty of geography and history","geography","history",
            "facultat de geografia i historia", "facultad de geografia e historia"
        ],
        # 12
        "Audiovisual Media": [
            "audiovisual media", "comunicacio audiovisual", "comunicació audiovisual",
            "comunicacion audiovisual", "comunicación audiovisual",
            "audiovisual communication", "faculty of audiovisual media",
            "facultat de comunicacio audiovisual", "facultad de comunicacion audiovisual", "audiovisual", "media"
        ],
        # 13
        "Nursing": [
            "nursing", "infermeria", "enfermeria", "faculty of nursing",
            "facultat d'infermeria", "facultad de enfermeria"
        ],
        # 14
        "Maths and CS": [
            "maths and cs", "mathematics and computer science",
            "mathematics & computer science", "mathematics & informatics",
            "mathematics and informatics", "computer science", "informatics", "cs",
            "matematiques i informatica", "matemàtiques i informàtica",
            "matematicas e informatica", "matemáticas e informática",
            "faculty of mathematics and computer science",
            "facultat de matematiques i informatica", "facultad de matematicas e informatica",
            "mathematics", "matematiques", "matematicas", "informatica", "informatics"
        ],
        # 15
        "Medicine": [
            "medicine", "medicina", "faculty of medicine",
            "facultat de medicina", "facultad de medicina"
        ],
        # 16
        "Psychology": [
            "psychology", "psicologia", "psicología", "faculty of psychology",
            "facultat de psicologia", "facultad de psicologia"
        ],
        # 17
        "Chemistry": [
            "chemistry", "quimica", "química", "chemical sciences",
            "faculty of chemistry", "facultat de quimica", "facultad de quimica"
        ],
    }

    # 2) Bind curated aliases to actual present labels by substring
    for canon in present:
        fcanon = fold(canon)
        for short_name, alias_list in aliases.items():
            for alias in alias_list:
                falias = fold(alias)
                if falias in fcanon or fcanon in falias:
                    m[falias] = canon

    return m


def _profile_synonyms(df: pd.DataFrame) -> Dict[str, str]:
    if "ub_profile" not in df.columns: return {}
    present = set(df["ub_profile"].dropna().astype(str).unique())
    m: Dict[str, str] = {}

    def add(key: str, canon: str):
        key = _fold(key)
        if canon in present: m[key] = canon

    add("associate", "Associate");
    add("associat", "Associate");
    add("asociado", "Associate")
    add("predoc", "PreDoc");
    add("postdoc", "PostDoc");
    add("collab", "Collab")
    add("lecturer", "Lecturer");
    add("senior lecturer", "Senior Lecturer");
    add("professor", "Professor")
    for p in list(present):
        add(p, p)
    return m


def _gender_synonyms(df: pd.DataFrame) -> Dict[str, str]:
    if "gender" not in df.columns: return {}
    m: Dict[str, str] = {}

    def add(key: str, canon: str): m[_fold(key)] = canon

    add("women", "Female");
    add("female", "Female");
    add("dones", "Female");
    add("mujeres", "Female")
    add("men", "Male");
    add("male", "Male");
    add("homes", "Male");
    add("hombres", "Male")
    return m


def _experience_synonyms(df: pd.DataFrame) -> Dict[str, str]:
    if "teaching_experience" not in df.columns: return {}
    m: Dict[str, str] = {}

    def add(keys: List[str], canon: str):
        for k in keys: m[_fold(k)] = canon

    add(["less than 5", "<5", "under 5", "0-4", "menys de 5", "menos de 5"], "Less than 5")
    add(["between 5 and 10", "5-10", "entre 5 i 10", "entre 5 y 10"], "Between 5 and 10")
    add(["between 11 and 20", "11-20", "entre 11 i 20", "entre 11 y 20"], "Between 11 and 20")
    add(["more than 20", ">=20", "20+", "over 20", "mes de 20", "más de 20"], "More than 20")
    return m


def _collect_candidates(df: pd.DataFrame, col: str) -> Dict[str, Set[str]]:
    out: Dict[str, Set[str]] = {}
    if col not in df.columns: return out
    if col == "faculty_name":
        syn = _faculty_synonyms(df)
        for k, canon in syn.items(): out.setdefault(k, set()).add(canon)
    elif col == "ub_profile":
        syn = _profile_synonyms(df)
        for k, canon in syn.items(): out.setdefault(k, set()).add(canon)
    elif col == "gender":
        syn = _gender_synonyms(df)
        for k, canon in syn.items(): out.setdefault(k, set()).add(canon)
    elif col == "teaching_experience":
        syn = _experience_synonyms(df)
        for k, canon in syn.items(): out.setdefault(k, set()).add(canon)
    uniques = df[col].dropna().astype(str).unique().tolist()
    for v in uniques:
        fv = _fold(v)
        if not fv: continue
        out.setdefault(fv, set()).add(v)
    return out


def _nl_mask_impl(df: pd.DataFrame, question_text: str) -> pd.Series:
    """
    Build a boolean mask from NL:
      - detect values for each filterable column
      - AND across columns
      - OR within the same column
      - UB override applies ONLY if UB is mentioned AND no other filters were found
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return pd.Series([True] * 0, dtype=bool, index=df.index if isinstance(df, pd.DataFrame) else None)

    q = _fold(question_text or "")

    # Collect candidates per column
    col_to_values: Dict[str, Set[str]] = {}
    for col in _FILTERABLE_COLS:
        cand = _collect_candidates(df, col)
        hits: Set[str] = set()
        for key, originals in cand.items():
            if key and key in q:
                hits.update(originals)
        if hits:
            col_to_values[col] = hits

    # If we found NO specific filters and the question mentions UB, use full sample
    if not col_to_values and _mentions_ub(q):
        return pd.Series([True] * len(df), index=df.index, dtype=bool)

    # Otherwise, build mask with AND across columns
    mask = pd.Series(True, index=df.index, dtype=bool)
    for col, values in col_to_values.items():
        mask &= df[col].astype(str).isin(sorted(values))

    return mask


# =================== GROUP-BY COERCION ===================
_VALID_GROUP_COLS = {"ub_profile", "faculty_name", "gender", "teaching_experience", "teaching_mode"}


def _coerce_group_col_hint(by_col_hint: str, question_text: str, df: pd.DataFrame) -> str:
    q = _fold(question_text)
    if by_col_hint in _VALID_GROUP_COLS and by_col_hint in df.columns:
        return by_col_hint
    if any(w in q for w in
           ["ub profile", "teaching profile", "perfil ub", "perfil docent", "perfil de professorat", "profile"]):
        if "ub_profile" in df.columns: return "ub_profile"
    if any(w in q for w in
           ["faculty", "facultat", "facultad", "department", "departament", "depto", "chemistry", "quimica", "química",
            "medicine", "medicina"]):
        if "faculty_name" in df.columns: return "faculty_name"
    if any(w in q for w in ["experience", "experiencia", "teaching experience", "anys docencia", "years teaching"]):
        if "teaching_experience" in df.columns: return "teaching_experience"
    if any(w in q for w in ["mode", "modalitat", "modalidad", "in-person", "online", "hybrid"]):
        if "teaching_mode" in df.columns: return "teaching_mode"
    if any(w in q for w in
           ["gender", "genere", "género", "women", "men", "female", "male", "dones", "homes", "mujeres", "hombres"]):
        if "gender" in df.columns: return "gender"
    if by_col_hint in df.columns and by_col_hint in _VALID_GROUP_COLS: return by_col_hint
    if "ub_profile" in df.columns: return "ub_profile"
    if "faculty_name" in df.columns: return "faculty_name"
    for c in ["gender", "teaching_experience", "teaching_mode"]:
        if c in df.columns: return c
    return by_col_hint


# =================== RISKS / TRAINING ===================
def _cols_with_prefix(df: pd.DataFrame, prefix: str) -> List[str]:
    return [c for c in df.columns if c.startswith(prefix)]


def _agreement4_counts_for_cols_impl(df: pd.DataFrame, cols: List[str], mask: Optional[pd.Series] = None) -> Dict[
    str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    if not cols: return out
    m = mask if (isinstance(mask, pd.Series) and len(mask) == len(df)) else slice(None)
    sub = df.loc[m, cols] if not isinstance(m, slice) else df[cols]
    for c in cols:
        vc = sub[c].value_counts(dropna=True).to_dict()
        out[c] = {lvl: int(vc.get(lvl, 0)) for lvl in AGREEMENT4_LEVELS}
    return out


def _agreement4_top_by_net_agreement(counts: Dict[str, Dict[str, int]], k: int = 5, reverse: bool = True) -> List[
    Tuple[str, int, int, int]]:
    scored: List[Tuple[str, int, int, int]] = []
    for c, d in counts.items():
        pos = int(d.get("Agree", 0)) + int(d.get("Strongly agree", 0))
        neg = int(d.get("Disagree", 0)) + int(d.get("Strongly disagree", 0))
        scored.append((c, pos - neg, pos, neg))
    scored.sort(key=lambda x: x[1], reverse=reverse)
    return scored[:k]


def _per_oporiscuni_summary_impl(df: pd.DataFrame, mask: Optional[pd.Series] = None, k: int = 5) -> str:
    cols = _cols_with_prefix(df, PER_OPORISCUNI_PREFIX)
    if not cols: return "no-opportunities-risks"
    counts = _agreement4_counts_for_cols_impl(df, cols, mask)
    top_pos = _agreement4_top_by_net_agreement(counts, k=k, reverse=True)
    top_neg = _agreement4_top_by_net_agreement(counts, k=k, reverse=False)

    def fmt(items):
        return "; ".join(
            [f"{PER_OPORISCUNI_AXIS_SHORT_EN.get(c, c)} (net={net})" for c, net, _, _ in items]) if items else "none"

    return f"Top opportunities: {fmt(top_pos)} | Top risks: {fmt(top_neg)}"


def _training_needs_distribution_impl(df: pd.DataFrame, mask: Optional[pd.Series] = None) -> List[Dict]:
    """
    Returns one record per training item with:
      - total responses
      - per-level counts AND percentages for all four AGREEMENT4_LEVELS
        (Strongly disagree, Disagree, Agree, Strongly agree)
    """
    cols = [c for c in TRAINING_NEEDS_COLS if c in df.columns]
    if not cols:
        return []

    counts = _agreement4_counts_for_cols_impl(df, cols, mask)
    out: List[Dict[str, Any]] = []

    for c in cols:
        d = counts.get(c, {})
        total = sum(int(d.get(lvl, 0)) for lvl in AGREEMENT4_LEVELS)
        rec = {
            "item": c,
            "label": TRAINING_NEEDS_AXIS_SHORT_EN.get(c, c),
            "total": int(total),
        }
        # Add both counts and percentages for every level, in canonical order
        for lvl in AGREEMENT4_LEVELS:
            cnt = int(d.get(lvl, 0))
            rec[f"{lvl}_count"] = cnt
            rec[f"{lvl}_pct"] = (100.0 * cnt / total) if total else 0.0
        out.append(rec)

    return out


def _training_needs_summary_impl(df: pd.DataFrame, mask: Optional[pd.Series] = None, k: int = 4) -> str:
    """
    Summarizes top-k items ranked by A+SA, but prints a full breakdown:
      SD, D, A, SA — each with count/total and percentage.
    """
    dist = _training_needs_distribution_impl(df, mask)
    if not dist:
        return "no-training-needs"

    # Rank by positives (A + SA), tie-break by total
    scored = []
    for it in dist:
        pos = int(it["Agree_count"]) + int(it["Strongly agree_count"])
        scored.append((it["label"], pos, int(it["total"]), it))
    scored.sort(key=lambda x: (x[1], x[2]), reverse=True)
    top = scored[: int(k)]

    def fmt(it, lvl):
        tot = max(int(it["total"]), 1)
        return f"{it[f'{lvl}_count']}/{tot} ({it[f'{lvl}_pct']:.1f}%)"

    parts = []
    for label, _, _, it in top:
        parts.append(
            f"{label}: SD={fmt(it, 'Strongly disagree')}, "
            f"D={fmt(it, 'Disagree')}, "
            f"A={fmt(it, 'Agree')}, "
            f"SA={fmt(it, 'Strongly agree')}"
        )

    return " | ".join(parts)


# ------- REPLACE the entire existing TOOLS section with this -------
from collections import Counter


def _tools_count_df_via_normalizer(
        df: pd.DataFrame,
        mask: Optional[pd.Series] = None,
        source_col: str = "ia_uses_tools",
        unique_per_respondent: bool = True,
) -> pd.DataFrame:
    """
    If tools_normalizer.py is present, call its `count_tools` on the masked subset.
    Otherwise fall back to the previous naive tokenization (kept compatible).
    """
    if source_col not in df.columns:
        return pd.DataFrame(columns=["tool", "count", "share"])

    # 1) Subset rows per mask (this is how we honor faculty/profile/etc. filters)
    sub = df.loc[mask] if (isinstance(mask, pd.Series) and len(mask) == len(df)) else df

    # 2) Preferred path: your robust normalizer
    if _TOOLS_NORMALIZER_OK:
        try:
            # We don’t pass `filters` because we’ve already applied them via `mask`
            out = tn.count_tools(
                sub,
                source_col=source_col,
                unique_per_respondent=unique_per_respondent,
                filters=None,
            )
            # Ensure expected columns/order
            cols = ["tool", "count", "share"]
            for c in cols:
                if c not in out.columns:
                    out[c] = []  # keep schema
            return out[cols].reset_index(drop=True)
        except Exception as e:
            logger.warning("[chatbot] tools_normalizer.count_tools failed; using fallback. Error: %s", e)


def _tools_summary_impl(df: pd.DataFrame, mask: Optional[pd.Series] = None, k: int = 5) -> str:
    tdf = _tools_count_df_via_normalizer(df, mask, source_col="ia_uses_tools", unique_per_respondent=True)
    if tdf.empty:
        return "no-tools"
    top = tdf.head(int(k))
    parts = [f"{row.tool}: {int(row.count)} ({row.share:.1%})" for row in top.itertuples()]
    total = int(tdf["count"].sum())
    return "Top tools — " + "; ".join(parts) + f". Total mentions={total}."


def _tool_share_impl(df: pd.DataFrame, tool: str, mask: Optional[pd.Series] = None) -> Dict[str, float]:
    tdf = _tools_count_df_via_normalizer(df, mask, source_col="ia_uses_tools", unique_per_respondent=True)
    if tdf.empty:
        return {"tool": tool, "count": 0, "total": 0, "share": 0.0}
    total = int(tdf["count"].sum())
    row = tdf[tdf["tool"].str.lower() == str(tool).lower()]
    if row.empty:
        return {"tool": tool, "count": 0, "total": total, "share": 0.0}
    return {
        "tool": str(row["tool"].iloc[0]),
        "count": int(row["count"].iloc[0]),
        "total": total,
        "share": float(row["share"].iloc[0]),
    }


# ---------- NEW: NORMATIVE COUNTS + PCT ----------
def _normative_counts_pct_impl(df: pd.DataFrame, mask: Optional[pd.Series] = None) -> Dict[str, Dict[str, float]]:
    if "ia_normative_ub" not in df.columns:
        return {"counts": {}, "total": 0, "pct": {}}
    m = mask if (isinstance(mask, pd.Series) and len(mask) == len(df)) else slice(None)
    s = df.loc[m, "ia_normative_ub"].dropna().astype(str)
    total = int(s.shape[0])
    counts = s.value_counts().to_dict()
    pct = {k: (v / total if total else 0.0) for k, v in counts.items()}
    return {"counts": {k: int(v) for k, v in counts.items()}, "total": total, "pct": pct}


# =================== RANK / COMPARE ===================
def _rank_groups_impl(df: pd.DataFrame, df_num: pd.DataFrame, metric: str, by_col: str, min_n: int = 1) -> pd.DataFrame:
    if not isinstance(by_col, str): return pd.DataFrame(columns=["group", "mean", "n", "std"])
    metric = _resolve_metric_impl(metric)
    if df_num is None or metric not in df_num.columns or by_col not in df.columns:
        return pd.DataFrame(columns=["group", "mean", "n", "std"])
    tmp = pd.DataFrame({by_col: df[by_col], metric: df_num[metric]})
    g = tmp.groupby(by_col, dropna=False)[metric]
    out = g.agg(['mean', 'count', 'std']).rename(columns={"count": "n"}).reset_index()
    out = out[out["n"] >= int(min_n)]
    out = out.sort_values("mean", ascending=False, kind="mergesort").reset_index(drop=True)
    out = out.rename(columns={by_col: "group"})
    return out


def _rank_groups_impl_masked(df: pd.DataFrame, df_num: pd.DataFrame, mask: pd.Series, metric: str, by_col: str,
                             min_n: int = 1) -> pd.DataFrame:
    metric = _resolve_metric_impl(metric)
    if df_num is None or metric not in df_num.columns or by_col not in df.columns:
        return pd.DataFrame(columns=["group", "mean", "n", "std"])
    m = mask if (isinstance(mask, pd.Series) and len(mask) == len(df)) else pd.Series([True] * len(df), index=df.index)
    tmp = pd.DataFrame({by_col: df.loc[m, by_col], metric: pd.to_numeric(df_num.loc[m, metric], errors="coerce")})
    g = tmp.groupby(by_col, dropna=False)[metric]
    out = g.agg(['mean', 'count', 'std']).rename(columns={"count": "n"}).reset_index()
    out = out[out["n"] >= int(min_n)]
    out = out.sort_values("mean", ascending=False, kind="mergesort").reset_index(drop=True)
    out = out.rename(columns={by_col: "group"})
    return out


def _compare_groups_basic_impl(df: pd.DataFrame, df_num: pd.DataFrame, metric: str, by_col: str, a: str, b: str) -> str:
    metric = _resolve_metric_impl(metric)
    if df_num is None or metric not in df_num.columns or by_col not in df.columns: return "Columns missing."
    A = df_num[df[by_col] == a][metric].dropna();
    B = df_num[df[by_col] == b][metric].dropna()
    nA, nB = A.shape[0], B.shape[0]
    if nA == 0 or nB == 0: return "Insufficient data."
    meanA, meanB = A.mean(), B.mean();
    varA, varB = A.var(ddof=1), B.var(ddof=1)
    delta = meanA - meanB;
    se = (varA / nA + varB / nB) ** 0.5
    z = (delta / se) if se and se == se else float("nan")

    def _phi(x: float) -> float:
        t = 1.0 / (1.0 + 0.2316419 * abs(x))
        poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
        cdf = 1.0 - (1.0 / (2.506628274631)) * pow(2.718281828459045, -0.5 * x * x) * poly
        return cdf if x >= 0 else 1.0 - cdf

    p = 2.0 * (1.0 - _phi(abs(z))) if z == z else float("nan")
    sp_num = ((nA - 1) * varA + (nB - 1) * varB);
    sp_den = max(nA + nB - 2, 1)
    sp = (sp_num / sp_den) ** 0.5;
    d = (delta / sp) if sp and sp == sp else float("nan")
    ci_lo, ci_hi = (delta - 1.96 * se, delta + 1.96 * se) if se and se == se else (float("nan"), float("nan"))
    tight = " (negligible gap)" if abs(delta) < 2 else ""
    return (f"{a}: mean={meanA:.2f}, n={nA}; {b}: mean={meanB:.2f}, n={nB}; "
            f"Δ={delta:.2f}{tight}, 95% CI=({ci_lo:.2f},{ci_hi:.2f}), p={p:.3f}, d={d:.2f}")


def _compare_groups_basic_masked_impl(df: pd.DataFrame, df_num: pd.DataFrame, metric: str, by_col: str, a: str, b: str,
                                      mask: pd.Series) -> str:
    metric = _resolve_metric_impl(metric)
    if df_num is None or metric not in df_num.columns or by_col not in df.columns: return "Columns missing."
    m = mask if (isinstance(mask, pd.Series) and len(mask) == len(df)) else pd.Series([True] * len(df), index=df.index)
    A = pd.to_numeric(df_num.loc[m & (df[by_col] == a), metric], errors="coerce").dropna()
    B = pd.to_numeric(df_num.loc[m & (df[by_col] == b), metric], errors="coerce").dropna()
    nA, nB = A.shape[0], B.shape[0]
    if nA == 0 or nB == 0: return "Insufficient data."
    meanA, meanB = A.mean(), B.mean();
    varA, varB = A.var(ddof=1), B.var(ddof=1)
    delta = meanA - meanB;
    se = (varA / nA + varB / nB) ** 0.5
    z = (delta / se) if se and se == se else float("nan")

    def _phi(x: float) -> float:
        t = 1.0 / (1.0 + 0.2316419 * abs(x))
        poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
        cdf = 1.0 - (1.0 / (2.506628274631)) * pow(2.718281828459045, -0.5 * x * x) * poly
        return cdf if x >= 0 else 1.0 - cdf

    p = 2.0 * (1.0 - _phi(abs(z))) if z == z else float("nan")
    sp_num = ((nA - 1) * varA + (nB - 1) * varB);
    sp_den = max(nA + nB - 2, 1)
    sp = (sp_num / sp_den) ** 0.5;
    d = (delta / sp) if sp and sp == sp else float("nan")
    ci_lo, ci_hi = (delta - 1.96 * se, delta + 1.96 * se) if se and se == se else (float("nan"), float("nan"))
    tight = " (negligible gap)" if abs(delta) < 2 else ""
    return (f"{a}: mean={meanA:.2f}, n={nA}; {b}: mean={meanB:.2f}, n={nB}; "
            f"Δ={delta:.2f}{tight}, 95% CI=({ci_lo:.2f},{ci_hi:.2f}), p={p:.3f}, d={d:.2f}")


def _top2_summary_masked_impl(df: pd.DataFrame, df_num: pd.DataFrame, metric: str, by_col: str, mask: pd.Series,
                              min_n: int = 1) -> str:
    tbl = _rank_groups_impl_masked(df, df_num, mask, _resolve_metric_impl(metric), by_col, min_n)
    if tbl.empty:
        return "No groups with sufficient data."
    if len(tbl) == 1:
        t0 = tbl.iloc[0]
        return f"{t0['group']} is highest on {_resolve_metric_impl(metric)} (mean={t0['mean']:.2f}, n={int(t0['n'])})."
    t0, t1 = tbl.iloc[0], tbl.iloc[1]
    gap = float(t0['mean'] - t1['mean'])
    tight = " (very tight gap)" if abs(gap) < 2 else ""
    return (f"{t0['group']} leads on {_resolve_metric_impl(metric)} (mean={t0['mean']:.2f}, n={int(t0['n'])}), "
            f"followed by {t1['group']} (mean={t1['mean']:.2f}, n={int(t1['n'])}); gap={gap:.2f}{tight}.")


# =================== EXTRA ANALYSIS HELPERS ===================
def _knowledge_app_means_impl(df: pd.DataFrame, df_num: Optional[pd.DataFrame], mask: Optional[pd.Series] = None) -> \
        List[Tuple[str, float, int]]:
    if df_num is None: return []
    cols = [c for c in KNOW_APP_COLS if c in df_num.columns]
    if not cols: return []
    m = mask if (isinstance(mask, pd.Series) and len(mask) == len(df)) else slice(None)
    out = []
    for c in cols:
        ser = pd.to_numeric(df_num.loc[m, c], errors="coerce") if not isinstance(m, slice) else pd.to_numeric(df_num[c],
                                                                                                              errors="coerce")
        n = int(ser.notna().sum())
        if n == 0: continue
        out.append((c, float(ser.mean()), n))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def _knowledge_app_means_str_impl(df: pd.DataFrame, df_num: Optional[pd.DataFrame], mask: Optional[pd.Series] = None,
                                  k: int = 999) -> str:
    items = _knowledge_app_means_impl(df, df_num, mask)
    if not items: return "no-knowledge-applications"
    items = items[:int(k)]
    return "; ".join([f"{c}={v:.2f} (n={n})" for c, v, n in items])


# --- NEW: uses task-level means across ia_uses_* ---
def _uses_task_means_impl(df: pd.DataFrame, df_num: Optional[pd.DataFrame], mask: Optional[pd.Series] = None) -> List[
    Tuple[str, float, int]]:
    if df_num is None: return []
    cols = [c for c in USES_FREQ_COLS if c in df_num.columns]
    if not cols: return []
    m = mask if (isinstance(mask, pd.Series) and len(mask) == len(df)) else slice(None)
    out = []
    for c in cols:
        ser = pd.to_numeric(df_num.loc[m, c], errors="coerce") if not isinstance(m, slice) else pd.to_numeric(df_num[c],
                                                                                                              errors="coerce")
        n = int(ser.notna().sum())
        if n == 0: continue
        out.append((c, float(ser.mean()), n))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def _uses_task_means_str_impl(df: pd.DataFrame, df_num: Optional[pd.DataFrame], mask: Optional[pd.Series] = None,
                              k: int = 999) -> str:
    items = _uses_task_means_impl(df, df_num, mask)
    if not items: return "no-uses-tasks"
    items = items[:int(k)]
    return "; ".join([f"{c}={v:.2f} (n={n})" for c, v, n in items])


# --- NEW: detect students 'use' columns by value domain ---
def _students_use_cols(df: pd.DataFrame) -> List[str]:
    wanted = set(STUDENTS_USE_LEVELS)
    cols = []
    for c in df.columns:
        s = df[c].dropna().astype(str)
        if s.empty: continue
        vals = set(s.unique())
        if vals.issubset(wanted) and ("ESTUD" in c or "STUD" in c or "ALUM" in c or "student" in c.lower()):
            cols.append(c)
    return cols


def _students_use_distribution_impl(df: pd.DataFrame, mask: Optional[pd.Series] = None) -> Dict[str, Any]:
    cols = _students_use_cols(df)
    levels = STUDENTS_USE_LEVELS[:]
    if not cols:
        return {"categories": [], "levels": levels, "series": [], "totals_by_cat": [], "long_labels": {}}
    m = mask if (isinstance(mask, pd.Series) and len(mask) == len(df)) else slice(None)
    categories = cols[:]  # keep original; frontend can humanize
    totals = []
    counts_per_level: Dict[str, List[int]] = {lvl: [] for lvl in levels}
    sub = df.loc[m, cols] if not isinstance(m, slice) else df[cols]
    for c in cols:
        s = sub[c].dropna().astype(str)
        tot = 0
        for lvl in levels:
            cnt = int((s == lvl).sum())
            counts_per_level[lvl].append(cnt)
            tot += cnt
        totals.append(tot)
    series = [{"name": lvl, "values": counts_per_level[lvl]} for lvl in levels]
    return {"categories": categories, "levels": levels, "series": series, "totals_by_cat": totals, "long_labels": {}}


# --- NEW: students attitudes (Likert-4) auto-detect ---
def _students_attitudes_cols(df: pd.DataFrame) -> List[str]:
    wanted = set(AGREEMENT4_LEVELS)
    cols = []
    for c in df.columns:
        s = df[c].dropna().astype(str)
        if s.empty: continue
        vals = set(s.unique())
        if vals.issubset(wanted) and ("ESTUD" in c or "STUD" in c or "ALUM" in c or "student" in c.lower()):
            cols.append(c)
    return cols


def _students_attitudes_distribution_impl(df: pd.DataFrame, mask: Optional[pd.Series] = None) -> Dict[str, Any]:
    cols = _students_attitudes_cols(df)
    levels = AGREEMENT4_LEVELS[:]
    if not cols:
        return {"categories": [], "levels": levels, "series": [], "totals_by_cat": [], "long_labels": {}}
    m = mask if (isinstance(mask, pd.Series) and len(mask) == len(df)) else slice(None)
    categories = cols[:]
    totals = []
    counts_per_level: Dict[str, List[int]] = {lvl: [] for lvl in levels}
    sub = df.loc[m, cols] if not isinstance(m, slice) else df[cols]
    for c in cols:
        s = sub[c].dropna().astype(str)
        tot = 0
        for lvl in levels:
            cnt = int((s == lvl).sum())
            counts_per_level[lvl].append(cnt)
            tot += cnt
        totals.append(tot)
    series = [{"name": lvl, "values": counts_per_level[lvl]} for lvl in levels]
    return {"categories": categories, "levels": levels, "series": series, "totals_by_cat": totals, "long_labels": {}}


# =================== OPEN-TEXT HELPERS (DEFENSIVE) ===================
def _get_open_text_df(open_text: Optional[dict], qid: Any) -> pd.DataFrame:
    """
    open_text is expected to be a dict[qid] -> DataFrame.
    We accept either a DataFrame or a dict-like that can become one.
    """
    if not isinstance(open_text, dict):
        return pd.DataFrame()
    df_ot = open_text.get(qid, None)
    if df_ot is None:
        return pd.DataFrame()
    if isinstance(df_ot, pd.DataFrame):
        return df_ot.copy()
    try:
        return pd.DataFrame(df_ot).copy()
    except Exception:
        return pd.DataFrame()


def _normalize_sentiment_column(df_ot: pd.DataFrame) -> pd.Series:
    """
    Try several common column names for sentiment. Returns a string series (may be empty).
    Accepted labels mapped to {'positive','negative','neutral'} when obvious.
    """
    candidates = ["sentiment", "polarity", "label", "sentiment_label", "pred_label"]
    col = next((c for c in candidates if c in df_ot.columns), None)
    if col is None:
        return pd.Series([], dtype="object")
    s = df_ot[col].astype(str).str.strip().str.lower()
    # map common variants
    mapping = {
        "pos": "positive", "positive": "positive", "1": "positive", "posi": "positive",
        "neg": "negative", "negative": "negative", "-1": "negative",
        "neu": "neutral", "neutral": "neutral", "0": "neutral",
    }
    return s.map(lambda x: mapping.get(x, x))


def _extract_row_ids(df_ot: pd.DataFrame) -> pd.Series:
    """Find a row-id column to join with survey mask; fallbacks handle common names."""
    for c in ["row_id", "ROW_ID", "respondent_id", "id", "ID", "response_id"]:
        if c in df_ot.columns:
            return df_ot[c]
    # If no explicit id, try using index if it's numeric-like
    if df_ot.index.is_integer():
        return pd.Series(df_ot.index, index=df_ot.index, name="row_id")
    return pd.Series([], dtype="int64")


def _apply_mask_to_open_text(df_ot: pd.DataFrame, df: pd.DataFrame, mask: Optional[pd.Series]) -> pd.DataFrame:
    """
    If mask is provided and df has a row identifier, subset open_text to those ids.
    We look for df['row_id'] first, else try to match by df index if both are integer-like.
    """
    if mask is None or df_ot.empty or not isinstance(df, pd.DataFrame) or df.empty:
        return df_ot

    # Case 1: df has explicit row_id
    if "row_id" in df.columns:
        keep_ids = set(pd.to_numeric(df.loc[mask, "row_id"], errors="coerce").dropna().astype(int).tolist())
        if keep_ids:
            ot_ids = pd.to_numeric(_extract_row_ids(df_ot), errors="coerce").dropna().astype(int)
            return df_ot.loc[ot_ids.index[ot_ids.isin(list(keep_ids))]]
        return df_ot

    # Case 2: both use integer-like index and mask aligns
    try:
        if df.index.is_integer():
            keep_idx = set(df.index[mask].tolist())
            if df_ot.index.is_integer():
                return df_ot.loc[df_ot.index.intersection(list(keep_idx))]
    except Exception:
        pass

    return df_ot


def _sentiment_counts_impl(open_text: Optional[dict], qid: Any) -> str:
    """Return 'positive=X; neutral=Y; negative=Z' or 'no-open-text'."""
    df_ot = _get_open_text_df(open_text, qid)
    if df_ot.empty:
        return "no-open-text"
    s = _normalize_sentiment_column(df_ot)
    if s.empty:
        return "no-sentiment"
    vc = s.value_counts()
    pos = int(vc.get("positive", 0))
    neu = int(vc.get("neutral", 0))
    neg = int(vc.get("negative", 0))
    # include any other labels if present
    extras = [f"{k}={int(v)}" for k, v in vc.items() if k not in {"positive", "neutral", "negative"}]
    core = [f"positive={pos}", f"neutral={neu}", f"negative={neg}"]
    return "; ".join(core + extras)


def _sentiment_counts_masked_impl(open_text: Optional[dict], qid: Any, df: pd.DataFrame,
                                  mask: Optional[pd.Series]) -> str:
    """Same as above but restricted to respondents in mask (when possible)."""
    df_ot = _get_open_text_df(open_text, qid)
    if df_ot.empty:
        return "no-open-text"
    sub = _apply_mask_to_open_text(df_ot, df, mask)
    if sub.empty:
        return "no-open-text-after-mask"
    s = _normalize_sentiment_column(sub)
    if s.empty:
        return "no-sentiment"
    vc = s.value_counts()
    pos = int(vc.get("positive", 0))
    neu = int(vc.get("neutral", 0))
    neg = int(vc.get("negative", 0))
    extras = [f"{k}={int(v)}" for k, v in vc.items() if k not in {"positive", "neutral", "negative"}]
    core = [f"positive={pos}", f"neutral={neu}", f"negative={neg}"]
    return "; ".join(core + extras)


def _topic_series(df_ot: pd.DataFrame) -> pd.Series:
    """
    Try to locate topic/keyword columns. Preference order:
    - 'topic', 'topics'
    - 'keyphrase', 'keyphrases'
    - 'cluster', 'cluster_label'
    Returns a string series or empty if nothing matches.
    """
    candidates = ["topic", "topics", "keyphrase", "keyphrases", "cluster", "cluster_label"]
    for c in candidates:
        if c in df_ot.columns:
            s = df_ot[c]
            # explode list-like cells
            if any(isinstance(x, (list, tuple, set)) for x in s.head(50)):
                s = s.explode()
            return s.dropna().astype(str).str.strip()
    return pd.Series([], dtype="object")


def _top_topics_impl(open_text: Optional[dict], qid: Any, k: int = 5) -> str:
    """
    Return up to k topics as 'topic=count; ...'. If nothing, 'no-topics'.
    """
    df_ot = _get_open_text_df(open_text, qid)
    if df_ot.empty:
        return "no-open-text"
    s = _topic_series(df_ot)
    if s.empty:
        return "no-topics"
    vc = s.value_counts().head(int(k))
    return "; ".join([f"{t}={int(c)}" for t, c in vc.items()])


def _top_topics_masked_impl(open_text: Optional[dict], qid: Any, df: pd.DataFrame, mask: Optional[pd.Series],
                            k: int = 5) -> str:
    df_ot = _get_open_text_df(open_text, qid)
    if df_ot.empty:
        return "no-open-text"
    sub = _apply_mask_to_open_text(df_ot, df, mask)
    if sub.empty:
        return "no-open-text-after-mask"
    s = _topic_series(sub)
    if s.empty:
        return "no-topics"
    vc = s.value_counts().head(int(k))
    return "; ".join([f"{t}={int(c)}" for t, c in vc.items()])


# =================== SANITIZERS ===================
_BAD_METRIC_REWRITES = [
    (r'df_num\[\s*[\'"]ia_knowledge[\'"]\s*\]', 'df_num["knowledge_score"]'),
    (r'df_num\[\s*[\'"]ia_uses[\'"]\s*\]', 'df_num["uses_score"]'),
    (r"\bia_knowledge_score\b", "knowledge_score"),
]
_GROUPBY_MEAN_COL_RE = re.compile(r"df_num\.groupby\((?P<key>[^)]+)\)\.mean\(\)\s*\[\s*['\"](?P<col>\w+)['\"]\s*\]")


def _enforce_overall_metric(code: str) -> str:
    out = code
    for pat, repl in _BAD_METRIC_REWRITES: out = re.sub(pat, repl, out)
    out = _GROUPBY_MEAN_COL_RE.sub(r'df_num.groupby(\g<key>)["\g<col>"].mean()', out)
    # fix wrong API kwargs passed by codegen in older runs
    out = re.sub(r"compare_groups_basic_masked\(", "compare_groups_basic_masked(", out)
    return out


class _SandboxError(RuntimeError): pass


def _default_metric_for(question_text: str) -> Optional[str]:
    q = _fold(question_text)
    if not q: return None
    subarea_keys = ["text creation", "multimedia", "class planning", "material", "activity", "evaluation",
                    "research management", "data collection", "translation", "transcription", "data analysis",
                    "technical support", "experiments", "inclusion"]
    if any(k in q for k in subarea_keys): return None
    if any(k in q for k in ["knowledge", "coneixement", "conocimiento", "saber"]): return "knowledge_score"
    if any(
            k in q for k in
            ["use", "uses", "usage", "utilitzacio", "ús", "us", "uso", "utilización"]): return "uses_score"
    return None


def _mentions_teaching_research(question_text: str) -> bool:
    q = _fold(question_text)
    return (("teaching" in q or "docencia" in q or "docència" in q or "docent" in q)
            and ("research" in q or "recerca" in q or "investig" in q))


def _mentions_tools(question_text: str) -> bool:
    q = _fold(question_text)
    return any(
        t in q for t in ["tool", "tools", "eina", "eines", "herramienta", "herramientas", "ai tools", "gai tools"])


def _mentions_students(question_text: str) -> bool:
    q = _fold(question_text)
    return any(w in q for w in ["student", "students", "alumn", "estud", "estudiantes", "estudiants"])


def _mentions_perceptions(question_text: str) -> bool:
    q = _fold(question_text)
    return any(w in q for w in ["perception", "perceptions", "percepc", "attitude", "attitudes"])


# ---------- NEW: policy detector ----------
def _mentions_policy(question_text: str) -> bool:
    q = _fold(question_text)
    return any(w in q for w in [
        "policy", "policies", "rule", "rules", "regulation", "regulations", "normative", "normativa",
        "guia", "guide", "guideline", "guidelines", "protocol", "protocols"
    ])


# =================== SAFE EXEC ===================
def _safe_exec_python(code: str, df: pd.DataFrame, df_num: Optional[pd.DataFrame], points: Dict[str, Dict],
                      open_text: Optional[Dict[str, pd.DataFrame]], question_text: str) -> str:
    banned_patterns = [r"\bimport\b", r"\bopen\s*\(", r"\bexec\s*\(", r"\beval\s*\(", r"__\w+__", r"\bos\.", r"\bsys\.",
                       r"\bsubprocess\b", r"\bsocket\b", r"\brequests\b", r"\bglob\s*\(", r"\bpathlib\b"]
    low = (code or "").lower()
    for pat in banned_patterns:
        if re.search(pat, low): raise _SandboxError("Disallowed construct detected in generated code.")

    safe_builtins = {"len": len, "min": min, "max": max, "sum": sum, "round": round, "sorted": sorted,
                     "list": list, "dict": dict, "set": set, "tuple": tuple, "enumerate": enumerate,
                     "range": range, "any": any, "all": all, "abs": abs, "float": float, "int": int, "str": str,
                     "print": print, "Exception": Exception}
    safe_globals = {"__builtins__": safe_builtins}

    if df_num is not None:
        overall_knowledge = df_num.get("knowledge_score", _nan_series_like(df_num))
        overall_uses = df_num.get("uses_score", _nan_series_like(df_num))
    else:
        overall_knowledge = pd.Series([], dtype="float64");
        overall_uses = pd.Series([], dtype="float64")

    def _coerce_metric_name(metric_name: str) -> str:
        default = _default_metric_for(question_text)
        mn = (metric_name or "").strip()
        key = mn.lower().replace(" ", "_")
        if key in {"knowledge", "ai_knowledge", "gai_knowledge"}: return "knowledge_score"
        if key in {"use", "uses", "usage", "ai_use", "gai_use"}: return "uses_score"
        if default and key in {"ia_knowledge", "ia_uses"}: return default
        return _resolve_metric_impl(mn)

    def _resolve_metric_compat(name, *_, **__):
        return _coerce_metric_name(name)

    def _coerce_group_col(by_col_hint: str) -> str:
        return _coerce_group_col_hint(by_col_hint or "", question_text, df)

    # Compat wrappers to swallow stray kwargs like group_by=... or group=...
    def _rank_groups_masked_compat(*args, **kwargs):
        metric = kwargs.pop("metric", args[0] if len(args) > 0 else "knowledge_score")
        by_col_hint = kwargs.pop("by_col",
                                 kwargs.pop("group",
                                            kwargs.pop("group_by",
                                                       args[1] if len(args) > 1 else "ub_profile")))
        mask = kwargs.pop("mask", args[2] if len(args) > 2 else _nl_mask_impl(df, question_text))
        min_n = kwargs.pop("min_n", args[3] if len(args) > 3 else 1)
        _ = kwargs.pop("by", None)  # swallow any stray alias
        return _rank_groups_impl_masked(
            df, df_num, mask,
            _coerce_metric_name(metric),
            _coerce_group_col(by_col_hint),
            int(min_n)
        )

    def _rank_groups_top_row_masked_compat(*args, **kwargs):
        metric = kwargs.pop("metric", args[0] if len(args) > 0 else "knowledge_score")
        by_col_hint = kwargs.pop("by_col",
                                 kwargs.pop("group",
                                            kwargs.pop("group_by",
                                                       args[1] if len(args) > 1 else "ub_profile")))
        mask = kwargs.pop("mask", args[2] if len(args) > 2 else _nl_mask_impl(df, question_text))
        min_n = kwargs.pop("min_n", args[3] if len(args) > 3 else 1)
        tbl = _rank_groups_impl_masked(
            df, df_num, mask,
            _coerce_metric_name(metric),
            _coerce_group_col(by_col_hint),
            int(min_n)
        )
        return tbl.head(1).to_dict(orient="records")[0] if not tbl.empty else {}

    def _rank_groups_bottom_row_masked_compat(*args, **kwargs):
        metric = kwargs.pop("metric", args[0] if len(args) > 0 else "knowledge_score")
        by_col_hint = kwargs.pop("by_col",
                                 kwargs.pop("group",
                                            kwargs.pop("group_by",
                                                       args[1] if len(args) > 1 else "ub_profile")))
        mask = kwargs.pop("mask", args[2] if len(args) > 2 else _nl_mask_impl(df, question_text))
        min_n = kwargs.pop("min_n", args[3] if len(args) > 3 else 1)
        tbl = _rank_groups_impl_masked(
            df, df_num, mask,
            _coerce_metric_name(metric),
            _coerce_group_col(by_col_hint),
            int(min_n)
        )
        return tbl.tail(1).to_dict(orient="records")[0] if not tbl.empty else {}

    def _compare_groups_basic_masked_compat(*args, **kwargs):
        metric = kwargs.pop("metric", args[0] if len(args) > 0 else "knowledge_score")
        by_col_hint = kwargs.pop("by_col",
                                 kwargs.pop("group",
                                            kwargs.pop("group_by",
                                                       args[1] if len(args) > 1 else "ub_profile")))
        a = kwargs.pop("a", args[2] if len(args) > 2 else "")
        b = kwargs.pop("b", args[3] if len(args) > 3 else "")
        mask = kwargs.pop("mask", args[4] if len(args) > 4 else _nl_mask_impl(df, question_text))
        return _compare_groups_basic_masked_impl(
            df, df_num,
            _coerce_metric_name(metric),
            _coerce_group_col(by_col_hint),
            a, b, mask
        )

    # Single authoritative safe_locals mapping (no duplicates)
    safe_locals = {
        "pd": pd, "df": df, "df_num": df_num,
        "QUESTION_TEXT": question_text,
        "default_metric_for": lambda: (_default_metric_for(question_text) or "knowledge_score"),
        "mentions_teaching_research": lambda: _mentions_teaching_research(question_text),
        "mentions_tools": lambda: _mentions_tools(question_text),
        "mentions_students": lambda: _mentions_students(question_text),
        "mentions_perceptions": lambda: _mentions_perceptions(question_text),
        "mentions_policy": lambda: _mentions_policy(question_text),

        "nl_mask": lambda question_text_arg=None: _nl_mask_impl(df,
                                                                question_text if question_text_arg is None else question_text_arg),

        "rank_groups": lambda metric, by_col, min_n=1: _rank_groups_impl(df, df_num, _coerce_metric_name(metric),
                                                                         _coerce_group_col(by_col), min_n),
        "rank_groups_masked": _rank_groups_masked_compat,
        "rank_groups_top_row_masked": _rank_groups_top_row_masked_compat,
        "rank_groups_bottom_row_masked": _rank_groups_bottom_row_masked_compat,

        "top2_summary_masked": lambda metric, by_col, mask, min_n=1: _top2_summary_masked_impl(df, df_num,
                                                                                               _coerce_metric_name(
                                                                                                   metric),
                                                                                               _coerce_group_col(
                                                                                                   by_col), mask,
                                                                                               min_n),

        "compare_groups_basic": lambda metric, by_col, a, b: _compare_groups_basic_impl(df, df_num,
                                                                                        _coerce_metric_name(metric),
                                                                                        _coerce_group_col(by_col), a,
                                                                                        b),
        "compare_groups_basic_masked": _compare_groups_basic_masked_compat,

        "value_counts_str": lambda s, top=10: _value_counts_impl(s, top),
        "respondents_n": lambda mask=None: int(df.shape[0]) if _mentions_ub(question_text) else _respondents_n_impl(df,
                                                                                                                    mask),

        "resolve_metric": _resolve_metric_compat,
        "metric_series": lambda metric_name, mask=None: (
            pd.to_numeric(df_num[_coerce_metric_name(metric_name)], errors="coerce")[mask]
            if (df_num is not None and _coerce_metric_name(metric_name) in df_num.columns and mask is not None)
            else (pd.to_numeric(df_num[_coerce_metric_name(metric_name)], errors="coerce")
                  if (df_num is not None and _coerce_metric_name(metric_name) in df_num.columns)
                  else _nan_series_like(df_num or df))
        ),
        "metric_mean": lambda metric_name, mask=None:
        float(pd.to_numeric(df_num[_coerce_metric_name(metric_name)], errors="coerce")[mask].mean())
        if (df_num is not None and _coerce_metric_name(metric_name) in df_num.columns and mask is not None)
        else (float(pd.to_numeric(df_num[_coerce_metric_name(metric_name)], errors="coerce").mean())
              if (df_num is not None and _coerce_metric_name(metric_name) in df_num.columns)
              else float("nan")),

        "teach_research_overview": lambda mask=None: _teach_research_overview_impl(df, df_num, mask),
        "teach_research_and_overall_uses": lambda mask=None: _teach_research_and_overall_uses(df, df_num, mask),

        "knowledge_app_means_str": lambda mask=None, k=999: _knowledge_app_means_str_impl(df, df_num, mask, k),

        # uses tasks + students distributions
        "uses_task_means_str": lambda mask=None, k=999: _uses_task_means_str_impl(df, df_num, mask, k),
        "students_use_distribution": lambda mask=None: _students_use_distribution_impl(df, mask),
        "students_attitudes_distribution": lambda mask=None: _students_attitudes_distribution_impl(df, mask),

        "OVERALL_KNOWLEDGE": overall_knowledge, "OVERALL_USES": overall_uses,

        # open-text (unchanged)
        "sentiment_counts": lambda qid: _sentiment_counts_impl(open_text, qid),
        "sentiment_counts_masked": lambda qid, mask=None: _sentiment_counts_masked_impl(open_text, qid, df, mask),
        "top_topics": lambda qid, k=5: _top_topics_impl(open_text, qid, k),
        "top_topics_masked": lambda qid, mask=None, k=5: _top_topics_masked_impl(open_text, qid, df, mask, k),

        "FREQ_POINTS": points.get("FREQ_POINTS"),
        "USES_LEVEL_POINTS": points.get("USES_LEVEL_POINTS"),
        "KNOW_LEVEL_POINTS": points.get("KNOW_LEVEL_POINTS"),
        "KNOW_APP_POINTS": points.get("KNOW_APP_POINTS"),
        "NORMATIVE_POINTS": points.get("NORMATIVE_POINTS"),

        "pearsonr_basic": lambda s1, s2: _pearsonr_basic_impl(s1, s2),

        "normative_distribution": lambda mask=None: (
            _value_counts_impl(df["ia_normative_ub"][mask]) if (mask is not None and "ia_normative_ub" in df.columns)
            else (_value_counts_impl(df["ia_normative_ub"]) if "ia_normative_ub" in df.columns else "no-normative")
        ),
        "normative_counts_pct": lambda mask=None: _normative_counts_pct_impl(df, mask),

        "per_oporiscuni_summary": lambda mask=None, k=5: _per_oporiscuni_summary_impl(df, mask, k),
        "training_needs_summary": lambda mask=None, k=4: _training_needs_summary_impl(df, mask, k),
        "training_needs_distribution": lambda mask=None: _training_needs_distribution_impl(df, mask),

        "tools_summary": lambda mask=None, k=5: _tools_summary_impl(df, mask, k),
        "tool_share": lambda tool, mask=None: _tool_share_impl(df, tool, mask),
    }

    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(code, "<analysis>", "exec"), safe_globals, safe_locals)
    except Exception as e:
        raise _SandboxError(f"Execution error: {e}")

    ans = safe_locals.get("answer", None)
    if ans is not None:
        try:
            return str(ans).strip()
        except Exception:
            pass
    out = buf.getvalue().strip()
    if out: return out
    for k in ("result", "summary", "out"):
        if k in safe_locals and safe_locals[k] is not None:
            try:
                return str(safe_locals[k]).strip()
            except Exception:
                continue
    raise _SandboxError("No output. Define `answer` or print the result.")


# =================== COUNTS / OPEN-TEXT / PEARSON ===================
def _value_counts_impl(series: pd.Series, top: int = 10) -> str:
    s = series.dropna()
    if any(isinstance(x, (list, tuple, set)) for x in s.head(50)):
        s = s.explode()
    vc = s.dropna().astype(str).value_counts().head(int(top))
    return "; ".join([f"{idx}={cnt}" for idx, cnt in vc.items()])


def _respondents_n_impl(df: pd.DataFrame, mask=None) -> int:
    if mask is None: return int(df.shape[0])
    try:
        return int(mask.sum()) if hasattr(mask, "sum") else int(df[mask].shape[0])
    except Exception:
        return int(df.shape[0])


def _pearsonr_basic_impl(x: pd.Series, y: pd.Series):
    xs = pd.to_numeric(x, errors="coerce");
    ys = pd.to_numeric(y, errors="coerce")
    mask = xs.notna() & ys.notna();
    xs, ys = xs[mask], ys[mask]
    n = int(xs.shape[0])
    if n < 3: return float("nan"), float("nan"), n
    mx, my = float(xs.mean()), float(ys.mean());
    dx, dy = xs - mx, ys - my
    num = float((dx * dy).sum());
    den = float((dx.pow(2).sum() * dy.pow(2).sum()) ** 0.5)
    if den == 0.0: return float("nan"), float("nan"), n
    r = num / den;
    z = r * (n - 3) ** 0.5

    def _phi(x: float) -> float:
        t = 1.0 / (1.0 + 0.2316419 * abs(x))
        poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
        cdf = 1.0 - (1.0 / (2.506628274631)) * pow(2.718281828459045, -0.5 * x * x) * poly
        return cdf if x >= 0 else 1.0 - cdf

    p = 2.0 * (1.0 - _phi(abs(z)))
    return float(r), float(p), n


# =================== AGENT ===================
class SurveyChatAgent:
    """Dataset-grounded agent with UB-scope override, robust NL masking, teaching/research routing, tools & students distributions, and compat wrappers."""

    def __init__(self, surveys_df: Optional[pd.DataFrame] = None):
        self.df: Optional[pd.DataFrame] = surveys_df
        if self.df is None:
            ds_path = os.getenv("DATASET_PATH", "").strip()
            if ds_path and os.path.exists(ds_path):
                try:
                    self.df = pd.read_csv(ds_path)
                    logger.warning(f"[chatbot] Loaded fallback CSV: {ds_path} ({len(self.df)}x{len(self.df.columns)})")
                except Exception as e:
                    logger.error(f"[chatbot] Failed to read DATASET_PATH CSV: {e}")
                    self.df = None
            else:
                logger.warning("[chatbot] No surveys_df and no DATASET_PATH found. Agent will answer without data.]")

        if isinstance(self.df, pd.DataFrame):
            self.df.columns = [str(c).strip() for c in self.df.columns]
            self.groups = _group_columns(self.df)
            self.manifest = _manifest(self.df)
        else:
            self.groups = {};
            self.manifest = "DataFrame present: false"

        self.df_num: Optional[pd.DataFrame] = None
        if isinstance(self.df, pd.DataFrame):
            num = self.df.copy()

            if "ia_knowledge" in num.columns:
                num["ia_knowledge"] = num["ia_knowledge"].map(KNOW_LEVEL_POINTS).astype("float64")
            if "ia_uses" in num.columns:
                num["ia_uses"] = num["ia_uses"].map(USES_LEVEL_POINTS).astype("float64")

            for c in KNOW_APP_COLS:
                if c in num.columns: num[c] = num[c].map(KNOW_APP_POINTS).astype("float64")
            for c in USES_FREQ_COLS:
                if c in num.columns: num[c] = num[c].map(FREQ_POINTS).astype("float64")

            if "ia_normative_ub" in num.columns:
                num["ia_normative_ub"] = num["ia_normative_ub"].map(NORMATIVE_POINTS).astype("float64")

            for c in ["knowledge_score", "uses_score", "perceptions_score", "training_needs_score"]:
                if c in num.columns: num[c] = pd.to_numeric(num[c], errors="coerce")

            for c in ("per_ia_tasks_doc", "per_ia_tasks_rec"):
                if c in self.df.columns and c not in num.columns:
                    try:
                        num[c] = self.df[c].map(AGREEMENT4_POINTS).astype("float64")
                    except Exception:
                        pass

            self.df_num = num

        self.open_text = {}
        if load_open_text_analysis is not None:
            try:
                self.open_text = load_open_text_analysis() or {}
                logger.info("[chatbot] Open-text analysis loaded for qids: %s", list(self.open_text.keys()))
            except Exception as e:
                logger.warning("[chatbot] Could not load open-text analysis: %s", e)

        api_key = os.getenv("OPENAI_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key: logger.error("[chatbot] OPENAI_API_KEY not set; model answers will not work.")
        self.openai = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("CHATBOT_TEMPERATURE", "0"))
        self.max_tokens = int(os.getenv("CHATBOT_MAX_TOKENS", "900"))

    # -------- PROMPTS --------
    def _codegen_prompt(self, question: str, lang: str) -> List[Dict[str, str]]:
        lang_name = {"en": "English", "ca": "Catalan", "es": "Spanish"}.get((lang or "en")[:2], "English")
        routing = textwrap.dedent("""
        DEMOGRAPHIC ROUTING:
        - Always build `mask = nl_mask(QUESTION_TEXT)` and apply it to ALL numeric/likert computations and tools/students counts.
        - If the text mentions “UB / Universitat de Barcelona / University of Barcelona”, DO NOT narrow with filters: treat as full-sample.
        - Filters may include faculty, profile, gender, teaching_experience, teaching_mode. Combine filters with AND across columns (OR within same column).
        """).strip()
        semantics = textwrap.dedent("""
        COLUMN SEMANTICS (HARD OVERRIDES):
        - Generic “knowledge” → 'knowledge_score'. Generic “use/usage” → 'uses_score'. Do NOT average per-area columns for generic overall metrics.
        - If the question compares TEACHING and RESEARCH:
            • Use Likert-4 task support blocks: per_ia_tasks_doc and per_ia_tasks_rec (0–100). Report means and n.
            • Also report the requested overall metric “in general” (e.g., uses_score).
            • Additionally list task-level means: uses_task_means_str(mask=mask).
        - UB-level “What knowledge does the teaching staff have…?”:
            • After the overall knowledge_score, also list the knowledge-application means across all ia_knowledge_* columns:
              knowledge_app_means_str(mask=mask).
        - Students:
            • If the question mentions students + use → students_use_distribution(mask=mask) with fixed level order:
              ["Not at all","A little","Quite a bit","A lot","Don't know"].
            • If the question mentions students + perceptions/attitudes → students_attitudes_distribution(mask=mask) with levels:
              ["Strongly disagree","Disagree","Agree","Strongly agree"].
        - Policy / normative / rules / guides:
            • If the question mentions any of these, call normative_distribution(mask=mask) OR normative_counts_pct(mask=mask).
              Return counts AND percentages for each option:
              "Yes, there is a guide or normative", "I ignore if there's a guide or normative", "There is no guide or normative".
        - Rankings by demographic (e.g., “Which profile has the most/least …?”):
            • Use rank_groups_top_row_masked(...) for most/highest and rank_groups_bottom_row_masked(...) for least/lowest.
            • ALWAYS include group, mean (two decimals), and n.
        - Binary comparisons (e.g., men vs women):
            • Call compare_groups_basic_masked(metric='knowledge_score' unless another metric is explicit, by_col=<demographic>,
              a=<groupA>, b=<groupB>, mask=mask) and print the returned line (includes Δ, CI, p, d).
        - Risks/opportunities: per_oporiscuni_summary(mask=mask, k=5).
        - Training interests:
            • Call training_needs_summary(mask=mask) to return a formatted line that includes Strongly Disagree/Disagree/Agree/Strongly Agree counts and percentages.
            • If you need raw data for charts, also call training_needs_distribution(mask=mask).
        - Tools:
            • If the question mentions tools but not a specific tool: tools_summary(mask=mask, k=5).
            • If a specific tool appears, also call tool_share('<name>', mask=mask).
        """).strip()
        hard_rules = textwrap.dedent("""
        HARD RULES:
        - Use df_num for numeric aggregation; pass `mask` whenever possible.
        - resolve_metric('<area>') returns a COLUMN NAME; to get a number use metric_mean(..., mask=mask).
        - For rankings/comparisons, ALWAYS coerce group columns to one of:
              ub_profile, faculty_name, gender, teaching_experience, teaching_mode
        - Emit ONLY a Python code block that sets `answer` OR prints a result. No imports.
        """).strip()
        sys = f"""
You are a data analyst. Always answer in {lang_name}.
You have two pandas DataFrames:
- `df`: string/categorical, lists, open-text.
- `df_num`: numeric mirror (0..100).

Manifest of available data:
{self.manifest}

{routing}

{semantics}

{hard_rules}
"""
        return [{"role": "system", "content": sys.strip()}, {"role": "user", "content": question.strip()}]

    def _summarize_prompt(self, question: str, analysis_text: str, lang: str) -> List[Dict[str, str]]:
        lang_name = {"en": "English", "ca": "Catalan", "es": "Spanish"}.get((lang or "en")[:2], "English")
        sys = f"""
You are the MapAI assistant. Always answer in {lang_name}.
Use the ANALYSIS RESULTS to answer the CURRENT question.
- Be concise but analytical (2–5 bullets/sentences).
- Include respondent n and any filters. If UB is referenced explicitly, assume full sample n (no demographic narrowing).
- For teaching vs research, state these are “AI support for tasks in teaching/research” (0–100) and include means + n; also add overall uses_score/knowledge_score if requested and list task-level uses.
- For generic knowledge, if knowledge_app_means are present, list the top items (use human wording).
- For students use/attitudes, report stacked levels (order fixed); mention totals_by_cat if helpful.
- For training, report Strongly Disagree, Disagree, Agree, Strongly Agree separately (both counts and % if provided). Do NOT collapse negatives.
- For tools, list top tools with counts and shares.
- Avoid raw column tokens; use human wording only. Call out negligible gaps (<2 points).
- When analysis provides {{group, mean, n}} for “most/least”, include those numbers verbatim.
- If analysis contains lines like "mean=" / "n=" / "Δ=" / "p=" / "d=", quote them exactly; do NOT recompute or re-round.
"""
        analysis_text = _humanize_text(analysis_text or "")
        user = f"""CURRENT QUESTION:
{question}

ANALYSIS RESULTS (from executed Python on df/df_num and/or tools/students counts):
{analysis_text}
"""
        return [{"role": "system", "content": sys.strip()}, {"role": "user", "content": user}]

    # -------- PIPELINE --------
    def _generate_analysis_code(self, question: str, lang: str) -> str:
        msgs = self._codegen_prompt(question, lang)
        r = self.openai.chat.completions.create(
            model=self.model, messages=msgs, temperature=0, max_tokens=min(self.max_tokens, 800),
        )
        content = (r.choices[0].message.content or "").strip()
        code = _extract_python_code(content)
        code = _enforce_overall_metric(code)
        if code.lstrip().lower().startswith("python"):
            code = "\n".join(code.splitlines()[1:]).strip()
        if ("answer" not in code) and ("print(" not in code):
            code += """
# --- AUTO EMIT (appended by server) ---
try:
    _val = answer
except Exception:
    _val = None
if _val is None:
    try:
        _val = result
    except Exception:
        pass
if _val is None:
    try:
        _val = summary
    except Exception:
        pass
if _val is not None:
    try:
        print(_val)
    except Exception:
        pass
"""
        return code

    def _run_analysis(self, code: str, question: str) -> str:
        if not isinstance(self.df, pd.DataFrame):
            return "DataFrame not available in runtime. Cannot compute."
        points = {
            "FREQ_POINTS": FREQ_POINTS,
            "USES_LEVEL_POINTS": USES_LEVEL_POINTS,
            "KNOW_LEVEL_POINTS": KNOW_LEVEL_POINTS,
            "KNOW_APP_POINTS": KNOW_APP_POINTS,
            "NORMATIVE_POINTS": NORMATIVE_POINTS,
        }
        try:
            with open("/tmp/chatbot_last_code.py", "w", encoding="utf-8") as fh:
                fh.write(code)
        except Exception:
            pass
        return _safe_exec_python(code, self.df, self.df_num, points, self.open_text, question)

    def _summarize(self, question: str, analysis_text: str, lang: str) -> str:
        msg = self._summarize_prompt(question, analysis_text, lang)
        r = self.openai.chat.completions.create(
            model=self.model, messages=msg, temperature=self.temperature, max_tokens=self.max_tokens
        )
        return (r.choices[0].message.content or "").strip()

    def answer(self, question: str, lang: str = "en") -> str:
        code = self._generate_analysis_code(question, lang)
        logger.debug("Generated code:\n%s", code)
        try:
            analysis_text = self._run_analysis(code, question)
            logger.debug("Analysis output:\n%s", analysis_text)
        except _SandboxError as e:
            logger.warning("[chatbot] sandbox error: %s\n--- CODE ---\n%s\n-----------", e, code)
            fallback_q = (
                f"{question}\n\n"
                "Use mask = nl_mask(QUESTION_TEXT). If TEACHING & RESEARCH appear, call teach_research_and_overall_uses(mask=mask) "
                "and list uses_task_means_str(mask=mask). If tools are mentioned, call tools_summary(mask=mask, k=5) and tool_share if any tool name appears. "
                "If students + use appear, call students_use_distribution(mask=mask). If students + perceptions/attitudes appear, call students_attitudes_distribution(mask=mask). "
                "If the question mentions policy/rule/guide/normative, call normative_counts_pct(mask=mask) and return counts + percentages for each option. "
                "For generic knowledge/use, use metric_mean(resolve_metric('knowledge'/'uses'), mask=mask). "
                "For rankings, use rank_groups_top_row_masked/rank_groups_bottom_row_masked and print group, mean, n. "
                "For binary compares, call compare_groups_basic_masked and print its line. "
                "Also list knowledge_app_means_str(mask=mask) when the question is about general knowledge. "
                "For risks/opportunities use per_oporiscuni_summary(mask=mask). "
                "For training, use training_needs_distribution(mask=mask) and print 4-level breakdown per item. "
                "When comparing or ranking by demographics, ALWAYS coerce group columns via ub_profile/faculty_name/gender/teaching_experience/teaching_mode. "
                "Emit `answer` or print."
            )
            code = self._generate_analysis_code(fallback_q, lang)
            try:
                analysis_text = self._run_analysis(code, question)
                logger.debug("Analysis output (fallback):\n%s", analysis_text)
            except Exception:
                return ("I couldn't produce an analysis output from the generated code. "
                        "Please rephrase your question (e.g., specify columns or filters).")
        except Exception:
            logger.exception("[chatbot] unexpected execution error")
            return "I couldn't analyze the dataset due to an internal error."
        return self._summarize(question, analysis_text, lang)