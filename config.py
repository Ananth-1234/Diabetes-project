import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Secret key for sessions (CHANGE THIS IN PRODUCTION)
    SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key_change_this")

    # Database configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE = os.path.join(BASE_DIR, "database.db")

    # Model Path
    MODEL_PATH = os.path.join(BASE_DIR, "diabetes_xgboost_model.pkl")

    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Gemini Model Name
    GEMINI_MODEL = "gemini-2.5-flash-lite"

    # Debug mode
    DEBUG = True