import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/curation';

// ---------------------------------------------------------------------------
// Types — matches guide §3.3 Creative Brief schema
// ---------------------------------------------------------------------------

export interface SunoMusicDirection {
    genre: string;
    mood: string;
    bpm_hint: number;
    instruments: string[];
    style_tags: string[];
}

export interface BriefScene {
    scene_number: number;
    lyric_or_timestamp: string;
    description: string;
    motion_prompt: string;
    negative_prompt: string;
    target_duration_sec: number;
    kling_model: string;
    kling_mode: 'std' | 'pro';
    image_tail_scene: number | null;
    animation_method: string;
    transition_note: string | null;
}

export interface CreativeBrief {
    theme: string;
    palette: string[];
    mood: string;
    genre: string;
    total_scenes: number;
    audio_duration_hint_sec: number;
    scenes: BriefScene[];
    suno_music_direction: SunoMusicDirection;
}

export interface CurationJob {
    id: string;
    research_job_id: string;
    status: 'pending' | 'briefing' | 'ready' | 'approved' | 'failed';
    creative_brief?: CreativeBrief;
    user_approved_brief?: CreativeBrief;
    num_scenes?: number;
    error_message?: string;
    approved_at?: string;
}

// ---------------------------------------------------------------------------
// Service methods
// ---------------------------------------------------------------------------

export const curationService = {
    startCuration: async (
        researchJobId: string,
        selectedVideoIds?: string[],
        numScenes?: number,
    ): Promise<CurationJob> => {
        const response = await axios.post(`${API_BASE_URL}/start`, {
            research_job_id: researchJobId,
            selected_video_ids: selectedVideoIds,
            num_scenes: numScenes || 20,
        });
        return response.data;
    },

    listJobs: async (): Promise<CurationJob[]> => {
        const response = await axios.get(`${API_BASE_URL}/`);
        return response.data;
    },

    getJob: async (jobId: string): Promise<CurationJob> => {
        const response = await axios.get(`${API_BASE_URL}/${jobId}`);
        return response.data;
    },

    /**
     * Edit the creative brief before approval.
     * Full brief JSON replacement.
     */
    updateBrief: async (jobId: string, brief: CreativeBrief): Promise<CurationJob> => {
        const response = await axios.put(`${API_BASE_URL}/${jobId}/brief`, {
            brief,
        });
        return response.data;
    },

    /**
     * Approve the creative brief (Stage 2 → Stage 3 gate).
     * Optionally pass an edited brief; otherwise the current brief is approved as-is.
     */
    approveBrief: async (jobId: string, editedBrief?: CreativeBrief): Promise<CurationJob> => {
        const response = await axios.put(`${API_BASE_URL}/${jobId}/approve`, {
            edited_brief: editedBrief || null,
        });
        return response.data;
    },
};
