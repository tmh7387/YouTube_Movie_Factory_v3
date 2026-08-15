import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
    BookOpen,
    Plus,
    Loader2,
    CheckCircle2,
    AlertCircle,
    Clock,
    Lightbulb,
    Wrench,
    ListOrdered,
    ExternalLink,
    AlertTriangle,
    Tag,
    Youtube,
} from 'lucide-react';
import { knowledgeService } from '../services/knowledge';
import type { KnowledgeEntry, KnowledgeCategory } from '../services/knowledge';

const CATEGORIES: { value: KnowledgeCategory; label: string }[] = [
    { value: 'general', label: 'General' },
    { value: 'music_video', label: 'Music Video' },
    { value: 'product_brand', label: 'Product / Brand' },
    { value: 'asmr', label: 'ASMR' },
];

const STATUS_CONFIG: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
    pending:   { color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30', icon: <Clock className="w-3 h-3" />, label: 'Pending' },
    analyzing: { color: 'bg-blue-500/20 text-blue-400 border-blue-500/30', icon: <Loader2 className="w-3 h-3 animate-spin" />, label: 'Analyzing' },
    completed: { color: 'bg-green-500/20 text-green-400 border-green-500/30', icon: <CheckCircle2 className="w-3 h-3" />, label: 'Completed' },
    failed:    { color: 'bg-red-500/20 text-red-400 border-red-500/30', icon: <AlertCircle className="w-3 h-3" />, label: 'Failed' },
};

const Knowledge: React.FC = () => {
    const qc = useQueryClient();
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [url, setUrl] = useState('');
    const [category, setCategory] = useState<KnowledgeCategory>('general');
    const [extraContext, setExtraContext] = useState('');
    const [showForm, setShowForm] = useState(false);

    const { data, isLoading } = useQuery({
        queryKey: ['knowledgeEntries'],
        queryFn: () => knowledgeService.listEntries(),
        refetchInterval: (query) => {
            const active = query.state.data?.entries.some(e => e.status === 'pending' || e.status === 'analyzing');
            return active ? 4000 : false;
        },
    });

    const { data: detail, isLoading: detailLoading } = useQuery({
        queryKey: ['knowledgeEntry', selectedId],
        queryFn: () => knowledgeService.getEntry(selectedId!),
        enabled: !!selectedId,
    });

    const ingestMutation = useMutation({
        mutationFn: knowledgeService.ingest,
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['knowledgeEntries'] });
            setUrl('');
            setExtraContext('');
            setShowForm(false);
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!url.trim()) return;
        ingestMutation.mutate({ youtube_url: url.trim(), category, extra_context: extraContext });
    };

    const entries = data?.entries ?? [];

    return (
        <div className="p-8 max-w-7xl mx-auto">
            {/* Header */}
            <header className="mb-8 flex justify-between items-start">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                            <BookOpen className="w-6 h-6 text-emerald-400" />
                        </div>
                        Knowledge Base
                    </h1>
                    <p className="text-gray-400 mt-2 max-w-lg">
                        Feed YouTube tutorials into the AI learning system. Gemini extracts production techniques, prompts, and workflows into reusable knowledge.
                    </p>
                </div>
                <button
                    onClick={() => setShowForm(v => !v)}
                    className="flex items-center gap-2 px-5 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl transition-all shadow-lg shadow-emerald-600/20 hover:scale-105 active:scale-95"
                >
                    <Plus className="w-4 h-4" />
                    Ingest Tutorial
                </button>
            </header>

            {/* Ingest form */}
            <AnimatePresence>
                {showForm && (
                    <motion.div
                        initial={{ opacity: 0, y: -12, height: 0 }}
                        animate={{ opacity: 1, y: 0, height: 'auto' }}
                        exit={{ opacity: 0, y: -12, height: 0 }}
                        className="mb-8 overflow-hidden"
                    >
                        <form
                            onSubmit={handleSubmit}
                            className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-4"
                        >
                            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                <Youtube className="w-5 h-5 text-red-400" />
                                New Tutorial Ingest
                            </h2>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="md:col-span-2">
                                    <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
                                        YouTube URL
                                    </label>
                                    <input
                                        type="url"
                                        value={url}
                                        onChange={e => setUrl(e.target.value)}
                                        placeholder="https://youtube.com/watch?v=..."
                                        required
                                        className="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-all"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
                                        Category
                                    </label>
                                    <select
                                        value={category}
                                        onChange={e => setCategory(e.target.value as KnowledgeCategory)}
                                        className="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-all"
                                    >
                                        {CATEGORIES.map(c => (
                                            <option key={c.value} value={c.value}>{c.label}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
                                    Extra Context (optional)
                                </label>
                                <textarea
                                    value={extraContext}
                                    onChange={e => setExtraContext(e.target.value)}
                                    placeholder="Any additional context to guide extraction..."
                                    rows={2}
                                    className="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-all resize-none"
                                />
                            </div>
                            <div className="flex justify-end gap-3">
                                <button
                                    type="button"
                                    onClick={() => setShowForm(false)}
                                    className="px-5 py-2.5 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-all"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={ingestMutation.isPending}
                                    className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl flex items-center gap-2 transition-all disabled:opacity-60"
                                >
                                    {ingestMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                                    Start Ingest
                                </button>
                            </div>
                            {ingestMutation.isError && (
                                <p className="text-red-400 text-sm">Failed to submit: {String(ingestMutation.error)}</p>
                            )}
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Main layout: list + detail */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Entry list */}
                <div className="lg:col-span-1 space-y-3">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest">
                            {entries.length} Entries
                        </h2>
                    </div>
                    {isLoading ? (
                        <div className="flex items-center justify-center py-20">
                            <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
                        </div>
                    ) : entries.length === 0 ? (
                        <div className="text-center py-16 border-2 border-dashed border-white/10 rounded-2xl">
                            <BookOpen className="w-10 h-10 text-gray-600 mx-auto mb-3" />
                            <p className="text-gray-500">No tutorials ingested yet.</p>
                            <p className="text-gray-600 text-sm mt-1">Click "Ingest Tutorial" to start.</p>
                        </div>
                    ) : (
                        entries.map(entry => (
                            <motion.div
                                key={entry.id}
                                whileHover={{ scale: 1.01 }}
                                onClick={() => setSelectedId(entry.id)}
                                className={`p-4 rounded-xl cursor-pointer border transition-all ${
                                    selectedId === entry.id
                                        ? 'bg-emerald-600/15 border-emerald-500/50'
                                        : 'bg-white/5 border-white/10 hover:bg-white/8 hover:border-white/20'
                                }`}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <StatusBadge status={entry.status} />
                                    <span className="text-xs text-gray-500 capitalize">{entry.category.replace('_', ' ')}</span>
                                </div>
                                <p className="text-gray-200 text-sm truncate font-medium">
                                    {entry.youtube_url.replace('https://www.youtube.com/watch?v=', 'yt: ')
                                        .replace('https://youtu.be/', 'yt: ')}
                                </p>
                                {entry.standout_tip && (
                                    <p className="text-gray-500 text-xs mt-1.5 line-clamp-2">{entry.standout_tip}</p>
                                )}
                                <div className="mt-2 flex gap-3 text-xs text-gray-600">
                                    {entry.exact_prompts && <span>{entry.exact_prompts.length} prompts</span>}
                                    {entry.tool_names && <span>{entry.tool_names.length} tools</span>}
                                </div>
                            </motion.div>
                        ))
                    )}
                </div>

                {/* Detail panel */}
                <div className="lg:col-span-2">
                    <AnimatePresence mode="wait">
                        {selectedId && detail ? (
                            <motion.div
                                key={selectedId}
                                initial={{ opacity: 0, y: 16 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -16 }}
                                className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden"
                            >
                                <EntryDetail entry={detail} isLoading={detailLoading} />
                            </motion.div>
                        ) : (
                            <div className="h-full flex items-center justify-center border-2 border-dashed border-white/10 rounded-2xl p-16 text-center min-h-[400px]">
                                <div>
                                    <BookOpen className="w-12 h-12 text-gray-700 mx-auto mb-3" />
                                    <p className="text-gray-500">Select an entry to view extracted knowledge</p>
                                </div>
                            </div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
    const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending;
    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-tighter border ${cfg.color}`}>
            {cfg.icon}
            {cfg.label}
        </span>
    );
};

const EntryDetail: React.FC<{ entry: KnowledgeEntry; isLoading: boolean }> = ({ entry, isLoading }) => {
    if (isLoading) return (
        <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
        </div>
    );

    return (
        <div className="divide-y divide-white/10">
            {/* Header */}
            <div className="p-6 bg-gradient-to-br from-emerald-600/10 to-teal-600/5">
                <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                            <StatusBadge status={entry.status} />
                            <span className="text-xs text-gray-500 capitalize">{entry.category.replace('_', ' ')}</span>
                        </div>
                        <a
                            href={entry.youtube_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-emerald-400 hover:text-emerald-300 text-sm flex items-center gap-1 truncate"
                        >
                            <ExternalLink className="w-3 h-3 flex-none" />
                            {entry.youtube_url}
                        </a>
                    </div>
                </div>
                {entry.standout_tip && (
                    <div className="flex items-start gap-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 mt-3">
                        <Lightbulb className="w-5 h-5 text-emerald-400 flex-none mt-0.5" />
                        <p className="text-emerald-200 text-sm leading-relaxed">{entry.standout_tip}</p>
                    </div>
                )}
                {entry.notion_links_alert && (
                    <div className="flex items-start gap-3 bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 mt-3">
                        <AlertTriangle className="w-5 h-5 text-amber-400 flex-none mt-0.5" />
                        <p className="text-amber-200 text-sm">{entry.notion_links_alert}</p>
                    </div>
                )}
                {entry.error_message && (
                    <div className="flex items-start gap-3 bg-red-500/10 border border-red-500/20 rounded-xl p-4 mt-3">
                        <AlertCircle className="w-5 h-5 text-red-400 flex-none mt-0.5" />
                        <p className="text-red-300 text-sm">{entry.error_message}</p>
                    </div>
                )}
            </div>

            {/* Summary */}
            {entry.full_technique_summary && (
                <div className="p-6">
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Technique Summary</h3>
                    <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-line">{entry.full_technique_summary}</p>
                </div>
            )}

            {/* Tools + Workflow */}
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                {entry.tool_names && entry.tool_names.length > 0 && (
                    <div>
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                            <Wrench className="w-3.5 h-3.5" /> Tools Used
                        </h3>
                        <div className="flex flex-wrap gap-2">
                            {entry.tool_names.map((t, i) => (
                                <span key={i} className="px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-500/15 text-blue-300 border border-blue-500/20">
                                    {t}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
                {entry.workflow_steps && entry.workflow_steps.length > 0 && (
                    <div>
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                            <ListOrdered className="w-3.5 h-3.5" /> Workflow Steps
                        </h3>
                        <ol className="space-y-1.5">
                            {entry.workflow_steps.map((step, i) => (
                                <li key={i} className="flex gap-2.5 text-sm text-gray-300">
                                    <span className="flex-none w-5 h-5 rounded-full bg-white/10 flex items-center justify-center text-[10px] font-bold text-gray-400 mt-0.5">
                                        {i + 1}
                                    </span>
                                    {step}
                                </li>
                            ))}
                        </ol>
                    </div>
                )}
            </div>

            {/* Exact Prompts */}
            {entry.exact_prompts && entry.exact_prompts.length > 0 && (
                <div className="p-6">
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                        <Tag className="w-3.5 h-3.5" /> Extracted Prompts ({entry.exact_prompts.length})
                    </h3>
                    <div className="space-y-2">
                        {entry.exact_prompts.map((p, i) => (
                            <div key={i} className="group relative bg-black/40 border border-white/5 rounded-xl p-4 hover:border-emerald-500/30 transition-colors">
                                <p className="text-gray-300 text-sm leading-relaxed font-mono">{p}</p>
                                <button
                                    onClick={() => navigator.clipboard.writeText(p)}
                                    className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity text-xs text-gray-500 hover:text-emerald-400 px-2 py-1 rounded bg-white/5"
                                >
                                    Copy
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Resources */}
            {entry.aggregated_resources && entry.aggregated_resources.length > 0 && (
                <div className="p-6">
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                        <ExternalLink className="w-3.5 h-3.5" /> Found Resources
                    </h3>
                    <div className="space-y-1.5">
                        {entry.aggregated_resources.map((r, i) => (
                            <a
                                key={i}
                                href={r}
                                target="_blank"
                                rel="noreferrer"
                                className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 truncate"
                            >
                                <ExternalLink className="w-3 h-3 flex-none" />
                                {r}
                            </a>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default Knowledge;
