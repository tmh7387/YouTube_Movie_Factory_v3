import { useState, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Upload, FileText, Youtube, Image, Music, BookMarked, Globe, Send, Loader2, CheckCircle, Tv } from 'lucide-react';
import axios from 'axios';

const API = 'http://localhost:8000/api';

interface SourceOption {
    id: string;
    label: string;
    icon: React.ReactNode;
    description: string;
    color: string;
}

const SOURCE_OPTIONS: SourceOption[] = [
    { id: 'youtube_search', label: 'YouTube Search', icon: <Youtube className="w-5 h-5" />, description: 'Search YouTube for video references', color: 'text-red-400' },
    { id: 'text_brief', label: 'Text Brief', icon: <FileText className="w-5 h-5" />, description: 'Paste a creative concept or script', color: 'text-blue-400' },
    { id: 'single_video', label: 'Single Video', icon: <Youtube className="w-5 h-5" />, description: 'Analyze a specific YouTube video', color: 'text-orange-400' },
    { id: 'image_board', label: 'Image Board', icon: <Image className="w-5 h-5" />, description: 'Upload reference images', color: 'text-green-400' },
    { id: 'audio_track', label: 'Audio Track', icon: <Music className="w-5 h-5" />, description: 'Upload music / audio reference', color: 'text-purple-400' },
    { id: 'existing_bible', label: 'Existing Bible', icon: <BookMarked className="w-5 h-5" />, description: 'Start from a pre-production bible', color: 'text-yellow-400' },
    { id: 'web_article', label: 'Web Article', icon: <Globe className="w-5 h-5" />, description: 'Import content from a URL', color: 'text-cyan-400' },
    { id: 'youtube_channel', label: 'Channel DNA', icon: <Tv className="w-5 h-5" />, description: 'Extract creative principles from a channel\'s top videos', color: 'text-pink-400' },
];

export default function ResearchIntake({ onStarted }: { onStarted?: (jobId: string) => void }) {
    const [sourceType, setSourceType] = useState('youtube_search');
    const [query, setQuery] = useState('');
    const [textBrief, setTextBrief] = useState('');
    const [videoUrl, setVideoUrl] = useState('');
    const [webUrl, setWebUrl] = useState('');
    const [bibleId, setBibleId] = useState('');
    const [files, setFiles] = useState<File[]>([]);
    const [channelUrl, setChannelUrl] = useState('');
    const [channelIntent, setChannelIntent] = useState('');
    const [channelVideoCount, setChannelVideoCount] = useState(5);
    const fileRef = useRef<HTMLInputElement>(null);

    const startMutation = useMutation({
        mutationFn: async () => {
            const sourceData: any = {};

            switch (sourceType) {
                case 'youtube_search':
                    sourceData.query = query;
                    break;
                case 'text_brief':
                    sourceData.text = textBrief;
                    break;
                case 'single_video':
                    sourceData.url = videoUrl;
                    break;
                case 'web_article':
                    sourceData.url = webUrl;
                    break;
                case 'existing_bible':
                    sourceData.bible_id = bibleId;
                    break;
                case 'image_board':
                case 'audio_track':
                    // Upload files first, then pass URLs
                    if (files.length > 0) {
                        const urls: string[] = [];
                        for (const f of files) {
                            const form = new FormData();
                            form.append('file', f);
                            const resp = await axios.post(`${API}/bible/upload-intake?source_type=${sourceType}`, form);
                            urls.push(resp.data.public_url);
                        }
                        sourceData.urls = urls;
                    }
                    break;
                case 'youtube_channel':
                    sourceData.channel_url = channelUrl;
                    sourceData.creative_intent = channelIntent;
                    sourceData.video_count = channelVideoCount;
                    break;
            }

            const resp = await axios.post(`${API}/research/start`, {
                topic:
                    sourceType === 'youtube_channel'
                        ? channelIntent || channelUrl
                        : query || textBrief?.slice(0, 100) || videoUrl || webUrl || `${sourceType} intake`,
                source_type: sourceType,
                source_data: sourceData,
            });
            return resp.data;
        },
        onSuccess: (data) => {
            onStarted?.(data.job_id || data.id);
        },
    });

    const activeSource = SOURCE_OPTIONS.find(s => s.id === sourceType)!;

    return (
        <div className="bg-gray-900/50 border border-white/5 rounded-2xl p-6 space-y-6 max-w-2xl mx-auto">
            <div>
                <h2 className="text-lg font-bold text-white">Research Intake</h2>
                <p className="text-sm text-gray-500 mt-1">Choose your source type and provide input</p>
            </div>

            {/* Source Type Selector */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {SOURCE_OPTIONS.map(opt => (
                    <button key={opt.id} onClick={() => setSourceType(opt.id)}
                        className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all text-center ${
                            sourceType === opt.id
                                ? 'border-blue-500/50 bg-blue-600/10 shadow-lg'
                                : 'border-white/5 bg-gray-800/30 hover:border-white/10 hover:bg-gray-800/60'
                        }`}>
                        <span className={opt.color}>{opt.icon}</span>
                        <span className="text-xs font-medium text-gray-300">{opt.label}</span>
                    </button>
                ))}
            </div>

            {/* Dynamic Input */}
            <div className="space-y-3">
                <p className="text-xs text-gray-500">{activeSource.description}</p>

                {(sourceType === 'youtube_search') && (
                    <input type="text" value={query} onChange={e => setQuery(e.target.value)}
                        placeholder="e.g. dark cinematic music video visuals"
                        className="w-full bg-gray-800 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none" />
                )}

                {sourceType === 'text_brief' && (
                    <textarea value={textBrief} onChange={e => setTextBrief(e.target.value)}
                        placeholder="Paste your script, treatment, or creative brief..."
                        rows={6}
                        className="w-full bg-gray-800 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none resize-none" />
                )}

                {sourceType === 'single_video' && (
                    <input type="text" value={videoUrl} onChange={e => setVideoUrl(e.target.value)}
                        placeholder="https://youtube.com/watch?v=..."
                        className="w-full bg-gray-800 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none" />
                )}

                {sourceType === 'web_article' && (
                    <input type="text" value={webUrl} onChange={e => setWebUrl(e.target.value)}
                        placeholder="https://example.com/article"
                        className="w-full bg-gray-800 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none" />
                )}

                {sourceType === 'existing_bible' && (
                    <input type="text" value={bibleId} onChange={e => setBibleId(e.target.value)}
                        placeholder="Bible UUID"
                        className="w-full bg-gray-800 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none" />
                )}

                {(sourceType === 'image_board' || sourceType === 'audio_track') && (
                    <div>
                        <input ref={fileRef} type="file" multiple accept={sourceType === 'audio_track' ? 'audio/*' : 'image/*'}
                            onChange={e => setFiles(Array.from(e.target.files || []))}
                            className="hidden" />
                        <button onClick={() => fileRef.current?.click()}
                            className="w-full border-2 border-dashed border-white/10 rounded-xl p-6 text-center hover:border-white/20 transition-colors">
                            <Upload className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                            <p className="text-sm text-gray-400">
                                {files.length > 0 ? `${files.length} file(s) selected` : 'Click to upload files'}
                            </p>
                        </button>
                        {files.length > 0 && (
                            <div className="mt-2 space-y-1">
                                {files.map((f, i) => (
                                    <p key={i} className="text-xs text-gray-500 flex items-center gap-1">
                                        <CheckCircle className="w-3 h-3 text-green-500" /> {f.name}
                                    </p>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {sourceType === 'youtube_channel' && (
                    <div className="space-y-3">
                        <input
                            type="text"
                            value={channelUrl}
                            onChange={e => setChannelUrl(e.target.value)}
                            placeholder="https://youtube.com/@channelname"
                            className="w-full bg-gray-800 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                        />
                        <textarea
                            value={channelIntent}
                            onChange={e => setChannelIntent(e.target.value)}
                            placeholder="What are you making? e.g. 'A cinematic documentary about aviation history' — this shapes how principles are extracted"
                            rows={3}
                            className="w-full bg-gray-800 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none resize-none"
                        />
                        <div className="flex items-center gap-3">
                            <label className="text-xs text-gray-500 shrink-0">
                                Videos to sample:
                            </label>
                            <input
                                type="range"
                                min={3}
                                max={7}
                                value={channelVideoCount}
                                onChange={e => setChannelVideoCount(Number(e.target.value))}
                                className="flex-1"
                            />
                            <span className="text-xs text-gray-400 w-4">{channelVideoCount}</span>
                        </div>
                        <p className="text-[11px] text-gray-600">
                            Fetches the channel's top videos by view count and extracts
                            transferable creative principles — not a replication formula.
                        </p>
                    </div>
                )}
            </div>

            {/* Submit */}
            <button onClick={() => startMutation.mutate()} disabled={startMutation.isPending}
                className="w-full px-4 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white font-medium text-sm hover:from-blue-500 hover:to-blue-400 transition-all disabled:opacity-50 flex items-center justify-center gap-2">
                {startMutation.isPending ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Processing...</>
                ) : (
                    <><Send className="w-4 h-4" /> Start Research</>
                )}
            </button>

            {startMutation.isSuccess && (
                <p className="text-sm text-green-400 text-center">Research job started successfully!</p>
            )}
            {startMutation.isError && (
                <p className="text-sm text-red-400 text-center">Failed to start research. Check logs.</p>
            )}
        </div>
    );
}
