/**
 * InspirationExtractor — extracts character/environment inspiration from a
 * Single Video research result and stages it for bible population.
 *
 * Props:
 *   videoUrl: the YouTube URL from the research job source_data
 *
 * Flow:
 *   1. User clicks "Extract Inspiration to Bible"
 *   2. Extraction runs (calls POST /bible/extract-inspiration)
 *   3. Results shown in staging panel: characters, environments, style, camera
 *   4. User toggles which items to include
 *   5. User selects target bible from dropdown
 *   6. User clicks "Apply to Bible" -> calls POST /bible/{id}/apply-suggestions
 *   7. Success state + link to BibleWorkspace
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Sparkles, CheckCircle, XCircle, BookOpen,
  Loader2, ChevronDown,
} from 'lucide-react';
import { bibleService } from '../services/bible';
import type {
  InspirationData,
  InspirationCharacter,
  InspirationEnvironment,
} from '../services/bible';

interface Props {
  videoUrl: string;
}

export default function InspirationExtractor({ videoUrl }: Props) {
  const queryClient = useQueryClient();
  const [inspiration, setInspiration] = useState<InspirationData | null>(null);
  const [selectedCharacters, setSelectedCharacters] = useState<Set<number>>(new Set());
  const [selectedEnvironments, setSelectedEnvironments] = useState<Set<number>>(new Set());
  const [applyStyle, setApplyStyle] = useState(false);
  const [applyCamera, setApplyCamera] = useState(false);
  const [targetBibleId, setTargetBibleId] = useState<string>('');
  const [applied, setApplied] = useState(false);

  const { data: bibles = [] } = useQuery({
    queryKey: ['bibles'],
    queryFn: bibleService.list,
  });

  const extractMutation = useMutation({
    mutationFn: () => bibleService.extractInspiration(videoUrl),
    onSuccess: (data) => {
      setInspiration(data);
      // Pre-select all high- and medium-confidence items
      setSelectedCharacters(
        new Set(
          data.characters
            .map((_, i) => i)
            .filter(i => data.characters[i].confidence !== 'low')
        )
      );
      setSelectedEnvironments(
        new Set(
          data.environments
            .map((_, i) => i)
            .filter(i => data.environments[i].confidence !== 'low')
        )
      );
    },
  });

  const applyMutation = useMutation({
    mutationFn: () => {
      if (!inspiration || !targetBibleId) throw new Error('Select a bible first');
      return bibleService.applySuggestions(targetBibleId, {
        characters: Array.from(selectedCharacters).map(i => inspiration.characters[i]),
        environments: Array.from(selectedEnvironments).map(i => inspiration.environments[i]),
        style_signals: applyStyle ? inspiration.style_signals : undefined,
        camera_signals: applyCamera ? inspiration.camera_signals : undefined,
        apply_style: applyStyle,
        apply_camera: applyCamera,
        source_video_url: inspiration.source_video_url,
        source_video_title: inspiration.source_video_title,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bibles'] });
      setApplied(true);
    },
  });

  const confidenceBadge = (c: string) => {
    const colors: Record<string, string> = {
      high: 'bg-green-500/20 text-green-400',
      medium: 'bg-yellow-500/20 text-yellow-400',
      low: 'bg-gray-500/20 text-gray-400',
    };
    return (
      <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${colors[c] ?? colors.medium}`}>
        {c}
      </span>
    );
  };

  const toggleChar = (i: number) =>
    setSelectedCharacters(prev => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });

  const toggleEnv = (i: number) =>
    setSelectedEnvironments(prev => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });

  const nothingSelected =
    selectedCharacters.size === 0 &&
    selectedEnvironments.size === 0 &&
    !applyStyle &&
    !applyCamera;

  if (applied) {
    return (
      <div className="mt-4 p-4 bg-green-500/10 border border-green-500/30 rounded-xl text-green-400 flex items-center gap-3">
        <CheckCircle className="w-5 h-5 shrink-0" />
        <div>
          <p className="font-medium text-sm">Inspiration applied to bible</p>
          <a href="/bible" className="text-xs underline opacity-70 hover:opacity-100">
            Open Bible Workspace →
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4">
      {/* Trigger button */}
      {!inspiration && (
        <button
          onClick={() => extractMutation.mutate()}
          disabled={extractMutation.isPending}
          className="flex items-center gap-2 px-4 py-2.5 bg-purple-600/20 border border-purple-500/30 text-purple-400 rounded-xl hover:bg-purple-600/30 transition-all text-sm font-medium disabled:opacity-50"
        >
          {extractMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Watching video… (~60 seconds)
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              Extract Inspiration to Bible
            </>
          )}
        </button>
      )}

      {extractMutation.isError && (
        <p className="mt-2 text-red-400 text-sm">
          {(extractMutation.error as Error).message}
        </p>
      )}

      {/* Staging Panel */}
      {inspiration && (
        <div className="mt-4 space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-bold text-white">
              Inspiration from "{inspiration.source_video_title}"
            </h3>
          </div>

          {/* Characters */}
          {inspiration.characters.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Characters ({inspiration.characters.length})
              </p>
              {inspiration.characters.map((char, i) => (
                <div
                  key={i}
                  onClick={() => toggleChar(i)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    selectedCharacters.has(i)
                      ? 'bg-purple-600/15 border-purple-500/40'
                      : 'bg-gray-800/40 border-white/5 opacity-60'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {selectedCharacters.has(i)
                          ? <CheckCircle className="w-4 h-4 text-purple-400" />
                          : <XCircle className="w-4 h-4 text-gray-600" />
                        }
                        <span className="text-sm font-semibold text-white">{char.name}</span>
                        {confidenceBadge(char.confidence)}
                        <span className="text-[10px] text-gray-600">{char.role}</span>
                      </div>
                      <p className="text-xs text-gray-400">{char.physical}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{char.wardrobe}</p>
                      {char.visual_keywords.length > 0 && (
                        <div className="flex gap-1 mt-1 flex-wrap">
                          {char.visual_keywords.map((k, j) => (
                            <span
                              key={j}
                              className="text-[10px] px-1.5 py-0.5 bg-gray-700/60 text-gray-400 rounded"
                            >
                              {k}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Environments */}
          {inspiration.environments.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Environments ({inspiration.environments.length})
              </p>
              {inspiration.environments.map((env, i) => (
                <div
                  key={i}
                  onClick={() => toggleEnv(i)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    selectedEnvironments.has(i)
                      ? 'bg-blue-600/15 border-blue-500/40'
                      : 'bg-gray-800/40 border-white/5 opacity-60'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {selectedEnvironments.has(i)
                      ? <CheckCircle className="w-4 h-4 text-blue-400" />
                      : <XCircle className="w-4 h-4 text-gray-600" />
                    }
                    <span className="text-sm font-semibold text-white">{env.name}</span>
                    {confidenceBadge(env.confidence)}
                  </div>
                  <p className="text-xs text-gray-400">{env.description}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {env.lighting} · {env.mood} · {env.time_of_day}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Style & Camera toggles */}
          <div className="flex gap-4 flex-wrap">
            <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={applyStyle}
                onChange={e => setApplyStyle(e.target.checked)}
                className="rounded"
              />
              Apply style signals to bible
            </label>
            <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={applyCamera}
                onChange={e => setApplyCamera(e.target.checked)}
                className="rounded"
              />
              Apply camera signals to bible
            </label>
          </div>

          {/* Bible selector + apply */}
          <div className="flex gap-3 items-center flex-wrap">
            <div className="relative flex-1 min-w-48">
              <select
                value={targetBibleId}
                onChange={e => setTargetBibleId(e.target.value)}
                className="w-full appearance-none bg-gray-800 border border-white/10 text-gray-300 text-sm rounded-xl px-3 py-2 pr-8"
              >
                <option value="">Select a bible to populate…</option>
                {bibles
                  .filter(b => b.status !== 'locked')
                  .map(b => (
                    <option key={b.id} value={b.id}>
                      {b.name} ({b.characters?.length ?? 0} chars · {b.environments?.length ?? 0} envs)
                    </option>
                  ))}
              </select>
              <ChevronDown className="w-4 h-4 text-gray-500 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>

            <button
              onClick={() => applyMutation.mutate()}
              disabled={!targetBibleId || nothingSelected || applyMutation.isPending}
              className="px-4 py-2 bg-purple-600 text-white rounded-xl text-sm font-medium hover:bg-purple-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            >
              {applyMutation.isPending ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Applying…</>
              ) : (
                <><BookOpen className="w-4 h-4" /> Apply to Bible</>
              )}
            </button>
          </div>

          {applyMutation.isError && (
            <p className="text-red-400 text-sm">{(applyMutation.error as Error).message}</p>
          )}
        </div>
      )}
    </div>
  );
}
