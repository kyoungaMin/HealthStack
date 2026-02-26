import { useState } from 'react';
import { Plus, Trash2, Clock, X } from 'lucide-react';
import { useSettings } from '../../contexts/SettingsContext';
import type { MedicationSchedule } from '../../types/settings';

const DAY_LABELS = ['일', '월', '화', '수', '목', '금', '토'];

export default function MedicationSchedulePanel() {
  const { settings, updateNotification, showToast } = useSettings();
  const schedules = settings.notification.medicationSchedules;

  const [showAddForm, setShowAddForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);

  // Add form state
  const [newDrugName, setNewDrugName] = useState('');
  const [newTimes, setNewTimes] = useState<string[]>(['08:00']);
  const [newDays, setNewDays] = useState<number[]>([]);

  const resetForm = () => {
    setNewDrugName('');
    setNewTimes(['08:00']);
    setNewDays([]);
    setShowAddForm(false);
  };

  const addSchedule = () => {
    if (!newDrugName.trim()) return;
    const schedule: MedicationSchedule = {
      id: Date.now().toString() + Math.random().toString(36).slice(2, 6),
      drugName: newDrugName.trim(),
      times: newTimes.filter(Boolean),
      daysOfWeek: newDays,
      enabled: true,
    };
    updateNotification({
      medicationSchedules: [...schedules, schedule],
    });
    showToast('복약 일정이 추가되었습니다');
    resetForm();
  };

  const removeSchedule = (id: string) => {
    updateNotification({
      medicationSchedules: schedules.filter(s => s.id !== id),
    });
    showToast('복약 일정이 삭제되었습니다');
  };

  const toggleSchedule = (id: string) => {
    updateNotification({
      medicationSchedules: schedules.map(s =>
        s.id === id ? { ...s, enabled: !s.enabled } : s
      ),
    });
  };

  const updateScheduleField = (id: string, partial: Partial<MedicationSchedule>) => {
    updateNotification({
      medicationSchedules: schedules.map(s =>
        s.id === id ? { ...s, ...partial } : s
      ),
    });
  };

  const toggleDay = (days: number[], day: number) =>
    days.includes(day) ? days.filter(d => d !== day) : [...days, day];

  return (
    <div className="mt-2 ml-11 space-y-2">
      {/* Existing schedules */}
      {schedules.map((s) => (
        <div
          key={s.id}
          className={`px-4 py-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-color)] transition-opacity ${!s.enabled ? 'opacity-50' : ''}`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <button
                type="button"
                onClick={() => toggleSchedule(s.id)}
                className={`relative w-10 h-5 rounded-full transition-colors flex-shrink-0 ${
                  s.enabled ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'
                }`}
              >
                <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                  s.enabled ? 'translate-x-5' : 'translate-x-0.5'
                }`} />
              </button>
              <span className="text-sm font-semibold text-[var(--text-primary)] truncate">{s.drugName}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setEditId(editId === s.id ? null : s.id)}
                className="p-1.5 text-slate-400 hover:text-blue-500 transition-colors"
                title="편집"
              >
                <Clock size={14} />
              </button>
              <button
                type="button"
                onClick={() => removeSchedule(s.id)}
                className="p-1.5 text-slate-400 hover:text-red-500 transition-colors"
                title="삭제"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>

          {/* Time badges */}
          <div className="flex flex-wrap gap-1.5 mt-2">
            {s.times.map((t, i) => (
              <span key={i} className="text-xs bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full">
                {t}
              </span>
            ))}
            {s.daysOfWeek.length > 0 && (
              <span className="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded-full">
                {s.daysOfWeek.sort().map(d => DAY_LABELS[d]).join(', ')}
              </span>
            )}
            {s.daysOfWeek.length === 0 && (
              <span className="text-xs bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 px-2 py-0.5 rounded-full">매일</span>
            )}
          </div>

          {/* Inline edit */}
          {editId === s.id && (
            <div className="mt-3 pt-3 border-t border-[var(--border-color)] space-y-3">
              {/* Edit times */}
              <div>
                <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">복용 시간</label>
                <div className="flex flex-wrap gap-2">
                  {s.times.map((t, i) => (
                    <div key={i} className="flex items-center gap-1">
                      <input
                        type="time"
                        value={t}
                        onChange={(e) => {
                          const updated = [...s.times];
                          updated[i] = e.target.value;
                          updateScheduleField(s.id, { times: updated });
                        }}
                        className="px-2 py-1 text-xs rounded-lg border border-[var(--border-color)] bg-[var(--bg-surface)] text-[var(--text-primary)]"
                      />
                      {s.times.length > 1 && (
                        <button
                          type="button"
                          onClick={() => updateScheduleField(s.id, { times: s.times.filter((_, j) => j !== i) })}
                          className="text-slate-400 hover:text-red-500"
                        >
                          <X size={12} />
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => updateScheduleField(s.id, { times: [...s.times, '12:00'] })}
                    className="px-2 py-1 text-xs text-emerald-600 hover:text-emerald-700 border border-dashed border-emerald-300 rounded-lg"
                  >
                    + 추가
                  </button>
                </div>
              </div>

              {/* Edit days */}
              <div>
                <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">반복 요일 (미선택 시 매일)</label>
                <div className="flex gap-1.5">
                  {DAY_LABELS.map((label, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => updateScheduleField(s.id, { daysOfWeek: toggleDay(s.daysOfWeek, i) })}
                      className={`w-8 h-8 rounded-full text-xs font-semibold transition-colors ${
                        s.daysOfWeek.includes(i)
                          ? 'bg-emerald-500 text-white'
                          : 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      ))}

      {/* Add form */}
      {showAddForm ? (
        <div className="px-4 py-3 bg-[var(--bg-primary)] rounded-xl border-2 border-dashed border-emerald-300 dark:border-emerald-700 space-y-3">
          <div>
            <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">약물명</label>
            <input
              type="text"
              value={newDrugName}
              onChange={(e) => setNewDrugName(e.target.value)}
              placeholder="예: 아목시실린"
              className="w-full px-3 py-2 text-sm rounded-lg border border-[var(--border-color)] bg-[var(--bg-surface)] text-[var(--text-primary)] placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">복용 시간</label>
            <div className="flex flex-wrap gap-2">
              {newTimes.map((t, i) => (
                <div key={i} className="flex items-center gap-1">
                  <input
                    type="time"
                    value={t}
                    onChange={(e) => {
                      const updated = [...newTimes];
                      updated[i] = e.target.value;
                      setNewTimes(updated);
                    }}
                    className="px-2 py-1 text-xs rounded-lg border border-[var(--border-color)] bg-[var(--bg-surface)] text-[var(--text-primary)]"
                  />
                  {newTimes.length > 1 && (
                    <button type="button" onClick={() => setNewTimes(newTimes.filter((_, j) => j !== i))} className="text-slate-400 hover:text-red-500">
                      <X size={12} />
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                onClick={() => setNewTimes([...newTimes, '12:00'])}
                className="px-2 py-1 text-xs text-emerald-600 hover:text-emerald-700 border border-dashed border-emerald-300 rounded-lg"
              >
                + 추가
              </button>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-[var(--text-secondary)] mb-1.5 block">반복 요일 (미선택 시 매일)</label>
            <div className="flex gap-1.5">
              {DAY_LABELS.map((label, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setNewDays(toggleDay(newDays, i))}
                  className={`w-8 h-8 rounded-full text-xs font-semibold transition-colors ${
                    newDays.includes(i)
                      ? 'bg-emerald-500 text-white'
                      : 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={addSchedule}
              disabled={!newDrugName.trim()}
              className="flex-1 px-3 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 disabled:dark:bg-slate-600 rounded-lg transition-colors"
            >
              추가
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="px-3 py-2 text-xs font-semibold text-slate-500 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-lg transition-colors"
            >
              취소
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setShowAddForm(true)}
          className="w-full flex items-center justify-center gap-1.5 px-4 py-2.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 hover:bg-emerald-100 dark:hover:bg-emerald-900/30 rounded-xl border border-dashed border-emerald-300 dark:border-emerald-700 transition-colors"
        >
          <Plus size={14} />
          복약 일정 추가
        </button>
      )}

      {schedules.length === 0 && !showAddForm && (
        <p className="text-xs text-center text-[var(--text-secondary)] py-2">
          처방전 분석 시 약물이 자동으로 추가됩니다
        </p>
      )}
    </div>
  );
}
