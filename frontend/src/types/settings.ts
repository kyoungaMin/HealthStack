// ─── Profile Settings ─────────────────────────────────────────────
export interface ProfileSettings {
  displayName: string;
  avatarUrl: string;
  birthYear: number | null;
  gender: 'male' | 'female' | 'other' | null;
  heightCm: number | null;
  weightKg: number | null;
  drugAllergies: string[];
  foodAllergies: string[];
  healthConditions: string[];
}

// ─── Display Settings ─────────────────────────────────────────────
export type ThemeMode = 'light' | 'dark' | 'system';
export type FontSize = 'small' | 'medium' | 'large';
export type Language = 'ko' | 'en';

export interface DisplaySettings {
  themeMode: ThemeMode;
  fontSize: FontSize;
  ttsSpeed: number;
  language: Language;
}

// ─── Analysis Settings ────────────────────────────────────────────
export interface AnalysisSettings {
  defaultSections: number[];       // 1~5 중 기본 활성 섹션
  showEvidenceLevel: boolean;      // Level A~D 표시 여부
  includeDonguibogam: boolean;     // 동의보감 섹션 기본 포함
}

// ─── Medication Schedule ─────────────────────────────────────────
export interface MedicationSchedule {
  id: string;
  drugName: string;
  times: string[];            // e.g. ["08:00", "12:00", "18:00"]
  daysOfWeek: number[];       // 0=Sun..6=Sat, empty = every day
  enabled: boolean;
}

// ─── Notification Settings ────────────────────────────────────────
export interface NotificationSettings {
  medicationReminder: boolean;
  healthNewsPush: boolean;
  analysisComplete: boolean;
  medicationSchedules: MedicationSchedule[];
  newsCheckIntervalMin: number;  // 30 | 60 | 120 | 240
}

// ─── Privacy Settings ─────────────────────────────────────────────
export interface PrivacySettings {
  autoDeleteImages: boolean;       // 처방전 이미지 자동 삭제
  historyRetentionDays: number;    // 30 | 90 | 180 | 365
}

// ─── Pharmacy Settings ───────────────────────────────────────────
export interface PharmacySettings {
  searchRadiusKm: number;          // 1~5
  favoritePharmacies: string[];
}

// ─── Combined Settings ────────────────────────────────────────────
export interface UserSettings {
  profile: ProfileSettings;
  display: DisplaySettings;
  analysis: AnalysisSettings;
  notification: NotificationSettings;
  privacy: PrivacySettings;
  pharmacy: PharmacySettings;
}

// ─── Defaults ─────────────────────────────────────────────────────
export const DEFAULT_SETTINGS: UserSettings = {
  profile: {
    displayName: '',
    avatarUrl: '',
    birthYear: null,
    gender: null,
    heightCm: null,
    weightKg: null,
    drugAllergies: [],
    foodAllergies: [],
    healthConditions: [],
  },
  display: {
    themeMode: 'light',
    fontSize: 'medium',
    ttsSpeed: 0.9,
    language: 'ko',
  },
  analysis: {
    defaultSections: [1, 2, 3, 4, 5],
    showEvidenceLevel: true,
    includeDonguibogam: true,
  },
  notification: {
    medicationReminder: true,
    healthNewsPush: false,
    analysisComplete: true,
    medicationSchedules: [],
    newsCheckIntervalMin: 60,
  },
  privacy: {
    autoDeleteImages: false,
    historyRetentionDays: 90,
  },
  pharmacy: {
    searchRadiusKm: 2,
    favoritePharmacies: [],
  },
};
