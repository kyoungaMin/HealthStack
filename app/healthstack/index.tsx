
import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';

const BACKEND_URL = 'http://localhost:8000';

// --- Types (SERVICE_PLAN2.md 기준) ---
interface DrugDetail {
  name: string;
  efficacy: string;
  sideEffects: string;
}

interface AcademicPaper {
  title: string;
  url: string;
}

interface DonguibogamFood {
  name: string;
  reason: string;
  precaution: string;
}

interface TraditionalPrescription {
  name: string;
  source: string;
  description: string;
}

interface TkmPaper {
  title: string;
  url: string;
}

interface AnalysisData {
  prescriptionSummary: {
    drugList: string[];
    warnings: string;
  };
  drugDetails: DrugDetail[];
  academicEvidence: {
    summary: string;
    trustLevel: string;
    papers: AcademicPaper[];
  };
  lifestyleGuide: {
    symptomTokens: string[];
    advice: string;
  };
  donguibogam: {
    foods: DonguibogamFood[];
    donguiSection: string;
    traditionalPrescriptions?: TraditionalPrescription[];
    tkmPapers?: TkmPaper[];
  };
}

interface SavedStack {
  id: string;
  date: string;
  drugList: string[];
  data: AnalysisData;
  videos?: { title: string; uri: string }[];
  dietPlan?: string;
}

// --- Helpers ---
const decode = (base64: string) => {
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
};

async function decodeAudioData(
  data: Uint8Array,
  ctx: AudioContext,
  sampleRate: number,
  numChannels: number,
): Promise<AudioBuffer> {
  const dataInt16 = new Int16Array(data.buffer);
  const frameCount = dataInt16.length / numChannels;
  const buffer = ctx.createBuffer(numChannels, frameCount, sampleRate);

  for (let channel = 0; channel < numChannels; channel++) {
    const channelData = buffer.getChannelData(channel);
    for (let i = 0; i < frameCount; i++) {
      channelData[i] = dataInt16[i * numChannels + channel] / 32768.0;
    }
  }
  return buffer;
}

const blobToBase64 = (blob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64String = (reader.result as string).split(',')[1];
      resolve(base64String);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
};

// --- App Component ---

const App = () => {
  const [activeTab, setActiveTab] = useState<'home' | 'stack' | 'map' | 'report'>('home');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [recommendedVideos, setRecommendedVideos] = useState<{title: string; uri: string}[]>([]);
  const [dietRecommendation, setDietRecommendation] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [savedStacks, setSavedStacks] = useState<SavedStack[]>([]);
  
  const [loadingVideos, setLoadingVideos] = useState(false);
  const [isVideosLoaded, setIsVideosLoaded] = useState(false);
  const [loadingDiet, setLoadingDiet] = useState(false);
  const [isDietLoaded, setIsDietLoaded] = useState(false);
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const stored = localStorage.getItem('health_stacks_v3_warm');
    if (stored) {
      setSavedStacks(JSON.parse(stored));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('health_stacks_v3_warm', JSON.stringify(savedStacks));
  }, [savedStacks]);

  const initAudio = () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setLoadingStep('소중한 건강 정보를 읽고 있어요...');
    setIsVideosLoaded(false);
    setIsDietLoaded(false);
    setRecommendedVideos([]);
    setDietRecommendation(null);

    try {
      setLoadingStep('처방전을 분석하고 있어요...');
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${BACKEND_URL}/api/v1/analyze/prescription`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`서버 오류 (${response.status}): ${errText}`);
      }

      setLoadingStep('동의보감 지혜를 연결하고 있어요...');
      const data: AnalysisData = await response.json();

      setAnalysisData(data);
      // 동의보감 데이터가 백엔드에서 함께 오므로 즉시 표시
      setIsVideosLoaded(true);

      const newEntry: SavedStack = {
        id: Date.now().toString(),
        date: new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
        drugList: data.prescriptionSummary.drugList,
        data: data
      };

      setSavedStacks(prev => [newEntry, ...prev]);
      setShowResult(true);
      setActiveTab('home');

    } catch (error: any) {
      console.error(error);
      const msg = error?.message ?? '';
      if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
        alert("백엔드 서버에 연결할 수 없습니다.\n서버가 실행 중인지 확인해주세요 (http://localhost:8000)");
      } else {
        alert(`분석에 실패했습니다.\n${msg}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchRelatedVideos = async () => {
    if (!analysisData) {
      alert('먼저 처방전을 분석해주세요.');
      return;
    }
    if (loadingVideos) return;
    if (recommendedVideos.length > 0) {
      console.log('영상이 이미 로드되었습니다.');
      return;
    }

    setLoadingVideos(true);
    try {
      const foods = analysisData.donguibogam?.foods ?? [];
      if (foods.length === 0) {
        alert('추천 식재료가 없어 영상을 검색할 수 없습니다.');
        setLoadingVideos(false);
        return;
      }

      const YOUTUBE_API_KEY = 'AIzaSyDEbol0b3cNklevraAls5OLV2V--6a1Yqw';
      let videoLinks = [];

      // 전략 1: 첫 번째 식재료로 검색 (가장 구체적)
      const firstFood = foods[0].name.split(',')[0].trim(); // "생강, 염분이 많은 음식" -> "생강"
      const searchQuery1 = encodeURIComponent(`${firstFood} 효능 요리법`);
      console.log('[Video Search] 검색 1:', firstFood);

      const response1 = await fetch(`https://www.googleapis.com/youtube/v3/search?part=snippet&q=${searchQuery1}&type=video&maxResults=2&key=${YOUTUBE_API_KEY}`);
      if (response1.ok) {
        const data1 = await response1.json();
        console.log('[Video Search] 응답 1:', data1);
        if (data1.items && data1.items.length > 0) {
          videoLinks = data1.items.map((item: any) => ({
            title: item.snippet.title,
            uri: `https://www.youtube.com/watch?v=${item.id.videoId}`
          }));
        }
      }

      // 전략 2: 결과 없으면 일반적인 건강 요리법으로 검색
      if (videoLinks.length === 0) {
        const searchQuery2 = encodeURIComponent('건강 요리법 추천');
        console.log('[Video Search] 검색 2: 건강 요리법 추천 (fallback)');
        const response2 = await fetch(`https://www.googleapis.com/youtube/v3/search?part=snippet&q=${searchQuery2}&type=video&maxResults=2&key=${YOUTUBE_API_KEY}`);
        if (response2.ok) {
          const data2 = await response2.json();
          console.log('[Video Search] 응답 2:', data2);
          videoLinks = data2.items?.map((item: any) => ({
            title: item.snippet.title,
            uri: `https://www.youtube.com/watch?v=${item.id.videoId}`
          })) ?? [];
        }
      }

      if (videoLinks.length === 0) {
        alert('관련 영상을 찾을 수 없습니다.');
      } else {
        console.log('[Video Search] 성공:', videoLinks);
      }

      setRecommendedVideos(videoLinks);
      setSavedStacks(prev => prev.map((s, i) => i === 0 ? { ...s, videos: videoLinks } : s));
    } catch (error) {
      console.error('[Video Search] 오류:', error);
      alert(`영상 검색 중 오류가 발생했습니다: ${error.message || error}`);
    } finally {
      setLoadingVideos(false);
    }
  };

  const fetchDietRecommendation = async () => {
    if (!analysisData || loadingDiet) return;
    setLoadingDiet(true);
    try {
      const foodNames = (analysisData.donguibogam?.foods ?? []).map((f: any) => f.name).join(', ');
      const drugNames = (analysisData.prescriptionSummary?.drugList ?? []).join(', ');

      const response = await fetch(`${BACKEND_URL}/api/v1/analyze/diet-recommendation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ foodNames, drugNames })
      });

      if (!response.ok) {
        throw new Error(`서버 오류 (${response.status})`);
      }

      const data = await response.json();
      setDietRecommendation(data.recommendation);
      setIsDietLoaded(true);
      setSavedStacks(prev => prev.map((s, i) => i === 0 ? { ...s, dietPlan: data.recommendation } : s));
    } catch (error) {
      console.error('레시피 추천 오류:', error);
      alert('레시피 추천에 실패했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setLoadingDiet(false);
    }
  };

  const deleteStack = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm("이 기록을 삭제하시겠습니까?")) {
      setSavedStacks(prev => prev.filter(s => s.id !== id));
    }
  };

  const viewSavedStack = (stack: SavedStack) => {
    setAnalysisData(stack.data);
    setRecommendedVideos(stack.videos || []);
    setDietRecommendation(stack.dietPlan || null);
    setIsVideosLoaded(!!stack.videos);
    setIsDietLoaded(!!stack.dietPlan);
    setShowResult(true);
  };

  const speakSummary = async (text: string) => {
    initAudio();
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const response = await ai.models.generateContent({
        model: "gemini-2.5-flash-preview-04-17-tts",
        contents: [{ parts: [{ text: text.substring(0, 300) }] }],
        config: {
          responseModalities: [Modality.AUDIO],
          speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Kore' } } },
        },
      });
      const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
      if (base64Audio && audioContextRef.current) {
        const audioBuffer = await decodeAudioData(decode(base64Audio), audioContextRef.current, 24000, 1);
        const source = audioContextRef.current.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContextRef.current.destination);
        source.start();
      }
    } catch (e) { console.error(e); }
  };

  return (
    <div className="flex flex-col h-screen max-w-md mx-auto bg-[#fffdfa] shadow-2xl overflow-hidden relative border-x border-amber-50 font-sans">
      
      {/* Header */}
      <header className="p-5 bg-white flex items-center justify-between border-b border-amber-50 sticky top-0 z-50">
        <div>
          <h1 className="text-xl font-bold text-emerald-600 flex items-center gap-2">
            <span className="text-2xl">🌱</span> Health Stack <span className="text-[10px] bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded-full ml-1 font-normal">v3</span>
          </h1>
          <p className="text-[10px] text-emerald-400 font-medium tracking-wider">따뜻한 내 몸 설명서</p>
        </div>
        {showResult && (
          <button onClick={() => setShowResult(false)} className="text-amber-600 text-xs font-bold bg-amber-50 px-3 py-1.5 rounded-full hover:bg-amber-100">닫기</button>
        )}
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-4 pb-32">
        
        {activeTab === 'home' && !showResult && (
          <div className="space-y-6 animate-in">
            <div className="bg-gradient-to-br from-emerald-500 to-teal-600 p-8 rounded-[40px] text-white shadow-xl relative overflow-hidden">
              <div className="relative z-10">
                <h2 className="text-3xl font-gaegu font-bold mb-3">내 몸 설명서 📖</h2>
                <p className="text-emerald-50 opacity-90 leading-relaxed text-lg font-gaegu">
                  오늘 받은 처방전 사진을 올려주세요.<br/>
                  몸과 마음이 편안해지는 분석으로<br/>
                  건강을 꼼꼼히 챙겨드릴게요.
                </p>
              </div>
              <div className="absolute -bottom-4 -right-4 text-9xl opacity-10 rotate-12">🍃</div>
            </div>

            <div className="bg-white rounded-[32px] p-6 shadow-sm border border-emerald-50">
              <h3 className="font-bold text-emerald-800 mb-6 flex items-center gap-2 text-lg">
                <span className="w-2 h-6 bg-emerald-500 rounded-full"></span>
                지금 시작하기
              </h3>
              
              <div className="grid gap-4">
                <button 
                  onClick={() => fileInputRef.current?.click()}
                  className="group relative flex flex-col items-center justify-center p-12 bg-emerald-50 border-2 border-dashed border-emerald-200 rounded-[32px] hover:bg-emerald-100/50 transition-all active:scale-95"
                >
                  <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-md mb-4 group-hover:scale-110 transition-transform">
                    <span className="text-3xl">📸</span>
                  </div>
                  <p className="font-bold text-emerald-800">처방전 분석하기</p>
                  <p className="text-[10px] text-emerald-400 mt-2 font-medium">따뜻한 약사가 꼼꼼히 읽어드립니다</p>
                  <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept="image/*" className="hidden" />
                </button>
              </div>
            </div>

            {/* Feature Examples Section */}
            <div className="px-2">
              <h3 className="font-bold text-amber-500/60 text-[10px] uppercase tracking-widest mb-4 flex items-center gap-2">
                ✨ 따스한 건강 리포트 미리보기
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white p-5 rounded-[28px] border border-emerald-50 shadow-sm space-y-2">
                  <div className="w-9 h-9 bg-emerald-50 rounded-full flex items-center justify-center text-lg">💊</div>
                  <h4 className="text-xs font-bold text-emerald-800">약물 기전 분석</h4>
                  <p className="text-[10px] text-slate-500 leading-tight">약이 몸에서 어떻게 속삭이는지 쉽게 설명해요.</p>
                </div>
                <div className="bg-white p-5 rounded-[28px] border border-emerald-50 shadow-sm space-y-2">
                  <div className="w-9 h-9 bg-teal-50 rounded-full flex items-center justify-center text-lg">🔬</div>
                  <h4 className="text-xs font-bold text-emerald-800">PubMed 근거</h4>
                  <p className="text-[10px] text-slate-500 leading-tight">글로벌 지식으로 탄탄한 신뢰를 드립니다.</p>
                </div>
                <div className="bg-white p-5 rounded-[28px] border border-amber-50 shadow-sm space-y-2">
                  <div className="w-9 h-9 bg-amber-50 rounded-full flex items-center justify-center text-lg">📜</div>
                  <h4 className="text-xs font-bold text-amber-800">동의보감 지혜</h4>
                  <p className="text-[10px] text-slate-500 leading-tight">예로부터 전해오는 자연의 치유법을 매칭해요.</p>
                </div>
                <div className="bg-white p-5 rounded-[28px] border border-rose-50 shadow-sm space-y-2">
                  <div className="w-9 h-9 bg-rose-50 rounded-full flex items-center justify-center text-lg">🥘</div>
                  <h4 className="text-xs font-bold text-rose-800">AI 식단 큐레이션</h4>
                  <p className="text-[10px] text-slate-500 leading-tight">맛있는 한 끼로 건강까지 채워드릴게요.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Results View - SERVICE_PLAN2.md 5개 섹션 */}
        {showResult && analysisData && (
          <div className="space-y-6 animate-in pb-10">

            {/* ═══════════════════════════════════════════════════════ */}
            {/* Section 1 — 처방전 요약 */}
            {/* ═══════════════════════════════════════════════════════ */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className="bg-emerald-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">SECTION 1</span>
                <h3 className="text-emerald-400 text-[10px] font-bold uppercase tracking-widest">처방전 요약</h3>
              </div>
              <section className="bg-white rounded-[32px] overflow-hidden shadow-sm border border-emerald-50">
                <div className="p-5 bg-emerald-600 text-white flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">📝</span>
                    <div>
                      <h3 className="font-bold">복용 약물 목록</h3>
                      <p className="text-[10px] opacity-80">{analysisData.prescriptionSummary.drugList.length}종 분석 완료</p>
                    </div>
                  </div>
                  <button onClick={() => speakSummary(analysisData.prescriptionSummary.warnings)} className="w-9 h-9 bg-white/20 rounded-full flex items-center justify-center text-xl hover:bg-white/30 transition-colors">🔊</button>
                </div>
                <div className="p-5 space-y-4">
                  <div className="flex flex-wrap gap-2">
                    {analysisData.prescriptionSummary.drugList.map((drug: string, i: number) => (
                      <span key={i} className="px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-xl text-xs font-bold border border-emerald-100">{drug}</span>
                    ))}
                  </div>
                  <div className="p-4 bg-rose-50 rounded-2xl border border-rose-100 flex gap-3">
                    <span className="text-rose-500 font-bold text-lg">💡</span>
                    <p className="text-xs text-rose-800 leading-normal font-medium">{analysisData.prescriptionSummary.warnings}</p>
                  </div>
                </div>
              </section>
            </div>

            {/* ═══════════════════════════════════════════════════════ */}
            {/* Section 2 — 약 이해 (각 약물별 효능·부작용) */}
            {/* ═══════════════════════════════════════════════════════ */}
            {analysisData.drugDetails && analysisData.drugDetails.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <span className="bg-blue-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">SECTION 2</span>
                  <h3 className="text-blue-400 text-[10px] font-bold uppercase tracking-widest">약 이해 - 효능·부작용</h3>
                </div>
                <div className="space-y-3">
                  {analysisData.drugDetails.map((drug: DrugDetail, i: number) => (
                    <section key={i} className="bg-white rounded-[24px] p-5 shadow-sm border border-blue-50">
                      <div className="flex items-start gap-3 mb-3">
                        <div className="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center text-xl flex-shrink-0">💊</div>
                        <div className="flex-1">
                          <h4 className="font-bold text-blue-900 text-sm mb-1">{drug.name}</h4>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="bg-blue-50/30 p-3 rounded-xl">
                          <p className="text-[10px] text-blue-600 font-bold mb-1">🟢 효능·효과</p>
                          <p className="text-[11px] text-blue-900/80 leading-relaxed">{drug.efficacy || '정보 없음'}</p>
                        </div>
                        {drug.sideEffects && (
                          <div className="bg-orange-50/30 p-3 rounded-xl">
                            <p className="text-[10px] text-orange-600 font-bold mb-1">⚠️ 주의사항·부작용</p>
                            <p className="text-[11px] text-orange-900/80 leading-relaxed">{drug.sideEffects}</p>
                          </div>
                        )}
                      </div>
                    </section>
                  ))}
                </div>
              </div>
            )}

            {/* ═══════════════════════════════════════════════════════ */}
            {/* Section 3 — 학술 근거 (PubMed) */}
            {/* ═══════════════════════════════════════════════════════ */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className="bg-teal-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">SECTION 3</span>
                <h3 className="text-teal-400 text-[10px] font-bold uppercase tracking-widest">학술 근거</h3>
              </div>
              <section className="bg-white rounded-[32px] p-6 shadow-sm border border-teal-50">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-xl">🔬</span>
                  <h3 className="font-bold text-teal-800 text-sm">PubMed 기반 분석</h3>
                  <span className="text-[9px] bg-teal-100 text-teal-600 px-2 py-0.5 rounded-full font-bold ml-auto">
                    신뢰 등급: {analysisData.academicEvidence.trustLevel}
                  </span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed bg-teal-50/20 p-4 rounded-2xl mb-4 italic">
                  "{analysisData.academicEvidence.summary}"
                </p>
                {analysisData.academicEvidence.papers && analysisData.academicEvidence.papers.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-[10px] text-teal-700 font-bold">📚 참고 논문</p>
                    {analysisData.academicEvidence.papers.map((paper: AcademicPaper, i: number) => (
                      <a key={i} href={paper.url} target="_blank" rel="noopener noreferrer" className="block p-3 bg-teal-50/30 rounded-xl hover:bg-teal-50 transition-colors">
                        <p className="text-[11px] text-teal-900 font-medium leading-relaxed">{paper.title}</p>
                      </a>
                    ))}
                  </div>
                )}
              </section>
            </div>

            {/* ═══════════════════════════════════════════════════════ */}
            {/* Section 4 — 생활 가이드 */}
            {/* ═══════════════════════════════════════════════════════ */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className="bg-purple-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">SECTION 4</span>
                <h3 className="text-purple-400 text-[10px] font-bold uppercase tracking-widest">생활 가이드</h3>
              </div>
              <section className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-[32px] p-6 shadow-sm border border-purple-100">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-xl">💡</span>
                  <h3 className="font-bold text-purple-800 text-sm">주의 증상 & 식습관 권장</h3>
                </div>
                {analysisData.lifestyleGuide.symptomTokens && analysisData.lifestyleGuide.symptomTokens.length > 0 && (
                  <div className="mb-4">
                    <p className="text-[10px] text-purple-600 font-bold mb-2">🏷️ 관련 증상</p>
                    <div className="flex flex-wrap gap-2">
                      {analysisData.lifestyleGuide.symptomTokens.map((token: string, i: number) => (
                        <span key={i} className="px-2 py-1 bg-white text-purple-700 rounded-lg text-[11px] font-bold border border-purple-100">
                          {token}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                <div className="bg-white/70 p-4 rounded-2xl border border-purple-200/50">
                  <p className="text-[12px] text-purple-900 leading-relaxed font-medium">
                    {analysisData.lifestyleGuide.advice}
                  </p>
                </div>
              </section>
            </div>

            {/* ═══════════════════════════════════════════════════════ */}
            {/* Section 5 — 동의보감 추천 */}
            {/* ═══════════════════════════════════════════════════════ */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className="bg-amber-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">SECTION 5</span>
                <h3 className="text-amber-900/40 text-[10px] font-bold uppercase tracking-widest">동의보감 추천</h3>
              </div>
              <section className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-[32px] p-6 shadow-sm border border-amber-100">
                <div className="bg-white/70 p-4 rounded-2xl mb-5 italic text-sm text-amber-900 border border-amber-200/50 leading-relaxed font-gaegu text-lg">
                  "{analysisData.donguibogam.donguiSection}"
                </div>

                {/* 식재료 추천 */}
                {analysisData.donguibogam.foods && analysisData.donguibogam.foods.length > 0 && (
                  <div className="mb-5">
                    <h5 className="text-[10px] font-bold text-amber-700 uppercase tracking-widest mb-3">🌿 추천 식재료</h5>
                    <div className="grid gap-3">
                      {analysisData.donguibogam.foods.map((food: DonguibogamFood, i: number) => (
                        <div key={i} className="bg-white p-4 rounded-2xl shadow-sm border border-amber-100 flex items-start gap-4">
                          <div className="w-10 h-10 bg-amber-50 rounded-full flex items-center justify-center text-xl flex-shrink-0">🍲</div>
                          <div className="flex-1">
                            <h4 className="font-bold text-amber-900 text-sm mb-1">{food.name}</h4>
                            <p className="text-[11px] text-amber-800/80 leading-relaxed mb-1">{food.reason}</p>
                            {food.precaution && (
                              <p className="text-[10px] text-rose-600 font-bold bg-rose-50 px-2 py-0.5 rounded inline-block">
                                참고: {food.precaution}
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 유사 처방 (한국전통지식포털) */}
                {analysisData.donguibogam.traditionalPrescriptions && analysisData.donguibogam.traditionalPrescriptions.length > 0 && (
                  <div className="mb-5 pt-5 border-t border-amber-200">
                    <h5 className="text-[10px] font-bold text-amber-700 uppercase tracking-widest mb-3">📜 유사 한방 처방</h5>
                    <div className="space-y-2">
                      {analysisData.donguibogam.traditionalPrescriptions.map((pres: TraditionalPrescription, i: number) => (
                        <div key={i} className="bg-white p-3 rounded-xl border border-amber-100">
                          <p className="text-[11px] font-bold text-amber-900 mb-1">{pres.name}</p>
                          <p className="text-[10px] text-amber-700">출처: {pres.source}</p>
                          <p className="text-[10px] text-amber-800/70 mt-1">{pres.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 한의학 논문 */}
                {analysisData.donguibogam.tkmPapers && analysisData.donguibogam.tkmPapers.length > 0 && (
                  <div className="mb-5 pt-5 border-t border-amber-200">
                    <h5 className="text-[10px] font-bold text-amber-700 uppercase tracking-widest mb-3">📚 한의학 연구 논문</h5>
                    <div className="space-y-2">
                      {analysisData.donguibogam.tkmPapers.map((paper: TkmPaper, i: number) => (
                        <a key={i} href={paper.url} target="_blank" rel="noopener noreferrer" className="block p-3 bg-white rounded-xl border border-amber-100 hover:bg-amber-50/50 transition-colors">
                          <p className="text-[10px] text-amber-900 leading-relaxed">{paper.title}</p>
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* 관련 영상 (선택적 로드) */}
                {loadingVideos ? (
                  <div className="mt-5 py-6 flex flex-col items-center gap-2">
                    <div className="w-5 h-5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-[10px] text-amber-600 font-bold">힐링 영상을 찾는 중...</p>
                  </div>
                ) : recommendedVideos.length > 0 ? (
                  <div className="mt-5 pt-5 border-t border-amber-200">
                    <h5 className="text-[10px] font-bold text-amber-700 uppercase tracking-widest mb-3">📺 건강을 요리하는 영상</h5>
                    <div className="grid grid-cols-2 gap-3">
                      {recommendedVideos.map((v, i) => (
                        <a key={i} href={v.uri} target="_blank" rel="noopener noreferrer" className="bg-white rounded-xl overflow-hidden shadow-sm hover:scale-[1.02] transition-transform">
                          <div className="h-20 bg-amber-50 flex items-center justify-center text-2xl opacity-60">🍯</div>
                          <div className="p-2 truncate text-[10px] font-bold text-amber-900">{v.title}</div>
                        </a>
                      ))}
                    </div>
                  </div>
                ) : (
                  <button onClick={fetchRelatedVideos} className="mt-5 w-full text-[10px] font-bold text-amber-600 bg-white py-2 rounded-xl hover:bg-amber-50 transition-colors border border-amber-200">
                    📺 관련 건강 영상 찾기
                  </button>
                )}
              </section>
            </div>

            {/* ═══════════════════════════════════════════════════════ */}
            {/* 추가: AI 레시피 생성 (Optional) */}
            {/* ═══════════════════════════════════════════════════════ */}
            <div className="space-y-4">
              {!isDietLoaded && !loadingDiet ? (
                <button onClick={fetchDietRecommendation} className="w-full p-6 rounded-[32px] flex flex-col items-center gap-2 shadow-sm transition-all bg-gradient-to-br from-rose-400 to-pink-500 text-white shadow-rose-100 hover:brightness-105 active:scale-95">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">🍯</span>
                    <span className="font-bold text-lg">AI 맞춤 레시피</span>
                  </div>
                  <p className="text-[10px] opacity-90 font-medium">지금 내 몸에 꼭 필요한 따뜻한 한 끼</p>
                </button>
              ) : (
                <div className="animate-in space-y-4">
                  <div className="flex items-center gap-2">
                    <span className="bg-rose-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">AI 레시피</span>
                    <h3 className="text-rose-900/40 text-[10px] font-bold uppercase tracking-widest">맞춤 힐링 레시피</h3>
                  </div>
                  <section className="bg-white rounded-[32px] p-6 shadow-md border-t-4 border-rose-400">
                    {loadingDiet ? (
                      <div className="py-10 flex flex-col items-center gap-3">
                        <div className="w-8 h-8 border-4 border-rose-100 border-t-rose-500 rounded-full animate-spin"></div>
                        <p className="text-rose-600 font-bold text-sm">레시피를 정성껏 작성 중...</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <h4 className="text-rose-800 font-bold flex items-center gap-2">
                            <span className="text-lg">👩‍🍳</span> 정성이 담긴 오늘의 메뉴
                          </h4>
                          <button onClick={() => speakSummary(dietRecommendation || '')} className="text-rose-400 text-lg hover:text-rose-500 transition-colors">🔊</button>
                        </div>
                        <div className="text-slate-600 text-sm leading-relaxed whitespace-pre-wrap bg-rose-50/20 p-5 rounded-2xl border border-rose-50 font-medium font-gaegu text-xl">
                          {dietRecommendation}
                        </div>
                      </div>
                    )}
                  </section>
                </div>
              )}
            </div>

            <p className="text-[10px] text-slate-400 text-center px-6 leading-relaxed opacity-60">
              ※ 제공된 정보는 참고 자료입니다. 정확한 진단과 치료는 의사·약사와 상담하세요.
            </p>
          </div>
        )}

        {/* My Stack Tab */}
        {activeTab === 'stack' && !showResult && (
          <div className="animate-in space-y-6">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-2xl font-bold font-gaegu text-emerald-800">복용 스택 아카이브 📋</h2>
              <span className="text-[10px] bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded-full font-bold">{savedStacks.length}개 보관 중</span>
            </div>
            
            {savedStacks.length === 0 ? (
              <div className="py-20 text-center bg-white rounded-[32px] border border-emerald-50 shadow-sm">
                 <div className="text-6xl mb-4 opacity-10">🌿</div>
                 <p className="text-slate-400 text-sm font-medium">아직 보관된 건강 기록이 없어요.<br/>홈에서 첫 분석을 시작해볼까요?</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {savedStacks.map((s) => (
                  <div key={s.id} onClick={() => viewSavedStack(s)} className="bg-white p-5 rounded-[32px] shadow-sm hover:border-emerald-200 border border-emerald-50 transition-all cursor-pointer group relative">
                    <div className="flex justify-between items-start mb-2">
                       <p className="text-[10px] font-bold text-emerald-300 mb-1">{s.date}</p>
                       <button onClick={(e) => deleteStack(s.id, e)} className="w-6 h-6 flex items-center justify-center text-rose-200 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity">✕</button>
                    </div>
                    <h4 className="font-bold text-slate-800 truncate mb-2">{s.drugList.join(', ')}</h4>
                    <div className="flex gap-1">
                      {s.videos && <span className="text-[9px] font-bold px-2 py-0.5 bg-amber-50 text-amber-600 rounded-full border border-amber-100">영상 가이드</span>}
                      {s.dietPlan && <span className="text-[9px] font-bold px-2 py-0.5 bg-rose-50 text-rose-600 rounded-full border border-rose-100">식단 포함</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {(activeTab === 'map' || activeTab === 'report') && (
           <div className="py-20 text-center opacity-30"><span className="text-6xl mb-4 block">🌳</span><p className="font-gaegu text-xl">더 풍성한 숲을 만들고 있어요</p></div>
        )}
      </main>

      {/* Nav */}
      <nav className="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-white/95 backdrop-blur-md border-t border-emerald-50 flex justify-around p-3 pb-8 z-50 shadow-lg">
        <button onClick={() => { setActiveTab('home'); setShowResult(false); }} className={`flex flex-col items-center gap-1 ${activeTab === 'home' && !showResult ? 'text-emerald-600 font-bold scale-110' : 'text-slate-300'}`}>
          <span className="text-xl">🏠</span><span className="text-[10px]">홈</span>
        </button>
        <button onClick={() => { setActiveTab('stack'); setShowResult(false); }} className={`flex flex-col items-center gap-1 ${activeTab === 'stack' && !showResult ? 'text-emerald-600 font-bold scale-110' : 'text-slate-300'}`}>
          <span className="text-xl">📋</span><span className="text-[10px]">내 스택</span>
        </button>
        <button onClick={() => setActiveTab('map')} className={`flex flex-col items-center gap-1 ${activeTab === 'map' ? 'text-emerald-600 font-bold' : 'text-slate-300'}`}><span className="text-xl">📍</span><span className="text-[10px]">동네 약국</span></button>
        <button onClick={() => setActiveTab('report')} className={`flex flex-col items-center gap-1 ${activeTab === 'report' ? 'text-emerald-600 font-bold' : 'text-slate-300'}`}><span className="text-xl">📊</span><span className="text-[10px]">건강 리포트</span></button>
      </nav>

      {/* Analysis Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-white/98 backdrop-blur-xl z-[100] flex flex-col items-center justify-center px-10 text-center">
          <div className="relative w-24 h-24 mb-10">
            <div className="absolute inset-0 border-4 border-emerald-50 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center text-4xl">🌿</div>
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2 font-gaegu text-2xl">건강 정보를 살피고 있어요</h3>
          <p className="text-emerald-600 font-gaegu text-2xl tracking-tight">{loadingStep}</p>
        </div>
      )}
    </div>
  );
};

const root = createRoot(document.getElementById('root')!);
root.render(<App />);
