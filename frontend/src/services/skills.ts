import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/skills';

export type SkillDifficulty = 'beginner' | 'intermediate' | 'advanced';

export interface Skill {
    id: string;
    slug: string;
    name: string;
    description: string | null;
    category: string;
    applicable_video_types: string[] | null;
    tags: string[] | null;
    prompt_template: string | null;
    example_prompts: string[] | null;
    workflow_steps: string[] | null;
    tools_tested_with: string[] | null;
    difficulty: SkillDifficulty | null;
    confidence_score: number | null;
    usage_count: number;
    source_video_url: string | null;
    skill_file_path: string | null;
    created_at: string | null;
    // Full detail only
    skill_body?: string;
    source_knowledge_entry_id?: string;
}

export interface SkillFilters {
    category?: string;
    video_type?: string;
    tags?: string;
    difficulty?: SkillDifficulty;
    limit?: number;
}

export const skillsService = {
    listSkills: async (filters?: SkillFilters): Promise<{ skills: Skill[]; total: number }> => {
        const response = await axios.get(`${API_BASE}/`, { params: filters });
        return response.data;
    },

    getSkill: async (idOrSlug: string): Promise<Skill> => {
        const response = await axios.get(`${API_BASE}/${idOrSlug}`);
        return response.data;
    },

    getSkillsForProduction: async (videoType: string, limit = 10): Promise<{
        video_type: string;
        skill_count: number;
        skills: Skill[];
        prompt_injection_block: string;
    }> => {
        const response = await axios.get(`${API_BASE}/for-production`, { params: { video_type: videoType, limit } });
        return response.data;
    },
};
