import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import type { ReactNode } from 'react';
import type {
  UserSettings,
  ProfileSettings,
  DisplaySettings,
  AnalysisSettings,
  NotificationSettings,
  PrivacySettings,
  PharmacySettings,
} from '../types/settings';
import { DEFAULT_SETTINGS } from '../types/settings';
import { supabase } from '../services/supabase';
import { fetchSettings, saveSettings } from '../services/settingsApi';
import { subscribeToPush } from '../services/pushService';
import { syncMedicationSchedules } from '../services/medicationSyncApi';
import type { User as SupabaseUser } from '@supabase/supabase-js';

const STORAGE_KEY = 'health_settings_v1';
const FONT_SIZE_MAP = { small: '16px', medium: '18px', large: '22px' } as const;

interface SettingsContextValue {
  settings: UserSettings;
  updateProfile: (partial: Partial<ProfileSettings>) => void;
  updateDisplay: (partial: Partial<DisplaySettings>) => void;
  updateAnalysis: (partial: Partial<AnalysisSettings>) => void;
  updateNotification: (partial: Partial<NotificationSettings>) => void;
  updatePrivacy: (partial: Partial<PrivacySettings>) => void;
  updatePharmacy: (partial: Partial<PharmacySettings>) => void;
  resetSettings: () => void;
  toastMessage: string;
  showToast: (msg: string) => void;
  hideToast: () => void;
}

const SettingsContext = createContext<SettingsContextValue>({
  settings: DEFAULT_SETTINGS,
  updateProfile: () => {},
  updateDisplay: () => {},
  updateAnalysis: () => {},
  updateNotification: () => {},
  updatePrivacy: () => {},
  updatePharmacy: () => {},
  resetSettings: () => {},
  toastMessage: '',
  showToast: () => {},
  hideToast: () => {},
});

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<UserSettings>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        return {
          profile: { ...DEFAULT_SETTINGS.profile, ...parsed.profile },
          display: { ...DEFAULT_SETTINGS.display, ...parsed.display },
          analysis: { ...DEFAULT_SETTINGS.analysis, ...parsed.analysis },
          notification: { ...DEFAULT_SETTINGS.notification, ...parsed.notification },
          privacy: { ...DEFAULT_SETTINGS.privacy, ...parsed.privacy },
          pharmacy: { ...DEFAULT_SETTINGS.pharmacy, ...parsed.pharmacy },
        };
      }
      return DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  });

  const [toastMessage, setToastMessage] = useState('');
  const showToast = useCallback((msg: string) => setToastMessage(msg), []);
  const hideToast = useCallback(() => setToastMessage(''), []);

  const [user, setUser] = useState<SupabaseUser | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Auth listener — rely solely on onAuthStateChange (handles token refresh properly)
  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, session) => {
      setUser(session?.user ?? null);
    });
    return () => subscription.unsubscribe();
  }, []);

  // Sync to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }, [settings]);

  // Apply dark mode
  useEffect(() => {
    const root = document.documentElement;
    const { themeMode } = settings.display;

    const applyTheme = (dark: boolean) => {
      root.classList.toggle('dark', dark);
    };

    if (themeMode === 'dark') {
      applyTheme(true);
    } else if (themeMode === 'system') {
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      applyTheme(mq.matches);
      const handler = (e: MediaQueryListEvent) => applyTheme(e.matches);
      mq.addEventListener('change', handler);
      return () => mq.removeEventListener('change', handler);
    } else {
      applyTheme(false);
    }
  }, [settings.display.themeMode]);

  // Apply font size
  useEffect(() => {
    document.documentElement.style.setProperty(
      '--app-font-size',
      FONT_SIZE_MAP[settings.display.fontSize]
    );
  }, [settings.display.fontSize]);

  // Fetch from Supabase on login + subscribe to push
  const hasFetchedRef = useRef(false);
  const backendReadyRef = useRef(false);
  useEffect(() => {
    if (!user || hasFetchedRef.current) return;
    hasFetchedRef.current = true;
    // Validate session with Supabase server before calling backend
    (async () => {
      const { data: { user: validUser } } = await supabase.auth.getUser();
      if (!validUser) {
        await supabase.auth.signOut();
        return;
      }
      const remote = await fetchSettings();
      if (remote === 'auth_failed') {
        // Backend settings API rejected the token — skip sync but don't logout.
        // The user is already validated by supabase.auth.getUser() above.
        backendReadyRef.current = false;
        console.warn('Settings API auth failed — skipping settings sync');
        return;
      }
      if (!remote) {
        backendReadyRef.current = false;
        return;
      }
      backendReadyRef.current = true;
      setSettings(prev => ({
        ...prev,
        profile: {
          ...prev.profile,
          ...Object.fromEntries(
            Object.entries(remote.profile).filter(([, v]) => v != null && !(Array.isArray(v) && v.length === 0))
          ),
        },
        display: {
          ...prev.display,
          ...Object.fromEntries(
            Object.entries(remote.display).filter(([, v]) => v != null)
          ),
        },
      } as UserSettings));
      subscribeToPush().catch(() => {});
    })();
  }, [user]);

  // Debounced Supabase sync (profile + display only)
  const isInitialRef = useRef(true);
  useEffect(() => {
    if (isInitialRef.current) {
      isInitialRef.current = false;
      return;
    }
    if (!user || !backendReadyRef.current) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      saveSettings({ profile: settings.profile, display: settings.display });
    }, 1000);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [settings.profile, settings.display, user]);

  // Sync medication schedules to backend (2s debounce, logged-in users only)
  const medSyncRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const medSyncInitRef = useRef(true);
  useEffect(() => {
    if (medSyncInitRef.current) {
      medSyncInitRef.current = false;
      return;
    }
    if (!user || !backendReadyRef.current) return;
    if (medSyncRef.current) clearTimeout(medSyncRef.current);
    medSyncRef.current = setTimeout(() => {
      syncMedicationSchedules(settings.notification.medicationSchedules);
    }, 2000);
    return () => {
      if (medSyncRef.current) clearTimeout(medSyncRef.current);
    };
  }, [settings.notification.medicationSchedules, user]);

  const updateProfile = useCallback((partial: Partial<ProfileSettings>) => {
    setSettings(prev => ({ ...prev, profile: { ...prev.profile, ...partial } }));
  }, []);

  const updateDisplay = useCallback((partial: Partial<DisplaySettings>) => {
    setSettings(prev => ({ ...prev, display: { ...prev.display, ...partial } }));
  }, []);

  const updateAnalysis = useCallback((partial: Partial<AnalysisSettings>) => {
    setSettings(prev => ({ ...prev, analysis: { ...prev.analysis, ...partial } }));
  }, []);

  const updateNotification = useCallback((partial: Partial<NotificationSettings>) => {
    setSettings(prev => ({ ...prev, notification: { ...prev.notification, ...partial } }));
  }, []);

  const updatePrivacy = useCallback((partial: Partial<PrivacySettings>) => {
    setSettings(prev => ({ ...prev, privacy: { ...prev.privacy, ...partial } }));
  }, []);

  const updatePharmacy = useCallback((partial: Partial<PharmacySettings>) => {
    setSettings(prev => ({ ...prev, pharmacy: { ...prev.pharmacy, ...partial } }));
  }, []);

  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  // History retention: clean up expired analysis records on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem('health_stacks_v5');
      if (!raw) return;
      const stacks = JSON.parse(raw);
      if (!Array.isArray(stacks) || stacks.length === 0) return;
      const retentionMs = settings.privacy.historyRetentionDays * 24 * 60 * 60 * 1000;
      const cutoff = Date.now() - retentionMs;
      const filtered = stacks.filter((s: any) => {
        const ts = s.timestamp || new Date(s.date).getTime();
        return ts > cutoff;
      });
      if (filtered.length < stacks.length) {
        localStorage.setItem('health_stacks_v5', JSON.stringify(filtered));
      }
    } catch { /* ignore */ }
  }, [settings.privacy.historyRetentionDays]);

  return (
    <SettingsContext.Provider value={{
      settings,
      updateProfile,
      updateDisplay,
      updateAnalysis,
      updateNotification,
      updatePrivacy,
      updatePharmacy,
      resetSettings,
      toastMessage,
      showToast,
      hideToast,
    }}>
      {children}
    </SettingsContext.Provider>
  );
}

export const useSettings = () => useContext(SettingsContext);
