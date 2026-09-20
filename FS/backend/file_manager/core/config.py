from pathlib import Path
import os
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    def __init__(self):
        self.root: Path | None = None

        self.host = "0.0.0.0"
        self.port = int(os.environ.get("PORT4FS", 3000))

        self.password = "PeergosRules!"

        self.debug = True

        self.secret_key = "mysecretkeyforremotefilesystemserver"

        self.secure_cookies = os.environ.get("SECURE_COOKIES", "True").lower() == "true"

        cors_origins_str = os.environ.get("CORS_ORIGINS4FS", "http://localhost:5173")
        self.cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

        self.campusgpt_api_url = os.environ.get("CAMPUSGPT_API_URL", "http://127.0.0.1:8000")


settings = Settings()