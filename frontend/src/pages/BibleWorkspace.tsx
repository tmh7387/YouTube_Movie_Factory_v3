import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { BookOpen, Plus, Lock, Trash2, Palette, Users, MapPin, Camera, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import { bibleService } from '../services/bible';
import type { BibleCreatePayload } from '../services/bible';

export default function BibleWorkspace() {
    const queryClient = useQueryClient();
    const [selectedBibleId, setSelectedBibleId] = useState<string | null>(null);
    const [editMode, setEditMode] = useState(false);
    const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
        characters: true, environments: true, style: true, motifs: false, camera: false,
    });

    const { data: bibles = [], isLoading } = useQuery({ queryKey: ['bibles'], queryFn: bibleService.list });
    const selectedBible = bibles.find(b => b.id === selectedBibleId);

    const createMutation = useMutation({
        mutationFn: (data: BibleCreatePayload) => bibleService.create(data),
        onSuccess: (bible) => { queryClient.invalidateQueries({ queryKey: ['bibles'] }); setSelectedBibleId(bible.id); },
    });



    const lockMutation = useMutation({
        mutationFn: (id: string) => bibleService.lock(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['bibles'] }),
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => bibleService.delete(id),
        onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['bibles'] }); setSelectedBibleId(null); },
    });

    const toggleSection = (key: string) => setExpandedSections(prev => ({ ...prev, [key]: !prev[key] }));

    const handleCreate = () => {
        const name = prompt('Bible name:');
        if (name) createMutation.mutate({ name });
    };

    if (isLoading) return <div className="flex items-center justify-center h-full text-gray-400">Loading bibles...</div>;

    return (
        <div className="flex h-full">
            {/* Sidebar — Bible List */}
            <div className="w-72 border-r border-white/5 bg-gray-900/50 flex flex-col">
                <div className="p-4 border-b border-white/5 flex items-center justify-between">
                    <h2 className="text-sm font-bold text-gray-300 uppercase tracking-wider">Bibles</h2>
                    <button onClick={handleCreate} className="p-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 transition-colors" title="New Bible">
                        <Plus className="w-4 h-4" />
                    </button>
                </div>
                <div className="flex-1 overflow-auto p-2 space-y-1">
                    {bibles.map(b => (
                        <button key={b.id} onClick={() => { setSelectedBibleId(b.id); setEditMode(false); }}
                            className={`w-full text-left px-3 py-2.5 rounded-lg transition-all text-sm ${
                                selectedBibleId === b.id ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' : 'text-gray-400 hover:bg-gray-800/50'
                            }`}>
                            <div className="flex items-center gap-2">
                                <BookOpen className="w-4 h-4 shrink-0" />
                                <span className="truncate font-medium">{b.name}</span>
                                {b.status === 'locked' && <Lock className="w-3 h-3 text-amber-400 shrink-0" />}
                            </div>
                            <p className="text-[10px] text-gray-600 mt-1">
                                {(b.characters?.length || 0)} chars · {(b.environments?.length || 0)} envs · {b.status}
                            </p>
                        </button>
                    ))}
                    {bibles.length === 0 && <p className="text-gray-600 text-xs text-center py-8">No bibles yet</p>}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto">
                {!selectedBible ? (
                    <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-4">
                        <BookOpen className="w-16 h-16 text-gray-700" />
                        <p className="text-lg">Select or create a Pre-Production Bible</p>
                        <button onClick={handleCreate} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors flex items-center gap-2">
                            <Plus className="w-4 h-4" /> New Bible
                        </button>
                    </div>
                ) : (
                    <div className="max-w-4xl mx-auto p-8 space-y-6">
                        {/* Header */}
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-2xl font-bold text-white">{selectedBible.name}</h1>
                                <p className="text-sm text-gray-500 mt-1">Status: <span className={selectedBible.status === 'locked' ? 'text-amber-400' : 'text-green-400'}>{selectedBible.status}</span></p>
                            </div>
                            <div className="flex gap-2">
                                {selectedBible.status === 'draft' && (
                                    <>
                                        <button onClick={() => setEditMode(!editMode)} className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${editMode ? 'bg-green-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}>
                                            {editMode ? 'Viewing' : 'Edit'}
                                        </button>
                                        <button onClick={() => lockMutation.mutate(selectedBible.id)} className="px-3 py-1.5 rounded-lg text-sm bg-amber-600/20 text-amber-400 hover:bg-amber-600/30 flex items-center gap-1">
                                            <Lock className="w-3 h-3" /> Lock
                                        </button>
                                        <button onClick={() => { if (confirm('Delete this bible?')) deleteMutation.mutate(selectedBible.id); }}
                                            className="px-3 py-1.5 rounded-lg text-sm bg-red-600/20 text-red-400 hover:bg-red-600/30">
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>

                        {/* Characters Section */}
                        <CollapsibleSection title="Characters" icon={Users} count={selectedBible.characters?.length || 0}
                            expanded={expandedSections.characters} onToggle={() => toggleSection('characters')}>
                            <div className="grid gap-3">
                                {(selectedBible.characters || []).map((char, i) => (
                                    <div key={i} className="bg-gray-800/50 rounded-xl p-4 border border-white/5">
                                        <h4 className="font-semibold text-white">{char.name} <span className="text-xs text-gray-500 ml-2">{char.role}</span></h4>
                                        <p className="text-sm text-gray-400 mt-1">{char.physical}</p>
                                        {char.wardrobe && <p className="text-xs text-gray-500 mt-1">👗 {char.wardrobe}</p>}
                                        {char.expressions && <p className="text-xs text-gray-500 mt-1">😊 {char.expressions.join(', ')}</p>}
                                    </div>
                                ))}
                                {(!selectedBible.characters || selectedBible.characters.length === 0) && (
                                    <p className="text-gray-600 text-sm">No characters defined yet</p>
                                )}
                            </div>
                        </CollapsibleSection>

                        {/* Environments Section */}
                        <CollapsibleSection title="Environments" icon={MapPin} count={selectedBible.environments?.length || 0}
                            expanded={expandedSections.environments} onToggle={() => toggleSection('environments')}>
                            <div className="grid gap-3">
                                {(selectedBible.environments || []).map((env, i) => (
                                    <div key={i} className="bg-gray-800/50 rounded-xl p-4 border border-white/5">
                                        <h4 className="font-semibold text-white">{env.name}</h4>
                                        <p className="text-sm text-gray-400 mt-1">{env.description}</p>
                                        <div className="flex gap-4 mt-2 text-xs text-gray-500">
                                            {env.lighting && <span>💡 {env.lighting}</span>}
                                            {env.mood && <span>🎭 {env.mood}</span>}
                                            {env.time_of_day && <span>🕐 {env.time_of_day}</span>}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CollapsibleSection>

                        {/* Style Lock Section */}
                        <CollapsibleSection title="Style Lock" icon={Palette} expanded={expandedSections.style} onToggle={() => toggleSection('style')}>
                            {selectedBible.style_lock ? (
                                <div className="space-y-3">
                                    {selectedBible.style_lock.color_palette && (
                                        <div>
                                            <p className="text-xs text-gray-500 uppercase mb-2">Color Palette</p>
                                            <div className="flex gap-2">
                                                {selectedBible.style_lock.color_palette.map((c, i) => (
                                                    <div key={i} className="flex flex-col items-center gap-1">
                                                        <div className="w-10 h-10 rounded-lg shadow-lg border border-white/10" style={{ backgroundColor: c }} />
                                                        <span className="text-[10px] text-gray-500 font-mono">{c}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    {selectedBible.style_lock.visual_rules && (
                                        <div>
                                            <p className="text-xs text-gray-500 uppercase mb-1">Visual Rules</p>
                                            <ul className="text-sm text-gray-400 space-y-1">
                                                {selectedBible.style_lock.visual_rules.map((r, i) => <li key={i}>• {r}</li>)}
                                            </ul>
                                        </div>
                                    )}
                                    {selectedBible.style_lock.negative_prompt && (
                                        <div>
                                            <p className="text-xs text-gray-500 uppercase mb-1">Negative Prompt</p>
                                            <p className="text-sm text-red-400/80 bg-red-900/20 rounded-lg p-2">{selectedBible.style_lock.negative_prompt}</p>
                                        </div>
                                    )}
                                </div>
                            ) : <p className="text-gray-600 text-sm">No style lock defined</p>}
                        </CollapsibleSection>

                        {/* Camera Specs */}
                        <CollapsibleSection title="Camera Specs" icon={Camera} expanded={expandedSections.camera} onToggle={() => toggleSection('camera')}>
                            {selectedBible.camera_specs ? (
                                <div className="grid grid-cols-3 gap-4">
                                    {Object.entries(selectedBible.camera_specs).map(([k, v]) => (
                                        <div key={k} className="bg-gray-800/50 rounded-lg p-3 border border-white/5">
                                            <p className="text-[10px] text-gray-500 uppercase">{k.replace(/_/g, ' ')}</p>
                                            <p className="text-sm text-gray-300 mt-1">{String(v)}</p>
                                        </div>
                                    ))}
                                </div>
                            ) : <p className="text-gray-600 text-sm">No camera specs defined</p>}
                        </CollapsibleSection>

                        {/* Surreal Motifs */}
                        <CollapsibleSection title="Surreal Motifs" icon={Sparkles} count={selectedBible.surreal_motifs?.length || 0}
                            expanded={expandedSections.motifs} onToggle={() => toggleSection('motifs')}>
                            <div className="grid gap-2">
                                {(selectedBible.surreal_motifs || []).map((m, i) => (
                                    <div key={i} className="bg-gray-800/50 rounded-lg p-3 border border-white/5 flex gap-3">
                                        <span className="text-xl">✨</span>
                                        <div>
                                            <p className="text-sm font-medium text-white">{m.symbol}</p>
                                            <p className="text-xs text-gray-500">{m.meaning}</p>
                                            <p className="text-xs text-gray-400 italic mt-1">"{m.visual_fragment}"</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CollapsibleSection>

                        {/* Process Log */}
                        {selectedBible.process_log && selectedBible.process_log.length > 0 && (
                            <div className="border-t border-white/5 pt-4">
                                <p className="text-xs text-gray-500 uppercase mb-2">Process Log</p>
                                <div className="space-y-1 max-h-40 overflow-auto">
                                    {selectedBible.process_log.map((entry, i) => (
                                        <div key={i} className="text-xs text-gray-500 flex gap-2">
                                            <span className="text-gray-700 font-mono shrink-0">{new Date(entry.timestamp).toLocaleString()}</span>
                                            <span className="text-gray-400">[{entry.agent}]</span>
                                            <span>{entry.action}</span>
                                            {entry.outcome && <span className="text-gray-600">→ {entry.outcome}</span>}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

function CollapsibleSection({ title, icon: Icon, count, expanded, onToggle, children }: {
    title: string; icon: any; count?: number; expanded: boolean; onToggle: () => void; children: React.ReactNode;
}) {
    return (
        <div className="bg-gray-900/50 rounded-xl border border-white/5 overflow-hidden">
            <button onClick={onToggle} className="w-full flex items-center justify-between px-5 py-3 hover:bg-gray-800/30 transition-colors">
                <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 text-blue-400" />
                    <span className="font-semibold text-sm text-gray-200">{title}</span>
                    {count !== undefined && <span className="text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded-full">{count}</span>}
                </div>
                {expanded ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
            </button>
            {expanded && <div className="px-5 pb-4">{children}</div>}
        </div>
    );
}
