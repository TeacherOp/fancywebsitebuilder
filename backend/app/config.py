"""
Application Configuration.

Loads settings from environment variables and defines paths for data storage.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Config:
    """Application configuration."""

    # API Keys
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Claude Model
    CLAUDE_MODEL = "claude-opus-4-5-20251101"
    CLAUDE_MAX_TOKENS = 16000
    CLAUDE_TEMPERATURE = 0.2

    # Data directories
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    CHATS_DIR = DATA_DIR / "chats"
    AGENTS_DIR = DATA_DIR / "agents"
    WEBSITES_DIR = DATA_DIR / "websites"

    # Website agent settings
    WEBSITE_AGENT_MAX_ITERATIONS = 30

    @classmethod
    def ensure_directories(cls):
        """Create data directories if they don't exist."""
        cls.CHATS_DIR.mkdir(parents=True, exist_ok=True)
        cls.AGENTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.WEBSITES_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        missing = []
        if not cls.ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")

        if missing:
            print(f"Warning: Missing environment variables: {', '.join(missing)}")
            return False
        return True
