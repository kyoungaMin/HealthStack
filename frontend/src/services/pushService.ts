import { supabase } from './supabase';

const API_BASE_URL =
  (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001') + '/api/v1';

async function getAuthHeader(): Promise<Record<string, string>> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) return {};
  // Skip if token is expired
  if (session.expires_at && session.expires_at * 1000 < Date.now()) return {};
  return { Authorization: `Bearer ${session.access_token}` };
}

/** Convert VAPID public key from URL-safe base64 to Uint8Array */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i++) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

/** Fetch VAPID public key from backend */
export async function fetchVapidPublicKey(): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/push/vapid-public-key`);
    if (!res.ok) return null;
    const data = await res.json();
    return data.publicKey || null;
  } catch {
    return null;
  }
}

/** Register service worker */
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) {
    console.warn('Service Worker not supported');
    return null;
  }
  try {
    const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
    return reg;
  } catch (err) {
    console.error('SW registration failed:', err);
    return null;
  }
}

async function sendSubscriptionToBackend(
  sub: PushSubscription,
  authHeaders: Record<string, string>,
): Promise<void> {
  const key = sub.getKey('p256dh');
  const auth = sub.getKey('auth');
  if (!key || !auth) return;

  const body = {
    endpoint: sub.endpoint,
    p256dh: btoa(String.fromCharCode(...new Uint8Array(key))),
    auth_key: btoa(String.fromCharCode(...new Uint8Array(auth))),
  };

  await fetch(`${API_BASE_URL}/push/subscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders },
    body: JSON.stringify(body),
  });
}

/** Subscribe to Web Push and send subscription to backend */
export async function subscribeToPush(): Promise<PushSubscription | null> {
  const authHeaders = await getAuthHeader();
  if (!authHeaders.Authorization) {
    console.warn('Push subscribe skipped: no auth');
    return null;
  }

  const reg = await registerServiceWorker();
  if (!reg) return null;

  // Check if already subscribed
  const existing = await reg.pushManager.getSubscription();
  if (existing) {
    await sendSubscriptionToBackend(existing, authHeaders);
    return existing;
  }

  const vapidKey = await fetchVapidPublicKey();
  if (!vapidKey) {
    console.error('Failed to fetch VAPID public key');
    return null;
  }

  // Request notification permission first
  const permission = await Notification.requestPermission();
  if (permission !== 'granted') {
    console.warn('Push subscription skipped: notification permission denied');
    return null;
  }

  try {
    const subscription = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidKey),
    });
    await sendSubscriptionToBackend(subscription, authHeaders);
    return subscription;
  } catch (err) {
    console.error('Push subscription failed:', err);
    return null;
  }
}

/** Unsubscribe from Web Push */
export async function unsubscribeFromPush(): Promise<void> {
  const reg = await navigator.serviceWorker?.ready;
  if (!reg) return;

  const sub = await reg.pushManager.getSubscription();
  if (!sub) return;

  const authHeaders = await getAuthHeader();
  if (authHeaders.Authorization) {
    await fetch(`${API_BASE_URL}/push/unsubscribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders },
      body: JSON.stringify({ endpoint: sub.endpoint }),
    });
  }

  await sub.unsubscribe();
}

/** Check if push is currently subscribed */
export async function isPushSubscribed(): Promise<boolean> {
  if (!('serviceWorker' in navigator)) return false;
  try {
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.getSubscription();
    return sub !== null;
  } catch {
    return false;
  }
}
