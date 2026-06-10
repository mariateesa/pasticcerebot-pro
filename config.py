import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"
RICETTE_DIR = os.path.join(os.path.dirname(__file__), "data", "ricette")
CHUNK_SIZE = 400
TOP_K = 3
