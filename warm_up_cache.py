import requests
import json
import time
import os

BACKEND_URL = "http://localhost:8000"
SAMPLE_FILE = "data/sample_test_cases.json"
DUMMY_IMAGE = "dummy_prescription.jpg"

if not os.path.exists(DUMMY_IMAGE):
    with open(DUMMY_IMAGE, "wb") as f:
        f.write(b"dummy content")

def warm_up_cache():
    print("=" * 60)
    print("🔥 캐시 워밍(Cache Warming) 시작")
    print("API 제한을 피하기 위해 천천히 실행합니다. (요청 간 20초 대기)")
    print("=" * 60)
    
    with open(SAMPLE_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    for i, case in enumerate(cases):
        label = f"[{i+1}/{len(cases)}] {case['id']}"
        print(f"\n🚀 {label} 처리 중... ({case['symptom'][:15]}...)")
        
        try:
            # 먼저 이미 캐시되어 있는지 확인하기 위해 짧은 타임아웃으로 시도해볼 수도 있지만,
            # analyze-with-image 엔드포인트는 내부적으로 캐시를 체크합니다.
            
            with open(DUMMY_IMAGE, "rb") as f:
                files = {"file": ("test.jpg", f, "image/jpeg")}
                data = {
                    "symptom": case["symptom"],
                    "user_id": case["user_id"],
                    "medications_json": json.dumps(case["medications"])
                }
                
                # 60초 타임아웃
                start = time.time()
                response = requests.post(f"{BACKEND_URL}/api/analyze-with-image", files=files, data=data, timeout=90)
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    res = response.json()
                    source = res.get('source', 'unknown')
                    print(f"   ✅ 성공! ({elapsed:.1f}초) - Source: {source}")
                    print(f"   💊 결과: {res.get('matched_symptom_name')}")
                else:
                    print(f"   ❌ 실패 (HTTP {response.status_code})")
                    print(f"   Reason: {response.text[:100]}")
                    
        except requests.exceptions.Timeout:
            print("   ⏰ 타임아웃 (서버가 응답하지 않음)")
        except Exception as e:
            print(f"   ⚠️ 오류: {e}")
            
        # API Rate Limit 방지용 대기
        if i < len(cases) - 1:
            print("   ⏳ 20초 대기 중...")
            time.sleep(20)

if __name__ == "__main__":
    warm_up_cache()
