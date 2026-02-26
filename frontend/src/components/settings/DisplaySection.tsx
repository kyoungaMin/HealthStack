import { Monitor, Sun, Moon, Type, Volume2, Globe } from 'lucide-react';
import { useSettings } from '../../contexts/SettingsContext';
import type { ThemeMode, FontSize, Language } from '../../types/settings';

export default function DisplaySection() {
  const { settings, updateDisplay, showToast } = useSettings();
  const { display } = settings;

  const handleUpdate = (partial: Partial<typeof display>) => {
    updateDisplay(partial);
    showToast('설정이 저장되었습니다');
  };

  const themeOptions: { value: ThemeMode; label: string; icon: typeof Sun }[] = [
    { value: 'light', label: '라이트', icon: Sun },
    { value: 'dark', label: '다크', icon: Moon },
    { value: 'system', label: '시스템', icon: Monitor },
  ];

  const fontOptions: { value: FontSize; label: string; size: string }[] = [
    { value: 'small', label: '작게', size: 'text-xs' },
    { value: 'medium', label: '보통', size: 'text-sm' },
    { value: 'large', label: '크게', size: 'text-base' },
  ];

  const languageOptions: { value: Language; label: string }[] = [
    { value: 'ko', label: '한국어' },
    { value: 'en', label: 'English' },
  ];

  const testTTS = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance('안녕하세요, 건강한 하루 되세요!');
      utter.lang = 'ko-KR';
      utter.rate = display.ttsSpeed;
      window.speechSynthesis.speak(utter);
    }
  };

  return (
    <div className="bg-[var(--bg-surface)] rounded-[32px] p-8 shadow-sm border border-[var(--border-color)] transition-colors duration-300">
      {/* Section Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/40 rounded-xl flex items-center justify-center">
          <Monitor size={20} className="text-purple-600" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)]">디스플레이</h3>
          <p className="text-xs text-[var(--text-secondary)]">화면 테마, 글자 크기, 음성 속도를 설정합니다</p>
        </div>
      </div>

      <div className="space-y-8">
        {/* Theme Mode */}
        <div>
          <label className="block text-sm font-semibold text-[var(--text-primary)] mb-3">테마</label>
          <div className="grid grid-cols-3 gap-3">
            {themeOptions.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                type="button"
                onClick={() => handleUpdate({ themeMode: value })}
                className={`flex flex-col items-center gap-2 px-4 py-4 rounded-2xl border-2 transition-all ${
                  display.themeMode === value
                    ? 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-500 text-emerald-700 dark:text-emerald-300 shadow-md shadow-emerald-100 dark:shadow-emerald-900/20'
                    : 'bg-[var(--bg-primary)] border-[var(--border-color)] text-[var(--text-secondary)] hover:border-emerald-300'
                }`}
              >
                <Icon size={24} />
                <span className="text-sm font-medium">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Font Size */}
        <div>
          <label className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)] mb-3">
            <Type size={16} />
            글자 크기
          </label>
          <div className="grid grid-cols-3 gap-3">
            {fontOptions.map(({ value, label, size }) => (
              <button
                key={value}
                type="button"
                onClick={() => handleUpdate({ fontSize: value })}
                className={`px-4 py-3 rounded-2xl border-2 transition-all ${
                  display.fontSize === value
                    ? 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-500 text-emerald-700 dark:text-emerald-300 shadow-md shadow-emerald-100 dark:shadow-emerald-900/20'
                    : 'bg-[var(--bg-primary)] border-[var(--border-color)] text-[var(--text-secondary)] hover:border-emerald-300'
                }`}
              >
                <span className={`${size} font-medium`}>{label}</span>
              </button>
            ))}
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-2">현재: {display.fontSize === 'small' ? '16px' : display.fontSize === 'medium' ? '18px' : '22px'}</p>
        </div>

        {/* Language */}
        <div>
          <label className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)] mb-3">
            <Globe size={16} />
            언어
          </label>
          <div className="grid grid-cols-2 gap-3">
            {languageOptions.map(({ value, label }) => (
              <button
                key={value}
                type="button"
                onClick={() => handleUpdate({ language: value })}
                className={`px-4 py-3 rounded-2xl border-2 transition-all ${
                  display.language === value
                    ? 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-500 text-emerald-700 dark:text-emerald-300 shadow-md shadow-emerald-100 dark:shadow-emerald-900/20'
                    : 'bg-[var(--bg-primary)] border-[var(--border-color)] text-[var(--text-secondary)] hover:border-emerald-300'
                }`}
              >
                <span className="text-sm font-medium">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* TTS Speed */}
        <div>
          <label className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)] mb-3">
            <Volume2 size={16} />
            음성 읽기 속도
          </label>
          <div className="flex items-center gap-4">
            <span className="text-xs text-[var(--text-secondary)] w-8">느림</span>
            <input
              type="range"
              min={0.5}
              max={2.0}
              step={0.1}
              value={display.ttsSpeed}
              onChange={e => updateDisplay({ ttsSpeed: Number(e.target.value) })}
              className="flex-1 h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-600"
            />
            <span className="text-xs text-[var(--text-secondary)] w-8">빠름</span>
            <span className="text-sm font-bold text-emerald-600 min-w-[40px] text-center">{display.ttsSpeed.toFixed(1)}x</span>
          </div>
          <button
            type="button"
            onClick={testTTS}
            className="mt-3 px-4 py-2 text-xs font-medium bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 rounded-xl hover:bg-emerald-100 dark:hover:bg-emerald-900/50 transition-colors"
          >
            미리 듣기
          </button>
        </div>
      </div>
    </div>
  );
}
