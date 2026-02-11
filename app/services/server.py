"""
Health Stack FastAPI 백엔드 서버
프론트엔드와 Python 서비스를 연결하는 API 엔드포인트
"""
import os
import sys
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import tempfile
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.healthstack_api import HealthStackAPI
from app.services.analyze_service import analyze_symptom_sync
from app.services.pubmed_service import search_pubmed_papers
from app.services.youtube_service import search_youtube_videos
from app.services.naver_ocr_service import NaverOCRService
from app.services.faq_service import FAQService
from app.utils.drug_info_loader import get_drugs_info_list
from app.utils.cache_manager import CacheManager

app = FastAPI(
    title="Health Stack API",
    description="증상/처방전 기반 동의보감 식재료 추천 서비스",
    version="1.0.0"
)

# ★ Pre-computed 캐시 로딩 함수
def load_precomputed_cache():
    """서버 시작 시 pre-computed 캐시 데이터 로드"""
    cache_metadata_path = Path("data/cache/precomputed_metadata.json")
    
    if cache_metadata_path.exists():
        try:
            with open(cache_metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            cached_count = len(metadata.get("cached_diseases", []))
            if cached_count > 0:
                print("\n" + "="*70)
                print(f"✅ Pre-computed 캐시 로드 완료!")
                print(f"   캐시된 질환: {cached_count}개")
                for disease in metadata.get("cached_diseases", [])[:3]:
                    print(f"   • {disease['description']}")
                if cached_count > 3:
                    print(f"   ... 외 {cached_count - 3}개")
                print("="*70 + "\n")
        except Exception as e:
            print(f"⚠️ Pre-computed 캐시 로드 실패: {e}")
    else:
        print("\n⚠️ Pre-computed 캐시 파일이 없습니다.")
        print("   스크립트 실행: python scripts/generate_precomputed_cache.py\n")


# 앱 시작 시 캐시 로드
@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    load_precomputed_cache()

# Static Files Mount (이미지 서빙)
if not os.path.exists("data/uploads"):
    os.makedirs("data/uploads")
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")

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
    medications: list[str] = []
    user_id: Optional[str] = None


class IngredientResponse(BaseModel):
    rep_code: str
    modern_name: str
    rationale_ko: str
    direction: str
    evidence_level: str
    pubmed_papers: list = []
    youtube_video: Optional[dict] = None
    tip: str = ""


class RecipeResponse(BaseModel):
    id: int
    title: str
    description: str
    meal_slot: str
    priority: int
    rationale_ko: str
    tags: list[str]


class AnalyzeResponse(BaseModel):
    symptom_summary: str
    confidence_level: str
    source: str
    ingredients: list[IngredientResponse]
    recipes: list[RecipeResponse] = []
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
            prescription_image_path=None,
            medications=request.medications,
            user_id=request.user_id
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
            recipes=[
                RecipeResponse(
                    id=rec.id,
                    title=rec.title,
                    description=rec.description,
                    meal_slot=rec.meal_slot,
                    priority=rec.priority,
                    rationale_ko=rec.rationale_ko,
                    tags=rec.tags
                )
                for rec in result.recipes
            ],
            medications=result.medications,
            cautions=result.cautions,
            matched_symptom_name=result.matched_symptom_name,
            disclaimer=result.disclaimer
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Server Error details: {e}")
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
    user_id: str = Form(None),
    file: Optional[UploadFile] = File(None),
    medications_json: str = Form("")  # ★ JSON 문자열로 약물 받기
):
    """
    증상 + 처방전 이미지 통합 분석 API
    """
    try:
        prescription_path = None
        extracted_medications = []
        hospital_name = None
        ocr_full_text = ""
        
        # ★ JSON 문자열을 파싱하여 약물 추출
        user_medications = []
        if medications_json:
            try:
                import json
                user_medications = json.loads(medications_json)
                if not isinstance(user_medications, list):
                    user_medications = []
            except json.JSONDecodeError:
                user_medications = []
        print(f"[User Medications] Received: {user_medications}")
        
        # 이미지가 있으면 임시 저장 후 OCR 처리
        if file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                content = await file.read()
                tmp.write(content)
                prescription_path = tmp.name
            
            # ★ OCR 처리: 처방전에서 약물 추출
            ocr_service = NaverOCRService()
            try:
                ocr_result = ocr_service.extract_prescription_info(prescription_path)
                print(f"[OCR Result] Hospital: {ocr_result.get('hospital_name')}, Drugs: {ocr_result.get('drugs', [])}")
                
                # 추출된 약물과 병원명 저장
                extracted_medications = ocr_result.get("drugs", [])
                hospital_name = ocr_result.get("hospital_name")
                ocr_full_text = ocr_result.get("full_text", "")
                
                # MedicationService에 저장
                from app.services.medication_service import MedicationService
                med_service = MedicationService()
                med_service.save_prescription(
                    image_path=prescription_path,
                    drugs=extracted_medications,
                    hospital_name=hospital_name,
                    user_id=user_id
                )
                print(f"✅ Prescription saved: {len(extracted_medications)} drugs extracted")
            except Exception as ocr_error:
                print(f"⚠️ OCR Processing Error (continuing): {ocr_error}")
                # OCR 실패 - 약물 없이 계속 진행
                extracted_medications = []
                ocr_full_text = ""
        
        # ★ 프론트엔드 약물 + OCR 약물 통합
        all_medications = list(set(extracted_medications + user_medications))
        print(f"[Final Medications] OCR: {extracted_medications}, User: {user_medications}, Combined: {all_medications}")
        
        # 분석 실행: 추출된 약물 + 증상 텍스트 전달
        # ★ 중요: OCR 텍스트를 함께 전달하여 약물 정보가 분석에 포함되도록 함
        combined_symptom = symptom
        if ocr_full_text:
            combined_symptom = f"{symptom}\n\n[처방전 정보]\n{ocr_full_text}".strip()
        
        api = HealthStackAPI()
        result = await api.analyze(
            symptom_text=combined_symptom,
            prescription_image_path=None,  # ★ OCR 텍스트를 이미 처리했으므로 None 전달
            medications=all_medications,  # ★ 수정: 통합된 약물 목록 전달
            user_id=user_id
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
            "recipes": [
                {
                    "id": rec.get("id") if isinstance(rec, dict) else rec.id,
                    "title": rec.get("title") if isinstance(rec, dict) else rec.title,
                    "description": rec.get("description") if isinstance(rec, dict) else rec.description,
                    "meal_slot": rec.get("meal_slot") if isinstance(rec, dict) else rec.meal_slot,
                    "priority": rec.get("priority") if isinstance(rec, dict) else rec.priority,
                    "rationale_ko": rec.get("rationale_ko") if isinstance(rec, dict) else rec.rationale_ko,
                    "tags": rec.get("tags") if isinstance(rec, dict) else rec.tags
                }
                for rec in result.recipes
            ],
            "medications": [
                {
                    "name_ko": med.get("name_ko", med.get("name", "")),
                    "name_en": med.get("name_en", ""),
                    "classification": med.get("classification", ""),
                    "indication": med.get("indication", "주요 효능 정보 없음"),
                    "common_side_effects": med.get("common_side_effects", []),
                    "interaction_risk": med.get("interaction_risk", "unknown")
                }
                for med in get_drugs_info_list(all_medications)
            ],
            "cautions": result.cautions,
            "matched_symptom_name": result.matched_symptom_name,
            "disclaimer": result.disclaimer
        }
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] /api/analyze-with-image: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


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


@app.get("/api/cache-status")
async def get_cache_status():
    """Pre-computed 캐시 상태 조회"""
    cache_metadata_path = Path("data/cache/precomputed_metadata.json")
    
    if cache_metadata_path.exists():
        try:
            with open(cache_metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            return {
                "precomputed_cache_enabled": True,
                "generated_at": metadata.get("generated_at"),
                "total_diseases": metadata.get("total_diseases", 0),
                "cached_diseases": len(metadata.get("cached_diseases", [])),
                "failed_diseases": len(metadata.get("failed_diseases", [])),
                "diseases": metadata.get("cached_diseases", [])[:5]  # 처음 5개만
            }
        except Exception as e:
            return {
                "precomputed_cache_enabled": False,
                "error": str(e)
            }
    else:
        return {
            "precomputed_cache_enabled": False,
            "message": "Pre-computed 캐시 데이터가 없습니다"
        }

@app.get("/api/prescriptions")
async def get_prescriptions(user_id: Optional[str] = None):
    """저장된 처방전 목록 조회"""
    try:
        api = HealthStackAPI()
        prescriptions = api.medication_service.get_prescriptions(user_id)
        # 이미지 URL을 웹 접근 가능하게 변환
        for p in prescriptions:
            if "image_path" in p:
                # data/uploads/xxx.jpg -> /uploads/xxx.jpg
                p["image_url"] = p["image_path"].replace("data/uploads", "/uploads").replace("\\", "/")
        return {"prescriptions": prescriptions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
