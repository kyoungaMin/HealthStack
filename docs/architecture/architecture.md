flowchart LR
  %% =========================
  %% Health Stack System Architecture
  %% =========================

  subgraph FE[Frontend]
    UI[React UI\n- Symptoms Input\n- Stack Manager\n- Results + Evidence\n- PDF Download]
  end

  subgraph BE[Backend API]
    API[FastAPI\n- Auth Context\n- Stack Logic\n- RAG Orchestrator\n- Recommendation\n- PDF Generator]
  end

  subgraph DB[Data Layer (Supabase Postgres)]
    PG[(PostgreSQL)]
    RLS[RLS Policies\n(Row Level Security)]
    T1[users]
    T2[symptoms / logs]
    T3[drugs]
    T4[supplements]
    T5[foods]
    T6[reports]
  end

  subgraph VS[Vector Layer (pgvector)]
    VDB[(Vectors)]
    E1[symptoms embeddings]
    E2[foods embeddings]
    E3[traditional medicine embeddings]
    E4[papers embeddings]
    E5[contents embeddings]
  end

  subgraph CACHE[Cache & Control]
    REDIS[(Redis / Upstash)]
    RL[Rate Limit]
    SES[Short-lived session cache]
  end

  subgraph EXT[External Sources]
    DKB[Traditional Medicine DB\n(동의보감/현대어)]
    PUB[PubMed / Papers]
    YT[YouTube / Content APIs]
  end

  UI -->|REST/JSON| API

  API --> PG
  PG --- RLS
  PG --> T1
  PG --> T2
  PG --> T3
  PG --> T4
  PG --> T5
  PG --> T6

  API --> VDB
  VDB --> E1
  VDB --> E2
  VDB --> E3
  VDB --> E4
  VDB --> E5

  API --> REDIS
  REDIS --> RL
  REDIS --> SES

  API --> DKB
  API --> PUB
  API --> YT

##Notes

#This diagram is intended as the single source of truth for the high-level system topology.

#Pair this with ERDs under /docs/erd/ for database-level detail.