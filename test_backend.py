
import requests
import json
import time

print("Sending request...")
start = time.time()
try:
    resp = requests.post("http://localhost:8000/api/analyze", 
                         json={"symptom": "test", "medications": []},
                         timeout=60)
    print(f"Time: {time.time() - start:.2f}s")
    print(f"Status: {resp.status_code}")
    # print(f"Body: {resp.text[:500]}...") 
except Exception as e:
    print(f"Request failed: {e}")
