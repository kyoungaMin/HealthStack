import { FlaskConical, CheckSquare, BookOpen } from 'lucide-react';
import { useSettings } from '../../contexts/SettingsContext';

const SECTION_LABELS: Record<number, string> = {
  1: '약물 기본 정보',
  2: '상호작용 분석',
  3: 'PubMed 근거 요약',
  4: '맞춤 복약 지도',
  5: '종합 건강 리포트',
};

export default function AnalysisSection() {
  const { settings, updateAnalysis, showToast } = useSettings();
  const { analysis } = settings;

  const toggleSection = (num: number) => {
    const next = analysis.defaultSections.includes(num)
      ? analysis.defaultSections.filter(n => n !== num)
      : [...analysis.defaultSections, num].sort();
    updateAnalysis({ defaultSections: next });
    showToast('설정이 저장되었습니다');
  };

  return (
    <div className="bg-[var(--bg-surface)] rounded-[32px] p-8 shadow-sm border border-[var(--border-color)] transition-colors duration-300">
      {/* Section Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 bg-sky-100 dark:bg-sky-900/40 rounded-xl flex items-center justify-center">
          <FlaskConical size={20} className="text-sky-600" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)]">분석 설정</h3>
          <p className="text-xs text-[var(--text-secondary)]">처방 분석 시 기본 옵션을 설정합니다</p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Default Sections */}
        <div>
          <label className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)] mb-3">
            <CheckSquare size={16} />
            기본 분석 섹션
          </label>
          <p className="text-xs text-[var(--text-secondary)] mb-3">분석 시 기본으로 활성화할 섹션을 선택합니다</p>
          <div className="space-y-2">
            {Object.entries(SECTION_LABELS).map(([num, label]) => {
              const n = Number(num);
              const checked = analysis.defaultSections.includes(n);
              return (
                <button
                  key={n}
                  type="button"
                  onClick={() => toggleSection(n)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl border transition-all text-left ${
                    checked
                      ? 'bg-sky-50 dark:bg-sky-900/20 border-sky-300 dark:border-sky-700'
                      : 'bg-[var(--bg-primary)] border-[var(--border-color)] hover:border-sky-200'
                  }`}
                >
                  <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-colors ${
                    checked
                      ? 'bg-sky-600 border-sky-600'
                      : 'border-[var(--border-color)]'
                  }`}>
                    {checked && (
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <path d="M2.5 6L5 8.5L9.5 3.5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    )}
                  </div>
                  <span className="text-sm font-medium text-[var(--text-primary)]">
                    섹션 {n}. {label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="border-t border-[var(--border-color)]" />

        {/* Toggle Options */}
        <div className="space-y-4">
          {/* Evidence Level */}
          <div className="flex items-center justify-between px-4 py-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-color)]">
            <div>
              <p className="text-sm font-semibold text-[var(--text-primary)]">근거 수준 표시</p>
              <p className="text-xs text-[var(--text-secondary)]">Level A~D 표시 여부</p>
            </div>
            <button
              type="button"
              onClick={() => { updateAnalysis({ showEvidenceLevel: !analysis.showEvidenceLevel }); showToast('설정이 저장되었습니다'); }}
              className={`relative w-12 h-7 rounded-full transition-colors ${
                analysis.showEvidenceLevel ? 'bg-emerald-600' : 'bg-slate-300 dark:bg-slate-600'
              }`}
            >
              <div className={`absolute top-0.5 w-6 h-6 bg-white rounded-full shadow-md transition-transform ${
                analysis.showEvidenceLevel ? 'translate-x-5' : 'translate-x-0.5'
              }`} />
            </button>
          </div>

          {/* Donguibogam */}
          <div className="flex items-center justify-between px-4 py-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-color)]">
            <div className="flex items-center gap-3">
              <BookOpen size={16} className="text-amber-600" />
              <div>
                <p className="text-sm font-semibold text-[var(--text-primary)]">동의보감 섹션 포함</p>
                <p className="text-xs text-[var(--text-secondary)]">분석 시 동의보감 정보를 기본 포함</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => { updateAnalysis({ includeDonguibogam: !analysis.includeDonguibogam }); showToast('설정이 저장되었습니다'); }}
              className={`relative w-12 h-7 rounded-full transition-colors ${
                analysis.includeDonguibogam ? 'bg-emerald-600' : 'bg-slate-300 dark:bg-slate-600'
              }`}
            >
              <div className={`absolute top-0.5 w-6 h-6 bg-white rounded-full shadow-md transition-transform ${
                analysis.includeDonguibogam ? 'translate-x-5' : 'translate-x-0.5'
              }`} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
