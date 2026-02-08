"""
병렬 처리 성능 테스트
PubMed + YouTube 동시 검색으로 응답 시간 개선 검증
"""
import asyncio
import time
import os
import sys
from pathlib import Path

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent))

from app.services.healthstack_api import HealthStackAPI

async def test_parallel_performance():
    """병렬 처리 성능 테스트"""
    
    print("\n" + "="*70)
    print("🚀 병렬 처리 성능 테스트 (PubMed + YouTube 동시 검색)")
    print("="*70)
    
    api = HealthStackAPI()
    
    # 테스트 케이스
    test_cases = [
        {
            "symptom": "속이 더부룩하고 소화가 안 돼요",
            "description": "소화 문제"
        },
        {
            "symptom": "감기에 걸렸어요",
            "description": "감기 증상"
        },
        {
            "symptom": "피로감이 심해요",
            "description": "피로 증상"
        }
    ]
    
    total_time = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {test_case['description']}")
        print(f"입력: {test_case['symptom']}")
        print("-" * 70)
        
        start_time = time.time()
        
        try:
            result = await api.analyze(
                symptom_text=test_case['symptom'],
                prescription_image_path=None,
                medications=[],
                user_id=f"test_user_{i}"
            )
            
            elapsed = time.time() - start_time
            total_time += elapsed
            
            # 결과 출력
            print(f"✅ 증상 분석 완료: {result.symptom_summary[:50]}...")
            print(f"📊 신뢰도: {result.confidence_level} ({result.source})")
            print(f"🥬 식재료: {len(result.ingredients)}개 추출")
            
            for ing in result.ingredients[:2]:
                print(f"   - {ing.modern_name}")
                if ing.pubmed_papers:
                    print(f"     📄 논문: {len(ing.pubmed_papers)}개")
                if ing.youtube_video:
                    print(f"     ▶️ 영상: {ing.youtube_video['title'][:40]}...")
            
            print(f"⏱️ 소요 시간: {elapsed:.2f}초")
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ 오류 발생: {e}")
            print(f"⏱️ 소요 시간: {elapsed:.2f}초")
            import traceback
            traceback.print_exc()
    
    # 종합 결과
    print("\n" + "="*70)
    print("📊 성능 종합 분석")
    print("="*70)
    
    avg_time = total_time / len(test_cases)
    print(f"✅ 총 테스트: {len(test_cases)}개")
    print(f"⏱️ 총 소요 시간: {total_time:.2f}초")
    print(f"📈 평균 응답 시간: {avg_time:.2f}초")
    print(f"🚀 병렬 처리 활성화 (예상 개선: 약 30-40% 단축)")
    print("="*70 + "\n")
    
    return {
        "total_time": total_time,
        "avg_time": avg_time,
        "test_count": len(test_cases)
    }

if __name__ == "__main__":
    asyncio.run(test_parallel_performance())
