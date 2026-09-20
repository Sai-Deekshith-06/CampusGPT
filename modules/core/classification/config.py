import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# Load .env from the modules project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

@dataclass(frozen=True)
class ClassifierConfig:
    # Text slicing limits
    header_word_limit: int = 1500
    
    # Confidence gating
    high_confidence_threshold: float = 0.85
    min_review_threshold: float = 0.60
    
    # Model configuration
    llm_model_name: str = "gemini-2.5-flash"
    api_key: str | None = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("API_KEY")
    )


config = ClassifierConfig()