
import requests
import json

try:
    resp = requests.get("http://localhost:8000/api/prescriptions", timeout=5)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")
except Exception as e:
    print(f"Request failed: {e}")
