import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/bible';

export interface BibleCharacter {
    name: string;
    physical: string;
    wardrobe?: string;
    expressions?: string[];
    role?: string;
    ref_sheet_url?: string | null;
}

export interface BibleEnvironment {
    name: string;
    description: string;
    lighting?: string;
    mood?: string;
    time_of_day?: string;
    ref_sheet_url?: string | null;
}

export interface StyleLock {
    color_palette?: string[];
    visual_rules?: string[];
    negative_prompt?: string;
    looks?: string;
    angles?: string;
}

export interface SurrealMotif {
    symbol: string;
    meaning: string;
    visual_fragment: string;
}

export interface CameraSpecs {
    default_lens?: string;
    default_movement?: string;
    lighting_setup?: string;
}

export interface ProcessLogEntry {
    timestamp: string;
    agent: string;
    action: string;
    outcome: string;
}

export interface Bible {
    id: string;
    curation_job_id?: string | null;
    name: string;
    status: 'draft' | 'locked' | 'archived';
    characters?: BibleCharacter[];
    environments?: BibleEnvironment[];
    style_lock?: StyleLock;
    surreal_motifs?: SurrealMotif[];
    camera_specs?: CameraSpecs;
    character_sheet_urls?: string[];
    environment_sheet_urls?: string[];
    process_log?: ProcessLogEntry[];
    created_at?: string;
    updated_at?: string;
}

export interface BibleCreatePayload {
    name: string;
    curation_job_id?: string;
    characters?: BibleCharacter[];
    environments?: BibleEnvironment[];
    style_lock?: StyleLock;
    surreal_motifs?: SurrealMotif[];
    camera_specs?: CameraSpecs;
}

export interface BibleUpdatePayload {
    name?: string;
    characters?: BibleCharacter[];
    environments?: BibleEnvironment[];
    style_lock?: StyleLock;
    surreal_motifs?: SurrealMotif[];
    camera_specs?: CameraSpecs;
    character_sheet_urls?: string[];
    environment_sheet_urls?: string[];
}

export interface RippleEditPayload {
    directive: string;
    target_field?: string;
    preview_only?: boolean;
}

export interface RippleEditResult {
    original_scenes: any[];
    modified_scenes: any[];
    changes_summary: string;
}

// ── Inspiration Extraction Types ───────────────────────────────────

export interface InspirationCharacter {
    name: string;
    physical: string;
    wardrobe: string;
    expressions: string[];
    role: string;
    visual_keywords: string[];
    confidence: 'high' | 'medium' | 'low';
}

export interface InspirationEnvironment {
    name: string;
    description: string;
    lighting: string;
    mood: string;
    color_palette_description: string;
    time_of_day: string;
    confidence: 'high' | 'medium' | 'low';
}

export interface InspirationData {
    characters: InspirationCharacter[];
    environments: InspirationEnvironment[];
    style_signals: {
        color_grade: string;
        visual_aesthetic: string;
        cinematography_notes: string;
    };
    camera_signals: {
        dominant_shot_types: string[];
        movement_style: string;
        lens_feel: string;
    };
    source_video_url: string;
    source_video_title: string;
    error: string | null;
}

export interface ApplySuggestionsPayload {
    characters: InspirationCharacter[];
    environments: InspirationEnvironment[];
    style_signals?: InspirationData['style_signals'];
    camera_signals?: InspirationData['camera_signals'];
    apply_style: boolean;
    apply_camera: boolean;
    source_video_url: string;
    source_video_title: string;
}

// ── Bible Service ──────────────────────────────────────────────────

export const bibleService = {
    create: async (data: BibleCreatePayload): Promise<Bible> => {
        const response = await axios.post(`${API_BASE_URL}/`, data);
        return response.data;
    },

    list: async (): Promise<Bible[]> => {
        const response = await axios.get(`${API_BASE_URL}/`);
        return response.data;
    },

    get: async (bibleId: string): Promise<Bible> => {
        const response = await axios.get(`${API_BASE_URL}/${bibleId}`);
        return response.data;
    },

    update: async (bibleId: string, data: BibleUpdatePayload): Promise<Bible> => {
        const response = await axios.put(`${API_BASE_URL}/${bibleId}`, data);
        return response.data;
    },

    lock: async (bibleId: string): Promise<Bible> => {
        const response = await axios.put(`${API_BASE_URL}/${bibleId}/lock`);
        return response.data;
    },

    appendLog: async (bibleId: string, action: string, outcome?: string): Promise<Bible> => {
        const response = await axios.post(`${API_BASE_URL}/${bibleId}/log`, {
            agent: 'user',
            action,
            outcome: outcome || '',
        });
        return response.data;
    },

    delete: async (bibleId: string): Promise<void> => {
        await axios.delete(`${API_BASE_URL}/${bibleId}`);
    },

    extractInspiration: async (videoUrl: string): Promise<InspirationData> => {
        const response = await axios.post(`${API_BASE_URL}/extract-inspiration`, {
            video_url: videoUrl,
        });
        return response.data;
    },

    applySuggestions: async (
        bibleId: string,
        payload: ApplySuggestionsPayload
    ): Promise<Bible> => {
        const response = await axios.post(
            `${API_BASE_URL}/${bibleId}/apply-suggestions`,
            payload
        );
        return response.data;
    },
};

// Ripple edit calls go to curation API
const CURATION_API = 'http://localhost:8000/api/curation';

export const rippleService = {
    preview: async (jobId: string, data: RippleEditPayload): Promise<RippleEditResult> => {
        const response = await axios.post(`${CURATION_API}/${jobId}/ripple-edit`, {
            ...data,
            preview_only: true,
        });
        return response.data;
    },

    apply: async (jobId: string, data: RippleEditPayload): Promise<any> => {
        const response = await axios.post(`${CURATION_API}/${jobId}/ripple-apply`, data);
        return response.data;
    },
};
