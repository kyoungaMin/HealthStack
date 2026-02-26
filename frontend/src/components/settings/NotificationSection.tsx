import { useState, useEffect } from 'react';
import { Bell, Pill, Newspaper, CheckCircle, Smartphone, ShieldAlert, ExternalLink } from 'lucide-react';
import { useSettings } from '../../contexts/SettingsContext';
import { subscribeToPush, unsubscribeFromPush, isPushSubscribed } from '../../services/pushService';
import MedicationSchedulePanel from './MedicationSchedulePanel';

export default function NotificationSection() {
  const { settings, updateNotification, showToast } = useSettings();
  const { notification } = settings;
  const [permissionStatus, setPermissionStatus] = useState<NotificationPermission>(
    typeof Notification !== 'undefined' ? Notification.permission : 'default'
  );

  const [pushActive, setPushActive] = useState(false);

  useEffect(() => {
    isPushSubscribed().then(setPushActive);
  }, []);

  const requestPermission = async () => {
    if (typeof Notification === 'undefined') return;
    const result = await Notification.requestPermission();
    setPermissionStatus(result);
    // 허용 시 자동으로 push 구독 시도
    if (result === 'granted') {
      const sub = await subscribeToPush();
      setPushActive(sub !== null);
    }
  };

  const togglePush = async () => {
    if (pushActive) {
      await unsubscribeFromPush();
      setPushActive(false);
      showToast('백그라운드 알림이 해제되었습니다');
    } else {
      const sub = await subscribeToPush();
      setPushActive(sub !== null);
      showToast(sub ? '백그라운드 알림이 활성화되었습니다' : '알림 등록에 실패했습니다. 로그인이 필요합니다.');
    }
  };

  const toggleItems: {
    key: 'medicationReminder' | 'healthNewsPush' | 'analysisComplete';
    label: string;
    desc: string;
    icon: typeof Bell;
    iconColor: string;
    iconBg: string;
  }[] = [
    {
      key: 'medicationReminder',
      label: '복약 리마인더',
      desc: '복용 시간에 맞춰 알림을 보냅니다',
      icon: Pill,
      iconColor: 'text-emerald-600',
      iconBg: 'bg-emerald-100 dark:bg-emerald-900/40',
    },
    {
      key: 'healthNewsPush',
      label: '건강 뉴스 · 트렌드',
      desc: '최신 건강 뉴스와 방송 트렌드 알림',
      icon: Newspaper,
      iconColor: 'text-blue-600',
      iconBg: 'bg-blue-100 dark:bg-blue-900/40',
    },
    {
      key: 'analysisComplete',
      label: '분석 완료 알림',
      desc: '처방 분석이 완료되면 알림을 보냅니다',
      icon: CheckCircle,
      iconColor: 'text-purple-600',
      iconBg: 'bg-purple-100 dark:bg-purple-900/40',
    },
  ];

  return (
    <div className="bg-[var(--bg-surface)] rounded-[32px] p-8 shadow-sm border border-[var(--border-color)] transition-colors duration-300">
      {/* Section Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 bg-amber-100 dark:bg-amber-900/40 rounded-xl flex items-center justify-center">
          <Bell size={20} className="text-amber-600" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)]">알림 설정</h3>
          <p className="text-xs text-[var(--text-secondary)]">알림 수신 여부를 관리합니다</p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Browser permission: default (not yet asked) */}
        {permissionStatus === 'default' && (
          <div className="flex items-center justify-between px-4 py-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl">
            <div>
              <p className="text-sm font-semibold text-amber-700 dark:text-amber-400">브라우저 알림 허용 필요</p>
              <p className="text-xs text-amber-600 dark:text-amber-400/70">알림을 받으려면 브라우저 권한을 허용하세요</p>
            </div>
            <button
              type="button"
              onClick={requestPermission}
              className="px-4 py-2 text-xs font-medium bg-amber-600 text-white rounded-xl hover:bg-amber-700 transition-colors"
            >
              허용
            </button>
          </div>
        )}

        {/* Browser permission: denied (blocked) */}
        {permissionStatus === 'denied' && (
          <div className="px-4 py-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-red-100 dark:bg-red-900/40 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                <ShieldAlert size={16} className="text-red-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-red-700 dark:text-red-400">알림이 차단되어 있습니다</p>
                <p className="text-xs text-red-600 dark:text-red-400/70 mt-1">
                  브라우저에서 알림 권한이 차단된 상태입니다. 아래 방법으로 직접 허용해 주세요.
                </p>
              </div>
            </div>
            <div className="ml-11 space-y-2">
              <div className="flex items-start gap-2">
                <span className="text-xs font-bold text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/40 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0">1</span>
                <p className="text-xs text-red-600 dark:text-red-400/80">주소창 왼쪽의 <strong>자물쇠(또는 튜닝) 아이콘</strong>을 클릭하세요</p>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-xs font-bold text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/40 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0">2</span>
                <p className="text-xs text-red-600 dark:text-red-400/80"><strong>알림</strong> 항목을 <strong>허용</strong>으로 변경하세요</p>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-xs font-bold text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/40 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0">3</span>
                <p className="text-xs text-red-600 dark:text-red-400/80">페이지를 <strong>새로고침</strong>하면 알림이 활성화됩니다</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="ml-11 flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-900/50 rounded-lg transition-colors"
            >
              <ExternalLink size={12} />
              설정 완료 후 새로고침
            </button>
          </div>
        )}

        {/* Background push toggle */}
        {permissionStatus === 'granted' && (
          <div className="flex items-center justify-between px-4 py-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-color)]">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-indigo-100 dark:bg-indigo-900/40 rounded-lg flex items-center justify-center">
                <Smartphone size={16} className="text-indigo-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-[var(--text-primary)]">백그라운드 푸시 알림</p>
                <p className="text-xs text-[var(--text-secondary)]">브라우저가 닫혀있어도 알림을 받습니다</p>
              </div>
            </div>
            <button
              type="button"
              onClick={togglePush}
              className={`relative w-14 h-8 rounded-full transition-colors ${
                pushActive ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-600'
              }`}
            >
              <div className={`absolute top-0.5 w-7 h-7 bg-white rounded-full shadow-md transition-transform ${
                pushActive ? 'translate-x-6' : 'translate-x-0.5'
              }`} />
            </button>
          </div>
        )}

        {/* Toggle Items */}
        {toggleItems.map(({ key, label, desc, icon: Icon, iconColor, iconBg }) => (
          <div key={key}>
            <div className="flex items-center justify-between px-4 py-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-color)]">
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 ${iconBg} rounded-lg flex items-center justify-center`}>
                  <Icon size={16} className={iconColor} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-[var(--text-primary)]">{label}</p>
                  <p className="text-xs text-[var(--text-secondary)]">{desc}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => { updateNotification({ [key]: !notification[key] }); showToast('설정이 저장되었습니다'); }}
                className={`relative w-14 h-8 rounded-full transition-colors ${
                  notification[key] ? 'bg-emerald-600' : 'bg-slate-300 dark:bg-slate-600'
                }`}
              >
                <div className={`absolute top-0.5 w-7 h-7 bg-white rounded-full shadow-md transition-transform ${
                  notification[key] ? 'translate-x-6' : 'translate-x-0.5'
                }`} />
              </button>
            </div>

            {/* Medication schedule sub-panel */}
            {key === 'medicationReminder' && notification.medicationReminder && (
              <MedicationSchedulePanel />
            )}

            {/* News check interval selector */}
            {key === 'healthNewsPush' && notification.healthNewsPush && (
              <div className="mt-2 ml-11 px-4 py-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-color)]">
                <label className="text-xs font-semibold text-[var(--text-secondary)] mb-2 block">확인 주기</label>
                <select
                  value={notification.newsCheckIntervalMin}
                  onChange={(e) => { updateNotification({ newsCheckIntervalMin: Number(e.target.value) }); showToast('설정이 저장되었습니다'); }}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-[var(--border-color)] bg-[var(--bg-surface)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value={30}>30분마다</option>
                  <option value={60}>1시간마다</option>
                  <option value={120}>2시간마다</option>
                  <option value={240}>4시간마다</option>
                </select>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
