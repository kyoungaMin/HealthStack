import { useState, useRef } from 'react';
import { Info, FileText, Scale, MessageSquare, ChevronRight, X, Send, CheckCircle, Star, Bug, HelpCircle, Lightbulb, MoreHorizontal, ImagePlus, Trash2, Monitor, Smartphone, Mail } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const APP_VERSION = '1.0.0';

type ModalType = 'terms' | 'privacy' | 'licenses' | 'feedback' | null;

// ─── 오픈소스 라이선스 데이터 ──────────────────────────────────────
const OPEN_SOURCE_LIBS = [
  { name: 'React', version: '19.2.0', license: 'MIT', url: 'https://github.com/facebook/react' },
  { name: 'React DOM', version: '19.2.0', license: 'MIT', url: 'https://github.com/facebook/react' },
  { name: 'React Router DOM', version: '7.13.0', license: 'MIT', url: 'https://github.com/remix-run/react-router' },
  { name: 'Supabase JS', version: '2.97.0', license: 'MIT', url: 'https://github.com/supabase/supabase-js' },
  { name: 'Tailwind CSS', version: '4.1.18', license: 'MIT', url: 'https://github.com/tailwindlabs/tailwindcss' },
  { name: 'Framer Motion', version: '12.34.0', license: 'MIT', url: 'https://github.com/framer/motion' },
  { name: 'Lucide React', version: '0.564.0', license: 'ISC', url: 'https://github.com/lucide-icons/lucide' },
  { name: 'Axios', version: '1.13.5', license: 'MIT', url: 'https://github.com/axios/axios' },
  { name: 'clsx', version: '2.1.1', license: 'MIT', url: 'https://github.com/lukeed/clsx' },
  { name: 'tailwind-merge', version: '3.4.0', license: 'MIT', url: 'https://github.com/dcastil/tailwind-merge' },
  { name: 'Vite', version: '7.3.1', license: 'MIT', url: 'https://github.com/vitejs/vite' },
  { name: 'TypeScript', version: '5.9.3', license: 'Apache-2.0', url: 'https://github.com/microsoft/TypeScript' },
];

// ─── 모달 오버레이 ─────────────────────────────────────────────────
function ModalOverlay({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ type: 'spring', duration: 0.4 }}
        className="relative w-full max-w-2xl max-h-[85vh] bg-[var(--bg-surface)] rounded-[32px] shadow-2xl border border-[var(--border-color)] overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-8 py-5 border-b border-[var(--border-color)]">
          <h3 className="text-lg font-bold text-[var(--text-primary)]">{title}</h3>
          <button
            type="button"
            onClick={onClose}
            className="w-9 h-9 flex items-center justify-center rounded-xl bg-[var(--bg-primary)] border border-[var(--border-color)] hover:border-rose-300 transition-colors"
          >
            <X size={18} className="text-[var(--text-secondary)]" />
          </button>
        </div>
        {/* Body */}
        <div className="flex-1 overflow-y-auto px-8 py-6">
          {children}
        </div>
      </motion.div>
    </div>
  );
}

// ─── 이용약관 ──────────────────────────────────────────────────────
function TermsContent() {
  return (
    <div className="space-y-6 text-sm text-[var(--text-primary)] leading-relaxed">
      <section>
        <h4 className="font-bold text-base mb-2">제1조 (목적)</h4>
        <p className="text-[var(--text-secondary)]">
          본 약관은 HealthStack(이하 "서비스")이 제공하는 건강 관리 및 처방 분석 서비스의 이용 조건과 절차, 이용자와 서비스 간의 권리·의무 및 책임사항을 규정함을 목적으로 합니다.
        </p>
      </section>

      <section>
        <h4 className="font-bold text-base mb-2">제2조 (서비스의 내용)</h4>
        <p className="text-[var(--text-secondary)]">서비스는 다음과 같은 기능을 제공합니다:</p>
        <ul className="list-disc pl-5 mt-2 space-y-1 text-[var(--text-secondary)]">
          <li>처방전 이미지 분석 및 약물 정보 제공</li>
          <li>약물 상호작용 검사</li>
          <li>PubMed 기반 의학 근거 요약</li>
          <li>동의보감 기반 한방 정보 제공</li>
          <li>주변 약국 찾기</li>
          <li>건강 뉴스 및 트렌드 정보 제공</li>
        </ul>
      </section>

      <section>
        <h4 className="font-bold text-base mb-2">제3조 (면책 조항)</h4>
        <p className="text-[var(--text-secondary)]">
          본 서비스에서 제공하는 정보는 의학적 조언이 아니며, 전문 의료인의 진단이나 처방을 대체할 수 없습니다.
          건강에 관한 중요한 결정은 반드시 의료 전문가와 상담하시기 바랍니다.
        </p>
      </section>

      <section>
        <h4 className="font-bold text-base mb-2">제4조 (이용자의 의무)</h4>
        <ul className="list-disc pl-5 space-y-1 text-[var(--text-secondary)]">
          <li>타인의 개인정보나 처방전을 무단으로 사용하지 않을 것</li>
          <li>서비스를 불법적인 목적으로 사용하지 않을 것</li>
          <li>서비스의 정상적인 운영을 방해하지 않을 것</li>
        </ul>
      </section>

      <section>
        <h4 className="font-bold text-base mb-2">제5조 (서비스 변경 및 중단)</h4>
        <p className="text-[var(--text-secondary)]">
          서비스는 운영상 또는 기술상의 필요에 의해 제공하는 서비스의 전부 또는 일부를 변경하거나 중단할 수 있습니다.
          서비스 변경 또는 중단 시 사전에 공지합니다.
        </p>
      </section>

      <section>
        <h4 className="font-bold text-base mb-2">제6조 (지적재산권)</h4>
        <p className="text-[var(--text-secondary)]">
          서비스에서 제공하는 콘텐츠의 저작권은 서비스에 귀속됩니다.
          이용자는 서비스를 통해 얻은 정보를 개인적인 용도로만 사용할 수 있습니다.
        </p>
      </section>

      <p className="text-xs text-[var(--text-secondary)] pt-4 border-t border-[var(--border-color)]">
        시행일: 2026년 1월 1일
      </p>
    </div>
  );
}

// ─── 개인정보처리방침 ──────────────────────────────────────────────
function PrivacyContent() {
  return (
    <div className="space-y-6 text-sm text-[var(--text-primary)] leading-relaxed">
      <section>
        <h4 className="font-bold text-base mb-2">1. 수집하는 개인정보</h4>
        <p className="text-[var(--text-secondary)] mb-2">서비스는 다음의 개인정보를 수집합니다:</p>
        <div className="bg-[var(--bg-primary)] rounded-xl p-4 border border-[var(--border-color)]">
          <p className="font-semibold text-xs mb-2">필수 수집 항목</p>
          <ul className="list-disc pl-5 space-y-1 text-xs text-[var(--text-secondary)]">
            <li>Google 계정 정보 (이메일, 이름, 프로필 사진)</li>
          </ul>
          <p className="font-semibold text-xs mt-3 mb-2">선택 수집 항목</p>
          <ul className="list-disc pl-5 space-y-1 text-xs text-[var(--text-secondary)]">
            <li>출생연도, 성별, 키, 체중</li>
            <li>약물/식품 알레르기 정보</li>
            <li>기저 질환 정보</li>
            <li>처방전 이미지 (분석 목적)</li>
          </ul>
        </div>
      </section>

      <section>
        <h4 className="font-bold text-base mb-2">2. 개인정보의 이용 목적</h4>
        <ul className="list-disc pl-5 space-y-1 text-[var(--text-secondary)]">
          <li>처방전 분석 및 맞춤형 건강 리포트 제공</li>
          <li>약물 상호작용 경고 및 알레르기 주의사항 알림</li>
          <li>서비스 개선 및 통계 분석</li>
        </ul>
      </section>

      <section>
        <h4 className="font-bold text-base mb-2">3. 개인정보의 보관 및 파기</h4>
        <ul className="list-disc pl-5 space-y-1 text-[var(--text-secondary)]">
          <li>처방전 이미지: 분석 완료 후 즉시 삭제 (자동 삭제 설정 시) 또는 설정된 보관 기간 후 삭제</li>
          <li>건강 프로필: 회원 탈퇴 시 즉시 삭제</li>
          <li>분석 기록: 설정된 보관 기간 경과 후 자동 삭제</li>
        </ul>
      </section>

      <section>
        <h4 className="font-bold text-base mb-2">4. 개인정보의 제3자 제공</h4>
        <p className="text-[var(--text-secondary)]">
          서비스는 이용자의 동의 없이 개인정보를 제3자에게 제공하지 않습니다.
          단, 법령에 의해 요구되는 경우는 예외로 합니다.
        </p>
      </section>

      <section>
        <h4 className="font-bold text-base mb-2">5. 개인정보 보호 조치</h4>
        <ul className="list-disc pl-5 space-y-1 text-[var(--text-secondary)]">
          <li>데이터 전송 시 SSL/TLS 암호화 적용</li>
          <li>Supabase Row Level Security (RLS) 정책을 통한 접근 제어</li>
          <li>최소 권한 원칙에 따른 데이터 접근 관리</li>
        </ul>
      </section>

      <section>
        <h4 className="font-bold text-base mb-2">6. 이용자의 권리</h4>
        <ul className="list-disc pl-5 space-y-1 text-[var(--text-secondary)]">
          <li>개인정보 열람, 수정, 삭제 요청</li>
          <li>처리 정지 요청</li>
          <li>회원 탈퇴를 통한 전체 데이터 삭제</li>
        </ul>
      </section>

      <p className="text-xs text-[var(--text-secondary)] pt-4 border-t border-[var(--border-color)]">
        시행일: 2026년 1월 1일 · 문의: support@healthstack.app
      </p>
    </div>
  );
}

// ─── 오픈소스 라이선스 ─────────────────────────────────────────────
function LicensesContent() {
  return (
    <div className="space-y-4">
      <p className="text-sm text-[var(--text-secondary)] mb-4">
        본 서비스는 아래 오픈소스 소프트웨어를 사용하여 개발되었습니다.
        각 소프트웨어의 저작권과 라이선스를 존중하며, 해당 라이선스 조건에 따라 사용하고 있습니다.
      </p>

      <div className="space-y-2">
        {OPEN_SOURCE_LIBS.map((lib, i) => (
          <motion.a
            key={lib.name}
            href={lib.url}
            target="_blank"
            rel="noopener noreferrer"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03 }}
            className="flex items-center justify-between px-4 py-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-color)] hover:border-emerald-300 transition-all group"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900/40 rounded-lg flex items-center justify-center">
                <Scale size={14} className="text-purple-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-[var(--text-primary)]">{lib.name}</p>
                <p className="text-xs text-[var(--text-secondary)]">v{lib.version}</p>
              </div>
            </div>
            <span className="text-xs font-medium px-2.5 py-1 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 rounded-lg">
              {lib.license}
            </span>
          </motion.a>
        ))}
      </div>
    </div>
  );
}

// ─── 공통 입력 스타일 ──────────────────────────────────────────────
const inputClass = "w-full px-4 py-2.5 text-sm bg-[var(--bg-primary)] text-[var(--text-primary)] border border-[var(--border-color)] rounded-xl outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-50 transition-all placeholder:text-[var(--text-secondary)]";
const textareaClass = `${inputClass} resize-none`;
const labelClass = "block text-sm font-semibold text-[var(--text-primary)] mb-2";

// ─── 디바이스 정보 자동 수집 ───────────────────────────────────────
function getDeviceInfo() {
  const ua = navigator.userAgent;
  const isMobile = /Mobi|Android|iPhone|iPad/i.test(ua);
  let browser = 'Unknown';
  if (ua.includes('Firefox')) browser = 'Firefox';
  else if (ua.includes('Edg')) browser = 'Edge';
  else if (ua.includes('Chrome')) browser = 'Chrome';
  else if (ua.includes('Safari')) browser = 'Safari';

  let os = 'Unknown';
  if (ua.includes('Windows')) os = 'Windows';
  else if (ua.includes('Mac OS')) os = 'macOS';
  else if (ua.includes('Android')) os = 'Android';
  else if (ua.includes('iPhone') || ua.includes('iPad')) os = 'iOS';
  else if (ua.includes('Linux')) os = 'Linux';

  return {
    device: isMobile ? '모바일' : 'PC',
    browser,
    os,
    screenSize: `${window.innerWidth}x${window.innerHeight}`,
    url: window.location.href,
  };
}

// ─── 피드백 저장 유틸 ──────────────────────────────────────────────
function saveFeedback(data: Record<string, unknown>) {
  const entry = {
    ...data,
    timestamp: new Date().toISOString(),
    appVersion: APP_VERSION,
    deviceInfo: getDeviceInfo(),
  };
  const stored = localStorage.getItem('health_feedback') ?? '[]';
  const list = JSON.parse(stored);
  list.push(entry);
  localStorage.setItem('health_feedback', JSON.stringify(list));
}

// ─── 제출 완료 화면 ───────────────────────────────────────────────
function SubmittedView({ onClose, title, desc }: { onClose: () => void; title: string; desc: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center justify-center py-12 text-center"
    >
      <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-900/40 rounded-2xl flex items-center justify-center mb-4">
        <CheckCircle size={32} className="text-emerald-600" />
      </div>
      <h4 className="text-lg font-bold text-[var(--text-primary)] mb-2">{title}</h4>
      <p className="text-sm text-[var(--text-secondary)] mb-6 whitespace-pre-line">{desc}</p>
      <button type="button" onClick={onClose} className="px-6 py-2.5 text-sm font-medium bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition-colors">
        닫기
      </button>
    </motion.div>
  );
}

// ─── 스크린샷 첨부 컴포넌트 ───────────────────────────────────────
function ScreenshotAttach({ screenshots, onChange }: { screenshots: string[]; onChange: (s: string[]) => void }) {
  const fileRef = useRef<HTMLInputElement>(null);

  const addScreenshot = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      alert('파일 크기는 5MB 이하여야 합니다.');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      onChange([...screenshots, reader.result as string]);
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  return (
    <div>
      <label className={labelClass}>스크린샷 첨부 <span className="font-normal text-[var(--text-secondary)]">(선택, 최대 3장)</span></label>
      <div className="flex gap-3 flex-wrap">
        {screenshots.map((src, i) => (
          <div key={i} className="relative group">
            <img src={src} alt={`screenshot-${i + 1}`} className="w-20 h-20 object-cover rounded-xl border border-[var(--border-color)]" />
            <button
              type="button"
              onClick={() => onChange(screenshots.filter((_, j) => j !== i))}
              className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-rose-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <Trash2 size={10} className="text-white" />
            </button>
          </div>
        ))}
        {screenshots.length < 3 && (
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="w-20 h-20 rounded-xl border-2 border-dashed border-[var(--border-color)] flex flex-col items-center justify-center gap-1 hover:border-emerald-400 transition-colors text-[var(--text-secondary)]"
          >
            <ImagePlus size={18} />
            <span className="text-[10px]">추가</span>
          </button>
        )}
      </div>
      <input ref={fileRef} type="file" accept="image/*" onChange={addScreenshot} className="hidden" />
    </div>
  );
}

// ─── 1. 기능 제안 폼 ──────────────────────────────────────────────
function FeatureForm({ onClose }: { onClose: () => void }) {
  const [title, setTitle] = useState('');
  const [detail, setDetail] = useState('');
  const [rating, setRating] = useState(0);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    if (!title.trim()) return;
    saveFeedback({ category: 'feature', title: title.trim(), detail: detail.trim(), rating });
    setSubmitted(true);
  };

  if (submitted) return <SubmittedView onClose={onClose} title="제안해 주셔서 감사합니다!" desc="소중한 아이디어를 검토 후 반영하겠습니다." />;

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3 px-4 py-3 bg-sky-50 dark:bg-sky-900/20 border border-sky-200 dark:border-sky-800 rounded-xl">
        <Lightbulb size={18} className="text-sky-600 shrink-0" />
        <p className="text-xs text-sky-700 dark:text-sky-300">어떤 기능이 있으면 좋겠는지 자유롭게 제안해 주세요!</p>
      </div>

      <div>
        <label className={labelClass}>제안 제목 <span className="text-rose-500">*</span></label>
        <input type="text" value={title} onChange={e => setTitle(e.target.value)} placeholder="예: 복약 알림 반복 설정 기능" className={inputClass} />
      </div>

      <div>
        <label className={labelClass}>상세 설명</label>
        <textarea value={detail} onChange={e => setDetail(e.target.value)} placeholder="이 기능이 필요한 이유나 구체적인 동작 방식을 설명해 주세요..." rows={4} className={textareaClass} />
      </div>

      <div>
        <label className={labelClass}>전반적 만족도</label>
        <div className="flex gap-2">
          {[1, 2, 3, 4, 5].map(n => (
            <button key={n} type="button" onClick={() => setRating(n)} className="transition-transform hover:scale-110">
              <Star size={28} className={n <= rating ? 'text-amber-400 fill-amber-400' : 'text-slate-300 dark:text-slate-600'} />
            </button>
          ))}
        </div>
      </div>

      <button type="button" onClick={handleSubmit} disabled={!title.trim()} className="w-full flex items-center justify-center gap-2 py-3.5 text-sm font-bold bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-emerald-200 dark:shadow-emerald-900/30">
        <Send size={16} />
        제안 보내기
      </button>
    </div>
  );
}

// ─── 2. 버그 신고 폼 ──────────────────────────────────────────────
function BugForm({ onClose }: { onClose: () => void }) {
  const [title, setTitle] = useState('');
  const [steps, setSteps] = useState('');
  const [expected, setExpected] = useState('');
  const [actual, setActual] = useState('');
  const [severity, setSeverity] = useState<'low' | 'medium' | 'high' | 'critical'>('medium');
  const [screenshots, setScreenshots] = useState<string[]>([]);
  const [submitted, setSubmitted] = useState(false);

  const deviceInfo = getDeviceInfo();

  const severityOptions: { value: typeof severity; label: string; color: string }[] = [
    { value: 'low', label: '낮음', color: 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800' },
    { value: 'medium', label: '보통', color: 'bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800' },
    { value: 'high', label: '높음', color: 'bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-800' },
    { value: 'critical', label: '심각', color: 'bg-rose-100 text-rose-700 border-rose-200 dark:bg-rose-900/30 dark:text-rose-300 dark:border-rose-800' },
  ];

  const handleSubmit = () => {
    if (!title.trim()) return;
    saveFeedback({
      category: 'bug',
      title: title.trim(),
      steps: steps.trim(),
      expected: expected.trim(),
      actual: actual.trim(),
      severity,
      screenshots,
      deviceInfo,
    });
    setSubmitted(true);
  };

  if (submitted) return <SubmittedView onClose={onClose} title="버그 신고 완료!" desc={"신고하신 문제를 빠르게 확인하겠습니다.\n수정 후 업데이트에 반영됩니다."} />;

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3 px-4 py-3 bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 rounded-xl">
        <Bug size={18} className="text-rose-600 shrink-0" />
        <p className="text-xs text-rose-700 dark:text-rose-300">버그를 상세히 설명해 주시면 더 빠르게 수정할 수 있습니다.</p>
      </div>

      {/* Title */}
      <div>
        <label className={labelClass}>버그 제목 <span className="text-rose-500">*</span></label>
        <input type="text" value={title} onChange={e => setTitle(e.target.value)} placeholder="예: 다크모드에서 텍스트가 안 보임" className={inputClass} />
      </div>

      {/* Severity */}
      <div>
        <label className={labelClass}>심각도</label>
        <div className="grid grid-cols-4 gap-2">
          {severityOptions.map(({ value, label, color }) => (
            <button
              key={value}
              type="button"
              onClick={() => setSeverity(value)}
              className={`px-3 py-2 text-xs font-medium rounded-xl border transition-all ${
                severity === value ? color + ' shadow-sm' : 'bg-[var(--bg-primary)] text-[var(--text-secondary)] border-[var(--border-color)] hover:border-emerald-300'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Steps */}
      <div>
        <label className={labelClass}>재현 단계</label>
        <textarea value={steps} onChange={e => setSteps(e.target.value)} placeholder={"1. 설정 탭을 클릭\n2. 다크모드로 전환\n3. 프로필 섹션 확인"} rows={3} className={textareaClass} />
      </div>

      {/* Expected / Actual */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={labelClass}>예상 동작</label>
          <textarea value={expected} onChange={e => setExpected(e.target.value)} placeholder="어떻게 동작해야 하는지..." rows={2} className={textareaClass} />
        </div>
        <div>
          <label className={labelClass}>실제 동작</label>
          <textarea value={actual} onChange={e => setActual(e.target.value)} placeholder="실제로 어떻게 동작하는지..." rows={2} className={textareaClass} />
        </div>
      </div>

      {/* Screenshots */}
      <ScreenshotAttach screenshots={screenshots} onChange={setScreenshots} />

      {/* Device Info (auto-detected) */}
      <div>
        <label className={labelClass}>환경 정보 <span className="font-normal text-[var(--text-secondary)]">(자동 수집)</span></label>
        <div className="grid grid-cols-2 gap-2">
          {[
            { icon: deviceInfo.device === '모바일' ? Smartphone : Monitor, label: deviceInfo.device, value: deviceInfo.os },
            { icon: Monitor, label: '브라우저', value: deviceInfo.browser },
            { icon: Monitor, label: '화면 크기', value: deviceInfo.screenSize },
            { icon: Monitor, label: '앱 버전', value: `v${APP_VERSION}` },
          ].map(({ label, value }, i) => (
            <div key={i} className="flex items-center gap-2 px-3 py-2 bg-[var(--bg-primary)] rounded-lg border border-[var(--border-color)]">
              <span className="text-[10px] text-[var(--text-secondary)]">{label}</span>
              <span className="text-xs font-medium text-[var(--text-primary)] ml-auto">{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Submit */}
      <button type="button" onClick={handleSubmit} disabled={!title.trim()} className="w-full flex items-center justify-center gap-2 py-3.5 text-sm font-bold bg-rose-600 text-white rounded-xl hover:bg-rose-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-rose-200 dark:shadow-rose-900/30">
        <Bug size={16} />
        버그 신고하기
      </button>
    </div>
  );
}

// ─── 3. 문의사항 폼 ──────────────────────────────────────────────
function QuestionForm({ onClose }: { onClose: () => void }) {
  const [topic, setTopic] = useState('account');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const topics = [
    { value: 'account', label: '계정/로그인' },
    { value: 'analysis', label: '분석 기능' },
    { value: 'data', label: '데이터/결제' },
    { value: 'other', label: '기타 문의' },
  ];

  const handleSubmit = () => {
    if (!message.trim()) return;
    saveFeedback({ category: 'question', topic, email: email.trim(), message: message.trim() });
    setSubmitted(true);
  };

  if (submitted) return <SubmittedView onClose={onClose} title="문의가 접수되었습니다!" desc={"답변은 입력하신 이메일로 발송됩니다.\n영업일 기준 1~2일 내에 답변드립니다."} />;

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3 px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl">
        <HelpCircle size={18} className="text-blue-600 shrink-0" />
        <p className="text-xs text-blue-700 dark:text-blue-300">궁금한 점이 있으시면 편하게 문의해 주세요.</p>
      </div>

      {/* Topic */}
      <div>
        <label className={labelClass}>문의 주제</label>
        <div className="grid grid-cols-4 gap-2">
          {topics.map(({ value, label }) => (
            <button
              key={value}
              type="button"
              onClick={() => setTopic(value)}
              className={`px-3 py-2.5 text-xs font-medium rounded-xl border transition-all ${
                topic === value
                  ? 'bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-200 dark:shadow-blue-900/30'
                  : 'bg-[var(--bg-primary)] text-[var(--text-secondary)] border-[var(--border-color)] hover:border-blue-300'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Reply Email */}
      <div>
        <label className={labelClass}>
          <span className="flex items-center gap-1.5">
            <Mail size={14} />
            답변 받을 이메일
          </span>
        </label>
        <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="example@email.com" className={inputClass} />
      </div>

      {/* Message */}
      <div>
        <label className={labelClass}>문의 내용 <span className="text-rose-500">*</span></label>
        <textarea value={message} onChange={e => setMessage(e.target.value)} placeholder="문의하실 내용을 자세히 작성해 주세요..." rows={5} className={textareaClass} />
      </div>

      {/* Submit */}
      <button type="button" onClick={handleSubmit} disabled={!message.trim()} className="w-full flex items-center justify-center gap-2 py-3.5 text-sm font-bold bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-blue-200 dark:shadow-blue-900/30">
        <Send size={16} />
        문의 보내기
      </button>

      <p className="text-xs text-[var(--text-secondary)] text-center">
        긴급 문의: support@healthstack.app
      </p>
    </div>
  );
}

// ─── 4. 기타 피드백 폼 ────────────────────────────────────────────
function OtherForm({ onClose }: { onClose: () => void }) {
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const [rating, setRating] = useState(0);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    if (!message.trim()) return;
    saveFeedback({ category: 'other', message: message.trim(), email: email.trim(), rating });
    setSubmitted(true);
  };

  if (submitted) return <SubmittedView onClose={onClose} title="감사합니다!" desc="소중한 의견이 접수되었습니다." />;

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3 px-4 py-3 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl">
        <MoreHorizontal size={18} className="text-slate-600 dark:text-slate-400 shrink-0" />
        <p className="text-xs text-slate-600 dark:text-slate-300">카테고리에 해당하지 않는 의견을 자유롭게 남겨주세요.</p>
      </div>

      {/* Message */}
      <div>
        <label className={labelClass}>내용 <span className="text-rose-500">*</span></label>
        <textarea value={message} onChange={e => setMessage(e.target.value)} placeholder="의견을 자유롭게 작성해 주세요..." rows={5} className={textareaClass} />
      </div>

      {/* Email (optional) */}
      <div>
        <label className={labelClass}>이메일 <span className="font-normal text-[var(--text-secondary)]">(선택)</span></label>
        <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="답변을 원하시면 이메일을 입력하세요" className={inputClass} />
      </div>

      {/* Rating */}
      <div>
        <label className={labelClass}>전반적 만족도</label>
        <div className="flex gap-2">
          {[1, 2, 3, 4, 5].map(n => (
            <button key={n} type="button" onClick={() => setRating(n)} className="transition-transform hover:scale-110">
              <Star size={28} className={n <= rating ? 'text-amber-400 fill-amber-400' : 'text-slate-300 dark:text-slate-600'} />
            </button>
          ))}
        </div>
      </div>

      {/* Submit */}
      <button type="button" onClick={handleSubmit} disabled={!message.trim()} className="w-full flex items-center justify-center gap-2 py-3.5 text-sm font-bold bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-emerald-200 dark:shadow-emerald-900/30">
        <Send size={16} />
        보내기
      </button>
    </div>
  );
}

// ─── 피드백 / 문의하기 (메인) ─────────────────────────────────────
function FeedbackContent({ onClose }: { onClose: () => void }) {
  const [category, setCategory] = useState<string | null>(null);

  const categories = [
    { value: 'feature', label: '기능 제안', desc: '새로운 기능을 제안합니다', icon: Lightbulb, iconBg: 'bg-sky-100 dark:bg-sky-900/40', iconColor: 'text-sky-600' },
    { value: 'bug', label: '버그 신고', desc: '오류나 문제를 제보합니다', icon: Bug, iconBg: 'bg-rose-100 dark:bg-rose-900/40', iconColor: 'text-rose-600' },
    { value: 'question', label: '문의사항', desc: '궁금한 점을 질문합니다', icon: HelpCircle, iconBg: 'bg-blue-100 dark:bg-blue-900/40', iconColor: 'text-blue-600' },
    { value: 'other', label: '기타', desc: '그 외 자유로운 의견', icon: MoreHorizontal, iconBg: 'bg-slate-100 dark:bg-slate-800', iconColor: 'text-slate-600 dark:text-slate-400' },
  ];

  // 카테고리 미선택: 선택 화면
  if (!category) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-[var(--text-secondary)]">어떤 유형의 피드백을 보내시겠습니까?</p>
        <div className="space-y-3">
          {categories.map(({ value, label, desc, icon: Icon, iconBg, iconColor }) => (
            <motion.button
              key={value}
              type="button"
              onClick={() => setCategory(value)}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="w-full flex items-center gap-4 px-5 py-4 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-2xl hover:border-emerald-300 transition-all group"
            >
              <div className={`w-11 h-11 ${iconBg} rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform`}>
                <Icon size={20} className={iconColor} />
              </div>
              <div className="text-left">
                <p className="text-sm font-semibold text-[var(--text-primary)]">{label}</p>
                <p className="text-xs text-[var(--text-secondary)]">{desc}</p>
              </div>
              <ChevronRight size={16} className="text-[var(--text-secondary)] ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
            </motion.button>
          ))}
        </div>

        <p className="text-xs text-[var(--text-secondary)] text-center pt-2">
          이메일로 직접 문의: support@healthstack.app
        </p>
      </div>
    );
  }

  // 카테고리별 전용 폼
  return (
    <div>
      {/* Back to category select */}
      <button
        type="button"
        onClick={() => setCategory(null)}
        className="flex items-center gap-1.5 text-xs font-medium text-[var(--text-secondary)] hover:text-emerald-600 transition-colors mb-5"
      >
        <ChevronRight size={14} className="rotate-180" />
        카테고리 다시 선택
      </button>

      <AnimatePresence mode="wait">
        <motion.div key={category} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.2 }}>
          {category === 'feature' && <FeatureForm onClose={onClose} />}
          {category === 'bug' && <BugForm onClose={onClose} />}
          {category === 'question' && <QuestionForm onClose={onClose} />}
          {category === 'other' && <OtherForm onClose={onClose} />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

// ─── 메인 컴포넌트 ─────────────────────────────────────────────────
export default function AppInfoSection() {
  const [activeModal, setActiveModal] = useState<ModalType>(null);

  const infoItems: {
    key: ModalType;
    icon: typeof FileText;
    label: string;
    desc: string;
    iconBg: string;
    iconColor: string;
  }[] = [
    {
      key: 'terms',
      icon: FileText,
      label: '이용약관',
      desc: '서비스 이용 조건을 확인합니다',
      iconBg: 'bg-blue-100 dark:bg-blue-900/40',
      iconColor: 'text-blue-600',
    },
    {
      key: 'privacy',
      icon: FileText,
      label: '개인정보처리방침',
      desc: '개인정보 수집·이용에 대한 안내',
      iconBg: 'bg-indigo-100 dark:bg-indigo-900/40',
      iconColor: 'text-indigo-600',
    },
    {
      key: 'licenses',
      icon: Scale,
      label: '오픈소스 라이선스',
      desc: '사용된 오픈소스 소프트웨어 정보',
      iconBg: 'bg-purple-100 dark:bg-purple-900/40',
      iconColor: 'text-purple-600',
    },
    {
      key: 'feedback',
      icon: MessageSquare,
      label: '피드백 · 문의하기',
      desc: '기능 제안, 버그 신고, 문의사항',
      iconBg: 'bg-emerald-100 dark:bg-emerald-900/40',
      iconColor: 'text-emerald-600',
    },
  ];

  const modalTitles: Record<string, string> = {
    terms: '이용약관',
    privacy: '개인정보처리방침',
    licenses: '오픈소스 라이선스',
    feedback: '피드백 · 문의하기',
  };

  const closeModal = () => setActiveModal(null);

  return (
    <>
      <div className="bg-[var(--bg-surface)] rounded-[32px] p-8 shadow-sm border border-[var(--border-color)] transition-colors duration-300">
        {/* Section Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 bg-slate-100 dark:bg-slate-800 rounded-xl flex items-center justify-center">
            <Info size={20} className="text-slate-600 dark:text-slate-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-[var(--text-primary)]">앱 정보</h3>
            <p className="text-xs text-[var(--text-secondary)]">HealthStack v{APP_VERSION}</p>
          </div>
        </div>

        <div className="space-y-3">
          {/* Version Card */}
          <div className="flex items-center justify-between px-5 py-4 bg-[var(--bg-primary)] rounded-2xl border border-[var(--border-color)]">
            <div>
              <p className="text-sm font-semibold text-[var(--text-primary)]">버전 정보</p>
              <p className="text-xs text-[var(--text-secondary)]">최신 버전을 사용하고 있습니다</p>
            </div>
            <span className="text-sm font-bold text-emerald-600">v{APP_VERSION}</span>
          </div>

          {/* Info Items */}
          {infoItems.map(({ key, icon: Icon, label, desc, iconBg, iconColor }) => (
            <button
              key={label}
              type="button"
              onClick={() => setActiveModal(key)}
              className="w-full flex items-center gap-3 px-5 py-4 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-2xl hover:border-emerald-300 transition-all group"
            >
              <div className={`w-10 h-10 ${iconBg} rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform`}>
                <Icon size={18} className={iconColor} />
              </div>
              <div className="flex-1 text-left">
                <p className="text-sm font-semibold text-[var(--text-primary)]">{label}</p>
                <p className="text-xs text-[var(--text-secondary)]">{desc}</p>
              </div>
              <ChevronRight size={16} className="text-[var(--text-secondary)] opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
          ))}
        </div>
      </div>

      {/* Modals */}
      <AnimatePresence>
        {activeModal && (
          <ModalOverlay title={modalTitles[activeModal]} onClose={closeModal}>
            {activeModal === 'terms' && <TermsContent />}
            {activeModal === 'privacy' && <PrivacyContent />}
            {activeModal === 'licenses' && <LicensesContent />}
            {activeModal === 'feedback' && <FeedbackContent onClose={closeModal} />}
          </ModalOverlay>
        )}
      </AnimatePresence>
    </>
  );
}
