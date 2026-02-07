"""
통합 분석 서비스 모듈
증상 분석 → 동의보감 식재료 추천 → PubMed 근거 연결
3단계 Fallback 전략 적용
"""
import os
import sys
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.supabase_client import get_supabase_client

load_dotenv()


@dataclass
class Ingredient:
    """추천 식재료 정보"""
    rep_code: str
    modern_name: str
    rationale_ko: str
    direction: str  # recommend | good | neutral | caution | avoid
    priority: int
    evidence_level: str  # traditional | clinical | empirical


@dataclass
class AnalysisResult:
    """분석 결과"""
    symptom_summary: str
    ingredients: list[Ingredient] = field(default_factory=list)
    confidence_level: str = "general"  # high | medium | general
    source: str = "ai_generated"  # database | similarity | ai_generated
    matched_symptom_id: Optional[int] = None
    matched_symptom_name: Optional[str] = None
    cautions: list[str] = field(default_factory=list)


class AnalyzeService:
    """통합 분석 서비스"""
    
    def __init__(self):
        self.db = get_supabase_client()
    
    async def analyze_symptom(self, symptom_text: str) -> AnalysisResult:
        """
        증상 텍스트를 분석하고 식재료를 추천합니다.
        3단계 Fallback 전략 적용
        
        Args:
            symptom_text: 사용자 입력 증상 텍스트
            
        Returns:
            AnalysisResult: 분석 결과
        """
        # 1차: disease_master 정확 매칭
        matched = self._search_exact_symptom(symptom_text)
        
        if matched:
            ingredients = self._get_ingredients_from_db(matched["id"])
            return AnalysisResult(
                symptom_summary=f"{matched.get('modern_name_ko', matched.get('disease_read', ''))} 관련 증상입니다.",
                ingredients=ingredients,
                confidence_level="high",
                source="database",
                matched_symptom_id=matched["id"],
                matched_symptom_name=matched.get("modern_name_ko")
            )
        
        # 2차: 유사 증상 검색 (aliases, 부분 매칭)
        similar = self._search_similar_symptom(symptom_text)
        
        if similar:
            ingredients = self._get_ingredients_from_db(similar["id"])
            return AnalysisResult(
                symptom_summary=f"'{similar.get('modern_name_ko', '')}' 증상과 유사합니다.",
                ingredients=ingredients,
                confidence_level="medium",
                source="similarity",
                matched_symptom_id=similar["id"],
                matched_symptom_name=similar.get("modern_name_ko")
            )
        
        # 3차: AI Fallback (빈 결과 반환 - 프론트엔드에서 Google AI 호출)
        return AnalysisResult(
            symptom_summary="입력하신 증상에 대해 AI가 분석합니다.",
            ingredients=[],
            confidence_level="general",
            source="ai_generated"
        )
    
    def _search_exact_symptom(self, symptom_text: str) -> Optional[dict]:
        """disease_master에서 정확 매칭 검색 (식재료 매핑이 있는 증상 우선)"""
        try:
            # modern_name_ko 또는 disease_read로 검색
            result = self.db.table("disease_master").select("*").or_(
                f"modern_name_ko.ilike.%{symptom_text}%,"
                f"disease_read.ilike.%{symptom_text}%,"
                f"name_en.ilike.%{symptom_text}%"
            ).limit(10).execute()
            
            if not result.data:
                return None
            
            # 여러 결과가 있으면 symptom_ingredient_map에 매핑이 있는 것 우선
            for row in result.data:
                map_check = self.db.table("symptom_ingredient_map").select(
                    "id"
                ).eq("symptom_id", row["id"]).limit(1).execute()
                
                if map_check.data:
                    return row
            
            # 매핑이 없으면 첫 번째 결과 반환
            return result.data[0]
        except Exception as e:
            print(f"정확 매칭 검색 오류: {e}")
            return None
    
    def _search_similar_symptom(self, symptom_text: str) -> Optional[dict]:
        """aliases 배열 또는 부분 매칭으로 유사 증상 검색 (식재료 매핑 있는 것 우선)"""
        try:
            keywords = self._extract_keywords(symptom_text)
            
            for keyword in keywords:
                # disease_read 필드도 검색에 추가
                result = self.db.table("disease_master").select("*").or_(
                    f"modern_name_ko.ilike.%{keyword}%,"
                    f"disease_read.ilike.%{keyword}%,"
                    f"disease_alias_read.ilike.%{keyword}%,"
                    f"category.ilike.%{keyword}%"
                ).limit(10).execute()
                
                if not result.data:
                    continue
                
                # 여러 결과가 있으면 symptom_ingredient_map에 매핑이 있는 것 우선
                for row in result.data:
                    map_check = self.db.table("symptom_ingredient_map").select(
                        "id"
                    ).eq("symptom_id", row["id"]).limit(1).execute()
                    
                    if map_check.data:
                        return row
                
                # 매핑이 없으면 첫 번째 결과 반환
                return result.data[0]
            
            return None
        except Exception as e:
            print(f"유사 검색 오류: {e}")
            return None
    
    def _extract_keywords(self, text: str) -> list[str]:
        """텍스트에서 핵심 키워드 추출"""
        # 간단한 키워드 추출 (나중에 NLP로 개선 가능)
        keywords = []
        
        # 흔한 증상 키워드 매핑 (사용자 입력 → DB 검색 키워드)
        symptom_keywords = {
            "불면": ["수면", "잠", "불면", "못 자", "안 자", "깨"],
            "소화": ["소화", "위장", "더부룩", "체한", "소화불량"],
            "피로": ["피로", "지침", "기력", "힘이 없"],
            "두통": ["두통", "머리", "편두통"],
            "냉증": ["냉증", "손발", "차가", "냉한"],
            "혈압": ["혈압", "고혈압", "저혈압"],
            "당뇨": ["당뇨", "혈당"],
            "호흡": ["호흡", "기침", "가래", "숨"],
            "변비": ["변비", "배변", "대변"],
        }
        
        for db_keyword, input_patterns in symptom_keywords.items():
            for pattern in input_patterns:
                if pattern in text:
                    keywords.append(db_keyword)  # DB 검색용 키워드 추가
                    break
        
        # 원본 텍스트 단어도 추가
        words = text.replace("이", "").replace("가", "").replace("요", "").split()
        keywords.extend([w for w in words if len(w) >= 2])
        
        return list(set(keywords))
    
    def _get_ingredients_from_db(self, symptom_id: int) -> list[Ingredient]:
        """symptom_ingredient_map에서 추천 식재료 조회"""
        try:
            # 1. symptom_ingredient_map에서 식재료 매핑 조회
            result = self.db.table("symptom_ingredient_map").select(
                "rep_code, direction, rationale_ko, priority, evidence_level"
            ).eq("symptom_id", symptom_id).order(
                "priority", desc=False
            ).limit(3).execute()
            
            if not result.data:
                return []
            
            # 2. rep_code들로 foods_master에서 이름 조회
            rep_codes = [row["rep_code"] for row in result.data]
            foods_result = self.db.table("foods_master").select(
                "rep_code, modern_name"
            ).in_("rep_code", rep_codes).execute()
            
            # rep_code -> modern_name 매핑
            food_names = {f["rep_code"]: f["modern_name"] for f in foods_result.data}
            
            ingredients = []
            for row in result.data:
                rep_code = row.get("rep_code", "")
                ingredients.append(Ingredient(
                    rep_code=rep_code,
                    modern_name=food_names.get(rep_code, rep_code),
                    rationale_ko=row.get("rationale_ko", ""),
                    direction=row.get("direction", "recommend"),
                    priority=row.get("priority", 100),
                    evidence_level=row.get("evidence_level", "traditional")
                ))
            
            return ingredients
        except Exception as e:
            print(f"식재료 조회 오류: {e}")
            return []
    
    def get_cautions_for_drugs(self, drug_names: list[str]) -> list[str]:
        """약 이름으로 주의사항 조회"""
        cautions = []
        try:
            for drug_name in drug_names:
                result = self.db.table("interaction_facts").select(
                    "summary_ko, action_ko, severity"
                ).or_(
                    f"a_ref.ilike.%{drug_name}%,"
                    f"b_ref.ilike.%{drug_name}%"
                ).limit(3).execute()
                
                for row in result.data:
                    if row.get("summary_ko"):
                        cautions.append(row["summary_ko"])
        except Exception as e:
            print(f"주의사항 조회 오류: {e}")
        
        return cautions


# 동기 래퍼 함수 (테스트용)
def analyze_symptom_sync(symptom_text: str) -> dict:
    """동기 버전 분석 함수"""
    import asyncio
    service = AnalyzeService()
    
    # 이벤트 루프가 없으면 새로 생성
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(service.analyze_symptom(symptom_text))
    
    return {
        "symptom_summary": result.symptom_summary,
        "ingredients": [
            {
                "rep_code": ing.rep_code,
                "modern_name": ing.modern_name,
                "rationale_ko": ing.rationale_ko,
                "direction": ing.direction,
                "priority": ing.priority,
                "evidence_level": ing.evidence_level
            }
            for ing in result.ingredients
        ],
        "confidence_level": result.confidence_level,
        "source": result.source,
        "matched_symptom_id": result.matched_symptom_id,
        "matched_symptom_name": result.matched_symptom_name
    }


if __name__ == "__main__":
    # 테스트
    test_symptoms = [
        "속이 더부룩해요",
        "잠을 잘 못 자요",
        "손발이 차요"
    ]
    
    for symptom in test_symptoms:
        print(f"\n{'='*50}")
        print(f"증상: {symptom}")
        print("="*50)
        result = analyze_symptom_sync(symptom)
        print(f"요약: {result['symptom_summary']}")
        print(f"신뢰도: {result['confidence_level']} ({result['source']})")
        print(f"추천 식재료: {len(result['ingredients'])}개")
        for ing in result['ingredients']:
            print(f"  - {ing['modern_name']}: {ing['rationale_ko'][:30]}...")
