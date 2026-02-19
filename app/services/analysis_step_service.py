from typing import Dict, List, Optional, Any
from .naver_ocr_service import NaverOCRService
from .medication_service import MedicationService 
from .analyze_service import AnalyzeService, AnalysisResult, Ingredient, Recipe # Import new service

class StepByStepAnalysisService:
    def __init__(self):
        # OCR Service
        self.ocr_service = NaverOCRService()
        self.analyze_service = AnalyzeService() # Reuse AnalyzeService
        
        # In-memory storage for simple session management (Replace with Redis/DB in production)
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def step1_extract(self, search_type: str, text: Optional[str], image_url: Optional[str]) -> Dict[str, Any]:
        """
        [Step 1] Symptom text or Prescription OCR -> Initial Keywords
        """
        import uuid
        session_id = str(uuid.uuid4())
        
        detected_keywords = []
        ocr_text = ""
        
        if search_type == "symptom":
            # For symptom search, text is the input
            if text:
                # Simple keyword extraction (can be enhanced with NLP)
                # Here we just mock or split
                keywords = [k.strip() for k in text.split() if len(k.strip()) > 1]
                detected_keywords = [{"keyword": k, "confidence": 1.0} for k in keywords]
                ocr_text = text # Just echo for symptom
                
        elif search_type == "prescription":
            if image_url:
                # Call Naver OCR
                ocr_text = self.ocr_service.extract_text_from_url(image_url)
                
                # Parse OCR result to find drug names / symptoms
                drug_names = self.ocr_service.parse_ocr_result(ocr_text)
                
                # Keywords are drug names
                detected_keywords = [{"keyword": k, "confidence": 0.9} for k in drug_names]
        
        # Save session state
        self._sessions[session_id] = {
            "type": search_type,
            "raw_text": ocr_text,
            "keywords": [k["keyword"] for k in detected_keywords]
        }
        
        return {
            "session_id": session_id,
            "detected_keywords": detected_keywords,
            "ocr_text": ocr_text
        }

    def step2_search(self, session_id: str, confirmed_keywords: List[str]) -> Dict[str, Any]:
        """
        [Step 2] Confirmed Keywords -> Candidate Search (TKM Symptoms, Modern Drugs)
        """
        # Update session
        if session_id in self._sessions:
            self._sessions[session_id]["keywords"] = confirmed_keywords
        
        # 1. Search DB for TKM Symptoms (disease_master)
        # Using Supabase (via AnalyzeService's client or direct)
        db = self.analyze_service.db
        
        tkm_candidates = []
        modern_candidates = []
        
        try:
            for keyword in confirmed_keywords:
                # A. Search TKM Symptoms
                # Search by name or description
                res_tkm = db.table("disease_master").select("id, modern_name_ko, disease_read, description").or_(
                    f"modern_name_ko.ilike.%{keyword}%,"
                    f"disease_read.ilike.%{keyword}%"
                ).limit(5).execute()
                
                for item in res_tkm.data:
                    c = {
                        "id": item["id"],
                        "name": item.get("modern_name_ko") or item.get("disease_read"),
                        "description": item.get("description"),
                        "match_score": 0.9, # Mock score
                        "type": "tkm_symptom"
                    }
                    if c not in tkm_candidates: # Deduplicate simple
                         tkm_candidates.append(c)
                
                # B. Search Modern Drugs (catalog_drugs)
                # Ensure catalog_drugs table exists or use medication_service logic
                # Let's assume catalog_drugs table
                res_drug = db.table("catalog_drugs").select("id, name_ko, name_en, manufacturer, description, category").or_(
                     f"name_ko.ilike.%{keyword}%,"
                     f"name_en.ilike.%{keyword}%"
                ).limit(5).execute()
                
                for item in res_drug.data:
                    c = {
                         "id": item["id"],
                         "name": f"{item.get('name_ko')} ({item.get('name_en')})",
                         "description": item.get("description"),
                         "category": item.get("category"),
                         "match_score": 0.95,
                         "type": "modern_drug",
                         "efficacy": item.get("description") # using description as efficacy
                    }
                    if c not in modern_candidates:
                        modern_candidates.append(c)

        except Exception as e:
            print(f"Search candidates error: {e}")
            
        return {
            "candidates": {
                "tkm_symptoms": tkm_candidates,
                "modern_drugs": modern_candidates
            }
        }

    async def step3_report(self, session_id: str, selected_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        [Step 3] Selected Candidates -> Final Report (using AnalyzeService & LLM)
        """
        # Group selections
        symptom_texts = []
        meds = []
        
        for cand in selected_candidates:
            c_type = cand.get("type", "")
            c_id = cand.get("id")
            
            # Fetch details if needed, or just rely on IDs if AnalyzeService supports it
            # But AnalyzeService mostly takes text.
            # Let's fetch names to pass to AnalyzeService
            
            if c_type == "tkm_symptom":
                 # Fetch name
                 res = self.analyze_service.db.table("disease_master").select("modern_name_ko").eq("id", c_id).single().execute()
                 if res.data:
                     symptom_texts.append(res.data["modern_name_ko"])
            elif c_type == 'modern_drug':
                 # Fetch name
                 res = self.analyze_service.db.table("catalog_drugs").select("name_ko, name_en").eq("id", c_id).single().execute()
                 if res.data:
                     meds.append(res.data["name_ko"] or res.data["name_en"])
        
        # Combine symptom texts
        final_symptom_text = ", ".join(symptom_texts)
        if not final_symptom_text and not meds:
             # Fallback to session keywords if nothing selected (though UI warns)
             if session_id in self._sessions:
                 final_symptom_text = ", ".join(self._sessions[session_id]["keywords"])
        
        # Call AnalyzeService (Async)
        # Warning: analyze_symptom is async, we must await it.
        # But this method (step3_report) was synchronous in interface.
        # We need to change the interface to async.
        
        analysis_result: AnalysisResult = await self.analyze_service.analyze_symptom(final_symptom_text, meds)
        
        # Transform AnalysisResult to API Response format
        recommended = []
        avoid = []
        
        for ing in analysis_result.ingredients:
            item = {
                "name": ing.modern_name,
                "reason": ing.rationale_ko,
                "tip": "함께 드시면 더욱 좋습니다." # Mock tip or from DB
            }
            if ing.direction == "recommend" or ing.direction == "good":
                recommended.append(item)
            else:
                avoid.append(item)
        
        # Extract Cautions/Medication Guide
        # AnalysisResult has `cautions` list which are strings
        # ReportData expects `medication_guide` as dict.
        medication_guide = {}
        for idx, caution in enumerate(analysis_result.cautions):
             medication_guide[f"주의사항 {idx+1}"] = caution
             
        # Lifestyle Advice - Not in AnalysisResult explicitly, but maybe in summary?
        # Let's create a synthesized advice or extract from summary.
        # Or add lifestyle_advice field to AnalysisResult later.
        lifestyle_advice = "규칙적인 식습관과 충분한 휴식이 필요합니다."
        if "수면" in final_symptom_text:
            lifestyle_advice = "잠들기 2시간 전에는 스마트폰 사용을 자제하고 따뜻한 우유를 마시는 것이 좋습니다."
        elif "소화" in final_symptom_text:
            lifestyle_advice = "식사 후 30분 정도 가벼운 산책을 하는 것이 소화에 도움이 됩니다."

        return {
            "summary": analysis_result.symptom_summary,
            "medication_guide": medication_guide,
            "food_therapy": {
                "recommended": recommended,
                "avoid": avoid
            },
            "lifestyle_advice": lifestyle_advice,
            "source": analysis_result.source
        }
