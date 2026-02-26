import { useRef } from 'react';
import { User, Heart, ShieldAlert, Camera } from 'lucide-react';
import { useSettings } from '../../contexts/SettingsContext';
import AllergyTagInput from './AllergyTagInput';

export default function ProfileSection() {
  const { settings, updateProfile, showToast } = useSettings();
  const { profile } = settings;
  const fileInputRef = useRef<HTMLInputElement>(null);

  const currentYear = new Date().getFullYear();

  const initials = profile.displayName
    ? profile.displayName.slice(0, 2).toUpperCase()
    : '?';

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      updateProfile({ avatarUrl: reader.result as string });
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className="bg-[var(--bg-surface)] rounded-[32px] p-8 shadow-sm border border-[var(--border-color)] transition-colors duration-300">
      {/* Section Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-900/40 rounded-xl flex items-center justify-center">
          <User size={20} className="text-emerald-600" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)]">프로필 정보</h3>
          <p className="text-xs text-[var(--text-secondary)]">건강 분석 개인화에 활용됩니다</p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Avatar + Name Row */}
        <div className="flex items-center gap-5">
          <div className="relative group">
            {profile.avatarUrl ? (
              <img
                src={profile.avatarUrl}
                alt="프로필"
                className="w-16 h-16 rounded-2xl object-cover border-2 border-[var(--border-color)]"
              />
            ) : (
              <div className="w-16 h-16 rounded-2xl bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center border-2 border-[var(--border-color)]">
                <span className="text-lg font-bold text-emerald-600">{initials}</span>
              </div>
            )}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="absolute -bottom-1 -right-1 w-7 h-7 bg-emerald-600 rounded-lg flex items-center justify-center shadow-md hover:bg-emerald-700 transition-colors"
            >
              <Camera size={14} className="text-white" />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleAvatarChange}
              className="hidden"
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-2">이름</label>
            <input
              type="text"
              value={profile.displayName}
              onChange={e => updateProfile({ displayName: e.target.value })}
              placeholder="이름을 입력하세요"
              className="w-full px-4 py-2.5 text-sm bg-[var(--bg-primary)] text-[var(--text-primary)] border border-[var(--border-color)] rounded-xl outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-50 transition-all placeholder:text-[var(--text-secondary)]"
            />
          </div>
        </div>

        {/* Basic Info Row */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-2">출생연도</label>
            <input
              type="number"
              min={1930}
              max={currentYear}
              value={profile.birthYear ?? ''}
              onChange={e => updateProfile({ birthYear: e.target.value ? Number(e.target.value) : null })}
              placeholder="예: 1985"
              className="w-full px-4 py-2.5 text-sm bg-[var(--bg-primary)] text-[var(--text-primary)] border border-[var(--border-color)] rounded-xl outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-50 transition-all placeholder:text-[var(--text-secondary)]"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-2">성별</label>
            <div className="flex gap-2">
              {([['male', '남성'], ['female', '여성'], ['other', '기타']] as const).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => { updateProfile({ gender: value }); showToast('설정이 저장되었습니다'); }}
                  className={`flex-1 px-3 py-2.5 text-sm font-medium rounded-xl border transition-all ${
                    profile.gender === value
                      ? 'bg-emerald-600 text-white border-emerald-600 shadow-md shadow-emerald-200 dark:shadow-emerald-900/30'
                      : 'bg-[var(--bg-primary)] text-[var(--text-secondary)] border-[var(--border-color)] hover:border-emerald-300'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Height / Weight Row */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-2">키 (cm)</label>
            <input
              type="number"
              min={50}
              max={300}
              step={0.1}
              value={profile.heightCm ?? ''}
              onChange={e => updateProfile({ heightCm: e.target.value ? Number(e.target.value) : null })}
              placeholder="예: 170"
              className="w-full px-4 py-2.5 text-sm bg-[var(--bg-primary)] text-[var(--text-primary)] border border-[var(--border-color)] rounded-xl outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-50 transition-all placeholder:text-[var(--text-secondary)]"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-[var(--text-primary)] mb-2">체중 (kg)</label>
            <input
              type="number"
              min={10}
              max={500}
              step={0.1}
              value={profile.weightKg ?? ''}
              onChange={e => updateProfile({ weightKg: e.target.value ? Number(e.target.value) : null })}
              placeholder="예: 65"
              className="w-full px-4 py-2.5 text-sm bg-[var(--bg-primary)] text-[var(--text-primary)] border border-[var(--border-color)] rounded-xl outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-50 transition-all placeholder:text-[var(--text-secondary)]"
            />
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-[var(--border-color)]" />

        {/* Allergies */}
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 bg-rose-100 dark:bg-rose-900/40 rounded-lg flex items-center justify-center">
            <ShieldAlert size={16} className="text-rose-600" />
          </div>
          <p className="text-sm font-bold text-[var(--text-primary)]">알레르기 및 건강 정보</p>
        </div>

        <AllergyTagInput
          label="약물 알레르기"
          placeholder="예: 페니실린"
          tags={profile.drugAllergies}
          onChange={drugAllergies => { updateProfile({ drugAllergies }); showToast('설정이 저장되었습니다'); }}
        />

        <AllergyTagInput
          label="식품 알레르기"
          placeholder="예: 땅콩, 갑각류"
          tags={profile.foodAllergies}
          onChange={foodAllergies => { updateProfile({ foodAllergies }); showToast('설정이 저장되었습니다'); }}
        />

        {/* Health Conditions */}
        <div className="border-t border-[var(--border-color)]" />
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 bg-amber-100 dark:bg-amber-900/40 rounded-lg flex items-center justify-center">
            <Heart size={16} className="text-amber-600" />
          </div>
          <p className="text-sm font-bold text-[var(--text-primary)]">기저 질환</p>
        </div>

        <AllergyTagInput
          label="기저 질환"
          placeholder="예: 고혈압, 당뇨"
          tags={profile.healthConditions}
          onChange={healthConditions => { updateProfile({ healthConditions }); showToast('설정이 저장되었습니다'); }}
        />
      </div>
    </div>
  );
}
