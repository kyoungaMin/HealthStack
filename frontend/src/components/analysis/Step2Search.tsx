import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Check, Edit, Loader2 } from 'lucide-react';
import type { CandidateItem } from '../../services/analysisApi';

interface Props {
    initialKeywords: string[];
    ocrText: string;
    onSearch: (keywords: string[]) => Promise<{ tkm_symptoms: CandidateItem[], modern_drugs: CandidateItem[] }>;
    onGenerateReport: (candidates: { type: string, id: string | number }[]) => Promise<void>;
    isLoading: boolean;
}

export default function Step2Search({ initialKeywords, ocrText: _ocrText, onSearch, onGenerateReport, isLoading }: Props) {
    const [keywords, setKeywords] = useState<string[]>(initialKeywords);
    const [isSearching, setIsSearching] = useState(false);
    const [searchResults, setSearchResults] = useState<{ tkm_symptoms: CandidateItem[], modern_drugs: CandidateItem[] } | null>(null);
    const [selectedCandidates, setSelectedCandidates] = useState<{ type: string, id: string | number }[]>([]);

    // Auto-search on mount if keywords exist
    useEffect(() => {
        if (keywords.length > 0 && !searchResults) {
            handleInitialSearch();
        }
    }, []);

    const handleInitialSearch = async () => {
        setIsSearching(true);
        try {
            const results = await onSearch(keywords);
            setSearchResults(results);
        } catch (e) {
            // Error handled by parent
        } finally {
            setIsSearching(false);
        }
    };

    const toggleCandidate = (type: string, id: string | number) => {
        const isSelected = selectedCandidates.some(c => c.type === type && c.id === id);
        if (isSelected) {
            setSelectedCandidates(selectedCandidates.filter(c => !(c.type === type && c.id === id)));
        } else {
            setSelectedCandidates([...selectedCandidates, { type, id }]);
        }
    };

    const handleNext = () => {
        if (selectedCandidates.length === 0) {
            alert("분석할 항목을 적어도 하나 선택해주세요.");
            return;
        }
        onGenerateReport(selectedCandidates);
    };

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
        >
            {/* 1. Keyword Confirmation */}
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-emerald-100">
                <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <span className="w-6 h-6 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center text-xs">1</span>
                    증상 키워드 확인
                </h3>

                <div className="flex flex-wrap gap-2">
                    {keywords.map((kw, idx) => (
                        <div key={idx} className="bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-2 border border-emerald-100">
                            #{kw}
                            <button onClick={() => setKeywords(keywords.filter(k => k !== kw))} className="text-emerald-400 hover:text-emerald-600">×</button>
                        </div>
                    ))}
                    <button className="text-gray-400 text-sm px-2 py-1 flex items-center gap-1 hover:text-emerald-500">
                        <Edit size={14} /> 추가
                    </button>
                </div>
            </div>

            {/* 2. Candidate Selection */}
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100 min-h-[300px]">
                <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs">2</span>
                    관련된 항목 선택
                </h3>

                {isSearching ? (
                    <div className="flex flex-col items-center justify-center h-40 text-gray-400 gap-2">
                        <Loader2 className="animate-spin text-emerald-500" size={32} />
                        <p className="text-sm">동의보감과 약학정보를 검색 중입니다...</p>
                    </div>
                ) : searchResults ? (
                    <div className="space-y-6">
                        {/* TKM Symptoms */}
                        {(searchResults.tkm_symptoms.length > 0) && (
                            <div>
                                <h4 className="text-xs font-bold text-gray-500 mb-3 ml-1">동의보감 증상 (한의학)</h4>
                                <div className="space-y-3">
                                    {searchResults.tkm_symptoms.map(item => (
                                        <div
                                            key={`tkm-${item.id}`}
                                            onClick={() => toggleCandidate('tkm_symptom', item.id)}
                                            className={`p-4 rounded-xl border-2 transition-all cursor-pointer relative ${selectedCandidates.some(c => c.type === 'tkm_symptom' && c.id === item.id)
                                                ? 'border-emerald-500 bg-emerald-50/50'
                                                : 'border-gray-100 hover:border-emerald-200'
                                                }`}
                                        >
                                            <div className="flex justify-between items-start gap-3">
                                                <div className="flex-1 min-w-0">
                                                    <h5 className="font-bold text-gray-800 break-words">{item.name}</h5>
                                                    <p className="text-sm text-gray-600 mt-1 line-clamp-3 break-words">{item.description}</p>
                                                </div>
                                                {selectedCandidates.some(c => c.type === 'tkm_symptom' && c.id === item.id) && (
                                                    <div className="bg-emerald-500 text-white rounded-full p-1 shadow-sm flex-shrink-0">
                                                        <Check size={14} />
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Modern Drugs */}
                        {(searchResults.modern_drugs.length > 0) && (
                            <div>
                                <h4 className="text-xs font-bold text-gray-500 mb-3 ml-1 mt-6">현대 의약품 정보</h4>
                                <div className="space-y-3">
                                    {searchResults.modern_drugs.map(item => (
                                        <div
                                            key={`drug-${item.id}`}
                                            onClick={() => toggleCandidate('modern_drug', item.id)}
                                            className={`p-4 rounded-xl border-2 transition-all cursor-pointer relative ${selectedCandidates.some(c => c.type === 'modern_drug' && c.id === item.id)
                                                ? 'border-blue-500 bg-blue-50/50'
                                                : 'border-gray-100 hover:border-blue-200'
                                                }`}
                                        >
                                            <div className="flex justify-between items-start gap-3">
                                                <div className="flex-1 min-w-0">
                                                    <h5 className="font-bold text-gray-800 break-words">{item.name}</h5>
                                                    <p className="text-xs text-blue-600 bg-blue-50 inline-block px-2 py-0.5 rounded-md mt-1 break-all">{item.category}</p>
                                                    <p className="text-sm text-gray-600 mt-2 line-clamp-2 break-words">{item.efficacy}</p>
                                                </div>
                                                {selectedCandidates.some(c => c.type === 'modern_drug' && c.id === item.id) && (
                                                    <div className="bg-blue-500 text-white rounded-full p-1 shadow-sm flex-shrink-0">
                                                        <Check size={14} />
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="text-center py-10 text-gray-400">
                        검색 결과가 없습니다.
                    </div>
                )}
            </div>

            {/* Next Button */}
            <button
                onClick={handleNext}
                disabled={isLoading || selectedCandidates.length === 0}
                className="w-full bg-emerald-600 text-white font-bold py-4 rounded-2xl shadow-lg shadow-emerald-200 hover:bg-emerald-700 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
                {isLoading ? <Loader2 className="animate-spin" /> : '최종 리포트 생성하기'}
            </button>

        </motion.div>
    );
}
