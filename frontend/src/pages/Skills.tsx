import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Zap,
    Loader2,
    Star,
    Filter,
    X,
    ChevronRight,
    FileText,
    Tag,
    Wrench,
    ListOrdered,
    TrendingUp,
    Clock,
    BarChart3,
    ExternalLink,
    Pencil,
    Trash2,
    Save,
    CalendarDays,
} from 'lucide-react';
import { skillsService } from '../services/skills';
import type { Skill, SkillDifficulty } from '../services/skills';

const CATEGORIES = [
    { value: '', label: 'All Categories' },
    { value: 'general', label: 'General' },
    { value: 'music_video', label: 'Music Video' },
    { value: 'product_brand', label: 'Product / Brand' },
    { value: 'asmr', label: 'ASMR' },
];

const DIFFICULTIES: { value: SkillDifficulty | ''; label: string; color: string }[] = [
    { value: '', label: 'Any Level', color: '' },
    { value: 'beginner', label: 'Beginner', color: 'text-green-400' },
    { value: 'intermediate', label: 'Intermediate', color: 'text-yellow-400' },
    { value: 'advanced', label: 'Advanced', color: 'text-red-400' },
];

const DIFFICULTY_COLORS: Record<string, string> = {
    beginner:     'bg-green-500/15 text-green-400 border-green-500/25',
    intermediate: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25',
    advanced:     'bg-red-500/15 text-red-400 border-red-500/25',
};

const Skills: React.FC = () => {
    const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
    const [filterCategory, setFilterCategory] = useState('');
    const [filterDifficulty, setFilterDifficulty] = useState<SkillDifficulty | ''>('');
    const queryClient = useQueryClient();

    const { data, isLoading } = useQuery({
        queryKey: ['skills', filterCategory, filterDifficulty],
        queryFn: () => skillsService.listSkills({
            category: filterCategory || undefined,
            difficulty: filterDifficulty || undefined,
        }),
    });

    // When a skill card is clicked, fetch full details
    const { data: fullSkill, isLoading: fullLoading } = useQuery({
        queryKey: ['skill', selectedSkill?.id],
        queryFn: () => skillsService.getSkill(selectedSkill!.id),
        enabled: !!selectedSkill,
    });

    const skills = data?.skills ?? [];

    return (
        <div className="p-8 max-w-7xl mx-auto">
            {/* Header */}
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center">
                        <Zap className="w-6 h-6 text-violet-400" />
                    </div>
                    Production Skills
                </h1>
                <p className="text-gray-400 mt-2 max-w-lg">
                    Reusable, tool-agnostic production techniques synthesized from tutorial analysis. These are injected into Claude during brief generation.
                </p>
            </header>

            {/* Filters */}
            <div className="flex flex-wrap gap-3 mb-8 p-4 bg-white/5 border border-white/10 rounded-2xl">
                <div className="flex items-center gap-2 text-gray-400 text-sm font-medium mr-2">
                    <Filter className="w-4 h-4" />
                    Filter:
                </div>

                {/* Category filter */}
                <div className="flex gap-1.5 flex-wrap">
                    {CATEGORIES.map(c => (
                        <button
                            key={c.value}
                            onClick={() => setFilterCategory(c.value)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                                filterCategory === c.value
                                    ? 'bg-violet-600 text-white'
                                    : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white border border-white/10'
                            }`}
                        >
                            {c.label}
                        </button>
                    ))}
                </div>

                <div className="w-px bg-white/10 self-stretch mx-1" />

                {/* Difficulty filter */}
                <div className="flex gap-1.5">
                    {DIFFICULTIES.map(d => (
                        <button
                            key={d.value}
                            onClick={() => setFilterDifficulty(d.value as SkillDifficulty | '')}
                            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                                filterDifficulty === d.value
                                    ? 'bg-violet-600 text-white'
                                    : `bg-white/5 ${d.color || 'text-gray-400'} hover:bg-white/10 border border-white/10`
                            }`}
                        >
                            {d.label}
                        </button>
                    ))}
                </div>

                {(filterCategory || filterDifficulty) && (
                    <button
                        onClick={() => { setFilterCategory(''); setFilterDifficulty(''); }}
                        className="ml-auto flex items-center gap-1 text-xs text-gray-500 hover:text-white transition-colors"
                    >
                        <X className="w-3 h-3" />
                        Clear
                    </button>
                )}
            </div>

            {/* Stats bar */}
            <div className="flex gap-6 mb-6 text-sm text-gray-400">
                <span className="flex items-center gap-1.5">
                    <BarChart3 className="w-4 h-4 text-violet-400" />
                    <strong className="text-white">{data?.total ?? 0}</strong> skills
                </span>
                {skills.length > 0 && (
                    <span className="flex items-center gap-1.5">
                        <TrendingUp className="w-4 h-4 text-green-400" />
                        Avg confidence: {(skills.reduce((a, s) => a + (s.confidence_score ?? 0), 0) / skills.length).toFixed(2)}
                    </span>
                )}
            </div>

            {/* Grid + Side Panel */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                {/* Skills grid */}
                <div className="lg:col-span-3">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-24">
                            <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
                        </div>
                    ) : skills.length === 0 ? (
                        <div className="text-center py-24 border-2 border-dashed border-white/10 rounded-2xl">
                            <Zap className="w-12 h-12 text-gray-700 mx-auto mb-4" />
                            <h3 className="text-gray-400 text-lg font-medium">No skills yet</h3>
                            <p className="text-gray-600 text-sm mt-2">
                                Ingest tutorials in the Knowledge tab to auto-generate skills.
                            </p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {skills.map((skill) => (
                                <motion.div
                                    key={skill.id}
                                    whileHover={{ scale: 1.01, y: -2 }}
                                    onClick={() => setSelectedSkill(skill)}
                                    className={`p-5 rounded-2xl cursor-pointer border transition-all ${
                                        selectedSkill?.id === skill.id
                                            ? 'bg-violet-600/15 border-violet-500/50 shadow-lg shadow-violet-500/10'
                                            : 'bg-white/5 border-white/10 hover:bg-white/8 hover:border-white/20'
                                    }`}
                                >
                                    <div className="flex justify-between items-start mb-3">
                                        <div className="flex gap-2 flex-wrap">
                                            {skill.difficulty && (
                                                <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-tighter border ${DIFFICULTY_COLORS[skill.difficulty] || ''}`}>
                                                    {skill.difficulty}
                                                </span>
                                            )}
                                            {skill.category && (
                                                <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-tighter bg-white/10 text-gray-400 border border-white/10">
                                                    {skill.category.replace('_', ' ')}
                                                </span>
                                            )}
                                        </div>
                                        <ChevronRight className="w-4 h-4 text-gray-600 flex-none" />
                                    </div>

                                    <h3 className="text-white font-semibold text-base leading-snug mb-1.5">{skill.name}</h3>
                                    {skill.description && (
                                        <p className="text-gray-400 text-sm line-clamp-2 leading-relaxed">{skill.description}</p>
                                    )}

                                    <div className="mt-4 flex items-center gap-4 text-xs text-gray-600 flex-wrap">
                                        {skill.confidence_score != null && (
                                            <span className="flex items-center gap-1">
                                                <Star className="w-3 h-3 text-yellow-500" />
                                                {(skill.confidence_score * 100).toFixed(0)}%
                                            </span>
                                        )}
                                        <span className="flex items-center gap-1">
                                            <TrendingUp className="w-3 h-3" />
                                            {skill.usage_count} uses
                                        </span>
                                        {skill.tools_tested_with && (
                                            <span className="flex items-center gap-1">
                                                <Wrench className="w-3 h-3" />
                                                {skill.tools_tested_with.length} tools
                                            </span>
                                        )}
                                        {skill.created_at && (
                                            <span className="flex items-center gap-1">
                                                <CalendarDays className="w-3 h-3" />
                                                {new Date(skill.created_at).toLocaleDateString()}
                                            </span>
                                        )}
                                    </div>

                                    {skill.tags && skill.tags.length > 0 && (
                                        <div className="mt-3 flex gap-1.5 flex-wrap">
                                            {skill.tags.slice(0, 4).map((t, i) => (
                                                <span key={i} className="px-1.5 py-0.5 rounded text-[10px] text-gray-500 bg-white/5">
                                                    #{t}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </motion.div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Side detail panel */}
                <div className="lg:col-span-2">
                    <AnimatePresence mode="wait">
                        {selectedSkill ? (
                            <motion.div
                                key={selectedSkill.id}
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                className="sticky top-8 bg-white/5 border border-white/10 rounded-2xl overflow-hidden max-h-[calc(100vh-10rem)] overflow-y-auto"
                            >
                                {fullLoading ? (
                                    <div className="flex items-center justify-center py-16">
                                        <Loader2 className="w-6 h-6 animate-spin text-violet-500" />
                                    </div>
                                ) : fullSkill ? (
                                    <SkillDetail
                                        skill={fullSkill}
                                        onClose={() => setSelectedSkill(null)}
                                        onDelete={async () => {
                                            await skillsService.deleteSkill(fullSkill.id);
                                            setSelectedSkill(null);
                                            queryClient.invalidateQueries({ queryKey: ['skills'] });
                                        }}
                                        onUpdate={async (data) => {
                                            await skillsService.updateSkill(fullSkill.id, data);
                                            queryClient.invalidateQueries({ queryKey: ['skills'] });
                                            queryClient.invalidateQueries({ queryKey: ['skill', fullSkill.id] });
                                        }}
                                    />
                                ) : null}
                            </motion.div>
                        ) : (
                            <div className="sticky top-8 flex items-center justify-center border-2 border-dashed border-white/10 rounded-2xl p-12 text-center min-h-[300px]">
                                <div>
                                    <Zap className="w-10 h-10 text-gray-700 mx-auto mb-3" />
                                    <p className="text-gray-500 text-sm">Click a skill to view details</p>
                                </div>
                            </div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

interface SkillDetailProps {
    skill: Skill;
    onClose: () => void;
    onDelete: () => Promise<void>;
    onUpdate: (data: Partial<Skill>) => Promise<void>;
}

const SkillDetail: React.FC<SkillDetailProps> = ({ skill, onClose, onDelete, onUpdate }) => {
    const [editing, setEditing] = useState(false);
    const [confirmDelete, setConfirmDelete] = useState(false);
    const [saving, setSaving] = useState(false);
    const [deleting, setDeleting] = useState(false);

    // Edit form state
    const [editName, setEditName] = useState(skill.name);
    const [editDesc, setEditDesc] = useState(skill.description || '');
    const [editTemplate, setEditTemplate] = useState(skill.prompt_template || '');
    const [editSteps, setEditSteps] = useState((skill.workflow_steps || []).join('\n'));
    const [editTags, setEditTags] = useState((skill.tags || []).join(', '));
    const [editDifficulty, setEditDifficulty] = useState(skill.difficulty || 'intermediate');
    const [editBody, setEditBody] = useState(skill.skill_body || '');

    const handleSave = async () => {
        setSaving(true);
        try {
            await onUpdate({
                name: editName,
                description: editDesc,
                prompt_template: editTemplate || null,
                workflow_steps: editSteps.split('\n').map(s => s.trim()).filter(Boolean),
                tags: editTags.split(',').map(s => s.trim()).filter(Boolean),
                difficulty: editDifficulty as any,
                skill_body: editBody || null,
            });
            setEditing(false);
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async () => {
        setDeleting(true);
        try { await onDelete(); } finally { setDeleting(false); }
    };

    return (
        <div className="divide-y divide-white/10">
            {/* Header */}
            <div className="p-6 bg-gradient-to-br from-violet-600/10 to-indigo-600/5">
                <div className="flex justify-between items-start mb-3">
                    <div className="flex gap-2 flex-wrap">
                        {skill.difficulty && (
                            <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-tighter border ${DIFFICULTY_COLORS[skill.difficulty] || ''}`}>
                                {skill.difficulty}
                            </span>
                        )}
                        {skill.category && (
                            <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-tighter bg-white/10 text-gray-400 border border-white/10">
                                {skill.category.replace('_', ' ')}
                            </span>
                        )}
                    </div>
                    <div className="flex items-center gap-1">
                        <button onClick={() => { setEditing(!editing); setConfirmDelete(false); }} className="text-gray-500 hover:text-violet-400 transition-colors p-1.5 rounded-lg hover:bg-white/10" title="Edit">
                            <Pencil className="w-4 h-4" />
                        </button>
                        <button onClick={() => { setConfirmDelete(!confirmDelete); setEditing(false); }} className="text-gray-500 hover:text-red-400 transition-colors p-1.5 rounded-lg hover:bg-white/10" title="Delete">
                            <Trash2 className="w-4 h-4" />
                        </button>
                        <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors p-1.5 rounded-lg hover:bg-white/10">
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Delete confirmation */}
                <AnimatePresence>
                    {confirmDelete && (
                        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mb-3 p-3 bg-red-500/10 border border-red-500/30 rounded-xl">
                            <p className="text-red-300 text-sm mb-2">Delete <strong>{skill.name}</strong>? Removes from database and disk. Cannot be undone.</p>
                            <div className="flex gap-2">
                                <button onClick={handleDelete} disabled={deleting} className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-lg transition-colors disabled:opacity-50">
                                    {deleting ? 'Deleting...' : 'Yes, delete'}
                                </button>
                                <button onClick={() => setConfirmDelete(false)} className="px-3 py-1.5 bg-white/10 text-gray-300 text-xs font-semibold rounded-lg hover:bg-white/15 transition-colors">Cancel</button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {editing ? (
                    <input value={editName} onChange={e => setEditName(e.target.value)} className="w-full text-xl font-bold text-white bg-white/10 border border-white/20 rounded-lg px-3 py-2 mb-2 focus:outline-none focus:border-violet-500" />
                ) : (
                    <h2 className="text-xl font-bold text-white leading-snug mb-2">{skill.name}</h2>
                )}

                {editing ? (
                    <textarea value={editDesc} onChange={e => setEditDesc(e.target.value)} rows={3} className="w-full text-sm text-gray-300 bg-white/10 border border-white/20 rounded-lg px-3 py-2 focus:outline-none focus:border-violet-500 resize-none" />
                ) : (
                    skill.description && <p className="text-gray-300 text-sm leading-relaxed">{skill.description}</p>
                )}

                {/* Meta row */}
                <div className="flex gap-4 mt-4 text-xs text-gray-500 flex-wrap">
                    {skill.confidence_score != null && (
                        <span className="flex items-center gap-1"><Star className="w-3 h-3 text-yellow-500" />{(skill.confidence_score * 100).toFixed(0)}% confidence</span>
                    )}
                    <span className="flex items-center gap-1"><TrendingUp className="w-3 h-3" />{skill.usage_count} uses</span>
                    {skill.created_at && (
                        <span className="flex items-center gap-1"><CalendarDays className="w-3 h-3" />{new Date(skill.created_at).toLocaleDateString()}</span>
                    )}
                </div>
                {/* Source link */}
                {skill.source_video_url && (
                    <a href={skill.source_video_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 mt-3 text-xs text-violet-400 hover:text-violet-300 transition-colors">
                        <ExternalLink className="w-3 h-3" />Source tutorial
                    </a>
                )}
            </div>

            {/* Prompt template */}
            {(editing || skill.prompt_template) && (
                <div className="p-5">
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2"><FileText className="w-3.5 h-3.5" /> Prompt Template</h3>
                    {editing ? (
                        <textarea value={editTemplate} onChange={e => setEditTemplate(e.target.value)} rows={5} className="w-full text-xs text-gray-300 font-mono bg-black/40 border border-white/10 rounded-xl p-4 focus:outline-none focus:border-violet-500 resize-y" />
                    ) : (
                        <div className="group relative">
                            <pre className="text-gray-300 text-xs leading-relaxed bg-black/40 rounded-xl p-4 whitespace-pre-wrap border border-white/5 font-mono">{skill.prompt_template}</pre>
                            <button onClick={() => navigator.clipboard.writeText(skill.prompt_template!)} className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-xs text-gray-500 hover:text-violet-400 px-2 py-1 rounded bg-white/5">Copy</button>
                        </div>
                    )}
                </div>
            )}

            {/* Workflow steps */}
            {(editing || (skill.workflow_steps && skill.workflow_steps.length > 0)) && (
                <div className="p-5">
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2"><ListOrdered className="w-3.5 h-3.5" /> Workflow</h3>
                    {editing ? (
                        <textarea value={editSteps} onChange={e => setEditSteps(e.target.value)} rows={6} placeholder="One step per line" className="w-full text-sm text-gray-300 bg-black/40 border border-white/10 rounded-xl p-4 focus:outline-none focus:border-violet-500 resize-y" />
                    ) : (
                        <ol className="space-y-2">
                            {skill.workflow_steps!.map((step, i) => (
                                <li key={i} className="flex gap-2.5 text-sm text-gray-300">
                                    <span className="flex-none w-5 h-5 rounded-full bg-violet-500/20 flex items-center justify-center text-[10px] font-bold text-violet-400 mt-0.5">{i + 1}</span>
                                    {step}
                                </li>
                            ))}
                        </ol>
                    )}
                </div>
            )}

            {/* Tags (edit mode) */}
            {editing && (
                <div className="p-5">
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2"><Tag className="w-3.5 h-3.5" /> Tags</h3>
                    <input value={editTags} onChange={e => setEditTags(e.target.value)} placeholder="tag1, tag2, tag3" className="w-full text-sm text-gray-300 bg-black/40 border border-white/10 rounded-xl px-4 py-2 focus:outline-none focus:border-violet-500" />
                </div>
            )}

            {/* Difficulty (edit mode) */}
            {editing && (
                <div className="p-5">
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Difficulty</h3>
                    <select value={editDifficulty} onChange={e => setEditDifficulty(e.target.value)} className="text-sm text-gray-300 bg-black/40 border border-white/10 rounded-xl px-4 py-2 focus:outline-none focus:border-violet-500">
                        <option value="beginner">Beginner</option>
                        <option value="intermediate">Intermediate</option>
                        <option value="advanced">Advanced</option>
                    </select>
                </div>
            )}

            {/* Example prompts (read-only) */}
            {!editing && skill.example_prompts && skill.example_prompts.length > 0 && (
                <div className="p-5">
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2"><Tag className="w-3.5 h-3.5" /> Example Prompts</h3>
                    <div className="space-y-2">
                        {skill.example_prompts.map((p, i) => (
                            <div key={i} className="group relative bg-black/40 border border-white/5 rounded-xl p-3 hover:border-violet-500/30 transition-colors">
                                <p className="text-gray-300 text-xs leading-relaxed font-mono">{p}</p>
                                <button onClick={() => navigator.clipboard.writeText(p)} className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-xs text-gray-500 hover:text-violet-400 px-1.5 py-0.5 rounded bg-white/5">Copy</button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Tools (read-only) */}
            {!editing && skill.tools_tested_with && skill.tools_tested_with.length > 0 && (
                <div className="p-5">
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2"><Wrench className="w-3.5 h-3.5" /> Tested With</h3>
                    <div className="flex flex-wrap gap-2">
                        {skill.tools_tested_with.map((t, i) => (
                            <span key={i} className="px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-500/15 text-blue-300 border border-blue-500/20">{t}</span>
                        ))}
                    </div>
                </div>
            )}

            {/* Full SKILL.md body */}
            {(editing || skill.skill_body) && (
                <div className="p-5">
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2"><FileText className="w-3.5 h-3.5" /> Full SKILL.md</h3>
                    {editing ? (
                        <textarea value={editBody} onChange={e => setEditBody(e.target.value)} rows={12} className="w-full text-xs text-gray-400 font-mono bg-black/40 border border-white/10 rounded-xl p-4 focus:outline-none focus:border-violet-500 resize-y" />
                    ) : (
                        <pre className="text-gray-400 text-xs leading-relaxed bg-black/40 rounded-xl p-4 whitespace-pre-wrap border border-white/5 overflow-auto max-h-64">{skill.skill_body}</pre>
                    )}
                </div>
            )}

            {/* Save / Cancel bar */}
            {editing && (
                <div className="p-5 flex gap-3">
                    <button onClick={handleSave} disabled={saving} className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white text-sm font-semibold rounded-xl transition-colors disabled:opacity-50">
                        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                        {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                    <button onClick={() => setEditing(false)} className="px-4 py-2 bg-white/10 text-gray-300 text-sm font-semibold rounded-xl hover:bg-white/15 transition-colors">Cancel</button>
                </div>
            )}
        </div>
    );
};

export default Skills;
