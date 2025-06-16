from pathlib import Path
import logging
import os
from dotenv import load_dotenv, find_dotenv

# ── logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ── locate the .env file ───────────────────────────────────────────────────────
dotenv_path = Path(
    os.getenv("DOTENV_FILE", find_dotenv(usecwd=True))  # respects $DOTENV_FILE first
).expanduser()

if not dotenv_path or not dotenv_path.is_file():
    logging.error("Could not find .env file (looked for %s)", dotenv_path or "<none>")

logging.info("Loading environment variables from: %s", dotenv_path)

# `override=True` clobbers any values already in the shell
load_dotenv(dotenv_path, override=True)

# ── helper ─────────────────────────────────────────────────────────────────────
def get_required_env_var(key: str) -> str:
    value = os.getenv(key)
    if not value:
        logging.error("Missing required environment variable: %s", key)
    logging.debug("Using %s = %s", key, value if len(value) < 10 else value[:6] + "…")
    return value

# ── fetch the goodies ──────────────────────────────────────────────────────────
OPENAI_API_KEY      = get_required_env_var("OPENAI_API_KEY")
QDRANT_API_KEY      = get_required_env_var("QDRANT_API_KEY")
QDRANT_CLIENT_URL   = get_required_env_var("QDRANT_CLIENT_URL")


def main():
    try:
        # Access variables safely with defaults if needed
        openai_api_key = get_required_env_var("OPENAI_API_KEY")
        qdrant_api_key = get_required_env_var("QDRANT_API_KEY")
        qdrant_client_url = get_required_env_var("QDRANT_CLIENT_URL")
        print("Environment variables loaded successfully:")
        print(f"OPENAI_API_KEY: {openai_api_key}")
        print(f"QDRANT_API_KEY: {qdrant_api_key}")
        print(f"QDRANT_CLIENT_URL: {qdrant_client_url}")
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()