import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { GoogleGenerativeAI } from "@google/generative-ai";
import './index.css';

// --- Backend API Types ---
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
  medications?: { 
    name_ko: string; 
    name_en: string; 
    classification: string;
    indication: string;
    common_side_effects: string[];
    interaction_risk: string;
  }[];
  cautions: string[];
  matched_symptom_name: string | null;
  disclaimer: string;
}

interface AnalysisHistory {
  id: string;
  date: string;
  symptom: string;
  result: BackendResponse | null;
  aiSummary: string | null;
}

interface PrescriptionRecord {
  id: string;
  date: string;
  image_url: string;
  hospital_name: string;
  drugs: string[];
}

interface Medication {
  id: string;
  name: string;
  time: string; // "HH:MM" format
  taken: boolean;
}

const BACKEND_URL = 'http://localhost:8000';

// --- Golden Questions Data ---
interface GoldenQuestion {
  id: string;
  category: string;
  q: string;
}

// --- App Component ---

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
  const [goldenQuestions, setGoldenQuestions] = useState<GoldenQuestion[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('전체');
  const [faqPage, setFaqPage] = useState(1);

  const [history, setHistory] = useState<AnalysisHistory[]>(() => {
    try {
      const saved = localStorage.getItem('health-history');
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });

  // Guest ID Init
  const [userId] = useState(() => {
    let id = localStorage.getItem('guest_user_id');
    if (!id) {
      id = 'guest_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('guest_user_id', id);
    }
    return id;
  });

  useEffect(() => {
    localStorage.setItem('health-history', JSON.stringify(history));
  }, [history]);

  const categories = React.useMemo(() => {
    const cats = Array.from(new Set(goldenQuestions.map(q => q.category)));
    return ['전체', ...cats];
  }, [goldenQuestions]);

  const filteredQuestions = selectedCategory === '전체'
    ? goldenQuestions
    : goldenQuestions.filter(q => q.category === selectedCategory);

  const totalFaqPages = Math.ceil(filteredQuestions.length / 5);
  const currentFaqItems = filteredQuestions.slice((faqPage - 1) * 5, faqPage * 5);

  // Medication States
  const [medications, setMedications] = useState<Medication[]>(() => {
    const saved = localStorage.getItem('medications');
    return saved ? JSON.parse(saved) : [];
  });
  const [prescriptionRecords, setPrescriptionRecords] = useState<PrescriptionRecord[]>([]);
  const [selectedPrescriptionId, setSelectedPrescriptionId] = useState<string | null>(null);

  const [newMedName, setNewMedName] = useState('');
  const [newMedTime, setNewMedTime] = useState('');
  const [notificationPermission, setNotificationPermission] = useState(Notification.permission);

  const audioContextRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
      });
    }
    fetch(`${BACKEND_URL}/api/golden-questions`)
      .then(res => res.json())
      .then(data => setGoldenQuestions(data.questions))
      .catch(err => console.error(err));
  }, []);

  // Fetch prescription records when entering stack tab
  useEffect(() => {
    if (activeTab === 'stack') {
      fetch(`${BACKEND_URL}/api/prescriptions?user_id=${userId}`)
        .then(res => res.json())
        .then(data => setPrescriptionRecords(data.prescriptions || []))
        .catch(err => console.error("Failed to fetch prescriptions:", err));
    }
  }, [activeTab, userId]);

  // Save medications to local storage
  useEffect(() => {
    localStorage.setItem('medications', JSON.stringify(medications));
  }, [medications]);

  // Check for notifications every minute
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

      medications.forEach(med => {
        if (med.time === currentTime && !med.taken) {
          if (Notification.permission === 'granted') {
            new Notification('💊 복용 알림', {
              body: `${med.name} 복용할 시간이에요!`,
              icon: '/vite.svg'
            });
          }
        }
      });
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [medications]);

  const requestNotificationPermission = async () => {
    const permission = await Notification.requestPermission();
    setNotificationPermission(permission);
  };

  const addMedication = () => {
    if (!newMedName || !newMedTime) return;
    const newMed: Medication = {
      id: Date.now().toString(),
      name: newMedName,
      time: newMedTime,
      taken: false
    };
    setMedications([...medications, newMed]);
    setNewMedName('');
    setNewMedTime('');
  };

  const toggleMedication = (id: string) => {
    setMedications(medications.map(med =>
      med.id === id ? { ...med, taken: !med.taken } : med
    ));
  };

  const deleteMedication = (id: string) => {
    setMedications(medications.filter(med => med.id !== id));
  };

  const initAudio = () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
    }
  };

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleAnalysisWithImage(file);
    }
  };

  const handleAnalysisWithImage = async (file: File) => {
    setLoading(true);
    setAnalysisResult(null);
    setBackendResult(null);
    setShowResult(false);

    const formData = new FormData();
    formData.append('symptom', userInput);
    formData.append('user_id', userId);
    formData.append('file', file);

    // ★ 추가: 현재 입력된 약물 목록을 JSON으로 전달
    const medNames = medications.map(med => med.name);
    formData.append('medications_json', JSON.stringify(medNames));

    try {
      const res = await fetch(`${BACKEND_URL}/api/analyze-with-image`, {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        const data: BackendResponse = await res.json();
        setBackendResult(data);

        let summary = data.symptom_summary ? (data.symptom_summary + "\n\n") : "";

        if (data.medications && data.medications.length > 0) {
          summary += `💊 **처방약 분석 결과**\n총 ${data.medications.length}개의 약물이 식별되었습니다. 아래에서 상세 정보를 확인하세요.\n\n`;
        }

        if (data.ingredients.length > 0) {
          summary += `🌿 **동의보감 추천 식재료**\n${data.ingredients.map(ing => `👉 **${ing.modern_name}**: ${ing.rationale_ko}`).join('\n')}`;
        }

        setAnalysisResult(summary);

        const newRecord: AnalysisHistory = {
          id: Date.now().toString(),
          date: new Date().toLocaleString(),
          symptom: "📷 처방전 분석",
          result: data,
          aiSummary: summary
        };
        setHistory(prev => [newRecord, ...prev]);

        setShowResult(true);
      }
    } catch (e) {
      console.error(e);
      setAnalysisResult("이미지 분석 중 오류가 발생했습니다.");
      setShowResult(true);
    } finally {
      setLoading(false);
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
      const backendRes = await fetch(`${BACKEND_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptom: query, user_id: userId })
      });

      if (backendRes.ok) {
        const data: BackendResponse = await backendRes.json();
        setBackendResult(data);

        const videos = data.ingredients
          .filter(ing => ing.youtube_video)
          .map(ing => ({
            title: ing.youtube_video!.title,
            uri: ing.youtube_video!.url
          }));
        setRecommendedVideos(videos);

        const papers = data.ingredients
          .flatMap(ing => ing.pubmed_papers)
          .slice(0, 3)
          .map(p => ({ title: p.title, uri: p.url }));
        setGroundingLinks(papers);

        if (data.source !== 'ai_generated' && data.ingredients.length > 0) {
          const summary = `${data.symptom_summary}\n\n🌿 **동의보감 추천 식재료**\n${data.ingredients.map(ing =>
            `👉 **${ing.modern_name}**: ${ing.rationale_ko}\n  💡 ${ing.tip}`
          ).join('\n\n')}\n\n${data.disclaimer}`;
          setAnalysisResult(summary);

          const newRecord: AnalysisHistory = {
            id: Date.now().toString(),
            date: new Date().toLocaleString(),
            symptom: query,
            result: data,
            aiSummary: summary
          };
          setHistory(prev => [newRecord, ...prev]);
          setShowResult(true);
          return;
        }
      }

      const ai = new GoogleGenerativeAI((import.meta as any).env.VITE_API_KEY!);
      const model = ai.getGenerativeModel({ model: "gemini-pro" });
      const result = await model.generateContent(`사용자의 증상이나 질문: "${query}". 
        이 내용을 바탕으로 (1) 현재 상태를 친절하게 설명해주고 
        (2) 현대 의학적 주의사항과 (3) 동의보감 기반 또는 도움이 되는 구체적인 식재료 2-3개를 추천해줘. 
        말투는 아주 따뜻한 이웃집 약사처럼 해줘. 
        답변은 3~4개의 섹션으로 나눠서 작성해줘.`);

      const text = result.response.text();
      setAnalysisResult(text);

      const newRecord: AnalysisHistory = {
        id: Date.now().toString(),
        date: new Date().toLocaleString(),
        symptom: query,
        result: null,
        aiSummary: text
      };
      setHistory(prev => [newRecord, ...prev]);

      setShowResult(true);

    } catch (error) {
      console.error(error);
      setAnalysisResult("🙏 정보를 불러오는 중에 작은 문제가 생겼어요. 다시 한번 말씀해 주시겠어요?");
      setShowResult(true);
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = () => {
    setAnalysisResult(`안녕하세요! 속이 더부룩하고 어지러우시군요. 복용 중인 혈압약 때문일 가능성이 있어 보여요.

💊 **현재 상태 이해**
혈압약 성분이 위장을 자극하면 일시적으로 소화기능으로 가는 혈류에 변화를 줄 수 있습니다. 걱정하실 정도는 아니지만 갑자기 일어서면 더 어지러울 수 있으니 주의가 필요해요.

⚠️ **주의사항**
식사 후 바로 눕지 마시고 30분 정도 가벼운 산책을 권해드려요. 어지러움이 심해지면 주치의와 상담해보시는 것이 좋겠습니다.

🌿 **동의보감 생활 가이드**
동의보감에서는 이런 증상을 '무'와 '생강'을 권장합니다. 무는 천연 소화제 역할을 하고, 생강은 속의 냉기를 몰아내고 위를 편안하게 하는 데 도움이 됩니다.

📍 **추천 선택지**
근처에 소화가 편한 '죽 전문점'이나 '한식'을 지도에서 찾아보시는 건 어떨까요?`);
    setGroundingLinks([
      { title: "약물 부작용 정보 센터", uri: "#" },
      { title: "동의보감 식이요법 가이드", uri: "#" }
    ]);
    setRecommendedVideos([
      { title: "속이 편해지는 무나물 맛있게 만드는 법", uri: "https://www.youtube.com/results?search_query=무나물레시피" },
      { title: "몸을 따뜻하게 하는 생강차 만들기", uri: "https://www.youtube.com/results?search_query=생강차만들기" }
    ]);

    const demoSummary = `안녕하세요! 속이 더부룩하고 어지러우시군요. 복용 중인 혈압약 때문일 가능성이 있어 보여요.

💊 **현재 상태 이해**
혈압약 성분이 위장을 자극하면 일시적으로 소화기능으로 가는 혈류에 변화를 줄 수 있습니다. 걱정하실 정도는 아니지만 갑자기 일어서면 더 어지러울 수 있으니 주의가 필요해요.

⚠️ **주의사항**
식사 후 바로 눕지 마시고 30분 정도 가벼운 산책을 권해드려요. 어지러움이 심해지면 주치의와 상담해보시는 것이 좋겠습니다.

🌿 **동의보감 생활 가이드**
동의보감에서는 이런 증상을 '무'와 '생강'을 권장합니다. 무는 천연 소화제 역할을 하고, 생강은 속의 냉기를 몰아내고 위를 편안하게 하는 데 도움이 됩니다.

📍 **추천 선택지**
근처에 소화가 편한 '죽 전문점'이나 '한식'을 지도에서 찾아보시는 건 어떨까요?`;

    const newRecord: AnalysisHistory = {
      id: Date.now().toString(),
      date: new Date().toLocaleString(),
      symptom: "체험하기 예시",
      result: null,
      aiSummary: demoSummary
    };
    setHistory(prev => [newRecord, ...prev]);

    setShowResult(true);
  };

  const speakResult = async (text: string) => {
    // TTS Placeholder
    console.log("TTS not available in this version");
  };

  return (
    <div className="flex flex-col h-screen max-w-md mx-auto bg-[#f8fafc] shadow-2xl overflow-hidden relative border-x border-gray-100">

      {/* Header */}
      <header className="p-6 bg-white flex items-center justify-between border-b border-slate-100 sticky top-0 z-50">
        <div>
          <h1 className="text-xl font-extrabold text-emerald-600 flex items-center gap-2">
            <span className="text-2xl">⚕️</span> Health Stack
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
                <h2 className="text-3xl font-gaegu font-bold mb-3">반가워요! 민지님</h2>
                <p className="text-emerald-50 opacity-95 leading-relaxed text-lg">
                  오늘 몸 상태는 어떠신가요?<br />
                  사소한 증상이라도 괜찮아요.<br />
                  제가 찬찬히 들어드릴게요.
                </p>
              </div>
              <div className="absolute -bottom-6 -right-6 text-9xl opacity-10 rotate-12">🩺</div>
            </div>

            <div className="health-card p-6 border-2 border-emerald-50">
              <h3 className="font-extrabold text-slate-800 mb-4 flex items-center gap-2">
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



                <div className="flex gap-3">
                  <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={handleFileUpload} />
                  <button
                    onClick={() => {
                      if (!userInput.trim()) {
                        alert("증상을 먼저 말씀해 주시겠어요? ☺️\n어디가 불편하신지 알면 처방전을 더 꼼꼼히 봐드릴 수 있어요! 💕");
                        return;
                      }
                      fileInputRef.current?.click();
                    }}
                    className="px-4 bg-emerald-100 text-emerald-600 font-bold rounded-2xl hover:bg-emerald-200 transition-colors flex items-center gap-2"
                  >
                    <span>📷</span> <span className="text-xs">처방전</span>
                  </button>

                  <button
                    onClick={() => handleAnalysis(userInput)}
                    disabled={!userInput.trim() || loading}
                    className="flex-1 bg-emerald-500 text-white font-bold py-4 rounded-2xl shadow-lg shadow-emerald-200 active:scale-[0.98] transition-all disabled:opacity-50 disabled:shadow-none flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                        분석중...
                      </>
                    ) : '분석 시작하기'}
                  </button>
                  <button
                    onClick={handleDemo}
                    className="px-4 bg-indigo-50 text-indigo-600 font-bold rounded-2xl hover:bg-indigo-100 transition-colors flex items-center gap-1"
                  >
                    <span>✨</span> 체험하기
                  </button>
                </div>
              </div>
            </div>

            {/* Golden Questions List (Bottom) with Pagination */}
            <div className="mt-8 mb-10">
              <h3 className="font-bold text-slate-700 text-sm mb-4 px-2 flex items-center gap-2">
                <span className="text-xl">💡</span> 자주 묻는 질문
              </h3>

              {/* Category Tabs */}
              <div className="flex gap-2 overflow-x-auto pb-4 -mx-2 px-2 snap-x scrollbar-hide mb-2">
                {categories.map((cat, i) => (
                  <button
                    key={i}
                    onClick={() => { setSelectedCategory(cat); setFaqPage(1); }}
                    className={`whitespace-nowrap px-4 py-2 text-xs font-bold rounded-full transition-all flex-shrink-0 snap-start border ${selectedCategory === cat ? 'bg-emerald-600 text-white shadow-md shadow-emerald-200 border-emerald-600' : 'bg-white text-slate-500 border-slate-100'}`}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {/* Questions List */}
              <div className="space-y-3 min-h-[300px]">
                {currentFaqItems.length === 0 ? (
                  <div className="text-center py-10 text-slate-400 text-sm">질문이 없습니다.</div>
                ) : (
                  currentFaqItems.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => { setUserInput(item.q); handleAnalysis(item.q); }}
                      className="w-full text-left p-4 bg-white rounded-2xl shadow-sm border border-slate-100 hover:border-emerald-300 hover:bg-emerald-50/30 hover:shadow-md transition-all active:scale-[0.99] group"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full border border-emerald-100">
                          {item.category}
                        </span>
                        <span className="text-[10px] text-slate-300 font-mono">#{item.id}</span>
                      </div>
                      <p className="text-slate-700 text-[13px] font-medium leading-relaxed group-hover:text-emerald-800 transition-colors">
                        {item.q}
                      </p>
                    </button>
                  ))
                )}
              </div>

              {/* Pagination */}
              {totalFaqPages > 1 && (
                <div className="flex justify-center gap-2 mt-4 pb-4">
                  <button
                    onClick={() => setFaqPage(p => Math.max(1, p - 1))}
                    disabled={faqPage === 1}
                    className="w-10 h-10 rounded-xl bg-white border border-slate-100 text-slate-500 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-50 flex items-center justify-center font-bold"
                  >
                    &lt;
                  </button>
                  <div className="flex items-center justify-center px-4 bg-white rounded-xl border border-slate-100 text-sm font-bold text-slate-600">
                    {faqPage} / {totalFaqPages}
                  </div>
                  <button
                    onClick={() => setFaqPage(p => Math.min(totalFaqPages, p + 1))}
                    disabled={faqPage === totalFaqPages}
                    className="w-10 h-10 rounded-xl bg-white border border-slate-100 text-slate-500 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-50 flex items-center justify-center font-bold"
                  >
                    &gt;
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Analysis Result View */}
        {showResult && (
          <div className="space-y-6 animate-in pb-20">
            <div className="flex items-center justify-between mb-2">
              <button
                onClick={() => { setShowResult(false); setAnalysisResult(null); }}
                className="px-4 py-2 bg-white border border-slate-200 text-slate-600 rounded-xl text-sm font-bold shadow-sm hover:bg-slate-50"
              >
                ← 뒤로
              </button>
              <h2 className="text-lg font-extrabold text-slate-800">분석 결과</h2>
              <div className="w-16"></div>
            </div>

            <div className="health-card overflow-hidden">
              <div className="bg-emerald-50/50 p-4 border-b border-emerald-100 flex justify-between items-center">
                <span className="font-bold text-emerald-800 flex items-center gap-2">
                  <span className="text-xl">🤖</span> AI 건강 분석
                </span>
                <button
                  onClick={() => analysisResult && speakResult(analysisResult)}
                  className="p-2 bg-white rounded-full shadow-sm text-emerald-600 hover:text-emerald-700 active:scale-95 transition-all"
                  title="읽어주기"
                >
                  🔊
                </button>
              </div>
              <div className="p-6 space-y-6">
                <div className="text-slate-700 text-[15px] leading-relaxed whitespace-pre-wrap">
                  {analysisResult}
                </div>

                {/* Medication Info Section */}
                {backendResult?.medications && backendResult.medications.length > 0 && (
                  <div className="mt-6 border-t border-slate-100 pt-6">
                    <h4 className="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
                      <span className="text-lg">💊</span> 복용 약물 정보
                    </h4>
                    <div className="space-y-4">
                      {backendResult.medications.map((med, idx) => (
                        <div key={idx} className="bg-blue-50 rounded-xl p-4 border border-blue-100">
                          <div className="mb-3">
                            <h5 className="font-bold text-blue-900 text-sm">
                              {med.name_ko}
                              {med.name_en && <span className="text-xs text-blue-600 ml-2">({med.name_en})</span>}
                            </h5>
                            <span className="text-[10px] bg-blue-200 text-blue-700 px-2 py-0.5 rounded-full inline-block mt-1">
                              {med.classification || '의약품'}
                            </span>
                          </div>
                          
                          <div className="text-xs text-slate-700 space-y-2 mb-3">
                            {med.indication && (
                              <div>
                                <span className="font-semibold text-blue-900">주요 효능:</span>
                                <p className="text-slate-700 ml-2">{med.indication}</p>
                              </div>
                            )}
                            
                            {med.common_side_effects && med.common_side_effects.length > 0 && (
                              <div>
                                <span className="font-semibold text-red-600">⚠️ 주요 부작용:</span>
                                <ul className="text-slate-700 ml-2 list-disc list-inside">
                                  {med.common_side_effects.map((effect, i) => (
                                    <li key={i}>{effect}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {med.interaction_risk && med.interaction_risk !== 'unknown' && (
                              <div>
                                <span className="font-semibold text-slate-900">상호작용 위험:</span>
                                <span className={`ml-2 px-2 py-0.5 rounded text-xs font-bold ${
                                  med.interaction_risk === 'high' ? 'bg-red-100 text-red-700' :
                                  med.interaction_risk === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                  med.interaction_risk === 'low' ? 'bg-green-100 text-green-700' :
                                  'bg-gray-100 text-gray-700'
                                }`}>
                                  {med.interaction_risk === 'high' ? '높음' :
                                   med.interaction_risk === 'medium' ? '중간' :
                                   med.interaction_risk === 'low' ? '낮음' :
                                   '정보 없음'}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

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
          </div>
        )}

        {/* Existing Tab Contents */}
        {activeTab === 'map' && !showResult && (
          <div className="space-y-4 animate-in">
            <div className="health-card p-6 bg-blue-50/30 border-blue-100">
              <h2 className="text-xl font-bold text-blue-800 mb-2">📍 내 주변 건강 찾기 팁</h2>
              <p className="text-sm text-blue-600 mb-6">현재 위치를 기반으로 증상에 좋은 식당과 약국을 찾아드릴게요.</p>
              <button
                onClick={async () => {
                  setLoading(true);
                  try {
                    const ai = new GoogleGenerativeAI(process.env.API_KEY!);
                    const model = ai.getGenerativeModel({ model: "gemini-1.5-flash" });
                    const result = await model.generateContent("내 주변의 건강한 식당이나 죽집, 혹은 약국이 어디에 있니? (참고: 현재 위치 " + JSON.stringify(userLocation) + ")");
                    const text = result.response.text();
                    setAnalysisResult(text);
                    setShowResult(true);
                  } catch (e) { } finally { setLoading(false); }
                }}
                className="w-full bg-blue-600 text-white font-bold py-4 rounded-2xl shadow-md active:scale-[0.98] transition-all"
              >
                🏥 내 주변 병원/약국 찾기 (AI 검색)
              </button>
            </div>
          </div>
        )}

        {/* Report Tab (History) */}
        {activeTab === 'report' && (
          <div className="space-y-6 animate-in">
            <div className="gradient-bg p-6 rounded-[30px] text-white shadow-lg mb-6">
              <h2 className="text-2xl font-bold mb-2">나의 건강 기록 📋</h2>
              <p className="opacity-90 text-sm">지난 분석 결과를 다시 확인해보세요.</p>
            </div>

            <div className="px-2">
              {history.length === 0 ? (
                <div className="text-center py-20">
                  <div className="text-4xl mb-4 opacity-30">📭</div>
                  <p className="text-slate-400 font-medium">아직 분석 기록이 없어요.<br />증상이나 처방전을 분석해보세요!</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {history.map(item => (
                    <button
                      key={item.id}
                      onClick={() => {
                        setAnalysisResult(item.aiSummary);
                        setBackendResult(item.result);
                        setShowResult(true);
                        setActiveTab('home');
                      }}
                      className="w-full text-left bg-white p-5 rounded-3xl shadow-sm border border-slate-100 hover:border-emerald-200 hover:shadow-md transition-all group relative overflow-hidden"
                    >
                      <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                        <span className="text-xs bg-emerald-100 text-emerald-600 font-bold px-2 py-1 rounded-full">다시 보기 →</span>
                      </div>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-[10px] font-bold text-slate-400 bg-slate-100 px-2 py-1 rounded-full">{item.date.split('.').slice(1, 3).join('.')} {item.date.split(' ')[3]}</span>
                        {item.result?.medications && item.result.medications.length > 0 && (
                          <span className="text-[10px] font-bold text-blue-500 bg-blue-50 px-2 py-1 rounded-full">💊 처방전</span>
                        )}
                      </div>
                      <h3 className="text-slate-800 font-bold text-lg mb-2 truncate pr-16">{item.symptom}</h3>
                      <p className="text-slate-500 text-sm line-clamp-2 leading-relaxed bg-slate-50 p-3 rounded-xl">
                        {item.aiSummary?.replace(/\*\*/g, '').slice(0, 80)}...
                      </p>
                    </button>
                  ))}
                  <button
                    onClick={() => { if (confirm('기록을 모두 삭제하시겠습니까?')) setHistory([]); }}
                    className="w-full py-4 text-xs text-slate-400 underline hover:text-red-400 transition-colors"
                  >
                    기록 전체 삭제
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Medication Management Tab (Stack) */}
        {activeTab === 'stack' && !showResult && (
          <div className="space-y-6 animate-in">
            {/* 알림 권한 배너 */}
            {notificationPermission !== 'granted' && (
              <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-100 flex justify-between items-center">
                <div className="text-xs text-emerald-700">
                  <p className="font-bold">🔔 알림을 켜주세요</p>
                  <p>제 시간에 약을 챙겨드릴게요.</p>
                </div>
                <button
                  onClick={requestNotificationPermission}
                  className="px-3 py-1.5 bg-emerald-500 text-white text-xs font-bold rounded-lg shadow-sm"
                >
                  알림 허용
                </button>
              </div>
            )}

            {/* 처방전 기록 섹션 */}
            <div className="space-y-4">
              <h3 className="font-extrabold text-slate-800 text-lg flex items-center gap-2 px-2">
                <span className="text-xl">📷</span> 나의 처방전 기록
              </h3>

              {prescriptionRecords.length === 0 ? (
                <div className="bg-white rounded-2xl p-6 text-center border border-slate-100 shadow-sm">
                  <p className="text-slate-400 text-sm">저장된 처방전이 없습니다.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {prescriptionRecords.map(record => (
                    <div key={record.id} className="bg-white rounded-2xl border border-emerald-100 shadow-sm overflow-hidden transition-all">
                      <button
                        onClick={() => setSelectedPrescriptionId(selectedPrescriptionId === record.id ? null : record.id)}
                        className="w-full p-4 flex items-center justify-between hover:bg-emerald-50/50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center text-xl">🏥</div>
                          <div className="text-left">
                            <p className="font-bold text-slate-700 text-sm">{record.hospital_name}</p>
                            <p className="text-xs text-slate-400">{record.date}</p>
                          </div>
                        </div>
                        <span className={`text-slate-300 transition-transform ${selectedPrescriptionId === record.id ? 'rotate-180' : ''}`}>▼</span>
                      </button>

                      {selectedPrescriptionId === record.id && (
                        <div className="bg-emerald-50/30 p-4 border-t border-emerald-100 animate-in">
                          <div className="mb-4">
                            <h4 className="text-xs font-bold text-slate-500 mb-2">처방 약물 목록</h4>
                            <div className="flex flex-wrap gap-2">
                              {record.drugs.map((drug, i) => (
                                <span key={i} className="bg-white border border-emerald-200 text-emerald-700 px-2 py-1 rounded-lg text-xs font-bold shadow-sm">
                                  {drug}
                                </span>
                              ))}
                            </div>
                          </div>
                          {record.image_url && (
                            <div className="mt-3">
                              <p className="text-xs font-bold text-slate-500 mb-2">원본 이미지</p>
                              <img src={`${BACKEND_URL}${record.image_url}`} alt="처방전" className="w-full rounded-xl border border-slate-200" />
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="border-t border-slate-200 my-2"></div>

            <div className="health-card p-6">
              <h3 className="font-extrabold text-slate-800 mb-4 flex items-center gap-2">
                <span className="text-xl">💊</span> 새 알림 추가
              </h3>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  value={newMedName}
                  onChange={(e) => setNewMedName(e.target.value)}
                  placeholder="약 이름 (예: 혈압약)"
                  className="flex-1 bg-slate-50 border-none rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                />
                <input
                  type="time"
                  value={newMedTime}
                  onChange={(e) => setNewMedTime(e.target.value)}
                  className="bg-slate-50 border-none rounded-xl px-3 py-3 text-sm focus:ring-2 focus:ring-emerald-500 outline-none w-24"
                />
              </div>
              <button
                onClick={addMedication}
                disabled={!newMedName || !newMedTime}
                className="w-full bg-emerald-500 text-white font-bold py-3 rounded-xl shadow-md disabled:opacity-50 disabled:shadow-none transition-all hover:bg-emerald-600 active:scale-[0.98]"
              >
                추가하기
              </button>
            </div>

            <div className="space-y-3">
              <h3 className="font-bold text-slate-400 text-xs px-2">나의 복용 목록</h3>
              {medications.length === 0 ? (
                <div className="text-center py-10 text-slate-300">
                  <p className="text-4xl mb-2">📭</p>
                  <p className="text-sm">등록된 알림이 없어요</p>
                </div>
              ) : (
                medications.map(med => (
                  <div key={med.id} className={`health-card p-4 flex items-center justify-between transition-all ${med.taken ? 'opacity-60 bg-slate-50' : ''}`}>
                    <div className="flex items-center gap-4">
                      <button
                        onClick={() => toggleMedication(med.id)}
                        className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all ${med.taken ? 'bg-emerald-500 border-emerald-500 text-white' : 'border-slate-200 text-transparent hover:border-emerald-300'}`}
                      >
                        ✓
                      </button>
                      <div>
                        <p className={`font-bold text-slate-800 ${med.taken ? 'line-through text-slate-400' : ''}`}>{med.name}</p>
                        <p className="text-xs text-slate-500 flex items-center gap-1">
                          <span>⏰</span> {med.time}
                        </p>
                      </div>
                    </div>
                    <button onClick={() => deleteMedication(med.id)} className="text-slate-300 hover:text-red-400 p-2 text-sm">삭제</button>
                  </div>
                ))
              )}
            </div>

            <div className="p-4 bg-orange-50 rounded-2xl border border-orange-100 text-[11px] text-orange-700 leading-relaxed">
              <span className="font-bold block mb-1">💡 잊지 마세요!</span>
              약을 드신 후 체크 버튼(○)을 눌러 완료 표시를 해주세요. 기록이 쌓이면 건강 관리에 도움이 됩니다.
            </div>
          </div >
        )}

      </main >

      {/* Bottom Navigation */}
      < nav className="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-white/90 backdrop-blur-lg border-t border-slate-100 flex justify-around p-3 pb-8 z-50" >
        <button onClick={() => { setActiveTab('home'); setShowResult(false); }} className={`flex flex-col items-center gap-1 transition-all ${activeTab === 'home' ? 'nav-active' : 'text-slate-300'}`}>
          <span className="text-xl">🏠</span>
          <span className="text-[10px]">홈</span>
        </button>
        <button onClick={() => { setActiveTab('stack'); setShowResult(false); }} className={`flex flex-col items-center gap-1 transition-all ${activeTab === 'stack' ? 'nav-active' : 'text-slate-300'}`}>
          <span className="text-xl">📋</span>
          <span className="text-[10px]">나의 처방전</span>
        </button>
        <button onClick={() => { setActiveTab('map'); setShowResult(false); }} className={`flex flex-col items-center gap-1 transition-all ${activeTab === 'map' ? 'nav-active' : 'text-slate-300'}`}>
          <span className="text-xl">📍</span>
          <span className="text-[10px]">지도</span>
        </button>
        <button onClick={() => { setActiveTab('report'); setShowResult(false); }} className={`flex flex-col items-center gap-1 transition-all ${activeTab === 'report' ? 'nav-active' : 'text-slate-300'}`}>
          <span className="text-xl">📊</span>
          <span className="text-[10px]">리포트</span>
        </button>
      </nav >

      {/* Loading Overlay */}
      {
        loading && (
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
        )
      }
    </div >
  );
};

const root = createRoot(document.getElementById('root')!);
root.render(<App />);
