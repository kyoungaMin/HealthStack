import os
import json
import shutil
from datetime import datetime
from app.services.pubmed_service import PubMedService
from app.utils.cache_manager import CacheManager

try:
    import google.generativeai as genai
    # Configure GenAI
    genai.configure(api_key=os.getenv("API_KEY"))
except ImportError:
    genai = None
    print("Warning: google-generative-ai module not found. RAG features will be disabled.")
except Exception as e:
    genai = None
    print(f"Warning: Failed to configure GenAI: {e}")

class MedicationService:
    def __init__(self):
        self.pubmed = PubMedService()
        self.cache = CacheManager()  # ★ 캐시 매니저 추가
        self.db_path = "data/prescriptions.json"
        
        # Ensure data directory exists
        if not os.path.exists("data"):
            os.makedirs("data")
        
        # Image upload dir
        self.upload_dir = "data/uploads"
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
            
        # Initialize DB if not exists
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def save_prescription(self, image_path, drugs, hospital_name=None, user_id=None):
        """처방전 DB 저장 (JSON 기반 간이 DB) - 약물 정보가 없어도 저장"""
        try:
            # Read existing
            data = []
            if os.path.exists(self.db_path):
                with open(self.db_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []
            
            # Generate permanent path
            entry_id = str(int(datetime.now().timestamp()))
            ext = os.path.splitext(image_path)[1] or ".jpg"
            filename = f"{entry_id}{ext}"
            saved_path = os.path.join(self.upload_dir, filename).replace("\\", "/") # Ensure web-friendly
            
            # Copy file
            shutil.copy2(image_path, os.path.join(self.upload_dir, filename))
            
            # ★ 개선: drugs가 비어있으면 기본값 설정
            drug_list = drugs if drugs else ["약물 미식별"]
            
            entry = {
                "id": entry_id,
                "user_id": user_id,  # 사용자 ID 추가
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "image_path": saved_path,
                "hospital_name": hospital_name or "병원명 미상",
                "drugs": drug_list
            }
            data.append(entry)
            
            # Write back
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Prescription saved: {entry_id} with {len(drug_list)} drugs")
            return entry
        except Exception as e:
            print(f"❌ DB 저장 오류: {e}")
            return None

    def get_prescriptions(self, user_id=None):
        """저장된 처방전 목록 조회 (사용자 ID로 필터링)"""
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if user_id:
                        return [d for d in data if d.get("user_id") == user_id]
                    return data
                except:
                    return []
        return []

    async def get_drug_info(self, drug_name):
        """약물 정보 RAG 검색 (PubMed + Gemini) - 캐싱 적용"""
        print(f"[Drug Info] Searching: {drug_name}")
        
        # ★ 캐시 확인 (TTL: 7일)
        cache_key = f"drug_info:{drug_name}"
        cached_data = self.cache.get("drug_info", cache_key, ttl_hours=168)
        if cached_data:
            print(f"[Cache HIT] Returning cached drug info for: {drug_name}")
            return cached_data
        
        print(f"[Cache MISS] Fetching fresh data for: {drug_name}")
        
        # 0. 영문 변환 (PubMed 검색용)
        drug_name_en = await self.pubmed.translate_to_english(drug_name)
        print(f"[Translation] {drug_name} -> {drug_name_en}")

        # 1. PubMed 검색 (Retriever) - 영문명으로 검색
        papers = await self.pubmed.search_papers(f"{drug_name_en} mechanism side effects", max_results=2)
        
        context = ""
        if papers:
            context = "\n\n".join([f"Paper: {p.title}\nAbstract: {p.abstract}" for p in papers])
        
        # 2. Gemini Generation (Generator)
        try:
            if not genai:
                raise ImportError("Google Generative AI module is not available.")
                
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
            Role: 약사
            Target: 환자
            
            Instruction: 아래 약물에 대해 분석하고, 제공된 의학 논문(PubMed) 내용을 참고하여(RAG), 환자에게 필요한 정보를 요약해 주세요.
            
            약물명: {drug_name}
            
            [관련 논문 초록]
            {context}
            
            [응답 형식]
            마크다운 형식을 사용하지 말고, 평문 텍스트로 깔끔하게.
            1. 🟢 효능: (무엇을 치료하는 약인지)
            2. ⚠️ 주의: (주요 부작용이나 주의사항)
            3. 💡 팁: (복용 시 꿀팁)
            
            분량은 300자 이내로 핵심만.
            """
            
            # 비동기 호출
            response = await model.generate_content_async(prompt)
            info_text = response.text
            
            result = {
                "name": drug_name,
                "info": info_text,
                "papers": [{"title": p.title, "url": p.url} for p in papers]
            }
            
            # ★ 결과를 캐시에 저장
            self.cache.set(
                "drug_info",
                cache_key,
                result,
                metadata={"drug_name_en": drug_name_en, "paper_count": len(papers)}
            )
            
            return result
            
        except Exception as e:
            print(f"[RAG Generation Error] {e}")
            return {
                "name": drug_name, 
                "info": "정보를 불러오는 데 실패했습니다.",
                "papers": []
            }
