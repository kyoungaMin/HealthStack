import { useEffect, useRef } from 'react';
import { useSettings } from '../contexts/SettingsContext';
import { sendBrowserNotification, isTimeMatch, isDayMatch } from '../services/notificationService';
import { BACKEND_URL } from '../services/supabase';

const MEDICATION_CHECK_MS = 60_000;
const LAST_MED_KEY = 'notification_last_med';
const LAST_NEWS_KEY = 'notification_last_news_titles';

interface SchedulerOptions {
  onNotification?: (item: { type: 'medication' | 'news'; title: string; body: string }) => void;
}

export function useNotificationScheduler(options?: SchedulerOptions) {
  const { settings, showToast } = useSettings();
  const { notification } = settings;
  const onNotificationRef = useRef(options?.onNotification);
  onNotificationRef.current = options?.onNotification;

  const lastMedRef = useRef<string>(
    localStorage.getItem(LAST_MED_KEY) ?? '',
  );
  const lastNewsRef = useRef<string[]>(
    JSON.parse(localStorage.getItem(LAST_NEWS_KEY) ?? '[]'),
  );

  // ── Medication Reminder ───────────────────────────────────────
  useEffect(() => {
    if (!notification.medicationReminder) return;
    if (notification.medicationSchedules.length === 0) return;

    const check = () => {
      const now = new Date();
      const nowKey = `${now.getFullYear()}-${now.getMonth()}-${now.getDate()}-${now.getHours()}-${now.getMinutes()}`;

      notification.medicationSchedules.forEach((schedule) => {
        if (!schedule.enabled) return;
        if (!isDayMatch(now, schedule.daysOfWeek)) return;

        schedule.times.forEach((time) => {
          if (!isTimeMatch(now, time)) return;

          const dedupKey = `${schedule.id}-${time}-${nowKey}`;
          if (lastMedRef.current === dedupKey) return;
          lastMedRef.current = dedupKey;
          localStorage.setItem(LAST_MED_KEY, dedupKey);

          const body = `${schedule.drugName} 복용 시간입니다 (${time})`;
          sendBrowserNotification('복약 알림', body);
          showToast(`💊 ${body}`);
          onNotificationRef.current?.({ type: 'medication', title: '복약 알림', body });
        });
      });
    };

    check();
    const id = setInterval(check, MEDICATION_CHECK_MS);
    return () => clearInterval(id);
  }, [notification.medicationReminder, notification.medicationSchedules, showToast]);

  // ── Health News Polling ───────────────────────────────────────
  useEffect(() => {
    if (!notification.healthNewsPush) return;

    const intervalMs = (notification.newsCheckIntervalMin || 60) * 60 * 1000;

    const check = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/v1/analyze/health-news?query=건강&display=5`);
        if (!res.ok) return;
        const data = await res.json();
        const items: { title: string }[] = data.items ?? [];
        const newTitles = items.map((i) => i.title);
        const prevTitles = lastNewsRef.current;

        const fresh = newTitles.filter((t) => !prevTitles.includes(t));

        if (fresh.length > 0 && prevTitles.length > 0) {
          const body =
            fresh.length === 1
              ? fresh[0]
              : `새로운 건강 뉴스 ${fresh.length}건이 있습니다`;
          sendBrowserNotification('건강 뉴스', body);
          showToast(`📰 ${body}`);
          onNotificationRef.current?.({ type: 'news', title: '건강 뉴스', body });
        }

        lastNewsRef.current = newTitles;
        localStorage.setItem(LAST_NEWS_KEY, JSON.stringify(newTitles));
      } catch (e) {
        console.warn('News check failed:', e);
      }
    };

    check();
    const id = setInterval(check, intervalMs);
    return () => clearInterval(id);
  }, [notification.healthNewsPush, notification.newsCheckIntervalMin, showToast]);
}
