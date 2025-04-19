import os

import openai
from dotenv import load_dotenv

# Load .env variables
load_dotenv(override=True)

# Disable tracing since we're not connected to a supported tracing provider
TRACING_ENABLED = os.getenv("TRACING", "false").lower() == "true"

# Setup OpenAI client for GitHub Models
client = openai.AsyncOpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GITHUB_TOKEN"],
)

# Get model name from env (or default)
MODEL_NAME = os.getenv("GITHUB_MODEL", "gpt-4o")
