"""
Health Stack 통합 API 모듈
모든 서비스를 하나로 연결하여 프론트엔드에 제공
"""
import os
import sys
import asyncio
import time
from typing import Optional
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.analyze_service import AnalyzeService, AnalysisResult, Recipe
from app.services.pubmed_service import PubMedService, PubMedPaper
from app.services.youtube_service import YouTubeService, YouTubeVideo
from app.services.naver_ocr_service import NaverOCRService
from app.services.medication_service import MedicationService
from app.utils.drug_validator import DrugValidator

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
    recipes: list[Recipe] = field(default_factory=list)
    
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
        self.drug_validator = DrugValidator()  # ★ 의약품 검증 추가
    
    async def analyze(
        self, 
        symptom_text: Optional[str] = None,
        prescription_image_path: Optional[str] = None,
        medications: list[str] = None,
        user_id: Optional[str] = None
    ) -> HealthStackResponse:
        """
        증상/처방전 분석 통합 API
        
        Args:
            symptom_text: 증상 텍스트 (선택)
            prescription_image_path: 처방전 이미지 경로 (선택)
            medications: 복용 중인 약물 리스트 (선택)
            user_id: 사용자/게스트 ID (선택)
            
        Returns:
            HealthStackResponse: 통합 분석 결과
        """
        combined_input = symptom_text or ""
        drug_names = list(medications) if medications else []
        hospital_name = None
        ocr_full_text = ""
        
        # 1. OCR 처리 (처방전 이미지가 있는 경우)
        if prescription_image_path:
            try:
                ocr_result = self.ocr_service.extract_prescription_info(prescription_image_path)
                ocr_full_text = ocr_result.get("full_text", "")
                
                # ★ 개선: OCR 텍스트를 항상 분석 입력에 포함 (약물 추출 실패 시에도)
                combined_input += " " + ocr_full_text
                
                # ★ OCR 서비스에서 추출한 약물 목록 사용
                ocr_drugs = ocr_result.get("drugs", [])
                print(f"[OCR Drug Extraction] Found: {ocr_drugs}")
                
                # ★ 의약품 정규화 및 검증 (정확도 향상)
                if ocr_drugs:
                    try:
                        validated_drugs = self._validate_and_normalize_drugs(ocr_drugs)
                        print(f"[Drug Validation] Original: {ocr_drugs}")
                        print(f"[Drug Validation] Normalized: {[d['standard_name'] for d in validated_drugs if d['standard_name']]}")
                        
                        # 정규화된 약물 추가
                        for validated in validated_drugs:
                            if validated['standard_name'] and validated['standard_name'] not in drug_names:
                                drug_names.append(validated['standard_name'])
                    except Exception as e:
                        print(f"[Drug Validation Error] {e} - Using original drugs")
                        # 검증 실패 시 원본 약물 사용
                        for d in ocr_drugs:
                            if d not in drug_names:
                                drug_names.append(d)
                
                # 병원명 추출
                hospital_name = ocr_result.get("hospital_name")
                
                # ★ 처방전 저장 (약물 추출 유무 상관없이 저장)
                # 정규화된 약물 목록 사용
                self.medication_service.save_prescription(
                    prescription_image_path, 
                    drug_names if drug_names else [],
                    hospital_name,
                    user_id
                )
                
                # ★ 분석 결과에 포함할 약물 정보 출력
                print(f"✅ OCR Analysis Complete: {len(drug_names)} medications found")
            except Exception as e:
                print(f"❌ OCR Processing Error: {e}")
                import traceback
                traceback.print_exc()
        
        # 2. 증상 분석 (약물 상호작용 포함)
        # ★ 개선: combined_input에는 OCR 원문이 포함되어 있음 (약물 정보 최대한 활용)
        analysis = await self.analyze_service.analyze_symptom(combined_input, drug_names)
        
        # 3. 각 식재료에 대해 PubMed 논문 + YouTube 영상 조회 (병렬 처리)
        start_evidence = time.time()
        ingredient_recommendations = await self._fetch_evidence_parallel(
            analysis.ingredients[:3],
            analysis.matched_symptom_id
        )
        elapsed_evidence = time.time() - start_evidence
        print(f"[Evidence Collection] Completed in {elapsed_evidence:.2f}s (병렬 처리)")
        
        # 4. 약물 상세 정보 조회
        medication_details = []
        # OCR 원문이 아닌 실제 약물명만 RAG 검색
        real_drugs = [d for d in drug_names if not d.startswith("[OCR")]
        if real_drugs:
            for drug in real_drugs[:5]:  # 최대 5개
                try:
                    info = await self.medication_service.get_drug_info(drug)
                    medication_details.append(info)
                except Exception as e:
                    print(f"약물 정보 조회 실패: {drug} - {e}")
        
        return HealthStackResponse(
            symptom_summary=analysis.symptom_summary,
            confidence_level=analysis.confidence_level,
            source=analysis.source,
            ingredients=ingredient_recommendations,
            recipes=analysis.recipes,
            cautions=analysis.cautions,  # AnalyzeService에서 상호작용 체크 결과 반환
            medications=medication_details,
            matched_symptom_name=analysis.matched_symptom_name
        )
    
    def _extract_drug_names(self, texts: list[str]) -> list[str]:
        """OCR 텍스트에서 약 이름 추출 (강화 버전 - 한글 패턴 지원)"""
        import re
        drug_names = []
        
        # 약물이 아닌 텍스트 패턴 (제외할 키워드)
        exclude_patterns = [
            r"병원|의원|센터|클리닉|의료원",  # 병원명
            r"의사|선생|박사|교수",           # 직급
            r"전화|번호|번지|주소|우편",      # 주소/연락처
            r"최근|조제|내방|약국|진료"       # 처방전 관련 용어
        ]
        
        # 한글 약품명 패턴 (정, 캡슐, 밀리그램, 엑스정 등)
        # ★ 개선: 패턴 앞에 ^를 제거하여 줄 중간의 약품명도 인식
        drug_patterns = [
            r"\*?[가-힣]+정\s*[\(\[]",      # 아세로낙정 (, 넥세라정 20mg(
            r"\*?[가-힣]+정\s*$",            # 줄 끝의 정 형태
            r"\*?[가-힣]+캡슐",              # 캡슐
            r"\*?[가-힣]+엑스정",            # 엑스정
            r"\*?[가-힣]+세미정",            # 세미정
            r"\*?[가-힣]+신정",              # 에페신정
            r"[가-힣]+밀리그램\s*\(",        # 20밀리그램(
            r"\d+mg",                       # 20mg
            r"\d+ml",                       # 5ml
        ]
        
        for text in texts:
            text_clean = text.strip()
            # 너무 짧거나 긴 텍스트 무시 (수정: 50 -> 80)
            if len(text_clean) < 2 or len(text_clean) > 80:
                continue
            
            # ★ 제외 패턴 체크 (병원명, 주소 등)
            if any(re.search(pattern, text_clean) for pattern in exclude_patterns):
                continue
            
            matched = False
            for pattern in drug_patterns:
                if re.search(pattern, text_clean):
                    # 약품명 정제 (괄호 앞까지만, 불필요 문자 제거)
                    drug_name = re.split(r'[\(\[\{]', text_clean)[0].strip()
                    drug_name = drug_name.lstrip('*').strip()
                    
                    if drug_name and len(drug_name) >= 2 and drug_name not in drug_names:
                        # 숫자만 있는 경우 제외 (라인 번호 등)
                        if not drug_name.isdigit():
                            drug_names.append(drug_name)
                            matched = True
                            break
            
            # 패턴 미매칭이지만 "정", "캡슐" 등 약품 단위어를 직접 포함하는 경우
            if not matched and any(unit in text_clean for unit in ["정", "캡슐", "엑스", "세미"]):
                # 숫자로 시작하지 않는 한글 텍스트
                if re.match(r"[가-힣]", text_clean):
                    drug_name = re.split(r'[\(\[\{]', text_clean)[0].strip()
                    if drug_name and len(drug_name) >= 2 and drug_name not in drug_names and not drug_name.isdigit():
                        drug_names.append(drug_name)
        
        print(f"[Drug Extraction] Found {len(drug_names)} drugs: {drug_names}")
        return drug_names[:10]  # 최대 10개
    
    def _validate_and_normalize_drugs(self, drugs: list) -> list:
        """
        ★ 의약품 정규화 및 검증 (정확도 향상)
        추출된 약물 목록을 의약품 사전과 비교하여 정규화
        """
        normalized_results = []
        
        for drug_name in drugs:
            is_valid, corrected_name, confidence = self.drug_validator.validate_drug(drug_name)
            
            # 검증 결과 로깅
            if is_valid and corrected_name != drug_name:
                print(f"[Drug Validation] '{drug_name}' → '{corrected_name}' ({confidence:.0%})")
            elif not is_valid:
                print(f"[Drug Warning] '{drug_name}' is not in database (추가 검증 필요)")
            
            normalized_results.append({
                "original": drug_name,
                "standard_name": corrected_name if is_valid else drug_name,
                "status": "valid" if is_valid else "unknown",
                "confidence": confidence
            })
        
        return normalized_results
    
    async def _fetch_evidence_parallel(self, ingredients: list, matched_symptom_id: Optional[int]) -> list:
        """
        ★ 병렬 처리 구현: PubMed + YouTube 동시 검색
        각 식재료에 대해 논문과 영상을 동시에 검색하여 성능 최적화
        """
        async def fetch_ingredient_evidence(ing):
            """단일 식재료에 대한 증거 자료 수집"""
            try:
                # 1. PubMed 논문 검색 (비동기)
                papers = []
                if matched_symptom_id:
                    papers = await self.pubmed_service.search_by_symptom_and_ingredient(
                        matched_symptom_id,
                        ing.rep_code
                    )
                
                if not papers:
                    query = f"{ing.modern_name} health benefit"
                    papers = await self.pubmed_service.search_papers(query, max_results=1)
                
                # 2. YouTube 영상 검색 (동기 → 논문 검색과 동시 실행)
                video = None
                if matched_symptom_id:
                    video = self.youtube_service.get_video_for_symptom_ingredient(
                        matched_symptom_id,
                        ing.rep_code
                    )
                
                if not video:
                    videos = self.youtube_service.search_by_ingredient(ing.modern_name)
                    video = videos[0] if videos else None
                
                # 3. 결과 조합
                return IngredientRecommendation(
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
                )
            except Exception as e:
                # 에러 발생 시에도 기본 정보는 반환
                ing_name = ing.modern_name if hasattr(ing, 'modern_name') else str(ing)
                print(f"[Evidence Fetch Error] {ing_name}: {e}")
                
                # 안전하게 기본값 반환
                try:
                    return IngredientRecommendation(
                        rep_code=ing.rep_code,
                        modern_name=ing.modern_name,
                        rationale_ko=ing.rationale_ko,
                        direction=ing.direction,
                        evidence_level=ing.evidence_level,
                        pubmed_papers=[],
                        youtube_video=None,
                        tip=self._generate_tip(ing.modern_name)
                    )
                except Exception as fallback_e:
                    print(f"[Fallback Error] {fallback_e}")
                    return None
        
        # ★ 병렬 실행: 모든 식재료의 증거 자료를 동시에 수집
        print(f"[Parallel Fetch] Starting evidence collection for {len(ingredients)} ingredients...")
        results = await asyncio.gather(*[fetch_ingredient_evidence(ing) for ing in ingredients])
        return [r for r in results if r is not None]  # None 값 필터링
    
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
    prescription_image_path: Optional[str] = None,
    medications: list[str] = None,
    user_id: Optional[str] = None
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
        api.analyze(symptom_text, prescription_image_path, medications)
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
