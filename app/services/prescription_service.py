"""
처방전 분석 통합 서비스
이미지 → Gemini Vision OCR → MFDS(식약처) + PubMed 보강 → DUR 병용금기 → 동의보감 매핑 → 완성 리포트

근거 레이어:
  Level A : 식약처 e약은요 (MfdsService)  — 효능, 부작용, 주의사항
  Level A : DUR 병용금기 API (DurService) — 약물-약물 상호작용
  Level A : PubMed (MedicationService)   — 임상 논문 근거
  Fallback: Gemini AI                    — 위 데이터 없을 때
"""
import os
import json
import base64
import asyncio
from typing import Optional, AsyncGenerator

from .medication_service import MedicationService
from .analyze_service import AnalyzeService
from .dur_service import DurService
from .mfds_service import MfdsService, DrugLabel
from .sim_pre_service import SimPreService
from .tavily_service import TavilyService

try:
    from google import genai
except ImportError:
    import google.generativeai as genai


class PrescriptionService:
    """처방전 이미지 분석 통합 서비스"""

    def __init__(self):
        self.medication_service = MedicationService()   # PubMed RAG
        self.analyze_service = AnalyzeService()          # 동의보감/TKM
        self.dur_service = DurService()                  # DUR 병용금기
        self.mfds_service = MfdsService()                # 식약처 라벨 (Level A)
        self.sim_pre_service = SimPreService()           # 한국전통지식포털 유사처방 (Level TKM)
        self.tavily_service = TavilyService()            # 웹 검색 fallback (Level C)

    async def analyze_prescription_image(self, image_bytes: bytes, mime_type: str) -> dict:
        """Main entry point - with detailed error logging"""
        import traceback
        try:
            return await self._analyze_prescription_image_impl(image_bytes, mime_type)
        except Exception as e:
            import os
            error_file = os.path.join(os.getcwd(), "prescription_error.txt")
            with open(error_file, "w", encoding="utf-8") as f:
                f.write(f"CWD: {os.getcwd()}\n")
                f.write(f"Error in analyze_prescription_image: {e}\n")
                f.write(f"Error type: {type(e)}\n\n")
                traceback.print_exc(file=f)
            print(f"[ERROR] Wrote error to {error_file}", flush=True)
            raise

    async def _analyze_prescription_image_impl(self, image_bytes: bytes, mime_type: str) -> dict:
        import sys
        print("[TRACE] === Starting _analyze_prescription_image_impl ===", file=sys.stderr, flush=True)
        """
        처방전 이미지를 분석하여 5-섹션 리포트를 반환합니다.

        1. Gemini Vision  → 약물 목록 OCR
        2. DUR API        → 병용금기 경고
        3. MFDS (식약처)  → 약물별 효능/부작용 (Level A)
        4. PubMed RAG     → 임상 논문 근거 (MFDS 없을 때 fallback)
        5. AnalyzeService → 동의보감/식재료 매핑
        6. 결과 조합 반환
        """
        # ── Step 1: Gemini Vision OCR ──────────────────────────────
        ocr_result = await self._extract_drugs_from_image(image_bytes, mime_type)
        drug_list = ocr_result.get("drugList", [])
        warnings = ocr_result.get("warnings", "")

        # ── Step 2: DUR 병용금기 (약물 2개 이상) ───────────────────
        if len(drug_list) >= 2:
            try:
                dur_interactions = await self.dur_service.check_interactions(drug_list)
                if dur_interactions:
                    dur_warnings = self.dur_service.format_warnings(dur_interactions)
                    sep = " | " if warnings else ""
                    warnings = warnings + sep + " | ".join(dur_warnings)
            except Exception as e:
                print(f"[PrescriptionService] DUR 조회 오류: {e}")

        # ── Step 3: 식약처 라벨 + PubMed 병렬 조회 ────────────────
        # Fallback chain: Level A (MFDS) → Level B (PubMed) → Level C (Tavily)
        drug_details = []
        all_papers = []
        mfds_hit_count = 0
        tavily_results: dict = {}

        if drug_list:
            targets = drug_list[:3]

            # 식약처 & PubMed 동시 조회
            mfds_task = self.mfds_service.get_drug_labels_bulk(targets)
            pubmed_tasks = [
                self.medication_service.get_drug_info(drug) for drug in targets
            ]
            mfds_labels, *pubmed_results_raw = await asyncio.gather(
                mfds_task, *pubmed_tasks, return_exceptions=True
            )

            # gather 예외 처리 — mfds_labels 가 Exception이면 빈 dict
            if isinstance(mfds_labels, Exception):
                print(f"[PrescriptionService] MFDS bulk 오류: {mfds_labels}")
                mfds_labels = {}

            # MFDS/PubMed 둘 다 없는 약물만 Tavily로 보완
            tavily_needed = []
            for drug, pubmed_raw in zip(targets, pubmed_results_raw):
                label: Optional[DrugLabel] = mfds_labels.get(drug)
                has_pubmed = (
                    not isinstance(pubmed_raw, Exception)
                    and bool(pubmed_raw.get("info") or pubmed_raw.get("papers"))
                )
                if not label and not has_pubmed:
                    tavily_needed.append(drug)

            tavily_results: dict = {}
            if tavily_needed:
                try:
                    tavily_results = await self.tavily_service.search_bulk(tavily_needed)
                except Exception as e:
                    print(f"[PrescriptionService] Tavily bulk 오류: {e}")

            for drug, pubmed_raw in zip(targets, pubmed_results_raw):
                label: Optional[DrugLabel] = mfds_labels.get(drug)

                if label:
                    # ── Level A: 식약처 데이터 ──────────────────
                    mfds_hit_count += 1
                    detail = self.mfds_service.to_drug_detail(label)
                    drug_details.append({
                        "name":        detail["name"],
                        "efficacy":    detail["efficacy"],
                        "sideEffects": detail["sideEffects"],
                    })
                    # PubMed 논문은 academicEvidence 용으로만 수집
                    if not isinstance(pubmed_raw, Exception):
                        all_papers.extend(pubmed_raw.get("papers", []))

                elif not isinstance(pubmed_raw, Exception) and (
                    pubmed_raw.get("info") or pubmed_raw.get("papers")
                ):
                    # ── Level B: PubMed fallback ─────────────────
                    info_text = pubmed_raw.get("info", "")
                    papers = pubmed_raw.get("papers", [])
                    all_papers.extend(papers)
                    drug_details.append({
                        "name":        drug,
                        "efficacy":    self._extract_section(info_text, "효능"),
                        "sideEffects": self._extract_section(info_text, "주의"),
                    })

                elif drug in tavily_results and tavily_results[drug]:
                    # ── Level C: Tavily 웹 검색 fallback ─────────
                    web_info = tavily_results[drug]
                    detail = TavilyService.to_drug_detail(web_info)
                    all_papers.extend(TavilyService.to_papers(web_info))
                    drug_details.append({
                        "name":        detail["name"],
                        "efficacy":    detail["efficacy"],
                        "sideEffects": detail["sideEffects"],
                    })
                    print(f"[PrescriptionService] Tavily 보완: {drug}")

                else:
                    # ── 모든 소스 실패 ────────────────────────────
                    drug_details.append({
                        "name":        drug,
                        "efficacy":    "정보를 가져오지 못했습니다.",
                        "sideEffects": "",
                    })

        # ── Step 4: 동의보감/TKM 분석 + 유사처방 조회 (병렬) ────────
        symptom_text = (
            f"복용 약물: {', '.join(drug_list)}" if drug_list
            else warnings or "처방 분석"
        )
        analysis_result, sim_pre_result = await asyncio.gather(
            self.analyze_service.analyze_symptom(symptom_text, current_meds=drug_list),
            self.sim_pre_service.search_by_drugs(drug_list, num_rows=3),
            return_exceptions=True,
        )
        if isinstance(analysis_result, Exception):
            print(f"[PrescriptionService] AnalyzeService 오류: {analysis_result}")
            analysis_result = None
        if isinstance(sim_pre_result, Exception):
            print(f"[PrescriptionService] SimPreService 오류: {sim_pre_result}")
            sim_pre_result = None

        # ── Step 5: 학술 근거 요약 ────────────────────────────────
        # 신뢰도: A(식약처) → B(PubMed) → C(Tavily 웹) → C(AI)
        symptom_summary = analysis_result.symptom_summary if analysis_result else ""
        if mfds_hit_count > 0:
            trust_level = "A"
        elif all_papers:
            trust_level = "B"
        elif tavily_results:
            trust_level = "C"
        else:
            trust_level = (
                {"database": "A", "similarity": "B", "cache_similarity": "B"}
                .get(analysis_result.source if analysis_result else "", "C")
            )

        paper_titles = [p.get("title", "") for p in all_papers[:3] if p.get("title")]
        if paper_titles and mfds_hit_count > 0:
            academic_summary = (
                f"식약처 공인 정보 + PubMed 논문 {len(paper_titles)}편 분석 결과: "
                f"{symptom_summary}"
            )
        elif paper_titles:
            academic_summary = (
                f"관련 PubMed 논문 {len(paper_titles)}편 분석 결과: "
                f"{symptom_summary}"
            )
        else:
            academic_summary = symptom_summary

        # ── Step 6: 동의보감 식재료 ────────────────────────────────
        import sys
        print(f"[TRACE] Step 6: Processing ingredients. analysis_result type: {type(analysis_result)}", file=sys.stderr, flush=True)
        if analysis_result:
            print(f"[TRACE] Number of ingredients: {len(analysis_result.ingredients)}", file=sys.stderr, flush=True)
            if analysis_result.ingredients:
                print(f"[TRACE] First ingredient type: {type(analysis_result.ingredients[0])}", file=sys.stderr, flush=True)

        foods = []
        if analysis_result:
            for ing in analysis_result.ingredients:
                # Handle both dict and Ingredient object
                if isinstance(ing, dict):
                    direction = ing.get("direction", "recommend")
                    modern_name = ing.get("modern_name", "")
                    rationale_ko = ing.get("rationale_ko", "")
                else:
                    direction = ing.direction
                    modern_name = ing.modern_name
                    rationale_ko = ing.rationale_ko

                if direction in ("recommend", "good", "neutral"):
                    foods.append({
                        "name":       modern_name,
                        "reason":     rationale_ko,
                        "precaution": "과다 섭취는 피하고 의사와 상담 후 섭취하세요."
                                      if direction == "neutral" else "",
                    })
                elif direction in ("caution", "avoid"):
                    foods.append({
                        "name":       modern_name,
                        "reason":     rationale_ko,
                        "precaution": f"⚠️ 복용 중 주의 필요: {rationale_ko}",
                    })

        matched_name = analysis_result.matched_symptom_name if analysis_result else None
        dongui_section = (
            f"{matched_name} 관련 동의보감 처방"
            if matched_name
            else "처방약 기반 동의보감 권장 식재료"
        )

        lifestyle_advice = self._build_lifestyle_advice(analysis_result, drug_list)
        symptom_tokens = [
            t for t in (matched_name or "").split()
            if len(t) >= 2
        ]

        default_warning = (
            f"복용 약물 {len(drug_list)}종 분석 완료. "
            "복약 중 이상 증상 시 의사·약사와 상담하세요."
            if drug_list else "처방전 분석이 완료되었습니다."
        )

        # ── Step 7: 유사처방 (SimPre) 데이터 조합 ─────────────────
        sim_pre_section = (
            self.sim_pre_service.to_donguibogam_section(sim_pre_result)
            if sim_pre_result else {"traditionalPrescriptions": [], "tkmPapers": []}
        )

        return {
            "prescriptionSummary": {
                "drugList": drug_list,
                "warnings": warnings or default_warning,
            },
            "drugDetails": drug_details,
            "academicEvidence": {
                "summary":    academic_summary,
                "trustLevel": trust_level,
                "papers": [
                    {"title": p.get("title", ""), "url": p.get("url", "")}
                    for p in all_papers[:3]
                ],
            },
            "lifestyleGuide": {
                "symptomTokens": symptom_tokens,
                "advice":        lifestyle_advice,
            },
            "donguibogam": {
                "foods":                    foods[:5],
                "donguiSection":            dongui_section,
                "traditionalPrescriptions": sim_pre_section["traditionalPrescriptions"],
                "tkmPapers":                sim_pre_section["tkmPapers"],
            },
        }

    # ──────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────

    async def _extract_drugs_from_image(self, image_bytes: bytes, mime_type: str) -> dict:
        """OpenAI GPT-4o Vision으로 처방전에서 약물 목록 추출"""
        try:
            import openai
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

            client = openai.AsyncOpenAI(api_key=openai_key)
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")

            prompt = """이 처방전 이미지를 분석해서 아래 JSON 형식으로만 반환해줘:
{
  "drugList": ["약물명1", "약물명2"],
  "warnings": "중복 성분이나 상호작용 주의사항. 없으면 빈 문자열.",
  "hospitalName": "병원명 또는 미상"
}

규칙:
- 약물명은 처방전에 표기된 한글 약품명만 추출 (용량/횟수 제외)
- JSON 형식으로만 응답 (마크다운, 설명 없이)"""

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=500
            )

            text = response.choices[0].message.content.strip()
            return json.loads(text)

        except Exception as e:
            print(f"[PrescriptionService] 이미지 분석 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"drugList": [], "warnings": f"처방전 이미지 분석에 실패했습니다: {str(e)}"}

    def _extract_section(self, text: str, keyword: str) -> str:
        """PubMed RAG 텍스트에서 효능/주의사항 섹션 추출"""
        if not text:
            return ""
        lines = text.split("\n")
        result = []
        capturing = False
        stop_keywords = {"효능", "주의", "팁", "🟢", "⚠️", "💡"}

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if keyword in line or any(
                kw in line for kw in [f"🟢 {keyword}", f"⚠️ {keyword}", f"💡 {keyword}"]
            ):
                capturing = True
                if ":" in line:
                    content = line.split(":", 1)[-1].strip()
                    if content:
                        result.append(content)
            elif capturing:
                if any(kw in line for kw in stop_keywords) and keyword not in line:
                    break
                result.append(line)

        return " ".join(result) if result else text[:120]

    async def fetch_optional_sections(self, drug_list: list, sections: set) -> dict:
        """
        결과 화면에서 사용자가 개별 선택한 섹션(4·5)을 on-demand로 분석.
        - Section 3 (학술근거): 프론트에서 기존 academicEvidence 데이터를 즉시 표시 → 이 메서드 불필요
        - Section 4 (생활가이드): AnalyzeService 필요
        - Section 5 (동의보감): AnalyzeService + SimPreService 필요
        """
        result = {}
        analysis_result = None
        sim_pre_result = None

        if sections & {"4", "5"}:
            symptom_text = (
                f"복용 약물: {', '.join(drug_list)}" if drug_list
                else "처방 분석"
            )
            tasks: list = [
                self.analyze_service.analyze_symptom(symptom_text, current_meds=drug_list)
            ]
            include_sim_pre = "5" in sections
            if include_sim_pre:
                tasks.append(self.sim_pre_service.search_by_drugs(drug_list, num_rows=3))

            gathered = await asyncio.gather(*tasks, return_exceptions=True)
            analysis_result = gathered[0] if not isinstance(gathered[0], Exception) else None
            if include_sim_pre and len(gathered) > 1:
                sim_pre_result = gathered[1] if not isinstance(gathered[1], Exception) else None

        if "4" in sections:
            matched_name = analysis_result.matched_symptom_name if analysis_result else None
            symptom_tokens = [t for t in (matched_name or "").split() if len(t) >= 2]
            lifestyle_advice = self._build_lifestyle_advice(analysis_result, drug_list)
            result["lifestyleGuide"] = {
                "symptomTokens": symptom_tokens,
                "advice": lifestyle_advice,
            }

        if "5" in sections:
            foods = []
            if analysis_result:
                for ing in analysis_result.ingredients:
                    if isinstance(ing, dict):
                        direction = ing.get("direction", "recommend")
                        modern_name = ing.get("modern_name", "")
                        rationale_ko = ing.get("rationale_ko", "")
                    else:
                        direction = ing.direction
                        modern_name = ing.modern_name
                        rationale_ko = ing.rationale_ko
                    if direction in ("recommend", "good", "neutral"):
                        foods.append({
                            "name": modern_name,
                            "reason": rationale_ko,
                            "precaution": "과다 섭취는 피하고 의사와 상담 후 섭취하세요." if direction == "neutral" else "",
                        })
                    elif direction in ("caution", "avoid"):
                        foods.append({
                            "name": modern_name,
                            "reason": rationale_ko,
                            "precaution": f"⚠️ 복용 중 주의 필요: {rationale_ko}",
                        })

            matched_name = analysis_result.matched_symptom_name if analysis_result else None
            dongui_section = (
                f"{matched_name} 관련 동의보감 처방" if matched_name
                else "처방약 기반 동의보감 권장 식재료"
            )
            sim_pre_section = (
                self.sim_pre_service.to_donguibogam_section(sim_pre_result)
                if sim_pre_result else {"traditionalPrescriptions": [], "tkmPapers": []}
            )
            result["donguibogam"] = {
                "foods": foods[:5],
                "donguiSection": dongui_section,
                "traditionalPrescriptions": sim_pre_section["traditionalPrescriptions"],
                "tkmPapers": sim_pre_section["tkmPapers"],
            }

        return result

    async def analyze_prescription_streaming(
        self,
        image_bytes: bytes,
        mime_type: str,
        sections: set,
    ) -> AsyncGenerator[dict, None]:
        """
        SSE 스트리밍용 처방전 분석 generator.
        sections: {"1","2"} → AnalyzeService 스킵 (빠름)
                  {"1","2","3","4","5"} → 전체 실행
        각 단계마다 {"type":"progress",...} yield, 마지막에 {"type":"result","data":{...}} yield.
        """
        import sys

        # ── Step 1: OCR ────────────────────────────────────────────
        yield {"type": "progress", "step": 1, "message": "처방전 OCR 분석 중...", "progress": 15}
        ocr_result = await self._extract_drugs_from_image(image_bytes, mime_type)
        drug_list = ocr_result.get("drugList", [])
        warnings = ocr_result.get("warnings", "")

        # ── Step 2: DUR ─────────────────────────────────────────────
        yield {"type": "progress", "step": 2, "message": "병용금기 확인 중...", "progress": 35}
        if len(drug_list) >= 2:
            try:
                dur_interactions = await self.dur_service.check_interactions(drug_list)
                if dur_interactions:
                    dur_warnings = self.dur_service.format_warnings(dur_interactions)
                    sep = " | " if warnings else ""
                    warnings = warnings + sep + " | ".join(dur_warnings)
            except Exception as e:
                print(f"[PrescriptionService] DUR 조회 오류: {e}")

        # ── Step 3: MFDS + PubMed 병렬 (항상 실행) ─────────────────
        yield {"type": "progress", "step": 3, "message": "약물 정보 조회 중 (식약처·PubMed)...", "progress": 60}
        drug_details = []
        all_papers = []
        mfds_hit_count = 0
        tavily_results: dict = {}

        if drug_list:
            targets = drug_list[:3]
            mfds_task = self.mfds_service.get_drug_labels_bulk(targets)
            pubmed_tasks = [self.medication_service.get_drug_info(drug) for drug in targets]
            mfds_labels, *pubmed_results_raw = await asyncio.gather(
                mfds_task, *pubmed_tasks, return_exceptions=True
            )
            if isinstance(mfds_labels, Exception):
                print(f"[PrescriptionService/stream] MFDS bulk 오류: {mfds_labels}")
                mfds_labels = {}

            tavily_needed = []
            for drug, pubmed_raw in zip(targets, pubmed_results_raw):
                label: Optional[DrugLabel] = mfds_labels.get(drug)
                has_pubmed = (
                    not isinstance(pubmed_raw, Exception)
                    and bool(pubmed_raw.get("info") or pubmed_raw.get("papers"))
                )
                if not label and not has_pubmed:
                    tavily_needed.append(drug)

            if tavily_needed:
                try:
                    tavily_results = await self.tavily_service.search_bulk(tavily_needed)
                except Exception as e:
                    print(f"[PrescriptionService/stream] Tavily bulk 오류: {e}")

            for drug, pubmed_raw in zip(targets, pubmed_results_raw):
                label: Optional[DrugLabel] = mfds_labels.get(drug)
                if label:
                    mfds_hit_count += 1
                    detail = self.mfds_service.to_drug_detail(label)
                    drug_details.append({
                        "name": detail["name"],
                        "efficacy": detail["efficacy"],
                        "sideEffects": detail["sideEffects"],
                    })
                    if not isinstance(pubmed_raw, Exception):
                        all_papers.extend(pubmed_raw.get("papers", []))
                elif not isinstance(pubmed_raw, Exception) and (
                    pubmed_raw.get("info") or pubmed_raw.get("papers")
                ):
                    info_text = pubmed_raw.get("info", "")
                    papers = pubmed_raw.get("papers", [])
                    all_papers.extend(papers)
                    drug_details.append({
                        "name": drug,
                        "efficacy": self._extract_section(info_text, "효능"),
                        "sideEffects": self._extract_section(info_text, "주의"),
                    })
                elif drug in tavily_results and tavily_results[drug]:
                    web_info = tavily_results[drug]
                    detail = TavilyService.to_drug_detail(web_info)
                    all_papers.extend(TavilyService.to_papers(web_info))
                    drug_details.append({
                        "name": detail["name"],
                        "efficacy": detail["efficacy"],
                        "sideEffects": detail["sideEffects"],
                    })
                else:
                    drug_details.append({
                        "name": drug,
                        "efficacy": "정보를 가져오지 못했습니다.",
                        "sideEffects": "",
                    })

        # ── Step 4: 동의보감·생활가이드 (항상 실행) ──────────────────
        # Section 3 데이터(academic_summary)와 donguibogam.foods가 초기 응답에 포함되어야 함
        yield {"type": "progress", "step": 4, "message": "동의보감·생활가이드 분석 중...", "progress": 85}
        symptom_text = (
            f"복용 약물: {', '.join(drug_list)}" if drug_list
            else warnings or "처방 분석"
        )
        analysis_result, sim_pre_result = await asyncio.gather(
            self.analyze_service.analyze_symptom(symptom_text, current_meds=drug_list),
            self.sim_pre_service.search_by_drugs(drug_list, num_rows=3),
            return_exceptions=True,
        )
        if isinstance(analysis_result, Exception):
            print(f"[PrescriptionService/stream] AnalyzeService 오류: {analysis_result}")
            analysis_result = None
        if isinstance(sim_pre_result, Exception):
            print(f"[PrescriptionService/stream] SimPreService 오류: {sim_pre_result}")
            sim_pre_result = None

        # ── 결과 조합 ───────────────────────────────────────────────
        symptom_summary = analysis_result.symptom_summary if analysis_result else ""
        if mfds_hit_count > 0:
            trust_level = "A"
        elif all_papers:
            trust_level = "B"
        elif tavily_results:
            trust_level = "C"
        else:
            trust_level = (
                {"database": "A", "similarity": "B", "cache_similarity": "B"}
                .get(analysis_result.source if analysis_result else "", "C")
            )

        paper_titles = [p.get("title", "") for p in all_papers[:3] if p.get("title")]
        if paper_titles and mfds_hit_count > 0:
            academic_summary = (
                f"식약처 공인 정보 + PubMed 논문 {len(paper_titles)}편 분석 결과: {symptom_summary}"
            )
        elif paper_titles:
            academic_summary = (
                f"관련 PubMed 논문 {len(paper_titles)}편 분석 결과: {symptom_summary}"
            )
        else:
            academic_summary = symptom_summary or "약물 정보를 분석하였습니다."

        foods = []
        if analysis_result:
            for ing in analysis_result.ingredients:
                if isinstance(ing, dict):
                    direction = ing.get("direction", "recommend")
                    modern_name = ing.get("modern_name", "")
                    rationale_ko = ing.get("rationale_ko", "")
                else:
                    direction = ing.direction
                    modern_name = ing.modern_name
                    rationale_ko = ing.rationale_ko
                if direction in ("recommend", "good", "neutral"):
                    foods.append({
                        "name": modern_name,
                        "reason": rationale_ko,
                        "precaution": "과다 섭취는 피하고 의사와 상담 후 섭취하세요." if direction == "neutral" else "",
                    })
                elif direction in ("caution", "avoid"):
                    foods.append({
                        "name": modern_name,
                        "reason": rationale_ko,
                        "precaution": f"⚠️ 복용 중 주의 필요: {rationale_ko}",
                    })

        matched_name = analysis_result.matched_symptom_name if analysis_result else None
        dongui_section = (
            f"{matched_name} 관련 동의보감 처방" if matched_name
            else "처방약 기반 동의보감 권장 식재료"
        )
        lifestyle_advice = self._build_lifestyle_advice(analysis_result, drug_list)
        symptom_tokens = [t for t in (matched_name or "").split() if len(t) >= 2]
        default_warning = (
            f"복용 약물 {len(drug_list)}종 분석 완료. "
            "복약 중 이상 증상 시 의사·약사와 상담하세요."
            if drug_list else "처방전 분석이 완료되었습니다."
        )
        sim_pre_section = (
            self.sim_pre_service.to_donguibogam_section(sim_pre_result)
            if sim_pre_result else {"traditionalPrescriptions": [], "tkmPapers": []}
        )

        yield {
            "type": "result",
            "data": {
                "prescriptionSummary": {
                    "drugList": drug_list,
                    "warnings": warnings or default_warning,
                },
                "drugDetails": drug_details,
                "academicEvidence": {
                    "summary": academic_summary,
                    "trustLevel": trust_level,
                    "papers": [
                        {"title": p.get("title", ""), "url": p.get("url", "")}
                        for p in all_papers[:3]
                    ],
                },
                "lifestyleGuide": {
                    "symptomTokens": symptom_tokens,
                    "advice": lifestyle_advice,
                },
                "donguibogam": {
                    "foods": foods[:5],
                    "donguiSection": dongui_section,
                    "traditionalPrescriptions": sim_pre_section["traditionalPrescriptions"],
                    "tkmPapers": sim_pre_section["tkmPapers"],
                },
            },
        }

    def _build_lifestyle_advice(self, analysis_result, drug_list: list) -> str:
        """분석 결과 기반 생활 가이드 생성"""
        if not analysis_result:
            return "규칙적인 식습관과 충분한 수분 섭취를 권장드립니다. 복약 중 이상 증상 발생 시 즉시 담당 의사 또는 약사와 상담하세요."
        parts = []
        if analysis_result.recipes:
            # Handle both dict and Recipe object
            titles = []
            for r in analysis_result.recipes[:2]:
                if isinstance(r, dict):
                    titles.append(r.get("title", ""))
                else:
                    titles.append(r.title)
            if titles:
                parts.append(f"추천 식단: {', '.join(titles)}")
        if analysis_result.cautions:
            parts.append("약물-식품 상호작용에 주의하세요.")
        if not parts:
            parts.append("규칙적인 식습관과 충분한 수분 섭취를 권장드립니다.")
        parts.append("복용 중 이상 증상 발생 시 즉시 담당 의사 또는 약사와 상담하세요.")
        return " ".join(parts)
