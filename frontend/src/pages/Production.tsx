import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Film, Sparkles, Music, Image as ImageIcon, CheckCircle2,
    AlertCircle, RefreshCcw, Download, ChevronRight, Layers,
    Play, Zap, Upload, X, FileAudio, ToggleLeft, ToggleRight, Terminal
} from 'lucide-react';
import {
    productionService, type ProductionJob, type ProductionScene, type ProductionTrack,
    type ProductionJobDetail, PIPELINE_PHASES, sceneProgress, formatFileSize
} from '../services/production';
import { curationService, type CurationJob } from '../services/curation';

// ---------------------------------------------------------------------------
// Status colours
// ---------------------------------------------------------------------------
const STATUS_COLORS: Record<string, string> = {
    completed: 'text-green-400 bg-green-500/10 border-green-500/30',
    failed: 'text-red-400 bg-red-500/10 border-red-500/30',
    assembly_failed: 'text-red-400 bg-red-500/10 border-red-500/30',
    animating: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
    generating_images: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
    generating_music: 'text-pink-400 bg-pink-500/10 border-pink-500/30',
    assembling: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
    queued: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
    initializing: 'text-slate-400 bg-slate-500/10 border-slate-500/30',
    pending: 'text-slate-400 bg-slate-500/10 border-slate-500/30',
};
const statusColor = (s: string) => STATUS_COLORS[s] ?? STATUS_COLORS.pending;

const RUNNING = ['queued', 'initializing', 'generating_images', 'animating', 'generating_music', 'assembling'];
const isRunning = (s: string) => RUNNING.includes(s);

// ---------------------------------------------------------------------------
// Phase tracker
// ---------------------------------------------------------------------------
const PHASES = [
    { key: 'initializing',      label: 'Init',    icon: <Layers className="w-3.5 h-3.5" /> },
    { key: 'generating_images', label: 'Images',  icon: <ImageIcon className="w-3.5 h-3.5" /> },
    { key: 'animating',         label: 'Animate', icon: <Film className="w-3.5 h-3.5" /> },
    { key: 'assembling',        label: 'Assemble',icon: <Sparkles className="w-3.5 h-3.5" /> },
    { key: 'completed',         label: 'Done',    icon: <CheckCircle2 className="w-3.5 h-3.5" /> },
];

function PhaseTracker({ status }: { status: string }) {
    const currentOrder = PIPELINE_PHASES[status]?.order ?? 0;
    return (
        <div className="flex items-center gap-1">
            {PHASES.map((phase, i) => {
                const phaseOrder = PIPELINE_PHASES[phase.key]?.order ?? 0;
                const done = currentOrder > phaseOrder;
                const active = currentOrder === phaseOrder;
                return (
                    <div key={phase.key} className="flex items-center gap-1">
                        <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                            done    ? 'bg-green-500/15 border-green-500/30 text-green-400' :
                            active  ? 'bg-blue-500/20 border-blue-400/50 text-blue-300 animate-pulse' :
                                      'bg-white/5 border-white/10 text-gray-600'
                        }`}>
                            {done ? <CheckCircle2 className="w-3 h-3" /> : phase.icon}
                            <span className="hidden sm:block">{phase.label}</span>
                        </div>
                        {i < PHASES.length - 1 && (
                            <ChevronRight className={`w-3 h-3 ${done ? 'text-green-500/50' : 'text-gray-700'}`} />
                        )}
                    </div>
                );
            })}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Scene card
// ---------------------------------------------------------------------------
function SceneCard({ scene }: { scene: ProductionScene }) {
    const statusLabel: Record<string, string> = {
        pending: 'Waiting',
        image_failed: 'Image Failed',
        animating: 'Animating…',
        failed: 'Failed',
        completed: 'Ready',
    };
    const isDone = scene.animation_status === 'completed';
    const isFailed = ['failed', 'image_failed'].includes(scene.animation_status);
    const isAnim = scene.animation_status === 'animating';

    return (
        <motion.div layout className="bg-white/5 border border-white/10 rounded-xl overflow-hidden group">
            <div className="aspect-video bg-black/40 relative overflow-hidden">
                {scene.image_url ? (
                    <img src={scene.image_url} alt={`Scene ${scene.scene_number}`}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                ) : (
                    <div className="absolute inset-0 flex items-center justify-center">
                        {isAnim ? <RefreshCcw className="w-6 h-6 text-blue-400 animate-spin" /> :
                         isFailed ? <AlertCircle className="w-6 h-6 text-red-400" /> :
                         <Layers className="w-6 h-6 text-gray-700" />}
                    </div>
                )}
                <div className="absolute top-2 left-2 bg-black/70 backdrop-blur px-2 py-0.5 rounded text-[10px] font-bold text-white">
                    #{scene.scene_number}
                </div>
                {isDone && (
                    <div className="absolute top-2 right-2 bg-green-500/20 border border-green-500/40 backdrop-blur px-2 py-0.5 rounded text-[10px] text-green-400">
                        ✓ Done
                    </div>
                )}
                {isAnim && (
                    <div className="absolute inset-0 bg-blue-600/10 flex items-end p-3">
                        <div className="text-xs text-blue-300 flex items-center gap-1.5">
                            <RefreshCcw className="w-3 h-3 animate-spin" /> Animating…
                        </div>
                    </div>
                )}
            </div>
            <div className="p-3">
                <p className="text-xs text-gray-400 line-clamp-2 italic">"{scene.description}"</p>
                <div className="mt-2 flex items-center justify-between">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border ${statusColor(scene.animation_status)}`}>
                        {statusLabel[scene.animation_status] ?? scene.animation_status}
                    </span>
                    <span className="text-[10px] text-gray-600">{scene.animation_model ?? 'std'}</span>
                </div>
            </div>
        </motion.div>
    );
}

// ---------------------------------------------------------------------------
// Live log
// ---------------------------------------------------------------------------
function LiveLog({ logs }: { logs: string[] }) {
    const ref = useRef<HTMLDivElement>(null);
    useEffect(() => { if (ref.current) ref.current.scrollTop = ref.current.scrollHeight; }, [logs]);
    return (
        <div className="bg-black/40 rounded-xl border border-white/10 overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-2 border-b border-white/10">
                <Terminal className="w-4 h-4 text-green-400" />
                <span className="text-xs font-mono text-gray-400 uppercase tracking-widest">Live Log</span>
            </div>
            <div ref={ref} className="p-4 h-40 overflow-y-auto font-mono text-xs space-y-1">
                {logs.length === 0 ? (
                    <p className="text-gray-700">No log entries yet…</p>
                ) : logs.map((line, i) => (
                    <p key={i} className="text-green-300/80">{line}</p>
                ))}
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Launcher — pick a curation job and start
// ---------------------------------------------------------------------------
function Launcher({ prefillId, onStarted }: { prefillId?: string; onStarted: (jobId: string) => void }) {
    const [selectedCurationId, setSelectedCurationId] = useState(prefillId ?? '');
    const [animMode, setAnimMode] = useState<'std' | 'pro'>('std');
    const [audioFile, setAudioFile] = useState<File | null>(null);
    const [uploadedUrl, setUploadedUrl] = useState<string | null>(null);
    const [beatSyncEnabled, setBeatSyncEnabled] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const queryClient = useQueryClient();

    const { data: curations } = useQuery({
        queryKey: ['curation_jobs_for_launcher'],
        queryFn: curationService.listJobs,
    });

    const completedCurations = (curations ?? []).filter(j => j.status === 'completed');
    const selectedCuration: CurationJob | undefined = completedCurations.find(j => j.id === selectedCurationId);
    const isVideoRef = audioFile?.name.toLowerCase().endsWith('.mp4') ?? false;

    const handleFileSelect = async (file: File) => {
        setAudioFile(file);
        setUploadedUrl(null);
        setUploadError(null);
        setBeatSyncEnabled(false);
        setUploading(true);
        try {
            const result = await productionService.uploadAudio(file);
            setUploadedUrl(result.public_url);
        } catch (e: any) {
            setUploadError(e?.response?.data?.detail ?? 'Upload failed');
        } finally {
            setUploading(false);
        }
    };

    const clearAudio = () => {
        setAudioFile(null);
        setUploadedUrl(null);
        setUploadError(null);
        setBeatSyncEnabled(false);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const startMutation = useMutation({
        mutationFn: () => productionService.startJob(
            { curation_job_id: selectedCurationId, animation_mode: animMode, beat_sync_enabled: beatSyncEnabled && isVideoRef },
            uploadedUrl ?? undefined,
            audioFile?.name,
        ),
        onSuccess: (job) => {
            queryClient.invalidateQueries({ queryKey: ['production_jobs'] });
            onStarted(job.id);
        },
    });

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="max-w-2xl mx-auto">
            <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                <div className="p-8 border-b border-white/10 bg-gradient-to-br from-blue-600/10 to-purple-600/10">
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Zap className="text-blue-400" /> Launch Production
                    </h2>
                    <p className="text-gray-400 mt-1">Select a completed brief and configure generation settings</p>
                </div>

                <div className="p-8 space-y-6">
                    {/* Curation job selector */}
                    <div>
                        <label className="text-xs font-bold text-gray-400 uppercase tracking-widest block mb-2">
                            Creative Brief
                        </label>
                        <select
                            value={selectedCurationId}
                            onChange={e => setSelectedCurationId(e.target.value)}
                            className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500/50 appearance-none"
                        >
                            <option value="">— Select a completed curation —</option>
                            {completedCurations.map(j => (
                                <option key={j.id} value={j.id}>
                                    {j.creative_brief?.title ?? `Job ${j.id.slice(0, 8)}`} ({j.num_scenes ?? 0} scenes)
                                </option>
                            ))}
                        </select>
                        {selectedCuration && (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                className="mt-3 p-3 bg-blue-600/10 border border-blue-500/20 rounded-xl text-sm text-blue-300">
                                <p className="font-medium">{selectedCuration.creative_brief?.title}</p>
                                <p className="text-xs text-blue-400/70 mt-1">{selectedCuration.num_scenes} scenes · {selectedCuration.selected_video_ids?.length ?? 0} sources</p>
                            </motion.div>
                        )}
                    </div>

                    {/* Animation mode */}
                    <div>
                        <label className="text-xs font-bold text-gray-400 uppercase tracking-widest block mb-3">
                            Animation Engine
                        </label>
                        <div className="grid grid-cols-2 gap-3">
                            {([['std', 'Seedance 2.0', 'Fast · Cost-efficient'], ['pro', 'Kling Pro', 'Cinematic · Premium quality']] as const).map(([val, title, sub]) => (
                                <button key={val} onClick={() => setAnimMode(val)}
                                    className={`p-4 rounded-xl border text-left transition-all ${animMode === val
                                        ? 'bg-blue-600/20 border-blue-500 shadow-lg shadow-blue-500/10'
                                        : 'bg-white/5 border-white/10 hover:bg-white/10'}`}>
                                    <div className="text-sm font-semibold text-white">{title}</div>
                                    <div className="text-xs text-gray-400 mt-0.5">{sub}</div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Audio upload */}
                    <div>
                        <label className="text-xs font-bold text-gray-400 uppercase tracking-widest block mb-3">
                            Music Track <span className="text-gray-600 normal-case font-normal">(optional)</span>
                        </label>

                        {!audioFile ? (
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                className="w-full p-6 border-2 border-dashed border-white/10 rounded-xl hover:border-blue-500/40 hover:bg-blue-500/5 transition-all group text-center"
                            >
                                <Upload className="w-6 h-6 text-gray-500 group-hover:text-blue-400 mx-auto mb-2 transition-colors" />
                                <p className="text-sm text-gray-400 group-hover:text-gray-300">Click to upload audio or video</p>
                                <p className="text-xs text-gray-600 mt-1">.mp3 · .wav · .mp4 (max 50 MB)</p>
                            </button>
                        ) : (
                            <div className="space-y-3">
                                <div className="flex items-center gap-3 p-4 bg-white/5 border border-white/10 rounded-xl">
                                    <FileAudio className="w-5 h-5 text-blue-400 flex-shrink-0" />
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm text-white truncate">{audioFile.name}</p>
                                        <p className="text-xs text-gray-400">
                                            {uploading ? 'Uploading to Supabase…' :
                                             uploadError ? <span className="text-red-400">{uploadError}</span> :
                                             uploadedUrl ? <span className="text-green-400">Hosted · Ready</span> : ''}
                                        </p>
                                    </div>
                                    <button onClick={clearAudio} className="text-gray-600 hover:text-red-400 transition-colors flex-shrink-0">
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>

                                {/* Beat-sync toggle — only when .mp4 uploaded + Seedance selected */}
                                {isVideoRef && animMode === 'std' && uploadedUrl && (
                                    <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
                                        className="flex items-center justify-between p-4 bg-purple-600/10 border border-purple-500/20 rounded-xl">
                                        <div>
                                            <div className="text-sm font-medium text-white flex items-center gap-2">
                                                <Music className="w-4 h-4 text-purple-400" /> Beat-Sync Animation
                                            </div>
                                            <div className="text-xs text-gray-400 mt-0.5">
                                                Passes .mp4 to Seedance as audio reference · experimental
                                            </div>
                                        </div>
                                        <button onClick={() => setBeatSyncEnabled(v => !v)} className="text-gray-400 hover:text-white transition-colors">
                                            {beatSyncEnabled
                                                ? <ToggleRight className="w-8 h-8 text-purple-400" />
                                                : <ToggleLeft className="w-8 h-8" />}
                                        </button>
                                    </motion.div>
                                )}

                                {isVideoRef && animMode === 'std' && !uploadedUrl && !uploading && (
                                    <p className="text-xs text-gray-500 px-1">Beat-sync available once upload completes</p>
                                )}
                                {!isVideoRef && (
                                    <p className="text-xs text-gray-500 px-1">Audio will be mixed into the final video · Upload .mp4 for Seedance beat-sync</p>
                                )}
                            </div>
                        )}

                        <input ref={fileInputRef} type="file" accept=".mp3,.wav,.mp4,.m4a,.aac" className="hidden"
                            onChange={e => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }} />
                    </div>

                    {startMutation.isError && (
                        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
                            Failed to start: {(startMutation.error as any)?.message}
                        </div>
                    )}

                    <button
                        disabled={!selectedCurationId || startMutation.isPending || uploading}
                        onClick={() => startMutation.mutate()}
                        className="w-full py-4 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold rounded-2xl shadow-xl shadow-blue-600/20 flex items-center justify-center gap-2 transition-all transform hover:scale-[1.02] active:scale-95"
                    >
                        {startMutation.isPending
                            ? <><RefreshCcw className="w-5 h-5 animate-spin" /> Starting…</>
                            : <><Play className="w-5 h-5" /> Start Production</>}
                    </button>
                </div>
            </div>
        </motion.div>
    );
}

// ---------------------------------------------------------------------------
// Job monitor
// ---------------------------------------------------------------------------
function JobMonitor({ jobId }: { jobId: string }) {
    const { data, isLoading } = useQuery<ProductionJobDetail>({
        queryKey: ['production_detail', jobId],
        queryFn: () => productionService.getJob(jobId),
        refetchInterval: (q) => {
            const job = (q.state.data as ProductionJobDetail | undefined)?.job;
            return job && isRunning(job.status) ? 4000 : false;
        },
    });

    if (isLoading || !data) return (
        <div className="flex items-center justify-center py-24">
            <RefreshCcw className="w-6 h-6 text-blue-400 animate-spin mr-3" />
            <span className="text-gray-400">Loading job…</span>
        </div>
    );

    const { job, scenes, tracks } = data;
    const { done, total, pct } = sceneProgress(scenes);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                <div className="flex items-start justify-between mb-4">
                    <div>
                        <p className="text-xs font-mono text-gray-500 uppercase">JOB-{job.id.slice(0, 8)}</p>
                        <h2 className="text-xl font-bold text-white mt-1">Production Run</h2>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold border uppercase tracking-wider ${statusColor(job.status)}`}>
                        {job.status.replace(/_/g, ' ')}
                    </span>
                </div>

                <PhaseTracker status={job.status} />

                {/* Progress bar */}
                <div className="mt-4">
                    <div className="flex justify-between text-xs text-gray-400 mb-1">
                        <span>{done}/{total} scenes complete</span>
                        <span>{pct}%</span>
                    </div>
                    <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                        <motion.div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
                            animate={{ width: `${pct}%` }} transition={{ duration: 0.8 }} />
                    </div>
                </div>

                {/* Completed stats */}
                {job.status === 'completed' && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                        className="mt-4 flex items-center gap-4">
                        <a href={productionService.downloadUrl(job.id)}
                            className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-500 text-white font-bold rounded-xl transition-all shadow-lg shadow-green-600/20">
                            <Download className="w-4 h-4" /> Download Video
                        </a>
                        <div className="text-sm text-gray-400">
                            {job.total_duration_sec ? `${Number(job.total_duration_sec).toFixed(1)}s` : '—'} · {formatFileSize(job.file_size_bytes)}
                        </div>
                    </motion.div>
                )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left: music + log */}
                <div className="space-y-4">
                    {/* Music tracks */}
                    {tracks.length > 0 && (
                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                                <Music className="w-4 h-4 text-pink-400" /> Soundtrack
                            </h3>
                            {tracks.map((t: ProductionTrack) => (
                                <div key={t.id} className="space-y-2">
                                    <div className="flex justify-between items-center text-xs">
                                        <span className="text-gray-300 line-clamp-1">{t.song_prompt}</span>
                                        <span className={`px-2 py-0.5 rounded border text-[10px] ${statusColor(t.suno_status)}`}>{t.suno_status}</span>
                                    </div>
                                    {t.audio_url ? (
                                        <audio controls className="w-full h-8"><source src={t.audio_url} type="audio/mpeg" /></audio>
                                    ) : (
                                        <div className="h-8 bg-black/20 rounded flex items-center justify-center text-xs text-gray-600">
                                            {t.suno_status === 'generating' ? 'Generating…' : 'Pending'}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Live log */}
                    <LiveLog logs={job.progress_log ?? []} />
                </div>

                {/* Right: scene grid */}
                <div className="lg:col-span-2">
                    <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                        <ImageIcon className="w-4 h-4 text-blue-400" /> Scenes ({scenes.length})
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {scenes.map(s => <SceneCard key={s.id} scene={s} />)}
                    </div>
                </div>
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Job sidebar list
// ---------------------------------------------------------------------------
function JobSidebar({ jobs, selectedId, onSelect }: { jobs: ProductionJob[]; selectedId: string | null; onSelect: (id: string) => void }) {
    return (
        <div className="space-y-2">
            {jobs.map(job => (
                <button key={job.id} onClick={() => onSelect(job.id)}
                    className={`w-full text-left p-3 rounded-xl border transition-all ${selectedId === job.id
                        ? 'bg-blue-600/20 border-blue-500'
                        : 'bg-white/5 border-white/10 hover:bg-white/10'}`}>
                    <div className="flex justify-between items-center">
                        <span className="text-xs font-mono text-gray-500">JOB-{job.id.slice(0, 8)}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border font-bold ${statusColor(job.status)}`}>
                            {job.status.replace(/_/g, ' ')}
                        </span>
                    </div>
                    <p className="text-sm text-gray-300 mt-1">{job.num_scenes} scenes</p>
                    <p className="text-xs text-gray-500 mt-0.5">{new Date(job.created_at).toLocaleDateString()}</p>
                    {isRunning(job.status) && <div className="mt-2 h-1 bg-white/10 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 rounded-full animate-pulse w-1/2" />
                    </div>}
                </button>
            ))}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
const Production = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    const prefillCurationId = (location.state as any)?.curationJobId as string | undefined;
    const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
    const [showLauncher, setShowLauncher] = useState(false);

    const { data: jobs = [], isLoading } = useQuery<ProductionJob[]>({
        queryKey: ['production_jobs'],
        queryFn: productionService.listJobs,
        refetchInterval: 8000,
    });

    // Auto-open launcher if coming from Curation with a job ID
    useEffect(() => {
        if (prefillCurationId) {
            setShowLauncher(true);
            navigate(location.pathname, { replace: true, state: {} });
        }
    }, [prefillCurationId]);

    // Auto-select first job
    useEffect(() => {
        if (!selectedJobId && jobs.length > 0 && !showLauncher) {
            setSelectedJobId(jobs[0].id);
        }
    }, [jobs]);

    const handleStarted = (jobId: string) => {
        queryClient.invalidateQueries({ queryKey: ['production_jobs'] });
        setShowLauncher(false);
        setSelectedJobId(jobId);
    };

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <Film className="text-blue-400" /> Production Studio
                    </h1>
                    <p className="text-gray-400 mt-1">Autonomous cinematic video generation pipeline</p>
                </div>
                <button
                    onClick={() => setShowLauncher(v => !v)}
                    className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-all shadow-lg shadow-blue-600/20">
                    <Zap className="w-4 h-4" />
                    {showLauncher ? 'Hide Launcher' : 'New Production'}
                </button>
            </header>

            <AnimatePresence mode="wait">
                {showLauncher ? (
                    <motion.div key="launcher" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                        <Launcher prefillId={prefillCurationId} onStarted={handleStarted} />
                    </motion.div>
                ) : isLoading ? (
                    <div className="flex items-center justify-center py-24">
                        <RefreshCcw className="w-6 h-6 text-blue-400 animate-spin mr-3" />
                        <span className="text-gray-400">Loading…</span>
                    </div>
                ) : jobs.length === 0 ? (
                    <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                        className="text-center py-24 bg-white/5 border border-dashed border-white/10 rounded-2xl">
                        <Film className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                        <h3 className="text-xl font-semibold text-white mb-2">No Production Jobs</h3>
                        <p className="text-gray-500 mb-6">Start from a completed curation brief</p>
                        <button onClick={() => setShowLauncher(true)}
                            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-all">
                            Launch First Production
                        </button>
                    </motion.div>
                ) : (
                    <motion.div key="monitor" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                        className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                        {/* Sidebar */}
                        <div className="lg:col-span-1">
                            <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Jobs</h2>
                            <JobSidebar jobs={jobs} selectedId={selectedJobId} onSelect={setSelectedJobId} />
                        </div>
                        {/* Main panel */}
                        <div className="lg:col-span-3">
                            {selectedJobId
                                ? <JobMonitor jobId={selectedJobId} />
                                : <div className="flex items-center justify-center py-24 text-gray-500">Select a job</div>}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default Production;
