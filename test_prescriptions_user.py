
import requests
import json
import sys
import os

# 1. Add fake prescription via internal call (since upload needs file)
# But easier to just test GET endpoint filtering if I can inject data.
# I will use server's MedicationService directly via script?
# No, simpler: Just test that user_id param works and returns something (probably empty).

print("Testing GET /api/prescriptions?user_id=guest_123")
try:
    resp = requests.get("http://localhost:8000/api/prescriptions?user_id=guest_123", timeout=5)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")
except Exception as e:
    print(f"Request failed: {e}")
