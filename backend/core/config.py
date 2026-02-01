import os
import json
from pydantic_settings import BaseSettings
from typing import List, Dict, Any

class Settings(BaseSettings):
    APP_NAME: str = "Atlas"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://127.0.0.1:4202",
        "http://127.0.0.1:4204"
    ]
    DEBUG: bool = True
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    CONFIG_DIR: str = os.path.join(BASE_DIR, "config")
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    
    # Database
    DATABASE_URL: str = f"sqlite:///C:/Users/mhkem/OneDrive/Documents/databasedev/atlas.db"
    
    # Integrations
    ALTIMETER_PATH: str = r"c:/Users/mhkem/.altimeter"
    OBSIDIAN_KNOWLEDGE_PATH: str = r"C:\Users\mhkem\.obsidian\MKULTRA\CODEX\@Knowledge"
    ONEDRIVE_PATH: str = r"c:\Users\mhkem\OneDrive\Documents\Davis Projects OneDrive"
    
    # Secrets (Loaded from secrets.json or env vars)
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "insecure-fallback-development-only")
    
    class Config:
        env_file = ".env"

    def load_secrets(self):
        # 1. Local project config
        secrets_path = os.path.join(self.CONFIG_DIR, "secrets.json")
        # 2. User vault (high priority)
        vault_path = os.path.join(os.path.expanduser("~"), ".vault", "secrets.json")
        
        paths = [secrets_path, vault_path]
        
        for p in paths:
            if os.path.exists(p):
                try:
                    with open(p, "r") as f:
                        secrets = json.load(f)
                        # Map keys to settings attributes
                        if "GOOGLE_API_KEY" in secrets and not self.GEMINI_API_KEY:
                            self.GEMINI_API_KEY = secrets["GOOGLE_API_KEY"]
                        if "JWT_SECRET_KEY" in secrets:
                            self.JWT_SECRET_KEY = secrets["JWT_SECRET_KEY"]
                        # Load any other keys that match settings attributes
                        for key, value in secrets.items():
                            if hasattr(self, key):
                                setattr(self, key, value)
                except Exception as e:
                    print(f"Error loading secrets from {p}: {e}")

settings = Settings()
settings.load_secrets()

if settings.JWT_SECRET_KEY in ["your-secret-key-here", "insecure-fallback-development-only"]:
    print("\n" + "!" * 50)
    print("SECURITY WARNING: Using default or insecure JWT_SECRET_KEY.")
    print("Please set a secure JWT_SECRET_KEY in .vault/secrets.json")
    print("!" * 50 + "\n")
