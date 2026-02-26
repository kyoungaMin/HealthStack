import { useState } from 'react';
import { Bell, Clock, X, Check } from 'lucide-react';
import { useSettings } from '../../contexts/SettingsContext';
import type { MedicationSchedule } from '../../types/settings';

interface Props {
  drugList: string[];
  onClose: () => void;
}

const DAY_LABELS = ['일', '월', '화', '수', '목', '금', '토'];

export default function MedicationReminderSetup({ drugList, onClose }: Props) {
  const { settings, updateNotification, showToast } = useSettings();
  const existingNames = settings.notification.medicationSchedules.map(s => s.drugName);

  // Initialize: each drug gets default times, skip already-registered drugs
  const [items, setItems] = useState(() =>
    drugList.map(name => ({
      drugName: name,
      times: ['08:00', '12:00', '18:00'],
      daysOfWeek: [] as number[],
      enabled: !existingNames.includes(name),
      alreadyExists: existingNames.includes(name),
    }))
  );

  const toggleDrug = (idx: number) => {
    setItems(prev => prev.map((item, i) =>
      i === idx ? { ...item, enabled: !item.enabled } : item
    ));
  };

  const updateTime = (idx: number, tIdx: number, value: string) => {
    setItems(prev => prev.map((item, i) =>
      i === idx ? { ...item, times: item.times.map((t, j) => j === tIdx ? value : t) } : item
    ));
  };

  const addTime = (idx: number) => {
    setItems(prev => prev.map((item, i) =>
      i === idx ? { ...item, times: [...item.times, '12:00'] } : item
    ));
  };

  const removeTime = (idx: number, tIdx: number) => {
    setItems(prev => prev.map((item, i) =>
      i === idx ? { ...item, times: item.times.filter((_, j) => j !== tIdx) } : item
    ));
  };

  const toggleDay = (idx: number, day: number) => {
    setItems(prev => prev.map((item, i) =>
      i === idx
        ? { ...item, daysOfWeek: item.daysOfWeek.includes(day) ? item.daysOfWeek.filter(d => d !== day) : [...item.daysOfWeek, day] }
        : item
    ));
  };

  const handleSave = () => {
    const newSchedules: MedicationSchedule[] = items
      .filter(item => item.enabled && !item.alreadyExists)
      .map(item => ({
        id: Date.now().toString() + Math.random().toString(36).slice(2, 6),
        drugName: item.drugName,
        times: item.times.filter(Boolean),
        daysOfWeek: item.daysOfWeek,
        enabled: true,
      }));

    if (newSchedules.length === 0) {
      showToast('추가할 약물이 없습니다');
      onClose();
      return;
    }

    updateNotification({
      medicationReminder: true,
      medicationSchedules: [...settings.notification.medicationSchedules, ...newSchedules],
    });
    showToast(`💊 ${newSchedules.length}개 약물 복약 알림이 설정되었습니다`);
    onClose();
  };

  const enabledCount = items.filter(i => i.enabled && !i.alreadyExists).length;

  return (
    <div className="border-t border-slate-200 bg-gradient-to-b from-emerald-50/80 to-white">
      <div className="p-6 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center">
              <Bell size={16} className="text-emerald-600" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-800">복약 알림 설정</h4>
              <p className="text-[10px] text-slate-500">약물별 복용 시간을 설정하고 알림을 받으세요</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-600 transition-colors">
            <X size={16} />
          </button>
        </div>

        {/* Drug list */}
        <div className="space-y-3 max-h-[300px] overflow-y-auto">
          {items.map((item, idx) => (
            <div
              key={idx}
              className={`rounded-xl border transition-all ${
                item.alreadyExists
                  ? 'border-slate-200 bg-slate-50 opacity-60'
                  : item.enabled
                    ? 'border-emerald-200 bg-white shadow-sm'
                    : 'border-slate-200 bg-white'
              }`}
            >
              {/* Drug header */}
              <div className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    disabled={item.alreadyExists}
                    onClick={() => toggleDrug(idx)}
                    className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-colors ${
                      item.alreadyExists
                        ? 'border-slate-300 bg-slate-200'
                        : item.enabled
                          ? 'border-emerald-500 bg-emerald-500'
                          : 'border-slate-300 hover:border-emerald-400'
                    }`}
                  >
                    {(item.enabled || item.alreadyExists) && <Check size={12} className="text-white" />}
                  </button>
                  <span className={`text-sm font-semibold ${item.enabled ? 'text-slate-800' : 'text-slate-500'}`}>
                    {item.drugName}
                  </span>
                  {item.alreadyExists && (
                    <span className="text-[10px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full font-semibold">등록됨</span>
                  )}
                </div>
              </div>

              {/* Time settings (only if enabled and not already registered) */}
              {item.enabled && !item.alreadyExists && (
                <div className="px-4 pb-3 space-y-2">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <Clock size={12} className="text-slate-400" />
                    {item.times.map((t, tIdx) => (
                      <div key={tIdx} className="flex items-center gap-0.5">
                        <input
                          type="time"
                          value={t}
                          onChange={(e) => updateTime(idx, tIdx, e.target.value)}
                          className="px-2 py-1 text-xs rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                        />
                        {item.times.length > 1 && (
                          <button onClick={() => removeTime(idx, tIdx)} className="text-slate-300 hover:text-red-400 transition-colors">
                            <X size={10} />
                          </button>
                        )}
                      </div>
                    ))}
                    <button
                      onClick={() => addTime(idx)}
                      className="text-[10px] text-emerald-600 hover:text-emerald-700 px-1.5 py-1 border border-dashed border-emerald-300 rounded-md"
                    >
                      +
                    </button>
                  </div>

                  {/* Day selector */}
                  <div className="flex gap-1">
                    {DAY_LABELS.map((label, d) => (
                      <button
                        key={d}
                        type="button"
                        onClick={() => toggleDay(idx, d)}
                        className={`w-6 h-6 rounded-full text-[10px] font-bold transition-colors ${
                          item.daysOfWeek.includes(d)
                            ? 'bg-emerald-500 text-white'
                            : 'bg-slate-100 text-slate-400 hover:bg-slate-200'
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                    <span className="text-[10px] text-slate-400 ml-1 self-center">
                      {item.daysOfWeek.length === 0 ? '매일' : ''}
                    </span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Save button */}
        <div className="flex gap-2 pt-1">
          <button
            onClick={handleSave}
            disabled={enabledCount === 0}
            className="flex-1 px-4 py-2.5 bg-emerald-600 text-white text-sm font-bold rounded-xl hover:bg-emerald-700 disabled:bg-slate-300 transition-colors flex items-center justify-center gap-2"
          >
            <Bell size={14} />
            {enabledCount > 0 ? `${enabledCount}개 약물 알림 설정` : '알림 설정'}
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2.5 bg-slate-100 text-slate-600 text-sm font-semibold rounded-xl hover:bg-slate-200 transition-colors"
          >
            취소
          </button>
        </div>
      </div>
    </div>
  );
}
