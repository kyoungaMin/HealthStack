"""
백엔드 API 연결 테스트
"""
import requests
import json

BACKEND_URL = 'http://localhost:8000'

def test_health():
    """헬스체크"""
    try:
        res = requests.get(f'{BACKEND_URL}/', timeout=5)
        print(f"✅ Health Check: {res.status_code}")
        print(f"   Response: {res.json()}")
    except Exception as e:
        print(f"❌ Health Check Error: {e}")

def test_analyze():
    """증상 분석 API 테스트"""
    try:
        payload = {
            "symptom": "감기에 걸렸어요",
            "medications": []
        }
        res = requests.post(f'{BACKEND_URL}/api/analyze', json=payload, timeout=30)
        print(f"\n✅ Analyze API: {res.status_code}")
        if res.ok:
            data = res.json()
            print(f"   Summary: {data.get('symptom_summary', 'N/A')[:100]}")
        else:
            print(f"   Error: {res.text[:200]}")
    except Exception as e:
        print(f"❌ Analyze API Error: {e}")

def test_analyze_with_image():
    """이미지 분석 API 테스트"""
    import os
    
    # 테스트 이미지 찾기
    upload_dir = "data/uploads"
    if not os.path.exists(upload_dir):
        print(f"❌ Upload directory not found: {upload_dir}")
        return
    
    files = sorted(os.listdir(upload_dir), reverse=True)
    if not files:
        print(f"❌ No images in {upload_dir}")
        return
    
    image_path = os.path.join(upload_dir, files[0])
    print(f"\n📷 Testing with image: {files[0]}")
    
    try:
        with open(image_path, 'rb') as f:
            files_to_send = {'file': f}
            data = {
                'symptom': '감기에 걸렸어요',
                'user_id': 'test_user'
            }
            res = requests.post(
                f'{BACKEND_URL}/api/analyze-with-image',
                files=files_to_send,
                data=data,
                timeout=60
            )
        print(f"✅ Analyze-with-Image API: {res.status_code}")
        if res.ok:
            result = res.json()
            print(f"   Summary: {result.get('symptom_summary', 'N/A')[:100]}")
            print(f"   Ingredients: {len(result.get('ingredients', []))} items")
        else:
            print(f"   Error: {res.text[:300]}")
    except Exception as e:
        print(f"❌ Analyze-with-Image API Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Backend API Connection Test")
    print("=" * 60)
    test_health()
    test_analyze()
    test_analyze_with_image()
    print("\n" + "=" * 60)
