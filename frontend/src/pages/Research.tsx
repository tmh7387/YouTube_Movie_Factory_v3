import React, { useState } from 'react';
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
    Zap
} from 'lucide-react';
import { researchApi } from '../services/research';
import type { ResearchJob, ResearchJobDetail } from '../services/research';
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
        <span className={`px - 2 py - 0.5 rounded - full text - [10px] font - bold uppercase tracking - tighter border ${styles[status] || styles.pending} `}>
            {status.replace('_', ' ')}
        </span>
    );
};

const Research = () => {
    const [topic, setTopic] = useState('');
    const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
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

    const handleStart = (e: React.FormEvent) => {
        e.preventDefault();
        if (topic.trim()) {
            startMutation.mutate(topic);
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <header className="mb-10">
                <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
                    <Zap className="text-yellow-400" />
                    Research Hub
                </h1>
                <p className="text-gray-400 mt-2">Discover content and generate AI insights for your next video.</p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: New Job & List */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-white/5 p-6 rounded-2xl border border-white/10 shadow-xl">
                        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <Plus className="w-5 h-5 text-blue-400" />
                            New Video Project
                        </h2>
                        <form onSubmit={handleStart} className="space-y-4">
                            <div>
                                <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Video Topic</label>
                                <input
                                    type="text"
                                    value={topic}
                                    onChange={(e) => setTopic(e.target.value)}
                                    placeholder="e.g. AI Revolution 2025"
                                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all placeholder:text-gray-600"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={startMutation.isPending || !topic.trim()}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl shadow-lg shadow-blue-600/20 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {startMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
                                Initialize Research
                            </button>
                        </form>
                    </div>

                    <div className="bg-white/5 rounded-2xl border border-white/10 overflow-hidden shadow-xl">
                        <div className="p-4 border-b border-white/5 bg-white/5">
                            <h2 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Recent Analysis</h2>
                        </div>
                        <div className="divide-y divide-white/5 max-h-[600px] overflow-auto">
                            {jobsLoading ? (
                                <div className="p-8 text-center"><Loader2 className="w-8 h-8 animate-spin mx-auto text-gray-600" /></div>
                            ) : jobs?.map((job) => (
                                <button
                                    key={job.id}
                                    onClick={() => setSelectedJobId(job.id)}
                                    className={`w - full text - left p - 4 hover: bg - white / 5 transition - colors flex items - center justify - between group ${selectedJobId === job.id ? 'bg-blue-600/10 border-r-4 border-blue-500' : ''} `}
                                >
                                    <div className="truncate pr-4">
                                        <p className="font-semibold text-gray-200 truncate group-hover:text-white">{job.video_topic}</p>
                                        <p className="text-[10px] text-gray-500 mt-1 flex items-center gap-1 font-medium">
                                            <Clock className="w-3 h-3" />
                                            {new Date(job.created_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <JobStatusBadge status={job.status} />
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right Column: Detailed View */}
                <div className="lg:col-span-2">
                    {selectedJobId ? (
                        <div className="bg-white/5 rounded-2xl border border-white/10 min-h-[700px] shadow-2xl">
                            {jobDetailLoading ? (
                                <div className="flex flex-col items-center justify-center h-full gap-4 text-gray-500">
                                    <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
                                    <p className="font-medium">Synthesizing project intelligence...</p>
                                </div>
                            ) : selectedJob && (
                                <div className="p-8">
                                    <div className="flex items-start justify-between mb-8 pb-6 border-b border-white/10">
                                        <div>
                                            <h2 className="text-2xl font-bold text-white">{selectedJob.video_topic}</h2>
                                            <div className="flex items-center gap-4 mt-2">
                                                <JobStatusBadge status={selectedJob.status} />
                                                <span className="text-gray-500 text-[10px] font-mono uppercase tracking-widest">{selectedJob.id}</span>
                                            </div>
                                        </div>
                                        {selectedJob.status === 'completed' && (
                                            <button
                                                onClick={() => curateMutation.mutate(selectedJob.id)}
                                                disabled={curateMutation.isPending}
                                                className="bg-green-600 hover:bg-green-700 text-white text-sm font-bold px-6 py-2.5 rounded-xl shadow-lg shadow-green-600/20 flex items-center gap-2 transition-all"
                                            >
                                                {curateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <ClipboardCheck className="w-4 h-4" />}
                                                Start Curation
                                            </button>
                                        )}
                                    </div>

                                    <div className="space-y-12">
                                        {/* Insights Section */}
                                        <section>
                                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                                <FileText className="w-5 h-5 text-purple-400" />
                                                AI Narratives & Synthesis
                                            </h3>
                                            {selectedJob.status === 'completed' ? (
                                                <div className="bg-purple-900/10 border border-purple-500/20 rounded-2xl p-6 text-gray-300 leading-relaxed whitespace-pre-wrap text-sm shadow-inner italic">
                                                    {selectedJob.research_summary}
                                                </div>
                                            ) : (
                                                <div className="bg-white/5 rounded-2xl p-10 text-center text-gray-500 border-2 border-dashed border-white/5">
                                                    {selectedJob.status === 'analyzing' ? (
                                                        <>
                                                            <Loader2 className="w-10 h-10 animate-spin mx-auto mb-4 text-purple-500" />
                                                            <p className="text-purple-400 font-bold animate-pulse uppercase tracking-tighter">Synthesizing insights from multiple transcripts...</p>
                                                        </>
                                                    ) : (
                                                        <p className="text-sm">Narrative analysis will appear once content discovery is complete.</p>
                                                    )}
                                                </div>
                                            )}
                                        </section>

                                        {/* Discovered Videos */}
                                        <section>
                                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                                <Youtube className="w-5 h-5 text-red-500" />
                                                Discovered Sources
                                            </h3>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                {selectedJob.videos?.map((video) => (
                                                    <div key={video.video_id} className="group border border-white/10 rounded-xl overflow-hidden hover:border-white/20 transition-all bg-white/5">
                                                        <div className="aspect-video bg-gray-900 relative">
                                                            <img
                                                                src={`https://img.youtube.com/vi/${video.video_id}/mqdefault.jpg`}
                                                                alt={video.title}
                                                                className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity"
                                                            />
                                                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                                                <a
                                                                    href={`https://youtube.com/watch?v=${video.video_id}`}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="p-3 bg-white rounded-full text-gray-900 hover:scale-110 shadow-xl transition-transform"
                                                                >
                                                                    <ExternalLink className="w-5 h-5" />
                                                                </a>
                                                            </div>
                                                        </div >
                                                        <div className="p-4">
                                                            <h4 className="font-semibold text-gray-200 line-clamp-2 text-xs h-8 group-hover:text-white transition-colors">{video.title}</h4>
                                                            <div className="mt-4 flex items-center justify-between text-[10px] font-bold text-gray-600 uppercase tracking-widest">
                                                                <span className="bg-white/5 px-2 py-0.5 rounded border border-white/5">{video.video_id}</span>
                                                                <span>{video.published_at ? new Date(video.published_at).getFullYear() : ''}</span>
                                                            </div>
                                                        </div>
                                                    </div >
                                                ))}
                                            </div >
                                        </section >
                                    </div >
                                </div >
                            )}
                        </div >
                    ) : (
                        <div className="bg-white/2 rounded-2xl border-2 border-dashed border-white/5 flex flex-col items-center justify-center p-20 text-center h-full">
                            <div className="w-20 h-20 bg-white/5 rounded-3xl flex items-center justify-center mb-6 border border-white/10 shadow-2xl">
                                <Search className="w-10 h-10 text-gray-700" />
                            </div>
                            <h3 className="text-xl font-bold text-gray-300">No project selected</h3>
                            <p className="text-gray-500 mt-2 max-w-xs text-sm">Select a project from the left sidebar or start a new one to begin the research phase.</p>
                        </div>
                    )}
                </div >
            </div >
        </div >
    );
};

export default Research;
