import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/knowledge';

export type KnowledgeCategory = 'music_video' | 'product_brand' | 'asmr' | 'general';
export type KnowledgeStatus = 'pending' | 'analyzing' | 'completed' | 'failed';

export interface KnowledgeEntry {
    id: string;
    youtube_url: string;
    video_id: string | null;
    category: KnowledgeCategory;
    status: KnowledgeStatus;
    standout_tip: string | null;
    exact_prompts: string[] | null;
    tool_names: string[] | null;
    workflow_steps: string[] | null;
    key_settings: Record<string, any> | null;
    category_specific: Record<string, any> | null;
    full_technique_summary: string | null;
    aggregated_resources: string[] | null;
    notion_links_found: string[];
    notion_links_alert: string | null;
    gemini_model_used: string | null;
    error_message: string | null;
    created_at: string | null;
    completed_at: string | null;
}

export interface IngestRequest {
    youtube_url: string;
    category: KnowledgeCategory;
    extra_context?: string;
}

export interface IngestResponse {
    entry_id: string;
    status: string;
    message: string;
}

export const knowledgeService = {
    ingest: async (req: IngestRequest): Promise<IngestResponse> => {
        const response = await axios.post(`${API_BASE}/ingest`, req);
        return response.data;
    },

    listEntries: async (params?: { category?: string; status?: string }): Promise<{ entries: KnowledgeEntry[]; total: number }> => {
        const response = await axios.get(`${API_BASE}/`, { params });
        return response.data;
    },

    getEntry: async (entryId: string): Promise<KnowledgeEntry> => {
        const response = await axios.get(`${API_BASE}/${entryId}`);
        return response.data;
    },
};
