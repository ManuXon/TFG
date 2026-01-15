import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class ChatbotConfig:
    openai_api_key: str
    model_name: str = "gpt-4o-mini"
    num_docs: int = 5
    temperature: float = 0
    max_tokens: int = 700

    persist_path: str = "./chatbot_db"
    collection_name: str = "mapai_dataset"

    # Optional CSV fallback (ONLY used if surveys_df is unavailable)
    dataset_path: str = ""

    # Reranking
    initial_retrieval_k: int = 10

    @classmethod
    def from_env(cls, env_path: str | None = None):
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()
            load_dotenv("../../.env")
            load_dotenv("../.env")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables or .env file")

        return cls(
            openai_api_key=api_key,
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            num_docs=int(os.getenv("NUM_DOCS", "5")),
            max_tokens=int(os.getenv("CHATBOT_MAX_TOKENS", "700")),
            dataset_path=os.getenv("DATASET_PATH", ""),
        )
