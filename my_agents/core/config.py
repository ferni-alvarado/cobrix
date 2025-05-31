import os

import openai
from dotenv import load_dotenv

# Load .env variables
load_dotenv(override=True)

# Disable tracing since we're not connected to a supported tracing provider
TRACING_ENABLED = os.getenv("TRACING", "false").lower() == "true"

# Setup OpenAI client (usando la API oficial, no GitHub ni Azure)
#client = openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

#MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o")


# Setup OpenAI client for GitHub Models
client = openai.AsyncOpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GITHUB_TOKEN"],
)

# Get model name from env (or default)
MODEL_NAME = os.getenv("GITHUB_MODEL", "gpt-4o")


BACK_URLS = {
    "success": os.getenv("MP_SUCCESS_URL", "https://example.com/success"),
    "failure": os.getenv("MP_FAILURE_URL", "https://example.com/failure"),
    "pending": os.getenv("MP_PENDING_URL", "https://example.com/pending"),
}
