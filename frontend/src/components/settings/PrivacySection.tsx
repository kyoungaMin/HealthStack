import { useState } from 'react';
import { Shield, ImageOff, Clock, Unlink, UserX, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSettings } from '../../contexts/SettingsContext';
import { supabase } from '../../services/supabase';
import { deleteAllData } from '../../services/settingsApi';

const RETENTION_OPTIONS = [
  { value: 30, label: '30일' },
  { value: 90, label: '90일' },
  { value: 180, label: '180일' },
  { value: 365, label: '1년' },
];

export default function PrivacySection() {
  const { settings, updatePrivacy, resetSettings, showToast } = useSettings();
  const { privacy } = settings;
  const [showWithdraw, setShowWithdraw] = useState(false);
  const [withdrawInput, setWithdrawInput] = useState('');

  const handleUnlinkGoogle = async () => {
    const ok = window.confirm('Google 계정 연동을 해제하시겠습니까?\n로그아웃됩니다.');
    if (!ok) return;
    await supabase.auth.signOut();
  };

  const handleWithdraw = async () => {
    if (withdrawInput !== '탈퇴') return;
    await deleteAllData();
    resetSettings();
    localStorage.clear();
    await supabase.auth.signOut();
    window.location.reload();
  };

  return (
    <div className="bg-[var(--bg-surface)] rounded-[32px] p-8 shadow-sm border border-[var(--border-color)] transition-colors duration-300">
      {/* Section Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/40 rounded-xl flex items-center justify-center">
          <Shield size={20} className="text-indigo-600" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)]">개인정보 및 보안</h3>
          <p className="text-xs text-[var(--text-secondary)]">데이터 보호 및 계정 관리</p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Auto-delete images */}
        <div className="flex items-center justify-between px-4 py-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-color)] opacity-50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-rose-100 dark:bg-rose-900/40 rounded-lg flex items-center justify-center">
              <ImageOff size={16} className="text-rose-600" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="text-sm font-semibold text-[var(--text-primary)]">처방전 이미지 자동 삭제</p>
                <span className="text-[10px] font-bold text-slate-400 bg-slate-100 dark:bg-slate-700 dark:text-slate-400 px-2 py-0.5 rounded-full">준비 중</span>
              </div>
              <p className="text-xs text-[var(--text-secondary)]">분석 완료 후 서버에서 이미지를 즉시 삭제</p>
            </div>
          </div>
          <div
            className={`relative w-14 h-8 rounded-full pointer-events-none ${
              privacy.autoDeleteImages ? 'bg-emerald-600' : 'bg-slate-300 dark:bg-slate-600'
            }`}
          >
            <div className={`absolute top-0.5 w-7 h-7 bg-white rounded-full shadow-md transition-transform ${
              privacy.autoDeleteImages ? 'translate-x-6' : 'translate-x-0.5'
            }`} />
          </div>
        </div>

        {/* History retention */}
        <div className="px-4 py-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-color)]">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/40 rounded-lg flex items-center justify-center">
              <Clock size={16} className="text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-[var(--text-primary)]">분석 기록 보관 기간</p>
              <p className="text-xs text-[var(--text-secondary)]">설정된 기간이 지난 기록은 자동 삭제됩니다</p>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-2">
            {RETENTION_OPTIONS.map(({ value, label }) => (
              <button
                key={value}
                type="button"
                onClick={() => { updatePrivacy({ historyRetentionDays: value }); showToast('설정이 저장되었습니다'); }}
                className={`px-3 py-2 text-sm font-medium rounded-xl border transition-all ${
                  privacy.historyRetentionDays === value
                    ? 'bg-emerald-600 text-white border-emerald-600 shadow-md shadow-emerald-200 dark:shadow-emerald-900/30'
                    : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] border-[var(--border-color)] hover:border-emerald-300'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="border-t border-[var(--border-color)]" />

        {/* Google unlink */}
        <button
          type="button"
          onClick={handleUnlinkGoogle}
          className="w-full flex items-center gap-3 px-5 py-4 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-2xl hover:border-indigo-300 transition-all group"
        >
          <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/40 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
            <Unlink size={18} className="text-indigo-600" />
          </div>
          <div className="text-left">
            <p className="text-sm font-semibold text-[var(--text-primary)]">Google 계정 연동 해제</p>
            <p className="text-xs text-[var(--text-secondary)]">로그아웃 후 계정 연결이 해제됩니다</p>
          </div>
        </button>

        {/* Withdraw */}
        <AnimatePresence>
          {!showWithdraw ? (
            <motion.button
              key="withdraw-btn"
              initial={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              type="button"
              onClick={() => setShowWithdraw(true)}
              className="w-full flex items-center gap-3 px-5 py-4 bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 rounded-2xl hover:bg-rose-100 dark:hover:bg-rose-900/30 transition-all group"
            >
              <div className="w-10 h-10 bg-rose-100 dark:bg-rose-900/40 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                <UserX size={18} className="text-rose-600" />
              </div>
              <div className="text-left">
                <p className="text-sm font-semibold text-rose-700 dark:text-rose-400">회원 탈퇴</p>
                <p className="text-xs text-rose-500 dark:text-rose-400/70">모든 데이터가 영구적으로 삭제됩니다</p>
              </div>
            </motion.button>
          ) : (
            <motion.div
              key="withdraw-confirm"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-5 bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 rounded-2xl"
            >
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle size={18} className="text-rose-600" />
                <p className="text-sm font-bold text-rose-700 dark:text-rose-400">정말 탈퇴하시겠습니까?</p>
              </div>
              <p className="text-xs text-rose-600 dark:text-rose-400/80 mb-4">
                이 작업은 되돌릴 수 없습니다. 확인하려면 아래에 <strong>"탈퇴"</strong>를 입력하세요.
              </p>
              <input
                type="text"
                value={withdrawInput}
                onChange={e => setWithdrawInput(e.target.value)}
                placeholder="탈퇴"
                className="w-full px-4 py-2.5 text-sm border border-rose-300 dark:border-rose-700 rounded-xl outline-none focus:border-rose-500 focus:ring-2 focus:ring-rose-100 bg-white dark:bg-slate-800 text-[var(--text-primary)] mb-3"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => { setShowWithdraw(false); setWithdrawInput(''); }}
                  className="flex-1 px-4 py-2.5 text-sm font-medium bg-[var(--bg-surface)] border border-[var(--border-color)] rounded-xl hover:bg-[var(--bg-primary)] transition-colors text-[var(--text-primary)]"
                >
                  취소
                </button>
                <button
                  type="button"
                  onClick={handleWithdraw}
                  disabled={withdrawInput !== '탈퇴'}
                  className="flex-1 px-4 py-2.5 text-sm font-bold bg-rose-600 text-white rounded-xl hover:bg-rose-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  탈퇴 확인
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
