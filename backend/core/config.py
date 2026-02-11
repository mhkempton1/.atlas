import os
import json
import secrets
from pydantic_settings import BaseSettings
from typing import List, Dict, Any

class Settings(BaseSettings):
    APP_NAME: str = "Atlas"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://127.0.0.1:4202",
        "http://127.0.0.1:4204",
        "http://localhost:4202",
        "http://localhost:4204",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000"
    ]
    DEBUG: bool = True
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    CONFIG_DIR: str = os.path.join(BASE_DIR, "config")
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/atlas.db")
    
    # Integrations
    ALTIMETER_PATH: str = os.getenv("ALTIMETER_PATH", "./data/altimeter")
    OBSIDIAN_KNOWLEDGE_PATH: str = os.getenv("OBSIDIAN_KNOWLEDGE_PATH", "./data/knowledge")
    ONEDRIVE_PATH: str = os.getenv("ONEDRIVE_PATH", "./data/onedrive")
    
    # Communication Protocols
    COMMUNICATION_PROVIDER: str = "google" # "google", "imap"
    IMAP_HOST: str = ""
    IMAP_PORT: int = 993
    IMAP_USER: str = ""
    IMAP_PASSWORD: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # Secrets (Loaded from secrets.json or env vars)
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    
    # Strata Permissions Definition
    STRATA_PERMISSIONS: Dict[int, List[str]] = {
        1: ["public", "safety", "sops"], # Field
        2: ["public", "safety", "sops", "schedules", "rosters"], # Supervision
        3: ["public", "safety", "sops", "schedules", "rosters", "budgets_limited"], # Management
        4: ["public", "safety", "sops", "schedules", "rosters", "budgets_limited", "hr", "strategy"], # Executive
        5: ["*"] # Developer / Eyes Only
    }

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
                        secret_data = json.load(f)
                        # Map keys to settings attributes
                        if "GOOGLE_API_KEY" in secret_data and not self.GEMINI_API_KEY:
                            self.GEMINI_API_KEY = secret_data["GOOGLE_API_KEY"]
                        if "JWT_SECRET_KEY" in secret_data:
                            self.JWT_SECRET_KEY = secret_data["JWT_SECRET_KEY"]
                        # Load any other keys that match settings attributes
                        for key, value in secret_data.items():
                            if hasattr(self, key):
                                setattr(self, key, value)
                except Exception as e:
                    print(f"Error loading secrets from {p}: {e}")

        # Security: If no secret key found after checking env and secrets, generate a secure random one
        if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY in ["your-secret-key-here", "insecure-fallback-development-only"]:
             print("\n" + "!" * 50)
             print("SECURITY WARNING: No secure JWT_SECRET_KEY found.")
             print("Generating a random key for this session (persistence will be lost on restart).")
             print("To fix: Set JWT_SECRET_KEY in .vault/secrets.json")
             print("!" * 50 + "\n")
             self.JWT_SECRET_KEY = secrets.token_urlsafe(32)

settings = Settings()
settings.load_secrets()
