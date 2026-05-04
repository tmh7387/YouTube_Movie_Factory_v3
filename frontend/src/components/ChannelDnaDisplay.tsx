import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
    Sparkles, ChevronDown, ChevronUp, BookOpen, Lightbulb,
    Zap, Target, ArrowRight, CheckCircle, Loader2,
} from 'lucide-react';
import axios from 'axios';

const API = 'http://localhost:8000/api';

/* ── Types ────────────────────────────────────────────────────────── */

interface NarrativeDna {
    opening_hook_style: string;
    storytelling_approach: string;
    pacing_cadence: string;
    tone_and_voice: string;
    content_format: string;
    emotional_register: string;
}

interface BibleNarrativeStyle {
    tone: string;
    opening_hook: string;
    storytelling_approach: string;
    pacing: string;
    principles: string[];
}

interface ChannelDna {
    channel_name: string;
    videos_analyzed_titles: string[];
    style_brief: string;
    narrative_dna: NarrativeDna;
    transferable_principles: string[];
    what_makes_it_distinctive: string;
    bible_narrative_style: BibleNarrativeStyle;
}

interface Bible {
    id: string;
    name: string;
    status: string;
}

/* ── Component ────────────────────────────────────────────────────── */

export default function ChannelDnaDisplay({ dna }: { dna: ChannelDna }) {
    const [expandedDna, setExpandedDna] = useState(false);
    const [selectedBibleId, setSelectedBibleId] = useState('');
    const [applySuccess, setApplySuccess] = useState(false);

    // Fetch available bibles for the dropdown
    const { data: bibles = [] } = useQuery<Bible[]>({
        queryKey: ['bibles-list'],
        queryFn: async () => {
            const resp = await axios.get(`${API}/bible`);
            return resp.data;
        },
    });

    // Mutation to apply narrative style to a bible
    const applyMutation = useMutation({
        mutationFn: async () => {
            if (!selectedBibleId) throw new Error('No bible selected');
            await axios.put(`${API}/bible/${selectedBibleId}`, {
                style_lock: {
                    narrative_style: dna.bible_narrative_style,
                },
            });
        },
        onSuccess: () => {
            setApplySuccess(true);
        },
    });

    // Reset success after 3 seconds
    useEffect(() => {
        if (applySuccess) {
            const t = setTimeout(() => setApplySuccess(false), 3000);
            return () => clearTimeout(t);
        }
    }, [applySuccess]);

    if (!dna?.channel_name) return null;

    const dnaEntries: { key: keyof NarrativeDna; icon: JSX.Element; label: string }[] = [
        { key: 'opening_hook_style', icon: <Zap className="w-4 h-4 text-amber-400" />, label: 'Opening Hook' },
        { key: 'storytelling_approach', icon: <BookOpen className="w-4 h-4 text-blue-400" />, label: 'Storytelling' },
        { key: 'pacing_cadence', icon: <ArrowRight className="w-4 h-4 text-green-400" />, label: 'Pacing' },
        { key: 'tone_and_voice', icon: <Sparkles className="w-4 h-4 text-purple-400" />, label: 'Tone & Voice' },
        { key: 'content_format', icon: <Target className="w-4 h-4 text-cyan-400" />, label: 'Format' },
        { key: 'emotional_register', icon: <Lightbulb className="w-4 h-4 text-rose-400" />, label: 'Emotional Register' },
    ];

    return (
        <div className="space-y-5">
            {/* Header */}
            <div className="flex items-center gap-3 mb-2">
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-pink-500/20 to-purple-500/20 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-pink-400" />
                </div>
                <div>
                    <h3 className="text-base font-semibold text-white">
                        {dna.channel_name}
                    </h3>
                    <p className="text-xs text-gray-500">
                        Creative DNA extracted from {dna.videos_analyzed_titles?.length || 0} top videos
                    </p>
                </div>
            </div>

            {/* Style Brief */}
            <div className="bg-gray-800/50 border border-white/5 rounded-lg p-4">
                <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
                    {dna.style_brief}
                </p>
            </div>

            {/* Distinctive Quality */}
            {dna.what_makes_it_distinctive && (
                <div className="bg-gradient-to-r from-pink-500/10 to-purple-500/10 border border-pink-500/20 rounded-lg p-3">
                    <p className="text-xs text-pink-200/70 uppercase tracking-wider mb-1 font-medium">
                        What makes it distinctive
                    </p>
                    <p className="text-sm text-white/90">
                        {dna.what_makes_it_distinctive}
                    </p>
                </div>
            )}

            {/* Narrative DNA Grid */}
            <div>
                <button
                    onClick={() => setExpandedDna(!expandedDna)}
                    className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors mb-3"
                >
                    {expandedDna ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    <span>Narrative DNA Breakdown</span>
                </button>

                {expandedDna && dna.narrative_dna && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {dnaEntries.map(({ key, icon, label }) => (
                            <div
                                key={key}
                                className="bg-gray-800/30 border border-white/5 rounded-lg p-3"
                            >
                                <div className="flex items-center gap-2 mb-1.5">
                                    {icon}
                                    <span className="text-xs font-medium text-gray-400">{label}</span>
                                </div>
                                <p className="text-sm text-gray-300 leading-relaxed">
                                    {dna.narrative_dna[key]}
                                </p>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Transferable Principles */}
            {dna.transferable_principles?.length > 0 && (
                <div>
                    <h4 className="text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
                        <Lightbulb className="w-4 h-4 text-amber-400" />
                        Transferable Principles
                    </h4>
                    <ul className="space-y-2">
                        {dna.transferable_principles.map((principle, i) => (
                            <li
                                key={i}
                                className="text-sm text-gray-300 bg-gray-800/30 border border-white/5 rounded-lg p-3 leading-relaxed"
                            >
                                <span className="text-amber-400/60 font-mono text-xs mr-2">
                                    {String(i + 1).padStart(2, '0')}
                                </span>
                                {principle}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Apply to Bible */}
            {dna.bible_narrative_style && (
                <div className="bg-gray-800/50 border border-white/10 rounded-lg p-4 mt-4">
                    <h4 className="text-sm font-medium text-white mb-3">
                        Apply to Production Bible
                    </h4>
                    <p className="text-xs text-gray-500 mb-3">
                        Inject the extracted narrative style into a Pre-Production Bible's style lock.
                        This adds a <code className="text-pink-400/80">narrative_style</code> block
                        alongside existing visual configurations — nothing is overwritten.
                    </p>
                    <div className="flex gap-2">
                        <select
                            value={selectedBibleId}
                            onChange={e => setSelectedBibleId(e.target.value)}
                            className="flex-1 bg-gray-900 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-pink-500 focus:outline-none"
                        >
                            <option value="">Select a bible…</option>
                            {bibles.map(b => (
                                <option key={b.id} value={b.id}>
                                    {b.name} ({b.status})
                                </option>
                            ))}
                        </select>
                        <button
                            onClick={() => applyMutation.mutate()}
                            disabled={!selectedBibleId || applyMutation.isPending || applySuccess}
                            className="px-4 py-2 rounded-lg text-sm font-medium transition-all
                                disabled:opacity-40 disabled:cursor-not-allowed
                                bg-gradient-to-r from-pink-600 to-purple-600
                                hover:from-pink-500 hover:to-purple-500
                                text-white flex items-center gap-2"
                        >
                            {applyMutation.isPending ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : applySuccess ? (
                                <>
                                    <CheckCircle className="w-4 h-4" />
                                    Applied
                                </>
                            ) : (
                                'Apply Style'
                            )}
                        </button>
                    </div>
                    {applyMutation.isError && (
                        <p className="text-xs text-red-400 mt-2">
                            Failed to apply style. Please try again.
                        </p>
                    )}
                </div>
            )}

            {/* Videos Analyzed */}
            {dna.videos_analyzed_titles?.length > 0 && (
                <div className="pt-2 border-t border-white/5">
                    <p className="text-xs text-gray-600 mb-1">Videos analyzed:</p>
                    <div className="flex flex-wrap gap-1.5">
                        {dna.videos_analyzed_titles.map((title, i) => (
                            <span
                                key={i}
                                className="text-[11px] text-gray-500 bg-gray-800/50 border border-white/5 rounded-md px-2 py-0.5"
                            >
                                {title.length > 50 ? title.slice(0, 47) + '…' : title}
                            </span>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
