import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/research';

export interface ResearchVideo {
    video_id: string;
    title: string;
    view_count: number | null;
    published_at: string | null;
    thumbnail_url?: string;
}

export interface ResearchJob {
    id: string;
    status: 'pending' | 'searching' | 'analyzing' | 'completed' | 'failed' | 'error';
    video_topic: string;
    research_depth: string;
    research_summary: string | null;
    created_at: string;
}

export interface ResearchJobDetail extends ResearchJob {
    videos: ResearchVideo[];
}

export const researchApi = {
    startJob: async (topic: string, depth: string = 'standard'): Promise<ResearchJob> => {
        const response = await axios.post(`${API_BASE_URL}/start`, { topic, research_depth: depth });
        return response.data;
    },

    listJobs: async (): Promise<ResearchJob[]> => {
        const response = await axios.get(API_BASE_URL);
        return response.data;
    },

    getJob: async (jobId: string): Promise<ResearchJobDetail> => {
        const response = await axios.get(`${API_BASE_URL}/${jobId}`);
        return response.data;
    }
};
