import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    X, Utensils, BookOpen, Heart, PlusCircle,
    Loader2, CheckCircle, Sparkles, RefreshCw, Send,
} from 'lucide-react';
import type { PrescriptionData, SymptomDietResult } from '../../services/analysisApi';
import { getDietRecommendation, getSymptomDiet } from '../../services/analysisApi';

// ─── Types ────────────────────────────────────────────────────────────────────

interface SavedStackLike {
    id: string;
    date: string;
    title: string;
    type: 'prescription' | 'symptom';
    prescriptionData?: PrescriptionData;
}

interface Props {
    savedStacks: SavedStackLike[];
    onClose: () => void;
    onAnalyzePrescription: () => void;
}

// ─── FoodCard ─────────────────────────────────────────────────────────────────

function FoodCard({ name, reason, precaution, index }: {
    name: string; reason: string; precaution?: string; index: number;
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.07 }}
            className="bg-white p-4 rounded-2xl border border-amber-100 shadow-sm"
        >
            <div className="flex items-center gap-2 mb-1">
                <span className="w-6 h-6 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0">
                    {index + 1}
                </span>
                <p className="font-bold text-amber-900 text-sm">{name}</p>
            </div>
            <p className="text-[11px] text-amber-700/80 leading-relaxed pl-8">{reason}</p>
            {precaution && (
                <p className="text-[10px] text-rose-500 mt-1 pl-8">⚠️ {precaution}</p>
            )}
        </motion.div>
    );
}

// ─── SymptomInputPanel ────────────────────────────────────────────────────────

function SymptomInputPanel({
    onResult,
    onAnalyzePrescription,
}: {
    onResult: (result: SymptomDietResult) => void;
    onAnalyzePrescription: () => void;
}) {
    const [symptom, setSymptom] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleSubmit = async () => {
        const text = symptom.trim();
        if (!text) { setError('증상을 입력해주세요.'); return; }
        setError('');
        setLoading(true);
        try {
            const result = await getSymptomDiet(text);
            onResult(result);
        } catch (e) {
            setError('분석 중 오류가 발생했습니다. 다시 시도해주세요.');
        } finally {
            setLoading(false);
        }
    };

    const EXAMPLES = ['소화가 안 되고 속이 더부룩해요', '잠을 잘 못 자고 피로가 심해요', '무릎이 자주 아프고 붓는 편이에요'];

    return (
        <div className="space-y-6">
            <div className="text-center py-4">
                <div className="w-16 h-16 bg-gradient-to-br from-amber-100 to-orange-100 rounded-[24px] flex items-center justify-center mx-auto mb-4">
                    <span className="text-3xl">🌿</span>
                </div>
                <h4 className="text-lg font-bold text-slate-800 mb-1">증상을 알려주세요</h4>
                <p className="text-slate-500 text-xs leading-relaxed">
                    증상을 입력하면 동의보감 기반 맞춤 식단을 추천해드려요.
                </p>
            </div>

            {/* 예시 태그 */}
            <div className="flex flex-wrap gap-2">
                {EXAMPLES.map((ex) => (
                    <button
                        key={ex}
                        onClick={() => { setSymptom(ex); textareaRef.current?.focus(); }}
                        className="px-3 py-1.5 bg-amber-50 text-amber-700 text-[11px] font-bold rounded-full border border-amber-100 hover:bg-amber-100 transition-colors"
                    >
                        {ex}
                    </button>
                ))}
            </div>

            {/* 입력창 */}
            <div className="relative">
                <textarea
                    ref={textareaRef}
                    value={symptom}
                    onChange={(e) => setSymptom(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit(); }}
                    placeholder="예: 요즘 소화가 안 되고 속이 더부룩해요. 피로도 심하고 식욕이 없어요."
                    rows={3}
                    className="w-full px-4 py-3 text-sm text-slate-700 bg-slate-50 border border-slate-200 rounded-2xl resize-none outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-50 transition-all placeholder:text-slate-400"
                />
                <p className="text-[10px] text-slate-400 mt-1 text-right">Ctrl+Enter로 빠르게 분석</p>
            </div>

            {error && <p className="text-xs text-rose-500">{error}</p>}

            <button
                onClick={handleSubmit}
                disabled={loading || !symptom.trim()}
                className="w-full py-3.5 bg-gradient-to-br from-amber-500 to-orange-500 text-white font-bold text-sm rounded-2xl flex items-center justify-center gap-2 hover:brightness-105 transition-all disabled:opacity-60 shadow-lg shadow-amber-100"
            >
                {loading ? (
                    <>
                        <Loader2 size={18} className="animate-spin" />
                        동의보감 식단 분석 중...
                    </>
                ) : (
                    <>
                        <Send size={16} />
                        식단 분석하기
                    </>
                )}
            </button>

            {/* 구분선 + 처방전 분석 유도 */}
            <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-slate-100" />
                <span className="text-[10px] text-slate-400 font-bold">또는</span>
                <div className="flex-1 h-px bg-slate-100" />
            </div>
            <button
                onClick={onAnalyzePrescription}
                className="w-full py-3 border border-slate-200 rounded-2xl text-sm font-bold text-slate-600 hover:bg-slate-50 flex items-center justify-center gap-2 transition-colors"
            >
                <PlusCircle size={16} />
                처방전 이미지로 분석하기
            </button>
        </div>
    );
}

// ─── DietGuideModal ───────────────────────────────────────────────────────────

export default function DietGuideModal({ savedStacks, onClose, onAnalyzePrescription }: Props) {
    const [recipeLoading, setRecipeLoading] = useState(false);
    const [recipeText, setRecipeText] = useState<string | null>(null);

    // 증상 입력으로 얻은 식단 결과 (케이스 2/3용)
    const [symptomDiet, setSymptomDiet] = useState<SymptomDietResult | null>(null);
    // 증상 입력 화면으로 돌아가기
    const [showSymptomInput, setShowSymptomInput] = useState(true);

    // 가장 최근 처방전 중 donguibogam.foods가 있는 것 찾기
    const latestWithDiet = savedStacks.find(
        s => s.type === 'prescription' &&
            (s.prescriptionData?.donguibogam?.foods?.length ?? 0) > 0
    );

    const donguibogam = latestWithDiet?.prescriptionData?.donguibogam;
    const lifestyleAdvice = latestWithDiet?.prescriptionData?.lifestyleGuide?.advice;

    // 추천 음식만 필터 (주의/회피 식품 제외)
    const getRecommendedFoods = () =>
        currentFoods.filter(f => !f.precaution || !f.precaution.includes('주의'));

    // 레시피 생성 (현재 표시 중인 추천 음식 기반)
    const fetchRecipe = async () => {
        const recommended = getRecommendedFoods();
        if (recommended.length === 0) return;
        setRecipeLoading(true);
        try {
            const foods = recommended.map(f => f.name).join(', ');
            const drugs = latestWithDiet?.prescriptionData?.prescriptionSummary?.drugList?.join(', ') ?? '';
            const result = await getDietRecommendation(foods, drugs);
            setRecipeText(result);
        } catch (e) {
            console.error(e);
        } finally {
            setRecipeLoading(false);
        }
    };

    // 증상 식단 결과 처리
    const handleSymptomDietResult = (result: SymptomDietResult) => {
        setSymptomDiet(result);
        setShowSymptomInput(false);
    };

    // 헤더 subtitle 결정
    const getSubtitle = () => {
        if (symptomDiet && !showSymptomInput) return '증상 기반 맞춤 식단';
        if (showSymptomInput) return '증상을 입력해서 식단을 받아보세요';
        return '동의보감 기반 맞춤 추천';
    };

    // 케이스 결정: 처방 식단 있으면 표시, 없으면 증상 입력 또는 결과
    const showSymptomResult = !!symptomDiet && !showSymptomInput;
    const showPrescriptionDiet = !!latestWithDiet && !showSymptomInput && !symptomDiet;
    const showInputPanel = !showPrescriptionDiet && !showSymptomResult;

    // 현재 표시할 foods (처방전 or 증상 분석)
    const currentFoods = showPrescriptionDiet
        ? (donguibogam?.foods ?? [])
        : (symptomDiet?.foods ?? []);

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-10">
            {/* Backdrop */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onClose}
                className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
            />

            {/* Modal */}
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className="relative w-full max-w-2xl max-h-[88vh] bg-white rounded-[40px] shadow-2xl overflow-hidden flex flex-col"
            >
                {/* Header */}
                <div className="p-8 bg-gradient-to-br from-amber-500 to-orange-500 text-white shrink-0">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-md">
                                <Utensils size={24} />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold">식단 가이드</h3>
                                <p className="text-amber-100 text-sm opacity-90">{getSubtitle()}</p>
                            </div>
                        </div>
                        <button onClick={onClose} className="p-3 bg-white/20 rounded-2xl hover:bg-white/30 transition-colors">
                            <X size={22} />
                        </button>
                    </div>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto p-8 space-y-6">
                    <AnimatePresence mode="wait">

                        {/* ── 식단 결과 표시 (처방전 기반 or 증상 기반) ── */}
                        {(showPrescriptionDiet || showSymptomResult) && (
                            <motion.div
                                key="diet-result"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="space-y-6"
                            >
                                {/* 증상으로 재분석 버튼 */}
                                <button
                                    onClick={() => { setShowSymptomInput(true); setSymptomDiet(null); setRecipeText(null); }}
                                    className="flex items-center gap-1.5 px-4 py-2 bg-amber-50 text-amber-700 text-xs font-bold rounded-full border border-amber-200 hover:bg-amber-100 transition-colors"
                                >
                                    <RefreshCw size={14} />
                                    다른 증상으로 재분석
                                </button>

                                {/* 동의보감 인용구 */}
                                {(donguibogam?.donguiSection || symptomDiet?.donguiSection) && (
                                    <div className="p-5 bg-amber-50 rounded-2xl border border-amber-100 relative overflow-hidden">
                                        <BookOpen size={14} className="text-amber-500 mb-2" />
                                        <p className="text-amber-800 text-sm italic leading-relaxed">
                                            "{showPrescriptionDiet ? donguibogam?.donguiSection : symptomDiet?.donguiSection}"
                                        </p>
                                        <div className="absolute -bottom-3 -right-3 text-6xl opacity-5">📖</div>
                                    </div>
                                )}

                                {/* 약선 음식 목록 */}
                                <div>
                                    <p className="text-[10px] font-bold text-amber-600 uppercase tracking-widest mb-3 flex items-center gap-2">
                                        <Sparkles size={12} />
                                        추천 약선 음식
                                    </p>
                                    <div className="space-y-2">
                                        {currentFoods.map((food, i) => (
                                            <FoodCard
                                                key={i}
                                                index={i}
                                                name={food.name}
                                                reason={food.reason}
                                                precaution={food.precaution}
                                            />
                                        ))}
                                    </div>
                                </div>

                                {/* 생활 가이드 (처방전 기반일 때만) */}
                                {showPrescriptionDiet && lifestyleAdvice && (
                                    <div className="p-5 bg-emerald-50 rounded-2xl border border-emerald-100">
                                        <div className="flex items-center gap-2 mb-2 text-emerald-700">
                                            <Heart size={14} />
                                            <span className="text-[10px] font-bold uppercase tracking-widest">생활 가이드</span>
                                        </div>
                                        <p className="text-emerald-800/80 text-sm leading-relaxed">{lifestyleAdvice}</p>
                                    </div>
                                )}

                                {/* 추천 식단 요약 (증상 기반일 때만) */}
                                {showSymptomResult && currentFoods.length > 0 && (() => {
                                    const recommended = getRecommendedFoods();
                                    const cautionFoods = currentFoods.filter(f => f.precaution && f.precaution.includes('주의'));
                                    return (
                                        <div className="p-5 bg-emerald-50 rounded-2xl border border-emerald-100">
                                            <div className="flex items-center gap-2 mb-2 text-emerald-700">
                                                <Heart size={14} />
                                                <span className="text-[10px] font-bold uppercase tracking-widest">맞춤 식단 요약</span>
                                            </div>
                                            <p className="text-emerald-800/80 text-sm leading-relaxed">
                                                {recommended.length > 0 && (
                                                    <>입력하신 증상에 도움이 되는 <strong>{recommended.map(f => f.name).join(', ')}</strong> 등을 추천드립니다. </>
                                                )}
                                                {cautionFoods.length > 0 && (
                                                    <><strong className="text-rose-600">{cautionFoods.map(f => f.name).join(', ')}</strong>은(는) 피하시는 것이 좋습니다. </>
                                                )}
                                                의약품 복용 중이시라면 반드시 전문의와 상담 후 드세요.
                                            </p>
                                        </div>
                                    );
                                })()}

                                {/* 힐링 레시피 버튼 */}
                                {!recipeText ? (
                                    <button
                                        onClick={fetchRecipe}
                                        disabled={recipeLoading || getRecommendedFoods().length === 0}
                                        className="w-full p-5 rounded-2xl bg-gradient-to-br from-rose-400 to-pink-500 text-white font-bold flex items-center justify-center gap-3 hover:brightness-105 transition-all disabled:opacity-70 shadow-lg shadow-rose-100"
                                    >
                                        {recipeLoading ? (
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
                                        <div className="flex items-center justify-between mb-3">
                                            <h5 className="text-xs font-bold text-rose-700 uppercase tracking-widest flex items-center gap-2">
                                                <CheckCircle size={14} />
                                                맞춤 힐링 레시피
                                            </h5>
                                            {/* 다시 받기 */}
                                            <button
                                                onClick={() => setRecipeText(null)}
                                                className="flex items-center gap-1 text-[10px] font-bold text-rose-400 hover:text-rose-600 transition-colors"
                                            >
                                                <RefreshCw size={12} />
                                                다시 받기
                                            </button>
                                        </div>
                                        <p className="text-slate-700 text-sm leading-relaxed whitespace-pre-wrap">
                                            {recipeText}
                                        </p>
                                    </motion.div>
                                )}
                            </motion.div>
                        )}

                        {/* ── 증상 입력 패널 ── */}
                        {showInputPanel && (
                            <motion.div
                                key="symptom-input"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                            >
                                <SymptomInputPanel
                                    onResult={handleSymptomDietResult}
                                    onAnalyzePrescription={() => { onClose(); onAnalyzePrescription(); }}
                                />
                            </motion.div>
                        )}

                    </AnimatePresence>
                </div>

                {/* Footer */}
                <div className="px-8 py-5 bg-slate-50 border-t border-slate-100 shrink-0">
                    <p className="text-center text-[10px] text-slate-400">
                        본 식단 정보는 동의보감 및 AI 분석을 기반으로 하며, 의료적 처방을 대신하지 않습니다.
                    </p>
                </div>
            </motion.div>
        </div>
    );
}
