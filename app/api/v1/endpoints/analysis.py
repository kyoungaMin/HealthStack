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
        result = service.step1_extract(req.search_type, req.text, req.image_url)
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
        result = service.step2_search(req.session_id, req.confirmed_keywords)
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
        return PrescriptionAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처방전 분석 오류: {str(e)}")


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
