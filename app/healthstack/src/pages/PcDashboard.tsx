import React, { useState, useEffect, useRef } from 'react';
import { supabase, BACKEND_URL } from '../services/supabase';
import type { AnalysisData, SavedStack } from '../types';

declare const kakao: any;

// ─── 약국 타입 (place_url 포함) ───
interface Pharmacy {
  name: string;
  address: string;
  phone: string;
  lat: number;
  lng: number;
  distance?: number;
  link?: string;
}

// ─── 색상 팔레트 ───
const PANEL = 'bg-white rounded-2xl border border-slate-100 overflow-hidden';
const PANEL_PAD = 'p-5';
const PANEL_TITLE = 'text-sm font-bold text-slate-700 mb-3 flex items-center gap-2';

// ─── 섹션 패널 공통 헤더 ───
const PanelHeader = ({ icon, title, badge }: { icon: string; title: string; badge?: string }) => (
  <div className="flex items-center justify-between mb-4">
    <h3 className={PANEL_TITLE}>
      <span>{icon}</span> {title}
    </h3>
    {badge && (
      <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-600 font-bold">{badge}</span>
    )}
  </div>
);

// ─── 빈 상태 ───
const EmptyState = ({ icon, text }: { icon: string; text: string }) => (
  <div className="flex flex-col items-center justify-center h-full text-center py-10 text-slate-300">
    <div className="text-4xl mb-3">{icon}</div>
    <p className="text-sm">{text}</p>
  </div>
);

// ─────────────────────────────────────────
// PC Dashboard
// ─────────────────────────────────────────
const PcDashboard = () => {
  // ── Tab ──
  const [activeTab, setActiveTab] = useState<'home' | 'stack' | 'map' | 'report'>('home');

  // ── Auth ──
  const [user, setUser] = useState<any>(null);
  const [authLoading, setAuthLoading] = useState(true);

  // ── 처방전 분석 ──
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── 스택 ──
  const [savedStacks, setSavedStacks] = useState<SavedStack[]>([]);
  const [selectedStack, setSelectedStack] = useState<SavedStack | null>(null);

  // ── 약국 ──
  const mapRef = useRef<HTMLDivElement>(null);
  const kakaoMapRef = useRef<any>(null);
  const [pharmacies, setPharmacies] = useState<Pharmacy[]>([]);
  const [loadingPharmacy, setLoadingPharmacy] = useState(false);
  const [selectedPharmacy, setSelectedPharmacy] = useState<Pharmacy | null>(null);
  const [locationError, setLocationError] = useState('');

  // ────────────────── Auth ──────────────────
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setAuthLoading(false);
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, session) => {
      setUser(session?.user ?? null);
    });
    return () => subscription.unsubscribe();
  }, []);

  // ────────────────── localStorage ──────────────────
  useEffect(() => {
    const stored = localStorage.getItem('health_stacks_v3_warm');
    if (stored) setSavedStacks(JSON.parse(stored));
  }, []);

  useEffect(() => {
    localStorage.setItem('health_stacks_v3_warm', JSON.stringify(savedStacks));
  }, [savedStacks]);

  // ────────────────── 처방전 분석 (SSE) ──────────────────
  const analyzePrescription = async (file: File) => {
    if (!file) return;
    setLoading(true);
    setLoadingStep('분석을 시작합니다...');
    setLoadingProgress(0);
    setAnalysisData(null);
    setSelectedStack(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('sections', '1,2');

      const response = await fetch(`${BACKEND_URL}/api/v1/analyze/prescription-stream`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok || !response.body) {
        throw new Error(`서버 오류 (${response.status})`);
      }

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
            const newEntry: SavedStack = {
              id: Date.now().toString(),
              date: new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
              drugList: data.prescriptionSummary.drugList,
              data,
              selectedSections: [],
            };
            setSavedStacks(prev => [newEntry, ...prev]);
          } else if (event.type === 'error') {
            throw new Error(event.message ?? '분석 오류');
          }
        }
      }
    } catch (err: any) {
      alert(`분석 실패: ${err?.message ?? ''}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFile = (file: File | undefined) => {
    if (!file) return;
    analyzePrescription(file);
  };

  // ────────────────── 약국 지도 ──────────────────
  const initPharmacyMap = () => {
    if (!mapRef.current || kakaoMapRef.current) return;
    if (typeof kakao === 'undefined' || !kakao.maps) {
      setLocationError('카카오 지도를 불러올 수 없습니다.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        const container = mapRef.current!;
        const map = new kakao.maps.Map(container, {
          center: new kakao.maps.LatLng(latitude, longitude),
          level: 4,
        });
        kakaoMapRef.current = map;

        // 내 위치 마커
        new kakao.maps.Marker({
          position: new kakao.maps.LatLng(latitude, longitude),
          map,
          title: '현재 위치',
        });

        // 약국 검색
        setLoadingPharmacy(true);
        try {
          const res = await fetch(`${BACKEND_URL}/api/v1/pharmacies/nearby?lat=${latitude}&lng=${longitude}&radius=2000`);
          const json = await res.json();
          const list: Pharmacy[] = json.items ?? [];
          setPharmacies(list);

          list.forEach((p, i) => {
            const markerPos = new kakao.maps.LatLng(p.lat, p.lng);
            const el = document.createElement('div');
            el.style.cssText = 'background:#059669;color:#fff;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:bold;cursor:pointer;box-shadow:0 2px 6px rgba(0,0,0,0.25);';
            el.textContent = String(i + 1);
            el.onclick = () => setSelectedPharmacy(p);
            new kakao.maps.CustomOverlay({ position: markerPos, content: el, map });
          });
        } catch {
          setLocationError('약국 정보를 불러오지 못했습니다.');
        } finally {
          setLoadingPharmacy(false);
        }
      },
      () => setLocationError('위치 정보를 허용해주세요.'),
    );
  };

  useEffect(() => {
    if (activeTab === 'map') {
      kakaoMapRef.current = null;
      setTimeout(initPharmacyMap, 150);
    }
  }, [activeTab]);

  // ────────────────── 건강 리포트 집계 ──────────────────
  const computeReport = () => {
    const drugFreq: Record<string, number> = {};
    const symptomFreq: Record<string, number> = {};
    const foodFreq: Record<string, number> = {};
    savedStacks.forEach(s => {
      s.drugList.forEach(d => { drugFreq[d] = (drugFreq[d] || 0) + 1; });
      (s.data?.lifestyleGuide?.symptomTokens ?? []).forEach((sym: string) => {
        symptomFreq[sym] = (symptomFreq[sym] || 0) + 1;
      });
      (s.data?.donguibogam?.foods ?? []).forEach((f: any) => {
        foodFreq[f.name] = (foodFreq[f.name] || 0) + 1;
      });
    });
    const topDrugs = Object.entries(drugFreq).sort((a, b) => b[1] - a[1]).slice(0, 5);
    const topSymptoms = Object.entries(symptomFreq).sort((a, b) => b[1] - a[1]).slice(0, 8);
    const topFoods = Object.entries(foodFreq).sort((a, b) => b[1] - a[1]).slice(0, 6);
    const uniqueDrugs = Object.keys(drugFreq).length;
    const uniqueSymptoms = Object.keys(symptomFreq).length;
    const uniqueFoods = Object.keys(foodFreq).length;
    return { topDrugs, topSymptoms, topFoods, uniqueDrugs, uniqueSymptoms, uniqueFoods };
  };

  // ────────────────── Sections fetch ──────────────────
  const fetchSection = async (sectionId: string) => {
    if (!analysisData) return;
    if (sectionId === '3') return; // already loaded inline
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/analyze/prescription/sections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ drug_list: analysisData.prescriptionSummary.drugList, sections: [sectionId] }),
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setAnalysisData(prev => prev ? { ...prev, ...data } : prev);
    } catch {
      alert('섹션 데이터를 불러오지 못했습니다.');
    }
  };

  // ════════════════════════════════════════════════════
  //  RENDER
  // ════════════════════════════════════════════════════
  return (
    <div className="flex h-screen bg-slate-50 font-sans overflow-hidden">

      {/* ── Sidebar ── */}
      <aside className="flex flex-col w-64 flex-shrink-0 bg-white border-r border-slate-100 h-screen">
        {/* Brand */}
        <div className="px-6 py-5 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🌱</span>
            <div>
              <h1 className="text-base font-bold text-emerald-600 leading-tight">내몸설명서</h1>
              <span className="text-[10px] text-emerald-400 font-medium">v3 · PC Dashboard</span>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5">
          {([
            { tab: 'home',   icon: '🏠', label: '처방전 분석', desc: 'OCR + 근거 분석' },
            { tab: 'stack',  icon: '📋', label: '내 스택',     desc: '처방 이력' },
            { tab: 'map',    icon: '📍', label: '동네 약국',   desc: '주변 약국 지도' },
            { tab: 'report', icon: '📊', label: '건강 리포트', desc: '종합 분석' },
          ] as const).map(({ tab, icon, label, desc }) => (
            <button key={tab}
              onClick={() => setActiveTab(tab)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-left ${
                activeTab === tab
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'
              }`}>
              <span className="text-lg flex-shrink-0">{icon}</span>
              <div>
                <p className={`text-sm leading-tight ${activeTab === tab ? 'font-bold' : 'font-medium'}`}>{label}</p>
                <p className="text-[10px] text-slate-400 mt-0.5">{desc}</p>
              </div>
            </button>
          ))}
        </nav>

        {/* Bottom */}
        <div className="p-3 border-t border-slate-100 space-y-1">
          {/* 모바일 버전 링크 */}
          <a href="/"
            className="w-full flex items-center gap-2 text-xs text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-xl px-3 py-2 transition-colors">
            <span>📱</span> 모바일 버전
          </a>
          {/* User auth */}
          {!authLoading && (user ? (
            <button onClick={() => supabase.auth.signOut()}
              className="flex items-center gap-2 w-full hover:bg-slate-50 rounded-xl px-3 py-2 transition-colors">
              {user.user_metadata?.avatar_url
                ? <img src={user.user_metadata.avatar_url} className="w-7 h-7 rounded-full border-2 border-emerald-200 flex-shrink-0" />
                : <span className="w-7 h-7 rounded-full bg-emerald-100 flex items-center justify-center text-sm flex-shrink-0">👤</span>}
              <div className="text-left overflow-hidden">
                <p className="text-xs font-medium text-slate-700 truncate">{user.email}</p>
                <p className="text-[10px] text-slate-400">로그아웃</p>
              </div>
            </button>
          ) : (
            <button
              onClick={() => supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: window.location.origin + '/pc' } })}
              className="flex items-center gap-2 bg-white border border-slate-200 rounded-xl px-3 py-2 hover:bg-slate-50 w-full transition-colors">
              <span className="text-sm">🔑</span>
              <span className="text-xs font-medium text-slate-600">Google로 로그인</span>
            </button>
          ))}
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="flex flex-col flex-1 min-w-0 h-screen">

        {/* Top header bar */}
        <header className="flex items-center justify-between px-6 py-4 bg-white border-b border-slate-100 flex-shrink-0">
          <div>
            <h2 className="text-lg font-bold text-slate-800">
              {activeTab === 'home'   && '처방전 분석'}
              {activeTab === 'stack'  && '내 스택'}
              {activeTab === 'map'    && '동네 약국'}
              {activeTab === 'report' && '건강 리포트'}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              {activeTab === 'home'   && '처방전 사진을 업로드하면 AI가 약물 정보와 동의보감을 분석합니다'}
              {activeTab === 'stack'  && `총 ${savedStacks.length}개의 처방 이력`}
              {activeTab === 'map'    && '현재 위치 기준 반경 2km 내 약국'}
              {activeTab === 'report' && '누적 처방 데이터 기반 건강 분석'}
            </p>
          </div>
          {activeTab === 'home' && analysisData && (
            <button
              onClick={() => { setAnalysisData(null); setSelectedStack(null); }}
              className="text-xs font-bold text-slate-500 bg-slate-100 hover:bg-slate-200 px-4 py-2 rounded-xl transition-colors">
              ← 새 처방전 분석
            </button>
          )}
        </header>

        {/* Content area */}
        <main className="flex-1 overflow-hidden">

          {/* ─────────── 홈: 처방전 분석 ─────────── */}
          {activeTab === 'home' && (
            <div className="h-full">
              {/* Loading */}
              {loading && (
                <div className="h-full flex flex-col items-center justify-center bg-white">
                  <div className="w-14 h-14 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-6" />
                  <h3 className="text-lg font-bold text-slate-800 mb-2">건강 정보를 분석하고 있어요</h3>
                  <p className="text-emerald-600 text-sm mb-6">{loadingStep}</p>
                  <div className="w-72">
                    <div className="flex justify-between text-xs text-slate-400 mb-1.5">
                      <span>분석 진행률</span>
                      <span className="font-bold text-emerald-500">{loadingProgress}%</span>
                    </div>
                    <div className="w-full bg-emerald-50 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-emerald-400 to-teal-500 h-2 rounded-full transition-all duration-700"
                        style={{ width: `${loadingProgress}%` }}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Upload screen */}
              {!loading && !analysisData && (
                <div className="h-full flex items-center justify-center p-8">
                  <div className="w-full max-w-2xl">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => handleFile(e.target.files?.[0])}
                    />
                    <div
                      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                      onDragLeave={() => setDragOver(false)}
                      onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files?.[0]); }}
                      onClick={() => fileInputRef.current?.click()}
                      className={`border-2 border-dashed rounded-3xl p-20 cursor-pointer transition-all text-center ${
                        dragOver
                          ? 'border-emerald-400 bg-emerald-50'
                          : 'border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/30'
                      }`}>
                      <div className="text-6xl mb-5">🌿</div>
                      <h3 className="text-xl font-bold text-slate-700 mb-2">처방전 이미지를 올려주세요</h3>
                      <p className="text-sm text-slate-400 mb-1">드래그 & 드롭 또는 클릭하여 파일 선택</p>
                      <p className="text-xs text-slate-300">JPG · PNG · 최대 10MB</p>
                    </div>

                    {/* 기능 안내 */}
                    <div className="grid grid-cols-4 gap-4 mt-8">
                      {[
                        { icon: '🔍', label: 'OCR 추출',       desc: 'AI가 약물 목록을 자동 인식' },
                        { icon: '💊', label: '약물 정보',       desc: '식약처 Level A 근거 분석' },
                        { icon: '🌿', label: '동의보감 매핑',   desc: '증상-식재료 연결' },
                        { icon: '🔬', label: 'PubMed 근거',    desc: '임상 논문 기반 요약' },
                      ].map(({ icon, label, desc }) => (
                        <div key={label} className="bg-white rounded-2xl p-4 text-center border border-slate-100">
                          <div className="text-2xl mb-2">{icon}</div>
                          <p className="text-xs font-bold text-slate-700">{label}</p>
                          <p className="text-[10px] text-slate-400 mt-1">{desc}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Analysis result — 2×2 grid */}
              {!loading && analysisData && (
                <div className="h-full grid grid-cols-2 grid-rows-2 gap-4 p-4">

                  {/* Panel 1: 처방전 요약 */}
                  <div className={`${PANEL} ${PANEL_PAD} overflow-y-auto`}>
                    <PanelHeader icon="📋" title="처방전 요약" badge={`${analysisData.prescriptionSummary.drugList.length}개 약물`} />
                    <div className="space-y-2 mb-4">
                      {analysisData.prescriptionSummary.drugList.map((drug, i) => (
                        <div key={i} className="flex items-center gap-2 bg-slate-50 rounded-xl px-3 py-2">
                          <span className="w-5 h-5 rounded-full bg-emerald-500 text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0">{i + 1}</span>
                          <span className="text-sm text-slate-700 font-medium">{drug}</span>
                        </div>
                      ))}
                    </div>
                    {analysisData.prescriptionSummary.warnings && (
                      <div className="bg-amber-50 border border-amber-100 rounded-xl p-3">
                        <p className="text-xs font-bold text-amber-700 mb-1">⚠️ 주의사항</p>
                        <p className="text-xs text-amber-600 leading-relaxed">{analysisData.prescriptionSummary.warnings}</p>
                      </div>
                    )}
                    {analysisData.lifestyleGuide?.symptomTokens?.length > 0 && (
                      <div className="mt-4">
                        <p className="text-xs font-bold text-slate-500 mb-2">추론된 증상</p>
                        <div className="flex flex-wrap gap-1.5">
                          {analysisData.lifestyleGuide.symptomTokens.map((sym, i) => (
                            <span key={i} className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{sym}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Panel 2: 약물 정보 */}
                  <div className={`${PANEL} ${PANEL_PAD} overflow-y-auto`}>
                    <PanelHeader icon="💊" title="약물 정보" badge="식약처 Level A" />
                    {analysisData.drugDetails.length === 0 ? (
                      <EmptyState icon="💊" text="약물 정보를 불러오고 있습니다..." />
                    ) : (
                      <div className="space-y-3">
                        {analysisData.drugDetails.map((drug, i) => (
                          <div key={i} className="border border-slate-100 rounded-xl p-3">
                            <p className="text-sm font-bold text-slate-800 mb-2">{drug.name}</p>
                            {drug.efficacy && (
                              <div className="mb-1.5">
                                <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider">효능</span>
                                <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">{drug.efficacy}</p>
                              </div>
                            )}
                            {drug.sideEffects && (
                              <div>
                                <span className="text-[10px] font-bold text-amber-600 uppercase tracking-wider">부작용</span>
                                <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{drug.sideEffects}</p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Panel 3: 동의보감 */}
                  <div className={`${PANEL} ${PANEL_PAD} overflow-y-auto`}>
                    <PanelHeader icon="🌿" title="동의보감 추천" />
                    {(!analysisData.donguibogam?.foods || analysisData.donguibogam.foods.length === 0) ? (
                      <div>
                        <EmptyState icon="🌿" text="동의보감 데이터를 불러오려면 아래 버튼을 눌러주세요" />
                        <button
                          onClick={() => fetchSection('5')}
                          className="w-full mt-3 py-2.5 bg-emerald-500 text-white text-sm font-bold rounded-xl hover:bg-emerald-600 transition-colors">
                          동의보감 분석하기
                        </button>
                      </div>
                    ) : (
                      <div>
                        {analysisData.donguibogam.donguiSection && (
                          <p className="text-xs font-bold text-emerald-700 mb-3 bg-emerald-50 px-3 py-1.5 rounded-lg">{analysisData.donguibogam.donguiSection}</p>
                        )}
                        <div className="grid grid-cols-2 gap-2 mb-3">
                          {analysisData.donguibogam.foods.map((food, i) => (
                            <div key={i} className="bg-emerald-50 rounded-xl p-3">
                              <p className="text-sm font-bold text-emerald-800">{food.name}</p>
                              {food.reason && <p className="text-[10px] text-emerald-600 mt-1 leading-relaxed">{food.reason}</p>}
                              {food.precaution && <p className="text-[10px] text-amber-500 mt-1">⚠️ {food.precaution}</p>}
                            </div>
                          ))}
                        </div>
                        {analysisData.donguibogam.traditionalPrescriptions?.map((tp, i) => (
                          <div key={i} className="border border-teal-100 rounded-xl p-3 mb-2">
                            <p className="text-xs font-bold text-teal-700">{tp.name}</p>
                            <p className="text-[10px] text-slate-500 mt-1">{tp.description}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Panel 4: 학술 근거 */}
                  <div className={`${PANEL} ${PANEL_PAD} overflow-y-auto`}>
                    <PanelHeader icon="🔬" title="학술 근거"
                      badge={analysisData.academicEvidence?.trustLevel ? `Level ${analysisData.academicEvidence.trustLevel}` : undefined} />
                    {!analysisData.academicEvidence?.summary ? (
                      <EmptyState icon="🔬" text="학술 근거 없음" />
                    ) : (
                      <div>
                        <p className="text-xs text-slate-600 leading-relaxed mb-4">{analysisData.academicEvidence.summary}</p>
                        {analysisData.academicEvidence.papers?.length > 0 && (
                          <div className="space-y-2">
                            {analysisData.academicEvidence.papers.map((paper, i) => (
                              <a key={i} href={paper.url} target="_blank" rel="noopener noreferrer"
                                className="flex items-start gap-2 p-3 rounded-xl border border-slate-100 hover:border-blue-200 hover:bg-blue-50/30 transition-colors group">
                                <span className="text-blue-400 text-sm flex-shrink-0 mt-0.5">📄</span>
                                <p className="text-xs text-slate-700 group-hover:text-blue-700 leading-relaxed line-clamp-2">{paper.title}</p>
                              </a>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                </div>
              )}
            </div>
          )}

          {/* ─────────── 내 스택 ─────────── */}
          {activeTab === 'stack' && (
            <div className="h-full flex overflow-hidden">
              {/* Table */}
              <div className={`flex-1 overflow-y-auto p-4 ${selectedStack ? 'w-1/2' : 'w-full'}`}>
                {savedStacks.length === 0 ? (
                  <div className="h-full flex items-center justify-center">
                    <EmptyState icon="📋" text="저장된 처방 이력이 없습니다. 처방전을 분석해보세요." />
                  </div>
                ) : (
                  <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-slate-50 border-b border-slate-100">
                        <tr>
                          <th className="text-left px-4 py-3 text-xs font-bold text-slate-500">날짜</th>
                          <th className="text-left px-4 py-3 text-xs font-bold text-slate-500">약물 목록</th>
                          <th className="text-left px-4 py-3 text-xs font-bold text-slate-500">증상</th>
                          <th className="px-4 py-3 text-xs font-bold text-slate-500">작업</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {savedStacks.map((stack) => (
                          <tr
                            key={stack.id}
                            onClick={() => setSelectedStack(selectedStack?.id === stack.id ? null : stack)}
                            className={`cursor-pointer transition-colors ${
                              selectedStack?.id === stack.id ? 'bg-emerald-50' : 'hover:bg-slate-50'
                            }`}>
                            <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">{stack.date}</td>
                            <td className="px-4 py-3">
                              <div className="flex flex-wrap gap-1">
                                {stack.drugList.slice(0, 3).map((d, i) => (
                                  <span key={i} className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">{d}</span>
                                ))}
                                {stack.drugList.length > 3 && (
                                  <span className="text-[10px] text-slate-400">+{stack.drugList.length - 3}</span>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex flex-wrap gap-1">
                                {(stack.data?.lifestyleGuide?.symptomTokens ?? []).slice(0, 2).map((sym: string, i: number) => (
                                  <span key={i} className="text-[10px] bg-blue-50 text-blue-500 px-2 py-0.5 rounded-full">{sym}</span>
                                ))}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-center">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (confirm('삭제하시겠습니까?')) {
                                    setSavedStacks(prev => prev.filter(s => s.id !== stack.id));
                                    if (selectedStack?.id === stack.id) setSelectedStack(null);
                                  }
                                }}
                                className="text-[10px] text-red-400 hover:text-red-600 hover:bg-red-50 px-2 py-1 rounded-lg transition-colors">
                                삭제
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Side detail panel */}
              {selectedStack && (
                <div className="w-1/2 border-l border-slate-100 overflow-y-auto p-4 bg-slate-50">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-bold text-slate-800">{selectedStack.date}</h3>
                    <button onClick={() => setSelectedStack(null)} className="text-slate-400 hover:text-slate-600 text-sm">✕ 닫기</button>
                  </div>
                  <div className="space-y-3">
                    <div className={`${PANEL} ${PANEL_PAD}`}>
                      <p className="text-xs font-bold text-slate-500 mb-2">약물 목록</p>
                      <div className="space-y-1.5">
                        {selectedStack.drugList.map((d, i) => (
                          <div key={i} className="text-sm text-slate-700 bg-slate-50 rounded-lg px-3 py-1.5">{d}</div>
                        ))}
                      </div>
                    </div>
                    {selectedStack.data?.lifestyleGuide?.symptomTokens?.length > 0 && (
                      <div className={`${PANEL} ${PANEL_PAD}`}>
                        <p className="text-xs font-bold text-slate-500 mb-2">추론된 증상</p>
                        <div className="flex flex-wrap gap-1.5">
                          {selectedStack.data.lifestyleGuide.symptomTokens.map((s: string, i: number) => (
                            <span key={i} className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{s}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {selectedStack.data?.donguibogam?.foods?.length > 0 && (
                      <div className={`${PANEL} ${PANEL_PAD}`}>
                        <p className="text-xs font-bold text-slate-500 mb-2">동의보감 추천 식재료</p>
                        <div className="grid grid-cols-2 gap-2">
                          {selectedStack.data.donguibogam.foods.map((f: any, i: number) => (
                            <div key={i} className="text-xs bg-emerald-50 text-emerald-700 px-2 py-1.5 rounded-lg font-medium">{f.name}</div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ─────────── 동네 약국 ─────────── */}
          {activeTab === 'map' && (
            <div className="h-full flex overflow-hidden">
              {/* Map */}
              <div className="flex-1 relative">
                <div ref={mapRef} className="w-full h-full bg-slate-100" />
                {!kakaoMapRef.current && !locationError && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-50">
                    <div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mb-3" />
                    <p className="text-sm text-slate-400">위치를 파악하고 있어요...</p>
                  </div>
                )}
                {locationError && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-50">
                    <p className="text-slate-400 text-sm">{locationError}</p>
                  </div>
                )}
              </div>

              {/* Pharmacy list */}
              <div className="w-80 flex-shrink-0 border-l border-slate-100 overflow-y-auto bg-white">
                <div className="px-4 py-3 border-b border-slate-100">
                  <p className="text-sm font-bold text-slate-700">
                    {loadingPharmacy ? '약국 검색 중...' : `약국 ${pharmacies.length}개`}
                  </p>
                </div>
                <div className="divide-y divide-slate-50">
                  {pharmacies.map((p, i) => (
                    <div key={i}
                      onClick={() => setSelectedPharmacy(selectedPharmacy?.name === p.name ? null : p)}
                      className={`p-4 cursor-pointer transition-colors ${
                        selectedPharmacy?.name === p.name ? 'bg-emerald-50' : 'hover:bg-slate-50'
                      }`}>
                      <div className="flex items-start gap-3">
                        <span className="w-6 h-6 rounded-full bg-emerald-500 text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">{i + 1}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-1">
                            <p className="text-sm font-bold text-slate-800 truncate">{p.name}</p>
                            {p.distance && <span className="text-[10px] text-slate-400 flex-shrink-0">{p.distance}m</span>}
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5 truncate">{p.address}</p>
                          {p.phone && <p className="text-xs text-slate-400 mt-0.5">📞 {p.phone}</p>}
                          {p.link && (
                            <a href={p.link} target="_blank" rel="noopener noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="inline-block text-[10px] text-amber-600 font-bold bg-amber-50 px-2 py-0.5 rounded-full mt-1.5">
                              🕐 영업시간 확인
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  {pharmacies.length === 0 && !loadingPharmacy && (
                    <EmptyState icon="📍" text="주변 약국을 검색하고 있습니다..." />
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ─────────── 건강 리포트 ─────────── */}
          {activeTab === 'report' && (() => {
            const { topDrugs, topSymptoms, topFoods, uniqueDrugs, uniqueSymptoms, uniqueFoods } = computeReport();
            const maxDrugCount = topDrugs[0]?.[1] ?? 1;

            return (
              <div className="h-full overflow-y-auto p-4">
                {savedStacks.length === 0 ? (
                  <div className="h-full flex items-center justify-center">
                    <EmptyState icon="📊" text="처방 이력이 없습니다. 처방전을 분석하면 리포트가 생성됩니다." />
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* KPI Cards */}
                    <div className="grid grid-cols-4 gap-4">
                      {[
                        { label: '총 처방 횟수', value: `${savedStacks.length}회`,  icon: '📋', color: 'text-blue-600',   bg: 'bg-blue-50' },
                        { label: '고유 약물 수',  value: `${uniqueDrugs}종`,         icon: '💊', color: 'text-emerald-600', bg: 'bg-emerald-50' },
                        { label: '증상 종류',     value: `${uniqueSymptoms}종`,       icon: '🩺', color: 'text-purple-600', bg: 'bg-purple-50' },
                        { label: '추천 식재료',   value: `${uniqueFoods}종`,          icon: '🌿', color: 'text-teal-600',   bg: 'bg-teal-50' },
                      ].map(({ label, value, icon, color, bg }) => (
                        <div key={label} className={`${PANEL} ${PANEL_PAD} flex items-center gap-4`}>
                          <div className={`w-12 h-12 rounded-2xl ${bg} flex items-center justify-center text-2xl flex-shrink-0`}>{icon}</div>
                          <div>
                            <p className={`text-2xl font-bold ${color}`}>{value}</p>
                            <p className="text-xs text-slate-500 mt-0.5">{label}</p>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Charts row */}
                    <div className="grid grid-cols-2 gap-4">
                      {/* TOP 약물 */}
                      <div className={`${PANEL} ${PANEL_PAD}`}>
                        <PanelHeader icon="💊" title="TOP 처방 약물" />
                        {topDrugs.length === 0 ? (
                          <EmptyState icon="💊" text="데이터 없음" />
                        ) : (
                          <div className="space-y-3">
                            {topDrugs.map(([name, count], i) => (
                              <div key={i} className="flex items-center gap-3">
                                <span className="text-xs text-slate-400 w-4 text-right flex-shrink-0">{i + 1}</span>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs font-medium text-slate-700 truncate">{name}</span>
                                    <span className="text-xs text-slate-400 flex-shrink-0 ml-2">{count}회</span>
                                  </div>
                                  <div className="w-full bg-slate-100 rounded-full h-1.5">
                                    <div
                                      className="bg-emerald-400 h-1.5 rounded-full transition-all"
                                      style={{ width: `${(count / maxDrugCount) * 100}%` }}
                                    />
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* 증상 패턴 */}
                      <div className={`${PANEL} ${PANEL_PAD}`}>
                        <PanelHeader icon="🩺" title="증상 패턴" />
                        {topSymptoms.length === 0 ? (
                          <EmptyState icon="🩺" text="데이터 없음" />
                        ) : (
                          <div className="flex flex-wrap gap-2">
                            {topSymptoms.map(([sym, count], i) => (
                              <span key={i}
                                className="text-xs px-3 py-1.5 rounded-full border font-medium"
                                style={{
                                  fontSize: `${Math.max(10, Math.min(14, 10 + count * 1.5))}px`,
                                  backgroundColor: `rgba(99,102,241,${0.05 + count * 0.08})`,
                                  borderColor: `rgba(99,102,241,${0.2 + count * 0.1})`,
                                  color: '#4f46e5',
                                }}>
                                {sym} <span className="opacity-60">{count}</span>
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* 처방 타임라인 + 식재료 */}
                    <div className="grid grid-cols-2 gap-4">
                      {/* 타임라인 */}
                      <div className={`${PANEL} ${PANEL_PAD}`}>
                        <PanelHeader icon="📅" title="처방 타임라인" />
                        <div className="space-y-3">
                          {savedStacks.slice(0, 5).map((s) => (
                            <div key={s.id} className="flex gap-3 items-start">
                              <div className="flex-shrink-0 mt-1">
                                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                              </div>
                              <div>
                                <p className="text-[10px] text-slate-400">{s.date}</p>
                                <p className="text-xs text-slate-700 font-medium mt-0.5">{s.drugList.slice(0, 2).join(', ')}{s.drugList.length > 2 ? ` 외 ${s.drugList.length - 2}종` : ''}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* 자주 등장 식재료 */}
                      <div className={`${PANEL} ${PANEL_PAD}`}>
                        <PanelHeader icon="🌿" title="자주 등장한 식재료" />
                        {topFoods.length === 0 ? (
                          <EmptyState icon="🌿" text="데이터 없음" />
                        ) : (
                          <div className="grid grid-cols-2 gap-2">
                            {topFoods.map(([name, count], i) => (
                              <div key={i} className="bg-emerald-50 rounded-xl p-3 flex items-center justify-between">
                                <span className="text-sm font-medium text-emerald-800">{name}</span>
                                <span className="text-[10px] text-emerald-500 bg-emerald-100 px-1.5 py-0.5 rounded-full">{count}회</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                  </div>
                )}
              </div>
            );
          })()}

        </main>
      </div>
    </div>
  );
};

export default PcDashboard;
