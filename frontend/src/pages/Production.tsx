import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
    Music,
    Image as ImageIcon,
    CheckCircle2,
    Clock,
    AlertCircle,
    RefreshCcw,
    Film,
    Layers,
    Sparkles
} from 'lucide-react';
import { motion } from 'framer-motion';

const API_BASE_URL = 'http://localhost:8000/api';

interface ProductionJob {
    id: string;
    curation_job_id: string;
    status: string;
    num_scenes: number;
    num_tracks: number;
    created_at: string;
}

interface Scene {
    id: string;
    scene_number: number;
    description: string;
    image_prompt: string;
    image_url: string;
    status: string;
    error_message?: string;
}

interface Track {
    id: string;
    track_number: number;
    suno_status: string;
    audio_url?: string;
    song_prompt: string;
}

const Production = () => {
    const [selectedJobId] = useState<string | null>(null);

    // Fetch production jobs
    useQuery({
        queryKey: ['production_jobs'],
        queryFn: async () => {
            const response = await axios.get(`${API_BASE_URL}/production/`);
            return response.data;
        },
        refetchInterval: 5000,
    });

    // Fetch specific job details
    const { data: jobDetails } = useQuery({
        queryKey: ['production_job', selectedJobId],
        queryFn: async () => {
            if (!selectedJobId) return null;
            const response = await axios.get(`${API_BASE_URL}/production/${selectedJobId}`);
            return response.data;
        },
        enabled: !!selectedJobId,
        refetchInterval: (query) => {
            const data: any = query.state.data;
            return data?.job?.status === 'processing' ? 3000 : false;
        },
    });

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed': return <CheckCircle2 className="w-5 h-5 text-green-400" />;
            case 'failed': return <AlertCircle className="w-5 h-5 text-red-400" />;
            case 'generating':
            case 'processing': return <RefreshCcw className="w-5 h-5 text-blue-400 animate-spin" />;
            default: return <Clock className="w-5 h-5 text-gray-500" />;
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <header className="mb-10 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <Sparkles className="text-blue-400" />
                        Production Studio
                    </h1>
                    <p className="text-gray-400 mt-2">Generate cinematic assets and soundtracks for your video.</p>
                </div>
            </header>

            {!selectedJobId ? (
                <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-20 text-center">
                    <Film className="w-16 h-16 text-gray-700 mx-auto mb-6" />
                    <h3 className="text-xl font-semibold text-white mb-2">No Active Production Jobs</h3>
                    <p className="text-gray-500 max-w-md mx-auto">
                        Start a production job from the Curation Board to see results here.
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left Column: Job Info & Music */}
                    <div className="lg:col-span-1 space-y-8">
                        <section className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl">
                            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                                <Music className="text-pink-400" />
                                Soundtrack
                            </h2>

                            {jobDetails?.tracks.map((track: Track) => (
                                <div key={track.id} className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                                    <div className="flex justify-between items-start mb-4">
                                        <div>
                                            <span className="text-xs font-bold text-pink-400 uppercase tracking-wider">Track {track.track_number}</span>
                                            <p className="text-sm text-gray-300 mt-1 line-clamp-2">{track.song_prompt}</p>
                                        </div>
                                        {getStatusIcon(track.suno_status)}
                                    </div>

                                    {track.audio_url ? (
                                        <audio controls className="w-full h-10 filter invert opacity-80">
                                            <source src={track.audio_url} type="audio/mpeg" />
                                        </audio>
                                    ) : (
                                        <div className="h-10 bg-gray-700/30 rounded-lg flex items-center justify-center text-xs text-gray-500">
                                            {track.suno_status === 'generating' ? 'Generating audio...' : 'Waiting for generation'}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </section>

                        <section className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl">
                            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                                <Layers className="text-purple-400" />
                                Production Status
                            </h2>
                            <div className="space-y-4">
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-400">Status</span>
                                    <span className="text-blue-400 font-bold uppercase">{jobDetails?.job?.status}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-400">Total Scenes</span>
                                    <span className="text-white">{jobDetails?.job?.num_scenes}</span>
                                </div>
                                <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                                    <div
                                        className="bg-blue-500 h-full transition-all duration-1000"
                                        style={{ width: `${(jobDetails?.scenes.filter((s: any) => s.status === 'completed').length / jobDetails?.job?.num_scenes) * 100}%` }}
                                    />
                                </div>
                            </div>
                        </section>
                    </div>

                    {/* Right Column: Scenes Grid */}
                    <div className="lg:col-span-2">
                        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                            <ImageIcon className="text-blue-400" />
                            Scene Assets
                        </h2>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {jobDetails?.scenes.map((scene: Scene) => (
                                <motion.div
                                    layout
                                    key={scene.id}
                                    className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden group shadow-lg"
                                >
                                    <div className="aspect-video bg-gray-800 relative overflow-hidden">
                                        {scene.image_url ? (
                                            <img
                                                src={scene.image_url}
                                                alt={`Scene ${scene.scene_number}`}
                                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                            />
                                        ) : (
                                            <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center">
                                                {scene.status === 'generating' ? (
                                                    <>
                                                        <RefreshCcw className="w-8 h-8 text-blue-500 animate-spin mb-3" />
                                                        <p className="text-xs text-blue-400 font-medium">Generating Visuals...</p>
                                                    </>
                                                ) : scene.status === 'failed' ? (
                                                    <>
                                                        <AlertCircle className="w-8 h-8 text-red-500 mb-3" />
                                                        <p className="text-xs text-red-400 font-medium">{scene.error_message || 'Generation Failed'}</p>
                                                    </>
                                                ) : (
                                                    <Clock className="w-8 h-8 text-gray-700" />
                                                )}
                                            </div>
                                        )}
                                        <div className="absolute top-3 left-3 bg-black/60 backdrop-blur-md px-2 py-1 rounded-md text-[10px] font-bold text-white">
                                            SCENE {scene.scene_number}
                                        </div>
                                    </div>
                                    <div className="p-4">
                                        <p className="text-sm text-gray-400 line-clamp-2 italic">"{scene.description}"</p>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Production;
