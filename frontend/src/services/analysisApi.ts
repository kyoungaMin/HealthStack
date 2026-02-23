import axios from 'axios';

// API Base URL (FastAPI)
const API_BASE_URL = (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001') + '/api/v1';

// ─── Symptom Analysis Types ───────────────────────────────────────────────────

export interface DetectionKeyword {
    keyword: string;
    confidence: number;
}

export interface CandidateItem {
    id: string | number;
    name: string;
    description?: string;
    match_score?: number;
    efficacy?: string;
    category?: string;
}

export interface SearchCandidates {
    tkm_symptoms: CandidateItem[];
    modern_drugs: CandidateItem[];
}

export interface FoodItem {
    name: string;
    reason: string;
}

export interface QAItem {
    question: string;
    answer: string;
}

// Symptom analysis final report
export interface ReportData {
    summary: string;
    medication_guide?: Record<string, string>;
    food_therapy: {
        recommended: FoodItem[];
        avoid: FoodItem[];
    };
    lifestyle_advice: string;
    related_questions?: QAItem[];
}

// ─── Prescription Analysis Types ─────────────────────────────────────────────

export interface DrugDetail {
    name: string;
    efficacy: string;
    sideEffects: string;
}

export interface AcademicEvidence {
    summary: string;
    trustLevel: string;        // "A" | "B" | "C"
    papers?: { title: string; url: string }[];
}

export interface DonguibogamFood {
    name: string;
    reason: string;
    precaution?: string;
}

export interface PrescriptionData {
    prescriptionSummary: {
        drugList: string[];
        warnings: string;
    };
    drugDetails: DrugDetail[];
    academicEvidence: AcademicEvidence;
    lifestyleGuide: {
        symptomTokens: string[];
        advice: string;
    };
    donguibogam: {
        foods: DonguibogamFood[];
        donguiSection: string;
    };
}

export interface ProgressEvent {
    step: number;
    message: string;
    progress: number;
}

// ─── Pharmacy Types ───────────────────────────────────────────────────────────

export interface PharmacyItem {
    title: string;
    address: string;
    phone?: string;
    distance?: string;
    mapx?: string;
    mapy?: string;
}

// ─── Symptom Analysis API ─────────────────────────────────────────────────────

export const step1Extract = async (type: 'symptom' | 'prescription', text?: string, imageUrl?: string) => {
    const response = await axios.post(`${API_BASE_URL}/analyze/step1-extract`, {
        search_type: type,
        text,
        image_url: imageUrl
    });
    return response.data.data;
};

export const step2Search = async (sessionId: string, confirmedKeywords: string[]) => {
    const response = await axios.post(`${API_BASE_URL}/analyze/step2-search`, {
        session_id: sessionId,
        confirmed_keywords: confirmedKeywords
    });
    return response.data.data;
};

export const step3Report = async (sessionId: string, selectedCandidates: { type: string, id: string | number }[]) => {
    const response = await axios.post(`${API_BASE_URL}/analyze/step3-report`, {
        session_id: sessionId,
        selected_candidates: selectedCandidates
    });
    return response.data.data;
};

// ─── Prescription SSE Streaming API ──────────────────────────────────────────

/**
 * 처방전 이미지를 SSE 스트리밍으로 분석합니다.
 * sections: "1,2,3,4,5" = 전체 분석 (OCR + 약물정보 + PubMed + 생활가이드 + 동의보감)
 * Returns AbortController — call .abort() to cancel.
 */
export const analyzePrescriptionSSE = (
    file: File,
    sections: string = '1,2,3,4,5',
    onProgress: (event: ProgressEvent) => void,
    onComplete: (data: PrescriptionData) => void,
    onError: (message: string) => void,
): AbortController => {
    const controller = new AbortController();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('sections', sections);

    fetch(`${API_BASE_URL}/analyze/prescription`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
    })
        .then(async (response) => {
            if (!response.ok) {
                onError(`서버 오류 (HTTP ${response.status})`);
                return;
            }
            const reader = response.body!.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                // SSE format: "data: {...}\n\n"
                const chunks = buffer.split('\n\n');
                buffer = chunks.pop() ?? '';

                for (const chunk of chunks) {
                    const line = chunk.trim();
                    if (!line.startsWith('data: ')) continue;
                    try {
                        const event = JSON.parse(line.slice(6));
                        if (event.type === 'progress') {
                            onProgress({ step: event.step, message: event.message, progress: event.progress ?? 0 });
                        } else if (event.type === 'result') {
                            onComplete(event.data as PrescriptionData);
                        } else if (event.type === 'error') {
                            onError(event.message ?? '알 수 없는 오류');
                        }
                    } catch {
                        // JSON parse error — skip malformed chunk
                    }
                }
            }
        })
        .catch((err) => {
            if (err.name !== 'AbortError') {
                onError(err.message ?? '네트워크 오류가 발생했습니다.');
            }
        });

    return controller;
};

// ─── Legacy non-streaming prescription (kept for AnalysisWizard) ─────────────

export const analyzePrescriptionFile = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('sections', '1,2,3,4,5');
    const response = await axios.post(`${API_BASE_URL}/analyze/prescription`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'text',
    });
    // Parse SSE text to extract the final "result" event
    const text: string = response.data;
    const lines = text.split('\n\n');
    for (const chunk of [...lines].reverse()) {
        const line = chunk.trim();
        if (line.startsWith('data: ')) {
            try {
                const event = JSON.parse(line.slice(6));
                if (event.type === 'result') return event.data;
            } catch { /* skip */ }
        }
    }
    return {};
};

// ─── Pharmacy API ─────────────────────────────────────────────────────────────

export const getNearbyPharmacies = async (
    lat: number,
    lng: number,
    radius = 1000,
    display = 10,
): Promise<{ total: number; pharmacies: PharmacyItem[] }> => {
    const response = await axios.get(`${API_BASE_URL}/analyze/pharmacy/nearby`, {
        params: { lat, lng, radius, display },
    });
    return response.data;
};

// ─── Diet Recommendation API ──────────────────────────────────────────────────

export const getDietRecommendation = async (foodNames: string, drugNames: string): Promise<string> => {
    const response = await axios.post(`${API_BASE_URL}/analyze/diet-recommendation`, {
        foodNames,
        drugNames,
    });
    return response.data.recommendation;
};

export interface SymptomDietResult {
    foods: { name: string; reason: string; precaution?: string }[];
    donguiSection: string;
    summary: string;
}

export const getSymptomDiet = async (symptom: string): Promise<SymptomDietResult> => {
    const response = await axios.post(`${API_BASE_URL}/analyze/symptom-diet`, { symptom });
    return response.data;
};

// ─── FAQ API ──────────────────────────────────────────────────────────────────

export const getFAQ = async (category?: string) => {
    const response = await axios.get(`${API_BASE_URL}/analyze/faq`, {
        params: category ? { category } : undefined,
    });
    return response.data;
};

// ─── Health News API ─────────────────────────────────────────────────────────

export interface HealthNewsItem {
    title: string;
    summary: string;
    url: string;
    date: string;
}

export const getHealthNews = async (query: string = '건강', display: number = 5): Promise<HealthNewsItem[]> => {
    const response = await axios.get(`${API_BASE_URL}/analyze/health-news`, {
        params: { query, display },
    });
    return response.data.items;
};

// ─── Health Trends API (방송가 핫 트렌드) ────────────────────────────────────

export interface HealthTrendItem {
    trend: string;
    description: string;
    source: string;
    url: string;
}

export const getHealthTrends = async (display: number = 3): Promise<HealthTrendItem[]> => {
    const response = await axios.get(`${API_BASE_URL}/analyze/health-trends`, {
        params: { display },
    });
    return response.data.items;
};

// ─── Health Tip API (오늘의 건강 팁) ─────────────────────────────────────────

export interface HealthTip {
    tip: string;
    description?: string;
    url: string;
}

export const getHealthTip = async (): Promise<HealthTip> => {
    const response = await axios.get(`${API_BASE_URL}/analyze/health-tip`);
    return response.data;
};
