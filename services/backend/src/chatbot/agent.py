# services/backend/src/chatbot/agent.py
from __future__ import annotations
import os, logging, re, textwrap, io, contextlib
from typing import Optional, List, Dict, Tuple
import pandas as pd
from openai import OpenAI

logger = logging.getLogger(__name__)

# ==========================================================
# Canonical numeric points mirroring data_loader
# ==========================================================
FREQ_POINTS = {"Never": 0, "Sometimes": 33, "Often": 66, "Very often": 100}
USES_LEVEL_POINTS = {"No use": 0, "Low use": 33, "Moderate use": 66, "Advanced use": 100}
KNOW_LEVEL_POINTS = {"No knowledge": 0, "Little knowledge": 33, "Good knowledge": 66, "Expert knowledge": 100}
KNOW_APP_POINTS = {"I don't know any": 0, "I know a few": 33, "I know several": 66, "I know many": 100}
NORMATIVE_POINTS = {
    "Yes, there is a guide or normative": 100,
    "I ignore if there's a guide or normative": 50,
    "There is no guide or normative": 0,
}

# Derived columns created in data_loader (teach the model they exist)
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

# Column families (string-valued) we’ll convert to numbers in df_num
KNOW_APP_COLS = [
    "ia_knowledge_text_creation","ia_knowledge_multimedia_creation","ia_knowledge_class_planning",
    "ia_knowledge_material_design","ia_knowledge_activity_design","ia_knowledge_evaluation",
    "ia_knowledge_research_management","ia_knowledge_data_collection",
    "ia_knowledge_transcription_translation","ia_knowledge_data_analysis",
    "ia_knowledge_technical_support","ia_knowledge_ai_experiments",
    "ia_knowledge_inclusion_support",
]

USES_FREQ_COLS = [
    "ia_uses_text_creation","ia_uses_multimedia_creation","ia_uses_class_planning",
    "ia_uses_material_design","ia_uses_activity_design","ia_uses_evaluation",
    "ia_uses_research_management","ia_uses_data_collection","ia_uses_transcription_translation",
    "ia_uses_data_analysis","ia_uses_technical_support","ia_uses_ai_experiments",
    "ia_uses_inclusion_support","ia_proposes_students",
]

STUDENTS_USES_COLS = [
    "ia_uses_text_creation_student","ia_uses_multimedia_creation_student",
    "ia_uses_activity_design_student","ia_uses_evaluation_student",
    "ia_uses_research_management_student","ia_uses_data_collection_student",
    "ia_uses_transcription_translation_student","ia_uses_data_analysis_student",
    "ia_uses_technical_support_student","ia_uses_ai_experiments_student",
    "ia_uses_inclusion_support_student",
]

# Likert helpers (guard old utilities)
LIKERT_ORDER = [
    "Molt d'acord", "D'acord", "Ni d'acord ni en desacord",
    "En desacord", "Molt en desacord"
]
LIKERT_ALT = [
    "Totalment d'acord", "D'acord", "Neutral",
    "En desacord", "Totalment en desacord"
]

# ==========================================================
# Code block extraction
# ==========================================================
_CODEBLOCK_RE = re.compile(
    r"```(?:\s*(?P<lang>[a-zA-Z0-9_+-]+))?\s*\n(?P<body>[\s\S]*?)```",
    re.MULTILINE,
)

def _extract_python_code(content: str) -> str:
    """
    Extract the first fenced code block. If it declares a language (python, py),
    return the body. If no fence exists, return the raw content (best effort).
    Also strips any accidental leading 'python' token line.
    """
    if not content:
        return ""
    m = _CODEBLOCK_RE.search(content)
    if m:
        body = m.group("body") or ""
        lines = body.splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        if lines and lines[0].strip().lower() in {"python", "py"}:
            lines = lines[1:]
        return "\n".join(lines).strip()

    raw = (content or "").strip()
    raw_lower = raw.lstrip().lower()
    if raw_lower.startswith("python") or raw_lower.startswith("py"):
        lines = raw.splitlines()
        if lines:
            lines = lines[1:]
        raw = "\n".join(lines)
    return raw.strip()

def _norm(s: str) -> str:
    import re as _re
    return _re.sub(r"\s+", " ", str(s or "")).strip()

def _is_likert_series(x: pd.Series) -> bool:
    vals = set(map(_norm, x.dropna().astype(str).unique()))
    sample = vals.intersection(set(LIKERT_ORDER) | set(LIKERT_ALT))
    return len(sample) >= max(2, min(4, len(vals)))

def _group_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
    cols = df.columns
    groups = {
        "core": [c for c in ["ID","age","gender","faculty_name","teaching_experience","ub_profile","teaching_mode"] if c in cols],
        "knowledge_all": [c for c in cols if c.startswith("ia_knowledge")],
        "uses_all": [c for c in cols if c.startswith("ia_uses_")] + (["ia_uses"] if "ia_uses" in cols else []),
        "student_uses": [c for c in cols if c.endswith("_student")],
        "per_estud": [c for c in cols if c.startswith("PER_IA_ESTUD_")],
        "per_usestud": [c for c in cols if c.startswith("PER_IA_ÚSESTUD_") or c.startswith("PER_IA_USESTUD_")],
        "per_tasques": [c for c in cols if c.startswith("PER_IA_TASQUES_")],
        "per_oporisc": [c for c in cols if c.startswith("PER_IA_OPORISCUNI_")],
        "for_all":  [c for c in cols if c.startswith("FOR_IA_")],
        "free_text": [c for c in ["CONEIX_IA_ALTRESFUNC","ÚS_IA_ALTRESUSOS","PER_IA_OPORISCUNI_ALTRES",
                                  "PER_IA_POSICPROF_PERQUE","FOR_IA_NECEFORMAT_ALTRES","COMENTARIS"] if c in cols],
        "policy": [c for c in ["ia_normative_ub","ia_proposes_students","ia_uses_tools","ia_perceptions_doc_priority","PARTICIPAR"] if c in cols],
    }
    return groups

def _manifest(df: pd.DataFrame) -> str:
    g = _group_columns(df)
    lines = [f"DataFrame present: rows={len(df)}, cols={len(df.columns)}"]
    for name in ["core","knowledge_all","uses_all","student_uses","per_usestud","per_estud","per_tasques","per_oporisc","for_all","policy","free_text"]:
        cols = g.get(name, [])
        if cols:
            lines.append(f"{name}({len(cols)}): {cols[:20]}")
    if "faculty_name" in df.columns:
        lines.append(f"faculty_name sample: {df['faculty_name'].value_counts().head(5).to_dict()}")
    if "gender" in df.columns:
        lines.append(f"gender sample: {df['gender'].value_counts().head(5).to_dict()}")

    derived_existing = [c for c in DERIVED_COLS if c in df.columns]
    if derived_existing:
        lines.append(f"derived_present({len(derived_existing)}): {derived_existing}")
        for sample_col in ("ia_uses_docchange_student_list", "training_received_list", "ia_perceptions_doc_priority_list"):
            if sample_col in df.columns:
                try:
                    example = df[sample_col].dropna().iloc[0]
                    lines.append(f"example {sample_col}: {example}")
                except Exception:
                    pass
    return "\n".join(lines)

# ==========================================================
# Helper functions exposed inside the sandbox
# ==========================================================
def _rank_groups_impl(df: pd.DataFrame, df_num: pd.DataFrame, metric: str, by_col: str, min_n: int = 1) -> pd.DataFrame:
    """
    Return a sorted DataFrame with columns: group, mean, n, std
    Uses df_num for numeric `metric`, grouped by df[by_col].
    """
    if metric not in df_num.columns or by_col not in df.columns:
        return pd.DataFrame(columns=["group", "mean", "n", "std"])
    group_vals = df[by_col]
    vals = df_num[metric]
    tmp = pd.DataFrame({by_col: group_vals, metric: vals})
    g = tmp.groupby(by_col, dropna=False)[metric]
    out = g.agg(['mean', 'count', 'std']).rename(columns={"count": "n"}).reset_index()
    out = out[out["n"] >= int(min_n)]
    out = out.sort_values("mean", ascending=False, kind="mergesort").reset_index(drop=True)
    out = out.rename(columns={by_col: "group"})
    return out

def _top2_summary_impl(df: pd.DataFrame, df_num: pd.DataFrame, metric: str, by_col: str, min_n: int = 1) -> str:
    tbl = _rank_groups_impl(df, df_num, metric, by_col, min_n=min_n)
    if tbl.empty:
        return "No groups with sufficient data."
    top = tbl.iloc[0]
    if len(tbl) == 1:
        return f"{top['group']} is highest on {metric} (mean={top['mean']:.2f}, n={int(top['n'])})."
    runner = tbl.iloc[1]
    gap = top['mean'] - runner['mean']
    tight = " (very tight gap)" if abs(gap) < 2 else ""
    return (f"{top['group']} leads on {metric} (mean={top['mean']:.2f}, n={int(top['n'])}), "
            f"followed by {runner['group']} (mean={runner['mean']:.2f}, n={int(runner['n'])}); "
            f"gap={gap:.2f}{tight}.")

def _compare_groups_basic_impl(df: pd.DataFrame, df_num: pd.DataFrame, metric: str, by_col: str, a: str, b: str) -> str:
    """
    Simple two-group comparison with means, ns, delta. Uses df (for masks) + df_num (for metric).
    """
    if metric not in df_num.columns or by_col not in df.columns:
        return "Columns missing."
    A = df_num[df[by_col] == a][metric].dropna()
    B = df_num[df[by_col] == b][metric].dropna()
    nA, nB = A.shape[0], B.shape[0]
    if nA == 0 or nB == 0:
        return "Insufficient data."
    meanA, meanB = A.mean(), B.mean()
    delta = meanA - meanB
    tight = " (negligible gap)" if abs(delta) < 2 else ""
    return (f"{a}: mean={meanA:.2f}, n={nA}; {b}: mean={meanB:.2f}, n={nB}; "
            f"Δ={delta:.2f}{tight}")

def _value_counts_impl(series: pd.Series, top: int = 10) -> str:
    vc = series.dropna().astype(str).value_counts().head(int(top))
    # Terse one-liner string so the summarizer can read it
    return "; ".join([f"{idx}={cnt}" for idx, cnt in vc.items()])


# ==========================================================
# SANDBOXED PYTHON EXEC
# ==========================================================
class _SandboxError(RuntimeError):
    pass

def _safe_exec_python(code: str, df: pd.DataFrame, df_num: Optional[pd.DataFrame], points: Dict[str, Dict]) -> str:
    """
    Execute model-produced code against `df` in a tight sandbox.
    You get df (string/list/text), df_num (numeric mirror), pd, and helper functions + points dicts.
    Prefer `answer` variable; else capture printed stdout; else common fallbacks.
    """
    banned_patterns = [
        r"\bimport\b", r"\bopen\s*\(", r"\bexec\s*\(", r"\beval\s*\(",
        r"__\w+__", r"\bos\.", r"\bsys\.", r"\bsubprocess\b", r"\bsocket\b",
        r"\brequests\b", r"\bglob\s*\(", r"\bpathlib\b",
    ]
    low = (code or "").lower()
    for pat in banned_patterns:
        if re.search(pat, low):
            raise _SandboxError("Disallowed construct detected in generated code.")

    safe_builtins = {
        "len": len, "min": min, "max": max, "sum": sum, "round": round, "sorted": sorted,
        "list": list, "dict": dict, "set": set, "tuple": tuple, "enumerate": enumerate,
        "range": range, "any": any, "all": all, "abs": abs, "float": float, "int": int, "str": str,
        "print": print  # <-- allow print, since we capture stdout
    }
    safe_globals = {"__builtins__": safe_builtins}
    safe_locals = {
        "pd": pd,
        "df": df,
        "df_num": df_num,
        # helper functions exposed to the generated code
        "rank_groups": lambda metric, by_col, min_n=1: _rank_groups_impl(df, df_num, metric, by_col, min_n),
        "top2_summary": lambda metric, by_col, min_n=1: _top2_summary_impl(df, df_num, metric, by_col, min_n),
        "compare_groups_basic": lambda metric, by_col, a, b: _compare_groups_basic_impl(df, df_num, metric, by_col, a, b),
        # points maps so the model can remap if needed
        "FREQ_POINTS": points.get("FREQ_POINTS"),
        "USES_LEVEL_POINTS": points.get("USES_LEVEL_POINTS"),
        "KNOW_LEVEL_POINTS": points.get("KNOW_LEVEL_POINTS"),
        "KNOW_APP_POINTS": points.get("KNOW_APP_POINTS"),
        "NORMATIVE_POINTS": points.get("NORMATIVE_POINTS"),
        "value_counts_str": lambda s, top=10: _value_counts_impl(s, top),
    }

    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(code, "<analysis>", "exec"), safe_globals, safe_locals)
    except Exception as e:
        raise _SandboxError(f"Execution error: {e}")

    # 1) Explicit answer variable wins
    ans = safe_locals.get("answer", None)
    if ans is not None:
        try:
            return str(ans).strip()
        except Exception:
            pass

    # 2) Anything printed?
    out = buf.getvalue().strip()
    if out:
        return out

    # 3) Common fallbacks (result/summary/out)
    for k in ("result", "summary", "out"):
        if k in safe_locals and safe_locals[k] is not None:
            try:
                return str(safe_locals[k]).strip()
            except Exception:
                continue

    raise _SandboxError("No output. Define `answer` or print the result.")

# ==========================================================
# AGENT
# ==========================================================
class SurveyChatAgent:
    """
    Dataset-grounded agent:
    - Loads your `surveys_df` (or DATASET_PATH csv).
    - Builds df_num (0..100 numeric mirror).
    - Generates Python that analyzes df/df_num in a sandbox.
    - Summarizes results concisely in the target language.
    """

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

        # Normalize & group
        if isinstance(self.df, pd.DataFrame):
            self.df.columns = [str(c).strip() for c in self.df.columns]
            self.groups = _group_columns(self.df)
            self.manifest = _manifest(self.df)
        else:
            self.groups = {}
            self.manifest = "DataFrame present: false"

        # Build numeric mirror (df_num)
        self.df_num: Optional[pd.DataFrame] = None
        if isinstance(self.df, pd.DataFrame):
            num = self.df.copy()

            # Self knowledge / usage levels
            if "ia_knowledge" in num.columns:
                num["ia_knowledge"] = num["ia_knowledge"].map(KNOW_LEVEL_POINTS).astype("float64")
            if "ia_uses" in num.columns:
                num["ia_uses"] = num["ia_uses"].map(USES_LEVEL_POINTS).astype("float64")

            # Knowledge application familiarity
            for c in KNOW_APP_COLS:
                if c in num.columns:
                    num[c] = num[c].map(KNOW_APP_POINTS).astype("float64")

            # Use frequencies
            for c in USES_FREQ_COLS:
                if c in num.columns:
                    num[c] = num[c].map(FREQ_POINTS).astype("float64")

            # Students’ uses (also frequencies)
            for c in STUDENTS_USES_COLS:
                if c in num.columns:
                    num[c] = num[c].map(FREQ_POINTS).astype("float64")

            # Normative awareness
            if "ia_normative_ub" in num.columns:
                num["ia_normative_ub"] = num["ia_normative_ub"].map(NORMATIVE_POINTS).astype("float64")

            # Keep computed scores (already numeric) if present
            for c in ["knowledge_score","uses_score","perceptions_score","training_needs_score"]:
                if c in num.columns:
                    num[c] = pd.to_numeric(num[c], errors="coerce")

            self.df_num = num

        # OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("[chatbot] OPENAI_API_KEY not set; model answers will not work.")
        self.openai = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("CHATBOT_TEMPERATURE", "0"))
        self.max_tokens = int(os.getenv("CHATBOT_MAX_TOKENS", "900"))

    # --------------- PROMPTS ---------------
    def _codegen_prompt(self, question: str, lang: str) -> List[Dict[str, str]]:
        lang_name = {"en":"English","ca":"Catalan","es":"Spanish"}.get((lang or "en")[:2], "English")
        sys = f"""
You are a data analyst. You have two pandas DataFrames:
- `df`: string/categorical, list columns, open-text.
- `df_num`: numeric mirror (0..100) aligned by rows/columns for safe aggregation.

Manifest of available data:
{self.manifest}

HARD RULES:
- For ANY numeric aggregation (mean, sum, corr, ranking), use `df_num` not `df`.
- When filtering by faculty/gender/etc., index `df_num` with masks from `df`, e.g.:
    sub = df_num[df["faculty_name"] == "Chemistry"]
- For list columns like *_list use: df["col_list"].explode().value_counts() to count selections.
- Prefer the helpers exposed in the environment:
    * rank_groups(metric, by_col, min_n=1) -> DataFrame columns: group, mean, n, std (sorted desc by mean)
    * top2_summary(metric, by_col, min_n=1) -> str (top vs runner-up with gap)
    * compare_groups_basic(metric, by_col, a, b) -> str
- Always include sample size as n=... (use the number of non-null rows used).
- No imports, no I/O, no OS/network, no dunder names.
- Use double quotes for Catalan strings that contain apostrophes.

OUTPUT CONTRACT (mandatory):
- Return ONLY a Python code block (no prose).
- The code MUST set a variable `answer` (string) OR call `print(...)`.
"""
        return [
            {"role": "system", "content": sys.strip()},
            {"role": "user", "content": question.strip()},
        ]

    def _summarize_prompt(self, question: str, analysis_text: str, lang: str) -> List[Dict[str, str]]:
        lang_name = {"en":"English","ca":"Catalan","es":"Spanish"}.get((lang or "en")[:2], "English")
        sys = f"""
You are the MapAI assistant. Always answer in {lang_name}.
Use the ANALYSIS RESULTS (below) to answer the CURRENT question.
- Be concise but insightful (avoid raw bullet dumps).
- Include sample size (n=...) and any filters if present in the analysis.
- If some referenced column is missing, say it briefly and proceed with what exists.
- Never reveal raw rows or personal data; only aggregates.
- If differences are small (<2 points on a 0–100 scale), explicitly call them negligible/tight.
"""
        user = f"""CURRENT QUESTION:
{question}

ANALYSIS RESULTS (from executed Python on df/df_num):
{analysis_text}
"""
        return [
            {"role": "system", "content": sys.strip()},
            {"role": "user", "content": user},
        ]

    # --------------- PIPELINE ---------------
    def _generate_analysis_code(self, question: str, lang: str) -> str:
        msgs = self._codegen_prompt(question, lang)
        r = self.openai.chat.completions.create(
            model=self.model,
            messages=msgs,
            temperature=0,
            max_tokens=min(self.max_tokens, 800),
        )
        content = (r.choices[0].message.content or "").strip()
        code = _extract_python_code(content)

        # FINAL DEFENSE: if some stray 'python' survived, drop first token/line
        stripped = code.lstrip()
        if stripped.lower().startswith("python"):
            code = "\n".join(stripped.splitlines()[1:]).strip()

        # AUTO-EMIT EPILOGUE
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

    def _run_analysis(self, code: str) -> str:
        if not isinstance(self.df, pd.DataFrame):
            return "DataFrame not available in runtime. Cannot compute."
        points = {
            "FREQ_POINTS": FREQ_POINTS,
            "USES_LEVEL_POINTS": USES_LEVEL_POINTS,
            "KNOW_LEVEL_POINTS": KNOW_LEVEL_POINTS,
            "KNOW_APP_POINTS": KNOW_APP_POINTS,
            "NORMATIVE_POINTS": NORMATIVE_POINTS,
        }
        return _safe_exec_python(code, self.df, self.df_num, points)

    def _summarize(self, question: str, analysis_text: str, lang: str) -> str:
        msg = self._summarize_prompt(question, analysis_text, lang)
        r = self.openai.chat.completions.create(
            model=self.model,
            messages=msg,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return (r.choices[0].message.content or "").strip()

    # --------------- PUBLIC API ---------------
    def answer(self, question: str, lang: str = "en") -> str:
        # 1) generate code
        code = self._generate_analysis_code(question, lang)
        logger.debug("Generated code:\n%s", code)

        # 2) execute
        try:
            analysis_text = self._run_analysis(code)
        except _SandboxError as e:
            logger.warning("[chatbot] sandbox error: %s\n--- CODE ---\n%s\n-----------", e, code)
            # Retry with a simplified instruction once
            fallback_q = (
                f"{question}\n\n"
                "Simplify and only compute the minimal aggregates to answer. "
                "Use df_num for numbers, explode() for lists, and prefer rank_groups/top2_summary. Emit `answer` or print."
            )
            code = self._generate_analysis_code(fallback_q, lang)
            try:
                analysis_text = self._run_analysis(code)
            except Exception:
                return (
                    "I couldn't produce an analysis output from the generated code. "
                    "Please rephrase your question (e.g., specify columns or filters)."
                )
        except Exception:
            logger.exception("[chatbot] unexpected execution error")
            return "I couldn't analyze the dataset due to an internal error."

        # 3) summarize in target language
        return self._summarize(question, analysis_text, lang)
