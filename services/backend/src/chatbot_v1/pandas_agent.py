from __future__ import annotations

from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PandasDatasetAgent:
    """Agent that can execute Python code on the dataset"""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o-mini",
        dataset_path: Optional[str] = None,
        surveys_df: Optional[pd.DataFrame] = None,
    ):
        if surveys_df is not None:
            self.df = surveys_df
        else:
            if not dataset_path:
                raise ValueError("PandasDatasetAgent needs either surveys_df or dataset_path")
            self.df = pd.read_csv(dataset_path)

        logger.info(f"Pandas agent loaded dataset: {len(self.df)} rows, {len(self.df.columns)} columns")

        self.llm = ChatOpenAI(
            temperature=0,
            model=model_name,
            api_key=api_key,
            max_tokens=2000,
        )

        self.agent = create_pandas_dataframe_agent(
            self.llm,
            self.df,
            agent_type="openai-tools",
            verbose=True,
            allow_dangerous_code=True,
            max_iterations=20,
            prefix="""You are a data analysis expert working with a pandas DataFrame called `df`.

The DataFrame is ALWAYS available in your environment - you never need to reload or reimport it.

STRING HANDLING CRITICAL:
- When working with Catalan text containing apostrophes, ALWAYS use DOUBLE QUOTES.

ANALYSIS RULES:
- Prefer robust operations: value_counts, groupby, mean, median, corr.
- If columns are missing, inspect df.columns and adapt.
""",
        )

    def query(self, question: str) -> str:
        try:
            logger.info(f"Pandas agent executing: {question}")
            result = self.agent.invoke({"input": question})
            return result.get("output", "No result generated")
        except Exception as e:
            logger.error(f"Error in pandas agent: {e}")
            return f"I encountered an error while analyzing the data: {str(e)}"
