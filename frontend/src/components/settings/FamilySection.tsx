import { useState, useEffect } from 'react';
import { Users, UserPlus, Copy, Check, LogOut, Edit3, Crown } from 'lucide-react';
import { useSettings } from '../../contexts/SettingsContext';
import {
  getFamilyInfo,
  createFamilyGroup,
  joinFamilyGroup,
  leaveFamily,
  updateMemberNickname,
} from '../../services/familyApi';
import type { FamilyInfo, FamilyMember } from '../../types/family';

export default function FamilySection() {
  const { showToast } = useSettings();
  const [familyInfo, setFamilyInfo] = useState<FamilyInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<'idle' | 'create' | 'join'>('idle');
  const [groupName, setGroupName] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [nickname, setNickname] = useState('');
  const [copied, setCopied] = useState(false);
  const [editingMember, setEditingMember] = useState<number | null>(null);
  const [editNickname, setEditNickname] = useState('');
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadFamilyInfo();
  }, []);

  const loadFamilyInfo = async () => {
    setLoading(true);
    const info = await getFamilyInfo();
    setFamilyInfo(info);
    setLoading(false);
  };

  const handleCreate = async () => {
    if (submitting) return;
    setSubmitting(true);
    try {
      await createFamilyGroup(groupName || '우리 가족');
      showToast('가족 그룹이 생성되었습니다');
      setMode('idle');
      setGroupName('');
      await loadFamilyInfo();
    } catch (e: any) {
      showToast(e.message || '그룹 생성 실패');
    } finally {
      setSubmitting(false);
    }
  };

  const handleJoin = async () => {
    if (submitting || inviteCode.length !== 6) return;
    setSubmitting(true);
    try {
      await joinFamilyGroup(inviteCode, nickname || undefined);
      showToast('가족 그룹에 참여했습니다');
      setMode('idle');
      setInviteCode('');
      setNickname('');
      await loadFamilyInfo();
    } catch (e: any) {
      showToast(e.message || '참가 실패');
    } finally {
      setSubmitting(false);
    }
  };

  const handleLeave = async () => {
    setSubmitting(true);
    try {
      await leaveFamily();
      showToast('가족 그룹에서 나왔습니다');
      setFamilyInfo(null);
      setShowLeaveConfirm(false);
    } catch (e: any) {
      showToast(e.message || '탈퇴 실패');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopyCode = async (code: string) => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    showToast('초대 코드가 복사되었습니다');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleUpdateNickname = async (memberId: number) => {
    if (!editNickname.trim()) return;
    try {
      await updateMemberNickname(memberId, editNickname.trim());
      setEditingMember(null);
      setEditNickname('');
      showToast('별명이 변경되었습니다');
      await loadFamilyInfo();
    } catch {
      showToast('별명 변경 실패');
    }
  };

  const hasGroup = familyInfo?.group != null;

  return (
    <div className="bg-[var(--bg-surface)] rounded-[32px] p-8 shadow-sm border border-[var(--border-color)] transition-colors duration-300">
      {/* Section Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 bg-rose-100 dark:bg-rose-900/40 rounded-xl flex items-center justify-center">
          <Users size={20} className="text-rose-600" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)]">가족 관리</h3>
          <p className="text-xs text-[var(--text-secondary)]">가족의 처방전을 함께 관리합니다</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <div className="w-6 h-6 border-2 border-rose-300 border-t-rose-600 rounded-full animate-spin" />
        </div>
      ) : !hasGroup ? (
        /* 미연결 상태 */
        <div className="space-y-4">
          {mode === 'idle' && (
            <>
              <div className="text-center py-6">
                <div className="w-16 h-16 bg-rose-50 dark:bg-rose-900/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Users size={32} className="text-rose-400" />
                </div>
                <p className="text-sm font-semibold text-[var(--text-primary)] mb-1">가족 그룹에 참여하세요</p>
                <p className="text-xs text-[var(--text-secondary)]">가족의 처방전과 복약 정보를 함께 확인할 수 있습니다</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setMode('create')}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-rose-600 text-white text-sm font-semibold rounded-xl hover:bg-rose-700 transition-colors"
                >
                  <Users size={16} />
                  그룹 만들기
                </button>
                <button
                  onClick={() => setMode('join')}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-[var(--bg-primary)] text-[var(--text-primary)] text-sm font-semibold rounded-xl border border-[var(--border-color)] hover:border-rose-300 transition-colors"
                >
                  <UserPlus size={16} />
                  코드로 참가
                </button>
              </div>
            </>
          )}

          {mode === 'create' && (
            <div className="space-y-3">
              <p className="text-sm font-semibold text-[var(--text-primary)]">새 가족 그룹 만들기</p>
              <input
                type="text"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                placeholder="그룹 이름 (예: 우리 가족)"
                maxLength={50}
                className="w-full px-4 py-3 text-sm rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-rose-500"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleCreate}
                  disabled={submitting}
                  className="flex-1 py-3 bg-rose-600 text-white text-sm font-semibold rounded-xl hover:bg-rose-700 disabled:opacity-50 transition-colors"
                >
                  {submitting ? '생성 중...' : '만들기'}
                </button>
                <button
                  onClick={() => { setMode('idle'); setGroupName(''); }}
                  className="px-4 py-3 text-sm text-[var(--text-secondary)] rounded-xl border border-[var(--border-color)] hover:bg-[var(--bg-primary)] transition-colors"
                >
                  취소
                </button>
              </div>
            </div>
          )}

          {mode === 'join' && (
            <div className="space-y-3">
              <p className="text-sm font-semibold text-[var(--text-primary)]">초대 코드로 참가</p>
              <input
                type="text"
                value={inviteCode}
                onChange={(e) => setInviteCode(e.target.value.toUpperCase().slice(0, 6))}
                placeholder="6자리 초대 코드"
                maxLength={6}
                className="w-full px-4 py-3 text-center text-lg font-mono font-bold tracking-[0.5em] rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-rose-500"
              />
              <input
                type="text"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="가족 내 별명 (선택, 예: 막내)"
                maxLength={20}
                className="w-full px-4 py-3 text-sm rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-rose-500"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleJoin}
                  disabled={submitting || inviteCode.length !== 6}
                  className="flex-1 py-3 bg-rose-600 text-white text-sm font-semibold rounded-xl hover:bg-rose-700 disabled:opacity-50 transition-colors"
                >
                  {submitting ? '참가 중...' : '참가하기'}
                </button>
                <button
                  onClick={() => { setMode('idle'); setInviteCode(''); setNickname(''); }}
                  className="px-4 py-3 text-sm text-[var(--text-secondary)] rounded-xl border border-[var(--border-color)] hover:bg-[var(--bg-primary)] transition-colors"
                >
                  취소
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* 연결됨 상태 */
        <div className="space-y-4">
          {/* 그룹 정보 */}
          <div className="px-4 py-3 bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 rounded-xl">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-bold text-rose-700 dark:text-rose-400">{familyInfo!.group!.name}</p>
                <p className="text-xs text-rose-600 dark:text-rose-400/70 mt-0.5">멤버 {familyInfo!.members.length}명</p>
              </div>
              <button
                onClick={() => handleCopyCode(familyInfo!.group!.invite_code)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300 rounded-lg hover:bg-rose-200 dark:hover:bg-rose-900/60 transition-colors"
              >
                {copied ? <Check size={12} /> : <Copy size={12} />}
                {familyInfo!.group!.invite_code}
              </button>
            </div>
          </div>

          {/* 멤버 목록 */}
          <div className="space-y-2">
            {familyInfo!.members.map((member: FamilyMember) => (
              <div key={member.id} className="flex items-center justify-between px-4 py-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-color)]">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-rose-100 dark:bg-rose-900/40 rounded-full flex items-center justify-center">
                    {member.role === 'owner' ? (
                      <Crown size={14} className="text-rose-600" />
                    ) : (
                      <span className="text-xs font-bold text-rose-600">
                        {(member.nickname || member.display_name || '?')[0]}
                      </span>
                    )}
                  </div>
                  <div>
                    {editingMember === member.id ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={editNickname}
                          onChange={(e) => setEditNickname(e.target.value)}
                          placeholder="별명 입력"
                          maxLength={20}
                          className="w-24 px-2 py-1 text-xs rounded border border-[var(--border-color)] bg-[var(--bg-surface)] text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-rose-500"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleUpdateNickname(member.id);
                            if (e.key === 'Escape') setEditingMember(null);
                          }}
                        />
                        <button
                          onClick={() => handleUpdateNickname(member.id)}
                          className="text-xs text-rose-600 font-semibold"
                        >
                          저장
                        </button>
                      </div>
                    ) : (
                      <>
                        <p className="text-sm font-semibold text-[var(--text-primary)]">
                          {member.nickname || member.display_name || '이름 없음'}
                          {member.role === 'owner' && (
                            <span className="ml-1.5 text-[10px] text-rose-500 font-medium">방장</span>
                          )}
                        </p>
                        {member.nickname && member.display_name && (
                          <p className="text-[10px] text-[var(--text-secondary)]">{member.display_name}</p>
                        )}
                      </>
                    )}
                  </div>
                </div>
                {editingMember !== member.id && (
                  <button
                    onClick={() => { setEditingMember(member.id); setEditNickname(member.nickname || ''); }}
                    className="p-1.5 text-[var(--text-secondary)] hover:text-rose-600 transition-colors"
                  >
                    <Edit3 size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* 그룹 나가기 */}
          {!showLeaveConfirm ? (
            <button
              onClick={() => setShowLeaveConfirm(true)}
              className="flex items-center justify-center gap-2 w-full py-3 text-sm text-red-500 font-medium rounded-xl border border-red-200 dark:border-red-800 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              <LogOut size={14} />
              가족 그룹 나가기
            </button>
          ) : (
            <div className="px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
              <p className="text-xs text-red-600 dark:text-red-400 mb-3">정말 가족 그룹에서 나가시겠습니까?</p>
              <div className="flex gap-2">
                <button
                  onClick={handleLeave}
                  disabled={submitting}
                  className="flex-1 py-2 bg-red-600 text-white text-xs font-semibold rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                >
                  {submitting ? '처리 중...' : '나가기'}
                </button>
                <button
                  onClick={() => setShowLeaveConfirm(false)}
                  className="px-4 py-2 text-xs text-[var(--text-secondary)] rounded-lg border border-[var(--border-color)] hover:bg-[var(--bg-primary)] transition-colors"
                >
                  취소
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
