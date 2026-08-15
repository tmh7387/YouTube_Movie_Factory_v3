import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/research';

export interface ResearchVideo {
    video_id: string;
    title: string;
    channel: string | null;
    view_count: number | null;
    likes: number | null;
    duration_seconds: number | null;
    published_at: string | null;
    thumbnail_url?: string;
    relevance_score: number | null;
    gemini_reasoning: string | null;
}

export interface ResearchJob {
    id: string;
    status: 'pending' | 'searching' | 'analyzing' | 'completed' | 'failed' | 'error';
    genre_topic: string;
    research_summary: string | null;
    research_brief: Record<string, any> | null;
    source_type?: string | null;
    source_data?: Record<string, any> | null;
    created_at: string;
}

export interface ResearchJobDetail extends ResearchJob {
    videos: ResearchVideo[];
}

// ── Research Brief types ──────────────────────────────────────────

export interface FilterOverrides {
    min_duration_sec: number | null;
    max_duration_sec: number | null;
    date_after: string | null;
    min_views: number | null;
}

export interface AudioMetadata {
    estimated_bpm: number | null;
    duration_sec: number | null;
}

export interface ResearchBriefSchema {
    intent_summary: string;
    mood: string;
    visual_style: string;
    audio_character: string;
    youtube_search_queries: string[];
    filter_overrides: FilterOverrides;
    negative_constraints: string[];
    reference_image_descriptions: string[];
    audio_metadata: AudioMetadata | null;
}

export interface ResearchBriefResponse {
    research_brief: ResearchBriefSchema;
    clarifying_question: string | null;
    is_complete: boolean;
}

// ── API methods ───────────────────────────────────────────────────

export const researchApi = {
    startJob: async (
        topic: string,
        depth: string = 'standard',
        researchBrief?: ResearchBriefSchema,
    ): Promise<ResearchJob> => {
        const body: Record<string, unknown> = { topic, research_depth: depth };
        if (researchBrief) {
            body.research_brief = researchBrief;
        }
        const response = await axios.post(`${API_BASE_URL}/start`, body);
        return response.data;
    },

    generateBrief: async (formData: FormData): Promise<ResearchBriefResponse> => {
        const response = await axios.post(`${API_BASE_URL}/brief`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 35000, // 35 sec (30 sec server + buffer)
        });
        return response.data;
    },

    listJobs: async (): Promise<ResearchJob[]> => {
        const response = await axios.get(API_BASE_URL);
        return response.data;
    },

    getJob: async (jobId: string): Promise<ResearchJobDetail> => {
        const response = await axios.get(`${API_BASE_URL}/${jobId}`);
        return response.data;
    },

    deleteJob: async (jobId: string): Promise<void> => {
        await axios.delete(`${API_BASE_URL}/${jobId}`);
    },
};
