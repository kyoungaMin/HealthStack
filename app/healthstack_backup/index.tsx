import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { GoogleGenAI, Modality } from "@google/genai";

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

// --- App Component ---

// Backend API 응답 타입
interface Ingredient {
  rep_code: string;
  modern_name: string;
  rationale_ko: string;
  direction: string;
  evidence_level: string;
  pubmed_papers: { pmid: string; title: string; journal: string; pub_year: number; url: string }[];
  youtube_video: { video_id: string; title: string; channel: string; thumbnail_url: string; url: string } | null;
  tip: string;
}

interface BackendResponse {
  symptom_summary: string;
  confidence_level: 'high' | 'medium' | 'general';
  source: 'database' | 'similarity' | 'ai_generated';
  ingredients: Ingredient[];
  cautions: string[];
  matched_symptom_name: string | null;
  disclaimer: string;
}

const BACKEND_URL = 'http://localhost:8000';

const App = () => {
  const [activeTab, setActiveTab] = useState<'home' | 'stack' | 'map' | 'report'>('home');
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<string | null>(null);
  const [backendResult, setBackendResult] = useState<BackendResponse | null>(null);
  const [groundingLinks, setGroundingLinks] = useState<{ title: string, uri: string }[]>([]);
  const [recommendedVideos, setRecommendedVideos] = useState<{ title: string, uri: string }[]>([]);
  const [userInput, setUserInput] = useState('');
  const [userLocation, setUserLocation] = useState<{ lat: number, lng: number } | null>(null);
  const [showResult, setShowResult] = useState(false);

  const audioContextRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
      });
    }
  }, []);

  const initAudio = () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
    }
  };

  const handleAnalysis = async (query: string) => {
    if (!query.trim()) return;
    setLoading(true);
    setAnalysisResult(null);
    setBackendResult(null);
    setGroundingLinks([]);
    setRecommendedVideos([]);
    setShowResult(false);

    try {
      // 1. 백엔드 API 호출 (DB 기반 분석)
      const backendRes = await fetch(`${BACKEND_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptom: query })
      });

      if (backendRes.ok) {
        const data: BackendResponse = await backendRes.json();
        setBackendResult(data);

        // YouTube 영상 정보 추출
        const videos = data.ingredients
          .filter(ing => ing.youtube_video)
          .map(ing => ({
            title: ing.youtube_video!.title,
            uri: ing.youtube_video!.url
          }));
        setRecommendedVideos(videos);

        // PubMed 논문 링크 추출
        const papers = data.ingredients
          .flatMap(ing => ing.pubmed_papers)
          .slice(0, 3)
          .map(p => ({ title: p.title, uri: p.url }));
        setGroundingLinks(papers);

        // DB 매칭 결과가 있으면 직접 표시
        if (data.source !== 'ai_generated' && data.ingredients.length > 0) {
          const summary = `${data.symptom_summary}\n\n🥬 **동의보감 추천 식재료**\n${data.ingredients.map(ing =>
            `• **${ing.modern_name}**: ${ing.rationale_ko}\n  💡 ${ing.tip}`
          ).join('\n\n')}\n\n${data.disclaimer}`;
          setAnalysisResult(summary);
          setShowResult(true);
          return;
        }
      }

      // 2. AI Fallback (DB에 없는 경우)
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: `사용자의 증상이나 질문: "${query}". 
        이 내용을 바탕으로 (1) 현재 상태를 친절하게 설명해주고, 
        (2) 현대 의학적 주의사항과 (3) 동의보감 기반 도움이 되는 구체적인 식재료 2-3개를 추천해줘. 
        말투는 아주 따뜻한 이웃집 약사처럼 해줘. 
        답변은 3~4개의 섹션으로 나누어서 작성해줘.`,
        config: {
          tools: [{ googleSearch: {} }]
        }
      });

      const text = response.text;
      setAnalysisResult(text);
      setShowResult(true);

      // Extract links from analysis
      const chunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks;
      if (chunks) {
        const links = chunks
          .filter(c => c.web)
          .map(c => ({ title: c.web!.title, uri: c.web!.uri }));
        setGroundingLinks(links);
      }

    } catch (error) {
      console.error(error);
      setAnalysisResult("앗, 정보를 불러오는 중에 작은 문제가 생겼어요. 다시 한번 말씀해 주시겠어요?");
      setShowResult(true);
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = () => {
    setAnalysisResult(`안녕하세요! 속이 더부룩하고 어지러우시군요. 복용 중인 혈압약 때문에 가끔 그럴 수 있어요.

🩺 **현재 상태 이해**
혈압약 성분이 혈관을 확장하면서 일시적으로 소화기관으로 가는 혈류에 변화를 줄 수 있습니다. 걱정하실 정도는 아니지만, 갑자기 일어날 때 주의가 필요해요.

⚠️ **주의사항**
식사 후 바로 눕지 마시고, 30분 정도 가벼운 산책을 권해드려요. 어지러움이 심해지면 주치의와 상담해보시는 것이 좋습니다.

🥬 **동의보감 생활 가이드**
동의보감에서는 이런 증상에 '무'와 '생강'을 권장합니다. 무는 천연 소화제 역할을 하고, 생강은 속의 냉기를 몰아내 어지러움을 완화하는 데 도움을 줍니다.

📍 **추천 선택지**
근처에 소화가 편한 '죽 전문점'이나 '한식당'을 지도에서 찾아보시는 건 어떨까요?`);
    setGroundingLinks([
      { title: "약물 부작용 정보 센터", uri: "#" },
      { title: "동의보감 식이요법 가이드", uri: "#" }
    ]);
    setRecommendedVideos([
      { title: "속이 편해지는 무나물 맛있게 만드는 법", uri: "https://www.youtube.com/results?search_query=무나물+레시피" },
      { title: "몸을 따뜻하게 하는 생강청 만들기", uri: "https://www.youtube.com/results?search_query=생강청+만들기" }
    ]);
    setShowResult(true);
  };

  const speakResult = async (text: string) => {
    initAudio();
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const response = await ai.models.generateContent({
        model: "gemini-2.5-flash-preview-tts",
        contents: [{ parts: [{ text }] }],
        config: {
          responseModalities: [Modality.AUDIO],
          speechConfig: {
            voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Kore' } },
          },
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
    <div className="flex flex-col h-screen max-w-md mx-auto bg-[#f8fafc] shadow-2xl overflow-hidden relative border-x border-gray-100">

      {/* Header */}
      <header className="p-6 bg-white flex items-center justify-between border-b border-slate-100 sticky top-0 z-50">
        <div>
          <h1 className="text-xl font-bold text-emerald-600 flex items-center gap-2">
            <span className="text-2xl">🌱</span> Health Stack
          </h1>
          <p className="text-[10px] text-slate-400 font-medium tracking-wider">내 몸을 위한 친절한 설명서</p>
        </div>
        <button onClick={() => { setAnalysisResult(null); setShowResult(false); setActiveTab('home'); }} className="text-slate-400 text-sm font-medium">초기화</button>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-5 pb-32">

        {activeTab === 'home' && !showResult && (
          <div className="space-y-6 animate-in">
            <div className="gradient-bg p-8 rounded-[40px] text-white shadow-xl shadow-emerald-100 relative overflow-hidden">
              <div className="relative z-10">
                <h2 className="text-3xl font-gaegu font-bold mb-3">반가워요! 👋</h2>
                <p className="text-emerald-50 opacity-95 leading-relaxed text-lg">
                  오늘 몸 상태는 어떠신가요?<br />
                  사소한 증상이라도 괜찮아요.<br />
                  제가 찬찬히 들어드릴게요.
                </p>
              </div>
              <div className="absolute -bottom-6 -right-6 text-9xl opacity-10 rotate-12">🌿</div>
            </div>

            <div className="health-card p-6 border-2 border-emerald-50">
              <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                지금 궁금한 점을 적어주세요
              </h3>
              <div className="space-y-4">
                <textarea
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  placeholder="예: 혈압약을 먹고 있는데 자꾸 어지러워요."
                  className="w-full h-32 bg-slate-50 border-none rounded-2xl p-4 text-slate-700 focus:ring-2 focus:ring-emerald-500 outline-none resize-none placeholder:text-slate-300"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => handleAnalysis(userInput)}
                    disabled={loading || !userInput}
                    className="flex-1 gradient-bg text-white font-bold py-4 rounded-2xl shadow-lg disabled:opacity-50 transition-all hover:brightness-110 active:scale-[0.98]"
                  >
                    {loading ? '기록을 읽는 중...' : '분석 시작하기'}
                  </button>
                  <button
                    onClick={handleDemo}
                    className="px-4 bg-slate-100 text-slate-500 rounded-2xl font-bold hover:bg-slate-200 transition-colors"
                  >
                    💡 예시
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-4 bg-orange-50 rounded-3xl border border-orange-100">
                <span className="text-orange-400 font-bold text-xs block mb-1">TIP</span>
                <p className="text-[11px] text-orange-700 leading-tight">처방전 사진을 찍어 올리면 더 정확한 분석이 가능해요!</p>
              </div>
              <div className="p-4 bg-blue-50 rounded-3xl border border-blue-100">
                <span className="text-blue-400 font-bold text-xs block mb-1">INFO</span>
                <p className="text-[11px] text-blue-700 leading-tight">근처 약국 위치가 궁금하면 지도 탭을 눌러보세요.</p>
              </div>
            </div>
          </div>
        )}

        {/* Improved Analysis Result Screen */}
        {showResult && analysisResult && (
          <div className="space-y-5 animate-in">
            <div className="flex items-center gap-2 mb-2">
              <button
                onClick={() => setShowResult(false)}
                className="w-8 h-8 rounded-full bg-white flex items-center justify-center text-slate-400 shadow-sm border border-slate-100"
              >
                ←
              </button>
              <h2 className="font-bold text-slate-800">오늘의 내 몸 리포트</h2>
            </div>

            <div className="health-card overflow-hidden">
              <div className="p-6 bg-emerald-50/50 border-b border-emerald-100 flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">👩‍⚕️</span>
                  <div>
                    <h3 className="font-bold text-emerald-800">이웃집 약사의 소견</h3>
                    <div className="flex items-center gap-2 mt-1">
                      {backendResult && (
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${backendResult.source === 'database'
                            ? 'bg-emerald-100 text-emerald-700'
                            : backendResult.source === 'similarity'
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-amber-100 text-amber-700'
                          }`}>
                          {backendResult.source === 'database' && '🔬 동의보감 근거'}
                          {backendResult.source === 'similarity' && '📊 유사 증상 기반'}
                          {backendResult.source === 'ai_generated' && '💡 AI 분석'}
                        </span>
                      )}
                      {!backendResult && <span className="text-[10px] text-emerald-600">친절한 설명과 주의사항을 확인하세요</span>}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => speakResult(analysisResult)}
                  className="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow-sm text-emerald-500 hover:scale-110 transition-transform"
                  title="음성으로 듣기"
                >
                  🔊
                </button>
              </div>

              <div className="p-6 space-y-6">
                <div className="text-slate-700 text-[15px] leading-relaxed whitespace-pre-wrap">
                  {analysisResult}
                </div>

                {/* Recommended Videos Section */}
                {recommendedVideos.length > 0 && (
                  <div className="pt-6 border-t border-slate-100">
                    <h4 className="text-xs font-bold text-slate-500 mb-4 flex items-center gap-2">
                      <span className="text-red-500">▶</span> 추천 식재료 활용 영상
                    </h4>
                    <div className="grid gap-3">
                      {recommendedVideos.map((video, i) => (
                        <a
                          key={i}
                          href={video.uri}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-3 p-3 bg-slate-50 rounded-2xl hover:bg-red-50 transition-colors border border-transparent hover:border-red-100 group"
                        >
                          <div className="w-14 h-10 bg-slate-200 rounded-lg flex items-center justify-center text-slate-400 group-hover:bg-red-200 group-hover:text-red-500 transition-colors">
                            <span className="text-lg">▶</span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-bold text-slate-700 truncate group-hover:text-red-700">{video.title}</p>
                            <p className="text-[10px] text-slate-400">유튜브에서 보기</p>
                          </div>
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {groundingLinks.length > 0 && (
                  <div className="pt-6 border-t border-slate-100">
                    <h4 className="text-xs font-bold text-slate-400 mb-4 flex items-center gap-1 uppercase tracking-widest">
                      참고 자료
                    </h4>
                    <div className="grid gap-2">
                      {groundingLinks.map((link, i) => (
                        <a
                          key={i}
                          href={link.uri}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-3 bg-slate-50 rounded-xl flex items-center justify-between group hover:bg-emerald-50 transition-colors"
                        >
                          <span className="text-xs text-slate-600 font-medium group-hover:text-emerald-700 truncate pr-4">{link.title}</span>
                          <span className="text-slate-300 group-hover:text-emerald-400 text-xs">↗</span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Actions after result */}
            <div className="flex flex-col gap-3">
              <button
                onClick={() => setActiveTab('map')}
                className="w-full bg-blue-600 text-white font-bold py-4 rounded-2xl shadow-lg flex items-center justify-center gap-2"
              >
                📍 근처 건강 식당 & 약국 찾기
              </button>
              <button
                onClick={() => { setShowResult(false); setUserInput(''); setRecommendedVideos([]); }}
                className="w-full bg-white text-emerald-600 border-2 border-emerald-100 font-bold py-4 rounded-2xl"
              >
                다른 증상 물어보기
              </button>
            </div>

            <p className="text-[10px] text-slate-400 text-center px-4 py-2">
              ※ 이 정보는 참고용이며, 의학적 진단을 대신할 수 없습니다. 증상이 심각할 경우 반드시 전문의를 찾아주세요.
            </p>
          </div>
        )}

        {/* Existing Tab Contents */}
        {activeTab === 'map' && !showResult && (
          <div className="space-y-4 animate-in">
            <div className="health-card p-6 bg-blue-50/30 border-blue-100">
              <h2 className="text-xl font-bold text-blue-800 mb-2">내 주변 건강 찾기 📍</h2>
              <p className="text-sm text-blue-600 mb-6">현재 위치를 기반으로 증상에 좋은 식당과 약국을 찾아드릴게요.</p>
              <button
                onClick={async () => {
                  setLoading(true);
                  try {
                    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
                    const response = await ai.models.generateContent({
                      model: "gemini-2.5-flash",
                      contents: "내 주변에 건강한 한식이나 죽집, 혹은 약국이 어디에 있니?",
                      config: {
                        tools: [{ googleMaps: {} }],
                        toolConfig: {
                          retrievalConfig: { latLng: userLocation || { latitude: 37.5665, longitude: 126.9780 } }
                        }
                      },
                    });
                    setAnalysisResult(response.text);
                    setShowResult(true);
                  } catch (e) { } finally { setLoading(false); }
                }}
                className="w-full bg-blue-600 text-white font-bold py-4 rounded-2xl shadow-md active:scale-[0.98] transition-all"
              >
                {loading ? '지도를 펼치는 중...' : '주변 추천지 검색'}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'stack' && !showResult && (
          <div className="space-y-4 animate-in text-center py-12">
            <div className="w-24 h-24 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-5xl">📦</span>
            </div>
            <h2 className="text-xl font-bold text-slate-800">나의 복용 스택</h2>
            <p className="text-slate-500 text-sm leading-relaxed">
              아직 등록된 약이나 영양제가 없어요.<br />
              처방전을 등록하면 복용 일정을 관리해 드려요.
            </p>
            <button className="mt-6 px-8 py-3 bg-emerald-500 text-white font-bold rounded-full shadow-lg shadow-emerald-100">처방전 등록하기</button>
          </div>
        )}

      </main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-white/90 backdrop-blur-lg border-t border-slate-100 flex justify-around p-3 pb-8 z-50">
        <button onClick={() => { setActiveTab('home'); setShowResult(false); }} className={`flex flex-col items-center gap-1 transition-all ${activeTab === 'home' ? 'nav-active' : 'text-slate-300'}`}>
          <span className="text-xl">🏠</span>
          <span className="text-[10px]">홈</span>
        </button>
        <button onClick={() => { setActiveTab('stack'); setShowResult(false); }} className={`flex flex-col items-center gap-1 transition-all ${activeTab === 'stack' ? 'nav-active' : 'text-slate-300'}`}>
          <span className="text-xl">📋</span>
          <span className="text-[10px]">내 스택</span>
        </button>
        <button onClick={() => { setActiveTab('map'); setShowResult(false); }} className={`flex flex-col items-center gap-1 transition-all ${activeTab === 'map' ? 'nav-active' : 'text-slate-300'}`}>
          <span className="text-xl">📍</span>
          <span className="text-[10px]">지도</span>
        </button>
        <button onClick={() => { setActiveTab('report'); setShowResult(false); }} className={`flex flex-col items-center gap-1 transition-all ${activeTab === 'report' ? 'nav-active' : 'text-slate-300'}`}>
          <span className="text-xl">📊</span>
          <span className="text-[10px]">리포트</span>
        </button>
      </nav>

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-white/70 backdrop-blur-[4px] z-[100] flex flex-col items-center justify-center px-10 text-center">
          <div className="relative w-20 h-20 mb-6">
            <div className="absolute inset-0 border-4 border-emerald-100 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
          <h3 className="text-xl font-bold text-emerald-800 mb-2">분석하고 있어요</h3>
          <p className="text-emerald-600 font-gaegu text-lg leading-tight">
            당신의 건강 기록과 어울리는<br />영상을 찾고 있습니다. 잠시만요!
          </p>
        </div>
      )}
    </div>
  );
};

const root = createRoot(document.getElementById('root')!);
root.render(<App />);