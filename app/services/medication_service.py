import os
import json
from datetime import datetime
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
        self.db_path = "data/prescriptions.json"
        
        # Ensure data directory exists
        if not os.path.exists("data"):
            os.makedirs("data")
            
        # Initialize DB if not exists
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def save_prescription(self, image_path, drugs):
        """처방전 DB 저장 (JSON 기반 간이 DB)"""
        try:
            # Read existing
            data = []
            if os.path.exists(self.db_path):
                with open(self.db_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []
            
            entry = {
                "id": str(int(datetime.now().timestamp())),
                "date": datetime.now().isoformat(),
                "image_path": image_path,
                "drugs": drugs
            }
            data.append(entry)
            
            # Write back
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return entry
        except Exception as e:
            print(f"DB 저장 오류: {e}")
            return None

    async def get_drug_info(self, drug_name):
        """약물 정보 RAG 검색 (PubMed + Gemini)"""
        print(f"Searching info for: {drug_name}")
        
        # 1. PubMed 검색 (Retriever)
        # 약물 이름으로 검색 (side effects, mechanism 등 키워드 추가)
        papers = self.pubmed.search_papers(f"{drug_name} mechanism side effects", max_results=2)
        
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
            
            return {
                "name": drug_name,
                "info": info_text,
                "papers": [{"title": p.title, "url": p.url} for p in papers]
            }
            
        except Exception as e:
            print(f"RAG Generation Error: {e}")
            return {
                "name": drug_name, 
                "info": "정보를 불러오는 데 실패했습니다.", 
                "papers": []
            }
