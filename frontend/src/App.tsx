import type React from 'react';
import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  History,
  MapPin,
  FileText,
  Settings,
  Bell,
  User,
  ChevronRight,
  Activity,
  Pill,
  Utensils,
  Brain,
  Volume2,
  Trash2,
  X,
  PlusCircle,
  Newspaper,
  ExternalLink,
  Tv,
  Navigation,
  Phone,
  Loader2,
  RefreshCw,
  Sparkles,
  LogOut,
  Users,
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import Step3Report from './components/analysis/Step3Report';
import PrescriptionReport from './components/analysis/PrescriptionReport';
import AnalysisWizard from './components/analysis/AnalysisWizard';
import SettingsPage from './components/settings/SettingsPage';
import Toast from './components/settings/Toast';
import { useSettings } from './contexts/SettingsContext';
import { useNotificationScheduler } from './hooks/useNotificationScheduler';
import { sendBrowserNotification } from './services/notificationService';
import type { MedicationSchedule } from './types/settings';
import DietGuideModal from './components/analysis/DietGuideModal';
import MedicationReminderSetup from './components/analysis/MedicationReminderSetup';
import NotificationPanel from './components/notifications/NotificationPanel';
import { useNotificationStore } from './hooks/useNotificationStore';
import {
  analyzePrescriptionSSE,
  getHealthNews,
  getHealthTrends,
  getHealthTip,
  type ReportData,
  type PrescriptionData,
  type ProgressEvent as AnalysisProgressEvent,
  type HealthNewsItem,
  type HealthTrendItem,
  type HealthTip,
} from './services/analysisApi';
import { supabase } from './services/supabase';
import { notifyFamilyNewPrescription } from './services/familyApi';
import { fetchStacks, saveStack, deleteStackApi } from './services/stacksApi';
import FamilyPrescriptionsView from './components/family/FamilyPrescriptionsView';
import type { User as SupabaseUser } from '@supabase/supabase-js';

declare const kakao: any;

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ─── Types ────────────────────────────────────────────────────────────────────

interface SavedStack {
  id: string;
  date: string;
  title: string;
  type: 'prescription' | 'symptom';
  prescriptionData?: PrescriptionData;
  report?: ReportData;
}

interface KakaoPharmacy {
  name: string;
  address: string;
  phone: string;
  lat: number;
  lng: number;
  place_url: string;
  distance: number;
}

// (HealthTrendItem is imported from analysisApi)

// ─── SidebarItem ──────────────────────────────────────────────────────────────

const SidebarItem = ({
  icon: Icon,
  label,
  active,
  onClick,
}: {
  icon: any;
  label: string;
  active?: boolean;
  onClick: () => void;
}) => (
  <button
    onClick={onClick}
    className={cn(
      'w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group',
      active
        ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-200'
        : 'text-slate-500 hover:bg-emerald-50 hover:text-emerald-600'
    )}
  >
    <Icon
      size={20}
      className={cn(
        'transition-transform group-hover:scale-110',
        active ? 'text-white' : 'text-slate-400 group-hover:text-emerald-600'
      )}
    />
    <span className="font-medium">{label}</span>
    {active && (
      <motion.div layoutId="active-pill" className="ml-auto w-1.5 h-1.5 rounded-full bg-white" />
    )}
  </button>
);

// ─── PharmacyCard ─────────────────────────────────────────────────────────────

const PharmacyCard = ({
  pharmacy,
  index,
  selected,
  onClick,
}: {
  pharmacy: KakaoPharmacy;
  index: number;
  selected?: boolean;
  onClick: () => void;
}) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: index * 0.06 }}
    onClick={onClick}
    className={cn(
      'p-4 bg-white rounded-2xl flex gap-4 items-start cursor-pointer transition-all border',
      selected ? 'border-teal-400 shadow-md bg-teal-50/30' : 'border-slate-100 hover:border-teal-200'
    )}
  >
    <div className="w-8 h-8 bg-emerald-600 text-white rounded-full flex items-center justify-center text-xs font-bold shrink-0">
      {index + 1}
    </div>
    <div className="flex-1 min-w-0">
      <p className="font-bold text-slate-800 text-sm mb-1 truncate">{pharmacy.name}</p>
      <p className="text-xs text-slate-500 mb-2 truncate">{pharmacy.address}</p>
      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-[10px] font-bold text-teal-600 bg-teal-50 px-2 py-0.5 rounded-full">
          {pharmacy.distance}m
        </span>
        {pharmacy.phone && pharmacy.phone !== '정보 없음' && (
          <a
            href={`tel:${pharmacy.phone}`}
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-teal-600 transition-colors"
          >
            <Phone size={10} />
            {pharmacy.phone}
          </a>
        )}
        {pharmacy.place_url && (
          <a
            href={pharmacy.place_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1 text-[10px] text-teal-600 hover:text-teal-800 font-bold"
          >
            <ExternalLink size={10} />
            상세
          </a>
        )}
      </div>
    </div>
  </motion.div>
);

// ─── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'stacks' | 'map' | 'reports' | 'settings'>('dashboard');
  const { settings, showToast, updateNotification } = useSettings();
  const notifStore = useNotificationStore();
  const [showNotifPanel, setShowNotifPanel] = useState(false);
  const bellRef = useRef<HTMLButtonElement>(null);
  useNotificationScheduler({
    onNotification: (item) => notifStore.addNotification(item),
  });

  // Stack view toggle (my / family)
  const [stackView, setStackView] = useState<'my' | 'family'>('my');

  // Auth
  const [user, setUser] = useState<SupabaseUser | null>(null);
  const [authLoading, setAuthLoading] = useState(true);

  // Loading / progress
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [loadingProgress, setLoadingProgress] = useState(0);
  const abortRef = useRef<AbortController | null>(null);

  // Stacks (initialize from localStorage to avoid data loss)
  const [savedStacks, setSavedStacks] = useState<SavedStack[]>(() => {
    try {
      const stored = localStorage.getItem('health_stacks_v5');
      return stored ? JSON.parse(stored) : [];
    } catch { return []; }
  });

  // Analysis modal (prescription or symptom)
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [modalStack, setModalStack] = useState<SavedStack | null>(null);

  // Symptom wizard modal
  const [showSymptomModal, setShowSymptomModal] = useState(false);

  // Medication reminder setup in modal
  const [showMedSetup, setShowMedSetup] = useState(false);

  // Diet guide modal
  const [showDietModal, setShowDietModal] = useState(false);

  // Pharmacy tab (Kakao Maps)
  const [pharmacies, setPharmacies] = useState<KakaoPharmacy[]>([]);
  const [pharmacyLoading, setPharmacyLoading] = useState(false);
  const [pharmacyError, setPharmacyError] = useState<string | null>(null);
  const [selectedPharmacy, setSelectedPharmacy] = useState<KakaoPharmacy | null>(null);
  const mapRef = useRef<HTMLDivElement>(null);
  const kakaoMapRef = useRef<any>(null);

  // Health news (API) & trends (API) & tip (API)
  const [healthNews, setHealthNews] = useState<HealthNewsItem[]>([]);
  const [newsLoading, setNewsLoading] = useState(false);
  const [healthTrends, setHealthTrends] = useState<HealthTrendItem[]>([]);
  const [trendsLoading, setTrendsLoading] = useState(false);
  const [healthTip, setHealthTip] = useState<HealthTip | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Health News 가져오기 ─────────────────────────────────────────────────
  const fetchNews = async () => {
    setNewsLoading(true);
    try {
      const items = await getHealthNews('건강', 5);
      setHealthNews(items);
    } catch (err) {
      console.error('뉴스 로드 실패:', err);
    } finally {
      setNewsLoading(false);
    }
  };

  const fetchTrends = async () => {
    setTrendsLoading(true);
    try {
      const items = await getHealthTrends(3);
      setHealthTrends(items);
    } catch (err) {
      console.error('트렌드 로드 실패:', err);
    } finally {
      setTrendsLoading(false);
    }
  };

  const fetchTip = async () => {
    try {
      const data = await getHealthTip();
      setHealthTip(data);
    } catch (err) {
      console.error('건강팁 로드 실패:', err);
    }
  };

  useEffect(() => { fetchNews(); fetchTrends(); fetchTip(); }, []);

  // ── localStorage 동기화 ──────────────────────────────────────────────────
  useEffect(() => {
    localStorage.setItem('health_stacks_v5', JSON.stringify(savedStacks));
  }, [savedStacks]);

  // ── Supabase Auth ──────────────────────────────────────────────────────────
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setAuthLoading(false);
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, session) => {
      setUser(session?.user ?? null);
      setAuthLoading(false);
    });
    return () => subscription.unsubscribe();
  }, []);

  // ── 서버에서 스택 불러오기 (로그인 시) ─────────────────────────────────────
  useEffect(() => {
    if (!user) return;
    fetchStacks().then((serverStacks) => {
      if (!serverStacks || serverStacks.length === 0) return;
      const rebuilt: SavedStack[] = serverStacks.map((s) => ({
        id: s.id,
        title: s.title,
        type: s.type as 'prescription' | 'symptom',
        date: s.date,
        prescriptionData: s.stack_data?.prescriptionData as PrescriptionData | undefined,
        report: s.stack_data?.report as ReportData | undefined,
      }));
      setSavedStacks((prev) => {
        // Merge: server stacks + local-only stacks (by id)
        const serverIds = new Set(rebuilt.map((s) => s.id));
        const localOnly = prev.filter((s) => !serverIds.has(s.id));
        return [...rebuilt, ...localOnly];
      });
    });
  }, [user]);

  const handleGoogleLogin = () => {
    supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: window.location.origin } });
  };

  const handleLogout = () => {
    supabase.auth.signOut();
  };

  // ── Prescription SSE Upload ───────────────────────────────────────────────

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (fileInputRef.current) fileInputRef.current.value = '';

    setLoading(true);
    setLoadingProgress(0);
    setLoadingStep('처방전을 불러오고 있어요...');

    const controller = analyzePrescriptionSSE(
      file,
      '1,2,3,4,5',
      (evt: AnalysisProgressEvent) => {
        setLoadingStep(evt.message);
        setLoadingProgress(evt.progress);
      },
      (data: PrescriptionData) => {
        const drugList = data.prescriptionSummary?.drugList ?? [];
        const title = drugList.length > 0 ? drugList.join(', ') : '처방전 분석';
        const newStack: SavedStack = {
          id: Date.now().toString(),
          date: new Date().toLocaleDateString('ko-KR', {
            year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit',
          }),
          title,
          type: 'prescription',
          prescriptionData: data,
        };
        setSavedStacks(prev => [newStack, ...prev]);
        // 서버에 저장
        if (user) {
          saveStack({ id: newStack.id, title: newStack.title, type: newStack.type, date: newStack.date, stack_data: { prescriptionData: data } });
        }
        setModalStack(newStack);
        setShowAnalysisModal(true);
        setLoading(false);
        setLoadingProgress(100);

        // Analysis complete notification
        if (settings.notification.analysisComplete) {
          sendBrowserNotification('분석 완료', `${title} 분석이 완료되었습니다`);
          showToast('✅ 처방전 분석이 완료되었습니다');
          notifStore.addNotification({ type: 'analysis', title: '분석 완료', body: `${title} 분석이 완료되었습니다` });
        }

        // 가족 그룹에 새 처방전 알림
        notifyFamilyNewPrescription();

        // Auto-extract medications for reminder schedules
        if (settings.notification.medicationReminder && drugList.length > 0) {
          const existingNames = settings.notification.medicationSchedules.map(s => s.drugName);
          const newDrugs = drugList.filter(d => !existingNames.includes(d));
          if (newDrugs.length > 0) {
            const newSchedules: MedicationSchedule[] = newDrugs.map(drugName => ({
              id: Date.now().toString() + Math.random().toString(36).slice(2, 6),
              drugName,
              times: ['08:00', '12:00', '18:00'],
              daysOfWeek: [],
              enabled: false,
            }));
            updateNotification({
              medicationSchedules: [...settings.notification.medicationSchedules, ...newSchedules],
            });
            showToast(`💊 ${newDrugs.length}개 약물이 복약 알림에 추가되었습니다 (설정에서 확인)`);
          }
        }
      },
      (errMsg: string) => {
        alert(`분석에 실패했습니다: ${errMsg}`);
        setLoading(false);
      },
    );

    abortRef.current = controller;
  };

  // ── Symptom report callback ───────────────────────────────────────────────

  const handleSymptomReport = (report: ReportData, title: string) => {
    const newStack: SavedStack = {
      id: Date.now().toString(),
      date: new Date().toLocaleDateString('ko-KR', {
        year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit',
      }),
      title: title || '증상 분석',
      type: 'symptom',
      report,
    };
    setSavedStacks(prev => [newStack, ...prev]);
    // 서버에 저장
    if (user) {
      saveStack({ id: newStack.id, title: newStack.title, type: newStack.type, date: newStack.date, stack_data: { report } });
    }
    setModalStack(newStack);
    setShowSymptomModal(false);
    setShowAnalysisModal(true);

    if (settings.notification.analysisComplete) {
      sendBrowserNotification('증상 분석 완료', `${title || '증상 분석'} 완료`);
      showToast('✅ 증상 분석이 완료되었습니다');
      notifStore.addNotification({ type: 'analysis', title: '증상 분석 완료', body: `${title || '증상 분석'} 완료` });
    }

    // 가족 그룹에 새 처방전 알림
    notifyFamilyNewPrescription();
  };

  // ── Open stack in modal ───────────────────────────────────────────────────

  const openStack = (stack: SavedStack) => {
    setModalStack(stack);
    setShowAnalysisModal(true);
  };

  const deleteStack = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm('이 기록을 삭제하시겠습니까?')) {
      setSavedStacks(prev => prev.filter(s => s.id !== id));
      if (user) deleteStackApi(id);
    }
  };

  // ── TTS ───────────────────────────────────────────────────────────────────

  const speakText = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text.substring(0, 300));
      utter.lang = 'ko-KR';
      utter.rate = settings.display.ttsSpeed;
      window.speechSynthesis.speak(utter);
    }
  };

  const getSpeakText = (stack: SavedStack | null) => {
    if (!stack) return '';
    if (stack.type === 'prescription' && stack.prescriptionData) {
      const w = stack.prescriptionData.prescriptionSummary?.warnings;
      if (Array.isArray(w)) return w.join('. ');
      return w ?? '';
    }
    return stack.report?.summary ?? '';
  };

  // ── Kakao Map Pharmacy Search ─────────────────────────────────────────────

  const initPharmacyMap = () => {
    if (!mapRef.current) return;
    if (typeof kakao === 'undefined' || !kakao.maps) {
      setPharmacyError('카카오 지도를 불러올 수 없습니다.');
      return;
    }

    setPharmacyLoading(true);
    setPharmacyError(null);
    setSelectedPharmacy(null);

    // kakao.maps.load()로 SDK 내부 모듈 로딩 완료 후 실행
    kakao.maps.load(() => {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude: lat, longitude: lng } = pos.coords;
          const center = new kakao.maps.LatLng(lat, lng);

          // Create or reuse map
          if (!kakaoMapRef.current) {
            kakaoMapRef.current = new kakao.maps.Map(mapRef.current, {
              center,
              level: 4,
            });
          } else {
            kakaoMapRef.current.setCenter(center);
          }
          const map = kakaoMapRef.current;

          // My location overlay (blue dot)
          new kakao.maps.CustomOverlay({
            position: center,
            content: '<div style="width:14px;height:14px;background:#3b82f6;border-radius:50%;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3)"></div>',
            map,
          });

          // Search pharmacies via Kakao Places API
          const ps = new kakao.maps.services.Places();
          ps.keywordSearch(
            '약국',
            (result: any, status: any) => {
              if (status === kakao.maps.services.Status.OK) {
                const nearbyPlaces: KakaoPharmacy[] = result.slice(0, 10).map((p: any) => ({
                  name: p.place_name,
                  address: p.road_address_name || p.address_name,
                  phone: p.phone || '정보 없음',
                  lat: Number(p.y),
                  lng: Number(p.x),
                  place_url: p.place_url || '',
                  distance: p.distance ? Number(p.distance) : 0,
                }));

                setPharmacies(nearbyPlaces);

                // Place markers
                nearbyPlaces.forEach((p, i) => {
                  const markerPos = new kakao.maps.LatLng(p.lat, p.lng);
                  const el = document.createElement('div');
                  el.style.cssText =
                    'background:#059669;color:white;font-size:10px;font-weight:bold;padding:3px 8px;border-radius:999px;box-shadow:0 2px 6px rgba(0,0,0,0.25);white-space:nowrap;cursor:pointer;line-height:1.4';
                  el.textContent = String(i + 1);
                  el.onclick = () => {
                    setSelectedPharmacy(p);
                    map.panTo(markerPos);
                  };
                  new kakao.maps.CustomOverlay({ position: markerPos, content: el, map });
                });
              } else {
                setPharmacyError('주변 약국을 찾을 수 없습니다.');
              }
              setPharmacyLoading(false);
            },
            {
              location: center,
              radius: 2000,
              sort: kakao.maps.services.SortBy.DISTANCE,
            }
          );
        },
        () => {
          setPharmacyError('위치 정보 접근이 거부되었습니다. 브라우저 설정에서 위치 권한을 허용해주세요.');
          setPharmacyLoading(false);
        },
        { timeout: 10000 }
      );
    });
  };


  // ─────────────────────────────────────────────────────────────────────────

  return (
    <div className="flex h-screen bg-[var(--bg-primary)] overflow-hidden font-sans transition-colors duration-300">

      {/* ── Sidebar ── */}
      <aside className="w-72 bg-[var(--bg-surface)] border-r border-[var(--border-color)] flex flex-col p-6 z-30 shrink-0 transition-colors duration-300">
        <div className="mb-10 px-2">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">H</div>
            <h1 className="text-xl font-bold text-[var(--text-primary)] tracking-tight">HealthStack</h1>
          </div>
          <p className="text-[10px] text-emerald-600 font-bold uppercase tracking-widest">My Body Manual v5</p>
        </div>

        <nav className="flex-1 space-y-2">
          <SidebarItem icon={LayoutDashboard} label="대시보드" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
          <SidebarItem icon={History} label="복용 스택" active={activeTab === 'stacks'} onClick={() => setActiveTab('stacks')} />
          <SidebarItem icon={MapPin} label="주변 약국" active={activeTab === 'map'} onClick={() => setActiveTab('map')} />
          <SidebarItem icon={FileText} label="건강 리포트" active={activeTab === 'reports'} onClick={() => setActiveTab('reports')} />
        </nav>

        <div className="mt-auto pt-6 border-t border-[var(--border-color)]">
          <SidebarItem icon={Settings} label="설정" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
          <div className="mt-4 p-4 bg-emerald-50 rounded-2xl">
            <p className="text-xs font-bold text-emerald-800 mb-1">프리미엄 혜택</p>
            <p className="text-[10px] text-emerald-600 mb-3">AI 정밀 분석 무제한 이용</p>
            <button className="w-full py-2 bg-emerald-600 text-white text-[10px] font-bold rounded-lg hover:bg-emerald-700 transition-colors shadow-md shadow-emerald-100">
              업그레이드
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="flex-1 flex flex-col overflow-hidden relative">

        {/* Top Header */}
        <header className="h-20 bg-[var(--bg-surface)]/50 backdrop-blur-md border-b border-[var(--border-color)] flex items-center justify-end px-10 sticky top-0 z-20 shrink-0 transition-colors duration-300">
          <div className="flex items-center gap-6">
            <button
              ref={bellRef}
              onClick={() => setShowNotifPanel(prev => !prev)}
              className="relative p-2 text-slate-400 hover:text-emerald-600 transition-colors"
            >
              <Bell size={22} />
              {notifStore.unreadCount > 0 && (
                <span className="absolute top-1 right-1 min-w-[16px] h-4 bg-rose-500 rounded-full border-2 border-white flex items-center justify-center text-[9px] font-bold text-white px-0.5">
                  {notifStore.unreadCount > 9 ? '9+' : notifStore.unreadCount}
                </span>
              )}
            </button>
            <NotificationPanel
              open={showNotifPanel}
              onClose={() => setShowNotifPanel(false)}
              triggerRef={bellRef}
              notifications={notifStore.notifications}
              unreadCount={notifStore.unreadCount}
              onMarkAsRead={notifStore.markAsRead}
              onMarkAllAsRead={notifStore.markAllAsRead}
              onRemove={notifStore.removeNotification}
              onClearAll={notifStore.clearAll}
            />
            {!authLoading && (
              <div className="flex items-center gap-3 pl-6 border-l border-slate-100">
                {user ? (
                  <>
                    <div className="text-right">
                      <p className="text-sm font-bold text-slate-800">{user.user_metadata?.full_name || user.email?.split('@')[0] || '사용자'} 님</p>
                      <p className="text-[10px] text-emerald-600 font-bold">Standard Plan</p>
                    </div>
                    {user.user_metadata?.avatar_url ? (
                      <img src={user.user_metadata.avatar_url} className="w-10 h-10 rounded-2xl shadow-lg" alt="avatar" />
                    ) : (
                      <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-2xl flex items-center justify-center text-white shadow-lg">
                        <User size={20} />
                      </div>
                    )}
                    <button onClick={handleLogout} className="p-2 text-slate-400 hover:text-rose-500 transition-colors" title="로그아웃">
                      <LogOut size={18} />
                    </button>
                  </>
                ) : (
                  <button
                    onClick={handleGoogleLogin}
                    className="flex items-center gap-2 px-5 py-2.5 bg-white border border-slate-200 rounded-2xl shadow-sm hover:bg-slate-50 active:scale-95 transition-all"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
                    <span className="text-sm font-bold text-slate-600">Google로 로그인</span>
                  </button>
                )}
              </div>
            )}
          </div>
        </header>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-10">
          <AnimatePresence mode="wait">

            {/* ────────────── DASHBOARD ────────────── */}
            {activeTab === 'dashboard' && (
              <motion.div key="dashboard" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="space-y-10">

                {/* Hero */}
                <div className="relative bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 rounded-[32px] p-10 text-white shadow-xl overflow-hidden">
                  <div className="relative z-10 flex justify-between items-start">
                    <div className="max-w-2xl">
                      <h2 className="text-3xl font-bold mb-3 tracking-tight">내 몸 설명서, HealthStack</h2>
                      <p className="text-emerald-50/90 text-sm leading-relaxed mb-6">
                        처방전 사진 한 장이면 AI가 약물 분석, 상호작용 확인, 동의보감 기반 맞춤 식단까지 한번에 알려드려요.
                        <br />나만의 건강 데이터가 쌓일수록 더 정확한 건강 리포트를 받아보실 수 있습니다.
                      </p>
                      <div className="flex flex-wrap gap-2 mb-6">
                        {['AI 처방전 분석', '약물 상호작용 확인', '동의보감 맞춤 식단', '건강 리포트'].map(tag => (
                          <span key={tag} className="px-3 py-1 bg-white/15 backdrop-blur-sm rounded-full text-[11px] font-bold">{tag}</span>
                        ))}
                      </div>
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="flex items-center gap-2 px-6 py-3 bg-white text-emerald-700 rounded-2xl font-bold shadow-lg hover:bg-emerald-50 transition-all active:scale-95"
                      >
                        <PlusCircle size={20} />
                        처방전 분석 시작하기
                      </button>
                      <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept="image/*" className="hidden" />
                    </div>
                    <div className="hidden lg:flex flex-col items-center gap-3 opacity-90">
                      <div className="w-20 h-20 bg-white/15 rounded-[24px] flex items-center justify-center backdrop-blur-sm text-4xl">💊</div>
                      <div className="flex gap-3">
                        <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center backdrop-blur-sm text-2xl">🌿</div>
                        <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center backdrop-blur-sm text-2xl">📊</div>
                      </div>
                    </div>
                  </div>
                  <div className="absolute -bottom-16 -right-16 text-[220px] opacity-[0.06] rotate-12 leading-none select-none">🍃</div>
                </div>

                {/* News + Trends */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Health News (2/3) */}
                  <div className="lg:col-span-2 glass-card p-8 bg-white">
                    <div className="flex justify-between items-center mb-8">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg"><Newspaper size={20} /></div>
                        <h3 className="text-xl font-bold text-slate-800">최신 건강 뉴스</h3>
                      </div>
                      <button onClick={fetchNews} disabled={newsLoading} className="text-xs font-bold text-emerald-600 hover:text-emerald-700 flex items-center gap-1">
                        {newsLoading ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />} 새로고침
                      </button>
                    </div>
                    <div className="space-y-6">
                      {newsLoading ? (
                        <div className="flex items-center justify-center py-16">
                          <Loader2 size={28} className="text-emerald-400 animate-spin" />
                        </div>
                      ) : healthNews.length === 0 ? (
                        <div className="text-center py-16 text-slate-400 text-sm">뉴스를 불러올 수 없습니다.</div>
                      ) : (
                        healthNews.map((news, i) => (
                          <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }} className="group p-4 rounded-2xl hover:bg-slate-50 border border-transparent hover:border-slate-100 transition-all">
                            <a href={news.url} target="_blank" rel="noopener noreferrer" className="block">
                              <div className="flex justify-between items-start mb-2">
                                <h4 className="font-bold text-slate-800 group-hover:text-emerald-600 transition-colors line-clamp-1">{news.title}</h4>
                                <ExternalLink size={14} className="text-slate-300 group-hover:text-emerald-400 shrink-0 ml-2" />
                              </div>
                              <p className="text-sm text-slate-500 leading-relaxed line-clamp-2">{news.summary}</p>
                              {news.date && <p className="text-[10px] text-slate-400 mt-1">{news.date}</p>}
                            </a>
                          </motion.div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Right: Trends + AI Tip */}
                  <div className="space-y-8">
                    <div className="glass-card p-8 bg-white">
                      <div className="flex justify-between items-center mb-6">
                        <div className="flex items-center gap-2">
                          <div className="p-2 bg-amber-50 text-amber-600 rounded-lg"><Tv size={18} /></div>
                          <h3 className="text-lg font-bold text-slate-800">방송가 핫 트렌드</h3>
                        </div>
                        <button onClick={fetchTrends} disabled={trendsLoading} className="text-xs font-bold text-amber-600 hover:text-amber-700 flex items-center gap-1">
                          {trendsLoading ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />} 새로고침
                        </button>
                      </div>
                      <div className="space-y-4">
                        {trendsLoading ? (
                          <div className="flex items-center justify-center py-12">
                            <Loader2 size={24} className="text-amber-400 animate-spin" />
                          </div>
                        ) : healthTrends.length === 0 ? (
                          <div className="text-center py-12 text-slate-400 text-sm">트렌드를 불러올 수 없습니다.</div>
                        ) : (
                          healthTrends.map((t, i) => (
                            <motion.a key={i} href={t.url} target="_blank" rel="noopener noreferrer" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }} className="block p-4 rounded-2xl bg-slate-50 border border-slate-100 hover:border-amber-200 hover:bg-amber-50/30 transition-all group">
                              <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">{t.source}</span>
                              <h4 className="font-bold text-slate-800 text-sm mt-1 mb-0.5 group-hover:text-amber-700 transition-colors line-clamp-2">{t.trend}</h4>
                              <p className="text-[11px] text-slate-500 leading-relaxed line-clamp-2">{t.description}</p>
                            </motion.a>
                          ))
                        )}
                      </div>
                    </div>

                    <div className="glass-card p-8 bg-gradient-to-br from-emerald-600 to-teal-700 text-white relative overflow-hidden">
                      <div className="relative z-10">
                        <div className="flex items-center justify-between mb-6">
                          <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm"><Brain size={24} /></div>
                          <button onClick={fetchTip} className="p-2 bg-white/15 rounded-xl hover:bg-white/25 transition-colors" title="다른 팁 보기">
                            <RefreshCw size={14} />
                          </button>
                        </div>
                        <h3 className="text-2xl font-gaegu font-bold mb-4">오늘의 건강 팁 💡</h3>
                        <p className="text-emerald-50/90 leading-relaxed mb-8 font-gaegu text-xl line-clamp-4">
                          "{healthTip?.tip || '오늘도 건강한 하루 보내세요!'}"
                        </p>
                        {healthTip?.url && (
                          <a href={healthTip.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 text-sm font-bold bg-white text-emerald-700 px-6 py-3 rounded-2xl hover:bg-emerald-50 transition-colors">
                            자세히 보기 <ExternalLink size={14} />
                          </a>
                        )}
                      </div>
                      <div className="absolute -bottom-10 -right-10 text-[180px] opacity-10 rotate-12 leading-none">🍃</div>
                    </div>
                  </div>
                </div>

                {/* Bento 4-column */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {/* 최근 복용 기록 */}
                  <div className="glass-card p-6 bg-white flex flex-col">
                    <div className="flex justify-between items-center mb-5">
                      <div className="flex items-center gap-2">
                        <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg"><History size={18} /></div>
                        <h3 className="text-base font-bold text-slate-800">최근 복용 기록</h3>
                      </div>
                      <button onClick={() => setActiveTab('stacks')} className="text-emerald-600 text-[10px] font-bold hover:underline">전체보기</button>
                    </div>
                    <div className="flex-1 space-y-3">
                      {savedStacks.slice(0, 3).map((stack) => (
                        <div key={stack.id} onClick={() => openStack(stack)} className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer group">
                          <div className="w-10 h-10 bg-emerald-50 rounded-lg flex items-center justify-center text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-colors shrink-0">
                            {stack.type === 'prescription' ? <Pill size={16} /> : <Brain size={16} />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-bold text-slate-800 truncate">{stack.title}</p>
                            <p className="text-[10px] text-slate-400">{stack.date}</p>
                          </div>
                          <ChevronRight size={14} className="text-slate-300 shrink-0" />
                        </div>
                      ))}
                      {savedStacks.length === 0 && (
                        <div className="flex-1 flex items-center justify-center py-6">
                          <p className="text-slate-400 text-xs text-center">아직 기록이 없습니다.</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 식단 가이드 */}
                  <div onClick={() => setShowDietModal(true)} className="glass-card p-6 bg-gradient-to-br from-amber-50 to-orange-50 border-amber-100 flex flex-col cursor-pointer group hover:shadow-md transition-all">
                    <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-amber-600 shadow-sm mb-5 group-hover:scale-110 transition-transform"><Utensils size={24} /></div>
                    <h3 className="text-lg font-bold text-amber-900 mb-2">식단 가이드</h3>
                    <p className="text-xs text-amber-700/70 leading-relaxed mb-4 flex-1">내 몸 상태에 맞는 맞춤 영양 식단을 확인하세요. 동의보감 약선 음식을 기반으로 추천합니다.</p>
                    <div className="flex items-center gap-1 text-xs font-bold text-amber-600 group-hover:text-amber-800 transition-colors">식단 분석 시작 <ChevronRight size={14} /></div>
                  </div>

                  {/* 약국 찾기 */}
                  <div onClick={() => setActiveTab('map')} className="glass-card p-6 bg-gradient-to-br from-teal-50 to-cyan-50 border-teal-100 flex flex-col cursor-pointer group hover:shadow-md transition-all">
                    <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-teal-600 shadow-sm mb-5 group-hover:scale-110 transition-transform"><MapPin size={24} /></div>
                    <h3 className="text-lg font-bold text-teal-900 mb-2">약국 찾기</h3>
                    <p className="text-xs text-teal-700/70 leading-relaxed mb-4 flex-1">가장 가까운 안심 약국을 찾아보세요. 영업 중인 약국과 야간 약국 정보를 제공합니다.</p>
                    <div className="flex items-center gap-1 text-xs font-bold text-teal-600 group-hover:text-teal-800 transition-colors">주변 약국 보기 <ChevronRight size={14} /></div>
                  </div>

                  {/* 건강 리포트 */}
                  <div onClick={() => setActiveTab('reports')} className="glass-card p-6 bg-gradient-to-br from-rose-50 to-pink-50 border-rose-100 flex flex-col cursor-pointer group hover:shadow-md transition-all">
                    <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-rose-600 shadow-sm mb-5 group-hover:scale-110 transition-transform"><Activity size={24} /></div>
                    <h3 className="text-lg font-bold text-rose-900 mb-2">건강 리포트</h3>
                    <p className="text-xs text-rose-700/70 leading-relaxed mb-4 flex-1">누적된 건강 데이터를 분석하여 나만의 건강 변화 추이를 한눈에 확인할 수 있습니다.</p>
                    <div className="flex items-center gap-1 text-xs font-bold text-rose-600 group-hover:text-rose-800 transition-colors">리포트 확인 <ChevronRight size={14} /></div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* ────────────── STACKS ────────────── */}
            {activeTab === 'stacks' && (
              <motion.div key="stacks" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-8">
                <div className="flex justify-between items-center">
                  <h2 className="text-3xl font-bold text-slate-800 tracking-tight">복용 스택 아카이브</h2>
                  <div className="flex gap-2">
                    {stackView === 'my' && (
                      <>
                        <button className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-50 transition-colors">필터</button>
                        <button className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-50 transition-colors">내보내기</button>
                        <button onClick={() => fileInputRef.current?.click()} className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-sm font-bold hover:bg-emerald-700 transition-colors flex items-center gap-2">
                          <PlusCircle size={16} /> 새 분석
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {/* 세그먼트 컨트롤: 로그인 시만 표시 */}
                {user && (
                  <div className="flex bg-slate-100 rounded-xl p-1 w-fit">
                    <button
                      onClick={() => setStackView('my')}
                      className={cn(
                        'px-5 py-2 text-sm font-bold rounded-lg transition-all',
                        stackView === 'my'
                          ? 'bg-white text-emerald-700 shadow-sm'
                          : 'text-slate-500 hover:text-slate-700'
                      )}
                    >
                      내 처방전
                    </button>
                    <button
                      onClick={() => setStackView('family')}
                      className={cn(
                        'flex items-center gap-1.5 px-5 py-2 text-sm font-bold rounded-lg transition-all',
                        stackView === 'family'
                          ? 'bg-white text-rose-600 shadow-sm'
                          : 'text-slate-500 hover:text-slate-700'
                      )}
                    >
                      <Users size={14} />
                      가족 처방전
                    </button>
                  </div>
                )}

                {/* 내 처방전 뷰 */}
                {stackView === 'my' && (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                  {savedStacks.map((stack) => (
                    <div key={stack.id} onClick={() => openStack(stack)} className="glass-card p-6 bg-white hover:border-emerald-200 transition-all cursor-pointer group relative">
                      <div className="flex justify-between items-start mb-4">
                        <div className="p-3 bg-emerald-50 rounded-2xl text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
                          {stack.type === 'prescription' ? <FileText size={20} /> : <Brain size={20} />}
                        </div>
                        <button onClick={(e) => deleteStack(e, stack.id)} className="p-2 text-slate-300 hover:text-rose-500 transition-colors">
                          <Trash2 size={18} />
                        </button>
                      </div>
                      <p className="text-[10px] font-bold text-emerald-600 mb-2">{stack.date}</p>
                      <h4 className="text-lg font-bold text-slate-800 mb-4 line-clamp-2">{stack.title}</h4>
                      <span className="px-2 py-1 bg-slate-100 text-slate-500 text-[10px] font-bold rounded-lg">
                        {stack.type === 'prescription' ? '처방전' : '증상'} 분석
                      </span>
                    </div>
                  ))}
                  {savedStacks.length === 0 && (
                    <div className="col-span-full py-40 text-center">
                      <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-6 text-slate-300"><History size={40} /></div>
                      <h3 className="text-xl font-bold text-slate-800 mb-2">아직 저장된 기록이 없습니다.</h3>
                      <p className="text-slate-500 mb-8">처방전을 분석하고 나만의 건강 스택을 쌓아보세요.</p>
                      <button onClick={() => fileInputRef.current?.click()} className="px-8 py-3 bg-emerald-600 text-white rounded-2xl font-bold shadow-lg shadow-emerald-100 hover:bg-emerald-700 transition-all">
                        첫 분석 시작하기
                      </button>
                    </div>
                  )}
                </div>
                )}

                {/* 가족 처방전 뷰 */}
                {stackView === 'family' && (
                  <FamilyPrescriptionsView
                    onViewPrescription={(data, drugList, sections) => {
                      const familyStack: SavedStack = {
                        id: 'family-' + Date.now().toString(),
                        date: new Date().toLocaleDateString('ko-KR', {
                          year: 'numeric', month: 'long', day: 'numeric',
                        }),
                        title: `가족 처방전 (약 ${drugList.length}종)`,
                        type: 'prescription',
                        prescriptionData: {
                          drugs: drugList,
                          analysis_result: data,
                          revealed_sections: sections,
                        } as any,
                      };
                      setModalStack(familyStack);
                      setShowAnalysisModal(true);
                    }}
                  />
                )}
              </motion.div>
            )}

            {/* ────────────── MAP (약국 찾기 - 카카오맵) ────────────── */}
            {activeTab === 'map' && (
              <motion.div key="map" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="space-y-6">
                <div className="flex justify-between items-center">
                  <div>
                    <h2 className="text-3xl font-bold text-slate-800 tracking-tight">주변 약국 찾기</h2>
                    <p className="text-slate-500 text-sm mt-1">내 위치 기반 반경 2km 내 약국을 검색합니다.</p>
                  </div>
                  <button
                    onClick={() => { kakaoMapRef.current = null; initPharmacyMap(); }}
                    disabled={pharmacyLoading}
                    className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-50 transition-colors disabled:opacity-50"
                  >
                    <RefreshCw size={16} className={pharmacyLoading ? 'animate-spin' : ''} />
                    새로고침
                  </button>
                </div>

                {pharmacyError && (
                  <div className="p-4 bg-rose-50 border border-rose-100 rounded-2xl text-sm text-rose-600">
                    {pharmacyError}
                  </div>
                )}

                {/* Map + List Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-6" style={{ minHeight: '500px' }}>
                  {/* Map (3/5) */}
                  <div className="lg:col-span-3 glass-card overflow-hidden bg-white relative">
                    <div ref={mapRef} className="w-full h-full min-h-[500px]" />
                    {/* Initial placeholder — shown until user triggers search */}
                    {!pharmacyLoading && pharmacies.length === 0 && (
                      <div className="absolute inset-0 bg-slate-50 flex flex-col items-center justify-center z-10">
                        <div className="w-20 h-20 bg-teal-50 rounded-[32px] flex items-center justify-center mb-6">
                          <MapPin size={40} className="text-teal-400" />
                        </div>
                        <p className="text-slate-600 font-bold mb-1">지도가 여기에 표시됩니다</p>
                        <p className="text-slate-400 text-xs">오른쪽의 약국 찾기 버튼을 눌러 시작하세요.</p>
                      </div>
                    )}
                    {pharmacyLoading && (
                      <div className="absolute inset-0 bg-white/80 flex flex-col items-center justify-center z-10">
                        <Loader2 size={40} className="text-teal-500 animate-spin mb-4" />
                        <p className="text-slate-600 font-medium text-sm">주변 약국을 검색하고 있어요...</p>
                      </div>
                    )}
                  </div>

                  {/* Pharmacy List (2/5) */}
                  <div className="lg:col-span-2 space-y-3 overflow-y-auto max-h-[600px] pr-1">
                    {pharmacies.length > 0 ? (
                      pharmacies.map((p, i) => (
                        <PharmacyCard
                          key={i}
                          pharmacy={p}
                          index={i}
                          selected={selectedPharmacy?.name === p.name}
                          onClick={() => {
                            setSelectedPharmacy(p);
                            if (kakaoMapRef.current) {
                              kakaoMapRef.current.panTo(new kakao.maps.LatLng(p.lat, p.lng));
                            }
                          }}
                        />
                      ))
                    ) : !pharmacyLoading ? (
                      <div className="flex flex-col items-center justify-center py-16 text-center px-4">
                        <div className="w-16 h-16 bg-teal-50 rounded-[24px] flex items-center justify-center mb-5">
                          <Navigation size={32} className="text-teal-500" />
                        </div>
                        <p className="text-slate-700 font-bold text-sm mb-1">내 위치로 약국 찾기</p>
                        <p className="text-slate-400 text-xs leading-relaxed mb-6">
                          반경 2km 내 약국을 지도에 표시합니다.<br/>
                          위치 권한 허용이 필요합니다.
                        </p>
                        <button
                          onClick={initPharmacyMap}
                          className="flex items-center gap-2 px-6 py-3 bg-teal-500 text-white text-sm font-bold rounded-2xl hover:bg-teal-600 transition-colors shadow-lg shadow-teal-100 active:scale-95"
                        >
                          <Navigation size={16} />
                          약국 검색 시작
                        </button>
                      </div>
                    ) : null}
                  </div>
                </div>
              </motion.div>
            )}

            {/* ────────────── HEALTH REPORT ────────────── */}
            {activeTab === 'reports' && (() => {
              // --- 집계 연산 ---
              const drugFreq: Record<string, number> = {};
              const symptomFreq: Record<string, number> = {};
              const seenFoods = new Set<string>();
              const uniqueFoods: { name: string; reason: string }[] = [];

              const allWarnings: string[] = [];
              const allAdvice: string[] = [];
              const drugEfficacy: Record<string, string> = {};
              let latestDoctorAnalysis = '';

              savedStacks.forEach(s => {
                const drugs = s.prescriptionData?.prescriptionSummary?.drugList ?? [];
                drugs.forEach(d => { drugFreq[d] = (drugFreq[d] || 0) + 1; });

                const symptoms = s.prescriptionData?.lifestyleGuide?.symptomTokens ?? [];
                symptoms.forEach(t => { symptomFreq[t] = (symptomFreq[t] || 0) + 1; });

                const foods = s.prescriptionData?.donguibogam?.foods ?? [];
                foods.forEach(f => {
                  if (!seenFoods.has(f.name)) { seenFoods.add(f.name); uniqueFoods.push(f); }
                });

                // AI 분석 결과 수집
                const warn = s.prescriptionData?.prescriptionSummary?.warnings;
                if (warn) {
                  if (typeof warn === 'object' && !Array.isArray(warn) && 'analysis' in warn) {
                    // DoctorAnalysis 형식: 종합분석 소견 + 주의사항 분리
                    const da = warn as { analysis: string; criticalAlerts: string[] };
                    if (da.analysis?.trim() && !latestDoctorAnalysis) latestDoctorAnalysis = da.analysis.trim();
                    da.criticalAlerts?.forEach(a => { if (a.trim()) allWarnings.push(a.trim()); });
                  } else if (Array.isArray(warn)) {
                    warn.forEach(w => { if (w.trim()) allWarnings.push(w.trim()); });
                  } else if (typeof warn === 'string' && warn.trim()) {
                    allWarnings.push(warn.trim());
                  }
                }

                const advice = s.prescriptionData?.lifestyleGuide?.advice;
                if (advice && advice.trim()) allAdvice.push(advice.trim());

                (s.prescriptionData?.drugDetails ?? []).forEach(d => {
                  if (d.efficacy && !drugEfficacy[d.name]) drugEfficacy[d.name] = d.efficacy;
                });
              });

              const topDrugs = Object.entries(drugFreq).sort((a, b) => b[1] - a[1]).slice(0, 5);
              const topSymptoms = Object.entries(symptomFreq).sort((a, b) => b[1] - a[1]).slice(0, 12);
              const totalDrugTypes = Object.keys(drugFreq).length;

              // 주요 약물 효능 요약 (상위 3개)
              const topDrugSummaries = topDrugs.slice(0, 3).map(([name]) => ({
                name,
                efficacy: drugEfficacy[name] || '',
              })).filter(d => d.efficacy);

              return savedStacks.length === 0 ? (
                <motion.div key="reports-empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center py-40 text-center">
                  <div className="w-24 h-24 bg-emerald-50 rounded-[40px] flex items-center justify-center text-emerald-600 mb-8">
                    <Activity size={48} />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-800 mb-3">건강 리포트</h2>
                  <p className="text-slate-500 text-sm mb-6">처방전을 분석하면 나만의 건강 리포트가 만들어져요</p>
                  <button onClick={() => setActiveTab('dashboard')} className="px-6 py-2.5 bg-emerald-600 text-white text-sm font-bold rounded-2xl hover:bg-emerald-700 transition-colors">대시보드에서 시작하기</button>
                </motion.div>
              ) : (
                <motion.div key="reports" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8 pb-10">
                  <h2 className="text-3xl font-bold text-slate-800 tracking-tight">건강 리포트</h2>

                  {/* 섹션 1: 나의 건강 한눈에 */}
                  <div className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-[32px] p-8 text-white shadow-lg">
                    <p className="text-xs font-bold opacity-70 uppercase tracking-widest mb-5">나의 건강 한눈에</p>
                    <div className="grid grid-cols-3 gap-4 text-center mb-4">
                      <div className="bg-white/15 rounded-2xl p-4">
                        <p className="text-4xl font-bold">{savedStacks.length}</p>
                        <p className="text-sm opacity-80 mt-1">총 분석</p>
                      </div>
                      <div className="bg-white/15 rounded-2xl p-4">
                        <p className="text-4xl font-bold">{totalDrugTypes}</p>
                        <p className="text-sm opacity-80 mt-1">약물 종류</p>
                      </div>
                      <div className="bg-white/15 rounded-2xl p-4">
                        <p className="text-4xl font-bold">{topSymptoms.length}</p>
                        <p className="text-sm opacity-80 mt-1">확인 증상</p>
                      </div>
                    </div>
                    <p className="text-xs opacity-60 text-center">최근 분석: {savedStacks[0]?.date}</p>
                  </div>

                  {/* AI 분석 종합 요약 */}
                  <div className="bg-white rounded-[32px] p-8 shadow-sm border border-slate-100 space-y-6">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-violet-100 rounded-xl flex items-center justify-center">
                        <Sparkles size={20} className="text-violet-600" />
                      </div>
                      <h3 className="text-lg font-bold text-slate-800">AI 분석 종합 요약</h3>
                    </div>

                    {/* 주치의 종합분석 소견 */}
                    {latestDoctorAnalysis && (
                      <div>
                        <p className="text-xs font-bold text-blue-700 uppercase tracking-widest mb-3">주치의 종합분석</p>
                        <div className="p-5 bg-blue-50/50 rounded-xl">
                          {latestDoctorAnalysis.split('\n\n').filter(Boolean).map((paragraph, i) => (
                            <p key={i} className="text-sm text-slate-700 leading-relaxed mb-3 last:mb-0">
                              {paragraph.split('\n').map((line, j) => (
                                <span key={j}>{j > 0 && <br />}{line}</span>
                              ))}
                            </p>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 주요 약물 효능 */}
                    {topDrugSummaries.length > 0 && (
                      <div>
                        <p className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-3">주요 복용 약물 분석</p>
                        <div className="space-y-2">
                          {topDrugSummaries.map(d => (
                            <div key={d.name} className="flex gap-3 p-3 bg-blue-50/50 rounded-xl items-start">
                              <span className="text-xs font-bold text-blue-600 bg-blue-100 px-2.5 py-1 rounded-full h-fit shrink-0">{d.name}</span>
                              <p className="text-sm text-slate-600 leading-relaxed line-clamp-2">{d.efficacy}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 주의사항 종합 (AI 주치의 기반) */}
                    {allWarnings.length > 0 && (
                      <div>
                        <p className="text-xs font-bold text-rose-600 uppercase tracking-widest mb-3">주의사항 안내</p>
                        <div className="p-5 bg-rose-50/50 rounded-xl space-y-2">
                          {allWarnings.slice(0, 7).map((w, i) => (
                            <p key={i} className="text-sm text-rose-800/80 leading-relaxed flex gap-2">
                              <span className="text-rose-400 shrink-0">&#9888;</span>
                              <span>{w}</span>
                            </p>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 생활 가이드 종합 */}
                    {allAdvice.length > 0 && (
                      <div>
                        <p className="text-xs font-bold text-emerald-600 uppercase tracking-widest mb-3">생활 관리 조언</p>
                        <div className="p-5 bg-emerald-50/50 rounded-xl">
                          <p className="text-sm text-emerald-800/80 leading-relaxed line-clamp-4">{allAdvice[allAdvice.length - 1]}</p>
                          {allAdvice.length > 1 && (
                            <p className="text-xs text-emerald-400 mt-2">외 {allAdvice.length - 1}건의 분석 결과 포함</p>
                          )}
                        </div>
                      </div>
                    )}

                    {/* 추천 식재료 한줄 요약 */}
                    {uniqueFoods.length > 0 && (
                      <div className="flex items-start gap-2 p-4 bg-amber-50/50 rounded-xl">
                        <span className="text-base shrink-0">🌿</span>
                        <p className="text-sm text-amber-800/80 leading-relaxed">
                          분석된 처방 기반 추천 식재료: <strong>{uniqueFoods.slice(0, 5).map(f => f.name).join(', ')}</strong>
                          {uniqueFoods.length > 5 && ` 외 ${uniqueFoods.length - 5}종`}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* 2단 그리드 */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                    {/* 섹션 2: 자주 처방받은 약물 */}
                    {topDrugs.length > 0 && (
                      <div className="space-y-3">
                        <div className="flex items-center gap-2">
                          <span className="bg-blue-600 text-white text-xs font-bold px-2.5 py-0.5 rounded-full">TOP</span>
                          <h3 className="text-blue-500 text-xs font-bold uppercase tracking-widest">자주 처방받은 약물</h3>
                        </div>
                        <div className="bg-white rounded-[24px] p-5 shadow-sm border border-blue-50 space-y-3">
                          {topDrugs.map(([name, count], i) => (
                            <div key={name} className="flex items-center gap-3">
                              <span className="w-7 h-7 bg-blue-50 text-blue-600 rounded-full text-xs font-bold flex items-center justify-center flex-shrink-0">{i + 1}</span>
                              <div className="flex-1">
                                <div className="flex justify-between items-center mb-1">
                                  <p className="text-sm font-bold text-slate-700 break-keep">{name}</p>
                                  <p className="text-xs text-blue-400 font-bold">{count}회</p>
                                </div>
                                <div className="w-full bg-blue-50 rounded-full h-2">
                                  <div className="bg-blue-400 h-2 rounded-full transition-all" style={{ width: `${(count / savedStacks.length) * 100}%` }} />
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 섹션 4: 자주 나타나는 증상 */}
                    {topSymptoms.length > 0 && (
                      <div className="space-y-3">
                        <div className="flex items-center gap-2">
                          <span className="bg-purple-600 text-white text-xs font-bold px-2.5 py-0.5 rounded-full">증상</span>
                          <h3 className="text-purple-500 text-xs font-bold uppercase tracking-widest">자주 나타나는 증상</h3>
                        </div>
                        <div className="bg-white rounded-[24px] p-5 shadow-sm border border-purple-50">
                          <div className="flex flex-wrap gap-2">
                            {topSymptoms.map(([token, count]) => (
                              <span key={token} className="px-3 py-1.5 rounded-xl font-bold border"
                                style={{ fontSize: `${Math.min(16, 12 + count)}px`, background: count > 1 ? '#f3f0ff' : '#fafaf9', color: count > 1 ? '#7c3aed' : '#78716c', borderColor: count > 1 ? '#ddd6fe' : '#e7e5e4' }}>
                                {token} {count > 1 && <span className="opacity-60 text-[11px]">&times;{count}</span>}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 섹션 3: 복용 이력 타임라인 */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="bg-emerald-600 text-white text-xs font-bold px-2.5 py-0.5 rounded-full">이력</span>
                      <h3 className="text-emerald-500 text-xs font-bold uppercase tracking-widest">복용 이력 타임라인</h3>
                    </div>
                    <div className="relative pl-4">
                      <div className="absolute left-4 top-0 bottom-0 w-px bg-emerald-100" />
                      <div className="space-y-4">
                        {savedStacks.map(s => {
                          const drugs = s.prescriptionData?.prescriptionSummary?.drugList ?? [];
                          return (
                            <div key={s.id} className="relative pl-6">
                              <div className="absolute left-0 top-1.5 w-3 h-3 rounded-full border-2 border-emerald-400 bg-white" />
                              <div className="bg-white rounded-[20px] p-4 shadow-sm border border-emerald-50">
                                <p className="text-xs text-emerald-400 font-bold mb-1">{s.date}</p>
                                <div className="flex flex-wrap gap-1.5">
                                  {drugs.slice(0, 4).map((d, j) => (
                                    <span key={j} className="text-xs px-2.5 py-1 bg-emerald-50 text-emerald-700 rounded-lg font-bold border border-emerald-100">{d}</span>
                                  ))}
                                  {drugs.length > 4 && (
                                    <span className="text-xs px-2.5 py-1 bg-slate-50 text-slate-400 rounded-lg">+{drugs.length - 4}개</span>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>

                  {/* 섹션 5: 동의보감 식재료 모음 */}
                  {uniqueFoods.length > 0 && (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <span className="bg-amber-500 text-white text-xs font-bold px-2.5 py-0.5 rounded-full">식재료</span>
                        <h3 className="text-amber-700 text-xs font-bold uppercase tracking-widest">내 몸에 자주 필요한 식재료</h3>
                      </div>
                      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                        {uniqueFoods.slice(0, 6).map((f, i) => (
                          <div key={i} className="bg-white rounded-[20px] p-5 shadow-sm border border-amber-50">
                            <p className="text-xl mb-1">🌿</p>
                            <p className="text-sm font-bold text-amber-900 break-keep">{f.name}</p>
                            <p className="text-xs text-slate-400 mt-1 leading-relaxed line-clamp-2">{f.reason}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <p className="text-xs text-slate-400 text-center px-6 leading-relaxed opacity-60">
                    ※ 리포트는 기기에 저장된 분석 이력을 기반으로 합니다.
                  </p>
                </motion.div>
              );
            })()}

            {activeTab === 'settings' && (
              <motion.div key="settings" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
                <SettingsPage />
              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </main>

      {/* ── Analysis Modal (Prescription or Symptom) ── */}
      <AnimatePresence>
        {showAnalysisModal && modalStack && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-10">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setShowAnalysisModal(false)} className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-5xl max-h-[90vh] bg-white rounded-[40px] shadow-2xl overflow-hidden flex flex-col"
            >
              {/* Modal Header */}
              <div className="p-8 border-b border-slate-100 flex items-center justify-between bg-emerald-600 text-white shrink-0">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-md">
                    <FileText size={24} />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold">건강 분석 리포트</h3>
                    <p className="text-emerald-100 text-sm opacity-80">따뜻한 이웃집 약사의 정밀 진단</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => speakText(getSpeakText(modalStack))}
                    className="p-3 bg-white/20 rounded-2xl hover:bg-white/30 transition-colors"
                    title="음성으로 듣기"
                  >
                    <Volume2 size={24} />
                  </button>
                  <button onClick={() => setShowAnalysisModal(false)} className="p-3 bg-white/20 rounded-2xl hover:bg-white/30 transition-colors">
                    <X size={24} />
                  </button>
                </div>
              </div>

              {/* Modal Body */}
              <div className="flex-1 overflow-y-auto p-8">
                {modalStack.type === 'prescription' && modalStack.prescriptionData ? (
                  <PrescriptionReport data={modalStack.prescriptionData} />
                ) : modalStack.report ? (
                  <Step3Report report={modalStack.report} />
                ) : (
                  <p className="text-slate-400 text-center py-20">데이터를 불러올 수 없습니다.</p>
                )}
              </div>

              {/* Medication Reminder Setup Panel */}
              {showMedSetup && modalStack.type === 'prescription' && modalStack.prescriptionData && (
                <MedicationReminderSetup
                  drugList={modalStack.prescriptionData.prescriptionSummary.drugList}
                  onClose={() => setShowMedSetup(false)}
                />
              )}

              {/* Modal Footer */}
              <div className="p-8 bg-slate-50 border-t border-slate-100 flex justify-between items-center shrink-0">
                <p className="text-[10px] text-slate-400 max-w-md">
                  ※ 이 분석은 AI 기술을 기반으로 하며, 참고용으로만 사용하시기 바랍니다.
                  정확한 의학적 판단은 반드시 전문의와 상담하세요.
                </p>
                <div className="flex gap-3">
                  {modalStack.type === 'prescription' && modalStack.prescriptionData && !showMedSetup && (
                    <button
                      onClick={() => setShowMedSetup(true)}
                      className="px-6 py-3 bg-emerald-600 text-white rounded-2xl font-bold hover:bg-emerald-700 transition-colors flex items-center gap-2 shadow-lg shadow-emerald-100"
                    >
                      <Bell size={16} />
                      복약 알림 설정
                    </button>
                  )}
                  <button onClick={() => { setShowAnalysisModal(false); setShowMedSetup(false); }} className="px-10 py-3 bg-slate-800 text-white rounded-2xl font-bold hover:bg-slate-900 transition-colors shadow-lg shadow-slate-200">
                    확인 완료
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── Diet Guide Modal ── */}
      <AnimatePresence>
        {showDietModal && (
          <DietGuideModal
            savedStacks={savedStacks}
            onClose={() => setShowDietModal(false)}
            onAnalyzePrescription={() => { setShowDietModal(false); fileInputRef.current?.click(); }}
          />
        )}
      </AnimatePresence>

      {/* ── Symptom Wizard Modal ── */}
      <AnimatePresence>
        {showSymptomModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setShowSymptomModal(false)} className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-md max-h-[90vh] bg-white rounded-[40px] shadow-2xl overflow-hidden flex flex-col"
            >
              <div className="p-5 border-b border-slate-100 flex items-center justify-between shrink-0">
                <h3 className="text-lg font-bold text-slate-800">증상 분석</h3>
                <button onClick={() => setShowSymptomModal(false)} className="p-2 text-slate-400 hover:text-slate-600 transition-colors rounded-xl hover:bg-slate-100">
                  <X size={22} />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto">
                <AnalysisWizard onReportComplete={handleSymptomReport} />
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── Loading Overlay ── */}
      {loading && (
        <div className="fixed inset-0 bg-white/90 backdrop-blur-xl z-[200] flex flex-col items-center justify-center px-10 text-center">
          <motion.div
            animate={{ scale: [1, 1.1, 1], rotate: [0, 5, -5, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="relative w-32 h-32 mb-10"
          >
            <div className="absolute inset-0 border-8 border-emerald-50 rounded-[48px]" />
            <div className="absolute inset-0 border-8 border-emerald-500 border-t-transparent rounded-[48px] animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center text-6xl">🌿</div>
          </motion.div>
          <h3 className="text-3xl font-bold text-slate-800 mb-4 font-gaegu">당신의 건강을 꼼꼼히 살피고 있어요</h3>
          <p className="text-emerald-600 font-gaegu text-2xl tracking-tight max-w-md">{loadingStep}</p>

          {/* Progress Bar */}
          <div className="mt-8 w-64 h-2 bg-slate-100 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-emerald-500 rounded-full"
              animate={{ width: `${loadingProgress}%` }}
              transition={{ duration: 0.4 }}
            />
          </div>
          <p className="text-slate-400 text-sm mt-2">{loadingProgress}%</p>

          <button
            onClick={() => { abortRef.current?.abort(); setLoading(false); }}
            className="mt-6 text-xs text-slate-400 hover:text-slate-600 underline"
          >
            취소
          </button>
        </div>
      )}

      {/* Global Toast */}
      <Toast />
    </div>
  );
}
