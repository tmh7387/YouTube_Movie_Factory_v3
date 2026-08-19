import axios from 'axios';

const API = 'http://localhost:8000/api';

/**
 * A video generation model as described by the backend registry
 * (backend/app/services/video_models.py).
 */
export interface VideoModel {
    id: string;
    display_name: string;
    family: 'seedance' | 'kling' | 'wan' | 'minimax' | string;
    /** available = wired end to end · preview = adapter exists, verify first · planned = roadmap only */
    status: 'available' | 'preview' | 'planned' | string;
    transport: string;
    /** Prompt grammar this model expects — drives which director skill writes its prompts. */
    dialect: string;
    min_duration: number;
    max_duration: number;
    modes: string[];
    native_audio: boolean;
    max_reference_images: number;
    max_reference_videos: number;
    max_reference_audio: number;
    resolutions: string[];
    ratios: string[];
    supports_timestamps: boolean;
    strengths: string[];
    weaknesses: string[];
    cost_tier: 'low' | 'medium' | 'high' | string;
    default_mode: string;
    notes: string;
    /** Whether this deployment has the credentials the model's transport needs. */
    configured: boolean;
}

export interface VideoModelCatalogue {
    default: string;
    models: VideoModel[];
}

export interface ModelRecommendation {
    model: string;
    display_name: string;
    mode: string;
    confidence: number;
    reasoning: string;
    alternatives: { model: string; display_name: string; score: number }[];
}

export const modelService = {
    listVideoModels: async (includePlanned = true): Promise<VideoModelCatalogue> => {
        const res = await axios.get(`${API}/models/video`, {
            params: { include_planned: includePlanned },
        });
        return res.data;
    },

    getVideoModel: async (modelId: string): Promise<VideoModel> => {
        const res = await axios.get(`${API}/models/video/${modelId}`);
        return res.data;
    },

    recommend: async (
        visualPrompt: string,
        motionPrompt = '',
        preferredModel?: string,
    ): Promise<ModelRecommendation> => {
        const res = await axios.post(`${API}/models/video/recommend`, {
            visual_prompt: visualPrompt,
            motion_prompt: motionPrompt,
            preferred_model: preferredModel ?? null,
        });
        return res.data;
    },
};

/** Models the user can actually launch a job with right now. */
export function usableModels(models: VideoModel[]): VideoModel[] {
    return models.filter(m => m.status !== 'planned' && m.configured);
}

/** Short "why you'd pick this" line for the picker. */
export function modelSummary(m: VideoModel): string {
    const bits: string[] = [`up to ${m.max_duration}s`];
    if (m.native_audio) bits.push('native audio');
    if (m.supports_timestamps) bits.push('timestamps');
    if (m.max_reference_images > 0) bits.push(`${m.max_reference_images} image refs`);
    bits.push(`${m.cost_tier} cost`);
    return bits.join(' · ');
}

export const COST_TIER_COLORS: Record<string, string> = {
    low: 'text-green-400',
    medium: 'text-yellow-400',
    high: 'text-orange-400',
};
