import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { X, Eye, Check, RefreshCw } from 'lucide-react';
import { rippleService } from '../services/bible';
import type { RippleEditPayload } from '../services/bible';

interface Props {
    jobId: string;
    isOpen: boolean;
    onClose: () => void;
    onApplied: () => void;
}

export default function RippleEditModal({ jobId, isOpen, onClose, onApplied }: Props) {
    const [directive, setDirective] = useState('');
    const [targetField, setTargetField] = useState('visual_prompt');
    const [previewResult, setPreviewResult] = useState<any>(null);

    const previewMutation = useMutation({
        mutationFn: (data: RippleEditPayload) => rippleService.preview(jobId, data),
        onSuccess: (result) => setPreviewResult(result),
    });

    const applyMutation = useMutation({
        mutationFn: (data: RippleEditPayload) => rippleService.apply(jobId, data),
        onSuccess: () => { onApplied(); onClose(); },
    });

    const handlePreview = () => {
        if (!directive.trim()) return;
        previewMutation.mutate({ directive, target_field: targetField });
    };

    const handleApply = () => {
        if (!directive.trim()) return;
        applyMutation.mutate({ directive, target_field: targetField });
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-gray-900 border border-white/10 rounded-2xl w-[700px] max-h-[80vh] overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
                    <div className="flex items-center gap-2">
                        <RefreshCw className="w-5 h-5 text-purple-400" />
                        <h2 className="text-lg font-bold text-white">Ripple Edit</h2>
                    </div>
                    <button onClick={onClose} className="p-1 rounded-lg hover:bg-gray-800 transition-colors">
                        <X className="w-5 h-5 text-gray-400" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-4 overflow-auto max-h-[60vh]">
                    <p className="text-sm text-gray-400">
                        Describe a change to apply across <strong>all storyboard scenes</strong>.
                        Use "Change X to Y" format for best results.
                    </p>

                    <div>
                        <label className="text-xs text-gray-500 uppercase block mb-1">Directive</label>
                        <input type="text" value={directive} onChange={e => setDirective(e.target.value)}
                            placeholder='e.g. "Change black hair to silver hair"'
                            className="w-full bg-gray-800 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:border-purple-500 focus:outline-none" />
                    </div>

                    <div>
                        <label className="text-xs text-gray-500 uppercase block mb-1">Target Field</label>
                        <select value={targetField} onChange={e => setTargetField(e.target.value)}
                            className="bg-gray-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none">
                            <option value="visual_prompt">visual_prompt</option>
                            <option value="motion_prompt">motion_prompt</option>
                            <option value="narration">narration</option>
                        </select>
                    </div>

                    {/* Preview Result */}
                    {previewResult && (
                        <div className="space-y-2">
                            <p className="text-xs text-green-400 font-medium">{previewResult.changes_summary}</p>
                            <div className="max-h-60 overflow-auto space-y-2">
                                {previewResult.modified_scenes.map((scene: any, i: number) => {
                                    const original = previewResult.original_scenes[i];
                                    const changed = original?.[targetField] !== scene[targetField];
                                    return (
                                        <div key={i} className={`text-xs rounded-lg p-3 border ${changed ? 'bg-green-900/20 border-green-500/30' : 'bg-gray-800/50 border-white/5'}`}>
                                            <p className="text-gray-500 mb-1">Scene {scene.scene_index || i + 1}</p>
                                            {changed ? (
                                                <>
                                                    <p className="text-red-400/60 line-through">{original?.[targetField]?.slice(0, 120)}...</p>
                                                    <p className="text-green-400 mt-1">{scene[targetField]?.slice(0, 120)}...</p>
                                                </>
                                            ) : (
                                                <p className="text-gray-600">No change</p>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex justify-end gap-2 px-6 py-4 border-t border-white/5">
                    <button onClick={handlePreview} disabled={!directive.trim() || previewMutation.isPending}
                        className="px-4 py-2 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 text-sm font-medium flex items-center gap-1.5 disabled:opacity-50">
                        <Eye className="w-4 h-4" /> {previewMutation.isPending ? 'Previewing...' : 'Preview'}
                    </button>
                    <button onClick={handleApply} disabled={!directive.trim() || !previewResult || applyMutation.isPending}
                        className="px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-500 text-sm font-medium flex items-center gap-1.5 disabled:opacity-50">
                        <Check className="w-4 h-4" /> {applyMutation.isPending ? 'Applying...' : 'Apply to All'}
                    </button>
                </div>
            </div>
        </div>
    );
}
