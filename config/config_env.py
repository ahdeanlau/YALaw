from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()  # load from .env in project root

def get_required_env_var(key: str) -> str:
    value = os.getenv(key)
    if value is None or value == "":
        logging.error(f"Failed to get required environment variable: {key}")
        raise ValueError(f"Missing required environment variable: {key}")
    return value

# Access variables safely with defaults if needed
OPENAI_API_KEY = get_required_env_var("OPENAI_API_KEY")
QDRANT_API_KEY = get_required_env_var("QDRANT_API_KEY")
QDRANT_CLIENT_URL = get_required_env_var("QDRANT_CLIENT_URL")
