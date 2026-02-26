// ─── Browser Web Notification ────────────────────────────────────

export function sendBrowserNotification(
  title: string,
  body: string,
  icon?: string,
): void {
  if (typeof Notification === 'undefined') return;
  if (Notification.permission !== 'granted') return;
  try {
    new Notification(title, {
      body,
      icon: icon ?? '/favicon.svg',
      tag: `healthstack-${Date.now()}`,
    });
  } catch (e) {
    console.warn('Browser notification failed:', e);
  }
}

// ─── Time / Day matching utilities ──────────────────────────────

export function isTimeMatch(now: Date, targetTime: string): boolean {
  const [h, m] = targetTime.split(':').map(Number);
  return now.getHours() === h && now.getMinutes() === m;
}

export function isDayMatch(now: Date, daysOfWeek: number[]): boolean {
  if (daysOfWeek.length === 0) return true; // empty = every day
  return daysOfWeek.includes(now.getDay());
}
