import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    BookMarked,
    Check,
    ChevronRight,
    Copy,
    Film,
    Grid3x3,
    Image as ImageIcon,
    Info,
    Layers,
    Lightbulb,
    Music,
    Search,
    Sparkles,
    Wand2,
    X,
    AlertTriangle,
    CheckCircle2,
    Blocks,
    Cpu,
} from 'lucide-react';
import {
    STYLE_TILES,
    PROMPT_STRUCTURES,
    PROMPT_CATEGORIES,
    MODEL_GUIDES,
    REFERENCE_PACKS,
    REFERENCE_RULES,
    REFERENCE_EXAMPLE,
    TIP_GROUPS,
    CONTINUITY_NOTE,
    CONTINUITY_BADGE,
    CORE_PREMISE,
    ANTI_SLOP_NOTE,
    assemblePrompt,
} from '../data/promptLibrary';
import type { StyleTile, ModelGuide } from '../data/promptLibrary';

type TabKey = 'styles' | 'structures' | 'categories' | 'models' | 'video' | 'tips';

const TABS: { key: TabKey; label: string; icon: React.ElementType }[] = [
    { key: 'styles', label: 'Style Tiles', icon: Grid3x3 },
    { key: 'structures', label: 'Structures', icon: Blocks },
    { key: 'categories', label: 'Prompt Library', icon: BookMarked },
    { key: 'models', label: 'Model Guides', icon: Cpu },
    { key: 'video', label: 'Video References', icon: Film },
    { key: 'tips', label: 'Tips', icon: Lightbulb },
];

/* ------------------------------------------------------------------ */
/* Shared bits                                                         */
/* ------------------------------------------------------------------ */

const CopyButton: React.FC<{ text: string; label?: string; className?: string }> = ({
    text,
    label = 'Copy',
    className = '',
}) => {
    const [copied, setCopied] = useState(false);

    const handle = async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1600);
    };

    return (
        <button
            onClick={handle}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                copied
                    ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                    : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-amber-300 border border-white/10'
            } ${className}`}
        >
            {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            {copied ? 'Copied' : label}
        </button>
    );
};

const PromptBlock: React.FC<{ text: string; maxHeight?: string }> = ({ text, maxHeight = 'none' }) => (
    <div className="group relative">
        <pre
            className="text-gray-300 text-xs leading-relaxed bg-black/40 rounded-xl p-4 whitespace-pre-wrap border border-white/5 font-mono overflow-auto"
            style={{ maxHeight }}
        >
            {text}
        </pre>
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <CopyButton text={text} />
        </div>
    </div>
);

const SectionHeading: React.FC<{ children: React.ReactNode; icon?: React.ElementType }> = ({
    children,
    icon: Icon,
}) => (
    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2">
        {Icon && <Icon className="w-3.5 h-3.5" />}
        {children}
    </h3>
);

/* ------------------------------------------------------------------ */
/* Style tiles tab                                                     */
/* ------------------------------------------------------------------ */

const StyleTilesTab: React.FC<{
    selected: string[];
    onToggle: (slug: string) => void;
}> = ({ selected, onToggle }) => {
    const [detail, setDetail] = useState<StyleTile | null>(null);
    const [filter, setFilter] = useState<'all' | 'strong' | 'medium' | 'weak'>('all');
    const [query, setQuery] = useState('');

    const tiles = useMemo(() => {
        return STYLE_TILES.filter(t => {
            if (filter !== 'all' && t.continuity !== filter) return false;
            if (!query.trim()) return true;
            const q = query.toLowerCase();
            return (
                t.name.toLowerCase().includes(q) ||
                t.descriptor.toLowerCase().includes(q) ||
                t.snippet.toLowerCase().includes(q) ||
                t.bestUses.some(u => u.toLowerCase().includes(q))
            );
        });
    }, [filter, query]);

    return (
        <div>
            {/* Continuity guidance */}
            <div className="mb-6 p-4 bg-amber-500/5 border border-amber-500/20 rounded-2xl flex gap-3">
                <Info className="w-4 h-4 text-amber-400 flex-none mt-0.5" />
                <p className="text-sm text-gray-300 leading-relaxed">{CONTINUITY_NOTE}</p>
            </div>

            {/* Controls */}
            <div className="flex flex-wrap gap-3 mb-6 items-center">
                <div className="relative flex-1 min-w-[220px]">
                    <Search className="w-4 h-4 text-gray-600 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        placeholder="Search styles, uses, snippets…"
                        className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-3 py-2 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-amber-500/50"
                    />
                </div>

                <div className="flex gap-1.5">
                    {(['all', 'strong', 'medium', 'weak'] as const).map(f => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all ${
                                filter === f
                                    ? 'bg-amber-600 text-white'
                                    : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white border border-white/10'
                            }`}
                        >
                            {f === 'all' ? 'All' : `${f} anchor`}
                        </button>
                    ))}
                </div>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
                {tiles.map(tile => {
                    const isSelected = selected.includes(tile.slug);
                    return (
                        <motion.button
                            key={tile.slug}
                            whileHover={{ y: -3 }}
                            onClick={() => setDetail(tile)}
                            className={`group text-left rounded-xl overflow-hidden border transition-all ${
                                isSelected
                                    ? 'border-amber-500/60 ring-2 ring-amber-500/30 bg-amber-500/5'
                                    : 'border-white/10 bg-white/5 hover:border-white/25'
                            }`}
                        >
                            {/* Text head */}
                            <div className="p-3 pb-2">
                                <div className="flex items-start justify-between mb-1.5">
                                    <span className="text-[10px] font-mono font-bold text-gray-600">
                                        {String(tile.id).padStart(2, '0')}
                                    </span>
                                    <span
                                        className={`w-1.5 h-1.5 rounded-full ${
                                            tile.continuity === 'strong'
                                                ? 'bg-green-500'
                                                : tile.continuity === 'medium'
                                                ? 'bg-yellow-500'
                                                : 'bg-orange-500'
                                        }`}
                                        title={`${tile.continuity} continuity anchor`}
                                    />
                                </div>
                                <h4 className="text-white text-sm font-semibold leading-tight">{tile.name}</h4>
                                <p className="text-[10px] text-gray-500 leading-snug mt-0.5 line-clamp-2">
                                    {tile.descriptor}
                                </p>
                            </div>

                            {/* Visual swatch */}
                            <div className={`relative h-20 ${tile.swatch}`}>
                                <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
                                <div className="absolute bottom-1.5 right-1.5 w-5 h-5 rounded-md bg-black/40 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                    <ChevronRight className="w-3 h-3 text-white" />
                                </div>
                                {isSelected && (
                                    <div className="absolute top-1.5 left-1.5 w-5 h-5 rounded-md bg-amber-500 flex items-center justify-center">
                                        <Check className="w-3 h-3 text-white" />
                                    </div>
                                )}
                            </div>
                        </motion.button>
                    );
                })}
            </div>

            {tiles.length === 0 && (
                <div className="text-center py-16 border-2 border-dashed border-white/10 rounded-2xl">
                    <p className="text-gray-500 text-sm">No styles match that filter.</p>
                </div>
            )}

            {/* Detail drawer */}
            <AnimatePresence>
                {detail && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setDetail(null)}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-end"
                    >
                        <motion.div
                            initial={{ x: 400 }}
                            animate={{ x: 0 }}
                            exit={{ x: 400 }}
                            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
                            onClick={e => e.stopPropagation()}
                            className="w-full max-w-md bg-[#12141c] border-l border-white/10 overflow-y-auto"
                        >
                            <div className={`h-32 ${detail.swatch} relative`}>
                                <div className="absolute inset-0 bg-gradient-to-t from-[#12141c] to-transparent" />
                                <button
                                    onClick={() => setDetail(null)}
                                    className="absolute top-4 right-4 w-8 h-8 rounded-lg bg-black/40 backdrop-blur-sm flex items-center justify-center text-white hover:bg-black/60 transition-colors"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="p-6 -mt-8 relative">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-xs font-mono font-bold text-gray-500">
                                        {String(detail.id).padStart(2, '0')}
                                    </span>
                                    <span
                                        className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-tighter border ${
                                            CONTINUITY_BADGE[detail.continuity].classes
                                        }`}
                                    >
                                        {CONTINUITY_BADGE[detail.continuity].label}
                                    </span>
                                </div>

                                <h2 className="text-2xl font-bold text-white mb-1">{detail.name}</h2>
                                <p className="text-gray-400 text-sm mb-6">{detail.descriptor}</p>

                                <div className="mb-6">
                                    <SectionHeading icon={Sparkles}>Prompt snippet</SectionHeading>
                                    <PromptBlock text={detail.snippet} />
                                </div>

                                <div className="mb-6">
                                    <SectionHeading>Best uses</SectionHeading>
                                    <div className="flex flex-wrap gap-2">
                                        {detail.bestUses.map(u => (
                                            <span
                                                key={u}
                                                className="px-2.5 py-1 rounded-lg text-xs font-medium bg-white/5 text-gray-300 border border-white/10"
                                            >
                                                {u}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                <button
                                    onClick={() => onToggle(detail.slug)}
                                    className={`w-full py-2.5 rounded-xl text-sm font-semibold transition-all ${
                                        selected.includes(detail.slug)
                                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                                            : 'bg-amber-600 text-white hover:bg-amber-700'
                                    }`}
                                >
                                    {selected.includes(detail.slug)
                                        ? 'Remove from selection'
                                        : 'Add to selection'}
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

/* ------------------------------------------------------------------ */
/* Structures tab — includes a live prompt builder                     */
/* ------------------------------------------------------------------ */

const StructuresTab: React.FC<{ styleSnippet: string }> = ({ styleSnippet }) => {
    const [fields, setFields] = useState({
        scene: '',
        subject: '',
        action: '',
        details: '',
        useCase: '',
        constraints: 'No watermark, no extra text, no logos.',
        continuityLocks: '',
    });
    const [useLocks, setUseLocks] = useState(false);

    const assembled = assemblePrompt({
        ...fields,
        style: styleSnippet,
        continuityLocks: useLocks ? fields.continuityLocks : undefined,
    });

    const set = (k: keyof typeof fields) => (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) =>
        setFields(f => ({ ...f, [k]: e.target.value }));

    return (
        <div className="space-y-8">
            {/* Structures */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                {PROMPT_STRUCTURES.map(s => (
                    <div key={s.slug} className="bg-white/5 border border-white/10 rounded-2xl p-5">
                        <h3 className="text-white font-semibold text-lg mb-2">{s.name}</h3>
                        <p className="text-gray-400 text-sm leading-relaxed mb-4">{s.summary}</p>

                        <SectionHeading>When to use</SectionHeading>
                        <ul className="space-y-1.5 mb-4">
                            {s.whenToUse.map((w, i) => (
                                <li key={i} className="flex gap-2 text-sm text-gray-300">
                                    <span className="text-amber-500 flex-none">·</span>
                                    {w}
                                </li>
                            ))}
                        </ul>

                        <PromptBlock text={s.template} maxHeight="280px" />

                        {s.notes && (
                            <div className="mt-3 flex gap-2 p-3 bg-amber-500/5 border border-amber-500/20 rounded-xl">
                                <Lightbulb className="w-3.5 h-3.5 text-amber-400 flex-none mt-0.5" />
                                <p className="text-xs text-gray-300 leading-relaxed">{s.notes}</p>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Builder */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                <h3 className="text-white font-semibold text-lg mb-1 flex items-center gap-2">
                    <Wand2 className="w-5 h-5 text-amber-400" />
                    Prompt builder
                </h3>
                <p className="text-gray-400 text-sm mb-6">
                    Fill the blocks and copy the assembled prompt. The Style block is filled from your selected
                    style tiles.
                </p>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="space-y-3">
                        {(
                            [
                                ['scene', 'Scene', 'Where this happens, time of day, environment'],
                                ['subject', 'Subject', 'Who or what is the main focus'],
                                ['action', 'Action', 'What is happening in this moment'],
                                ['details', 'Important details', 'Materials, lighting, camera angle, lens feel'],
                                ['useCase', 'Use case', 'Editorial photo / UI screen / concept frame'],
                                ['constraints', 'Constraints', 'No watermark, exact text only, preserve face'],
                            ] as const
                        ).map(([key, label, placeholder]) => (
                            <div key={key}>
                                <label className="block text-[11px] font-bold text-gray-500 uppercase tracking-widest mb-1.5">
                                    {label}
                                </label>
                                <textarea
                                    value={fields[key]}
                                    onChange={set(key)}
                                    rows={key === 'details' ? 3 : 2}
                                    placeholder={placeholder}
                                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-amber-500/50 resize-y"
                                />
                            </div>
                        ))}

                        <div>
                            <label className="flex items-center gap-2 mb-1.5 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={useLocks}
                                    onChange={e => setUseLocks(e.target.checked)}
                                    className="rounded border-white/20 bg-black/40 text-amber-500 focus:ring-amber-500/50"
                                />
                                <span className="text-[11px] font-bold text-gray-500 uppercase tracking-widest">
                                    Continuity locks (for video reference)
                                </span>
                            </label>
                            {useLocks && (
                                <textarea
                                    value={fields.continuityLocks}
                                    onChange={set('continuityLocks')}
                                    rows={3}
                                    placeholder="Preserve exact facial features, hair silhouette, outfit design, background geometry, lighting direction, camera height, lens feel, color palette"
                                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-amber-500/50 resize-y"
                                />
                            )}
                        </div>
                    </div>

                    {/* Live preview */}
                    <div>
                        <div className="flex items-center justify-between mb-1.5">
                            <label className="text-[11px] font-bold text-gray-500 uppercase tracking-widest">
                                Assembled prompt
                            </label>
                            {assembled && <CopyButton text={assembled} label="Copy prompt" />}
                        </div>
                        <pre className="text-gray-300 text-xs leading-relaxed bg-black/40 rounded-xl p-4 whitespace-pre-wrap border border-white/5 font-mono min-h-[400px] max-h-[600px] overflow-auto">
                            {assembled || (
                                <span className="text-gray-600">
                                    Fill in the blocks on the left to assemble a prompt…
                                </span>
                            )}
                        </pre>
                    </div>
                </div>
            </div>
        </div>
    );
};

/* ------------------------------------------------------------------ */
/* Categories tab                                                      */
/* ------------------------------------------------------------------ */

const CategoriesTab: React.FC = () => {
    const [active, setActive] = useState(PROMPT_CATEGORIES[0].slug);
    const category = PROMPT_CATEGORIES.find(c => c.slug === active)!;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Category rail */}
            <div className="lg:col-span-1">
                <div className="lg:sticky lg:top-8 space-y-1">
                    {PROMPT_CATEGORIES.map(c => (
                        <button
                            key={c.slug}
                            onClick={() => setActive(c.slug)}
                            className={`w-full text-left px-4 py-3 rounded-xl transition-all ${
                                active === c.slug
                                    ? 'bg-amber-600/20 text-white border border-amber-500/40'
                                    : 'text-gray-400 hover:bg-white/5 hover:text-white border border-transparent'
                            }`}
                        >
                            <span className="text-sm font-semibold leading-snug block">{c.name}</span>
                            <span className="text-[11px] text-gray-500">
                                {c.examples.length} prompt{c.examples.length === 1 ? '' : 's'}
                            </span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Content */}
            <div className="lg:col-span-3">
                <motion.div
                    key={category.slug}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-6"
                >
                    <div>
                        <h2 className="text-2xl font-bold text-white mb-2">{category.name}</h2>
                        <p className="text-gray-400 leading-relaxed">{category.summary}</p>
                    </div>

                    <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                        <SectionHeading icon={Lightbulb}>Guidance</SectionHeading>
                        <ul className="space-y-2">
                            {category.guidance.map((g, i) => (
                                <li key={i} className="flex gap-2.5 text-sm text-gray-300">
                                    <CheckCircle2 className="w-4 h-4 text-amber-500 flex-none mt-0.5" />
                                    {g}
                                </li>
                            ))}
                        </ul>
                    </div>

                    {category.template && (
                        <div>
                            <SectionHeading icon={Blocks}>Template</SectionHeading>
                            <PromptBlock text={category.template} />
                        </div>
                    )}

                    <div>
                        <SectionHeading icon={BookMarked}>
                            Copy-ready prompts ({category.examples.length})
                        </SectionHeading>
                        <div className="space-y-4">
                            {category.examples.map((ex, i) => (
                                <div key={i} className="bg-white/5 border border-white/10 rounded-2xl p-5">
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                            <h4 className="text-white font-semibold">{ex.title}</h4>
                                            {ex.continuityAnchor && (
                                                <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-tighter bg-green-500/15 text-green-400 border border-green-500/25 flex items-center gap-1">
                                                    <Film className="w-2.5 h-2.5" />
                                                    Video ref
                                                </span>
                                            )}
                                        </div>
                                        <CopyButton text={ex.prompt} />
                                    </div>
                                    <pre className="text-gray-300 text-xs leading-relaxed bg-black/40 rounded-xl p-4 whitespace-pre-wrap border border-white/5 font-mono">
                                        {ex.prompt}
                                    </pre>
                                </div>
                            ))}
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
};

/* ------------------------------------------------------------------ */
/* Models tab                                                          */
/* ------------------------------------------------------------------ */

const KIND_ICON: Record<ModelGuide['kind'], React.ElementType> = {
    image: ImageIcon,
    video: Film,
    audio: Music,
};

const ModelsTab: React.FC = () => {
    const [active, setActive] = useState(MODEL_GUIDES[0].slug);
    const model = MODEL_GUIDES.find(m => m.slug === active)!;
    const KindIcon = KIND_ICON[model.kind];

    return (
        <div>
            {/* Model selector */}
            <div className="flex flex-wrap gap-2 mb-6">
                {MODEL_GUIDES.map(m => {
                    const Icon = KIND_ICON[m.kind];
                    return (
                        <button
                            key={m.slug}
                            onClick={() => setActive(m.slug)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                                active === m.slug
                                    ? 'bg-amber-600 text-white'
                                    : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white border border-white/10'
                            }`}
                        >
                            <Icon className="w-4 h-4" />
                            {m.name}
                        </button>
                    );
                })}
            </div>

            <motion.div key={model.slug} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                {/* Header */}
                <div className="mb-6">
                    <div className="flex items-center gap-3 mb-2 flex-wrap">
                        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                            <KindIcon className="w-6 h-6 text-amber-400" />
                            {model.name}
                        </h2>
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-tighter bg-white/10 text-gray-400 border border-white/10">
                            {model.vendor}
                        </span>
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-tighter bg-white/10 text-gray-400 border border-white/10">
                            {model.kind}
                        </span>
                        {model.sourced ? (
                            <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-tighter bg-green-500/15 text-green-400 border border-green-500/25">
                                Sourced guidance
                            </span>
                        ) : (
                            <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-tighter bg-orange-500/15 text-orange-400 border border-orange-500/25">
                                General practice
                            </span>
                        )}
                    </div>
                    <p className="text-gray-400 leading-relaxed max-w-3xl">{model.summary}</p>
                </div>

                {!model.sourced && (
                    <div className="mb-6 p-4 bg-orange-500/5 border border-orange-500/20 rounded-2xl flex gap-3">
                        <AlertTriangle className="w-4 h-4 text-orange-400 flex-none mt-0.5" />
                        <p className="text-sm text-gray-300 leading-relaxed">
                            This guide is general prompting practice, not vendor-verified specification. Treat it as
                            a starting point and confirm parameter syntax against current vendor documentation.
                        </p>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Left column */}
                    <div className="space-y-6">
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                            <SectionHeading icon={Sparkles}>Strengths</SectionHeading>
                            <div className="flex flex-wrap gap-2">
                                {model.strengths.map(s => (
                                    <span
                                        key={s}
                                        className="px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-500/15 text-blue-300 border border-blue-500/20"
                                    >
                                        {s}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {model.settings && model.settings.length > 0 && (
                            <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                                <SectionHeading>Settings</SectionHeading>
                                <dl className="space-y-3">
                                    {model.settings.map(s => (
                                        <div key={s.label}>
                                            <dt className="text-xs font-semibold text-amber-400 mb-0.5">
                                                {s.label}
                                            </dt>
                                            <dd className="text-sm text-gray-300 leading-relaxed">{s.value}</dd>
                                        </div>
                                    ))}
                                </dl>
                            </div>
                        )}

                        <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                            <SectionHeading>Syntax &amp; structure</SectionHeading>
                            <dl className="space-y-3">
                                {model.syntax.map(s => (
                                    <div key={s.label}>
                                        <dt className="text-xs font-semibold text-amber-400 mb-0.5">{s.label}</dt>
                                        <dd className="text-sm text-gray-300 leading-relaxed">{s.detail}</dd>
                                    </div>
                                ))}
                            </dl>
                        </div>
                    </div>

                    {/* Right column */}
                    <div className="space-y-6">
                        <div className="bg-green-500/5 border border-green-500/20 rounded-2xl p-5">
                            <SectionHeading icon={CheckCircle2}>Do this</SectionHeading>
                            <ul className="space-y-2">
                                {model.doThis.map((d, i) => (
                                    <li key={i} className="flex gap-2.5 text-sm text-gray-300">
                                        <span className="text-green-500 flex-none">+</span>
                                        {d}
                                    </li>
                                ))}
                            </ul>
                        </div>

                        <div className="bg-red-500/5 border border-red-500/20 rounded-2xl p-5">
                            <SectionHeading icon={AlertTriangle}>Avoid this</SectionHeading>
                            <ul className="space-y-2">
                                {model.avoidThis.map((a, i) => (
                                    <li key={i} className="flex gap-2.5 text-sm text-gray-300">
                                        <span className="text-red-500 flex-none">−</span>
                                        {a}
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {model.examples.length > 0 && (
                            <div>
                                <SectionHeading icon={BookMarked}>Examples</SectionHeading>
                                <div className="space-y-3">
                                    {model.examples.map((ex, i) => (
                                        <div key={i} className="bg-white/5 border border-white/10 rounded-2xl p-4">
                                            <div className="flex items-center justify-between mb-2">
                                                <h4 className="text-white text-sm font-semibold">{ex.title}</h4>
                                                <CopyButton text={ex.prompt} />
                                            </div>
                                            <pre className="text-gray-300 text-xs leading-relaxed bg-black/40 rounded-xl p-3 whitespace-pre-wrap border border-white/5 font-mono max-h-64 overflow-auto">
                                                {ex.prompt}
                                            </pre>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </motion.div>
        </div>
    );
};

/* ------------------------------------------------------------------ */
/* Video references tab                                                */
/* ------------------------------------------------------------------ */

const VideoTab: React.FC = () => (
    <div className="space-y-8">
        <div className="p-5 bg-amber-500/5 border border-amber-500/20 rounded-2xl flex gap-3">
            <Film className="w-5 h-5 text-amber-400 flex-none mt-0.5" />
            <div>
                <h3 className="text-white font-semibold mb-1">Stills as production references</h3>
                <p className="text-sm text-gray-300 leading-relaxed">
                    When an image will later be animated, treat it as a production reference rather than standalone
                    artwork. The goal is not only visual quality but continuity: stable identity, costume,
                    proportions, camera logic and environment detail across every frame.
                </p>
            </div>
        </div>

        {/* Packs */}
        <div>
            <SectionHeading icon={Layers}>Recommended reference packs</SectionHeading>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {REFERENCE_PACKS.map(p => (
                    <div key={p.slug} className="bg-white/5 border border-white/10 rounded-2xl p-5">
                        <h4 className="text-white font-semibold mb-3">{p.name}</h4>
                        <ul className="space-y-1.5 mb-4">
                            {p.contents.map((c, i) => (
                                <li key={i} className="flex gap-2 text-sm text-gray-300">
                                    <span className="text-amber-500 flex-none">·</span>
                                    {c}
                                </li>
                            ))}
                        </ul>
                        <p className="text-xs text-gray-500 leading-relaxed border-t border-white/5 pt-3">
                            {p.why}
                        </p>
                    </div>
                ))}
            </div>
        </div>

        {/* Rules */}
        <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
            <SectionHeading icon={CheckCircle2}>Reference-image prompt rules</SectionHeading>
            <ol className="space-y-2.5">
                {REFERENCE_RULES.map((r, i) => (
                    <li key={i} className="flex gap-3 text-sm text-gray-300">
                        <span className="flex-none w-5 h-5 rounded-full bg-amber-500/20 flex items-center justify-center text-[10px] font-bold text-amber-400 mt-0.5">
                            {i + 1}
                        </span>
                        {r}
                    </li>
                ))}
            </ol>
        </div>

        {/* Example */}
        <div>
            <SectionHeading icon={BookMarked}>Example reference prompt</SectionHeading>
            <PromptBlock text={REFERENCE_EXAMPLE} />
        </div>
    </div>
);

/* ------------------------------------------------------------------ */
/* Tips tab                                                            */
/* ------------------------------------------------------------------ */

const TipsTab: React.FC = () => (
    <div className="space-y-6 max-w-4xl">
        <div className="p-5 bg-white/5 border border-white/10 rounded-2xl">
            <h3 className="text-white font-semibold mb-2">Core premise</h3>
            <p className="text-gray-300 leading-relaxed">{CORE_PREMISE}</p>
        </div>

        <div className="p-5 bg-orange-500/5 border border-orange-500/20 rounded-2xl flex gap-3">
            <AlertTriangle className="w-5 h-5 text-orange-400 flex-none mt-0.5" />
            <div>
                <h3 className="text-white font-semibold mb-1">The anti-slop rule</h3>
                <p className="text-gray-300 leading-relaxed">{ANTI_SLOP_NOTE}</p>
            </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {TIP_GROUPS.map(g => (
                <div
                    key={g.kind}
                    className={`rounded-2xl p-5 border ${
                        g.kind === 'do'
                            ? 'bg-green-500/5 border-green-500/20'
                            : 'bg-red-500/5 border-red-500/20'
                    }`}
                >
                    <h3
                        className={`font-semibold mb-4 flex items-center gap-2 ${
                            g.kind === 'do' ? 'text-green-400' : 'text-red-400'
                        }`}
                    >
                        {g.kind === 'do' ? (
                            <CheckCircle2 className="w-4 h-4" />
                        ) : (
                            <AlertTriangle className="w-4 h-4" />
                        )}
                        {g.title}
                    </h3>
                    <ul className="space-y-2.5">
                        {g.items.map((item, i) => (
                            <li key={i} className="flex gap-2.5 text-sm text-gray-300 leading-relaxed">
                                <span
                                    className={`flex-none ${
                                        g.kind === 'do' ? 'text-green-500' : 'text-red-500'
                                    }`}
                                >
                                    {g.kind === 'do' ? '+' : '−'}
                                </span>
                                {item}
                            </li>
                        ))}
                    </ul>
                </div>
            ))}
        </div>
    </div>
);

/* ------------------------------------------------------------------ */
/* Page                                                                */
/* ------------------------------------------------------------------ */

const PromptLibrary: React.FC = () => {
    const [tab, setTab] = useState<TabKey>('styles');
    const [selectedStyles, setSelectedStyles] = useState<string[]>([]);

    const toggleStyle = (slug: string) =>
        setSelectedStyles(prev =>
            prev.includes(slug) ? prev.filter(s => s !== slug) : [...prev, slug],
        );

    const styleSnippet = useMemo(
        () =>
            STYLE_TILES.filter(t => selectedStyles.includes(t.slug))
                .map(t => t.snippet)
                .join(', '),
        [selectedStyles],
    );

    return (
        <div className="p-8 max-w-[1600px] mx-auto">
            {/* Header */}
            <header className="mb-6">
                <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
                        <BookMarked className="w-6 h-6 text-amber-400" />
                    </div>
                    Prompt Guide Library
                </h1>
                <p className="text-gray-400 mt-2 max-w-2xl">
                    Universal prompt structures, selectable style tiles, category prompt sets and per-model
                    guidance. Curated reference — the stable counterpart to auto-generated Production Skills.
                </p>
            </header>

            {/* Selected styles tray */}
            <AnimatePresence>
                {selectedStyles.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="overflow-hidden mb-6"
                    >
                        <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-2xl">
                            <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                                <span className="text-xs font-bold text-amber-300 uppercase tracking-widest flex items-center gap-2">
                                    <Sparkles className="w-3.5 h-3.5" />
                                    Selected styles ({selectedStyles.length})
                                </span>
                                <div className="flex items-center gap-2">
                                    <CopyButton text={styleSnippet} label="Copy combined snippet" />
                                    <button
                                        onClick={() => setSelectedStyles([])}
                                        className="text-xs text-gray-400 hover:text-white transition-colors flex items-center gap-1"
                                    >
                                        <X className="w-3 h-3" />
                                        Clear
                                    </button>
                                </div>
                            </div>

                            <div className="flex flex-wrap gap-2 mb-3">
                                {selectedStyles.map(slug => {
                                    const tile = STYLE_TILES.find(t => t.slug === slug)!;
                                    return (
                                        <button
                                            key={slug}
                                            onClick={() => toggleStyle(slug)}
                                            className="group flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-white/10 text-white border border-white/15 hover:border-red-500/40 transition-colors"
                                        >
                                            {tile.name}
                                            <X className="w-3 h-3 text-gray-500 group-hover:text-red-400" />
                                        </button>
                                    );
                                })}
                            </div>

                            <pre className="text-amber-200/80 text-xs leading-relaxed bg-black/30 rounded-lg p-3 whitespace-pre-wrap font-mono">
                                {styleSnippet}
                            </pre>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Tabs */}
            <div className="flex gap-1 mb-8 p-1 bg-white/5 border border-white/10 rounded-2xl overflow-x-auto">
                {TABS.map(t => {
                    const Icon = t.icon;
                    return (
                        <button
                            key={t.key}
                            onClick={() => setTab(t.key)}
                            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold whitespace-nowrap transition-all ${
                                tab === t.key
                                    ? 'bg-amber-600 text-white shadow-lg shadow-amber-600/20'
                                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`}
                        >
                            <Icon className="w-4 h-4" />
                            {t.label}
                        </button>
                    );
                })}
            </div>

            {/* Content */}
            <AnimatePresence mode="wait">
                <motion.div
                    key={tab}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.15 }}
                >
                    {tab === 'styles' && (
                        <StyleTilesTab selected={selectedStyles} onToggle={toggleStyle} />
                    )}
                    {tab === 'structures' && <StructuresTab styleSnippet={styleSnippet} />}
                    {tab === 'categories' && <CategoriesTab />}
                    {tab === 'models' && <ModelsTab />}
                    {tab === 'video' && <VideoTab />}
                    {tab === 'tips' && <TipsTab />}
                </motion.div>
            </AnimatePresence>
        </div>
    );
};

export default PromptLibrary;
