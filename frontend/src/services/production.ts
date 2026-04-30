import axios from 'axios';

const API = 'http://localhost:8000/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ProductionScene {
    id: string;
    scene_number: number;
    description: string;
    image_prompt: string;
    image_url: string | null;
    motion_prompt: string | null;
    animation_model: string | null;
    animation_status: string;
    local_video_path: string | null;
    cometapi_task_id: string | null;
    created_at: string;
}

export interface ProductionTrack {
    id: string;
    track_number: number;
    song_prompt: string;
    suno_status: string;
    audio_url: string | null;
    error_message: string | null;
}

export interface ProductionJob {
    id: string;
    curation_job_id: string;
    status: string;
    num_scenes: number;
    num_tracks: number;
    assembled_video_path: string | null;
    total_duration_sec: number | null;
    file_size_bytes: number | null;
    error_message: string | null;
    progress_log: string[] | null;
    music_url: string | null;
    music_filename: string | null;
    beat_sync_enabled: boolean;
    created_at: string;
}

export interface ProductionJobDetail {
    job: ProductionJob;
    scenes: ProductionScene[];
    tracks: ProductionTrack[];
}

export interface StartProductionRequest {
    curation_job_id: string;
    animation_mode: 'std' | 'pro';
    beat_sync_enabled: boolean;
}

export interface AudioUploadResult {
    public_url: string;
    filename: string;
    size_bytes: number;
    is_video_reference: boolean;
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export const productionService = {
    listJobs: async (): Promise<ProductionJob[]> => {
        const res = await axios.get(`${API}/production/`);
        return res.data;
    },

    getJob: async (jobId: string): Promise<ProductionJobDetail> => {
        const res = await axios.get(`${API}/production/${jobId}`);
        return res.data;
    },

    getJobByCurationId: async (curationJobId: string): Promise<ProductionJob | null> => {
        const res = await axios.get(`${API}/production/curation/${curationJobId}`);
        if (res.data?.status === 'none') return null;
        return res.data;
    },

    startJob: async (
        req: StartProductionRequest,
        musicUrl?: string,
        musicFilename?: string,
    ): Promise<ProductionJob> => {
        const params = new URLSearchParams();
        if (musicUrl) params.set('music_url', musicUrl);
        if (musicFilename) params.set('music_filename', musicFilename);
        const url = `${API}/production/start${params.toString() ? '?' + params.toString() : ''}`;
        const res = await axios.post(url, req);
        return res.data;
    },

    uploadAudio: async (file: File): Promise<AudioUploadResult> => {
        const form = new FormData();
        form.append('file', file);
        const res = await axios.post(`${API}/production/upload/audio`, form, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return res.data;
    },

    downloadUrl: (jobId: string) => `${API}/production/download/${jobId}`,

    retryFailed: async (jobId: string): Promise<{ retried: number; message: string }> => {
        const res = await axios.post(`${API}/production/${jobId}/retry-failed`);
        return res.data;
    },

    triggerAssemble: async (jobId: string): Promise<{ message: string }> => {
        const res = await axios.post(`${API}/production/${jobId}/assemble`);
        return res.data;
    },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export const PIPELINE_PHASES: Record<string, { label: string; order: number }> = {
    queued:            { label: 'Queued',         order: 0 },
    initializing:      { label: 'Initializing',   order: 1 },
    generating_images: { label: 'Images',         order: 2 },
    animating:         { label: 'Animating',      order: 3 },
    assembling:        { label: 'Assembling',     order: 4 },
    completed:         { label: 'Complete',       order: 5 },
    failed:            { label: 'Failed',         order: -1 },
    assembly_failed:   { label: 'Assembly Failed',order: -1 },
};

export function sceneProgress(scenes: ProductionScene[]): { done: number; total: number; pct: number } {
    const total = scenes.length;
    const done = scenes.filter(s => s.animation_status === 'completed').length;
    return { done, total, pct: total > 0 ? Math.round((done / total) * 100) : 0 };
}

export function formatFileSize(bytes: number | null): string {
    if (!bytes) return '—';
    if (bytes > 1e9) return `${(bytes / 1e9).toFixed(1)} GB`;
    if (bytes > 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
    return `${(bytes / 1e3).toFixed(0)} KB`;
}
