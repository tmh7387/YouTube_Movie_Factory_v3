import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
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
    Trash2,
    Youtube,
    ExternalLink,
    CheckCircle2,
    Zap,
    Film,
    Clock,
    ChevronUp,
    ChevronDown,
} from 'lucide-react';
import { curationService, youtubeUrl, youtubeThumbnail } from '../services/curation';
import type { CreativeBrief, BriefScene } from '../services/curation';

const Curation: React.FC = () => {
    const navigate = useNavigate();
    const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
    const [hoveredJobId, setHoveredJobId] = useState<string | null>(null);
    const queryClient = useQueryClient();

    const { data: jobs, isLoading } = useQuery({
        queryKey: ['curationJobs'],
        queryFn: curationService.listJobs,
        refetchInterval: (query) => {
            const hasRunningJobs = query.state.data?.some(j => j.status === 'pending' || j.status === 'generating_brief');
            return hasRunningJobs ? 3000 : false;
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (jobId: string) => curationService.deleteJob(jobId),
        onSuccess: (_, deletedId) => {
            queryClient.invalidateQueries({ queryKey: ['curationJobs'] });
            if (selectedJobId === deletedId) setSelectedJobId(null);
        },
    });

    // Stage 2 -> Stage 3 approval gate (endpoints from Stage-2 schema alignment)
    const approveMutation = useMutation({
        mutationFn: (jobId: string) => curationService.approveBrief(jobId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['curationJobs'] });
        },
    });

    const canApprove = (status?: string) =>
        status === 'ready' || status === 'completed';

    const handleDelete = (e: React.MouseEvent, jobId: string) => {
        e.stopPropagation();
        if (window.confirm('Remove this curation job? This cannot be undone.')) {
            deleteMutation.mutate(jobId);
        }
    };

    const selectedJob = jobs?.find(j => j.id === selectedJobId);



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
                                onHoverStart={() => setHoveredJobId(job.id)}
                                onHoverEnd={() => setHoveredJobId(null)}
                                className={`p-4 rounded-xl cursor-pointer border transition-all relative ${selectedJobId === job.id
                                    ? 'bg-blue-600/20 border-blue-500 shadow-lg shadow-blue-500/10'
                                    : 'bg-white/5 border-white/10 hover:bg-white/10'
                                    }`}
                            >
                                {/* Delete button — uses React hover state (framer-motion blocks CSS group-hover) */}
                                <button
                                    onClick={(e) => handleDelete(e, job.id)}
                                    disabled={deleteMutation.isPending && deleteMutation.variables === job.id}
                                    className={`absolute top-3 right-3 p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-all z-10 ${
                                        hoveredJobId === job.id ? 'opacity-100' : 'opacity-0'
                                    }`}
                                    title="Remove this curation"
                                >
                                    {deleteMutation.isPending && deleteMutation.variables === job.id
                                        ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                        : <Trash2 className="w-3.5 h-3.5" />
                                    }
                                </button>

                                <div className="flex justify-between items-start mb-2 pr-6">
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
                                    {job.selected_video_ids?.length ? (
                                        <span className="flex items-center gap-1">
                                            <Youtube className="w-3 h-3 text-red-500" />
                                            {job.selected_video_ids.length} Source{job.selected_video_ids.length !== 1 ? 's' : ''}
                                        </span>
                                    ) : null}
                                    <span>{job.created_at ? new Date(job.created_at).toLocaleDateString() : '—'}</span>
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
                                {canApprove(selectedJob.status) && selectedJob.creative_brief ? (
                                    <>
                                        <BriefDetail brief={selectedJob.creative_brief} sourceVideoIds={selectedJob.selected_video_ids} />
                                        <div className="p-8 border-t border-white/10 bg-blue-600/10 flex justify-end">
                                            <button
                                                onClick={() => approveMutation.mutate(selectedJob.id)}
                                                disabled={approveMutation.isPending}
                                                className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl shadow-xl shadow-blue-600/20 flex items-center gap-2 transition-all transform hover:scale-105 active:scale-95"
                                            >
                                                {approveMutation.isPending ? (
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
                                                onClick={() => navigate('/production', { state: { curationJobId: selectedJob.id } })}
                                                className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-2xl shadow-xl shadow-blue-600/20 flex items-center gap-2 transition-all transform hover:scale-105 active:scale-95"
                                            >
                                                <Zap className="w-5 h-5" />
                                                Start Production
                                            </button>
                                        </div>
                                    </>
                                ) : (
                                    <div className="p-20 flex flex-col items-center justify-center text-center">
                                        {selectedJob.status === 'error' || selectedJob.status === 'failed' ? (
                                            <>
                                                <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
                                                <h3 className="text-xl font-semibold text-white">Generation Failed</h3>
                                                <p className="text-gray-400 mt-2">{selectedJob.error_message || selectedJob.creative_brief?.error || 'Unknown error occurred.'}</p>
                                                <button
                                                    onClick={(e) => handleDelete(e as any, selectedJob.id)}
                                                    className="mt-6 flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg text-sm transition-colors"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                    Remove this job
                                                </button>
                                            </>
                                        ) : (
                                            <>
                                                <Loader2 className="w-12 h-12 animate-spin text-blue-500 mb-4" />
                                                <h3 className="text-xl font-semibold text-white">Generating Creative Brief</h3>
                                                <p className="text-gray-400 mt-2">Claude is busy synthesizing your storyboard and narrative...</p>
                                            </>
                                        )}
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
        generating_brief: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        error: 'bg-red-500/20 text-red-400 border-red-500/30',
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

const BriefDetail: React.FC<{
    brief: CreativeBrief;
    sourceVideoIds?: string[] | null;
    readOnly?: boolean;
}> = ({ brief, sourceVideoIds, readOnly = false }) => {
    const briefScenes = brief.scenes ?? brief.storyboard ?? [];
    const totalDuration = briefScenes.reduce(
        (sum, sc) => sum + Number(sc.target_duration_sec ?? sc.duration ?? 0),
        0,
    );
    const imageTailCount = briefScenes.filter(
        (sc) => sc.image_tail_scene !== null && sc.image_tail_scene !== undefined,
    ).length;
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
                        value={String(brief.total_scenes || briefScenes.length)}
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

            {/* Source Videos */}
            {sourceVideoIds && sourceVideoIds.length > 0 && (
                <div className="p-8 bg-black/20">
                    <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                        <Youtube className="w-4 h-4 text-red-500" />
                        Source Videos
                    </h3>
                    <div className="flex flex-wrap gap-3">
                        {sourceVideoIds.map((vid) => (
                            <a
                                key={vid}
                                href={youtubeUrl(vid)}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="group flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-red-500/40 rounded-xl overflow-hidden transition-all pr-3"
                            >
                                <div className="w-16 h-12 shrink-0 relative overflow-hidden">
                                    <img
                                        src={youtubeThumbnail(vid)}
                                        alt={vid}
                                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                                        onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                                    />
                                    <div className="absolute inset-0 bg-black/30 group-hover:bg-black/10 transition-colors" />
                                </div>
                                <span className="text-xs font-mono text-gray-400 group-hover:text-white transition-colors">{vid}</span>
                                <ExternalLink className="w-3 h-3 text-gray-600 group-hover:text-red-400 transition-colors ml-1 shrink-0" />
                            </a>
                        ))}
                    </div>
                </div>
            )}

            <div className="p-8 bg-white/5">
                <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                    <Palette className="w-5 h-5 text-pink-400" />
                    Style &amp; Direction
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                        <h4 className="text-sm font-medium text-gray-400 uppercase tracking-widest">Audible Mood</h4>
                        <div className="flex items-center gap-3 bg-white/5 p-4 rounded-xl border border-white/10">
                            <Music className="text-blue-400" />
                            <span className="text-gray-200">{brief.music_mood ?? brief.mood}</span>
                        </div>
                    </div>
                    <div className="space-y-4">
                        <h4 className="text-sm font-medium text-gray-400 uppercase tracking-widest">Visual Palette</h4>
                        <div className="flex gap-2 flex-wrap">
                            {(brief.color_palette ?? brief.palette ?? []).map((color, idx) => (
                                <div key={idx} className="flex items-center gap-2 bg-white/5 px-3 py-2 rounded-lg border border-white/10">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color.toLowerCase().includes('#') ? color : '#3b82f6' }} />
                                    <span className="text-xs text-gray-300">{color}</span>
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
                                    {brief.suno_music_direction?.style_tags?.map((tag: string, i: number) => (
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
                    Storyboard ({briefScenes.length} scenes)
                </h3>
                <div className="space-y-6">
                    {briefScenes.map((scene, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.1 }}
                            className="flex gap-6 group"
                        >
                            <div className="flex-none w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 font-bold border border-blue-500/20">
                                {(scene.scene_index ?? scene.scene_number ?? idx + 1)}
                            </div>
                            <div className="flex-1 bg-white/5 border border-white/10 rounded-2xl p-6 group-hover:border-white/20 transition-colors">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-tighter block mb-2">Narration</span>
                                        <p className="text-gray-200 italic leading-relaxed">"{scene.narration ?? scene.description}"</p>
                                    </div>
                                    <div>
                                        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-tighter block mb-2">Visual Prompt</span>
                                        <p className="text-sm text-gray-300 leading-relaxed bg-black/30 p-3 rounded-lg border border-white/5 line-clamp-3 hover:line-clamp-none transition-all cursor-zoom-in">
                                            {scene.visual_prompt}
                                        </p>
                                    </div>
                                </div>
                                <div className="mt-4 pt-4 border-t border-white/5 flex gap-4 text-xs text-gray-500 font-medium">
                                    <span>Duration: {scene.duration ?? '—'}s</span>
                                    <span>Pacing: {scene.pacing ?? '—'}</span>
                                    {scene.kling_mode && <span>Mode: {scene.kling_mode}</span>}
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
};

// ---------------------------------------------------------------------------
// SceneCard — individual scene display
// ---------------------------------------------------------------------------

export const SceneCard: React.FC<{
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
                        <span>{(scene.kling_mode ?? 'std').toUpperCase()}</span>
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
                            <DetailRow label="Motion Prompt" value={scene.motion_prompt ?? ''} />
                            <DetailRow label="Negative Prompt" value={scene.negative_prompt ?? ''} />
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
