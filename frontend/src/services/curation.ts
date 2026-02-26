import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/curation';

export interface StoryboardScene {
    scene_index: number;
    narration: string;
    visual_prompt: string;
    pacing: string;
    duration: number;
}

export interface CreativeBrief {
    title: string;
    hook: string;
    narrative_goal: string;
    music_mood: string;
    color_palette: string[];
    storyboard: StoryboardScene[];
    error?: string;
}

export interface CurationJob {
    id: string;
    research_job_id: string;
    status: 'pending' | 'generating_brief' | 'completed' | 'error';
    creative_brief?: CreativeBrief;
    num_scenes?: number;
}

export const curationService = {
    startCuration: async (researchJobId: string, selectedVideoIds?: string[]): Promise<CurationJob> => {
        const response = await axios.post(`${API_BASE_URL}/start`, {
            research_job_id: researchJobId,
            selected_video_ids: selectedVideoIds
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
    }
};
