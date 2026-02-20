import os
import json
import shutil
from datetime import datetime
from app.services.pubmed_service import PubMedService
from app.utils.cache_manager import CacheManager

try:
    from google import genai
    # Ensure API Key is available
    if not os.getenv("API_KEY"):
        print("Warning: API_KEY not set for google-genai")
except ImportError:
    genai = None
    print("Warning: google-genai module not found. RAG features will be disabled.")
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

    def save_prescription(self, image_path, drugs, hospital_name=None, user_id=None, drug_info_dict=None):
        """처방전 DB 저장 (JSON 기반 간이 DB) - 약물 영문명도 함께 저장"""
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
            
            # ★ 개선: 약물 정보를 구조화된 형태로 저장 (한글명 + 영문명)
            drug_list = []
            if drugs:
                for drug_name in drugs:
                    if drug_info_dict and drug_name in drug_info_dict:
                        # 약물 정보가 있으면 한글명, 영문명, 유형을 모두 저장
                        drug_info = drug_info_dict[drug_name]
                        drug_list.append({
                            "korean_name": drug_name,
                            "scientific_name": drug_info.get('scientific_name', drug_name),
                            "english_name": drug_info.get('english_name', drug_info.get('scientific_name', drug_name)),
                            "type": drug_info.get('type', 'Unknown'),
                            "indication": drug_info.get('indication', '')
                        })
                    else:
                        # 정보가 없으면 약물명만 저장
                        drug_list.append({
                            "korean_name": drug_name,
                            "scientific_name": drug_name,
                            "english_name": drug_name,
                            "type": "Unknown",
                            "indication": ""
                        })
            else:
                drug_list = [{
                    "korean_name": "약물 미식별",
                    "scientific_name": "Unknown",
                    "english_name": "Unknown",
                    "type": "Unknown",
                    "indication": ""
                }]
            
            entry = {
                "id": entry_id,
                "user_id": user_id,  # 사용자 ID 추가
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "image_path": saved_path,
                "hospital_name": hospital_name or "병원명 미상",
                "drugs": drug_list  # 구조화된 약물 정보
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

        # 1. PubMed 검색 (Retriever) - 영문명으로 검색 (최적화: max_results=1)
        papers = await self.pubmed.search_papers(f"{drug_name_en} mechanism side effects", max_results=1)

        context = ""
        if papers:
            context = "\n\n".join([f"Paper: {p.title}\nAbstract: {p.abstract}" for p in papers])

        # 2. OpenAI 직접 사용 (Gemini 할당량 없음으로 스킵)
        try:
            import openai
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                raise ValueError("OPENAI_API_KEY not found")

            client = openai.AsyncOpenAI(api_key=openai_key)

            prompt = f"""약물명: {drug_name}

아래 의학 논문을 참고하여 환자에게 약물 정보를 설명해주세요.

[관련 논문 초록]
{context}

[응답 형식]
1. 🟢 효능: (무엇을 치료하는 약인지)
2. ⚠️ 주의: (주요 부작용이나 주의사항)
3. 💡 팁: (복용 시 꿀팁)

300자 이내로 핵심만 작성해주세요."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 친절한 약사입니다. 환자에게 약물 정보를 쉽게 설명해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            info_text = response.choices[0].message.content

            result = {
                "name": drug_name,
                "info": info_text,
                "papers": [{"title": p.title, "url": p.url} for p in papers]
            }

            # 캐시에 저장
            self.cache.set(
                "drug_info",
                cache_key,
                result,
                metadata={"drug_name_en": drug_name_en, "paper_count": len(papers), "source": "openai"}
            )

            print(f"[OpenAI Direct Success] {drug_name}")
            return result

        except Exception as openai_error:
            print(f"[OpenAI Direct Failed] {openai_error}")
            return {
                "name": drug_name,
                "info": "정보를 불러오는 데 실패했습니다.",
                "papers": []
            }
