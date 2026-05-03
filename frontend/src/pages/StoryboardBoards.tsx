import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy, useSortable, arrayMove } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, RefreshCw, Film } from 'lucide-react';
import { curationService } from '../services/curation';
import type { StoryboardScene } from '../services/curation';
import RippleEditModal from '../components/RippleEditModal';

function SortableScene({ scene, index }: { scene: StoryboardScene; index: number }) {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
        id: `scene-${scene.scene_index || index}`,
    });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
    };

    return (
        <div ref={setNodeRef} style={style} className={`bg-gray-800/60 rounded-xl border border-white/5 p-4 flex gap-3 ${isDragging ? 'shadow-2xl ring-2 ring-blue-500/40' : ''}`}>
            <button {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing text-gray-600 hover:text-gray-400 pt-1">
                <GripVertical className="w-5 h-5" />
            </button>

            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs bg-blue-600/20 text-blue-400 px-2 py-0.5 rounded-full font-mono">
                        #{scene.scene_index || index + 1}
                    </span>
                    {scene.pacing && (
                        <span className="text-xs bg-gray-700 text-gray-400 px-2 py-0.5 rounded-full">{scene.pacing}</span>
                    )}
                    {scene.duration && (
                        <span className="text-xs text-gray-500">{scene.duration}s</span>
                    )}
                </div>

                {scene.narration && (
                    <p className="text-sm text-gray-300 mb-2 italic">"{scene.narration}"</p>
                )}

                <div className="space-y-1.5">
                    <div>
                        <span className="text-[10px] text-gray-500 uppercase">Visual Prompt</span>
                        <p className="text-xs text-gray-400 line-clamp-2">{scene.visual_prompt}</p>
                    </div>
                    {scene.motion_prompt && (
                        <div>
                            <span className="text-[10px] text-gray-500 uppercase">Motion Prompt</span>
                            <p className="text-xs text-gray-400 line-clamp-2">{scene.motion_prompt}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function StoryboardBoards() {
    const queryClient = useQueryClient();
    const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
    const [scenes, setScenes] = useState<StoryboardScene[]>([]);
    const [rippleOpen, setRippleOpen] = useState(false);

    const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

    const { data: jobs = [], isLoading } = useQuery({
        queryKey: ['curation-jobs'],
        queryFn: curationService.listJobs,
    });

    const completedJobs = jobs.filter(j => j.status === 'completed' && j.creative_brief?.storyboard);

    useEffect(() => {
        if (selectedJobId) {
            const job = completedJobs.find(j => j.id === selectedJobId);
            if (job?.creative_brief?.storyboard) {
                setScenes([...job.creative_brief.storyboard]);
            }
        }
    }, [selectedJobId, jobs]);

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;
        if (!over || active.id === over.id) return;

        const oldIndex = scenes.findIndex((_, i) => `scene-${scenes[i].scene_index || i}` === active.id);
        const newIndex = scenes.findIndex((_, i) => `scene-${scenes[i].scene_index || i}` === over.id);

        if (oldIndex !== -1 && newIndex !== -1) {
            const reordered = arrayMove(scenes, oldIndex, newIndex).map((s, i) => ({
                ...s,
                scene_index: i + 1,
            }));
            setScenes(reordered);
        }
    };

    const totalDuration = scenes.reduce((sum, s) => sum + (s.duration || 0), 0);

    if (isLoading) return <div className="flex items-center justify-center h-full text-gray-400">Loading storyboards...</div>;

    return (
        <div className="flex h-full">
            {/* Sidebar — Job List */}
            <div className="w-72 border-r border-white/5 bg-gray-900/50 flex flex-col">
                <div className="p-4 border-b border-white/5">
                    <h2 className="text-sm font-bold text-gray-300 uppercase tracking-wider">Storyboards</h2>
                    <p className="text-[10px] text-gray-600 mt-1">{completedJobs.length} completed briefs</p>
                </div>
                <div className="flex-1 overflow-auto p-2 space-y-1">
                    {completedJobs.map(job => (
                        <button key={job.id} onClick={() => setSelectedJobId(job.id)}
                            className={`w-full text-left px-3 py-2.5 rounded-lg transition-all text-sm ${
                                selectedJobId === job.id ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' : 'text-gray-400 hover:bg-gray-800/50'
                            }`}>
                            <div className="flex items-center gap-2">
                                <Film className="w-4 h-4 shrink-0" />
                                <span className="truncate font-medium">{job.creative_brief?.title || 'Untitled'}</span>
                            </div>
                            <p className="text-[10px] text-gray-600 mt-1">
                                {job.num_scenes || 0} scenes · {job.created_at ? new Date(job.created_at).toLocaleDateString() : ''}
                            </p>
                        </button>
                    ))}
                    {completedJobs.length === 0 && <p className="text-gray-600 text-xs text-center py-8">No completed storyboards</p>}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto">
                {!selectedJobId ? (
                    <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-4">
                        <Film className="w-16 h-16 text-gray-700" />
                        <p className="text-lg">Select a completed brief to view its storyboard</p>
                    </div>
                ) : (
                    <div className="max-w-3xl mx-auto p-8 space-y-4">
                        {/* Header */}
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-2xl font-bold text-white">
                                    {completedJobs.find(j => j.id === selectedJobId)?.creative_brief?.title || 'Storyboard'}
                                </h1>
                                <p className="text-sm text-gray-500 mt-1">
                                    {scenes.length} scenes · ~{totalDuration}s total · Drag to reorder
                                </p>
                            </div>
                            <div className="flex gap-2">
                                <button onClick={() => setRippleOpen(true)}
                                    className="px-3 py-1.5 rounded-lg text-sm bg-purple-600/20 text-purple-400 hover:bg-purple-600/30 flex items-center gap-1.5">
                                    <RefreshCw className="w-3.5 h-3.5" /> Ripple Edit
                                </button>
                            </div>
                        </div>

                        {/* Sortable Scene List */}
                        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                            <SortableContext items={scenes.map((s, i) => `scene-${s.scene_index || i}`)} strategy={verticalListSortingStrategy}>
                                <div className="space-y-2">
                                    {scenes.map((scene, i) => (
                                        <SortableScene key={`scene-${scene.scene_index || i}`} scene={scene} index={i} />
                                    ))}
                                </div>
                            </SortableContext>
                        </DndContext>
                    </div>
                )}
            </div>

            {/* Ripple Edit Modal */}
            {selectedJobId && (
                <RippleEditModal
                    jobId={selectedJobId}
                    isOpen={rippleOpen}
                    onClose={() => setRippleOpen(false)}
                    onApplied={() => queryClient.invalidateQueries({ queryKey: ['curation-jobs'] })}
                />
            )}
        </div>
    );
}
