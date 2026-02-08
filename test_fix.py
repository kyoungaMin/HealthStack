"""
처방전 분석 수정사항 테스트
약물 추출, 병원명 추출, 처방전 저장, 증상 역추론 확인
"""
import asyncio
import os
import sys
from pathlib import Path

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent))

from app.services.healthstack_api import HealthStackAPI

async def test_prescription_analysis():
    """처방전 분석 테스트"""
    print("=" * 60)
    print("🔬 처방전 분석 테스트 시작")
    print("=" * 60)
    
    # 첨부 이미지 경로 (테스트용 경로)
    test_image_path = "test_prescription.jpg"
    
    # 처방전 이미지가 없으면 테스트용 더미 이미지 생성
    if not os.path.exists(test_image_path):
        print(f"⚠️  테스트 이미지 '{test_image_path}'를 찾을 수 없습니다.")
        print("💡 수동으로 처방전 이미지를 '{}'에 저장하세요.".format(test_image_path))
        return
    
    api = HealthStackAPI()
    
    try:
        print("\n📸 이미지 분석 중...")
        result = await api.analyze(
            symptom_text=None,  # 역추론 테스트
            prescription_image_path=test_image_path,
            user_id="test_user_fix_v1"
        )
        
        print("\n✅ 분석 완료!")
        print("-" * 60)
        
        # 1. 약물 추출 결과 확인
        print("\n📋 약물 정보:")
        if result.medications:
            print(f"   추출된 약물 수: {len(result.medications)}")
            for med in result.medications[:5]:
                print(f"   - {med.get('name', 'N/A')}")
        else:
            print("   ❌ 약물 정보 없음")
        
        # 2. 증상 역추론 결과 확인
        print("\n🎯 증상 분석:")
        print(f"   요약: {result.symptom_summary[:80]}...")
        print(f"   신뢰도: {result.confidence_level}")
        print(f"   출처: {result.source}")
        if result.matched_symptom_name:
            print(f"   매칭된 증상: {result.matched_symptom_name}")
        
        # 3. 추천 식재료
        print("\n🥗 추천 식재료:")
        if result.ingredients:
            print(f"   수량: {len(result.ingredients)}")
            for ing in result.ingredients[:3]:
                print(f"   - {ing.modern_name}: {ing.direction}")
        else:
            print("   추천 식재료 없음")
        
        # 4. 처방전 저장 확인
        print("\n💾 처방전 저장 확인:")
        import json
        db_path = "data/prescriptions.json"
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                prescriptions = json.load(f)
            
            # 가장 최신 처방전 확인
            if prescriptions:
                latest = prescriptions[-1]
                print(f"   ✅ 저장됨")
                print(f"   ID: {latest.get('id')}")
                print(f"   병원: {latest.get('hospital_name', 'N/A')}")
                print(f"   약물: {latest.get('drugs', [])}")
                print(f"   저장일: {latest.get('date')}")
            else:
                print(f"   ❌ 저장된 처방전 없음")
        else:
            print(f"   ❌ DB 파일 없음: {db_path}")
        
        print("\n" + "=" * 60)
        print("✨ 테스트 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_prescription_analysis())
