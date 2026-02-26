import React, { useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, Check, Trash2, Pill, Newspaper, FileText } from 'lucide-react';
import type { NotificationItem } from '../../types/notification';

interface NotificationPanelProps {
  open: boolean;
  onClose: () => void;
  notifications: NotificationItem[];
  unreadCount: number;
  onMarkAsRead: (id: string) => void;
  onMarkAllAsRead: () => void;
  onRemove: (id: string) => void;
  onClearAll: () => void;
  /** ref of the trigger button — clicks on it won't count as "outside" */
  triggerRef?: React.RefObject<HTMLElement | null>;
}

const typeConfig: Record<NotificationItem['type'], { icon: typeof Pill; color: string; bg: string }> = {
  medication: { icon: Pill, color: 'text-blue-500', bg: 'bg-blue-50' },
  news: { icon: Newspaper, color: 'text-amber-500', bg: 'bg-amber-50' },
  analysis: { icon: FileText, color: 'text-emerald-500', bg: 'bg-emerald-50' },
};

function timeAgo(ts: number): string {
  const diff = Date.now() - ts;
  const min = Math.floor(diff / 60000);
  if (min < 1) return '방금 전';
  if (min < 60) return `${min}분 전`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}시간 전`;
  const day = Math.floor(hr / 24);
  return `${day}일 전`;
}

export default function NotificationPanel({
  open,
  onClose,
  notifications,
  unreadCount,
  onMarkAsRead,
  onMarkAllAsRead,
  onRemove,
  onClearAll,
  triggerRef,
}: NotificationPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  // Close on outside click (stable ref-based, no dep on onClose)
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as Node;
      if (panelRef.current?.contains(target)) return;
      if (triggerRef?.current?.contains(target)) return;
      onCloseRef.current();
    };
    // Delay so the opening click doesn't immediately close
    const timer = setTimeout(() => document.addEventListener('mousedown', handler), 10);
    return () => {
      clearTimeout(timer);
      document.removeEventListener('mousedown', handler);
    };
  }, [open, triggerRef]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCloseRef.current();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open]);

  const panel = (
    <AnimatePresence>
      {open && (
        <motion.div
          ref={panelRef}
          initial={{ opacity: 0, y: -8, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -8, scale: 0.96 }}
          transition={{ duration: 0.18, ease: 'easeOut' }}
          style={{ position: 'fixed', top: 72, right: 40, zIndex: 9999 }}
          className="w-96 max-h-[480px] bg-[var(--bg-surface)] border border-[var(--border-color)] rounded-2xl shadow-2xl flex flex-col overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-3.5 border-b border-[var(--border-color)]">
            <div className="flex items-center gap-2">
              <Bell size={16} className="text-emerald-500" />
              <span className="font-bold text-sm text-[var(--text-primary)]">알림</span>
              {unreadCount > 0 && (
                <span className="text-[10px] font-bold bg-rose-500 text-white px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </div>
            <div className="flex items-center gap-1">
              {unreadCount > 0 && (
                <button
                  onClick={onMarkAllAsRead}
                  className="text-[11px] text-emerald-600 hover:text-emerald-700 font-medium px-2 py-1 rounded-lg hover:bg-emerald-50 transition-colors"
                >
                  <Check size={12} className="inline mr-0.5" />
                  모두 읽음
                </button>
              )}
              {notifications.length > 0 && (
                <button
                  onClick={onClearAll}
                  className="text-[11px] text-slate-400 hover:text-rose-500 font-medium px-2 py-1 rounded-lg hover:bg-rose-50 transition-colors"
                >
                  <Trash2 size={12} className="inline mr-0.5" />
                  전체 삭제
                </button>
              )}
            </div>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-3">
                  <Bell size={20} className="text-slate-300" />
                </div>
                <p className="text-sm font-medium text-[var(--text-primary)]">알림이 없습니다</p>
                <p className="text-[11px] text-slate-400 mt-1">복약 알림, 건강 뉴스, 분석 완료 시<br/>여기에 표시됩니다</p>
              </div>
            ) : (
              notifications.map((item) => {
                const cfg = typeConfig[item.type];
                const Icon = cfg.icon;
                return (
                  <div
                    key={item.id}
                    onClick={() => !item.read && onMarkAsRead(item.id)}
                    className={`flex items-start gap-3 px-5 py-3 cursor-pointer hover:bg-[var(--bg-hover,rgba(0,0,0,0.02))] transition-colors border-b border-[var(--border-color)] last:border-b-0 ${
                      !item.read ? 'bg-emerald-50/30' : ''
                    }`}
                  >
                    <div className={`shrink-0 w-8 h-8 rounded-xl ${cfg.bg} flex items-center justify-center mt-0.5`}>
                      <Icon size={14} className={cfg.color} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        {!item.read && (
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                        )}
                        <span className="text-xs font-bold text-[var(--text-primary)] truncate">{item.title}</span>
                        <span className="text-[10px] text-slate-400 shrink-0 ml-auto">{timeAgo(item.timestamp)}</span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">{item.body}</p>
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); onRemove(item.id); }}
                      className="shrink-0 p-1 text-slate-300 hover:text-rose-400 transition-colors mt-0.5"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  // Use portal to escape overflow:hidden on <main>
  return createPortal(panel, document.body);
}
