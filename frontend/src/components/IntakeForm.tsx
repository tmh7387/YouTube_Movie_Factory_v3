import React, { useState, useRef, useCallback } from 'react';
import {
    Search,
    Loader2,
    Plus,
    ChevronDown,
    ChevronRight,
    ImagePlus,
    Music,
    X,
    MessageCircle,
    SkipForward,
    Rocket,
    AlertCircle,
} from 'lucide-react';
import { researchApi } from '../services/research';
import type { ResearchBriefSchema } from '../services/research';

// ── State machine ─────────────────────────────────────────────────

type IntakeState =
    | { phase: 'idle' }
    | { phase: 'generating' }
    | {
          phase: 'question';
          brief: ResearchBriefSchema;
          question: string;
          answer: string;
      }
    | { phase: 'confirmed' }
    | { phase: 'error'; message: string };

interface IntakeFormProps {
    onJobCreated: () => void;
}

// ── Constants ─────────────────────────────────────────────────────

const MAX_IMAGES = 3;
const MAX_IMAGE_SIZE = 5 * 1024 * 1024;
const MAX_AUDIO_SIZE = 20 * 1024 * 1024;
const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png'];
const ALLOWED_AUDIO_TYPES = ['audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/mp3'];

// ── Component ─────────────────────────────────────────────────────

export const IntakeForm: React.FC<IntakeFormProps> = ({ onJobCreated }) => {
    // Form fields
    const [topic, setTopic] = useState('');
    const [styleNotes, setStyleNotes] = useState('');
    const [images, setImages] = useState<File[]>([]);
    const [audio, setAudio] = useState<File | null>(null);
    const [showOptional, setShowOptional] = useState(false);

    // State machine
    const [intake, setIntake] = useState<IntakeState>({ phase: 'idle' });

    // Query preview
    const [showQueries, setShowQueries] = useState(false);
    const [currentBrief, setCurrentBrief] = useState<ResearchBriefSchema | null>(null);

    const imageInputRef = useRef<HTMLInputElement>(null);
    const audioInputRef = useRef<HTMLInputElement>(null);

    // ── File handlers ─────────────────────────────────────────────

    const handleImageAdd = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || []);
        const valid = files.filter(
            (f) => ALLOWED_IMAGE_TYPES.includes(f.type) && f.size <= MAX_IMAGE_SIZE,
        );
        setImages((prev) => [...prev, ...valid].slice(0, MAX_IMAGES));
        if (imageInputRef.current) imageInputRef.current.value = '';
    }, []);

    const removeImage = useCallback((idx: number) => {
        setImages((prev) => prev.filter((_, i) => i !== idx));
    }, []);

    const handleAudioAdd = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file && ALLOWED_AUDIO_TYPES.includes(file.type) && file.size <= MAX_AUDIO_SIZE) {
            setAudio(file);
        }
        if (audioInputRef.current) audioInputRef.current.value = '';
    }, []);

    // ── Build FormData ────────────────────────────────────────────

    const buildFormData = useCallback(
        (previousAnswer?: string) => {
            const fd = new FormData();
            fd.append('topic', topic);
            if (styleNotes.trim()) fd.append('style_notes', styleNotes);
            if (previousAnswer) fd.append('previous_answer', previousAnswer);
            images.forEach((img) => fd.append('reference_images', img));
            if (audio) fd.append('reference_audio', audio);
            return fd;
        },
        [topic, styleNotes, images, audio],
    );

    // ── Launch research job ───────────────────────────────────────

    const launchResearch = useCallback(
        async (brief: ResearchBriefSchema) => {
            try {
                await researchApi.startJob(topic, 'standard', brief);
                setIntake({ phase: 'confirmed' });
                // Reset form
                setTopic('');
                setStyleNotes('');
                setImages([]);
                setAudio(null);
                setShowOptional(false);
                setCurrentBrief(null);
                setShowQueries(false);
                onJobCreated();
                // Reset to idle after brief visual confirmation
                setTimeout(() => setIntake({ phase: 'idle' }), 1500);
            } catch (err: any) {
                setIntake({
                    phase: 'error',
                    message: err?.response?.data?.detail || err.message || 'Failed to start research',
                });
            }
        },
        [topic, onJobCreated],
    );

    // ── Generate brief (first turn) ──────────────────────────────

    const handleGenerateBrief = useCallback(async () => {
        if (!topic.trim()) return;
        setIntake({ phase: 'generating' });
        try {
            const formData = buildFormData();
            const res = await researchApi.generateBrief(formData);
            setCurrentBrief(res.research_brief);

            if (res.is_complete) {
                await launchResearch(res.research_brief);
            } else {
                setIntake({
                    phase: 'question',
                    brief: res.research_brief,
                    question: res.clarifying_question || '',
                    answer: '',
                });
            }
        } catch (err: any) {
            setIntake({
                phase: 'error',
                message:
                    err?.response?.data?.detail || err.message || 'Brief generation failed',
            });
        }
    }, [topic, buildFormData, launchResearch]);

    // ── Confirm & Launch (second turn) ───────────────────────────

    const handleConfirmAndLaunch = useCallback(async () => {
        if (intake.phase !== 'question') return;
        const { answer } = intake;
        setIntake({ phase: 'generating' });
        try {
            const formData = buildFormData(answer || undefined);
            const res = await researchApi.generateBrief(formData);
            setCurrentBrief(res.research_brief);
            await launchResearch(res.research_brief);
        } catch (err: any) {
            setIntake({
                phase: 'error',
                message:
                    err?.response?.data?.detail || err.message || 'Brief generation failed',
            });
        }
    }, [intake, buildFormData, launchResearch]);

    // ── Skip & Launch ────────────────────────────────────────────

    const handleSkipAndLaunch = useCallback(async () => {
        if (intake.phase !== 'question') return;
        await launchResearch(intake.brief);
    }, [intake, launchResearch]);

    // ── Derived state ─────────────────────────────────────────────

    const isDisabled = intake.phase === 'generating' || intake.phase === 'confirmed';
    const briefQueries = currentBrief?.youtube_search_queries || [];

    // ── Render ─────────────────────────────────────────────────────

    return (
        <div className="p-5 shrink-0 bg-gray-900/50 shadow-sm z-10 relative">
            <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <Plus className="w-4 h-4 text-blue-400" />
                New Video Project
            </h2>

            {/* ── TOPIC INPUT ────────────────────────────────────── */}
            <div className="space-y-3">
                <div>
                    <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">
                        Video Topic
                    </label>
                    <input
                        type="text"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        placeholder="genre, mood, or topic — e.g. lofi chill beats"
                        maxLength={500}
                        disabled={isDisabled}
                        className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-lg text-sm text-white focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all placeholder:text-gray-600 disabled:opacity-50"
                    />
                </div>

                {/* ── OPTIONAL FIELDS TOGGLE ──────────────────────── */}
                {intake.phase !== 'question' && (
                    <button
                        type="button"
                        onClick={() => setShowOptional(!showOptional)}
                        disabled={isDisabled}
                        className="text-[11px] text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1 transition-colors disabled:opacity-50"
                    >
                        {showOptional ? (
                            <ChevronDown className="w-3 h-3" />
                        ) : (
                            <ChevronRight className="w-3 h-3" />
                        )}
                        Add creative direction
                    </button>
                )}

                {/* ── OPTIONAL FIELDS ────────────────────────────── */}
                {showOptional && intake.phase !== 'question' && (
                    <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
                        {/* Style notes */}
                        <div>
                            <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5">
                                Creative direction
                            </label>
                            <textarea
                                value={styleNotes}
                                onChange={(e) => setStyleNotes(e.target.value)}
                                placeholder="Describe the feel, visual style, references…"
                                maxLength={1000}
                                rows={3}
                                disabled={isDisabled}
                                className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-lg text-sm text-white focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all placeholder:text-gray-600 resize-none disabled:opacity-50"
                            />
                        </div>

                        {/* Reference images */}
                        <div>
                            <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5">
                                Reference images
                                <span className="text-gray-600 font-normal ml-1">
                                    ({images.length}/{MAX_IMAGES})
                                </span>
                            </label>
                            {images.length > 0 && (
                                <div className="flex gap-2 mb-2 flex-wrap">
                                    {images.map((img, idx) => (
                                        <div
                                            key={idx}
                                            className="relative w-14 h-14 rounded-lg overflow-hidden border border-white/10 group"
                                        >
                                            <img
                                                src={URL.createObjectURL(img)}
                                                alt={`ref-${idx}`}
                                                className="w-full h-full object-cover"
                                            />
                                            <button
                                                onClick={() => removeImage(idx)}
                                                className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                                            >
                                                <X className="w-3 h-3 text-white" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {images.length < MAX_IMAGES && (
                                <>
                                    <input
                                        ref={imageInputRef}
                                        type="file"
                                        accept="image/jpeg,image/png"
                                        multiple
                                        onChange={handleImageAdd}
                                        className="hidden"
                                    />
                                    <button
                                        onClick={() => imageInputRef.current?.click()}
                                        disabled={isDisabled}
                                        className="text-xs text-gray-400 hover:text-blue-400 flex items-center gap-1.5 px-2 py-1.5 bg-white/5 rounded-lg border border-dashed border-white/10 hover:border-blue-500/30 transition-all disabled:opacity-50"
                                    >
                                        <ImagePlus className="w-3 h-3" />
                                        Add image (JPEG/PNG, max 5 MB)
                                    </button>
                                </>
                            )}
                        </div>

                        {/* Reference audio */}
                        <div>
                            <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5">
                                Reference audio
                            </label>
                            {audio ? (
                                <div className="flex items-center gap-2 px-2.5 py-1.5 bg-white/5 rounded-lg border border-white/10 text-xs text-gray-300">
                                    <Music className="w-3 h-3 text-green-400 shrink-0" />
                                    <span className="truncate flex-1">{audio.name}</span>
                                    <button
                                        onClick={() => setAudio(null)}
                                        className="text-gray-500 hover:text-red-400 transition-colors"
                                    >
                                        <X className="w-3 h-3" />
                                    </button>
                                </div>
                            ) : (
                                <>
                                    <input
                                        ref={audioInputRef}
                                        type="file"
                                        accept="audio/mpeg,audio/wav"
                                        onChange={handleAudioAdd}
                                        className="hidden"
                                    />
                                    <button
                                        onClick={() => audioInputRef.current?.click()}
                                        disabled={isDisabled}
                                        className="text-xs text-gray-400 hover:text-blue-400 flex items-center gap-1.5 px-2 py-1.5 bg-white/5 rounded-lg border border-dashed border-white/10 hover:border-blue-500/30 transition-all disabled:opacity-50"
                                    >
                                        <Music className="w-3 h-3" />
                                        Add audio (MP3/WAV, max 20 MB)
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                )}

                {/* ── CLARIFYING QUESTION STATE ───────────────────── */}
                {intake.phase === 'question' && (
                    <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
                        {/* Question callout */}
                        <div className="p-3 bg-teal-900/20 border border-teal-500/20 rounded-xl">
                            <div className="flex items-start gap-2">
                                <MessageCircle className="w-4 h-4 text-teal-400 mt-0.5 shrink-0" />
                                <p className="text-sm text-teal-200 leading-relaxed">
                                    {intake.question}
                                </p>
                            </div>
                        </div>

                        {/* Answer input */}
                        <input
                            type="text"
                            value={intake.answer}
                            onChange={(e) =>
                                setIntake({ ...intake, answer: e.target.value })
                            }
                            placeholder="Your answer…"
                            maxLength={300}
                            className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-lg text-sm text-white focus:ring-1 focus:ring-teal-500 focus:border-teal-500 outline-none transition-all placeholder:text-gray-600"
                        />

                        {/* Action buttons */}
                        <div className="flex gap-2">
                            <button
                                onClick={handleConfirmAndLaunch}
                                className="flex-1 bg-green-600 hover:bg-green-500 text-white font-semibold py-2 rounded-lg text-xs shadow-lg shadow-green-600/20 transition-all flex items-center justify-center gap-1.5"
                            >
                                <Rocket className="w-3.5 h-3.5" />
                                Confirm & Launch
                            </button>
                            <button
                                onClick={handleSkipAndLaunch}
                                className="px-3 py-2 border border-white/10 hover:border-white/20 text-gray-400 hover:text-white font-medium rounded-lg text-xs transition-all flex items-center gap-1.5"
                            >
                                <SkipForward className="w-3.5 h-3.5" />
                                Skip
                            </button>
                        </div>
                    </div>
                )}

                {/* ── QUERY PREVIEW ──────────────────────────────── */}
                {briefQueries.length > 0 && intake.phase !== 'confirmed' && (
                    <div className="mt-1">
                        <button
                            onClick={() => setShowQueries(!showQueries)}
                            className="text-[10px] text-gray-500 hover:text-gray-300 flex items-center gap-1 font-medium uppercase tracking-widest transition-colors"
                        >
                            {showQueries ? (
                                <ChevronDown className="w-3 h-3" />
                            ) : (
                                <ChevronRight className="w-3 h-3" />
                            )}
                            View search queries ({briefQueries.length})
                        </button>
                        {showQueries && (
                            <ul className="mt-2 space-y-1 pl-4 animate-in fade-in duration-150">
                                {briefQueries.map((q, i) => (
                                    <li
                                        key={i}
                                        className="text-[11px] text-gray-400 before:content-['›'] before:mr-1.5 before:text-blue-500"
                                    >
                                        {q}
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                )}

                {/* ── ERROR STATE ─────────────────────────────────── */}
                {intake.phase === 'error' && (
                    <div className="p-3 bg-red-900/20 border border-red-500/20 rounded-xl flex items-start gap-2 animate-in fade-in duration-200">
                        <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
                        <div className="flex-1">
                            <p className="text-xs text-red-300">{intake.message}</p>
                            <button
                                onClick={() => setIntake({ phase: 'idle' })}
                                className="text-[10px] text-red-400 hover:text-red-300 mt-1 underline"
                            >
                                Try again
                            </button>
                        </div>
                    </div>
                )}

                {/* ── CONFIRMED STATE ─────────────────────────────── */}
                {intake.phase === 'confirmed' && (
                    <div className="p-3 bg-green-900/20 border border-green-500/20 rounded-xl text-center animate-in fade-in duration-200">
                        <p className="text-xs text-green-300 font-medium">
                            ✓ Research launched — check the log below
                        </p>
                    </div>
                )}

                {/* ── LAUNCH BUTTON (idle state) ──────────────────── */}
                {intake.phase !== 'question' && intake.phase !== 'confirmed' && (
                    <button
                        onClick={handleGenerateBrief}
                        disabled={isDisabled || !topic.trim()}
                        className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2 rounded-lg text-sm shadow-lg shadow-blue-600/20 transition-all disabled:opacity-50 flex items-center justify-center gap-2 group"
                    >
                        {intake.phase === 'generating' ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                            <Search className="w-4 h-4 group-hover:scale-110 transition-transform" />
                        )}
                        {intake.phase === 'generating'
                            ? 'Analyzing intent…'
                            : 'Initialize Research'}
                    </button>
                )}
            </div>
        </div>
    );
};

export default IntakeForm;
