from dotenv import load_dotenv
from pathlib import Path
import os

# Absolute path to backend root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Explicitly load .env
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    )
    EMAIL_HOST:str=os.getenv("EMAIL_HOST")
    EMAIL_PORT:str=os.getenv("EMAIL_PORT")
    EMAIL_USERNAME:str=os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD:str=os.getenv("EMAIL_PASSWORD")
    EMAIL_FROM:str =os.getenv("EMAIL_FROM")
    REMINDER_WINDOW_MINUTES:int=int(os.getenv("REMINDER_WINDOW_MINUTES",10))
    GEMINI_API_KEY:str=os.getenv("GEMINI_API_KEY")


settings = Settings()

# DEBUG (temporary)
print("✅ DATABASE_URL =", settings.DATABASE_URL)
print(f"✅ SECRET_KEY loaded: {settings.SECRET_KEY is not None}")
print(f"✅ ALGORITHM: {settings.ALGORITHM}")