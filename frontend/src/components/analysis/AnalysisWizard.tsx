import { useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import Step1Extraction from './Step1Extraction';
import Step2Search from './Step2Search';
import Step3Report from './Step3Report';
import { step1Extract, step2Search, step3Report, analyzePrescriptionFile } from '../../services/analysisApi';
import type { ReportData } from '../../services/analysisApi';

interface Props {
    onReportComplete?: (report: ReportData, title: string) => void;
}

export default function AnalysisWizard({ onReportComplete }: Props) {
    const [step, setStep] = useState<1 | 2 | 3>(1);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [sessionId, setSessionId] = useState<string>('');
    const [detectedKeywords, setDetectedKeywords] = useState<{ keyword: string, confidence: number }[]>([]);
    const [ocrText, setOcrText] = useState<string>('');
    const [_candidates, setCandidates] = useState<{ tkm_symptoms: any[], modern_drugs: any[] } | null>(null);
    const [finalReport, setFinalReport] = useState<any>(null);
    const [reportTitle, setReportTitle] = useState<string>('증상 분석');

    const handleExtract = async (type: 'symptom' | 'prescription', text?: string, file?: File | null) => {
        setIsLoading(true);
        setError(null);
        try {
            if (type === 'prescription' && file) {
                const result = await analyzePrescriptionFile(file);
                const report: ReportData = {
                    summary: result.summary || result.prescriptionSummary || '처방전 분석이 완료되었습니다.',
                    medication_guide: result.medicationGuide || result.medication_guide || {},
                    food_therapy: result.foodTherapy || result.food_therapy || { recommended: [], avoid: [] },
                    lifestyle_advice: result.lifestyleAdvice || result.lifestyle_advice || '',
                    related_questions: result.relatedQuestions || result.related_questions || [],
                };
                const title = Object.keys(report.medication_guide || {}).join(', ') || '처방전 분석';
                setFinalReport(report);
                setReportTitle(title);
                setStep(3);
                onReportComplete?.(report, title);
            } else {
                const data = await step1Extract(type, text);
                setSessionId(data.session_id);
                setDetectedKeywords(data.detected_keywords || []);
                setOcrText(data.ocr_text || '');
                if (text) setReportTitle(text.slice(0, 30) + (text.length > 30 ? '...' : ''));
                setStep(2);
            }
        } catch (err) {
            setError(type === 'prescription'
                ? "처방전 분석에 실패했습니다. 이미지를 확인하고 다시 시도해주세요."
                : "증상 인식에 실패했습니다. 다시 시도해주세요."
            );
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSearch = async (confirmedKeywords: string[]) => {
        setIsLoading(true);
        try {
            const data = await step2Search(sessionId, confirmedKeywords);
            setCandidates(data.candidates);
            return data.candidates;
        } catch (err) {
            setError("검색 중 오류가 발생했습니다.");
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    const handleGenerateReport = async (selectedCandidates: { type: string, id: string | number }[]) => {
        setIsLoading(true);
        try {
            const report = await step3Report(sessionId, selectedCandidates);
            setFinalReport(report);
            setStep(3);
            onReportComplete?.(report, reportTitle);
        } catch (err) {
            setError("리포트 생성에 실패했습니다.");
        } finally {
            setIsLoading(false);
        }
    };

    const onReset = () => {
        setStep(1);
        setSessionId('');
        setDetectedKeywords([]);
        setCandidates(null);
        setFinalReport(null);
        setError(null);
        setReportTitle('증상 분석');
    };

    return (
        <div className="min-h-[500px] bg-gray-50 flex flex-col">
            {/* Header */}
            <header className="p-4 bg-white border-b border-gray-100 flex justify-between items-center">
                <h1 className="text-lg font-bold text-emerald-600 flex items-center gap-2">
                    🌱 Health Stack
                </h1>
                <button onClick={onReset} className="text-xs text-gray-400 font-medium hover:text-emerald-500 transition-colors">
                    처음으로
                </button>
            </header>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto p-4 relative">
                <AnimatePresence mode="wait">
                    {step === 1 && (
                        <Step1Extraction
                            key="step1"
                            onExtract={handleExtract}
                            isLoading={isLoading}
                        />
                    )}
                    {step === 2 && (
                        <Step2Search
                            key="step2"
                            initialKeywords={detectedKeywords.map(k => k.keyword)}
                            ocrText={ocrText}
                            onSearch={handleSearch}
                            onGenerateReport={handleGenerateReport}
                            isLoading={isLoading}
                        />
                    )}
                    {step === 3 && finalReport && (
                        <Step3Report
                            key="step3"
                            report={finalReport}
                        />
                    )}
                </AnimatePresence>

                {error && (
                    <div className="absolute bottom-4 left-4 right-4 bg-red-50 text-red-600 p-3 rounded-xl text-sm shadow-lg border border-red-100 animate-in fade-in slide-in-from-bottom-2">
                        ⚠️ {error}
                    </div>
                )}
            </main>
        </div>
    );
}
