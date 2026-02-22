import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Search, FileText, Camera, Loader2, Sparkles, X } from 'lucide-react';

interface Props {
    onExtract: (type: 'symptom' | 'prescription', text?: string, file?: File | null) => Promise<void>;
    isLoading: boolean;
}

export default function Step1Extraction({ onExtract, isLoading }: Props) {
    const [activeTab, setActiveTab] = useState<'symptom' | 'prescription'>('symptom');
    const [textInput, setTextInput] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0] || null;
        setSelectedFile(file);
        if (file) {
            setPreviewUrl(URL.createObjectURL(file));
        } else {
            setPreviewUrl(null);
        }
    };

    const handleRemoveFile = () => {
        setSelectedFile(null);
        setPreviewUrl(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const handleSubmit = async () => {
        if (activeTab === 'symptom' && !textInput.trim()) return;
        if (activeTab === 'prescription' && !selectedFile) return;

        if (activeTab === 'symptom') {
            await onExtract('symptom', textInput);
        } else {
            // 처방전: File 객체를 AnalysisWizard로 전달 (multipart 업로드)
            await onExtract('prescription', undefined, selectedFile);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
        >
            {/* Welcome Banner */}
            <div className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-3xl p-6 text-white shadow-lg relative overflow-hidden">
                <h2 className="text-2xl font-bold mb-2">반가워요! 👋</h2>
                <p className="text-emerald-50 text-sm leading-relaxed opacity-90">
                    오늘 몸 상태는 어떠신가요?<br />
                    사소한 증상이라도 괜찮아요.<br />
                    제가 찬찬히 들어드릴게요.
                </p>
                <Sparkles className="absolute bottom-[-10px] right-[-10px] w-24 h-24 text-white opacity-10 rotate-12" />
            </div>

            {/* Tabs */}
            <div className="flex gap-2 p-1 bg-gray-100 rounded-2xl">
                <button
                    onClick={() => setActiveTab('symptom')}
                    className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'symptom' ? 'bg-white text-emerald-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'
                        }`}
                >
                    <Search size={18} />
                    증상 검색
                </button>
                <button
                    onClick={() => setActiveTab('prescription')}
                    className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'prescription' ? 'bg-white text-emerald-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'
                        }`}
                >
                    <FileText size={18} />
                    처방전 분석
                </button>
            </div>

            {/* Input Area */}
            <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-6 min-h-[280px] flex flex-col">
                {activeTab === 'symptom' ? (
                    <>
                        <h3 className="text-gray-800 font-bold mb-4 flex items-center gap-2">
                            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                            증상을 이야기해주세요
                        </h3>
                        <textarea
                            value={textInput}
                            onChange={(e) => setTextInput(e.target.value)}
                            placeholder="예: 요즘 소화가 잘 안 되고 머리가 지끈거려요."
                            className="w-full flex-1 bg-gray-50 rounded-xl p-4 text-gray-700 placeholder:text-gray-300 resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500/20 text-sm leading-relaxed"
                        />
                    </>
                ) : (
                    <div
                        onClick={() => fileInputRef.current?.click()}
                        className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-gray-200 rounded-xl bg-gray-50/50 hover:bg-emerald-50 hover:border-emerald-300 transition-colors cursor-pointer group relative"
                    >
                        {previewUrl ? (
                            <div className="relative w-full h-full flex items-center justify-center p-2">
                                <img src={previewUrl} alt="처방전 미리보기" className="max-h-40 rounded-lg object-contain shadow" />
                                <button
                                    onClick={(e) => { e.stopPropagation(); handleRemoveFile(); }}
                                    className="absolute top-2 right-2 bg-white rounded-full shadow p-1 text-red-400 hover:text-red-600"
                                >
                                    <X size={14} />
                                </button>
                                <p className="absolute bottom-2 text-xs text-gray-400">{selectedFile?.name}</p>
                            </div>
                        ) : (
                            <>
                                <div className="w-16 h-16 bg-white rounded-full shadow-sm flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                                    <Camera className="text-emerald-500" size={32} />
                                </div>
                                <p className="text-gray-500 font-medium text-sm">처방전을 찍어서 올려주세요</p>
                                <p className="text-gray-400 text-xs mt-1">JPG · PNG · WEBP 지원</p>
                            </>
                        )}
                        <input
                            ref={fileInputRef}
                            type="file"
                            className="hidden"
                            accept="image/jpeg,image/png,image/jpg,image/webp"
                            onChange={handleFileChange}
                        />
                    </div>
                )}

                <div className="mt-6">
                    <button
                        onClick={handleSubmit}
                        disabled={isLoading || (activeTab === 'symptom' ? !textInput : !selectedFile)}
                        className="w-full bg-emerald-600 text-white font-bold py-4 rounded-xl shadow-lg shadow-emerald-200 hover:bg-emerald-700 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="animate-spin" size={20} />
                                분석 중...
                            </>
                        ) : (
                            '분석 시작하기'
                        )}
                    </button>
                </div>
            </div>

            {/* Demo Tip */}
            <div className="text-center">
                <button onClick={() => setTextInput("소화가 안되고 머리가 아파요")} className="text-xs text-gray-400 hover:text-emerald-500 underline decoration-dotted">
                    💡 예시 입력해보기
                </button>
            </div>
        </motion.div>
    );
}
