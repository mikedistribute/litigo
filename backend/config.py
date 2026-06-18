import os
from dotenv import load_dotenv

_backend_dir = os.path.dirname(os.path.abspath(__file__))
# Charger d'abord backend/.env puis la racine du dépôt (emplacements usuels)
load_dotenv(os.path.join(_backend_dir, ".env"))
load_dotenv(os.path.join(_backend_dir, "..", ".env"))

GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "")

GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
GEMINI_MODEL_FREE = "gemini-3.1-flash-lite-preview"