
import os
from pathlib import Path
import google.generativeai as genai

# Manual .env loading to avoid dependency issues
env_path = Path(__file__).parent.parent.parent / ".env"
API_KEY = None

# Try to read from .env file directly
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('GEMINI_API_KEY='):
                API_KEY = line.split('=', 1)[1].strip()
                break

# Fallback to environment variable
if not API_KEY:
    API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not found in .env or environment")

# Configure GenAI
genai.configure(api_key=API_KEY)

# Model Definitions
# User requested 2.5 Flash
MODEL_NAME = "gemini-2.5-flash" 

GENERATION_CONFIG = {
  "temperature": 0.2,  # Low temperature for deterministic/factual responses
  "top_p": 0.8,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

SAFETY_SETTINGS = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
]
