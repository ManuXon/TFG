# tools_normalizer.py
import re
import unicodedata
from collections import Counter
from typing import Dict, Iterable, List, Optional, Set
import pandas as pd

# ---------- basic normalization ----------
def strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))

def norm_text(s: str) -> str:
    s = strip_accents(str(s)).lower()
    # normalize separators (commas, slashes, semicolons, pipes, newlines)
    s = re.sub(r"[,\|/;·•\n\t]+", " ", s)
    # remove parenthetical notes
    s = re.sub(r"\([^)]*\)", " ", s)
    # collapse dots/ellipses
    s = re.sub(r"\.{2,}|…", " ", s)
    # unify simple conjunctions
    s = re.sub(r"\b(i|y|e|amb|con)\b", " ", s)
    # collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s

def make_relaxed(word: str) -> str:
    """allow 'chat gpt' / 'chatgpt' / 'chat-gpt' / 'chat.gpt' …"""
    core = re.sub(r"\s+", "", strip_accents(word))
    pieces = [re.escape(ch) for ch in core]
    return r"\b" + r"\s*[-_.\s]*?".join(pieces) + r"\b"

def compile_any(patterns: Iterable[str]) -> List[re.Pattern]:
    return [re.compile(p, re.I) for p in patterns]

# ---------- canonical tool patterns (expand as you see new variants) ----------
PATTERNS: Dict[str, List[re.Pattern]] = {
    # LLM assistants
    "ChatGPT": compile_any([
        make_relaxed("chat gpt"), r"\bchatgpt\b", r"\bchatgtp\b", r"\bchagpt\b",
        r"\bchapgpt\b", r"\bxatgpt\b"
    ]),
    "Copilot": compile_any([
        r"\bcopilot\b", r"\bco-?pilot\b", r"\bcopiloto\b",
        r"\bgithub\s*copilot\b", r"\bmicrosoft\s*copilot\b"
    ]),
    "Gemini": compile_any([r"\bgemini(s)?\b", r"\bgoogle\s*ai(\s*mode)?\b", r"\bbard\b"]),
    "Claude": compile_any([r"\bclaude\b"]),
    "DeepSeek": compile_any([r"\bdeep\s*seek\b", r"\bdeepseek\b", r"\bdeep\s*sek\b", r"\bdeep\s*see?k\b"]),
    "Grok": compile_any([r"\bgrok\b", r"\bgork\b"]),
    "Mistral (Le Chat)": compile_any([r"\bmistral\b", r"\ble\s*chat\b"]),
    "Llama / Meta AI": compile_any([r"\bllama\b", r"\bmeta\s*ai\b"]),
    "Qwen": compile_any([r"\bqwen\b", r"\bqwen-?ai\b"]),
    "Poe": compile_any([r"\bpoe\b"]),
    "Ollama": compile_any([r"\bollama\b"]),

    # research/search/biblio
    "Perplexity": compile_any([r"\bperplexity(\s*pro)?\b", r"\bperplexity\.ai\b"]),
    "Consensus": compile_any([r"\bconsensus\b", r"\bconsenus\b"]),
    "Elicit": compile_any([r"\belicit(y)?\b", r"\belctit\b"]),
    "ResearchRabbit": compile_any([r"\bresearch\s*rabbit\b", r"\bresearchrabbit\b"]),

    # translation/writing
    "DeepL": compile_any([r"\bdeepl\b", r"\bdeep\s*l\b", r"\bdeep\s*blue\b"]),
    "Google Translate": compile_any([r"\bgoogle\s*translate(r)?\b", r"\btraductor\s*google\b"]),
    "LanguageTool": compile_any([r"\blanguage\s*tool\b"]),
    "Grammarly": compile_any([r"\bgrammarl?y(\.go)?\b"]),
    "Wordtune": compile_any([r"\bword\s*tune\b", r"\bwordtune\b"]),
    "Hemingway Editor": compile_any([r"\bhemingway\b"]),
    "Writefull": compile_any([r"\bwrite\s*full\b", r"\bwritefull\b"]),
    "GPTZero": compile_any([r"\bgpt\s*zero\b", r"\bgptzero\b"]),

    # notes/notebooks
    "NotebookLM": compile_any([r"\bnotebook\s*l+m\b", r"\bnotebook\s*llm\b",
                               r"\bnotebooklm\b", r"\bnote\s*klm\b"]),

    # image/video/audio
    "DALL·E": compile_any([r"\bdall[\s\-]*e(2)?\b", r"\bdalle\b"]),
    "Midjourney": compile_any([r"\bmid\s*journey\b", r"\bmidjourney\b"]),
    "Stable Diffusion": compile_any([r"\bstable\s*diffusion\b"]),
    "Leonardo": compile_any([r"\bleonardo\b"]),
    "Ideogram": compile_any([r"\bideogram\b"]),
    "Runway": compile_any([r"\brunway\b", r"\brunwayml\b", r"\brunaway\b"]),
    "Pika Labs": compile_any([r"\bpika\b"]),
    "Freepik (AI)": compile_any([r"\bfreepik\b"]),
    "Firefly (Adobe)": compile_any([r"\bfirefly\b"]),
    "Suno": compile_any([r"\bsuno\b"]),
    "HeyGen": compile_any([r"\bhey\s*gen\b|\bheygen\b"]),
    "Whisper": compile_any([r"\bwhisper\b"]),
    "Otter.ai": compile_any([r"\botter\.?ai\b"]),
    "Trint": compile_any([r"\btrint\b"]),
    "Sonix.ai": compile_any([r"\bsonix\.?ai\b"]),
    "Turboscribe": compile_any([r"\bturbo\s*scribe\b", r"\bturboscribe\b"]),
    "Transkriptor": compile_any([r"\btranskriptor\b"]),
    "Natural Readers": compile_any([r"\bnatural\s*readers?\b"]),
    "Narakeet": compile_any([r"\bnarakeet\b"]),
    "ElevenLabs": compile_any([r"\beleven\s*labs\b"]),

    # presentation/design/content
    "Canva (AI)": compile_any([r"\bcanva\b", r"\bmagic\s*(design|media)\b"]),
    "Beautiful.ai": compile_any([r"\bbeautiful\.ai\b"]),
    "Prezi (AI)": compile_any([r"\bprezi\b"]),
    "Gamma": compile_any([r"\bgamma(\.app)?\b", r"\bgamma\s*ai\b"]),
    "AhaSlides": compile_any([r"\bahas?lides\b"]),
    "Genially (AI)": compile_any([r"\bgenially\b"]),

    # classroom/edtech
    "Curipod": compile_any([r"\bcuripod\b"]),
    "MagicSchool.ai": compile_any([r"\bmagicschool(\.ai)?\b"]),
    "Edpuzzle (AI)": compile_any([r"\bedpuzzle\b"]),
    "Class Companion": compile_any([r"\bclass\s*companion\b"]),
    "Khanmigo": compile_any([r"\bkhanmigo\b"]),
    "To Teach AI": compile_any([r"\bto\s*teach\s*ai\b"]),
    "SchoolAI": compile_any([r"\bschool\s*ai\b|\bschoolai\b"]),
    "AI Class Assistant": compile_any([r"\bai\s*class\s*assistant\b"]),

    # office/forms/platforms
    "Google Forms (AI)": compile_any([r"\bgoogle\s*forms?\b"]),
    "Microsoft Power Platform (AI)": compile_any([r"\bpower\s*platform\b", r"\bpower\s*automate\b"]),
    "Notion (AI)": compile_any([r"\bnotion\b"]),
    "Make (Integromat)": compile_any([r"\bmake\b"]),
    "n8n": compile_any([r"\bn8n\b"]),
    "Framer (AI)": compile_any([r"\bframer\b"]),
    "Calendly": compile_any([r"\bcalendly\b"]),
    "Clipchamp": compile_any([r"\bclipchamp\b"]),
    "ComfyUI": compile_any([r"\bcomfyui\b"]),
    "Jupyter (AI)": compile_any([r"\bjupyter\b"]),
    "Google Colab (AI)": compile_any([r"\bcolab\b"]),
    "LangChain": compile_any([r"\blang\s*chain\b|\blangchain\b"]),

    # doc assistants / misc
    "ChatPDF": compile_any([r"\bchat\s*pdf\b", r"\bchatpdf\b"]),
    "ChatDOC": compile_any([r"\bchat\s*doc\b", r"\bchatdoc\b"]),
}

CANONICAL_ORDER = list(PATTERNS.keys())

# ---------- extraction & counting ----------
def extract_tools_from_cell(cell: str) -> Set[str]:
    if not isinstance(cell, str) or not cell.strip():
        return set()
    s = norm_text(cell)
    found: Set[str] = set()
    for canonical, pats in PATTERNS.items():
        if any(p.search(s) for p in pats):
            found.add(canonical)
    return found

def normalize_tools_column(
    df: pd.DataFrame,
    source_col: str = "ia_uses_tools",
    dest_col: str = "ia_uses_tools_normalized",
) -> pd.DataFrame:
    out = df.copy()
    if source_col in out.columns:
        out[dest_col] = out[source_col].apply(
            lambda x: "; ".join(sorted(extract_tools_from_cell(x))) or None
        )
    else:
        out[dest_col] = None
    return out

def count_tools(
    df: pd.DataFrame,
    source_col: str = "ia_uses_tools",
    unique_per_respondent: bool = True,
    filters: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    x = df
    if filters:
        for k, v in filters.items():
            if not v or k not in x.columns:
                continue
            if k == "gender" and v == "All":
                continue
            x = x[x[k] == v]

    counter = Counter()
    if unique_per_respondent:
        for raw in x[source_col].fillna("").astype(str):
            for tool in extract_tools_from_cell(raw):
                counter[tool] += 1
    else:
        for raw in x[source_col].fillna("").astype(str):
            s = norm_text(raw)
            for tool, pats in PATTERNS.items():
                if any(p.search(s) for p in pats):
                    counter[tool] += 1

    if not counter:
        return pd.DataFrame(columns=["tool", "count", "share"])

    total = sum(counter.values())
    rows = [{"tool": t, "count": c, "share": c / total} for t, c in counter.items()]
    order_index = {k: i for i, k in enumerate(CANONICAL_ORDER)}
    rows.sort(key=lambda r: (order_index.get(r["tool"], 10_000), -r["count"]))
    return pd.DataFrame(rows)
