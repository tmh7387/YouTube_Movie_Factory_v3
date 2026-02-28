import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
    Search,
    Plus,
    Loader2,
    Clock,
    Youtube,
    FileText,
    ExternalLink,
    ClipboardCheck,
    Zap,
    ChevronDown,
    ChevronRight,
    Trophy,
    ListVideo,
    ThumbsUp,
    Eye,
    Play,
    Trash2
} from 'lucide-react';
import { researchApi } from '../services/research';
import type { ResearchVideo } from '../services/research';
import { curationService } from '../services/curation';

const JobStatusBadge = ({ status }: { status: string }) => {
    const styles: Record<string, string> = {
        pending: 'bg-gray-800 text-gray-400 border-gray-700',
        searching: 'bg-blue-900/30 text-blue-400 border-blue-800/50',
        analyzing: 'bg-purple-900/30 text-purple-400 border-purple-800/50',
        completed: 'bg-green-900/30 text-green-400 border-green-800/50',
        failed: 'bg-red-900/30 text-red-400 border-red-800/50',
        error: 'bg-red-900/30 text-red-400 border-red-800/50',
    };

    return (
        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-tighter border ${styles[status] || styles.pending} `}>
            {status.replace('_', ' ')}
        </span>
    );
};

const formatDuration = (seconds?: number | null) => {
    if (!seconds) return '--:--';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
};

const formatNumber = (num?: number | null) => {
    if (num == null) return '--';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
};

const Research = () => {
    const [topic, setTopic] = useState('');
    const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
    const [isLogExpanded, setIsLogExpanded] = useState(() => {
        const saved = localStorage.getItem('researchLogExpanded');
        return saved !== null ? JSON.parse(saved) : true;
    });
    const [activeTab, setActiveTab] = useState<'analysis' | 'ranking' | 'sources'>('analysis');
    const [selectedVideos, setSelectedVideos] = useState<Set<string>>(new Set());
    const [expandedReasoning, setExpandedReasoning] = useState<string | null>(null);

    const queryClient = useQueryClient();
    const navigate = useNavigate();

    const { data: jobs, isLoading: jobsLoading } = useQuery({
        queryKey: ['research-jobs'],
        queryFn: researchApi.listJobs,
        refetchInterval: 5000,
    });

    const { data: selectedJob, isLoading: jobDetailLoading } = useQuery({
        queryKey: ['research-job', selectedJobId],
        queryFn: () => researchApi.getJob(selectedJobId!),
        enabled: !!selectedJobId,
        refetchInterval: (query) => (query.state.data?.status === 'completed' || query.state.data?.status === 'failed' ? false : 3000),
    });

    useEffect(() => {
        localStorage.setItem('researchLogExpanded', JSON.stringify(isLogExpanded));
    }, [isLogExpanded]);

    useEffect(() => {
        setSelectedVideos(new Set());
        setActiveTab('analysis');
        setExpandedReasoning(null);
    }, [selectedJobId]);

    const startMutation = useMutation({
        mutationFn: (newTopic: string) => researchApi.startJob(newTopic),
        onSuccess: () => {
            setTopic('');
            queryClient.invalidateQueries({ queryKey: ['research-jobs'] });
        },
    });

    const curateMutation = useMutation({
        mutationFn: (researchJobId: string) => curationService.startCuration(researchJobId),
        onSuccess: () => {
            navigate('/curation');
        }
    });

    const deleteMutation = useMutation({
        mutationFn: (researchJobId: string) => researchApi.deleteJob(researchJobId),
        onSuccess: (_, deletedJobId) => {
            queryClient.invalidateQueries({ queryKey: ['research-jobs'] });
            if (selectedJobId === deletedJobId) {
                setSelectedJobId(null);
            }
        }
    });

    const handleStart = (e: React.FormEvent) => {
        e.preventDefault();
        if (topic.trim()) {
            startMutation.mutate(topic);
        }
    };

    const toggleVideoSelection = (videoId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        const newSelection = new Set(selectedVideos);
        if (newSelection.has(videoId)) {
            newSelection.delete(videoId);
        } else {
            newSelection.add(videoId);
        }
        setSelectedVideos(newSelection);
    };

    const selectAllVideos = () => {
        if (!selectedJob?.videos) return;
        if (selectedVideos.size === selectedJob.videos.length) {
            setSelectedVideos(new Set());
        } else {
            setSelectedVideos(new Set(selectedJob.videos.map(v => v.video_id)));
        }
    };

    // Derived sorted videos based on Gemini Score
    const rankedVideos = selectedJob?.videos ? [...selectedJob.videos].sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0)) : [];

    return (
        <div className="h-[calc(100vh-theme(spacing.16))] md:h-full bg-[#0f1117] text-white flex flex-col font-sans overflow-hidden">
            <header className="px-6 py-4 border-b border-white/10 shrink-0 bg-gray-900/50 backdrop-blur-md z-10 flex justify-between items-center">
                <div>
                    <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                        <Zap className="w-5 h-5 text-yellow-400" />
                        Research Hub
                    </h1>
                    <p className="text-xs text-gray-400 mt-1">Discover content and generate AI insights for your next video.</p>
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
                {/* Column A: Left Sidebar */}
                <div className="w-[320px] shrink-0 border-r border-white/10 flex flex-col bg-gray-900/30 overflow-hidden relative">
                    {/* Top Section: New Job Form */}
                    <div className="p-5 shrink-0 bg-gray-900/50 shadow-sm z-10 relative">
                        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                            <Plus className="w-4 h-4 text-blue-400" />
                            New Video Project
                        </h2>
                        <form onSubmit={handleStart} className="space-y-4">
                            <div>
                                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Video Topic</label>
                                <input
                                    type="text"
                                    value={topic}
                                    onChange={(e) => setTopic(e.target.value)}
                                    placeholder="e.g. AI Revolution 2025"
                                    className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-lg text-sm text-white focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all placeholder:text-gray-600"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={startMutation.isPending || !topic.trim()}
                                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2 rounded-lg text-sm shadow-lg shadow-blue-600/20 transition-all disabled:opacity-50 flex items-center justify-center gap-2 group"
                            >
                                {startMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4 group-hover:scale-110 transition-transform" />}
                                Initialize Research
                            </button>
                        </form>
                    </div>

                    {/* Bottom Section: Analysis Log */}
                    <div className="flex-1 flex flex-col min-h-0 border-t border-white/5 relative bg-black/20">
                        <button
                            onClick={() => setIsLogExpanded(!isLogExpanded)}
                            className="w-full px-5 py-3 flex items-center justify-between text-xs font-bold text-gray-400 uppercase tracking-widest hover:text-white transition-colors hover:bg-white/5 bg-gray-900/80 sticky top-0 z-10 border-b border-white/5"
                        >
                            <span className="flex items-center gap-2">
                                <Clock className="w-3.5 h-3.5" />
                                Analysis Log
                            </span>
                            {isLogExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                        </button>

                        <div className={`overflow-y-auto transition-all duration-300 ease-in-out ${isLogExpanded ? 'flex-1 opacity-100' : 'h-0 opacity-0 overflow-hidden'}`}>
                            {jobsLoading ? (
                                <div className="p-8 text-center"><Loader2 className="w-6 h-6 animate-spin mx-auto text-gray-600" /></div>
                            ) : jobs?.map((job) => (
                                <button
                                    key={job.id}
                                    onClick={() => setSelectedJobId(job.id)}
                                    className={`w-full text-left px-5 py-4 border-b border-white/5 hover:bg-white/5 transition-colors group ${selectedJobId === job.id ? 'bg-blue-600/10 border-l-2 border-l-blue-500 border-b-transparent' : 'border-l-2 border-l-transparent'} `}
                                >
                                    <div className="flex justify-between items-start gap-2 mb-2">
                                        <p className="font-medium text-sm text-gray-300 line-clamp-2 max-w-[180px] group-hover:text-white transition-colors">{job.genre_topic}</p>
                                        <div className="flex items-center gap-2">
                                            <JobStatusBadge status={job.status} />
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    if (window.confirm('Are you sure you want to delete this research job?')) {
                                                        deleteMutation.mutate(job.id);
                                                    }
                                                }}
                                                className="text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                                                title="Delete Job"
                                            >
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                        </div>
                                    </div>
                                    <p className="text-[10px] text-gray-500 flex items-center gap-1 font-mono">
                                        {new Date(job.created_at).toLocaleDateString()}
                                    </p>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Columns B & C: Main Content Area */}
                <div className="flex-1 flex min-w-0 bg-[#0A0C10]">
                    {!selectedJobId ? (
                        <div className="flex-1 flex flex-col items-center justify-center p-20 text-center text-gray-500">
                            <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mb-6 border border-white/10 shadow-2xl">
                                <Search className="w-8 h-8 text-gray-600" />
                            </div>
                            <h3 className="text-xl font-semibold text-gray-300 mb-2">Select an analysis</h3>
                            <p className="text-sm max-w-sm">Choose a project from the left sidebar or start a new video research job to begin.</p>
                        </div>
                    ) : (
                        <>
                            {/* Column B: Center Panel (Tabs) */}
                            <div className="flex-1 flex flex-col min-w-0 border-r border-white/10 relative">
                                {jobDetailLoading ? (
                                    <div className="flex flex-col items-center justify-center h-full gap-4 text-gray-500">
                                        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                                        <p className="font-medium text-sm">Synthesizing intelligence...</p>
                                    </div>
                                ) : selectedJob && (
                                    <>
                                        {/* Header area in Center Column */}
                                        <div className="px-8 py-6 shrink-0 bg-gray-900/20">
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <h2 className="text-2xl font-bold text-white mb-2 line-clamp-2">{selectedJob.genre_topic}</h2>
                                                    <div className="flex items-center gap-3">
                                                        <JobStatusBadge status={selectedJob.status} />
                                                        <span className="text-gray-500 text-[10px] font-mono tracking-widest">{new Date(selectedJob.created_at).toLocaleDateString()}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Tabs */}
                                        <div className="px-8 shrink-0 border-b border-white/10 flex gap-6 mt-2">
                                            {[
                                                { id: 'analysis', label: 'Analysis', icon: FileText },
                                                { id: 'ranking', label: 'Ranking Report', icon: Trophy },
                                                { id: 'sources', label: 'Sources', icon: ListVideo, className: 'xl:hidden' }
                                            ].map(tab => (
                                                <button
                                                    key={tab.id}
                                                    onClick={() => setActiveTab(tab.id as any)}
                                                    className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${activeTab === tab.id ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-300'} ${tab.className || ''}`}
                                                >
                                                    <tab.icon className="w-4 h-4" />
                                                    {tab.label}
                                                </button>
                                            ))}
                                        </div>

                                        {/* Tab Content Area */}
                                        <div className="flex-1 overflow-y-auto p-8 relative scroll-smooth">
                                            {/* Analysis Tab */}
                                            {activeTab === 'analysis' && (
                                                <div className="max-w-3xl animate-in fade-in duration-300">
                                                    {selectedJob.status === 'completed' ? (
                                                        <div className="bg-purple-900/10 border border-purple-500/20 rounded-xl p-6 text-gray-300 leading-relaxed prose prose-invert prose-purple max-w-none shadow-sm font-serif">
                                                            <ReactMarkdown>{selectedJob.research_summary || "No summary available."}</ReactMarkdown>
                                                        </div>
                                                    ) : (
                                                        <div className="bg-white/5 rounded-xl p-12 text-center text-gray-500 border border-dashed border-white/10">
                                                            {selectedJob.status === 'analyzing' ? (
                                                                <>
                                                                    <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-purple-500" />
                                                                    <p className="text-purple-400 font-medium animate-pulse text-sm">Synthesizing insights from multiple transcripts...</p>
                                                                </>
                                                            ) : (
                                                                <p className="text-sm">Narrative analysis will appear once content discovery is complete.</p>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            )}

                                            {/* Ranking Report Tab */}
                                            {activeTab === 'ranking' && (
                                                <div className="animate-in fade-in duration-300 overflow-x-auto pb-8">
                                                    <table className="w-full text-left text-sm text-gray-400 border-collapse">
                                                        <thead className="text-xs uppercase bg-white/5 text-gray-500 sticky top-0 z-10 shadow-sm border-b border-white/10">
                                                            <tr>
                                                                <th className="px-4 py-3 font-semibold rounded-tl-lg">Title</th>
                                                                <th className="px-4 py-3 font-semibold text-center text-purple-400"><div className="flex items-center justify-center gap-1"><Zap className="w-3 h-3" /> Score</div></th>
                                                                <th className="px-4 py-3 font-semibold text-right">Views</th>
                                                                <th className="px-4 py-3 font-semibold text-right">Duration</th>
                                                                <th className="px-4 py-3 font-semibold rounded-tr-lg">Reasoning</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody className="divide-y divide-white/5">
                                                            {rankedVideos.map(video => (
                                                                <React.Fragment key={video.video_id}>
                                                                    <tr className="hover:bg-white/5 transition-colors group">
                                                                        <td className="px-4 py-3 font-medium text-gray-200 line-clamp-2 max-w-[200px] leading-snug group-hover:text-white" title={video.title}>{video.title}</td>
                                                                        <td className="px-4 py-3 text-center">
                                                                            <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-purple-900/30 text-purple-300 font-bold border border-purple-500/20 text-xs">
                                                                                {video.relevance_score || '-'}
                                                                            </span>
                                                                        </td>
                                                                        <td className="px-4 py-3 text-right font-mono text-xs">{formatNumber(video.view_count)}</td>
                                                                        <td className="px-4 py-3 text-right font-mono text-xs text-gray-500">{formatDuration(video.duration_seconds)}</td>
                                                                        <td className="px-4 py-3">
                                                                            <button
                                                                                onClick={() => setExpandedReasoning(expandedReasoning === video.video_id ? null : video.video_id)}
                                                                                className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1"
                                                                            >
                                                                                {expandedReasoning === video.video_id ? 'Hide' : 'Details'}
                                                                                {expandedReasoning === video.video_id ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                                                                            </button>
                                                                        </td>
                                                                    </tr>
                                                                    {expandedReasoning === video.video_id && (
                                                                        <tr className="bg-blue-900/10 border-l-2 border-blue-500">
                                                                            <td colSpan={5} className="px-6 py-4 text-xs text-gray-300 leading-relaxed italic border-b border-white/5">
                                                                                <span className="font-semibold text-blue-400 not-italic block mb-1 uppercase tracking-wider text-[10px]">Gemini Context:</span>
                                                                                {video.gemini_reasoning || "No reasoning provided by the AI."}
                                                                            </td>
                                                                        </tr>
                                                                    )}
                                                                </React.Fragment>
                                                            ))}
                                                            {rankedVideos.length === 0 && (
                                                                <tr>
                                                                    <td colSpan={5} className="px-4 py-12 text-center text-gray-600">No ranked sources available.</td>
                                                                </tr>
                                                            )}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            )}

                                            {/* Sources Tab (Mobile / Narrow screen fallback) */}
                                            {activeTab === 'sources' && (
                                                <div className="xl:hidden animate-in fade-in duration-300 grid grid-cols-1 sm:grid-cols-2 gap-4 pb-20">
                                                    {/* Duplicated Source Cards for responsiveness, relying on main right column for large screens */}
                                                    {selectedJob?.videos?.map((video) => (
                                                        <VideoSourceCard key={`mobile-${video.video_id}`} video={video} selected={selectedVideos.has(video.video_id)} onToggle={(e) => toggleVideoSelection(video.video_id, e)} />
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </>
                                )}
                            </div>

                            {/* Column C: Right Panel (Source Grid + Footer) */}
                            <div className="hidden xl:flex w-[480px] shrink-0 flex-col bg-[#0f1117] border-l border-white/5 relative shadow-[-10px_0_20px_-10px_rgba(0,0,0,0.5)]">
                                <div className="p-4 border-b border-white/5 shrink-0 flex items-center justify-between bg-gray-900/50 backdrop-blur-md sticky top-0 z-20">
                                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                        <Youtube className="w-4 h-4 text-red-500" />
                                        Discovered Sources
                                    </h3>
                                    <div className="flex items-center gap-3">
                                        <span className="text-xs font-semibold text-gray-500">{selectedJob?.videos?.length || 0} Total</span>
                                        <button onClick={selectAllVideos} className="text-[10px] uppercase tracking-widest font-bold text-blue-400 hover:text-blue-300 transition-colors px-2 py-1 bg-blue-500/10 rounded">
                                            {selectedVideos.size > 0 && selectedVideos.size === selectedJob?.videos?.length ? 'Deselect All' : 'Select All'}
                                        </button>
                                    </div>
                                </div>

                                <div className="flex-1 overflow-y-auto p-4 content-start">
                                    {selectedJob?.videos?.length ?? 0 > 0 ? (
                                        <div className="flex flex-col gap-3 pb-24">
                                            {selectedJob?.videos?.map((video) => (
                                                <VideoSourceCard key={video.video_id} video={video} selected={selectedVideos.has(video.video_id)} onToggle={(e) => toggleVideoSelection(video.video_id, e)} />
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="opacity-30 pointer-events-none flex flex-col gap-4 filter grayscale">
                                            {/* Empty state ghost cards */}
                                            {[1, 2, 3].map(i => (
                                                <div key={i} className="h-28 bg-white/5 border border-white/10 rounded-xl relative overflow-hidden">
                                                    <div className="absolute inset-y-0 left-0 w-40 bg-gray-800" />
                                                    <div className="absolute left-[170px] right-4 top-4 space-y-2">
                                                        <div className="h-4 bg-gray-800 rounded w-full" />
                                                        <div className="h-4 bg-gray-800 rounded w-2/3" />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                {/* Start Curation Sticky Footer */}
                                <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[#0A0C10] via-[#0A0C10] to-transparent shrink-0 pointer-events-none">
                                    <div className="pointer-events-auto">
                                        {selectedJob && selectedJob.status === 'completed' && (
                                            <button
                                                onClick={() => curateMutation.mutate(selectedJob.id)}
                                                disabled={curateMutation.isPending || selectedVideos.size === 0}
                                                className="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-3.5 px-6 rounded-xl shadow-lg shadow-green-600/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-between group overflow-hidden relative"
                                            >
                                                <span className="flex items-center gap-2 relative z-10">
                                                    {curateMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <ClipboardCheck className="w-5 h-5 group-hover:-rotate-12 transition-transform" />}
                                                    Start Curation
                                                </span>
                                                <span className="text-sm bg-black/20 px-3 py-1 rounded-lg relative z-10 font-mono tracking-widest">{selectedVideos.size} Selected</span>

                                                {/* Hover shine effect */}
                                                <div className="absolute inset-0 -translate-x-full group-hover:animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-white/10 to-transparent z-0" />
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

// Helper component for Source Cards
const VideoSourceCard = ({ video, selected, onToggle }: { video: ResearchVideo, selected: boolean, onToggle: (e: React.MouseEvent) => void }) => {
    return (
        <div
            onClick={onToggle}
            className={`group cursor-pointer border rounded-xl overflow-hidden transition-all flex bg-gray-900/40 relative h-28 hover:shadow-lg hover:-translate-y-0.5
                ${selected ? 'border-blue-500 ring-1 ring-blue-500 shadow-blue-500/10' : 'border-white/10 hover:border-white/30'} 
            `}
        >
            {/* Selection Checkbox indicator (custom) */}
            <div className={`absolute top-2 left-2 z-10 w-5 h-5 rounded border shadow-sm flex items-center justify-center transition-colors
                ${selected ? 'bg-blue-500 border-blue-400 text-white' : 'bg-black/50 border-white/30 text-transparent group-hover:border-white/60'}
            `}>
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
            </div>

            <div className="w-44 shrink-0 bg-black relative overflow-hidden">
                <img
                    src={`https://img.youtube.com/vi/${video.video_id}/mqdefault.jpg`}
                    alt={video.title}
                    className={`w-full h-full object-cover transition-all duration-500 ${selected ? 'opacity-40 scale-105' : 'opacity-70 group-hover:opacity-100 group-hover:scale-105'} `}
                />
                <div className="absolute bottom-1 right-1 bg-black/80 px-1.5 py-0.5 rounded text-[10px] font-mono text-white tracking-wider flex items-center gap-1">
                    <Play className="w-2.5 h-2.5" />
                    {formatDuration(video.duration_seconds)}
                </div>
            </div>
            <div className="p-3 flex-1 min-w-0 flex flex-col justify-between relative pl-4">
                <div>
                    <h4 className={`font-semibold text-sm leading-snug line-clamp-2 transition-colors ${selected ? 'text-blue-100' : 'text-gray-200 group-hover:text-white'}`}>{video.title}</h4>
                    <p className="text-[11px] text-gray-400 mt-1 truncate">{video.channel || 'YouTube Source'}</p>
                </div>

                <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center gap-3 text-xs text-gray-500 font-mono">
                        <span className="flex items-center gap-1" title="Views"><Eye className="w-3 h-3" />{formatNumber(video.view_count)}</span>
                        <span className="flex items-center gap-1" title="Likes"><ThumbsUp className="w-3 h-3" />{formatNumber(video.likes)}</span>
                    </div>
                </div>

                <a
                    href={`https://youtube.com/watch?v=${video.video_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="absolute top-3 right-3 p-1.5 rounded-full bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                    title="Watch on YouTube"
                >
                    <ExternalLink className="w-3.5 h-3.5" />
                </a>
            </div>
        </div>
    );
};

export default Research;
