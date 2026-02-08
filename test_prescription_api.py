"""
처방전 이미지 분석 API 테스트
"""
import requests
import json
import time

BACKEND_URL = "http://localhost:8000"
IMAGE_PATH = "img/KakaoTalk_20260208_142809689.jpg"

def test_analyze_with_image():
    print("=" * 60)
    print("처방전 이미지 분석 API 테스트")
    print("=" * 60)
    
    url = f"{BACKEND_URL}/api/analyze-with-image"
    
    with open(IMAGE_PATH, "rb") as f:
        files = {"file": ("prescription.jpg", f, "image/jpeg")}
        data = {
            "symptom": "",  # 빈 증상 - 약물에서 역추론 테스트
            "user_id": "test_user_v4"
        }
        
        print(f"\n📤 요청 전송 중... (symptom: 빈 값, user_id: test_user_v4)")
        start_time = time.time()
        
        try:
            response = requests.post(url, files=files, data=data, timeout=120)
            elapsed = time.time() - start_time
            
            print(f"\n⏱️ 응답 시간: {elapsed:.2f}초")
            print(f"📊 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                print("\n" + "=" * 40)
                print("📋 분석 결과")
                print("=" * 40)
                
                print(f"\n🔍 증상 요약: {result.get('symptom_summary', 'N/A')}")
                print(f"📈 신뢰도: {result.get('confidence_level', 'N/A')}")
                print(f"📂 출처: {result.get('source', 'N/A')}")
                print(f"🏷️ 매칭된 증상: {result.get('matched_symptom_name', 'N/A')}")
                
                # 식재료 추천
                ingredients = result.get('ingredients', [])
                print(f"\n🥬 추천 식재료: {len(ingredients)}개")
                for ing in ingredients:
                    print(f"  - {ing.get('modern_name', 'N/A')}: {ing.get('rationale_ko', '')[:50]}...")
                    if ing.get('youtube_video'):
                        print(f"    ▶️ 영상: {ing['youtube_video'].get('title', '')[:30]}...")
                    if ing.get('pubmed_papers'):
                        print(f"    📄 논문: {len(ing['pubmed_papers'])}편")
                
                # 레시피
                recipes = result.get('recipes', [])
                print(f"\n🍳 추천 레시피: {len(recipes)}개")
                for rec in recipes:
                    print(f"  - {rec.get('title', 'N/A')}: {rec.get('description', '')[:40]}...")
                
                # 약물 정보
                medications = result.get('medications', [])
                print(f"\n💊 약물 분석: {len(medications)}개")
                for med in medications:
                    print(f"  - {med.get('name', 'N/A')}")
                    info = med.get('info', '')
                    if info:
                        print(f"    {info[:100]}...")
                
                # 주의사항
                cautions = result.get('cautions', [])
                if cautions:
                    print(f"\n⚠️ 주의사항: {len(cautions)}개")
                    for c in cautions:
                        print(f"  - {c}")
                
                # 저장 결과
                return result
            else:
                print(f"\n❌ 오류: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("\n❌ 타임아웃 (120초 초과)")
            return None
        except Exception as e:
            print(f"\n❌ 예외 발생: {e}")
            return None

def test_get_prescriptions():
    print("\n" + "=" * 60)
    print("처방전 저장 확인 테스트")
    print("=" * 60)
    
    url = f"{BACKEND_URL}/api/prescriptions?user_id=test_user_v4"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            prescriptions = data.get('prescriptions', [])
            print(f"저장된 처방전 수: {len(prescriptions)}")
            
            for p in prescriptions:
                print(f"\n  📋 ID: {p.get('id')}")
                print(f"     🏥 병원: {p.get('hospital_name', 'N/A')}")
                print(f"     📅 날짜: {p.get('date', 'N/A')}")
                print(f"     💊 약물: {p.get('drugs', [])}")
                print(f"     🖼️ 이미지: {p.get('image_url', 'N/A')}")
            
            return prescriptions
    except Exception as e:
        print(f"오류: {e}")
        return []

if __name__ == "__main__":
    result = test_analyze_with_image()
    prescriptions = test_get_prescriptions()
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)
