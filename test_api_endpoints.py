"""
API 엔드포인트 테스트 스크립트
"""
import requests
import json

# 서버 URL
BASE_URL = "http://localhost:8000"

# 테스트 1: 간단한 증상 분석
print("\n" + "="*70)
print("테스트 1: 간단한 증상 분석 (/api/analyze)")
print("="*70)

test_data = {
    "symptom": "감기에 걸렸어요",
    "medications": [],
    "user_id": "test_user_001"
}

try:
    response = requests.post(f"{BASE_URL}/api/analyze", json=test_data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 성공!")
        print(f"증상 요약: {result['symptom_summary'][:50]}...")
        print(f"신뢰도: {result['confidence_level']}")
        print(f"식재료: {len(result['ingredients'])}개")
    else:
        print(f"❌ 오류: {response.status_code}")
        print(f"상세: {response.text}")
except Exception as e:
    print(f"❌ 요청 실패: {e}")

# 테스트 2: 처방전 이미지 분석
print("\n" + "="*70)
print("테스트 2: 처방전 이미지 분석 (/api/analyze-with-image)")
print("="*70)

# 처방전 이미지 파일 선택
image_path = "img/KakaoTalk_20260208_142809689.jpg"

try:
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {'symptom': '', 'user_id': 'test_user_ocr'}
        
        response = requests.post(
            f"{BASE_URL}/api/analyze-with-image",
            files=files,
            data=data
        )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 성공!")
        print(f"증상 요약: {result['symptom_summary'][:50]}...")
        print(f"신뢰도: {result['confidence_level']}")
        print(f"식재료: {len(result['ingredients'])}개")
        
        if result['ingredients']:
            print(f"\n추천 식재료:")
            for ing in result['ingredients'][:2]:
                print(f"  - {ing['modern_name']}: {ing['rationale_ko'][:40]}...")
    else:
        print(f"❌ 오류: {response.status_code}")
        print(f"상세: {response.text}")
except Exception as e:
    print(f"❌ 요청 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
