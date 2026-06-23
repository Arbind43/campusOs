from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Supabase Postgres (direct or pooler connection)
    DATABASE_URL: str

    # Supabase project URL and JWT secret for token verification
    SUPABASE_URL: str
    SUPABASE_JWT_SECRET: str

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Groq API key for OCR and AI parsing
    GROQ_API_KEY: str = ""

    # Gemini API key for AI assistant fallback
    GEMINI_API_KEY: str = ""

    # AI Assistant settings
    AI_ASSISTANT_LLM_PROVIDER: str = "groq"  # "groq" or "gemini"
    AI_ASSISTANT_LLM_TIMEOUT: int = 10  # seconds
    AI_ASSISTANT_MAX_CONTEXT_LENGTH: int = 10  # messages

    # CampusFlow settings
    DEPLOY_ENV: str = "local"
    ATTENDANCE_THRESHOLD: int = 80
    CRITICAL_ATTENDANCE_FLOOR: int = 75

    # Firebase Cloud Messaging (optional)
    FCM_PROJECT_ID: str = ""
    FCM_CREDENTIALS_JSON: str = ""

    # AWS settings (optional)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = ""
    TEXTRACT_REGION: str = "us-east-1"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
