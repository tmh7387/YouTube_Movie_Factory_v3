import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/production';

export interface ProductionJob {
    id: string;
    curation_job_id: string;
    status: string;
    num_scenes: number;
    num_tracks: number;
    created_at: string;
    upscale_enabled: boolean;
}

export interface StartProductionRequest {
    curation_job_id: string;
    video_engine?: 'kling' | 'seedance';
    image_engine?: 'nanabanana' | 'gpt_image_2';
    upscale_enabled?: boolean;
}

export const productionService = {
    startProduction: async (req: StartProductionRequest): Promise<ProductionJob> => {
        const response = await axios.post(`${API_BASE_URL}/start`, {
            curation_job_id: req.curation_job_id,
            video_engine: req.video_engine ?? 'kling',
            image_engine: req.image_engine ?? 'nanabanana',
            upscale_enabled: req.upscale_enabled ?? false,
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
    },

    // Phase 3 — per-scene download
    getSceneDownloadUrl: (jobId: string, sceneId: string): string =>
        `${API_BASE_URL}/${jobId}/scenes/${sceneId}/download`,

    getSceneImageDownloadUrl: (jobId: string, sceneId: string): string =>
        `${API_BASE_URL}/${jobId}/scenes/${sceneId}/download-image`,

    getZipExportUrl: (jobId: string): string =>
        `${API_BASE_URL}/${jobId}/export.zip`,

    // Phase 2 — character management
    createCharacter: async (
        jobId: string,
        name: string,
        description: string,
        referenceImages: File[],
    ): Promise<any> => {
        const form = new FormData();
        form.append('name', name);
        form.append('description', description);
        for (const f of referenceImages) {
            form.append('reference_images', f);
        }
        const response = await axios.post(`${API_BASE_URL}/${jobId}/characters`, form, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    listCharacters: async (jobId: string): Promise<any[]> => {
        const response = await axios.get(`${API_BASE_URL}/${jobId}/characters`);
        return response.data;
    },
};
