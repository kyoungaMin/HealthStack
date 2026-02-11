import requests
import json
import time
import os

BACKEND_URL = "http://localhost:8000"

# Use an existing image if available, otherwise create a dummy one
IMAGE_PATH = "data/uploads/1770544887.jpg"
if not os.path.exists(IMAGE_PATH):
    # Create a dummy image file if it doesn't exist
    with open("dummy_prescription.jpg", "wb") as f:
        f.write(b"dummy image content")
    IMAGE_PATH = "dummy_prescription.jpg"

def test_sample_data_workflow():
    print("=" * 60)
    print("임시 사용자 정보, 증상, 처방전 샘플 데이터 테스트")
    print("=" * 60)
    
    url = f"{BACKEND_URL}/api/analyze-with-image"
    
    # 1. Define sample data
    user_id = "temp_user_sample_001"
    symptom = "최근에 소화가 잘 안 되고 속이 자주 쓰립니다. 두통도 조금 있어요."
    
    # Sample medications (JSON format)
    # Simulating what the frontend would send if the user added medications manually
    medications_list = ["Tylenol", "Almagel"] 
    medications_json = json.dumps(medications_list)

    print(f"\n🏷️  사용자 ID: {user_id}")
    print(f"🤒 증상: {symptom}")
    print(f"💊 약물 목록 (JSON): {medications_json}")
    print(f"🖼️  처방전 이미지 경로: {IMAGE_PATH}")

    # 2. Send Request
    print(f"\n📤 데이터 전송 중...")
    start_time = time.time()
    
    try:
        with open(IMAGE_PATH, "rb") as f:
            files = {"file": ("sample_prescription.jpg", f, "image/jpeg")}
            data = {
                "symptom": symptom,
                "user_id": user_id,
                "medications_json": medications_json
            }
            
            response = requests.post(url, files=files, data=data, timeout=60)
            elapsed = time.time() - start_time
            
            print(f"\n⏱️  응답 시간: {elapsed:.2f}초")
            print(f"📊 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                print("\n" + "=" * 40)
                print("📋 분석 결과 확인")
                print("=" * 40)
                
                print(f"✅ 증상 요약: {result.get('symptom_summary', 'N/A')[:100]}...")
                print(f"✅ 신뢰도: {result.get('confidence_level', 'N/A')}")
                print(f"✅ 출처: {result.get('source', 'N/A')}")
                
                # Check if medications were processed
                meds = result.get('medications', [])
                if meds:
                    print(f"\n✅ 분석된 약물 ({len(meds)}개):")
                    for med in meds:
                        print(f"   - {med.get('name')}: {med.get('info', '')[:30]}...")
                else:
                    print("\n⚠️ 분석된 약물이 없습니다.")

                # Check ingredients
                ingredients = result.get('ingredients', [])
                if ingredients:
                    print(f"\n✅ 추천 식재료 ({len(ingredients)}개):")
                    for ing in ingredients:
                        print(f"   - {ing.get('modern_name')}: {ing.get('rationale_ko')[:30]}...")
                
                # Check matched symptom
                matched = result.get('matched_symptom_name')
                print(f"\n✅ 매칭된 증상: {matched}")

            else:
                print(f"\n❌ 오류 발생: {response.text}")
                
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")

if __name__ == "__main__":
    test_sample_data_workflow()
