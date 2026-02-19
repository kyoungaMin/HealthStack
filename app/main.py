from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import analysis

app = FastAPI(
    title="HealthStack API",
    description="Step-by-Step Analysis API for Symptoms & Prescriptions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정 (React 프론트엔드 연동)
origins = [
    "http://localhost:3000", # React
    "http://localhost:5173", # Vite
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router 등록
app.include_router(analysis.router, prefix="/api/v1/analyze", tags=["Analysis"])

@app.get("/")
def root():
    return {"message": "HealthStack API is running. Visit /docs for documentation."}
