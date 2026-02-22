from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import List
import json
from app.schemas.analysis import (
    Step1ExtractRequest, Step1ExtractResponse,
    Step2SearchRequest, Step2SearchResponse,
    Step3ReportRequest, Step3ReportResponse,
    PrescriptionAnalysisResponse,
    PillSearchByNameRequest, PillSearchByAppearanceRequest, PillSearchResponse
)
from app.services.analysis_step_service import StepByStepAnalysisService
from app.services.prescription_service import PrescriptionService
from app.services.pill_id_service import PillIdService
from app.services.faq_service import FAQService
from app.services.naver_search_service import NaverSearchService

router = APIRouter()

# Dependency Injection for Services
def get_analysis_service():
    return StepByStepAnalysisService()

def get_prescription_service():
    return PrescriptionService()

def get_pill_id_service():
    return PillIdService()

def get_naver_search_service():
    return NaverSearchService()

@router.post("/step1-extract", response_model=Step1ExtractResponse)
async def analyze_step1_extract(
    req: Step1ExtractRequest,
    service: StepByStepAnalysisService = Depends(get_analysis_service)
):
    """
    [Step 1] 증상/처방전 초기 인식 및 키워드 추출
    """
    try:
        import asyncio
        result = await asyncio.to_thread(service.step1_extract, req.search_type, req.text, req.image_url)
        return Step1ExtractResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.post("/step2-search", response_model=Step2SearchResponse)
async def analyze_step2_search(
    req: Step2SearchRequest,
    service: StepByStepAnalysisService = Depends(get_analysis_service)
):
    """
    [Step 2] 확정된 키워드로 DB/Vector 검색 수행
    """
    try:
        # Pydantic schema expects dict structure matching response model
        # The service returns {"candidates": {...}}
        import asyncio
        result = await asyncio.to_thread(service.step2_search, req.session_id, req.confirmed_keywords)
        return Step2SearchResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search Error: {str(e)}")


@router.post("/step3-report", response_model=Step3ReportResponse)
async def analyze_step3_report(
    req: Step3ReportRequest,
    service: StepByStepAnalysisService = Depends(get_analysis_service)
):
    """
    [Step 3] 최종 리포트 생성 (LLM 활용)
    """
    try:
        # Convert Pydantic models to dict for service
        candidates = [c.dict() for c in req.selected_candidates]
        result = await service.step3_report(req.session_id, candidates)

        return Step3ReportResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report Generation Error: {str(e)}")


# 📌 중요: 구체적인 경로를 먼저 정의해야 FastAPI가 올바르게 라우팅합니다!
# 순서: /prescription/stream → /prescription/sections → /prescription

@router.post("/prescription-stream")
async def analyze_prescription_stream(
    file: UploadFile = File(..., description="처방전 이미지 파일 (jpg/png)"),
    sections: str = Form("1,2", description="분석할 섹션 번호 (예: '1,2' 또는 '1,2,3,4,5')"),
    service: PrescriptionService = Depends(get_prescription_service),
):
    """
    [처방전 스트리밍 분석] SSE(Server-Sent Events) 방식으로 진행 상황을 실시간 전송.
    - sections="1,2"       → OCR + 약물정보만 (빠름)
    - sections="1,2,3,4,5" → 전체 분석 (학술근거·생활가이드·동의보감 포함)
    """
    allowed_types = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
    content_type = file.content_type or "image/jpeg"
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식: {content_type}")

    image_bytes = await file.read()
    selected_sections = set(sections.split(","))

    async def event_generator():
        try:
            async for event in service.analyze_prescription_streaming(
                image_bytes, content_type, selected_sections
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/prescription/sections")
async def fetch_prescription_sections(
    request: dict,
    service: PrescriptionService = Depends(get_prescription_service),
):
    """
    [결과 화면 on-demand 섹션 분석]
    처음 분석 후 사용자가 개별 선택한 섹션(4·생활가이드, 5·동의보감)을 추가로 실행.
    request: { "drug_list": ["약물1", ...], "sections": ["4"] }
    """
    drug_list: list = request.get("drug_list", [])
    sections: set = set(request.get("sections", []))
    if not sections:
        raise HTTPException(status_code=400, detail="sections 필드가 비어있습니다.")
    try:
        result = await service.fetch_optional_sections(drug_list, sections)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"섹션 분석 오류: {str(e)}")


@router.post("/prescription")
async def analyze_prescription(
    file: UploadFile = File(..., description="처방전 이미지 파일 (jpg/png)"),
    sections: str = Form("1,2", description="분석할 섹션 번호 (예: '1,2' 또는 '1,2,3,4,5')"),
    service: PrescriptionService = Depends(get_prescription_service),
):
    """
    [처방전 SSE 스트리밍] 실시간 진행 상황 전송
    - sections="1,2"       → OCR + 약물정보만 (빠름)
    - sections="1,2,3,4,5" → 전체 분석
    """
    print("[DEBUG] Prescription streaming endpoint called")  # Force reload
    allowed_types = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
    content_type = file.content_type or "image/jpeg"
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식: {content_type}")

    image_bytes = await file.read()
    selected_sections = set(sections.split(","))

    async def event_generator():
        try:
            async for event in service.analyze_prescription_streaming(
                image_bytes, content_type, selected_sections
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/diet-recommendation")
async def get_diet_recommendation(
    request: dict
):
    """
    AI 맞춤 레시피 추천
    """
    try:
        import os
        from openai import AsyncOpenAI

        food_names = request.get("foodNames", "")
        drug_names = request.get("drugNames", "")

        # OpenAI API 사용 (Gemini 할당량 초과 시 대체)
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

        client = AsyncOpenAI(api_key=openai_key)

        prompt = f"""추천된 식재료({food_names})를 활용하여 지금 드시는 약({drug_names})과 충돌하지 않는 '오늘의 한 끼 건강 레시피'를 하나만 추천해줘.

재료와 간단한 조리법, 그리고 왜 이 음식이 당신의 몸 상태에 좋은지 이유를 포함해줘.
말투는 아주 다정하게."""

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 한방 영양학 전문가입니다. 친절하고 다정한 말투로 건강 레시피를 추천해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        recommendation = response.choices[0].message.content

        return {"recommendation": recommendation}

    except Exception as e:
        print(f"[Diet Recommendation Error] {e}")
        raise HTTPException(status_code=500, detail=f"레시피 추천 오류: {str(e)}")


@router.post("/symptom-diet")
async def get_symptom_diet(
    request: dict,
    service: StepByStepAnalysisService = Depends(get_analysis_service),
):
    """
    증상 텍스트 → 동의보감 기반 맞춤 식단 추천
    request: { "symptom": "소화가 안 되고 속이 더부룩해요" }
    Returns: { "foods": [{name, reason, precaution}], "donguiSection": "..." }
    """
    symptom = request.get("symptom", "").strip()
    if not symptom:
        raise HTTPException(status_code=400, detail="symptom 필드가 비어있습니다.")

    try:
        from app.services.analyze_service import AnalyzeService
        analyze_svc = AnalyzeService()
        result = await analyze_svc.analyze_symptom(symptom)

        foods = []
        for ing in result.ingredients:
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

        # foods가 없으면 AI 직접 생성
        if not foods:
            from app.services.prescription_service import PrescriptionService
            ps = PrescriptionService()
            foods = await ps._ai_food_fallback([symptom])

        matched_name = getattr(result, "matched_symptom_name", None)
        dongui_section = (
            f"{matched_name} 관련 동의보감 처방" if matched_name
            else f'"{symptom[:30]}" 증상 기반 약선 식단'
        )

        # 추천 음식 기반 요약 생성
        food_names = [f["name"] for f in foods[:5] if f.get("name")]
        summary = (
            f"입력하신 증상에 도움이 되는 {', '.join(food_names)} 등을 추천드립니다."
            if food_names
            else result.symptom_summary
        )

        return {
            "foods": foods[:5],
            "donguiSection": dongui_section,
            "summary": summary,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"증상 식단 분석 오류: {str(e)}")


@router.post("/pill-search/name", response_model=PillSearchResponse)
async def pill_search_by_name(
    req: PillSearchByNameRequest,
    service: PillIdService = Depends(get_pill_id_service),
):
    """
    [낱알 검색 — 약품명]
    약품명으로 의약품 낱알 외형 정보(모양·색깔·각인·이미지)를 조회합니다.
    식약처 MdcinGrnIdntfcInfoService03 기반 (Level A)
    """
    try:
        pills = await service.search_by_name(req.drug_name)
        return PillSearchResponse(
            total=len(pills),
            items=[PillIdService.to_dict(p) for p in pills],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"낱알 검색 오류: {str(e)}")


@router.post("/pill-search/appearance", response_model=PillSearchResponse)
async def pill_search_by_appearance(
    req: PillSearchByAppearanceRequest,
    service: PillIdService = Depends(get_pill_id_service),
):
    """
    [낱알 검색 — 외형]
    모양·색깔·각인 등 외형 정보로 의약품 낱알을 검색합니다.
    알 수 없는 약을 모양으로 식별할 때 사용합니다.
    """
    if not any([req.drug_shape, req.color_class1, req.color_class2,
                req.mark_front, req.mark_back, req.leng_long, req.leng_short]):
        raise HTTPException(status_code=400, detail="검색 조건을 하나 이상 입력해주세요.")
    try:
        pills = await service.search_by_appearance(
            drug_shape=req.drug_shape or "",
            color_class1=req.color_class1 or "",
            color_class2=req.color_class2 or "",
            mark_front=req.mark_front or "",
            mark_back=req.mark_back or "",
            leng_long=req.leng_long or "",
            leng_short=req.leng_short or "",
        )
        return PillSearchResponse(
            total=len(pills),
            items=[PillIdService.to_dict(p) for p in pills],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"낱알 외형 검색 오류: {str(e)}")


@router.get("/faq")
def get_faq_questions(category: str = None):
    """
    [골든 FAQ] 증상 카테고리별 추천 질문 목록 반환
    ?category=소화/장 | 수면/스트레스 | 면역/호흡기 | 대사/만성 (없으면 전체)
    """
    svc = FAQService()
    questions = svc.get_golden_questions()
    if category:
        questions = [q for q in questions if q.get("category") == category]
    return {"total": len(questions), "questions": questions}


@router.get("/pharmacy/nearby")
async def search_nearby_pharmacies(
    lat: float,
    lng: float,
    radius: int = 1000,
    display: int = 5,
    service: NaverSearchService = Depends(get_naver_search_service),
):
    """
    [주변 약국 검색] 네이버 지역 검색 API를 사용하여 주변 약국 검색
    - lat: 위도
    - lng: 경도
    - radius: 검색 반경 (미터, 기본 1km)
    - display: 검색 결과 개수 (기본 5개)
    """
    try:
        pharmacies = await service.search_nearby_pharmacies(lat, lng, radius, display)
        return {
            "total": len(pharmacies),
            "pharmacies": pharmacies
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"약국 검색 오류: {str(e)}")


# ──────────────────────────────────────────────────────────────────────────────
#  건강 뉴스 검색 (네이버 뉴스 API)
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/health-news")
async def get_health_news(query: str = "건강", display: int = 5):
    """Google News RSS로 건강 관련 뉴스 검색 (무료, API 키 불필요)"""
    import httpx
    from urllib.parse import quote
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime

    rss_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=ko&gl=KR&ceid=KR:ko"

    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(rss_url, timeout=10.0)
            res.raise_for_status()

        root = ET.fromstring(res.content)
        channel = root.find("channel")
        if channel is None:
            return {"items": []}

        items = []
        for item in channel.findall("item")[:display]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            source = item.findtext("source", "")

            # pubDate를 한국어 날짜로 변환
            date_str = ""
            if pub_date:
                try:
                    dt = parsedate_to_datetime(pub_date)
                    date_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    date_str = pub_date

            # 제목에서 출처 분리 (Google News 형식: "제목 - 출처")
            summary = ""
            if " - " in title and source:
                summary = f"출처: {source}"

            items.append({
                "title": title,
                "summary": summary,
                "url": link,
                "date": date_str,
            })

        return {"items": items}

    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Google News RSS 호출 실패: {str(e)}")
    except ET.ParseError as e:
        raise HTTPException(status_code=502, detail=f"RSS 파싱 실패: {str(e)}")


# ──────────────────────────────────────────────────────────────────────────────
#  방송가 핫 트렌드 (건강 방송 프로그램 최신 소식)
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/health-trends")
async def get_health_trends(display: int = 3):
    """건강 관련 방송 프로그램의 최신 트렌드를 Google News RSS로 검색"""
    import httpx, re
    from urllib.parse import quote
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime

    def strip_html(text: str) -> str:
        return re.sub(r'<[^>]+>', '', text).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()

    # 건강 방송 프로그램 키워드: (검색어, 프로그램명, 제목에 포함되어야 할 단어)
    show_keywords = [
        ('"생로병사의 비밀"', "생로병사의 비밀", "생로병사"),
        ('"명의" KBS 건강 방송 프로그램', "명의", "명의"),
        ('"나는 몸신이다"', "나는 몸신이다", "몸신"),
        ('"무엇이든 물어보세요" KBS 건강', "무엇이든 물어보세요", "물어보세요"),
        ('"천기누설" MBN 건강', "천기누설", "천기누설"),
    ]

    # 제외할 단어 (건강 방송과 무관)
    exclude_words = ["명의도용", "도용", "사기", "협박", "범죄", "검찰", "경찰서"]

    items = []
    try:
        async with httpx.AsyncClient() as client:
            for keyword, source_label, must_contain in show_keywords:
                if len(items) >= display:
                    break
                rss_url = f"https://news.google.com/rss/search?q={quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
                try:
                    res = await client.get(rss_url, timeout=8.0)
                    res.raise_for_status()
                    root = ET.fromstring(res.content)
                    channel = root.find("channel")
                    if channel is None:
                        continue

                    # 여러 item 중 적합한 것 선택
                    found = False
                    for rss_item in channel.findall("item")[:5]:
                        title = rss_item.findtext("title", "")
                        # 제외 단어 필터
                        if any(w in title for w in exclude_words):
                            continue
                        # 프로그램명이 제목에 포함되어야 함
                        if must_contain not in title:
                            continue

                        description = rss_item.findtext("description", "")
                        link = rss_item.findtext("link", "")
                        clean_title = title.rsplit(" - ", 1)[0] if " - " in title else title

                        items.append({
                            "trend": strip_html(clean_title),
                            "description": strip_html(description) if description else clean_title,
                            "source": source_label,
                            "url": link,
                        })
                        found = True
                        break

                except Exception:
                    continue

        return {"items": items}

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"방송 트렌드 검색 실패: {str(e)}")


@router.get("/health-tip")
async def get_health_tip():
    """Google News RSS에서 오늘의 건강 팁을 가져옵니다."""
    import httpx, re, random
    from urllib.parse import quote
    import xml.etree.ElementTree as ET

    def strip_html(text: str) -> str:
        return re.sub(r'<[^>]+>', '', text).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()

    tip_queries = ["건강 팁", "건강 생활습관", "건강 음식 추천", "운동 건강", "면역력 높이는 방법"]
    query = random.choice(tip_queries)
    rss_url = f"https://news.google.com/rss/search?q={quote(query)}&hl=ko&gl=KR&ceid=KR:ko"

    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(rss_url, timeout=8.0)
            res.raise_for_status()

        root = ET.fromstring(res.content)
        channel = root.find("channel")
        if channel is None:
            return {"tip": "오늘도 건강한 하루 보내세요!", "url": ""}

        rss_items = channel.findall("item")
        if not rss_items:
            return {"tip": "오늘도 건강한 하루 보내세요!", "url": ""}

        # 랜덤하게 하나 선택
        chosen = random.choice(rss_items[:10])
        title = strip_html(chosen.findtext("title", ""))
        # "제목 - 출처" 형식에서 출처 제거
        clean_title = title.rsplit(" - ", 1)[0] if " - " in title else title
        link = chosen.findtext("link", "")
        description = strip_html(chosen.findtext("description", ""))

        return {
            "tip": clean_title,
            "description": description or clean_title,
            "url": link,
        }

    except Exception:
        return {"tip": "오늘도 건강한 하루 보내세요!", "url": ""}
