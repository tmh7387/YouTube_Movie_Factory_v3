import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Plus, Loader2, CheckCircle2, AlertCircle, Clock, Youtube, FileText, ExternalLink } from 'lucide-react';
import { researchApi, ResearchJob, ResearchJobDetail } from '../services/research';

const JobStatusBadge = ({ status }: { status: string }) => {
    const styles: Record<string, string> = {
        pending: 'bg-gray-100 text-gray-600',
        searching: 'bg-blue-100 text-blue-600',
        analyzing: 'bg-purple-100 text-purple-600',
        completed: 'bg-green-100 text-green-600',
        failed: 'bg-red-100 text-red-600',
        error: 'bg-red-100 text-red-600',
    };

    return (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || styles.pending}`}>
            {status.toUpperCase()}
        </span>
    );
};

const Research = () => {
    const [topic, setTopic] = useState('');
    const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
    const queryClient = useQueryClient();

    const { data: jobs, isLoading: jobsLoading } = useQuery({
        queryKey: ['research-jobs'],
        queryFn: researchApi.listJobs,
        refetchInterval: 5000, // Poll every 5s for updates
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

    const handleStart = (e: React.FormEvent) => {
        e.preventDefault();
        if (topic.trim()) {
            startMutation.mutate(topic);
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <header className="mb-10">
                <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Research Hub</h1>
                <p className="text-gray-500 mt-2">Discover content and generate AI insights for your next video.</p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: New Job & List */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Plus className="w-5 h-5 text-blue-600" />
                            New Video Project
                        </h2>
                        <form onSubmit={handleStart} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Video Topic</label>
                                <input
                                    type="text"
                                    value={topic}
                                    onChange={(e) => setTopic(e.target.value)}
                                    placeholder="e.g. History of Rome"
                                    className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={startMutation.isPending || !topic.trim()}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {startMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
                                Initialize Research
                            </button>
                        </form>
                    </div>

                    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                        <div className="p-4 border-b border-gray-50 bg-gray-50/50">
                            <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">Recent Jobs</h2>
                        </div>
                        <div className="divide-y divide-gray-50 max-h-[600px] overflow-auto">
                            {jobsLoading ? (
                                <div className="p-8 text-center"><Loader2 className="w-8 h-8 animate-spin mx-auto text-gray-300" /></div>
                            ) : jobs?.map((job) => (
                                <button
                                    key={job.id}
                                    onClick={() => setSelectedJobId(job.id)}
                                    className={`w-full text-left p-4 hover:bg-gray-50 transition-colors flex items-center justify-between group ${selectedJobId === job.id ? 'bg-blue-50/50 border-r-4 border-blue-500' : ''}`}
                                >
                                    <div className="truncate pr-4">
                                        <p className="font-semibold text-gray-900 truncate">{job.video_topic}</p>
                                        <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
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
                        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 min-h-[700px]">
                            {jobDetailLoading ? (
                                <div className="flex flex-col items-center justify-center h-full gap-4 text-gray-400">
                                    <Loader2 className="w-10 h-10 animate-spin" />
                                    <p>Loading project intelligence...</p>
                                </div>
                            ) : selectedJob && (
                                <div className="p-8">
                                    <div className="flex items-center justify-between mb-8 pb-6 border-b border-gray-100">
                                        <div>
                                            <h2 className="text-2xl font-bold text-gray-900">{selectedJob.video_topic}</h2>
                                            <div className="flex items-center gap-4 mt-2">
                                                <JobStatusBadge status={selectedJob.status} />
                                                <span className="text-gray-400 text-sm">{selectedJob.id}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-10">
                                        {/* Insights Section */}
                                        <section>
                                            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                                                <FileText className="w-6 h-6 text-purple-600" />
                                                Research Analysis
                                            </h3>
                                            {selectedJob.status === 'completed' ? (
                                                <div className="bg-purple-50/50 border border-purple-100 rounded-2xl p-6 text-gray-800 leading-relaxed whitespace-pre-wrap">
                                                    {selectedJob.research_summary}
                                                </div>
                                            ) : (
                                                <div className="bg-gray-50 rounded-2xl p-10 text-center text-gray-400 border-2 border-dashed border-gray-100">
                                                    {selectedJob.status === 'analyzing' ? (
                                                        <>
                                                            <Loader2 className="w-10 h-10 animate-spin mx-auto mb-4 text-purple-300" />
                                                            <p className="text-purple-600 font-medium animate-pulse">AI is currently synthesizing insights from transcripts...</p>
                                                        </>
                                                    ) : (
                                                        <p>Analysis will appear once video discovery and transcript extraction is complete.</p>
                                                    )}
                                                </div>
                                            )}
                                        </section>

                                        {/* Discovered Videos */}
                                        <section>
                                            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                                                <Youtube className="w-6 h-6 text-red-600" />
                                                Discovered Sources
                                            </h3>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                {selectedJob.videos?.map((video) => (
                                                    <div key={video.video_id} className="group border border-gray-100 rounded-xl overflow-hidden hover:shadow-md transition-shadow bg-gray-50/30">
                                                        <div className="aspect-video bg-gray-200 relative">
                                                            <img
                                                                src={`https://img.youtube.com/vi/${video.video_id}/mqdefault.jpg`}
                                                                alt={video.title}
                                                                className="w-full h-full object-cover"
                                                            />
                                                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                                                <a
                                                                    href={`https://youtube.com/watch?v=${video.video_id}`}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="p-2 bg-white rounded-full text-gray-900 hover:scale-110 transition-transform"
                                                                >
                                                                    <ExternalLink className="w-5 h-5" />
                                                                </a>
                                                            </div>
                                                        </div>
                                                        <div className="p-4">
                                                            <h4 className="font-semibold text-gray-900 line-clamp-2 text-sm h-10">{video.title}</h4>
                                                            <p className="text-xs text-gray-500 mt-2 flex justify-between">
                                                                <span>{video.video_id}</span>
                                                                <span>{video.published_at ? new Date(video.published_at).getFullYear() : ''}</span>
                                                            </p>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </section>
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200 flex flex-col items-center justify-center p-20 text-center h-full">
                            <div className="w-20 h-20 bg-white rounded-3xl shadow-sm flex items-center justify-center mb-6">
                                <Search className="w-10 h-10 text-gray-300" />
                            </div>
                            <h3 className="text-xl font-bold text-gray-600">No project selected</h3>
                            <p className="text-gray-400 mt-2 max-w-xs">Select a project from the left sidebar or start a new one to begin the research phase.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Research;
