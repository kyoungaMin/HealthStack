import { useState } from 'react';
import { Database, FileText, Trash2, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSettings } from '../../contexts/SettingsContext';

export default function DataManagementSection() {
  const { resetSettings } = useSettings();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteInput, setDeleteInput] = useState('');

  const getStorageSize = () => {
    try {
      let total = 0;
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key) {
          total += localStorage.getItem(key)?.length ?? 0;
        }
      }
      const kb = (total * 2) / 1024;
      return kb > 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb.toFixed(0)} KB`;
    } catch {
      return '알 수 없음';
    }
  };

  const getStackCount = () => {
    try {
      const stored = localStorage.getItem('health_stacks_v5');
      return stored ? JSON.parse(stored).length : 0;
    } catch {
      return 0;
    }
  };

  const handleExportPDF = () => {
    try {
      const stacksRaw = localStorage.getItem('health_stacks_v5');
      const settingsRaw = localStorage.getItem('health_settings_v1');
      const stacks = stacksRaw ? JSON.parse(stacksRaw) : [];
      const settings = settingsRaw ? JSON.parse(settingsRaw) : {};

      if (stacks.length === 0) {
        alert('내보낼 분석 기록이 없습니다.');
        return;
      }

      const profile = settings?.profile || {};
      const profileInfo = [
        profile.displayName && `이름: ${profile.displayName}`,
        profile.birthYear && `출생연도: ${profile.birthYear}`,
        profile.gender && `성별: ${{ male: '남성', female: '여성', other: '기타' }[profile.gender as string] || profile.gender}`,
        profile.heightCm && `키: ${profile.heightCm}cm`,
        profile.weightKg && `체중: ${profile.weightKg}kg`,
      ].filter(Boolean);

      const allergyInfo = [
        profile.drugAllergies?.length > 0 && `약물 알레르기: ${profile.drugAllergies.join(', ')}`,
        profile.foodAllergies?.length > 0 && `식품 알레르기: ${profile.foodAllergies.join(', ')}`,
        profile.healthConditions?.length > 0 && `기저 질환: ${profile.healthConditions.join(', ')}`,
      ].filter(Boolean);

      const stacksHtml = stacks.map((stack: any) => {
        const sections: string[] = [];

        // --- Prescription type ---
        if (stack.type === 'prescription' && stack.prescriptionData) {
          const d = stack.prescriptionData;

          // 처방 약물
          if (d.prescriptionSummary?.drugList?.length) {
            sections.push(`
              <div class="section">
                <h3>처방 약물 목록</h3>
                <div class="tags">${d.prescriptionSummary.drugList.map((drug: string) => `<span class="tag tag-green">${drug}</span>`).join('')}</div>
              </div>
            `);
          }

          // 주의사항
          if (d.prescriptionSummary?.warnings) {
            const warningItems = Array.isArray(d.prescriptionSummary.warnings)
              ? d.prescriptionSummary.warnings
              : [d.prescriptionSummary.warnings];
            sections.push(`
              <div class="section warn-box">
                <h3>주의사항 안내</h3>
                <ul style="margin:0;padding-left:18px;">${warningItems.map((w: string) => `<li style="margin-bottom:4px;">${w}</li>`).join('')}</ul>
              </div>
            `);
          }

          // 약물 상세
          if (d.drugDetails?.length) {
            const drugRows = d.drugDetails.map((drug: any) => `
              <tr>
                <td class="drug-name">${drug.name}</td>
                <td>${drug.efficacy || '-'}</td>
                <td>${drug.sideEffects || '-'}</td>
              </tr>
            `).join('');
            sections.push(`
              <div class="section">
                <h3>약물 상세 정보</h3>
                <table><thead><tr><th>약물명</th><th>효능</th><th>부작용</th></tr></thead><tbody>${drugRows}</tbody></table>
              </div>
            `);
          }

          // 학술적 근거
          if (d.academicEvidence?.summary) {
            const papers = d.academicEvidence.papers?.length
              ? `<ul class="papers">${d.academicEvidence.papers.map((p: any) => `<li><a href="${p.url}">${p.title}</a></li>`).join('')}</ul>`
              : '';
            sections.push(`
              <div class="section">
                <h3>학술적 근거 (PubMed)</h3>
                <p class="trust-badge">신뢰 등급: ${d.academicEvidence.trustLevel}</p>
                <p class="quote">${d.academicEvidence.summary}</p>
                ${papers}
              </div>
            `);
          }

          // 동의보감
          if (d.donguibogam?.foods?.length || d.donguibogam?.donguiSection) {
            const foodCards = (d.donguibogam.foods || []).map((f: any) =>
              `<div class="food-card"><strong>${f.name}</strong><p>${f.reason}</p>${f.precaution ? `<p class="precaution">${f.precaution}</p>` : ''}</div>`
            ).join('');
            sections.push(`
              <div class="section dongui-box">
                <h3>동의보감</h3>
                ${d.donguibogam.donguiSection ? `<p class="quote dongui-quote">${d.donguibogam.donguiSection}</p>` : ''}
                ${foodCards ? `<p class="sub-label">추천 약선 음식</p>${foodCards}` : ''}
              </div>
            `);
          }

          // 생활 가이드
          if (d.lifestyleGuide?.advice) {
            const tokens = d.lifestyleGuide.symptomTokens?.length
              ? `<div class="tags">${d.lifestyleGuide.symptomTokens.map((t: string) => `<span class="tag tag-teal">#${t}</span>`).join('')}</div>`
              : '';
            sections.push(`
              <div class="section lifestyle-box">
                <h3>생활 가이드</h3>
                <p>${d.lifestyleGuide.advice}</p>
                ${tokens}
              </div>
            `);
          }
        }

        // --- Symptom type ---
        if (stack.type === 'symptom' && stack.report) {
          const r = stack.report;
          if (r.summary) {
            sections.push(`<div class="section"><h3>분석 요약</h3><p>${r.summary}</p></div>`);
          }
          if (r.medication_guide) {
            const guideRows = Object.entries(r.medication_guide).map(([k, v]) => `<tr><td class="drug-name">${k}</td><td>${v}</td></tr>`).join('');
            sections.push(`<div class="section"><h3>복약 가이드</h3><table><thead><tr><th>약물</th><th>안내</th></tr></thead><tbody>${guideRows}</tbody></table></div>`);
          }
          if (r.food_therapy) {
            const rec = (r.food_therapy.recommended || []).map((f: any) => `<div class="food-card good"><strong>${f.name}</strong><p>${f.reason}</p></div>`).join('');
            const avoid = (r.food_therapy.avoid || []).map((f: any) => `<div class="food-card bad"><strong>${f.name}</strong><p>${f.reason}</p></div>`).join('');
            sections.push(`
              <div class="section">
                <h3>식이 요법</h3>
                ${rec ? `<p class="sub-label">추천 음식</p>${rec}` : ''}
                ${avoid ? `<p class="sub-label warn-label">피해야 할 음식</p>${avoid}` : ''}
              </div>
            `);
          }
          if (r.lifestyle_advice) {
            sections.push(`<div class="section lifestyle-box"><h3>생활 가이드</h3><p>${r.lifestyle_advice}</p></div>`);
          }
        }

        return `
          <div class="report-card">
            <div class="report-header">
              <h2>${stack.title || '분석 리포트'}</h2>
              <div class="report-meta">
                <span class="type-badge ${stack.type}">${stack.type === 'prescription' ? '처방 분석' : '증상 분석'}</span>
                <span class="date">${stack.date}</span>
              </div>
            </div>
            ${sections.join('')}
          </div>
        `;
      }).join('<div class="page-break"></div>');

      const html = `<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>HealthStack 건강 리포트</title>
<style>
  @page { margin: 20mm 15mm; size: A4; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; color: #1e293b; line-height: 1.6; padding: 0; }
  .cover { text-align: center; padding: 80px 40px 60px; border-bottom: 3px solid #059669; margin-bottom: 32px; }
  .cover h1 { font-size: 28px; color: #059669; margin-bottom: 8px; }
  .cover .subtitle { color: #64748b; font-size: 14px; }
  .cover .export-date { color: #94a3b8; font-size: 12px; margin-top: 24px; }
  .profile-box { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 16px 20px; margin: 0 0 32px; }
  .profile-box h3 { font-size: 13px; color: #059669; margin-bottom: 8px; }
  .profile-box p { font-size: 12px; color: #334155; margin: 2px 0; }
  .page-break { page-break-after: always; height: 0; }
  .report-card { border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; margin-bottom: 24px; break-inside: avoid-page; }
  .report-header { margin-bottom: 20px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; }
  .report-header h2 { font-size: 18px; color: #0f172a; margin-bottom: 6px; }
  .report-meta { display: flex; align-items: center; gap: 10px; }
  .type-badge { font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 20px; }
  .type-badge.prescription { background: #dbeafe; color: #1d4ed8; }
  .type-badge.symptom { background: #fef3c7; color: #b45309; }
  .date { font-size: 12px; color: #94a3b8; }
  .section { margin-bottom: 18px; }
  .section h3 { font-size: 13px; font-weight: 700; color: #334155; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid #f1f5f9; }
  .tags { display: flex; flex-wrap: wrap; gap: 6px; }
  .tag { font-size: 11px; font-weight: 600; padding: 4px 12px; border-radius: 8px; }
  .tag-green { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }
  .tag-teal { background: #f0fdfa; color: #0d9488; border: 1px solid #99f6e4; }
  .warn-box { background: #fff1f2; border: 1px solid #fecdd3; border-radius: 12px; padding: 14px 16px; }
  .warn-box h3 { color: #be123c; border-bottom-color: #fecdd3; }
  .warn-box p { color: #9f1239; font-size: 13px; }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th { background: #f8fafc; text-align: left; padding: 8px 10px; border-bottom: 2px solid #e2e8f0; font-size: 11px; color: #64748b; }
  td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }
  .drug-name { font-weight: 700; color: #0f172a; white-space: nowrap; }
  .quote { font-style: italic; color: #475569; background: #f8fafc; padding: 10px 14px; border-radius: 8px; border-left: 3px solid #94a3b8; font-size: 13px; margin: 8px 0; }
  .trust-badge { display: inline-block; font-size: 11px; font-weight: 700; background: #ccfbf1; color: #0d9488; padding: 2px 10px; border-radius: 20px; margin-bottom: 8px; }
  .papers { margin-top: 8px; padding-left: 16px; }
  .papers li { font-size: 11px; color: #0d9488; margin: 2px 0; }
  .papers a { color: #0d9488; text-decoration: underline; }
  .dongui-box { background: #fffbeb; border: 1px solid #fde68a; border-radius: 12px; padding: 14px 16px; }
  .dongui-box h3 { color: #b45309; border-bottom-color: #fde68a; }
  .dongui-quote { border-left-color: #f59e0b; background: #fefce8; }
  .sub-label { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin: 12px 0 6px; }
  .warn-label { color: #dc2626; }
  .food-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 14px; margin-bottom: 6px; }
  .food-card strong { font-size: 13px; color: #0f172a; }
  .food-card p { font-size: 11px; color: #64748b; margin-top: 2px; }
  .food-card.good { border-left: 3px solid #059669; }
  .food-card.bad { border-left: 3px solid #dc2626; }
  .precaution { color: #dc2626 !important; font-size: 10px !important; }
  .lifestyle-box { background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 12px; padding: 14px 16px; }
  .lifestyle-box h3 { color: #059669; border-bottom-color: #a7f3d0; }
  .lifestyle-box p { color: #065f46; font-size: 13px; }
  .footer { text-align: center; color: #94a3b8; font-size: 10px; margin-top: 40px; padding-top: 16px; border-top: 1px solid #e2e8f0; }
</style>
</head>
<body>
  <div class="cover">
    <h1>HealthStack</h1>
    <p class="subtitle">건강 분석 리포트</p>
    <p class="export-date">내보내기 일시: ${new Date().toLocaleString('ko-KR')}</p>
  </div>

  ${(profileInfo.length > 0 || allergyInfo.length > 0) ? `
    <div class="profile-box">
      <h3>프로필 정보</h3>
      ${profileInfo.map(info => `<p>${info}</p>`).join('')}
      ${allergyInfo.map(info => `<p style="color:#dc2626">${info}</p>`).join('')}
    </div>
  ` : ''}

  <p style="font-size:13px;color:#64748b;margin-bottom:20px;">총 ${stacks.length}건의 분석 기록</p>

  ${stacksHtml}

  <div class="footer">
    <p>본 결과는 의학적 진단을 대신할 수 없습니다. 정확한 진단은 전문의와 상담하세요.</p>
    <p>HealthStack v1.0.0 · ${new Date().toLocaleDateString('ko-KR')}</p>
  </div>
</body>
</html>`;

      const printWindow = window.open('', '_blank');
      if (!printWindow) {
        alert('팝업이 차단되었습니다. 팝업 차단을 해제해 주세요.');
        return;
      }
      printWindow.document.write(html);
      printWindow.document.close();
      printWindow.onload = () => {
        printWindow.print();
      };
    } catch (err) {
      console.error('PDF export failed:', err);
      alert('PDF 내보내기 중 오류가 발생했습니다.');
    }
  };

  const handleClearCache = () => {
    const keysToKeep = ['health_stacks_v5', 'health_settings_v1'];
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && !keysToKeep.includes(key)) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key));
    alert('임시 데이터가 정리되었습니다.');
  };

  const handleDeleteAll = () => {
    if (deleteInput !== '삭제') return;
    localStorage.removeItem('health_stacks_v5');
    resetSettings();
    setShowDeleteConfirm(false);
    setDeleteInput('');
    window.location.reload();
  };

  return (
    <div className="bg-[var(--bg-surface)] rounded-[32px] p-8 shadow-sm border border-[var(--border-color)] transition-colors duration-300">
      {/* Section Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/40 rounded-xl flex items-center justify-center">
          <Database size={20} className="text-blue-600" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)]">데이터 관리</h3>
          <p className="text-xs text-[var(--text-secondary)]">저장된 데이터를 관리합니다</p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Storage Info */}
        <div className="flex items-center justify-between p-4 bg-[var(--bg-primary)] rounded-2xl border border-[var(--border-color)]">
          <div>
            <p className="text-sm font-semibold text-[var(--text-primary)]">저장 공간 사용량</p>
            <p className="text-xs text-[var(--text-secondary)]">분석 기록 {getStackCount()}건</p>
          </div>
          <span className="text-lg font-bold text-emerald-600">{getStorageSize()}</span>
        </div>

        {/* Export PDF */}
        <button
          type="button"
          onClick={handleExportPDF}
          className="w-full flex items-center gap-3 px-5 py-4 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-2xl hover:border-blue-300 transition-all group"
        >
          <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/40 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
            <FileText size={18} className="text-blue-600" />
          </div>
          <div className="text-left">
            <p className="text-sm font-semibold text-[var(--text-primary)]">PDF 내보내기</p>
            <p className="text-xs text-[var(--text-secondary)]">현재 화면을 PDF로 인쇄/저장합니다</p>
          </div>
        </button>

        {/* Clear Cache */}
        <button
          type="button"
          onClick={handleClearCache}
          className="w-full flex items-center gap-3 px-5 py-4 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-2xl hover:border-amber-300 transition-all group"
        >
          <div className="w-10 h-10 bg-amber-100 dark:bg-amber-900/40 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
            <Trash2 size={18} className="text-amber-600" />
          </div>
          <div className="text-left">
            <p className="text-sm font-semibold text-[var(--text-primary)]">임시 데이터 정리</p>
            <p className="text-xs text-[var(--text-secondary)]">분석 기록과 설정은 유지하고 임시 데이터만 정리합니다</p>
          </div>
        </button>

        {/* Delete All */}
        <div className="border-t border-[var(--border-color)] pt-4">
          <AnimatePresence>
            {!showDeleteConfirm ? (
              <motion.button
                key="delete-btn"
                initial={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                type="button"
                onClick={() => setShowDeleteConfirm(true)}
                className="w-full flex items-center gap-3 px-5 py-4 bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 rounded-2xl hover:bg-rose-100 dark:hover:bg-rose-900/30 transition-all group"
              >
                <div className="w-10 h-10 bg-rose-100 dark:bg-rose-900/40 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                  <AlertTriangle size={18} className="text-rose-600" />
                </div>
                <div className="text-left">
                  <p className="text-sm font-semibold text-rose-700 dark:text-rose-400">전체 데이터 삭제</p>
                  <p className="text-xs text-rose-500 dark:text-rose-400/70">모든 분석 기록, 설정이 영구적으로 삭제됩니다</p>
                </div>
              </motion.button>
            ) : (
              <motion.div
                key="delete-confirm"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-5 bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 rounded-2xl"
              >
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle size={18} className="text-rose-600" />
                  <p className="text-sm font-bold text-rose-700 dark:text-rose-400">정말 삭제하시겠습니까?</p>
                </div>
                <p className="text-xs text-rose-600 dark:text-rose-400/80 mb-4">
                  이 작업은 되돌릴 수 없습니다. 확인하려면 아래에 <strong>"삭제"</strong>를 입력하세요.
                </p>
                <input
                  type="text"
                  value={deleteInput}
                  onChange={e => setDeleteInput(e.target.value)}
                  placeholder='삭제'
                  className="w-full px-4 py-2.5 text-sm border border-rose-300 dark:border-rose-700 rounded-xl outline-none focus:border-rose-500 focus:ring-2 focus:ring-rose-100 bg-white dark:bg-slate-800 text-[var(--text-primary)] mb-3"
                />
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => { setShowDeleteConfirm(false); setDeleteInput(''); }}
                    className="flex-1 px-4 py-2.5 text-sm font-medium bg-[var(--bg-surface)] border border-[var(--border-color)] rounded-xl hover:bg-[var(--bg-primary)] transition-colors text-[var(--text-primary)]"
                  >
                    취소
                  </button>
                  <button
                    type="button"
                    onClick={handleDeleteAll}
                    disabled={deleteInput !== '삭제'}
                    className="flex-1 px-4 py-2.5 text-sm font-bold bg-rose-600 text-white rounded-xl hover:bg-rose-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    삭제 확인
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
