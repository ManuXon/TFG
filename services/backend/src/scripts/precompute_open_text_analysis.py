# scripts/precompute_open_text_analysis.py
import os
import pandas as pd
from src.utils.data_loader import load_surveys_data
from src.utils.open_text_agent import (
    OpenTextRowAnalysis,
    OpenTextColumnAnalysis,
    OPEN_TEXT_DIR,
    QUESTION_TOPICS,
    FINE_TO_COARSE,
    call_llm_for_open_text,
    is_trivial_short_answer,
)


def _analyze_single_text(text: str, column_id: str) -> dict:
    """
    Real LLM-based analysis.

    Returns:
        {
            "sentiment": ... (coarse)
            "sentiment_fine": ... (canonical 6-way)
            "cluster_id": ...,
            "cluster_label": ...,
            "main_topics": [...],
            "english_text": "...",
        }
    """
    if not text or not str(text).strip():
        # empty text → we skip it at caller level anyway, but keep a safe fallback
        return {
            "sentiment": "neutral",
            "sentiment_fine": "neutral",
            "cluster_id": -1,
            "cluster_label": "No content",
            "main_topics": [],
            "english_text": "",
        }

    # TRIVIAL ONE-WORD ANSWERS: do NOT call the LLM
    if is_trivial_short_answer(text):
        return {
            "sentiment": "neutral",
            "sentiment_fine": "neutral",
            "cluster_id": -1,
            "cluster_label": "No content (short answer)",
            "main_topics": [],
            "english_text": text,
        }

    result = call_llm_for_open_text(str(text), column_id)

    return {
        "sentiment": result["sentiment"],
        "sentiment_fine": result["sentiment_fine"],
        "cluster_id": result["cluster_id"],
        "cluster_label": result["cluster_label"],
        "main_topics": result["main_topics"],
        "english_text": result["english_text"],
    }


def analyze_column(df: pd.DataFrame, text_col: str, question_id: str) -> pd.DataFrame:
    if text_col not in df.columns:
        print(f"[ERROR] Column '{text_col}' NOT in dataframe for question_id='{question_id}'.")
        return OpenTextColumnAnalysis(question_id=question_id, rows=[]).to_dataframe()

    n_total = 0
    n_nonempty = 0
    n_skipped_trivial = 0
    rows = []

    for _, row in df.iterrows():
        n_total += 1
        text = row.get(text_col)

        if pd.isna(text) or not str(text).strip():
            # completely empty → ignore
            continue

        text_str = str(text)
        n_nonempty += 1

        # Skip trivial one-word junk *entirely* (they won't appear in the parquet)
        if is_trivial_short_answer(text_str):
            n_skipped_trivial += 1
            continue

        res = _analyze_single_text(text_str, question_id)
        rows.append(
            OpenTextRowAnalysis(
                row_id=int(row["row_id"]),
                sentiment=res["sentiment"],
                sentiment_fine=res["sentiment_fine"],
                cluster_id=int(res["cluster_id"]),
                cluster_label=str(res["cluster_label"]),
                main_topics=res["main_topics"],
                english_text=res["english_text"],
            )
        )

    print(
        f"[STATS] {question_id}: total rows={n_total}, "
        f"non-empty texts={n_nonempty}, skipped_trivial={n_skipped_trivial}, "
        f"analyzed={len(rows)} from column '{text_col}'"
    )

    return OpenTextColumnAnalysis(question_id=question_id, rows=rows).to_dataframe()


def main():
    os.makedirs(OPEN_TEXT_DIR, exist_ok=True)

    df = load_surveys_data()

    mapping = {
        "per_ia_oporiscuni_altres": "per_ia_oporiscuni_altres_text",
        "per_ia_posicprof_perque": "per_ia_posicprof_perque_text",
        "for_ia_neceformat_altres": "for_ia_neceformat_altres_text",
        "comments": "comments_text",
    }

    print("=== OPEN TEXT COLUMN NON-EMPTY COUNTS ===")
    for qid, col in mapping.items():
        if col in df.columns:
            nonempty = df[col].apply(
                lambda x: bool(str(x).strip()) if pd.notna(x) else False
            ).sum()
            print(f"  - {qid} ({col}): {nonempty} non-empty rows")
        else:
            print(f"  - {qid} ({col}): MISSING COLUMN")
    print("=========================================")

    for qid, col in mapping.items():
        print(f"Analyzing {qid} from column {col}...")
        adf = analyze_column(df, col, qid)

        out_path = os.path.join(OPEN_TEXT_DIR, f"{qid}_analysis.parquet")
        print(f"  -> writing {len(adf)} rows to {out_path}")
        adf.to_parquet(out_path)

    print("Done.")


if __name__ == "__main__":
    main()
