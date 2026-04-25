import React, { useState, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ClipboardCheck,
    Loader2,
    Video,
    Music,
    Palette,
    Sparkles,
    AlertCircle,
    Layout,
    CheckCircle2,
    Clock,
    Film,
    Zap,
    ChevronDown,
    ChevronUp,
} from 'lucide-react';
import { curationService } from '../services/curation';
import type { BriefScene, CreativeBrief } from '../services/curation';

const Curation: React.FC = () => {
    const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
    const [isApproving, setIsApproving] = useState(false);
    const queryClient = useQueryClient();

    const { data: jobs, isLoading } = useQuery({
        queryKey: ['curationJobs'],
        queryFn: curationService.listJobs,
        refetchInterval: (query) => {
            const hasRunningJobs = query.state.data?.some(
                (j) => j.status === 'pending' || j.status === 'briefing'
            );
            return hasRunningJobs ? 3000 : false;
        },
    });

    const selectedJob = jobs?.find((j) => j.id === selectedJobId);

    const handleApprove = useCallback(async () => {
        if (!selectedJob) return;
        setIsApproving(true);
        try {
            await curationService.approveBrief(selectedJob.id);
            queryClient.invalidateQueries({ queryKey: ['curationJobs'] });
        } catch (err) {
            console.error('Failed to approve brief:', err);
        } finally {
            setIsApproving(false);
        }
    }, [selectedJob, queryClient]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            </div>
        );
    }

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-2">
                        <ClipboardCheck className="text-blue-400" />
                        Curation Board
                    </h1>
                    <p className="text-gray-400 mt-1">
                        Review, edit, and approve your AI-generated creative briefs.
                    </p>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Jobs List */}
                <div className="lg:col-span-1 space-y-4">
                    <h2 className="text-xl font-semibold text-white flex items-center gap-2 mb-4">
                        <Layout className="w-5 h-5 text-gray-400" />
                        Recent Projects
                    </h2>
                    <div className="space-y-3">
                        {jobs?.map((job) => (
                            <motion.div
                                key={job.id}
                                whileHover={{ scale: 1.02 }}
                                onClick={() => setSelectedJobId(job.id)}
                                className={`p-4 rounded-xl cursor-pointer border transition-all ${
                                    selectedJobId === job.id
                                        ? 'bg-blue-600/20 border-blue-500 shadow-lg shadow-blue-500/10'
                                        : 'bg-white/5 border-white/10 hover:bg-white/10'
                                }`}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">
                                        JOB-{job.id.slice(0, 8)}
                                    </span>
                                    <StatusBadge status={job.status} />
                                </div>
                                <h3 className="text-gray-200 font-medium truncate">
                                    {job.creative_brief?.theme || 'Initializing Brief...'}
                                </h3>
                                <div className="mt-3 flex items-center gap-4 text-xs text-gray-400">
                                    <span className="flex items-center gap-1">
                                        <Sparkles className="w-3 h-3" />
                                        {job.num_scenes || 0} Scenes
                                    </span>
                                    <span className="flex items-center gap-1">
                                        <Film className="w-3 h-3" />
                                        {job.creative_brief?.genre || '—'}
                                    </span>
                                </div>
                            </motion.div>
                        ))}
                        {jobs?.length === 0 && (
                            <div className="text-center py-12 bg-white/5 rounded-xl border border-dashed border-white/10">
                                <p className="text-gray-500">No curation jobs yet.</p>
                                <p className="text-gray-600 text-xs mt-1">
                                    Start from the Research page to create one.
                                </p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Job Detail */}
                <div className="lg:col-span-2">
                    <AnimatePresence mode="wait">
                        {selectedJob ? (
                            <motion.div
                                key={selectedJob.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="bg-white/5 rounded-2xl border border-white/10 overflow-hidden"
                            >
                                {selectedJob.status === 'ready' && selectedJob.creative_brief ? (
                                    <>
                                        <BriefDetail brief={selectedJob.creative_brief} />
                                        <div className="p-8 border-t border-white/10 bg-emerald-600/5 flex justify-between items-center">
                                            <div className="text-sm text-gray-400">
                                                <CheckCircle2 className="w-4 h-4 text-emerald-400 inline mr-1" />
                                                Brief is ready for your approval
                                            </div>
                                            <button
                                                onClick={handleApprove}
                                                disabled={isApproving}
                                                className="px-8 py-4 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-800 disabled:cursor-wait text-white font-bold rounded-2xl shadow-xl shadow-emerald-600/20 flex items-center gap-2 transition-all transform hover:scale-105 active:scale-95"
                                            >
                                                {isApproving ? (
                                                    <Loader2 className="w-5 h-5 animate-spin" />
                                                ) : (
                                                    <CheckCircle2 className="w-5 h-5" />
                                                )}
                                                Approve & Lock Brief
                                            </button>
                                        </div>
                                    </>
                                ) : selectedJob.status === 'approved' && selectedJob.user_approved_brief ? (
                                    <>
                                        <BriefDetail brief={selectedJob.user_approved_brief} readOnly />
                                        <div className="p-8 border-t border-white/10 bg-blue-600/10 flex justify-between items-center">
                                            <div className="text-sm text-emerald-400 flex items-center gap-2">
                                                <CheckCircle2 className="w-4 h-4" />
                                                Approved{' '}
                                                {selectedJob.approved_at &&
                                                    `on ${new Date(selectedJob.approved_at).toLocaleString()}`}
                                            </div>
                                            <button
                                                onClick={() => (window.location.href = '/production')}
                                                className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl shadow-xl shadow-blue-600/20 flex items-center gap-2 transition-all transform hover:scale-105 active:scale-95"
                                            >
                                                <Zap className="w-5 h-5" />
                                                Start Production
                                            </button>
                                        </div>
                                    </>
                                ) : selectedJob.status === 'failed' ? (
                                    <div className="p-20 flex flex-col items-center justify-center text-center">
                                        <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
                                        <h3 className="text-xl font-semibold text-white">
                                            Generation Failed
                                        </h3>
                                        <p className="text-gray-400 mt-2 max-w-md">
                                            {selectedJob.error_message || 'Unknown error occurred.'}
                                        </p>
                                    </div>
                                ) : (
                                    <div className="p-20 flex flex-col items-center justify-center text-center">
                                        <Loader2 className="w-12 h-12 animate-spin text-blue-500 mb-4" />
                                        <h3 className="text-xl font-semibold text-white">
                                            Generating Creative Brief
                                        </h3>
                                        <p className="text-gray-400 mt-2">
                                            Claude is analyzing thumbnails and crafting your storyboard...
                                        </p>
                                        <p className="text-gray-500 text-xs mt-4">
                                            This usually takes 30-60 seconds.
                                        </p>
                                    </div>
                                )}
                            </motion.div>
                        ) : (
                            <div className="h-full flex items-center justify-center border-2 border-dashed border-white/10 rounded-2xl p-12 text-center">
                                <div>
                                    <Sparkles className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                                    <h3 className="text-gray-400 text-lg">
                                        Select a project to view the Creative Brief
                                    </h3>
                                </div>
                            </div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

// ---------------------------------------------------------------------------
// StatusBadge — updated for guide status values
// ---------------------------------------------------------------------------

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
    const colors: Record<string, string> = {
        ready: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
        approved: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
        pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
        briefing: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        failed: 'bg-red-500/20 text-red-400 border-red-500/30',
    };

    return (
        <span
            className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-tighter border ${colors[status] || colors.pending}`}
        >
            {status.replace('_', ' ')}
        </span>
    );
};

// ---------------------------------------------------------------------------
// BriefDetail — renders the Creative Brief (guide §3.3 schema)
// ---------------------------------------------------------------------------

interface BriefDetailProps {
    brief: CreativeBrief;
    readOnly?: boolean;
}

const BriefDetail: React.FC<BriefDetailProps> = ({ brief, readOnly = false }) => {
    const [expandedScene, setExpandedScene] = useState<number | null>(null);

    const totalDuration = brief.scenes?.reduce((sum, s) => sum + (s.target_duration_sec || 0), 0) || 0;
    const imageTailCount = brief.scenes?.filter((s) => s.image_tail_scene !== null).length || 0;

    return (
        <div className="divide-y divide-white/10">
            {/* Header */}
            <div className="p-8 bg-gradient-to-br from-blue-600/10 to-cyan-600/10">
                <div className="flex items-start justify-between mb-4">
                    <div>
                        <h2 className="text-2xl font-bold text-white mb-2">{brief.theme}</h2>
                        <p className="text-gray-300 text-sm">{brief.mood} · {brief.genre}</p>
                    </div>
                    {readOnly && (
                        <span className="flex items-center gap-1 px-3 py-1 bg-emerald-500/20 text-emerald-400 rounded-full text-xs font-bold border border-emerald-500/30">
                            <CheckCircle2 className="w-3 h-3" /> Locked
                        </span>
                    )}
                </div>
                <div className="flex flex-wrap gap-4 mt-4">
                    <StatChip
                        icon={<Film className="w-3 h-3" />}
                        label="Scenes"
                        value={String(brief.total_scenes || brief.scenes?.length || 0)}
                    />
                    <StatChip
                        icon={<Clock className="w-3 h-3" />}
                        label="Total Duration"
                        value={`${totalDuration.toFixed(1)}s`}
                    />
                    <StatChip
                        icon={<Zap className="w-3 h-3" />}
                        label="Image Tails"
                        value={String(imageTailCount)}
                    />
                    <StatChip
                        icon={<Music className="w-3 h-3" />}
                        label="Audio Hint"
                        value={`${brief.audio_duration_hint_sec || 0}s`}
                    />
                </div>
            </div>

            {/* Palette & Music Direction */}
            <div className="p-8 bg-white/5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                        <h4 className="text-sm font-medium text-gray-400 uppercase tracking-widest flex items-center gap-2">
                            <Palette className="w-4 h-4 text-pink-400" />
                            Color Palette
                        </h4>
                        <div className="flex gap-2 flex-wrap">
                            {brief.palette?.map((color, idx) => (
                                <div
                                    key={idx}
                                    className="flex items-center gap-2 bg-white/5 px-3 py-2 rounded-lg border border-white/10"
                                >
                                    <div
                                        className="w-4 h-4 rounded-full border border-white/20"
                                        style={{ backgroundColor: color }}
                                    />
                                    <span className="text-xs text-gray-300 font-mono">{color}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="space-y-4">
                        <h4 className="text-sm font-medium text-gray-400 uppercase tracking-widest flex items-center gap-2">
                            <Music className="w-4 h-4 text-blue-400" />
                            Music Direction
                        </h4>
                        {brief.suno_music_direction && (
                            <div className="bg-white/5 p-4 rounded-xl border border-white/10 space-y-2">
                                <div className="flex gap-4 text-xs text-gray-300">
                                    <span>Genre: <strong>{brief.suno_music_direction.genre}</strong></span>
                                    <span>BPM: <strong>{brief.suno_music_direction.bpm_hint}</strong></span>
                                </div>
                                <div className="flex flex-wrap gap-1">
                                    {brief.suno_music_direction.style_tags?.map((tag, i) => (
                                        <span
                                            key={i}
                                            className="px-2 py-0.5 text-[10px] bg-blue-500/10 text-blue-300 rounded-full border border-blue-500/20"
                                        >
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Scenes */}
            <div className="p-8">
                <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                    <Video className="w-5 h-5 text-orange-400" />
                    Storyboard ({brief.scenes?.length || 0} scenes)
                </h3>
                <div className="space-y-3">
                    {brief.scenes?.map((scene) => (
                        <SceneCard
                            key={scene.scene_number}
                            scene={scene}
                            expanded={expandedScene === scene.scene_number}
                            onToggle={() =>
                                setExpandedScene(
                                    expandedScene === scene.scene_number ? null : scene.scene_number
                                )
                            }
                        />
                    ))}
                </div>
            </div>
        </div>
    );
};

// ---------------------------------------------------------------------------
// SceneCard — individual scene display
// ---------------------------------------------------------------------------

const SceneCard: React.FC<{
    scene: BriefScene;
    expanded: boolean;
    onToggle: () => void;
}> = ({ scene, expanded, onToggle }) => {
    return (
        <motion.div
            layout
            className="bg-white/5 border border-white/10 rounded-xl overflow-hidden hover:border-white/20 transition-colors"
        >
            {/* Header - always visible */}
            <div
                className="flex items-center gap-4 p-4 cursor-pointer"
                onClick={onToggle}
            >
                <div className="flex-none w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 font-bold text-sm border border-blue-500/20">
                    {scene.scene_number}
                </div>
                <div className="flex-1 min-w-0">
                    <p className="text-gray-200 text-sm truncate">{scene.description}</p>
                    <div className="flex gap-3 mt-1 text-[11px] text-gray-500">
                        <span>{scene.target_duration_sec}s</span>
                        <span>{scene.kling_mode.toUpperCase()}</span>
                        {scene.image_tail_scene && (
                            <span className="text-cyan-400">→ tail from #{scene.image_tail_scene}</span>
                        )}
                        <span className="text-gray-600">{scene.animation_method}</span>
                    </div>
                </div>
                {expanded ? (
                    <ChevronUp className="w-4 h-4 text-gray-500 flex-none" />
                ) : (
                    <ChevronDown className="w-4 h-4 text-gray-500 flex-none" />
                )}
            </div>

            {/* Expanded detail */}
            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="border-t border-white/5"
                    >
                        <div className="p-4 space-y-3 text-sm">
                            <DetailRow label="Motion Prompt" value={scene.motion_prompt} />
                            <DetailRow label="Negative Prompt" value={scene.negative_prompt} />
                            {scene.lyric_or_timestamp && (
                                <DetailRow label="Lyric / Timestamp" value={scene.lyric_or_timestamp} />
                            )}
                            {scene.transition_note && (
                                <DetailRow label="Transition Note" value={scene.transition_note} />
                            )}
                            <div className="flex gap-4 text-xs text-gray-500 pt-2 border-t border-white/5">
                                <span>Model: {scene.kling_model}</span>
                                <span>Mode: {scene.kling_mode}</span>
                                <span>Duration: {scene.target_duration_sec}s</span>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

// ---------------------------------------------------------------------------
// Small utility components
// ---------------------------------------------------------------------------

const StatChip: React.FC<{ icon: React.ReactNode; label: string; value: string }> = ({
    icon,
    label,
    value,
}) => (
    <div className="bg-black/20 px-4 py-2 rounded-xl border border-white/5 flex items-center gap-2">
        <span className="text-gray-500">{icon}</span>
        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">{label}</span>
        <span className="text-gray-200 font-semibold text-sm">{value}</span>
    </div>
);

const DetailRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
    <div>
        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block mb-1">
            {label}
        </span>
        <p className="text-gray-300 bg-black/20 p-3 rounded-lg border border-white/5 text-xs leading-relaxed">
            {value}
        </p>
    </div>
);

export default Curation;
