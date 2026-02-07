"""
Health Stack FastAPI 백엔드 서버
프론트엔드와 Python 서비스를 연결하는 API 엔드포인트
"""
import os
import sys
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.healthstack_api import HealthStackAPI
from app.services.analyze_service import analyze_symptom_sync
from app.services.pubmed_service import search_pubmed_papers
from app.services.youtube_service import search_youtube_videos
from app.services.naver_ocr_service import NaverOCRService
from app.services.faq_service import FAQService

app = FastAPI(
    title="Health Stack API",
    description="증상/처방전 기반 동의보감 식재료 추천 서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response 모델
class AnalyzeRequest(BaseModel):
    symptom: str
    prescription_text: Optional[str] = None


class IngredientResponse(BaseModel):
    rep_code: str
    modern_name: str
    rationale_ko: str
    direction: str
    evidence_level: str
    pubmed_papers: list = []
    youtube_video: Optional[dict] = None
    tip: str = ""


class AnalyzeResponse(BaseModel):
    symptom_summary: str
    confidence_level: str
    source: str
    ingredients: list[IngredientResponse]
    medications: list[dict] = []
    cautions: list[str] = []
    matched_symptom_name: Optional[str] = None
    disclaimer: str = "본 정보는 의학적 진단을 대신할 수 없습니다."


class PubMedRequest(BaseModel):
    query: str
    max_results: int = 2


class YouTubeRequest(BaseModel):
    ingredient: str


# API 엔드포인트
@app.get("/")
async def root():
    return {"message": "Health Stack API v1.0", "status": "running"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_symptom(request: AnalyzeRequest):
    """
    증상 분석 API
    - 증상 텍스트를 분석하여 동의보감 식재료 추천
    - DB 매칭 → 유사 검색 → AI Fallback 순으로 처리
    """
    try:
        api = HealthStackAPI()
        result = await api.analyze(
            symptom_text=request.symptom,
            prescription_image_path=None
        )
        
        return AnalyzeResponse(
            symptom_summary=result.symptom_summary,
            confidence_level=result.confidence_level,
            source=result.source,
            ingredients=[
                IngredientResponse(
                    rep_code=ing.rep_code,
                    modern_name=ing.modern_name,
                    rationale_ko=ing.rationale_ko,
                    direction=ing.direction,
                    evidence_level=ing.evidence_level,
                    pubmed_papers=ing.pubmed_papers,
                    youtube_video=ing.youtube_video,
                    tip=ing.tip
                )
                for ing in result.ingredients
            ],
            medications=result.medications,
            cautions=result.cautions,
            matched_symptom_name=result.matched_symptom_name,
            disclaimer=result.disclaimer
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ocr")
async def process_ocr(file: UploadFile = File(...)):
    """
    처방전 OCR API
    - 이미지에서 텍스트 추출
    """
    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # OCR 처리
        ocr_service = NaverOCRService()
        result = ocr_service.extract_prescription_info(tmp_path)
        
        # 임시 파일 삭제
        os.unlink(tmp_path)
        
        return {
            "success": True,
            "full_text": result.get("full_text", ""),
            "raw_texts": result.get("raw_texts", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-with-image")
async def analyze_with_image(
    symptom: str = Form(""),
    file: Optional[UploadFile] = File(None)
):
    """
    증상 + 처방전 이미지 통합 분석 API
    """
    try:
        prescription_path = None
        
        # 이미지가 있으면 임시 저장
        if file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                content = await file.read()
                tmp.write(content)
                prescription_path = tmp.name
        
        # 분석 실행
        api = HealthStackAPI()
        result = await api.analyze(
            symptom_text=symptom,
            prescription_image_path=prescription_path
        )
        
        # 임시 파일 삭제
        if prescription_path:
            os.unlink(prescription_path)
        
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
            "medications": result.medications,
            "cautions": result.cautions,
            "matched_symptom_name": result.matched_symptom_name,
            "disclaimer": result.disclaimer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pubmed")
async def search_pubmed(request: PubMedRequest):
    """
    PubMed 논문 검색 API
    """
    try:
        papers = search_pubmed_papers(request.query, request.max_results)
        return {"papers": papers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/youtube")
async def search_youtube(request: YouTubeRequest):
    """
    YouTube 영상 검색 API
    """
    try:
        videos = search_youtube_videos(request.ingredient)
        return {"videos": videos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/golden-questions")
async def get_golden_questions():
    """자주하는 질문 (Golden Questions) 리스트 반환"""
    service = FAQService()
    return {"questions": service.get_golden_questions()}


@app.get("/api/health")
async def health_check():
    """서버 상태 확인"""
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
