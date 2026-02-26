import { useState, useEffect } from 'react';
import { Users, ArrowLeft, Pill, AlertTriangle, Clock, ChevronRight } from 'lucide-react';
import { getFamilyInfo, getFamilyMemberPrescriptions } from '../../services/familyApi';
import type { FamilyInfo, FamilyMember, FamilyPrescription } from '../../types/family';

interface Props {
  onViewPrescription?: (data: Record<string, unknown>, drugList: string[], sections: number[]) => void;
}

export default function FamilyPrescriptionsView({ onViewPrescription }: Props) {
  const [familyInfo, setFamilyInfo] = useState<FamilyInfo | null>(null);
  const [selectedMember, setSelectedMember] = useState<FamilyMember | null>(null);
  const [prescriptions, setPrescriptions] = useState<FamilyPrescription[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingRx, setLoadingRx] = useState(false);

  useEffect(() => {
    loadFamily();
  }, []);

  const loadFamily = async () => {
    setLoading(true);
    const info = await getFamilyInfo();
    setFamilyInfo(info);
    setLoading(false);
  };

  const loadMemberPrescriptions = async (member: FamilyMember) => {
    setSelectedMember(member);
    setLoadingRx(true);
    const data = await getFamilyMemberPrescriptions(member.user_id);
    setPrescriptions(data);
    setLoadingRx(false);
  };

  const goBack = () => {
    setSelectedMember(null);
    setPrescriptions([]);
  };

  const getTotalDrugCount = (rx: FamilyPrescription) => rx.drug_list?.length ?? 0;

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('ko-KR', {
      year: 'numeric', month: 'long', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-8 h-8 border-2 border-rose-300 border-t-rose-600 rounded-full animate-spin" />
      </div>
    );
  }

  if (!familyInfo?.group) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-16 h-16 bg-rose-50 dark:bg-rose-900/20 rounded-2xl flex items-center justify-center mb-4">
          <Users size={32} className="text-rose-300" />
        </div>
        <p className="text-sm font-semibold text-[var(--text-primary)] mb-1">가족 그룹 없음</p>
        <p className="text-xs text-[var(--text-secondary)]">설정에서 가족 그룹에 참여하세요</p>
      </div>
    );
  }

  // 멤버 선택 전: PC 그리드 레이아웃으로 멤버 목록
  if (!selectedMember) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-rose-50 rounded-xl">
            <Users size={20} className="text-rose-600" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-800">{familyInfo.group.name}</h3>
            <p className="text-xs text-slate-500">멤버 {familyInfo.members.length}명</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {familyInfo.members.map((member) => (
            <button
              key={member.id}
              onClick={() => loadMemberPrescriptions(member)}
              className="flex items-center gap-4 p-5 bg-white rounded-2xl border border-slate-200 hover:border-rose-300 hover:shadow-md transition-all text-left group"
            >
              <div className="w-12 h-12 bg-rose-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-base font-bold text-rose-600">
                  {(member.nickname || member.display_name || '?')[0]}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-slate-800 truncate">
                  {member.nickname || member.display_name || '이름 없음'}
                </p>
                {member.nickname && member.display_name && (
                  <p className="text-[11px] text-slate-400 truncate">{member.display_name}</p>
                )}
                <p className="text-[10px] text-slate-400 mt-1">처방전 보기</p>
              </div>
              <ChevronRight size={16} className="text-slate-300 group-hover:text-rose-400 transition-colors flex-shrink-0" />
            </button>
          ))}
        </div>
      </div>
    );
  }

  // 멤버 선택 후: 해당 멤버의 처방전 목록 (PC 그리드)
  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center gap-3">
        <button onClick={goBack} className="p-2 hover:bg-slate-100 rounded-xl transition-colors">
          <ArrowLeft size={20} className="text-slate-600" />
        </button>
        <div className="w-10 h-10 bg-rose-100 rounded-full flex items-center justify-center">
          <span className="text-sm font-bold text-rose-600">
            {(selectedMember.nickname || selectedMember.display_name || '?')[0]}
          </span>
        </div>
        <div>
          <p className="text-lg font-bold text-slate-800">
            {selectedMember.nickname || selectedMember.display_name || '이름 없음'}
          </p>
          <p className="text-xs text-slate-500">처방전 {prescriptions.length}건</p>
        </div>
      </div>

      {loadingRx ? (
        <div className="flex items-center justify-center py-16">
          <div className="w-8 h-8 border-2 border-rose-300 border-t-rose-600 rounded-full animate-spin" />
        </div>
      ) : prescriptions.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Pill size={32} className="text-slate-300 mb-3" />
          <p className="text-sm font-medium text-slate-500">분석된 처방전이 없습니다</p>
        </div>
      ) : (
        <>
          {/* 다약제 경고 */}
          {(() => {
            const allDrugs = new Set<string>();
            prescriptions.forEach((rx) => rx.drug_list?.forEach((d) => allDrugs.add(d)));
            if (allDrugs.size >= 5) {
              return (
                <div className="flex items-start gap-3 px-5 py-4 bg-amber-50 border border-amber-200 rounded-2xl">
                  <AlertTriangle size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-bold text-amber-700">
                      다약제 주의 (총 {allDrugs.size}종)
                    </p>
                    <p className="text-xs text-amber-600 mt-0.5">
                      5종 이상의 약을 복용 중입니다. 병원 방문 시 약물 상호작용을 확인하세요.
                    </p>
                  </div>
                </div>
              );
            }
            return null;
          })()}

          {/* 처방전 그리드 */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {prescriptions.map((rx) => (
              <div
                key={rx.id}
                onClick={() => onViewPrescription?.(rx.analysis_data, rx.drug_list, rx.revealed_sections)}
                className="p-5 bg-white rounded-2xl border border-slate-200 hover:border-emerald-300 hover:shadow-md transition-all cursor-pointer group"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-emerald-50 rounded-xl group-hover:bg-emerald-600 group-hover:text-white transition-colors">
                      <Pill size={16} className="text-emerald-600 group-hover:text-white" />
                    </div>
                    <span className="text-sm font-bold text-slate-800">
                      약 {getTotalDrugCount(rx)}종
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-[11px] text-slate-400">
                    <Clock size={12} />
                    {formatDate(rx.created_at)}
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {rx.drug_list?.slice(0, 5).map((drug, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 text-[11px] font-medium bg-emerald-50 text-emerald-700 rounded-full"
                    >
                      {drug}
                    </span>
                  ))}
                  {(rx.drug_list?.length ?? 0) > 5 && (
                    <span className="px-2.5 py-1 text-[11px] text-slate-400">
                      +{rx.drug_list.length - 5}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
