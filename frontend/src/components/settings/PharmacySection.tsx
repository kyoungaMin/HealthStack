import { MapPin, Star } from 'lucide-react';
import { useSettings } from '../../contexts/SettingsContext';

export default function PharmacySection() {
  const { settings, updatePharmacy, showToast } = useSettings();
  const { pharmacy } = settings;

  return (
    <div className="bg-[var(--bg-surface)] rounded-[32px] p-8 shadow-sm border border-[var(--border-color)] transition-colors duration-300">
      {/* Section Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 bg-teal-100 dark:bg-teal-900/40 rounded-xl flex items-center justify-center">
          <MapPin size={20} className="text-teal-600" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)]">약국 찾기 설정</h3>
          <p className="text-xs text-[var(--text-secondary)]">주변 약국 검색 기본값을 설정합니다</p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Search Radius */}
        <div>
          <label className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)] mb-3">
            <MapPin size={16} />
            기본 검색 반경
          </label>
          <div className="flex items-center gap-4">
            <span className="text-xs text-[var(--text-secondary)] w-8">1km</span>
            <input
              type="range"
              min={1}
              max={5}
              step={0.5}
              value={pharmacy.searchRadiusKm}
              onChange={e => updatePharmacy({ searchRadiusKm: Number(e.target.value) })}
              className="flex-1 h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-600"
            />
            <span className="text-xs text-[var(--text-secondary)] w-8">5km</span>
            <span className="text-sm font-bold text-emerald-600 min-w-[48px] text-center">{pharmacy.searchRadiusKm}km</span>
          </div>
        </div>

        <div className="border-t border-[var(--border-color)]" />

        {/* Favorites placeholder */}
        <div>
          <label className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)] mb-3">
            <Star size={16} />
            즐겨찾기 약국
          </label>
          {pharmacy.favoritePharmacies.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <div className="w-12 h-12 bg-slate-100 dark:bg-slate-800 rounded-2xl flex items-center justify-center mb-3">
                <Star size={24} className="text-slate-300 dark:text-slate-600" />
              </div>
              <p className="text-sm text-[var(--text-secondary)]">즐겨찾기 약국이 없습니다</p>
              <p className="text-xs text-[var(--text-secondary)] mt-1">약국 지도에서 별표를 눌러 추가하세요</p>
            </div>
          ) : (
            <div className="space-y-2">
              {pharmacy.favoritePharmacies.map(id => (
                <div key={id} className="flex items-center justify-between px-4 py-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-color)]">
                  <span className="text-sm text-[var(--text-primary)]">{id}</span>
                  <button
                    type="button"
                    onClick={() => { updatePharmacy({
                      favoritePharmacies: pharmacy.favoritePharmacies.filter(p => p !== id),
                    }); showToast('설정이 저장되었습니다'); }}
                    className="text-xs text-rose-500 hover:text-rose-700 transition-colors"
                  >
                    삭제
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
