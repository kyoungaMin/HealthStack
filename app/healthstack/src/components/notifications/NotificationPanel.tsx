import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
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

const typeEmoji: Record<NotificationItem['type'], string> = {
  medication: '💊',
  news: '📰',
  analysis: '📋',
};

const typeBg: Record<NotificationItem['type'], string> = {
  medication: 'bg-blue-50',
  news: 'bg-amber-50',
  analysis: 'bg-emerald-50',
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

  // Close on outside click (stable ref-based)
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as Node;
      if (panelRef.current?.contains(target)) return;
      if (triggerRef?.current?.contains(target)) return;
      onCloseRef.current();
    };
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

  if (!open) return null;

  const panel = (
    <div
      ref={panelRef}
      style={{
        position: 'fixed',
        top: 72,
        left: 16,
        right: 16,
        maxHeight: 'calc(100vh - 160px)',
        zIndex: 9999,
        animation: 'notifSlideIn 0.2s ease-out',
      }}
      className="bg-white border border-slate-100 rounded-[24px] shadow-2xl flex flex-col overflow-hidden"
    >
      <style>{`
        @keyframes notifSlideIn {
          from { opacity: 0; transform: translateY(-8px) scale(0.96); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <span className="text-base">🔔</span>
          <span className="font-bold text-sm text-slate-800">알림</span>
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
              className="text-[11px] text-emerald-600 font-medium px-2 py-1 rounded-lg hover:bg-emerald-50 active:scale-95 transition-all"
            >
              ✓ 모두 읽음
            </button>
          )}
          {notifications.length > 0 && (
            <button
              onClick={onClearAll}
              className="text-[11px] text-slate-400 font-medium px-2 py-1 rounded-lg hover:bg-rose-50 active:scale-95 transition-all"
            >
              🗑 전체 삭제
            </button>
          )}
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <span className="text-3xl mb-2">🔔</span>
            <p className="text-sm font-medium text-slate-700">알림이 없습니다</p>
            <p className="text-[11px] text-slate-400 mt-1">복약 알림, 건강 뉴스, 분석 완료 시<br/>여기에 표시됩니다</p>
          </div>
        ) : (
          notifications.map((item) => (
            <div
              key={item.id}
              onClick={() => !item.read && onMarkAsRead(item.id)}
              className={`flex items-start gap-3 px-5 py-3 active:bg-slate-50 transition-colors border-b border-slate-50 last:border-b-0 ${
                !item.read ? 'bg-emerald-50/40' : ''
              }`}
            >
              <div className={`shrink-0 w-8 h-8 rounded-xl ${typeBg[item.type]} flex items-center justify-center mt-0.5`}>
                <span className="text-sm">{typeEmoji[item.type]}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  {!item.read && (
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                  )}
                  <span className="text-xs font-bold text-slate-800 truncate">{item.title}</span>
                  <span className="text-[10px] text-slate-400 shrink-0 ml-auto">{timeAgo(item.timestamp)}</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">{item.body}</p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); onRemove(item.id); }}
                className="shrink-0 p-1 text-slate-300 hover:text-rose-400 active:scale-90 transition-all mt-0.5"
              >
                <span className="text-xs">✕</span>
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );

  return createPortal(panel, document.body);
}
