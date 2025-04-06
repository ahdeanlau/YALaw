from dotenv import load_dotenv
import os

load_dotenv()  # load from .env in project root

def get_required_env_var(key: str) -> str:
    value = os.getenv(key)
    if value is None or value == "":
        raise ValueError(f"Missing required environment variable: {key}")
    return value

# Access variables safely with defaults if needed
OPENAI_API_KEY = get_required_env_var("OPENAI_API_KEY")
