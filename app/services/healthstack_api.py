"""
Health Stack 통합 API 모듈
모든 서비스를 하나로 연결하여 프론트엔드에 제공
"""
import os
import sys
from typing import Optional
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.analyze_service import AnalyzeService, AnalysisResult
from app.services.pubmed_service import PubMedService, PubMedPaper
from app.services.youtube_service import YouTubeService, YouTubeVideo
from app.services.naver_ocr_service import NaverOCRService
from app.services.medication_service import MedicationService

load_dotenv()


@dataclass
class IngredientRecommendation:
    """식재료 추천 결과"""
    rep_code: str
    modern_name: str
    rationale_ko: str
    direction: str
    evidence_level: str
    pubmed_papers: list[dict] = field(default_factory=list)
    youtube_video: Optional[dict] = None
    tip: str = ""


@dataclass
class HealthStackResponse:
    """Health Stack API 응답"""
    # 상태 요약 (MVP ③)
    symptom_summary: str
    confidence_level: str  # high | medium | general
    source: str  # database | similarity | ai_generated
    
    # 동의보감 음식 추천 (MVP ④)
    ingredients: list[IngredientRecommendation] = field(default_factory=list)
    
    # 주의사항
    cautions: list[str] = field(default_factory=list)

    # 처방약 상세 정보 (RAG)
    medications: list[dict] = field(default_factory=list)
    
    # 메타
    matched_symptom_name: Optional[str] = None
    disclaimer: str = "본 정보는 의학적 진단을 대신할 수 없습니다. 증상이 심각할 경우 전문의와 상담하세요."


class HealthStackAPI:
    """Health Stack 통합 API"""
    
    def __init__(self):
        self.analyze_service = AnalyzeService()
        self.pubmed_service = PubMedService()
        self.youtube_service = YouTubeService()
        self.ocr_service = NaverOCRService()
        self.medication_service = MedicationService()
    
    async def analyze(
        self, 
        symptom_text: Optional[str] = None,
        prescription_image_path: Optional[str] = None
    ) -> HealthStackResponse:
        """
        증상/처방전 분석 통합 API
        
        Args:
            symptom_text: 증상 텍스트 (선택)
            prescription_image_path: 처방전 이미지 경로 (선택)
            
        Returns:
            HealthStackResponse: 통합 분석 결과
        """
        combined_input = symptom_text or ""
        drug_names = []
        
        # 1. OCR 처리 (처방전 이미지가 있는 경우)
        if prescription_image_path:
            try:
                ocr_result = self.ocr_service.extract_prescription_info(prescription_image_path)
                # OCR 텍스트를 분석 입력에 추가
                combined_input += " " + ocr_result.get("full_text", "")
                # 약 이름 추출 (간단 버전)
                drug_names = self._extract_drug_names(ocr_result.get("raw_texts", []))
            except Exception as e:
                print(f"OCR 처리 오류: {e}")
        
        # 2. 증상 분석
        analysis = await self.analyze_service.analyze_symptom(combined_input)
        
        # 3. 각 식재료에 대해 PubMed 논문 + YouTube 영상 조회
        ingredient_recommendations = []
        
        for ing in analysis.ingredients[:3]:  # 최대 3개
            # PubMed 논문 검색
            papers = []
            if analysis.matched_symptom_id:
                papers = self.pubmed_service.search_by_symptom_and_ingredient(
                    analysis.matched_symptom_id,
                    ing.rep_code
                )
            if not papers:
                # Fallback: 직접 검색
                query = f"{ing.modern_name} health benefit"
                papers = self.pubmed_service.search_papers(query, max_results=1)
            
            # YouTube 영상 검색
            video = self.youtube_service.get_video_for_symptom_ingredient(
                analysis.matched_symptom_id or 0,
                ing.rep_code
            )
            if not video:
                videos = self.youtube_service.search_by_ingredient(ing.modern_name)
                video = videos[0] if videos else None
            
            ingredient_recommendations.append(IngredientRecommendation(
                rep_code=ing.rep_code,
                modern_name=ing.modern_name,
                rationale_ko=ing.rationale_ko,
                direction=ing.direction,
                evidence_level=ing.evidence_level,
                pubmed_papers=[
                    {
                        "pmid": p.pmid,
                        "title": p.title,
                        "journal": p.journal,
                        "pub_year": p.pub_year,
                        "url": p.url,
                        "summary": p.abstract[:100] + "..." if p.abstract else ""
                    }
                    for p in papers[:2]
                ],
                youtube_video={
                    "video_id": video.video_id,
                    "title": video.title,
                    "channel": video.channel,
                    "thumbnail_url": video.thumbnail_url,
                    "url": video.url
                } if video else None,
                tip=self._generate_tip(ing.modern_name)
            ))
        
        # 4. 약물 주의사항 조회
        cautions = []
        # 4. 약물 주의사항 조회
        cautions = []
        medication_details = []
        if drug_names:
            cautions = self.analyze_service.get_cautions_for_drugs(drug_names)
            
            # DB 저장
            if prescription_image_path:
                self.medication_service.save_prescription(prescription_image_path, drug_names)
            
            # RAG 검색 (약물 상세 정보)
            for drug in drug_names:
                info = await self.medication_service.get_drug_info(drug)
                medication_details.append(info)
        
        return HealthStackResponse(
            symptom_summary=analysis.symptom_summary,
            confidence_level=analysis.confidence_level,
            source=analysis.source,
            ingredients=ingredient_recommendations,
            cautions=cautions,
            medications=medication_details,
            matched_symptom_name=analysis.matched_symptom_name
        )
    
    def _extract_drug_names(self, texts: list[str]) -> list[str]:
        """OCR 텍스트에서 약 이름 추출 (간단 버전)"""
        drug_names = []
        
        # 흔한 약 키워드 패턴
        drug_patterns = ["정", "캡슐", "mg", "ml", "타블렛"]
        
        for text in texts:
            for pattern in drug_patterns:
                if pattern in text:
                    # 약 이름으로 추정
                    drug_names.append(text.strip())
                    break
        
        return drug_names[:5]  # 최대 5개
    
    def _generate_tip(self, ingredient_name: str) -> str:
        """식재료별 한 줄 팁 생성"""
        tips = {
            "무": "식후 반찬으로 무생채를 조금씩 드세요",
            "생강": "따뜻한 생강차로 하루를 시작해보세요",
            "대추": "간식으로 대추 2-3개를 드시면 좋아요",
            "인삼": "아침 공복에 인삼차 한 잔이 도움됩니다",
            "감초": "달인 물로 차처럼 음용하세요",
            "참깨": "밥 위에 뿌려 드시면 간편해요",
            "마": "죽으로 만들어 아침 식사로 추천해요"
        }
        return tips.get(ingredient_name, f"{ingredient_name}을(를) 식단에 포함해 보세요")


def analyze_sync(
    symptom_text: Optional[str] = None,
    prescription_image_path: Optional[str] = None
) -> dict:
    """동기 버전 분석 API"""
    import asyncio
    
    api = HealthStackAPI()
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(
        api.analyze(symptom_text, prescription_image_path)
    )
    
    return {
        "symptom_summary": result.symptom_summary,
        "confidence_level": result.confidence_level,
        "source": result.source,
        "ingredients": [
            {
                "rep_code": ing.rep_code,
                "modern_name": ing.modern_name,
                "rationale_ko": ing.rationale_ko,
                "direction": ing.direction,
                "evidence_level": ing.evidence_level,
                "pubmed_papers": ing.pubmed_papers,
                "youtube_video": ing.youtube_video,
                "tip": ing.tip
            }
            for ing in result.ingredients
        ],
        "cautions": result.cautions,
        "matched_symptom_name": result.matched_symptom_name,
        "disclaimer": result.disclaimer
    }


if __name__ == "__main__":
    # 테스트
    print("\n" + "="*60)
    print("Health Stack API 테스트")
    print("="*60)
    
    result = analyze_sync("속이 더부룩하고 소화가 안 돼요")
    
    print(f"\n📋 증상 요약: {result['symptom_summary']}")
    print(f"📊 신뢰도: {result['confidence_level']} ({result['source']})")
    
    print(f"\n🥬 추천 식재료: {len(result['ingredients'])}개")
    for ing in result['ingredients']:
        print(f"\n  [{ing['modern_name']}]")
        print(f"  근거: {ing['rationale_ko'][:50]}...")
        print(f"  💡 팁: {ing['tip']}")
        if ing['pubmed_papers']:
            print(f"  📄 논문: {ing['pubmed_papers'][0]['title'][:40]}...")
        if ing['youtube_video']:
            print(f"  ▶️ 영상: {ing['youtube_video']['title'][:40]}...")
    
    if result['cautions']:
        print(f"\n⚠️ 주의사항: {len(result['cautions'])}개")
        for c in result['cautions']:
            print(f"  - {c}")
    
    print(f"\n📌 면책조항: {result['disclaimer']}")
