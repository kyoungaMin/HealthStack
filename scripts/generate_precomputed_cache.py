"""
Pre-computed 캐시 데이터 생성 스크립트
자주 조회되는 질환에 대한 분석 결과를 미리 생성하여 캐시에 저장

사용법:
  python scripts/generate_precomputed_cache.py
"""
import os
import sys
import json
import asyncio
from datetime import datetime

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.analyze_service import AnalyzeService
from app.utils.cache_manager import CacheManager
from dataclasses import asdict


# 자주 조회되는 질환 목록 (TEST_REPORT_v1.md 기반)
COMMON_DISEASES = [
    {
        "id": "cold",
        "symptom": "콧물이 계속 나고 머리가 지끈거려요",
        "medications": ["Tylenol ER", "Sudafed", "Mucosolvan"],
        "description": "감기 (Cold)"
    },
    {
        "id": "hypertension",
        "symptom": "뒷목이 뻐근하고 자주 어지러워요",
        "medications": ["Amlodipine", "Valsartan", "Aspirin Protect"],
        "description": "고혈압 (Hypertension)"
    },
    {
        "id": "diabetes",
        "symptom": "갈증이 많고 자주 소변을 봐요",
        "medications": ["Metformin", "Diamicron", "Januvia"],
        "description": "당뇨 (Diabetes)"
    },
    {
        "id": "insomnia",
        "symptom": "밤에 잠이 잘 안 오고 자정이 넘어서야 겨우 잠듭니다",
        "medications": ["Stilnox", "Circadin"],
        "description": "불면증 (Insomnia)"
    },
    {
        "id": "indigestion",
        "symptom": "소화가 잘 안 되고 명치가 답답해요",
        "medications": ["Nexium", "Almagel", "Gasmotin", "Bearse"],
        "description": "소화불량 (Indigestion)"
    },
    {
        "id": "muscle_pain",
        "symptom": "운동 후 어깨와 허리가 쑤시고 아파요",
        "medications": ["Naxen", "Somalgen", "Mydocalm"],
        "description": "근육통 (Muscle Pain)"
    },
    {
        "id": "allergy",
        "symptom": "재채기를 자주 하고 눈이 가려워요",
        "medications": ["Zyrtec", "Allegra", "Avamys Spray"],
        "description": "알러지 (Allergy)"
    },
    {
        "id": "anxiety",
        "symptom": "가슴이 두근거리고 불안감이 많아요",
        "medications": ["Indenol", "Xanax", "Lexapro"],
        "description": "불안장애 (Anxiety Disorder)"
    },
    {
        "id": "dermatitis",
        "symptom": "피부가 가렵고 발진이 생겨요",
        "medications": ["Dermovate", "Zyrtec", "Prednisolone"],
        "description": "피부염 (Dermatitis)"
    },
    {
        "id": "chronic_fatigue",
        "symptom": "항상 피곤하고 무기력해요",
        "medications": ["Ursa", "Aronamin Gold", "Godex"],
        "description": "만성피로 (Chronic Fatigue)"
    }
]


async def generate_precomputed_cache():
    """자주 조회되는 질환에 대한 캐시 데이터 생성"""
    
    analyze_service = AnalyzeService()
    cache_manager = CacheManager()
    
    print("\n" + "="*70)
    print("🚀 Pre-computed 캐시 데이터 생성 시작")
    print("="*70)
    
    results = {
        "generated_at": datetime.now().isoformat(),
        "total_diseases": len(COMMON_DISEASES),
        "cached_diseases": [],
        "failed_diseases": []
    }
    
    for idx, disease in enumerate(COMMON_DISEASES, 1):
        try:
            print(f"\n[{idx}/{len(COMMON_DISEASES)}] {disease['description']} 분석 중...")
            
            # 분석 실행
            start_time = datetime.now()
            analysis_result = await analyze_service.analyze_symptom(
                symptom_text=disease['symptom'],
                current_meds=disease['medications']
            )
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # 결과를 캐시에 저장
            cache_key = f"{disease['symptom']}|{','.join(disease['medications'])}"
            
            # AnalysisResult를 JSON 직렬화 가능한 형태로 변환
            cache_data = {
                "symptom_summary": analysis_result.symptom_summary,
                "confidence_level": analysis_result.confidence_level,
                "source": analysis_result.source,
                "matched_symptom_name": analysis_result.matched_symptom_name,
                "cautions": analysis_result.cautions,
                "ingredients": [
                    {
                        "rep_code": ing.rep_code,
                        "modern_name": ing.modern_name,
                        "rationale_ko": ing.rationale_ko,
                        "direction": ing.direction,
                        "priority": ing.priority,
                        "evidence_level": ing.evidence_level
                    }
                    for ing in analysis_result.ingredients
                ],
                "recipes": [
                    {
                        "id": rec.id,
                        "title": rec.title,
                        "description": rec.description,
                        "meal_slot": rec.meal_slot,
                        "priority": rec.priority,
                        "rationale_ko": rec.rationale_ko,
                        "tags": rec.tags
                    }
                    for rec in analysis_result.recipes
                ]
            }
            
            # 캐시에 저장
            cache_manager.set(
                namespace="ai_analysis",
                key=cache_key,
                data=cache_data,
                metadata={
                    "disease_id": disease['id'],
                    "disease_description": disease['description'],
                    "precomputed": True,
                    "generation_time": elapsed
                }
            )
            
            results["cached_diseases"].append({
                "disease_id": disease['id'],
                "description": disease['description'],
                "symptom": disease['symptom'],
                "medications": disease['medications'],
                "analysis_time": f"{elapsed:.2f}초",
                "status": "✅ 캐시됨"
            })
            
            print(f"✅ 완료! ({elapsed:.2f}초)")
            print(f"   - 증상: {disease['symptom']}")
            print(f"   - 추천 식재료: {len(analysis_result.ingredients)}개")
            print(f"   - 추천 레시피: {len(analysis_result.recipes)}개")
            
        except Exception as e:
            print(f"❌ 실패: {str(e)}")
            results["failed_diseases"].append({
                "disease_id": disease['id'],
                "description": disease['description'],
                "error": str(e)
            })
    
    # 결과 저장
    os.makedirs("data/cache", exist_ok=True)
    with open("data/cache/precomputed_metadata.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 보고서 출력
    print("\n" + "="*70)
    print("📊 Pre-computed 캐시 생성 완료!")
    print("="*70)
    print(f"\n✅ 성공: {len(results['cached_diseases'])}/{len(COMMON_DISEASES)}")
    print(f"❌ 실패: {len(results['failed_diseases'])}/{len(COMMON_DISEASES)}")
    print(f"\n📁 캐시 위치: data/cache/")
    print(f"📝 메타데이터: data/cache/precomputed_metadata.json")
    
    # 상세 결과
    if results['cached_diseases']:
        print("\n✅ 캐시된 질환:")
        for disease in results['cached_diseases']:
            print(f"  • {disease['description']} ({disease['analysis_time']})")
    
    if results['failed_diseases']:
        print("\n❌ 캐시 실패한 질환:")
        for disease in results['failed_diseases']:
            print(f"  • {disease['description']}: {disease['error']}")
    
    print("\n" + "="*70 + "\n")
    
    return results


if __name__ == "__main__":
    # 비동기 실행
    results = asyncio.run(generate_precomputed_cache())
