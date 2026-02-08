import asyncio
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.analyze_service import AnalyzeService

GOLDEN_QUESTIONS = [
    # A. 소화/장
    {"id": "A1", "query": "식후 더부룩하고 트림이 잦아. 바로 먹으면 좋은 음식 3개와 피해야 할 음식 3개?"},
    {"id": "A2", "query": "속쓰림/역류가 있는데 매운 음식 말고 대체 레시피 추천해줘."},
    {"id": "A3", "query": "변비가 심한데 커피 마시면 더 심해져. 도움이 되는 식재료는?"},
    {"id": "A4", "query": "설사가 잦아. 유제품 먹으면 더 나빠지는 느낌. 어떤 식단이 안전해?"},
    {"id": "A5", "query": "복부 팽만과 가스가 많아. 생양파/콩류는 피해야 하나?"},
    {"id": "A6", "query": "과민성대장(IBS) 느낌인데 자극 없는 한끼 메뉴 추천."},
    {"id": "A7", "query": "아침 공복에 속이 쓰려. 공복에 안전한 음식/차는?"},
    {"id": "A8", "query": "야식 후 역류가 심해져. 밤에 먹어도 비교적 괜찮은 메뉴는?"},
    {"id": "A9", "query": "장트러블이 있는데 프로바이오틱스랑 같이 먹기 좋은 식재료?"},
    {"id": "A10", "query": "소화가 약한 편인데 생채소가 부담. 조리법까지 추천."},
    
    # B. 수면/스트레스
    {"id": "B1", "query": "잠이 얕고 새벽에 자주 깨. 저녁 식단/피해야 할 것?"},
    {"id": "B2", "query": "스트레스 받으면 폭식해. 식욕 안정에 도움 되는 음식?"},
    {"id": "B3", "query": "카페인을 줄이고 싶은데 오후 피로가 너무 심해. 대안은?"},
    {"id": "B4", "query": "긴장성 두통이 잦아. 혈관성 두통과 다르게 음식으로 조절 가능?"},
    {"id": "B5", "query": "불안이 올라오면 속이 불편해져. 위에 부담 없는 안정 메뉴?"},
    {"id": "B6", "query": "피로가 누적됐는데 철분/비타민B 말고 음식으로 채우는 법?"},
    {"id": "B7", "query": "야근 후 숙면을 돕는 따뜻한 한끼 추천."},
    {"id": "B8", "query": "머리가 멍하고 집중이 안 돼. 오전/오후 간식 추천."},
    
    # C. 면역/호흡기
    {"id": "C1", "query": "감기 기운(목 따가움)이 있어. 자극 없는 음식/차 추천."},
    {"id": "C2", "query": "기침·가래가 오래가. 유제품이 영향을 주는지?"},
    {"id": "C3", "query": "비염이 심한 날, 피해야 할 음식과 도움 되는 음식?"},
    {"id": "C4", "query": "알레르기 체질인데 벌꿀/견과류 조심해야 해?"},
    {"id": "C5", "query": "여드름이 자주 올라와. 당/유제품/기름 중 뭐를 먼저 줄일까?"},
    {"id": "C6", "query": "피부 염증이 있는데 오메가3 말고 식재료 추천."},
    
    # D. 만성질환
    {"id": "D1", "query": "혈압이 경계선. 짠맛 줄이기 말고 '칼륨' 중심 식단 예시."},
    {"id": "D2", "query": "혈당이 식후에 튀어. 같은 밥이라도 덜 튀게 먹는 조합은?"},
    {"id": "D3", "query": "중성지방이 높아. 탄수/알코올 말고 바꿀 포인트?"},
    {"id": "D4", "query": "고지혈 있는데 계란/새우는 얼마나 조심해야 해?"},
    {"id": "D5", "query": "다이어트 중인데 밤에 단 게 당겨. 대체 간식 추천."},
    {"id": "D6", "query": "혈압약/당뇨약 복용 중일 때 피해야 할 건강식재료(예: 자몽 등)도 같이 알려줘.", "medications": ["Amlodipine", "Metformin"]},
]

async def run_test():
    service = AnalyzeService()
    results = []

    print(f"Running Golden Questions Analysis Test ({len(GOLDEN_QUESTIONS)} Questions)...")
    print("="*80)

    for q in GOLDEN_QUESTIONS:
        print(f"\n[Question {q['id']}] {q['query']}")
        
        # Determine meds
        meds = q.get("medications", None)
        
        try:
            # Call the analysis service
            result = await service.analyze_symptom(q['query'], current_meds=meds)
            
            # Display simplified result
            print(f"  -> Source: {result.source} (Confidence: {result.confidence_level})")
            print(f"  -> Summary: {result.symptom_summary[:60]}...")
            
            if result.matched_symptom_name:
                print(f"  -> Matched: {result.matched_symptom_name}")
                
            print(f"  -> Ingredients: {len(result.ingredients)}")
            for i, ing in enumerate(result.ingredients[:2]): 
                print(f"     * {ing.modern_name} ({ing.direction}): {ing.rationale_ko[:40]}...")
                
            print(f"  -> Recipes: {len(result.recipes)}")
            for i, rec in enumerate(result.recipes[:1]):
                print(f"     @ {rec.title}: {rec.rationale_ko[:40]}...")
                
            if result.cautions:
                print(f"  -> Cautions ({len(result.cautions)}):")
                for c in result.cautions:
                    print(f"     ⚠️ {c}")
                
            # Basic Evaluation check
            passed = False
            
            # 1. Check if we got any meaningful result
            if len(result.ingredients) > 0 or len(result.recipes) > 0:
                passed = True
                
            # 2. Special check for D6 (Interaction)
            if q['id'] == 'D6':
                if not result.cautions:
                    passed = False
                    print("  -> FAIL Reason: Expected cautions for D6 but got none.")
            
            # 3. Source types
            if result.source == "error":
                passed = False
                
            print(f"  -> Result: {'✅ PASS' if passed else '❌ FAIL'}")
            
            # Store result details
            results.append({
                "id": q["id"],
                "query": q["query"],
                "passed": passed,
                "source": result.source,
                "symptom_summary": result.symptom_summary,
                "ingredient_count": len(result.ingredients),
                "recipe_count": len(result.recipes),
                "cautions_count": len(result.cautions)
            })
            
        except Exception as e:
            print(f"  -> ERROR: {str(e)}")
            results.append({
                "id": q["id"],
                "query": q["query"],
                "passed": False,
                "error": str(e)
            })

    print("\n" + "="*80)
    print("Test Summary")
    pass_count = sum(1 for r in results if r["passed"])
    print(f"Passed: {pass_count}/{len(results)}")
    
    # Generate Markdown Report
    report_path = "docs/test/analysis_golden_questions_v2.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Golden Questions V2 분석 결과 보고서\n\n")
        f.write(f"**검증 일시**: 2026-02-08 (Updated)\n")
        f.write(f"**총 질문 수**: {len(GOLDEN_QUESTIONS)}\n")
        f.write(f"**통과**: {pass_count} / **실패**: {len(results) - pass_count}\n\n")
        
        f.write("## 상세 결과\n\n")
        f.write("| ID | Source | 결과 | 비고 |\n")
        f.write("|---|---|---|---|\n")
        
        for r in results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            note = f"Ing: {r.get('ingredient_count',0)}, Rec: {r.get('recipe_count',0)}"
            if r.get('cautions_count', 0) > 0:
                note += f", Caution: {r['cautions_count']}"
            if "error" in r:
                note = f"Error: {r['error']}"
                
            f.write(f"| {r['id']} | {r.get('source', '-')} | {status} | {note} |\n")
            
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    asyncio.run(run_test())
