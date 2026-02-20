from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List
from app.schemas.analysis import (
    Step1ExtractRequest, Step1ExtractResponse,
    Step2SearchRequest, Step2SearchResponse,
    Step3ReportRequest, Step3ReportResponse,
    PrescriptionAnalysisResponse,
    PillSearchByNameRequest, PillSearchByAppearanceRequest, PillSearchResponse
)
from app.services.analysis_step_service import StepByStepAnalysisService
from app.services.prescription_service import PrescriptionService
from app.services.pill_id_service import PillIdService
from app.services.faq_service import FAQService

router = APIRouter()

# Dependency Injection for Services
def get_analysis_service():
    return StepByStepAnalysisService()

def get_prescription_service():
    return PrescriptionService()

def get_pill_id_service():
    return PillIdService()

@router.post("/step1-extract", response_model=Step1ExtractResponse)
async def analyze_step1_extract(
    req: Step1ExtractRequest,
    service: StepByStepAnalysisService = Depends(get_analysis_service)
):
    """
    [Step 1] 증상/처방전 초기 인식 및 키워드 추출
    """
    try:
        import asyncio
        result = await asyncio.to_thread(service.step1_extract, req.search_type, req.text, req.image_url)
        return Step1ExtractResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.post("/step2-search", response_model=Step2SearchResponse)
async def analyze_step2_search(
    req: Step2SearchRequest,
    service: StepByStepAnalysisService = Depends(get_analysis_service)
):
    """
    [Step 2] 확정된 키워드로 DB/Vector 검색 수행
    """
    try:
        # Pydantic schema expects dict structure matching response model
        # The service returns {"candidates": {...}}
        import asyncio
        result = await asyncio.to_thread(service.step2_search, req.session_id, req.confirmed_keywords)
        return Step2SearchResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search Error: {str(e)}")


@router.post("/step3-report", response_model=Step3ReportResponse)
async def analyze_step3_report(
    req: Step3ReportRequest,
    service: StepByStepAnalysisService = Depends(get_analysis_service)
):
    """
    [Step 3] 최종 리포트 생성 (LLM 활용)
    """
    try:
        # Convert Pydantic models to dict for service
        candidates = [c.dict() for c in req.selected_candidates]
        result = await service.step3_report(req.session_id, candidates)

        return Step3ReportResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report Generation Error: {str(e)}")


@router.post("/prescription", response_model=PrescriptionAnalysisResponse)
async def analyze_prescription(
    file: UploadFile = File(..., description="처방전 이미지 파일 (jpg/png)"),
    service: PrescriptionService = Depends(get_prescription_service)
):
    """
    [처방전 통합 분석]
    이미지 업로드 → OCR(Gemini) → PubMed 근거 → 동의보감 매핑 → 5섹션 리포트 반환
    """
    # 이미지 타입 검증
    allowed_types = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
    content_type = file.content_type or "image/jpeg"
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다: {content_type}")

    try:
        image_bytes = await file.read()
        result = await service.analyze_prescription_image(image_bytes, content_type)

        # Debug: log result structure
        import json
        with open("result_debug.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"[DEBUG] Result saved to result_debug.json", flush=True)

        return PrescriptionAnalysisResponse(**result)
    except Exception as e:
        import traceback
        import sys

        # Write detailed traceback to file for debugging
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write(f"=== Prescription Analysis Error ===\n")
            f.write(f"Error: {e}\n")
            f.write(f"Error type: {type(e)}\n\n")
            f.write("Full traceback:\n")
            traceback.print_exc(file=f)

        # Also print to console
        traceback.print_exc()
        print(f"[ERROR] Full error: {e}", file=sys.stderr, flush=True)
        print(f"[ERROR] Error type: {type(e)}", file=sys.stderr, flush=True)
        raise HTTPException(status_code=500, detail=f"처방전 분석 오류: {str(e)}")


@router.post("/diet-recommendation")
async def get_diet_recommendation(
    request: dict
):
    """
    AI 맞춤 레시피 추천
    """
    try:
        import os
        from openai import AsyncOpenAI

        food_names = request.get("foodNames", "")
        drug_names = request.get("drugNames", "")

        # OpenAI API 사용 (Gemini 할당량 초과 시 대체)
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

        client = AsyncOpenAI(api_key=openai_key)

        prompt = f"""추천된 식재료({food_names})를 활용하여 지금 드시는 약({drug_names})과 충돌하지 않는 '오늘의 한 끼 건강 레시피'를 하나만 추천해줘.

재료와 간단한 조리법, 그리고 왜 이 음식이 당신의 몸 상태에 좋은지 이유를 포함해줘.
말투는 아주 다정하게."""

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 한방 영양학 전문가입니다. 친절하고 다정한 말투로 건강 레시피를 추천해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        recommendation = response.choices[0].message.content

        return {"recommendation": recommendation}

    except Exception as e:
        print(f"[Diet Recommendation Error] {e}")
        raise HTTPException(status_code=500, detail=f"레시피 추천 오류: {str(e)}")


@router.post("/pill-search/name", response_model=PillSearchResponse)
async def pill_search_by_name(
    req: PillSearchByNameRequest,
    service: PillIdService = Depends(get_pill_id_service),
):
    """
    [낱알 검색 — 약품명]
    약품명으로 의약품 낱알 외형 정보(모양·색깔·각인·이미지)를 조회합니다.
    식약처 MdcinGrnIdntfcInfoService03 기반 (Level A)
    """
    try:
        pills = await service.search_by_name(req.drug_name)
        return PillSearchResponse(
            total=len(pills),
            items=[PillIdService.to_dict(p) for p in pills],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"낱알 검색 오류: {str(e)}")


@router.post("/pill-search/appearance", response_model=PillSearchResponse)
async def pill_search_by_appearance(
    req: PillSearchByAppearanceRequest,
    service: PillIdService = Depends(get_pill_id_service),
):
    """
    [낱알 검색 — 외형]
    모양·색깔·각인 등 외형 정보로 의약품 낱알을 검색합니다.
    알 수 없는 약을 모양으로 식별할 때 사용합니다.
    """
    if not any([req.drug_shape, req.color_class1, req.color_class2,
                req.mark_front, req.mark_back, req.leng_long, req.leng_short]):
        raise HTTPException(status_code=400, detail="검색 조건을 하나 이상 입력해주세요.")
    try:
        pills = await service.search_by_appearance(
            drug_shape=req.drug_shape or "",
            color_class1=req.color_class1 or "",
            color_class2=req.color_class2 or "",
            mark_front=req.mark_front or "",
            mark_back=req.mark_back or "",
            leng_long=req.leng_long or "",
            leng_short=req.leng_short or "",
        )
        return PillSearchResponse(
            total=len(pills),
            items=[PillIdService.to_dict(p) for p in pills],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"낱알 외형 검색 오류: {str(e)}")


@router.get("/faq")
def get_faq_questions(category: str = None):
    """
    [골든 FAQ] 증상 카테고리별 추천 질문 목록 반환
    ?category=소화/장 | 수면/스트레스 | 면역/호흡기 | 대사/만성 (없으면 전체)
    """
    svc = FAQService()
    questions = svc.get_golden_questions()
    if category:
        questions = [q for q in questions if q.get("category") == category]
    return {"total": len(questions), "questions": questions}
