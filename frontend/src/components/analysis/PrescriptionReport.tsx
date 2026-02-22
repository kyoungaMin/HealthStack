import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
    Pill, AlertTriangle, Brain, BookOpen, Heart,
    Loader2, CheckCircle, ChevronDown, ChevronUp,
} from 'lucide-react';
import type { PrescriptionData } from '../../services/analysisApi';
import { getDietRecommendation } from '../../services/analysisApi';

interface Props {
    data: PrescriptionData;
}

function Section({ title, icon: Icon, color, children }: {
    title: string;
    icon: any;
    color: string;
    children: React.ReactNode;
}) {
    return (
        <motion.section
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
        >
            <h4 className={`text-xs font-bold uppercase tracking-widest mb-3 flex items-center gap-2 ${color}`}>
                <Icon size={14} />
                {title}
            </h4>
            {children}
        </motion.section>
    );
}

export default function PrescriptionReport({ data }: Props) {
    const [dietLoading, setDietLoading] = useState(false);
    const [dietText, setDietText] = useState<string | null>(null);
    const [expandedDrug, setExpandedDrug] = useState<number | null>(null);

    const { prescriptionSummary, drugDetails, academicEvidence, lifestyleGuide, donguibogam } = data;

    const fetchDiet = async () => {
        setDietLoading(true);
        try {
            const foods = donguibogam?.foods?.map(f => f.name).join(', ') || '';
            const drugs = prescriptionSummary?.drugList?.join(', ') || '';
            const result = await getDietRecommendation(foods, drugs);
            setDietText(result);
        } catch (e) {
            console.error(e);
        } finally {
            setDietLoading(false);
        }
    };

    return (
        <div className="space-y-8 pb-4">
            {/* ── 처방 약물 목록 ── */}
            <Section title="처방 약물 목록" icon={Pill} color="text-slate-400">
                <div className="flex flex-wrap gap-2">
                    {prescriptionSummary.drugList.map((drug, i) => (
                        <span
                            key={i}
                            className="px-4 py-2 bg-emerald-50 text-emerald-700 rounded-xl text-sm font-bold border border-emerald-100 shadow-sm"
                        >
                            {drug}
                        </span>
                    ))}
                </div>
            </Section>

            {/* ── 주의사항 ── */}
            {prescriptionSummary.warnings && (
                <div className="p-6 bg-rose-50 rounded-2xl border border-rose-100 relative overflow-hidden">
                    <h4 className="text-rose-800 font-bold mb-2 flex items-center gap-2 text-sm">
                        <AlertTriangle size={16} className="text-rose-500" />
                        주의사항 및 상호작용
                    </h4>
                    <p className="text-rose-900/80 text-sm leading-relaxed">
                        {prescriptionSummary.warnings}
                    </p>
                    <div className="absolute -bottom-4 -right-4 text-7xl opacity-5 rotate-12">⚠️</div>
                </div>
            )}

            {/* ── 2-column layout: Drug Details + Donguibogam ── */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Drug Details */}
                {drugDetails && drugDetails.length > 0 && (
                    <Section title="약물 상세 정보" icon={Pill} color="text-slate-400">
                        <div className="space-y-2">
                            {drugDetails.map((drug, i) => (
                                <div
                                    key={i}
                                    className="bg-slate-50 rounded-2xl border border-slate-100 overflow-hidden"
                                >
                                    <button
                                        onClick={() => setExpandedDrug(expandedDrug === i ? null : i)}
                                        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-100 transition-colors"
                                    >
                                        <span className="font-bold text-slate-800 text-sm">{drug.name}</span>
                                        {expandedDrug === i
                                            ? <ChevronUp size={16} className="text-slate-400" />
                                            : <ChevronDown size={16} className="text-slate-400" />}
                                    </button>
                                    {expandedDrug === i && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            className="px-4 pb-4 space-y-2"
                                        >
                                            {drug.efficacy && (
                                                <p className="text-xs text-slate-600">
                                                    <span className="font-bold text-emerald-600">효능: </span>
                                                    {drug.efficacy}
                                                </p>
                                            )}
                                            {drug.sideEffects && (
                                                <p className="text-xs text-slate-500">
                                                    <span className="font-bold text-rose-500">부작용: </span>
                                                    {drug.sideEffects}
                                                </p>
                                            )}
                                        </motion.div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </Section>
                )}

                {/* Donguibogam */}
                {donguibogam && (
                    <Section title="동의보감의 지혜" icon={BookOpen} color="text-amber-600">
                        <div className="p-5 bg-amber-50 rounded-2xl border border-amber-100">
                            {donguibogam.donguiSection && (
                                <p className="text-amber-800 text-sm italic mb-4 bg-white/70 p-3 rounded-xl border border-amber-200/50 leading-relaxed">
                                    "{donguibogam.donguiSection}"
                                </p>
                            )}
                            <p className="text-[10px] font-bold text-amber-600 uppercase tracking-widest mb-2">
                                추천 약선 음식
                            </p>
                            <div className="space-y-2">
                                {donguibogam.foods.map((food, i) => (
                                    <div key={i} className="bg-white p-3 rounded-xl border border-amber-100 shadow-sm">
                                        <p className="font-bold text-amber-900 text-sm">{food.name}</p>
                                        <p className="text-[11px] text-amber-700/70 leading-relaxed mt-0.5">
                                            {food.reason}
                                        </p>
                                        {food.precaution && (
                                            <p className="text-[10px] text-rose-500 mt-1">⚠️ {food.precaution}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </Section>
                )}
            </div>

            {/* ── Academic Evidence ── */}
            {academicEvidence && (
                <Section title="학술적 근거 (PubMed)" icon={Brain} color="text-slate-400">
                    <div className="p-6 bg-slate-50 rounded-2xl border border-slate-200">
                        <div className="flex items-center gap-2 mb-3">
                            <span className="text-xs font-bold px-3 py-1 bg-teal-100 text-teal-700 rounded-full">
                                신뢰 등급: {academicEvidence.trustLevel}
                            </span>
                        </div>
                        <p className="text-slate-600 text-sm leading-relaxed italic">
                            "{academicEvidence.summary}"
                        </p>
                        {academicEvidence.papers && academicEvidence.papers.length > 0 && (
                            <div className="mt-3 space-y-1">
                                {academicEvidence.papers.map((paper, i) => (
                                    <a
                                        key={i}
                                        href={paper.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block text-xs text-teal-600 hover:underline truncate"
                                    >
                                        📄 {paper.title}
                                    </a>
                                ))}
                            </div>
                        )}
                    </div>
                </Section>
            )}

            {/* ── Lifestyle Guide ── */}
            {lifestyleGuide && (
                <Section title="생활 가이드" icon={Heart} color="text-emerald-600">
                    <div className="p-6 bg-emerald-50 rounded-2xl border border-emerald-100">
                        <p className="text-emerald-800/80 text-sm leading-relaxed">
                            {lifestyleGuide.advice}
                        </p>
                        {lifestyleGuide.symptomTokens && lifestyleGuide.symptomTokens.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-4">
                                {lifestyleGuide.symptomTokens.map((token, i) => (
                                    <span
                                        key={i}
                                        className="px-3 py-1 bg-white text-emerald-600 text-[10px] font-bold rounded-full border border-emerald-100"
                                    >
                                        #{token}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                </Section>
            )}

            {/* ── Diet Recommendation ── */}
            <div>
                {!dietText ? (
                    <button
                        onClick={fetchDiet}
                        disabled={dietLoading}
                        className="w-full p-5 rounded-2xl bg-gradient-to-br from-rose-400 to-pink-500 text-white font-bold flex items-center justify-center gap-3 hover:brightness-105 transition-all disabled:opacity-70 shadow-lg shadow-rose-100"
                    >
                        {dietLoading ? (
                            <>
                                <Loader2 className="animate-spin" size={20} />
                                레시피 생성 중...
                            </>
                        ) : (
                            <>
                                <span className="text-xl">🍯</span>
                                오늘의 힐링 레시피 받기
                            </>
                        )}
                    </button>
                ) : (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-6 rounded-2xl bg-rose-50 border border-rose-100"
                    >
                        <h5 className="text-xs font-bold text-rose-700 uppercase tracking-widest mb-3 flex items-center gap-2">
                            <CheckCircle size={14} />
                            맞춤 힐링 레시피
                        </h5>
                        <p className="text-slate-700 text-sm leading-relaxed whitespace-pre-wrap">
                            {dietText}
                        </p>
                    </motion.div>
                )}
            </div>

            <p className="text-center text-xs text-gray-300">
                본 결과는 의학적 진단을 대신할 수 없습니다.<br />
                정확한 진단은 전문의와 상담하세요.
            </p>
        </div>
    );
}
