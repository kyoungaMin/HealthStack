import React, { useState, useEffect, useRef } from 'react';
import { User } from '@supabase/supabase-js';
import { GoogleGenAI, Modality } from '@google/genai';
import { supabase, BACKEND_URL } from './services/supabase';
import { decode, decodeAudioData, blobToBase64 } from './utils/helpers';
import type { AnalysisData, SavedStack } from './types';

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
  const [revealedSections, setRevealedSections] = useState<Set<string>>(new Set());
  const [loadingSectionId, setLoadingSectionId] = useState<string | null>(null);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);

  // --- 동네약국 Map ---
  const mapRef = useRef<HTMLDivElement>(null);
  const naverMapRef = useRef<any>(null);
  const [pharmacies, setPharmacies] = useState<any[]>([]);
  const [loadingPharmacy, setLoadingPharmacy] = useState(false);
  const [selectedPharmacy, setSelectedPharmacy] = useState<any>(null);
  const [locationError, setLocationError] = useState<string>('');

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

  // --- Supabase Auth ---
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setAuthLoading(false);
      if (session?.user) syncStacksFromDB();
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, session) => {
      setUser(session?.user ?? null);
      if (session?.user) syncStacksFromDB();
      else setAuthLoading(false);
    });
    return () => subscription.unsubscribe();
  }, []);

  const syncStacksFromDB = async () => {
    const { data, error } = await supabase
      .from('prescription_records')
      .select('*')
      .order('created_at', { ascending: false });
    if (error) { console.error('DB 동기화 오류:', error); return; }
    if (data) {
      setSavedStacks(data.map((r: any) => ({
        id: r.id,
        date: new Date(r.created_at).toLocaleString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
        drugList: r.drug_list ?? [],
        data: r.analysis_data,
        videos: r.videos ?? undefined,
        dietPlan: r.diet_plan ?? undefined,
        selectedSections: r.revealed_sections ?? [],
      })));
    }
  };

  const saveStackToDB = async (entry: SavedStack) => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.user) return;
    await supabase.from('prescription_records').insert({
      user_id: session.user.id,
      drug_list: entry.drugList,
      analysis_data: entry.data,
      revealed_sections: entry.selectedSections ?? [],
    });
  };

  const deleteStackFromDB = async (id: string) => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.user) return;
    await supabase.from('prescription_records').delete().eq('id', id);
  };

  // --- 동네약국 지도 초기화 (Kakao Maps) ---
  const initPharmacyMap = () => {
    const kakao = (window as any).kakao;
    if (!mapRef.current || !kakao?.maps) {
      setLocationError('카카오 지도가 로드되지 않았습니다. 새로고침 후 다시 시도하세요.');
      return;
    }
    setLocationError('');
    setPharmacies([]);
    setSelectedPharmacy(null);

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude: lat, longitude: lng } = pos.coords;
        const center = new kakao.maps.LatLng(lat, lng);

        // 카카오 지도 초기화 (이미 있으면 중심만 이동)
        if (!naverMapRef.current) {
          naverMapRef.current = new kakao.maps.Map(mapRef.current, {
            center,
            level: 4,
          });
        } else {
          naverMapRef.current.setCenter(center);
        }
        const map = naverMapRef.current;

        // 내 위치 커스텀 오버레이 (파란 원)
        new kakao.maps.CustomOverlay({
          position: center,
          content: '<div style="width:14px;height:14px;background:#3b82f6;border-radius:50%;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3)"></div>',
          map,
        });

        // 약국 검색 (카카오 Places API 사용)
        setLoadingPharmacy(true);
        try {
          const ps = new kakao.maps.services.Places();

          ps.keywordSearch('약국', (result: any, status: any) => {
            if (status === kakao.maps.services.Status.OK) {
              // 거리순으로 정렬 (가까운 순)
              const sortedPlaces = result.sort((a: any, b: any) => {
                const distA = Math.sqrt(Math.pow(Number(a.y) - lat, 2) + Math.pow(Number(a.x) - lng, 2));
                const distB = Math.sqrt(Math.pow(Number(b.y) - lat, 2) + Math.pow(Number(b.x) - lng, 2));
                return distA - distB;
              });

              // 상위 10개만 사용
              const nearbyPlaces = sortedPlaces.slice(0, 10).map((p: any) => ({
                name: p.place_name,
                address: p.road_address_name || p.address_name,
                phone: p.phone || '정보 없음',
                lat: Number(p.y),
                lng: Number(p.x),
                place_url: p.place_url || '',
                distance: Math.round(
                  Math.sqrt(Math.pow(Number(p.y) - lat, 2) + Math.pow(Number(p.x) - lng, 2)) * 111000
                )
              }));

              setPharmacies(nearbyPlaces);

              // 약국 마커
              nearbyPlaces.forEach((p: any, i: number) => {
                const markerPosition = new kakao.maps.LatLng(p.lat, p.lng);
                const contentEl = document.createElement('div');
                contentEl.style.cssText = 'background:#059669;color:white;font-size:10px;font-weight:bold;padding:3px 8px;border-radius:999px;box-shadow:0 2px 6px rgba(0,0,0,0.25);white-space:nowrap;cursor:pointer;line-height:1.4';
                contentEl.textContent = String(i + 1);
                contentEl.onclick = () => setSelectedPharmacy(p);

                new kakao.maps.CustomOverlay({
                  position: markerPosition,
                  content: contentEl,
                  map,
                });
              });
            } else {
              setLocationError('주변 약국을 찾을 수 없습니다.');
            }
            setLoadingPharmacy(false);
          }, {
            location: center,
            radius: 2000, // 2km 반경
            sort: kakao.maps.services.SortBy.DISTANCE
          });
        } catch (err: any) {
          setLocationError(`약국 검색 실패: ${err.message}`);
          setLoadingPharmacy(false);
        }
      },
      () => setLocationError('위치 정보 접근이 거부되었습니다. 브라우저 설정에서 허용해주세요.'),
      { timeout: 10000 }
    );
  };

  useEffect(() => {
    if (activeTab === 'map') {
      // 탭 재진입 시 이전 DOM과 연결된 지도 인스턴스 초기화 (새 DOM에 다시 그리기)
      naverMapRef.current = null;
      setTimeout(initPharmacyMap, 150);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const initAudio = () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setLoadingProgress(5);
    setLoadingStep('소중한 건강 정보를 읽고 있어요...');
    setIsVideosLoaded(false);
    setIsDietLoaded(false);
    setRecommendedVideos([]);
    setDietRecommendation(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('sections', '1,2'); // 항상 Section 1,2만 빠르게 분석

      const response = await fetch(`${BACKEND_URL}/api/v1/analyze/prescription-stream`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok || !response.body) {
        const errText = await response.text();
        throw new Error(`서버 오류 (${response.status}): ${errText}`);
      }

      // SSE 스트림 읽기
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          let event: any;
          try { event = JSON.parse(raw); } catch { continue; }

          if (event.type === 'progress') {
            setLoadingStep(event.message ?? '');
            setLoadingProgress(event.progress ?? 0);
          } else if (event.type === 'result') {
            setLoadingProgress(100);
            const data: AnalysisData = event.data;
            setAnalysisData(data);
            setIsVideosLoaded(true);

            setRevealedSections(new Set()); // 새 분석 시 리셋
            const newEntry: SavedStack = {
              id: Date.now().toString(),
              date: new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
              drugList: data.prescriptionSummary.drugList,
              data: data,
              selectedSections: [],
            };
            setSavedStacks(prev => [newEntry, ...prev]);
            saveStackToDB(newEntry);
            setShowResult(true);
            setActiveTab('home');
          } else if (event.type === 'error') {
            throw new Error(event.message ?? '분석 중 오류가 발생했습니다.');
          }
        }
      }

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
      setLoadingProgress(0);
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
      deleteStackFromDB(id);
    }
  };

  const viewSavedStack = (stack: SavedStack) => {
    setAnalysisData(stack.data);
    setRecommendedVideos(stack.videos || []);
    setDietRecommendation(stack.dietPlan || null);
    setIsVideosLoaded(!!stack.videos);
    setIsDietLoaded(!!stack.dietPlan);
    // 저장된 섹션 정보 복원 (없으면 빈 Set — 결과 화면에서 개별 선택)
    setRevealedSections(new Set(stack.selectedSections ?? []));
    setShowResult(true);
  };

  const fetchSection = async (sectionId: string) => {
    if (!analysisData || loadingSectionId) return;
    // Section 3은 이미 academicEvidence 데이터가 있으므로 즉시 표시
    if (sectionId === '3') {
      setRevealedSections(prev => new Set([...prev, '3']));
      setSavedStacks(prev => prev.map((s, i) =>
        i === 0 ? { ...s, selectedSections: [...(s.selectedSections ?? []), '3'] } : s
      ));
      return;
    }
    setLoadingSectionId(sectionId);
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/analyze/prescription/sections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          drug_list: analysisData.prescriptionSummary.drugList,
          sections: [sectionId],
        }),
      });
      if (!response.ok) throw new Error(`서버 오류 (${response.status})`);
      const sectionData = await response.json();

      // analysisData를 해당 섹션 결과로 업데이트
      setAnalysisData(prev => prev ? { ...prev, ...sectionData } : prev);
      setRevealedSections(prev => new Set([...prev, sectionId]));
      setSavedStacks(prev => {
        const updated = [...prev];
        if (updated[0]) {
          updated[0] = {
            ...updated[0],
            data: { ...updated[0].data, ...sectionData },
            selectedSections: [...(updated[0].selectedSections ?? []), sectionId],
          };
        }
        return updated;
      });
    } catch (err: any) {
      alert(`분석에 실패했습니다.\n${err?.message ?? ''}`);
    } finally {
      setLoadingSectionId(null);
    }
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
            <span className="text-2xl">🌱</span> 내몸설명서 <span className="text-[10px] bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded-full ml-1 font-normal">v3</span>
          </h1>
          <p className="text-[10px] text-emerald-400 font-medium tracking-wider">따뜻한 내 몸 설명서</p>
        </div>
        <div className="flex items-center gap-2">
          {!authLoading && (
            user ? (
              <button onClick={() => supabase.auth.signOut()} className="flex items-center gap-1.5">
                {user.user_metadata?.avatar_url
                  ? <img src={user.user_metadata.avatar_url} className="w-7 h-7 rounded-full border-2 border-emerald-200" />
                  : <span className="w-7 h-7 rounded-full bg-emerald-100 flex items-center justify-center text-sm">👤</span>
                }
                <span className="text-[10px] text-slate-400 hidden sm:inline">로그아웃</span>
              </button>
            ) : (
              <button
                onClick={() => supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: window.location.origin } })}
                className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-full px-3 py-1.5 shadow-sm hover:bg-slate-50 active:scale-95 transition-all"
              >
                <span className="text-sm">🔑</span>
                <span className="text-[10px] font-bold text-slate-600">로그인</span>
              </button>
            )
          )}
          {showResult && (
            <button onClick={() => setShowResult(false)} className="text-amber-600 text-xs font-bold bg-amber-50 px-3 py-1.5 rounded-full hover:bg-amber-100">닫기</button>
          )}
        </div>
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
            {revealedSections.has('3') ? (
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
            ) : (
              <button onClick={() => fetchSection('3')} className="w-full p-5 rounded-[28px] flex items-center gap-4 shadow-sm transition-all bg-white border border-teal-100 hover:border-teal-300 hover:bg-teal-50/30 active:scale-95">
                <div className="w-12 h-12 bg-teal-50 rounded-full flex items-center justify-center text-2xl flex-shrink-0">🔬</div>
                <div className="text-left flex-1">
                  <p className="font-bold text-teal-800 text-sm">학술 근거 보기</p>
                  <p className="text-[10px] text-teal-500 mt-0.5">PubMed 논문 기반 분석 결과</p>
                </div>
                <span className="text-teal-300 text-lg">›</span>
              </button>
            )}

            {/* ═══════════════════════════════════════════════════════ */}
            {/* Section 4 — 생활 가이드 */}
            {/* ═══════════════════════════════════════════════════════ */}
            {revealedSections.has('4') ? (
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
            ) : loadingSectionId === '4' ? (
              <div className="w-full p-5 rounded-[28px] flex items-center gap-4 bg-white border border-purple-100">
                <div className="w-12 h-12 bg-purple-50 rounded-full flex items-center justify-center flex-shrink-0">
                  <div className="w-5 h-5 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
                </div>
                <div>
                  <p className="font-bold text-purple-800 text-sm">생활 가이드 분석 중...</p>
                  <p className="text-[10px] text-purple-400 mt-0.5">식습관·복약 주의사항 생성 중</p>
                </div>
              </div>
            ) : (
              <button onClick={() => fetchSection('4')} className="w-full p-5 rounded-[28px] flex items-center gap-4 shadow-sm transition-all bg-white border border-purple-100 hover:border-purple-300 hover:bg-purple-50/30 active:scale-95">
                <div className="w-12 h-12 bg-purple-50 rounded-full flex items-center justify-center text-2xl flex-shrink-0">💡</div>
                <div className="text-left flex-1">
                  <p className="font-bold text-purple-800 text-sm">생활 가이드 불러오기</p>
                  <p className="text-[10px] text-purple-400 mt-0.5">식습관·복약 주의사항 분석</p>
                </div>
                <span className="text-purple-200 text-lg">›</span>
              </button>
            )}

            {/* ═══════════════════════════════════════════════════════ */}
            {/* Section 5 — 동의보감 추천 */}
            {/* ═══════════════════════════════════════════════════════ */}
            {revealedSections.has('5') ? (
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
          ) : loadingSectionId === '5' ? (
            <div className="w-full p-5 rounded-[28px] flex items-center gap-4 bg-white border border-amber-100">
              <div className="w-12 h-12 bg-amber-50 rounded-full flex items-center justify-center flex-shrink-0">
                <div className="w-5 h-5 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
              </div>
              <div>
                <p className="font-bold text-amber-800 text-sm">동의보감 분석 중...</p>
                <p className="text-[10px] text-amber-400 mt-0.5">한방 식재료·처방 매핑 중</p>
              </div>
            </div>
          ) : (
            <button onClick={() => fetchSection('5')} className="w-full p-5 rounded-[28px] flex items-center gap-4 shadow-sm transition-all bg-white border border-amber-100 hover:border-amber-300 hover:bg-amber-50/30 active:scale-95">
              <div className="w-12 h-12 bg-amber-50 rounded-full flex items-center justify-center text-2xl flex-shrink-0">📜</div>
              <div className="text-left flex-1">
                <p className="font-bold text-amber-800 text-sm">동의보감 추천 불러오기</p>
                <p className="text-[10px] text-amber-400 mt-0.5">한방 식재료·처방 매핑</p>
              </div>
              <span className="text-amber-200 text-lg">›</span>
            </button>
          )}

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

            {!user && (
              <div className="bg-emerald-50 rounded-2xl p-4 border border-dashed border-emerald-200 text-center">
                <p className="text-xs text-emerald-700 font-bold mb-1">☁️ 클라우드 동기화</p>
                <p className="text-[10px] text-slate-400 mb-3">로그인하면 기록이 DB에 저장되어<br/>어느 기기에서든 볼 수 있어요</p>
                <button
                  onClick={() => supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: window.location.origin } })}
                  className="text-[10px] font-bold text-white bg-emerald-500 px-4 py-2 rounded-full hover:bg-emerald-600 active:scale-95 transition-all"
                >
                  구글로 시작하기
                </button>
              </div>
            )}
            
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
                    <h4 className="font-bold text-slate-800 text-sm leading-snug mb-2 break-keep">{s.drugList.join(', ')}</h4>
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

        {activeTab === 'map' && (
          <div className="flex flex-col" style={{ height: 'calc(100vh - 140px)' }}>
            {/* 지도 영역 */}
            <div className="relative flex-shrink-0" style={{ height: '260px' }}>
              <div ref={mapRef} className="w-full h-full bg-slate-100" />
              {/* 지도 로딩 전 또는 에러 */}
              {!naverMapRef.current && !locationError && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-50">
                  <div className="w-7 h-7 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mb-3" />
                  <p className="text-xs text-slate-400">위치를 파악하고 있어요...</p>
                </div>
              )}
              {locationError && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-50 px-6 text-center">
                  <p className="text-3xl mb-2">📍</p>
                  <p className="text-sm text-slate-500">{locationError}</p>
                  <button
                    onClick={initPharmacyMap}
                    className="mt-3 text-xs font-bold text-emerald-600 border border-emerald-200 rounded-full px-4 py-1.5"
                  >다시 시도</button>
                </div>
              )}
            </div>

            {/* 약국 리스트 */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
              <div className="flex justify-between items-center mb-1">
                <h3 className="text-sm font-bold text-emerald-800">
                  📍 주변 약국 {loadingPharmacy ? '검색 중...' : `${pharmacies.length}곳`}
                </h3>
                <button
                  onClick={initPharmacyMap}
                  className="text-[10px] text-emerald-500 font-bold border border-emerald-100 rounded-full px-2.5 py-0.5"
                >새로고침</button>
              </div>

              {loadingPharmacy && (
                <div className="flex items-center gap-3 py-6 justify-center">
                  <div className="w-5 h-5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                  <p className="text-sm text-slate-400">주변 약국 검색 중...</p>
                </div>
              )}

              {!loadingPharmacy && pharmacies.map((p, i) => (
                <div
                  key={i}
                  onClick={() => {
                    setSelectedPharmacy(p);
                    const kakao = (window as any).kakao;
                    if (naverMapRef.current && kakao?.maps) {
                      naverMapRef.current.panTo(new kakao.maps.LatLng(p.lat, p.lng));
                    }
                  }}
                  className={`bg-white p-4 rounded-2xl border shadow-sm cursor-pointer transition-all ${selectedPharmacy === p ? 'border-emerald-400 bg-emerald-50/30' : 'border-slate-100 hover:border-emerald-200'}`}
                >
                  <div className="flex items-start gap-3">
                    <span className="w-6 h-6 bg-emerald-500 text-white rounded-full text-[10px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-1">
                        <p className="font-bold text-slate-800 text-sm break-keep">{p.name}</p>
                        {p.distance && <span className="text-[10px] text-slate-400 flex-shrink-0">{p.distance}m</span>}
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5 break-keep">{p.address}</p>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        {p.phone && p.phone !== '정보 없음' && (
                          <a
                            href={`tel:${p.phone}`}
                            onClick={(e) => e.stopPropagation()}
                            className="text-[11px] text-emerald-600 font-bold"
                          >📞 {p.phone}</a>
                        )}
                        {p.place_url && (
                          <a
                            href={p.place_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-[11px] text-amber-600 font-bold bg-amber-50 px-2 py-0.5 rounded-full"
                          >🕐 영업시간 확인</a>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {!loadingPharmacy && pharmacies.length === 0 && !locationError && (
                <div className="text-center py-12 text-slate-300">
                  <p className="text-5xl mb-3">💊</p>
                  <p className="text-sm">위치 허용 후 주변 약국을 보여드려요</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'report' && (() => {
          // --- 집계 연산 ---
          const drugFreq: Record<string, number> = {};
          savedStacks.forEach(s => s.drugList.forEach(d => { drugFreq[d] = (drugFreq[d] || 0) + 1; }));
          const topDrugs = Object.entries(drugFreq).sort((a, b) => b[1] - a[1]).slice(0, 5);

          const symptomFreq: Record<string, number> = {};
          savedStacks.forEach(s => (s.data?.lifestyleGuide?.symptomTokens ?? []).forEach(t => {
            symptomFreq[t] = (symptomFreq[t] || 0) + 1;
          }));
          const topSymptoms = Object.entries(symptomFreq).sort((a, b) => b[1] - a[1]).slice(0, 12);

          const seenFoods = new Set<string>();
          const uniqueFoods: { name: string; reason: string }[] = [];
          savedStacks.forEach(s => (s.data?.donguibogam?.foods ?? []).forEach(f => {
            if (!seenFoods.has(f.name)) { seenFoods.add(f.name); uniqueFoods.push(f); }
          }));

          const stacksWithDiet = savedStacks.filter(s => s.dietPlan);
          const totalDrugTypes = Object.keys(drugFreq).length;

          return savedStacks.length === 0 ? (
            <div className="py-20 text-center">
              <div className="text-6xl mb-4 opacity-20">📊</div>
              <p className="text-slate-400 text-sm font-medium">처방전을 분석하면<br/>나만의 건강 리포트가 만들어져요</p>
              <button onClick={() => setActiveTab('home')} className="mt-4 text-[11px] font-bold text-emerald-600 bg-emerald-50 px-4 py-2 rounded-full">홈에서 시작하기</button>
            </div>
          ) : (
            <div className="space-y-6 animate-in pb-10">

              {/* ── 섹션 1: 나의 건강 한눈에 ── */}
              <div className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-[32px] p-6 text-white shadow-lg">
                <p className="text-[10px] font-bold opacity-70 uppercase tracking-widest mb-4">나의 건강 한눈에</p>
                <div className="grid grid-cols-3 gap-2 text-center mb-4">
                  <div className="bg-white/15 rounded-2xl p-3">
                    <p className="text-2xl font-bold">{savedStacks.length}</p>
                    <p className="text-[10px] opacity-80 mt-0.5">총 분석</p>
                  </div>
                  <div className="bg-white/15 rounded-2xl p-3">
                    <p className="text-2xl font-bold">{totalDrugTypes}</p>
                    <p className="text-[10px] opacity-80 mt-0.5">약물 종류</p>
                  </div>
                  <div className="bg-white/15 rounded-2xl p-3">
                    <p className="text-2xl font-bold">{topSymptoms.length}</p>
                    <p className="text-[10px] opacity-80 mt-0.5">확인 증상</p>
                  </div>
                </div>
                <p className="text-[10px] opacity-60 text-center">최근 분석: {savedStacks[0]?.date}</p>
              </div>

              {/* ── 섹션 2: 자주 처방받은 약물 ── */}
              {topDrugs.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="bg-blue-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">TOP</span>
                    <h3 className="text-blue-400 text-[10px] font-bold uppercase tracking-widest">자주 처방받은 약물</h3>
                  </div>
                  <div className="bg-white rounded-[24px] p-4 shadow-sm border border-blue-50 space-y-2">
                    {topDrugs.map(([name, count], i) => (
                      <div key={name} className="flex items-center gap-3">
                        <span className="w-5 h-5 bg-blue-50 text-blue-600 rounded-full text-[10px] font-bold flex items-center justify-center flex-shrink-0">{i + 1}</span>
                        <div className="flex-1">
                          <div className="flex justify-between items-center mb-1">
                            <p className="text-xs font-bold text-slate-700 break-keep">{name}</p>
                            <p className="text-[10px] text-blue-400 font-bold">{count}회</p>
                          </div>
                          <div className="w-full bg-blue-50 rounded-full h-1.5">
                            <div className="bg-blue-400 h-1.5 rounded-full" style={{ width: `${(count / savedStacks.length) * 100}%` }} />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── 섹션 3: 복용 이력 타임라인 ── */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="bg-emerald-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">이력</span>
                  <h3 className="text-emerald-400 text-[10px] font-bold uppercase tracking-widest">복용 이력 타임라인</h3>
                </div>
                <div className="relative pl-4">
                  <div className="absolute left-4 top-0 bottom-0 w-px bg-emerald-100" />
                  <div className="space-y-4">
                    {savedStacks.map((s, i) => (
                      <div key={s.id} className="relative pl-6">
                        <div className="absolute left-0 top-1.5 w-3 h-3 rounded-full border-2 border-emerald-400 bg-white" />
                        <div className="bg-white rounded-[20px] p-4 shadow-sm border border-emerald-50">
                          <p className="text-[10px] text-emerald-400 font-bold mb-1">{s.date}</p>
                          <div className="flex flex-wrap gap-1">
                            {s.drugList.slice(0, 4).map((d, j) => (
                              <span key={j} className="text-[10px] px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-lg font-bold border border-emerald-100">{d}</span>
                            ))}
                            {s.drugList.length > 4 && (
                              <span className="text-[10px] px-2 py-0.5 bg-slate-50 text-slate-400 rounded-lg">+{s.drugList.length - 4}개</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* ── 섹션 4: 자주 나타나는 증상 ── */}
              {topSymptoms.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="bg-purple-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">증상</span>
                    <h3 className="text-purple-400 text-[10px] font-bold uppercase tracking-widest">자주 나타나는 증상</h3>
                  </div>
                  <div className="bg-white rounded-[24px] p-4 shadow-sm border border-purple-50">
                    <div className="flex flex-wrap gap-2">
                      {topSymptoms.map(([token, count]) => (
                        <span key={token} className="px-3 py-1.5 rounded-xl text-[11px] font-bold border"
                          style={{ fontSize: `${Math.min(13, 10 + count)}px`, background: count > 1 ? '#f3f0ff' : '#fafaf9', color: count > 1 ? '#7c3aed' : '#78716c', borderColor: count > 1 ? '#ddd6fe' : '#e7e5e4' }}>
                          {token} {count > 1 && <span className="opacity-60 text-[9px]">×{count}</span>}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* ── 섹션 5: 동의보감 식재료 모음 ── */}
              {uniqueFoods.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="bg-amber-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">식재료</span>
                    <h3 className="text-amber-700 text-[10px] font-bold uppercase tracking-widest">내 몸에 자주 필요한 식재료</h3>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {uniqueFoods.slice(0, 6).map((f, i) => (
                      <div key={i} className="bg-white rounded-[20px] p-4 shadow-sm border border-amber-50">
                        <p className="text-lg mb-1">🌿</p>
                        <p className="text-xs font-bold text-amber-900 break-keep">{f.name}</p>
                        <p className="text-[10px] text-slate-400 mt-1 leading-tight line-clamp-2">{f.reason}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── 섹션 6: AI 레시피 아카이브 ── */}
              {stacksWithDiet.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="bg-rose-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">레시피</span>
                    <h3 className="text-rose-400 text-[10px] font-bold uppercase tracking-widest">AI 레시피 아카이브</h3>
                  </div>
                  <div className="space-y-3">
                    {stacksWithDiet.map((s, i) => (
                      <div key={s.id} className="bg-white rounded-[24px] p-4 shadow-sm border border-rose-50">
                        <p className="text-[10px] text-rose-400 font-bold mb-2">{s.date}</p>
                        <p className="text-[11px] text-slate-600 leading-relaxed line-clamp-3">{s.dietPlan}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <p className="text-[10px] text-slate-400 text-center px-6 leading-relaxed opacity-60">
                ※ 리포트는 기기에 저장된 분석 이력을 기반으로 합니다.
              </p>
            </div>
          );
        })()}
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
          <div className="relative w-24 h-24 mb-8">
            <div className="absolute inset-0 border-4 border-emerald-50 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center text-4xl">🌿</div>
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2 font-gaegu text-2xl">건강 정보를 살피고 있어요</h3>
          <p className="text-emerald-600 font-gaegu text-xl tracking-tight min-h-[28px]">{loadingStep}</p>

          {/* Progress Bar */}
          <div className="w-full max-w-xs mt-5">
            <div className="flex justify-between text-[10px] text-slate-400 mb-1.5">
              <span>⚡ 빠른 분석 모드</span>
              <span className="font-bold text-emerald-500">{loadingProgress}%</span>
            </div>
            <div className="w-full bg-emerald-50 rounded-full h-2 overflow-hidden">
              <div
                className="bg-gradient-to-r from-emerald-400 to-teal-500 h-2 rounded-full transition-all duration-700 ease-out"
                style={{ width: `${loadingProgress}%` }}
              />
            </div>
            {/* 단계 표시 */}
            <div className="flex justify-between mt-2">
              {(['OCR', '병용금기', '약물정보']).map((label, i, arr) => {
                const isActive = loadingProgress >= Math.round(100 / arr.length * i);
                return (
                  <span key={label} className={`text-[9px] font-bold transition-colors ${isActive ? 'text-emerald-500' : 'text-slate-200'}`}>
                    {label}
                  </span>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


export default App;
