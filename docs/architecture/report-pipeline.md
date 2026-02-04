flowchart TB
  %% =========================
  %% PDF Report Generation Pipeline
  %% =========================

  U[User] --> I[Inputs\n- Symptoms\n- Meds/Supplements\n- Diet/Notes\n- Goals]
  I --> S[Store in Postgres\n(symptom logs, stack items)]

  S --> C[Context Builder\n- Recent timeline\n- Current stack snapshot\n- Risk flags]
  C --> R[RAG Retrieval\n- Vector search\n- Source ranking\n- Evidence pack]
  R --> G[LLM Generation\n- Modern-language explanation\n- Recommendations\n- Warnings & interactions]
  G --> V[Validation & Rules\n- Tone/format rules\n- Safety disclaimers\n- Citations required]
  V --> P[PDF Renderer\n(Template + sections)]
  P --> A[Archive\n- Save PDF URL\n- Save summary metadata]
  A --> D[Deliver\n- Download link\n- Share for clinic]
  
  subgraph Evidence[Evidence Sources]
    E1[Traditional Medicine DB]
    E2[PubMed/Papers]
    E3[Curated content (YouTube/articles)]
  end

  Evidence --> R


##Implementation checkpoints

#Context Builder: 사용자 기록을 "이번 달 스냅샷"으로 요약(시간축/이행률/변화점)

#RAG Retrieval: 근거 패키지(evidence pack) 단위로 구성 (출처/요약/신뢰도)

#Validation & Rules: pdf_generation_rules.v1.json을 기반으로 문장/섹션 규칙 적용

#Archive: 리포트 메타데이터(기간, 주요 이슈 태그, 스택 요약)를 함께 저장

