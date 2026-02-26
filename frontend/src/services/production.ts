import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/production';

export interface ProductionJob {
    id: string;
    curation_job_id: string;
    status: string;
    num_scenes: number;
    num_tracks: number;
    created_at: string;
}

export const productionService = {
    startProduction: async (curationJobId: string): Promise<ProductionJob> => {
        const response = await axios.post(`${API_BASE_URL}/start`, {
            curation_job_id: curationJobId
        });
        return response.data;
    },

    getJob: async (jobId: string): Promise<any> => {
        const response = await axios.get(`${API_BASE_URL}/${jobId}`);
        return response.data;
    },

    getJobByCuration: async (curationJobId: string): Promise<any> => {
        const response = await axios.get(`${API_BASE_URL}/curation/${curationJobId}`);
        return response.data;
    }
};
