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
from typing import Optional

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
        foods = []
        if analysis_result:
            for ing in analysis_result.ingredients:
                if ing.direction in ("recommend", "good", "neutral"):
                    foods.append({
                        "name":       ing.modern_name,
                        "reason":     ing.rationale_ko,
                        "precaution": "과다 섭취는 피하고 의사와 상담 후 섭취하세요."
                                      if ing.direction == "neutral" else "",
                    })
                elif ing.direction in ("caution", "avoid"):
                    foods.append({
                        "name":       ing.modern_name,
                        "reason":     ing.rationale_ko,
                        "precaution": f"⚠️ 복용 중 주의 필요: {ing.rationale_ko}",
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
        """Gemini Vision으로 처방전에서 약물 목록 추출"""
        try:
            api_key = os.getenv("API_KEY")
            if not api_key:
                raise ValueError("API_KEY 환경변수가 설정되지 않았습니다.")

            client = genai.Client(api_key=api_key)
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")

            prompt = """이 처방전 이미지를 분석해서 아래 JSON만 반환해줘 (마크다운 없이):
{
  "drugList": ["약물명1", "약물명2"],
  "warnings": "중복 성분이나 상호작용 주의사항. 없으면 빈 문자열.",
  "hospitalName": "병원명 또는 미상"
}
약물명은 처방전에 표기된 한글 약품명(용량/횟수 제외)으로 추출해줘."""

            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=[{
                    "parts": [
                        {"inline_data": {"data": image_b64, "mime_type": mime_type}},
                        {"text": prompt},
                    ]
                }]
            )

            text = response.text.strip()
            if text.startswith("```"):
                parts = text.split("```")
                text = parts[1] if len(parts) > 1 else text
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            if "{" in text and "}" in text:
                text = text[text.find("{"):text.rfind("}") + 1]

            return json.loads(text)

        except Exception as e:
            print(f"[PrescriptionService] 이미지 분석 실패: {e}")
            return {"drugList": [], "warnings": "처방전 이미지 분석에 실패했습니다. 다시 시도해주세요."}

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

    def _build_lifestyle_advice(self, analysis_result, drug_list: list) -> str:
        """분석 결과 기반 생활 가이드 생성"""
        if not analysis_result:
            return "규칙적인 식습관과 충분한 수분 섭취를 권장드립니다. 복약 중 이상 증상 발생 시 즉시 담당 의사 또는 약사와 상담하세요."
        parts = []
        if analysis_result.recipes:
            titles = [r.title for r in analysis_result.recipes[:2]]
            parts.append(f"추천 식단: {', '.join(titles)}")
        if analysis_result.cautions:
            parts.append("약물-식품 상호작용에 주의하세요.")
        if not parts:
            parts.append("규칙적인 식습관과 충분한 수분 섭취를 권장드립니다.")
        parts.append("복용 중 이상 증상 발생 시 즉시 담당 의사 또는 약사와 상담하세요.")
        return " ".join(parts)
