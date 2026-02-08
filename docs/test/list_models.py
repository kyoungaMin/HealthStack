import google.generativeai as genai
import os
import sys

# Add project root to path to find .env if needed, but load_dotenv handles it.
# Assuming .env is in project root.
from dotenv import load_dotenv

# Load .env from project root
# c:\AI\dev5\.env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
if os.path.exists('c:\\AI\\dev5\\.env'):
    load_dotenv('c:\\AI\\dev5\\.env')
else:
    load_dotenv()

api_key = os.getenv("API_KEY")
if not api_key:
    print("API_KEY not found in env")
else:
    print(f"API_KEY found: {api_key[:5]}...")

genai.configure(api_key=api_key)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
