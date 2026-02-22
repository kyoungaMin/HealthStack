import React from 'react';
import { motion } from 'framer-motion';
import { PieChart, List, AlertTriangle, Lightbulb, MessageCircle } from 'lucide-react';
import type { ReportData } from '../../services/analysisApi';

interface Props {
    report: ReportData;
}

export default function Step3Report({ report }: Props) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-6 pb-20"
        >
            <div className="flex items-center gap-2 mb-2">
                <h2 className="font-bold text-gray-800 text-lg">오늘의 내 몸 리포트</h2>
                <span className="text-xs bg-emerald-100 text-emerald-600 px-2 py-0.5 rounded-full font-bold">AI 분석 완료</span>
            </div>

            {/* Summary Card */}
            <div className="bg-white rounded-3xl overflow-hidden shadow-md border border-emerald-100">
                <div className="bg-emerald-50/50 p-6 border-b border-emerald-50">
                    <div className="flex items-start gap-4">
                        <div className="bg-emerald-100 p-2 rounded-xl text-emerald-600">
                            <PieChart size={24} />
                        </div>
                        <div>
                            <h3 className="font-bold text-gray-800 text-lg mb-1">종합 분석 결과</h3>
                            <p className="text-sm text-gray-600 leading-relaxed text-justify">
                                {report.summary}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Medication Guide */}
                {report.medication_guide && Object.keys(report.medication_guide).length > 0 && (
                    <div className="p-6 border-b border-gray-50">
                        <h4 className="text-sm font-bold text-gray-400 mb-4 flex items-center gap-2">
                            <List size={16} /> 복약 가이드
                        </h4>
                        <div className="bg-blue-50 rounded-xl p-4 space-y-3">
                            {/* Assuming medication_guide has drug_name, usage, warning */}
                            {/* But the interface is Record<string,string> currently. Let's adjust display logic */}
                            {Object.entries(report.medication_guide).map(([key, value]) => (
                                <div key={key} className="flex gap-2 text-sm">
                                    <span className="font-bold text-blue-700 w-24 flex-shrink-0 break-words">{key}:</span>
                                    <span className="text-blue-900 flex-1 break-words">{value}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Food Therapy */}
                <div className="p-6">
                    <h4 className="text-sm font-bold text-gray-400 mb-4 flex items-center gap-2">
                        <Lightbulb size={16} /> 식이요법 추천
                    </h4>

                    <div className="space-y-4">
                        {/* Recommended */}
                        <div>
                            <h5 className="text-xs font-bold text-emerald-600 mb-2">✅ 추천해요</h5>
                            <div className="grid gap-3">
                                {report.food_therapy.recommended.map((food, idx) => (
                                    <div key={idx} className="flex items-start gap-3 bg-gray-50 p-3 rounded-xl">
                                        <span className="text-xl flex-shrink-0">🥬</span>
                                        <div className="flex-1 min-w-0">
                                            <div className="font-bold text-gray-800 text-sm break-words">{food.name}</div>
                                            <div className="text-xs text-gray-500 break-words leading-relaxed mt-0.5">{food.reason}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Avoid */}
                        {report.food_therapy.avoid.length > 0 && (
                            <div className="pt-4 border-t border-dashed border-gray-100">
                                <h5 className="text-xs font-bold text-red-500 mb-2">🚫 피해주세요</h5>
                                <div className="grid gap-3">
                                    {report.food_therapy.avoid.map((food, idx) => (
                                        <div key={idx} className="flex items-start gap-3 bg-red-50/50 p-3 rounded-xl border border-red-50">
                                            <span className="text-xl flex-shrink-0">🥡</span>
                                            <div className="flex-1 min-w-0">
                                                <div className="font-bold text-gray-800 text-sm break-words">{food.name}</div>
                                                <div className="text-xs text-red-400 break-words leading-relaxed mt-0.5">{food.reason}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Lifestyle Advice */}
                <div className="bg-gray-50 p-6 text-sm text-gray-600 border-t border-gray-100 flex items-start gap-3">
                    <AlertTriangle size={18} className="text-amber-500 flex-shrink-0 mt-0.5" />
                    <div>
                        <span className="font-bold text-gray-800 block mb-1">생활 습관 조언</span>
                        {report.lifestyle_advice}
                    </div>
                </div>
            </div>

            {/* Related Questions */}
            {report.related_questions && report.related_questions.length > 0 && (
                <div className="bg-white rounded-3xl shadow-md border border-emerald-100 p-6">
                    <h4 className="text-sm font-bold text-gray-400 mb-4 flex items-center gap-2">
                        <MessageCircle size={16} /> 이런 질문은 어떠세요?
                    </h4>
                    <div className="space-y-2">
                        {report.related_questions.map((item, idx) => (
                            <div key={idx} className="bg-gray-50 rounded-xl px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 cursor-pointer transition-colors">
                                💬 {item.question}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <p className="text-center text-xs text-gray-300">
                본 결과는 의학적 진단을 대신할 수 없습니다.<br />
                정확한 진단은 전문의와 상담하세요.
            </p>
        </motion.div>
    );
}
