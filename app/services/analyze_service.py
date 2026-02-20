"""
통합 분석 서비스 모듈
증상 분석 → 동의보감 식재료 추천 → PubMed 근거 연결
3단계 Fallback 전략 적용 + API 캐싱
"""
import os
import sys
import json
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.supabase_client import get_supabase_client
from app.utils.cache_manager import CacheManager
try:
    import google.genai as genai
except ImportError:
    import google.generativeai as genai

# DUR 서비스는 순환참조 방지를 위해 지연 임포트
_dur_service = None

def _get_dur_service():
    global _dur_service
    if _dur_service is None:
        from app.services.dur_service import DurService
        _dur_service = DurService()
    return _dur_service


@dataclass
class Ingredient:
    """추천 식재료 정보"""
    rep_code: str
    modern_name: str
    rationale_ko: str
    direction: str  # recommend | good | neutral | caution | avoid
    priority: int
    evidence_level: str  # traditional | clinical | empirical


@dataclass
class Recipe:
    """추천 레시피 정보"""
    id: int
    title: str
    description: str
    meal_slot: str
    priority: int
    rationale_ko: str
    tags: list[str]


@dataclass
class AnalysisResult:
    """분석 결과"""
    symptom_summary: str
    ingredients: list[Ingredient] = field(default_factory=list)
    recipes: list[Recipe] = field(default_factory=list)
    confidence_level: str = "general"  # high | medium | general
    source: str = "ai_generated"  # database | similarity | ai_generated
    matched_symptom_id: Optional[int] = None
    matched_symptom_name: Optional[str] = None
    cautions: list[str] = field(default_factory=list)
    related_questions: list[dict] = field(default_factory=list)


class AnalyzeService:
    """통합 분석 서비스"""
    
    def __init__(self):
        self.db = get_supabase_client()
        self.cache = CacheManager()  # ★ 캐시 매니저 추가
    
    def _check_interactions(self, drug_names: list[str], ingredients: list[Ingredient]) -> list[str]:
        """
        약물-식재료 상호작용 체크
        1차: Supabase interaction_facts 테이블
        2차: DUR API fallback (DB에 데이터 없을 때)
        """
        cautions = []
        if not drug_names or not ingredients:
            return []

        # Handle both dict and Ingredient object
        ing_names = set()
        for i in ingredients:
            if isinstance(i, dict):
                ing_names.add(i.get("modern_name", ""))
            else:
                ing_names.add(i.modern_name)

        db_hit = False

        try:
            for drug in drug_names:
                result = self.db.table("interaction_facts").select("*").or_(
                    f"a_ref.ilike.%{drug}%,"
                    f"b_ref.ilike.%{drug}%"
                ).execute()

                if not result.data:
                    continue

                db_hit = True
                for row in result.data:
                    other = row['b_ref'] if drug in row['a_ref'] else row['a_ref']
                    for ing in ing_names:
                        if ing in other or other in ing:
                            cautions.append(
                                f"⚠️ [약물상호작용] '{drug}' + '{ing}' 주의: "
                                f"{row.get('summary_ko', '')} ({row.get('severity', '주의')})"
                            )
        except Exception as e:
            print(f"Interaction check (DB) error: {e}")

        # 2차: DB에 데이터 없으면 DUR API로 약물-약물 병용금기 확인
        if not db_hit and len(drug_names) >= 2:
            try:
                dur = _get_dur_service()
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 이미 async 컨텍스트면 future 생성
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, dur.check_interactions(drug_names))
                        dur_results = future.result(timeout=15)
                else:
                    dur_results = loop.run_until_complete(dur.check_interactions(drug_names))

                for item in dur_results:
                    icon = "🚫" if item["severity"] == "CONTRAINDICATED" else "⚠️"
                    cautions.append(
                        f"{icon} [DUR 병용금기] '{item['drug_a']}' + '{item['drug_b']}' — "
                        f"{item['reason'] or '병용 주의'}"
                    )
            except Exception as e:
                print(f"Interaction check (DUR API) error: {e}")

        return list(set(cautions))

    async def analyze_symptom(self, symptom_text: str, current_meds: list[str] = None) -> AnalysisResult:
        """
        증상 텍스트를 분석하고 식재료를 추천합니다. (Wrapper with Global Error Handling)
        """
        try:
            return await self._analyze_symptom_logic(symptom_text, current_meds)
        except Exception as e:
            print(f"CRITICAL ANALYZE ERROR: {e}")
            try:
                # 최후의 수단: AI Fallback
                return await self._analyze_with_ai(symptom_text, current_meds)
            except Exception as ai_e:
                print(f"AI FALLBACK FAILED: {ai_e}")
                import traceback
                traceback.print_exc()
                return AnalysisResult(
                    symptom_summary="시스템 오류가 발생했습니다.",
                    confidence_level="error",
                    source="error"
                )

    async def _analyze_symptom_logic(self, symptom_text: str, current_meds: list[str] = None) -> AnalysisResult:
        """
        증상 분석 핵심 로직
        """
        # ★ 신규: 0차 - 유사도 기반 캐시 조회 (매우 빠름, 0.1초)
        # TEMPORARILY DISABLED FOR DEBUGGING
        cache_key = f"{symptom_text}|{','.join(current_meds or [])}"
        cached_result = None  # self.cache.get_with_similarity("ai_analysis", cache_key, threshold=0.80)

        if cached_result:
            print(f"✅ [Cache] 유사도 캐시 히트! 캐시된 분석 결과 반환 (0.1초)")
            # 캐시된 결과를 AnalysisResult로 복원
            try:
                # Convert dict to Ingredient objects
                ingredients_list = []
                for ing in cached_result.get("ingredients", []):
                    if isinstance(ing, dict):
                        ingredients_list.append(Ingredient(
                            rep_code=ing.get("rep_code", ""),
                            modern_name=ing.get("modern_name", ""),
                            rationale_ko=ing.get("rationale_ko", ""),
                            direction=ing.get("direction", "recommend"),
                            priority=ing.get("priority", 100),
                            evidence_level=ing.get("evidence_level", "")
                        ))
                    else:
                        ingredients_list.append(ing)

                # Convert dict to Recipe objects
                recipes_list = []
                for rec in cached_result.get("recipes", []):
                    if isinstance(rec, dict):
                        recipes_list.append(Recipe(
                            id=rec.get("id", 0),
                            title=rec.get("title", ""),
                            description=rec.get("description", ""),
                            meal_slot=rec.get("meal_slot", "anytime"),
                            priority=rec.get("priority", 50),
                            rationale_ko=rec.get("rationale_ko", ""),
                            tags=rec.get("tags", [])
                        ))
                    else:
                        recipes_list.append(rec)

                return AnalysisResult(
                    symptom_summary=cached_result.get("symptom_summary"),
                    ingredients=ingredients_list,
                    recipes=recipes_list,
                    confidence_level=cached_result.get("confidence_level", "general"),
                    source="cache_similarity",
                    matched_symptom_name=cached_result.get("matched_symptom_name"),
                    cautions=cached_result.get("cautions", []),
                    related_questions=cached_result.get("related_questions", [])
                )
            except Exception as e:
                print(f"⚠️ 캐시 복원 오류: {e}, 일반 분석 진행")
        
        # 1차: disease_master 정확 매칭
        matched = self._search_exact_symptom(symptom_text)
        
        if matched:
            ingredients = self._get_ingredients_from_db(matched["id"])
            recipes = self._get_recipes_from_db(matched["id"])
            
            # 데이터 부족(식재료 없음) 시 AI Fallback
            if not ingredients and not recipes:
                print(f"데이터 부족(정확매칭/식재료없음) -> AI 전환: {matched.get('modern_name_ko')}")
                return await self._analyze_with_ai(symptom_text, current_meds)

            # 레시피 부족 시 AI 자동 생성 및 저장
            if not recipes:
                print(f"레시피 부족(정확매칭): {matched['modern_name_ko']} -> AI 생성 시도")
                recipes = await self._generate_and_save_recipes(matched["id"], matched["modern_name_ko"])
                
            cautions = []
            if current_meds:
                cautions = self._check_interactions(current_meds, ingredients)

            return AnalysisResult(
                symptom_summary=f"{matched.get('modern_name_ko', matched.get('disease_read', ''))} 관련 증상입니다.",
                ingredients=ingredients,
                recipes=recipes,
                confidence_level="high",
                source="database",
                matched_symptom_id=matched["id"],
                matched_symptom_name=matched.get("modern_name_ko"),
                cautions=cautions
            )
        
        # 2차: 유사 증상 검색 (aliases, 부분 매칭)
        similar = self._search_similar_symptom(symptom_text)
        
        if similar:
            ingredients = self._get_ingredients_from_db(similar["id"])
            recipes = self._get_recipes_from_db(similar["id"])
            
            # 데이터 부족(식재료 없음) 시 AI Fallback
            if not ingredients and not recipes:
                print(f"데이터 부족(유사매칭/식재료없음) -> AI 전환: {similar.get('modern_name_ko')}")
                return await self._analyze_with_ai(symptom_text, current_meds)

            # 레시피 부족 시 AI 자동 생성 및 저장
            if not recipes:
                print(f"레시피 부족(유사매칭): {similar.get('modern_name_ko')} -> AI 생성 시도")
                recipes = await self._generate_and_save_recipes(similar["id"], similar.get('modern_name_ko', symptom_text))

            cautions = []
            if current_meds:
                cautions = self._check_interactions(current_meds, ingredients)

            return AnalysisResult(
                symptom_summary=f"'{similar.get('modern_name_ko', '')}' 증상과 유사합니다.",
                ingredients=ingredients,
                recipes=recipes,
                confidence_level="medium",
                source="similarity",
                matched_symptom_id=similar["id"],
                matched_symptom_name=similar.get("modern_name_ko"),
                cautions=cautions
            )
        
        # 3차: AI Fallback (Gemini 호출)
        return await self._analyze_with_ai(symptom_text, current_meds)

    async def _generate_and_save_recipes(self, symptom_id: int, symptom_name: str) -> list[Recipe]:
        """
        DB에 레시피가 없을 때 AI로 생성하여 DB에 저장하고 반환
        """
        try:
            api_key = os.getenv("API_KEY")
            if not api_key:
                return []

            client = genai.Client(api_key=api_key)
            
            prompt = f"""
            Role: Culinary Therapist
            Task: Create 2 healthy recipes helpful for the symptom: "{symptom_name}".
            
            Output Format: JSON string ONLY.
            [
                {{
                    "title": "Recipe Title (Korean)",
                    "description": "Brief description",
                    "meal_slot": "breakfast" | "lunch" | "dinner" | "tea" | "snack",
                    "rationale": "Why this helps (Korean)",
                    "difficulty": "easy" | "medium" | "hard",
                    "tags": ["tag1", "tag2"]
                }}
            ]
            """
            
            response = await client.aio.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt
            )
            text_response = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(text_response)
            
            generated_recipes = []
            
            for item in data:
                # 1. Insert into recipes table
                recipe_data = {
                    "title": item.get("title"),
                    "description": item.get("description"),
                    "difficulty": item.get("difficulty", "easy"),
                    "tags": item.get("tags", []),
                    "ingredients": [], # Placeholder
                    "steps": []       # Placeholder
                }
                
                # supabase insert and get id
                # Note: supabase-py insert returns data if select() is chained or usually returns data by default in v2?
                # Using execute() returns result.
                res_recipe = self.db.table("recipes").insert(recipe_data).select("id").execute()
                
                if res_recipe.data:
                    new_id = res_recipe.data[0]["id"]
                    
                    # 2. Insert into symptom_recipe_map
                    map_data = {
                        "symptom_id": symptom_id,
                        "recipe_id": new_id,
                        "rationale_ko": item.get("rationale"),
                        "meal_slot": item.get("meal_slot", "anytime"),
                        "priority": 80
                    }
                    self.db.table("symptom_recipe_map").insert(map_data).execute()
                    
                    # Add to list
                    generated_recipes.append(Recipe(
                        id=new_id,
                        title=item.get("title"),
                        description=item.get("description"),
                        meal_slot=item.get("meal_slot", "anytime"),
                        priority=80,
                        rationale_ko=item.get("rationale"),
                        tags=item.get("tags", [])
                    ))
            
            return generated_recipes

        except Exception as e:
            print(f"레시피 생성/저장 실패: {e}")
            return []

    async def _analyze_with_ai(self, symptom_text: str, current_meds: list[str] = None) -> AnalysisResult:
        """Call Gemini to analyze symptom and recommend ingredients/recipes - 캐싱 적용"""
        import json
        
        # ★ 캐시 키 생성 (증상 + 약물 조합)
        cache_key = f"ai_analysis:{symptom_text}:{','.join(sorted(current_meds or []))}"
        
        # ★ 캐시 확인 (TTL: 3일)
        # TEMPORARILY DISABLED FOR DEBUGGING
        cached_result = None  # self.cache.get("ai_analysis", cache_key, ttl_hours=72)
        if cached_result:
            print(f"[Cache HIT] Returning cached AI analysis result")
            # 캐시된 dict를 AnalysisResult로 복원 (ingredients와 recipes를 객체로 변환)
            try:
                ingredients_list = []
                for ing in cached_result.get("ingredients", []):
                    if isinstance(ing, dict):
                        ingredients_list.append(Ingredient(
                            rep_code=ing.get("rep_code", ""),
                            modern_name=ing.get("modern_name", ""),
                            rationale_ko=ing.get("rationale_ko", ""),
                            direction=ing.get("direction", "recommend"),
                            priority=ing.get("priority", 100),
                            evidence_level=ing.get("evidence_level", "")
                        ))
                    else:
                        ingredients_list.append(ing)

                recipes_list = []
                for rec in cached_result.get("recipes", []):
                    if isinstance(rec, dict):
                        recipes_list.append(Recipe(
                            id=rec.get("id", 0),
                            title=rec.get("title", ""),
                            description=rec.get("description", ""),
                            meal_slot=rec.get("meal_slot", "anytime"),
                            priority=rec.get("priority", 50),
                            rationale_ko=rec.get("rationale_ko", ""),
                            tags=rec.get("tags", [])
                        ))
                    else:
                        recipes_list.append(rec)

                return AnalysisResult(
                    symptom_summary=cached_result.get("symptom_summary"),
                    ingredients=ingredients_list,
                    recipes=recipes_list,
                    confidence_level=cached_result.get("confidence_level", "general"),
                    source=cached_result.get("source", "cache"),
                    matched_symptom_id=cached_result.get("matched_symptom_id"),
                    matched_symptom_name=cached_result.get("matched_symptom_name"),
                    cautions=cached_result.get("cautions", []),
                    related_questions=cached_result.get("related_questions", [])
                )
            except Exception as e:
                print(f"[Cache ERROR] Failed to restore cached result: {e}, fetching fresh data")
        
        print(f"[Cache MISS] Fetching fresh AI analysis")
            
        # 증상 텍스트가 없고 약물만 있는 경우, 약물 정보를 증상 텍스트로 변환
        if (not symptom_text or len(symptom_text.strip()) < 2) and current_meds:
            symptom_text = f"Prescribed Medications: {', '.join(current_meds)}"
            print(f"[Analysis] Empty symptom -> Inferred from meds: {symptom_text}")

        prompt = f"""
Role: Clinical Pharmacist & Oriental Medicine Doctor
Task: Analyze the inputs to INFER the user's underlying health condition/symptom.

Input Data:
- User Symptom/Text: "{symptom_text}"
- Prescribed Meds: {current_meds if current_meds else "None"}

CRITICAL INSTRUCTION:
1. If 'User Symptom' contains names of medications (e.g., Tylenol, Amlodipine) or is empty, **YOU MUST INFER the condition**.
   - E.g., "Amlodipine" -> Infer "High Blood Pressure"
   - E.g., "Metformin" -> Infer "Diabetes"
   - E.g., "Tylenol" -> Infer "Pain/Headache"
2. DO NOT say "I cannot determine the symptom". Make a reasonable medical inference based on the drugs.
3. Based on the INFERRED symptom, recommend food ingredients and recipes.

Output Format: JSON string ONLY (NO markdown, NO triple backticks).
Return ONLY valid JSON, starting with {{ and ending with }}.
DO NOT include ```json or ``` markers.

{{
    "symptom_name": "Inferred Symptom Name",
    "summary": "Brief explanation of the Inferred Symptom in Korean (polite tone, ~해요체)",
    "ingredients": [
        {{
            "name": "Ingredient Name (Korean)",
            "direction": "recommend" | "avoid",
            "rationale": "Why this is good/bad for the inferred symptom (Korean)"
        }}
    ],
    "recipes": [
        {{
            "title": "Recipe Title (Korean)",
            "description": "Brief description",
            "meal_slot": "breakfast" | "lunch" | "dinner" | "tea" | "snack",
            "rationale": "Why this recipe helps"
        }}
    ]
}}

Constraints:
- Provide 3 ingredients (mix of recommend/avoid).
- Provide 2 recipes.
- Start rationale with the ingredient/recipe name.

CRITICAL INSTRUCTION:
1. If 'User Symptom' contains prescription text or is unclear, **INFER the most likely symptom** from 'User Meds' or OCR text keywords.
   (e.g., 'Tylenol' -> 'Pain/Headache', 'Mucosolvan' -> 'Cold/Cough', 'Amlodipine' -> 'Hypertension')
2. NEVER say "I cannot find the symptom" or "General advice". Always generate specific advice for the inferred symptom.
3. If inferred symptom is 'High Blood Pressure' or 'Diabetes', recommend 'Low Sodium' or 'Low GI' foods.
"""
        
        data = None
        source = "ai_generated_openai"

        # 2. Use OpenAI Directly (Gemini 할당량 없음으로 스킵)
        try:
            import openai
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                raise ValueError("OpenAI API Key not found")

            client = openai.AsyncOpenAI(api_key=openai_key)

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful Oriental Medicine expert. Respond in JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            text_response = response.choices[0].message.content
            data = json.loads(text_response)
            print(f"[OpenAI Analysis Success]")

        except Exception as e_openai:
            print(f"[OpenAI Analysis Failed] {e_openai}")
            return AnalysisResult(
                symptom_summary="AI 분석 서비스 연결에 실패했습니다.",
                ingredients=[], recipes=[], confidence_level="none", source="error"
            )

        # 4. Process Result
        if data is None: # This should ideally not happen if both try blocks are handled, but as a safeguard
            return AnalysisResult(
                symptom_summary="AI 분석 결과를 처리하는 중 오류가 발생했습니다.",
                ingredients=[],
                recipes=[],
                confidence_level="general",
                source="error"
            )
        
        ingredients = []
        if "ingredients" in data:
            for ing_data in data["ingredients"]:
                try:
                    ingredients.append(Ingredient(
                        rep_code="AI_GEN",  # Temporary code
                        modern_name=ing_data.get("name", "Unknown"),
                        rationale_ko=ing_data.get("rationale", ""),
                        direction=ing_data.get("direction", "recommend"),
                        priority=90 if ing_data.get("direction") == "recommend" else 10,
                        evidence_level="ai_generated"
                    ))
                except Exception as loop_e:
                    print(f"Error processing ingredient data: {ing_data}. Error: {loop_e}")
                    # Optionally, you can log this error or skip this ingredient
                    continue
            
        recipes = []
        if "recipes" in data:
            for rec in data["recipes"]:
                recipes.append(Recipe(
                    id=0,  # Temporary ID
                    title=rec.get("title", ""),
                    description=rec.get("description", ""),
                    meal_slot=rec.get("meal_slot", "anytime"),
                    priority=80,
                    rationale_ko=rec.get("rationale", ""),
                    tags=["AI"]
                ))
            
        # Optional: Save to DB (Log new symptom)
        # self._log_new_symptom(data["symptom_name"], symptom_text)
            
        cautions = []
        if current_meds:
            cautions = self._check_interactions(current_meds, ingredients)

        result = AnalysisResult(
            symptom_summary=data.get("summary", "AI 분석 결과입니다."),
            ingredients=ingredients,
            recipes=recipes,
            confidence_level="general",
            source=source,
            matched_symptom_name=data.get("symptom_name"),
            cautions=cautions
        )
        
        # ★ 결과를 캐시에 저장 (TTL: 3일)
        # TEMPORARILY DISABLED - Causing dict serialization issues
        # try:
        #     from dataclasses import asdict
        #     self.cache.set(
        #         "ai_analysis",
        #         cache_key,
        #         asdict(result),
        #         metadata={"source": source, "meds_count": len(current_meds or [])}
        #     )
        #     print(f"[Cache SAVED] AI analysis result cached")
        # except Exception as e:
        #     print(f"[Cache ERROR] Failed to cache AI analysis: {e}")
        
        return result
    
    def _search_exact_symptom(self, symptom_text: str) -> Optional[dict]:
        """disease_master에서 정확 매칭 검색 (식재료 매핑이 있는 증상 우선)"""
        try:
            # modern_name_ko 또는 disease_read로 검색
            result = self.db.table("disease_master").select("*").or_(
                f"modern_name_ko.ilike.%{symptom_text}%,"
                f"disease_read.ilike.%{symptom_text}%,"
                f"name_en.ilike.%{symptom_text}%"
            ).limit(10).execute()
            
            if not result.data:
                return None
            
            # 여러 결과가 있으면 symptom_ingredient_map에 매핑이 있는 것 우선
            for row in result.data:
                map_check = self.db.table("symptom_ingredient_map").select(
                    "id"
                ).eq("symptom_id", row["id"]).limit(1).execute()
                
                if map_check.data:
                    return row
            
            # 매핑이 없으면 첫 번째 결과 반환
            return result.data[0]
        except Exception as e:
            print(f"정확 매칭 검색 오류: {e}")
            return None
    
    def _search_similar_symptom(self, symptom_text: str) -> Optional[dict]:
        """aliases 배열 또는 부분 매칭으로 유사 증상 검색 (식재료 매핑 있는 것 우선)"""
        try:
            keywords = self._extract_keywords(symptom_text)
            
            for keyword in keywords:
                # disease_read 필드도 검색에 추가
                result = self.db.table("disease_master").select("*").or_(
                    f"modern_name_ko.ilike.%{keyword}%,"
                    f"disease_read.ilike.%{keyword}%,"
                    f"disease_alias_read.ilike.%{keyword}%,"
                    f"category.ilike.%{keyword}%"
                ).limit(10).execute()
                
                if not result.data:
                    continue
                
                # 여러 결과가 있으면 symptom_ingredient_map에 매핑이 있는 것 우선
                for row in result.data:
                    map_check = self.db.table("symptom_ingredient_map").select(
                        "id"
                    ).eq("symptom_id", row["id"]).limit(1).execute()
                    
                    if map_check.data:
                        return row
                
                # 매핑이 없으면 첫 번째 결과 반환
                return result.data[0]
            
            return None
        except Exception as e:
            print(f"유사 검색 오류: {e}")
            return None
    
    def _extract_keywords(self, text: str) -> list[str]:
        """텍스트에서 핵심 키워드 추출"""
        # 간단한 키워드 추출 (나중에 NLP로 개선 가능)
        keywords = []
        
        # 흔한 증상 키워드 매핑 (사용자 입력 → DB 검색 키워드)
        symptom_keywords = {
            "불면": ["수면", "잠", "불면", "못 자", "안 자", "깨"],
            "소화": ["소화", "위장", "더부룩", "체한", "소화불량", "속쓰림", "역류"],
            "피로": ["피로", "지침", "기력", "힘이 없"],
            "두통": ["두통", "머리", "편두통"],
            "냉증": ["냉증", "손발", "차가", "냉한"],
            "혈압": ["혈압", "고혈압", "저혈압"],
            "당뇨": ["당뇨", "혈당"],
            "호흡": ["호흡", "기침", "가래", "숨", "감기", "몸살", "비염"],
            "변비": ["변비", "배변", "대변"],
        }
        
        mapped_keywords = []
        for db_keyword, input_patterns in symptom_keywords.items():
            for pattern in input_patterns:
                if pattern in text:
                    mapped_keywords.append(db_keyword)
                    break
        
        # 원본 텍스트 단어도 추가
        words = text.replace("이", "").replace("가", "").replace("요", "").split()
        other_keywords = [w for w in words if len(w) >= 2 and w not in mapped_keywords]
        
        # 중요 키워드 우선 검색
        return list(dict.fromkeys(mapped_keywords + other_keywords))
    
    def _get_ingredients_from_db(self, symptom_id: int) -> list[Ingredient]:
        """symptom_ingredient_map에서 추천 식재료 조회"""
        try:
            # 1. symptom_ingredient_map에서 식재료 매핑 조회
            result = self.db.table("symptom_ingredient_map").select(
                "rep_code, direction, rationale_ko, priority, evidence_level"
            ).eq("symptom_id", symptom_id).order(
                "priority", desc=True
            ).limit(3).execute()
            
            if not result.data:
                return []
            
            # 2. rep_code들로 foods_master에서 이름 조회
            rep_codes = [row["rep_code"] for row in result.data]
            foods_result = self.db.table("foods_master").select(
                "rep_code, modern_name"
            ).in_("rep_code", rep_codes).execute()
            
            # rep_code -> modern_name 매핑
            food_names = {f["rep_code"]: f["modern_name"] for f in foods_result.data}
            
            ingredients = []
            for row in result.data:
                rep_code = row.get("rep_code", "")
                ingredients.append(Ingredient(
                    rep_code=rep_code,
                    modern_name=food_names.get(rep_code, rep_code),
                    rationale_ko=row.get("rationale_ko", ""),
                    direction=row.get("direction", "recommend"),
                    priority=row.get("priority", 100),
                    evidence_level=row.get("evidence_level", "traditional")
                ))
            
            return ingredients
        except Exception as e:
            print(f"식재료 조회 오류: {e}")
            return []
    
    def _get_recipes_from_db(self, symptom_id: int) -> list[Recipe]:
        """symptom_recipe_map에서 추천 레시피 조회"""
        try:
            # 1. 매핑 조회
            result = self.db.table("symptom_recipe_map").select(
                "recipe_id, meal_slot, priority, rationale_ko"
            ).eq("symptom_id", symptom_id).order(
                "priority", desc=True
            ).limit(3).execute()
            
            if not result.data:
                return []
            
            # 2. recipe_id로 recipes 테이블 조회
            recipe_ids = [row["recipe_id"] for row in result.data]
            recipes_result = self.db.table("recipes").select(
                "id, title, description, tags"
            ).in_("id", recipe_ids).execute()
            
            # id -> recipe info 매핑
            recipe_map = {r["id"]: r for r in recipes_result.data}
            
            recipes = []
            for row in result.data:
                r_id = row["recipe_id"]
                r_info = recipe_map.get(r_id, {})
                
                recipes.append(Recipe(
                    id=r_id,
                    title=r_info.get("title", f"Recipe {r_id}"),
                    description=r_info.get("description", ""),
                    tags=r_info.get("tags", []),
                    meal_slot=row.get("meal_slot", "anytime"),
                    priority=row.get("priority", 50),
                    rationale_ko=row.get("rationale_ko", "")
                ))
            
            return recipes
        except Exception as e:
            print(f"레시피 조회 오류: {e}")
            return []
    
    def get_cautions_for_drugs(self, drug_names: list[str]) -> list[str]:
        """약 이름으로 주의사항 조회"""
        cautions = []
        try:
            for drug_name in drug_names:
                result = self.db.table("interaction_facts").select(
                    "summary_ko, action_ko, severity"
                ).or_(
                    f"a_ref.ilike.%{drug_name}%,"
                    f"b_ref.ilike.%{drug_name}%"
                ).limit(3).execute()
                
                for row in result.data:
                    if row.get("summary_ko"):
                        cautions.append(row["summary_ko"])
        except Exception as e:
            print(f"주의사항 조회 오류: {e}")
        
        return cautions


# 동기 래퍼 함수 (테스트용)
def analyze_symptom_sync(symptom_text: str, current_meds: list[str] = None) -> dict:
    """동기 버전 분석 함수"""
    import asyncio
    service = AnalyzeService()
    
    # 이벤트 루프가 없으면 새로 생성
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(service.analyze_symptom(symptom_text, current_meds))
    
    return {
        "symptom_summary": result.symptom_summary,
        "ingredients": [
            {
                "rep_code": ing.rep_code,
                "modern_name": ing.modern_name,
                "rationale_ko": ing.rationale_ko,
                "direction": ing.direction,
                "priority": ing.priority,
                "evidence_level": ing.evidence_level
            }
            for ing in result.ingredients
        ],
        "confidence_level": result.confidence_level,
        "source": result.source,
        "matched_symptom_id": result.matched_symptom_id,
        "matched_symptom_name": result.matched_symptom_name
    }


if __name__ == "__main__":
    # 테스트
    test_symptoms = [
        "속이 더부룩해요",
        "잠을 잘 못 자요",
        "손발이 차요"
    ]
    
    for symptom in test_symptoms:
        print(f"\n{'='*50}")
        print(f"증상: {symptom}")
        print("="*50)
        result = analyze_symptom_sync(symptom)
        print(f"요약: {result['symptom_summary']}")
        print(f"신뢰도: {result['confidence_level']} ({result['source']})")
        print(f"추천 식재료: {len(result['ingredients'])}개")
        for ing in result['ingredients']:
            print(f"  - {ing['modern_name']}: {ing['rationale_ko'][:30]}...")
