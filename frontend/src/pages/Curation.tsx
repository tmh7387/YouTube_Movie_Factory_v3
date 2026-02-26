import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ClipboardCheck,
    Loader2,
    Video,
    Music,
    Palette,
    Target,
    Sparkles,
    AlertCircle,
    Layout
} from 'lucide-react';
import { curationService } from '../services/curation';
import type { CreativeBrief } from '../services/curation';

const Curation: React.FC = () => {
    const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

    const { data: jobs, isLoading } = useQuery({
        queryKey: ['curationJobs'],
        queryFn: curationService.listJobs,
        refetchInterval: (query) => {
            // Poll if any job is still processing
            const hasRunningJobs = query.state.data?.some(j => j.status === 'pending' || j.status === 'generating_brief');
            return hasRunningJobs ? 3000 : false;
        }
    });

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
                    <p className="text-gray-400 mt-1">Refine your AI-generated storyboards and creative briefs.</p>
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
                                className={`p-4 rounded-xl cursor-pointer border transition-all ${selectedJobId === job.id
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
                                    {job.creative_brief?.title || 'Initializing Brief...'}
                                </h3>
                                <div className="mt-3 flex items-center gap-4 text-xs text-gray-400">
                                    <span className="flex items-center gap-1">
                                        <Sparkles className="w-3 h-3" />
                                        {job.num_scenes || 0} Scenes
                                    </span>
                                    <span>{new Date(job.id as any).toLocaleDateString()}</span>
                                </div>
                            </motion.div>
                        ))}
                        {jobs?.length === 0 && (
                            <div className="text-center py-12 bg-white/5 rounded-xl border border-dashed border-white/10">
                                <p className="text-gray-500">No curation jobs yet.</p>
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
                                {selectedJob.status === 'completed' && selectedJob.creative_brief ? (
                                    <BriefDetail brief={selectedJob.creative_brief} />
                                ) : (
                                    <div className="p-20 flex flex-col items-center justify-center text-center">
                                        {selectedJob.status === 'error' ? (
                                            <>
                                                <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
                                                <h3 className="text-xl font-semibold text-white">Generation Failed</h3>
                                                <p className="text-gray-400 mt-2">{selectedJob.creative_brief?.error || 'Unknown error occurred.'}</p>
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
                                    <h3 className="text-gray-400 text-lg">Select a project to view the Creative Brief</h3>
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
    const colors: Record<string, string> = {
        completed: 'bg-green-500/20 text-green-400 border-green-500/30',
        pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
        generating_brief: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        error: 'bg-red-500/20 text-red-400 border-red-500/30',
    };

    return (
        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-tighter border ${colors[status] || colors.pending}`}>
            {status.replace('_', ' ')}
        </span>
    );
};

const BriefDetail: React.FC<{ brief: CreativeBrief }> = ({ brief }) => {
    return (
        <div className="divide-y divide-white/10">
            <div className="p-8 bg-gradient-to-br from-blue-600/10 to-purple-600/10">
                <h2 className="text-2xl font-bold text-white mb-4">{brief.title}</h2>
                <div className="flex flex-wrap gap-4">
                    <MetaItem icon={<Target />} label="Hook" value={brief.hook} />
                    <MetaItem icon={<Sparkles />} label="Narrative" value={brief.narrative_goal} />
                </div>
            </div>

            <div className="p-8 bg-white/5">
                <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                    <Palette className="w-5 h-5 text-pink-400" />
                    Style & Direction
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                        <h4 className="text-sm font-medium text-gray-400 uppercase tracking-widest">Audible Mood</h4>
                        <div className="flex items-center gap-3 bg-white/5 p-4 rounded-xl border border-white/10">
                            <Music className="text-blue-400" />
                            <span className="text-gray-200">{brief.music_mood}</span>
                        </div>
                    </div>
                    <div className="space-y-4">
                        <h4 className="text-sm font-medium text-gray-400 uppercase tracking-widest">Visual Palette</h4>
                        <div className="flex gap-2">
                            {brief.color_palette.map((color, idx) => (
                                <div key={idx} className="flex items-center gap-2 bg-white/5 px-3 py-2 rounded-lg border border-white/10">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color.toLowerCase().includes('#') ? color : '#3b82f6' }} />
                                    <span className="text-xs text-gray-300">{color}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <div className="p-8">
                <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                    <Video className="w-5 h-5 text-orange-400" />
                    Storyboard
                </h3>
                <div className="space-y-6">
                    {brief.storyboard.map((scene, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.1 }}
                            className="flex gap-6 group"
                        >
                            <div className="flex-none w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 font-bold border border-blue-500/20">
                                {scene.scene_index}
                            </div>
                            <div className="flex-1 bg-white/5 border border-white/10 rounded-2xl p-6 group-hover:border-white/20 transition-colors">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-tighter block mb-2">Narration</span>
                                        <p className="text-gray-200 italic leading-relaxed">"{scene.narration}"</p>
                                    </div>
                                    <div>
                                        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-tighter block mb-2">Visual Prompt</span>
                                        <p className="text-sm text-gray-300 leading-relaxed bg-black/30 p-3 rounded-lg border border-white/5 line-clamp-3 hover:line-clamp-none transition-all cursor-zoom-in">
                                            {scene.visual_prompt}
                                        </p>
                                    </div>
                                </div>
                                <div className="mt-4 pt-4 border-t border-white/5 flex gap-4 text-xs text-gray-500 font-medium">
                                    <span>Duration: {scene.duration}s</span>
                                    <span>Pacing: {scene.pacing}</span>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
};

const MetaItem: React.FC<{ icon: React.ReactNode, label: string, value: string }> = ({ icon, label, value }) => (
    <div className="flex-1 min-w-[200px] bg-black/20 p-4 rounded-xl border border-white/5">
        <div className="flex items-center gap-2 text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
            {React.cloneElement(icon as React.ReactElement, { className: 'w-3 h-3' })}
            {label}
        </div>
        <p className="text-gray-200 text-sm line-clamp-2">{value}</p>
    </div>
);

export default Curation;
