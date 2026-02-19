from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Union

# --- Step 1: Extract ---
class Step1ExtractRequest(BaseModel):
    search_type: str = Field(..., description="'symptom' or 'prescription'")
    text: Optional[str] = None
    image_url: Optional[str] = None

class DetectedKeyword(BaseModel):
    keyword: str
    confidence: float

class Step1ExtractResponse(BaseModel):
    data: Dict[str, Any]

# --- Step 2: Search ---
class Step2SearchRequest(BaseModel):
    session_id: str
    confirmed_keywords: List[str]

class CandidateItem(BaseModel):
    id: Union[int, str]
    name: str
    description: Optional[str] = None
    match_score: Optional[float] = None
    efficacy: Optional[str] = None # For drugs
    category: Optional[str] = None

class SearchCandidates(BaseModel):
    tkm_symptoms: List[CandidateItem]
    modern_drugs: List[CandidateItem]

class Step2SearchResponse(BaseModel):
    data: Dict[str, SearchCandidates]

# --- Step 3: Report ---
class SelectedCandidate(BaseModel):
    type: str # 'tkm_symptom' or 'modern_drug'
    id: Union[int, str]

class Step3ReportRequest(BaseModel):
    session_id: str
    selected_candidates: List[SelectedCandidate]

class FoodItem(BaseModel):
    name: str
    reason: str

class FoodTherapy(BaseModel):
    recommended: List[FoodItem]
    avoid: List[FoodItem]

class Step3ReportData(BaseModel):
    summary: str
    medication_guide: Optional[Dict[str, str]] = None
    food_therapy: FoodTherapy
    lifestyle_advice: str

class Step3ReportResponse(BaseModel):
    data: Step3ReportData


# --- Prescription Image Analysis ---
class DrugDetail(BaseModel):
    name: str
    efficacy: str
    sideEffects: str

class PrescriptionSummary(BaseModel):
    drugList: List[str]
    warnings: str

class AcademicEvidence(BaseModel):
    summary: str
    trustLevel: str
    papers: Optional[List[Dict[str, str]]] = []

class LifestyleGuide(BaseModel):
    symptomTokens: List[str]
    advice: str

class DonguibogamFood(BaseModel):
    name: str
    reason: str
    precaution: str

class DonguibogamSection(BaseModel):
    foods: List[DonguibogamFood]
    donguiSection: str

class PrescriptionAnalysisResponse(BaseModel):
    prescriptionSummary: PrescriptionSummary
    drugDetails: List[DrugDetail]
    academicEvidence: AcademicEvidence
    lifestyleGuide: LifestyleGuide
    donguibogam: DonguibogamSection


# --- Pill Identification (낱알정보) ---
class PillSearchByNameRequest(BaseModel):
    drug_name: str = Field(..., description="약품명 (예: 타이레놀정)")

class PillSearchByAppearanceRequest(BaseModel):
    drug_shape: Optional[str] = Field(None, description="약 모양 (예: 원형, 타원형, 장방형)")
    color_class1: Optional[str] = Field(None, description="색깔 앞면 (예: 하양, 노랑, 분홍)")
    color_class2: Optional[str] = Field(None, description="색깔 뒷면")
    mark_front: Optional[str] = Field(None, description="각인 앞면 텍스트")
    mark_back: Optional[str] = Field(None, description="각인 뒷면 텍스트")
    leng_long: Optional[str] = Field(None, description="장축 크기(mm)")
    leng_short: Optional[str] = Field(None, description="단축 크기(mm)")

class PillInfoItem(BaseModel):
    itemSeq: str
    itemName: str
    manufacturer: str
    chart: str
    imageUrl: str
    printFront: str
    printBack: str
    drugShape: str
    colorFront: str
    colorBack: str
    lineFront: str
    lineBack: str
    lengLong: str
    lengShort: str
    thick: str
    formName: str
    className: str
    etcOtc: str
    ediCode: str
    source: str

class PillSearchResponse(BaseModel):
    total: int
    items: List[PillInfoItem]
