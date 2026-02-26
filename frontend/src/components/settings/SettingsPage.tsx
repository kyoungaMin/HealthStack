import { Settings } from 'lucide-react';
import ProfileSection from './ProfileSection';
import AnalysisSection from './AnalysisSection';
import DisplaySection from './DisplaySection';
import NotificationSection from './NotificationSection';
import FamilySection from './FamilySection';
import DataManagementSection from './DataManagementSection';
import PrivacySection from './PrivacySection';
import PharmacySection from './PharmacySection';
import AppInfoSection from './AppInfoSection';
export default function SettingsPage() {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/40 rounded-2xl flex items-center justify-center">
          <Settings size={24} className="text-emerald-600" />
        </div>
        <div>
          <h2 className="text-3xl font-bold text-[var(--text-primary)] tracking-tight">설정</h2>
          <p className="text-sm text-[var(--text-secondary)]">앱의 개인 설정을 관리합니다</p>
        </div>
      </div>

      {/* Settings Sections */}
      <ProfileSection />
      <AnalysisSection />
      <DisplaySection />
      <NotificationSection />
      <FamilySection />
      <DataManagementSection />
      <PrivacySection />
      <PharmacySection />
      <AppInfoSection />

      {/* Footer */}
      <p className="text-center text-[10px] text-[var(--text-secondary)] opacity-60 pb-4">
        설정은 이 기기에 자동 저장됩니다
      </p>
    </div>
  );
}
