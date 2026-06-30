/**
 * Sprint 5 Creator Studio result panels (S5-07).
 *
 * Panels for:
 *   - ThumbnailResultPanel    — radar chart + heatmap toggle + tip cards
 *   - CaptionLensResultPanel  — tabs by platform + caption cards + copy
 *   - MemeResultPanel         — suggestion carousel + text inputs + preview + download
 *   - VideoThumbnailResultPanel — scored frame grid + recommended highlight
 */

import { useState } from 'react';
import {
  Camera,
  Check,
  ChevronLeft,
  ChevronRight,
  Copy,
  Download,
  Film,
  Hash,
  Linkedin,
  Play,
  Sparkles,
  ThumbsUp,
  Twitter,
  Instagram,
} from 'lucide-react';

// ─────────────────────────────────────────────────────────────────────────────
// Shared helpers
// ─────────────────────────────────────────────────────────────────────────────

function ScoreRing({ score, size = 80 }: { score: number; size?: number }) {
  const r = size / 2 - 6;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color =
    score >= 80 ? '#22c55e' : score >= 60 ? '#eab308' : score >= 40 ? '#f97316' : '#ef4444';
  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="absolute rotate-[-90deg]">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="#374151" strokeWidth={6} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={color}
          strokeWidth={6}
          fill="none"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <span className="relative z-10 text-lg font-bold text-white">{Math.round(score)}</span>
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1 rounded px-2 py-1 text-xs text-gray-400 transition-colors hover:bg-gray-700 hover:text-white"
    >
      {copied ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
      {copied ? 'Copied!' : 'Copy'}
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ThumbnailResultPanel
// ─────────────────────────────────────────────────────────────────────────────

interface ThumbnailDimension {
  score: number;
  weight_pct: number;
  detail: Record<string, unknown>;
}

interface ThumbnailTip {
  dimension: string;
  issue: string;
  fix: string;
}

interface ThumbnailResult {
  ctr_score: number;
  grade: string;
  breakdown: Record<string, ThumbnailDimension>;
  tips: ThumbnailTip[];
  winner?: string;
  score_difference?: number;
  explanation?: string;
  thumbnail_a?: ThumbnailResult;
  thumbnail_b?: ThumbnailResult;
}

const DIM_LABELS: Record<string, string> = {
  face_visibility: 'Face',
  visual_contrast: 'Contrast',
  color_energy: 'Color',
  text_readability: 'Text',
  clutter_score: 'Clarity',
  emotional_trigger: 'Emotion',
};

const GRADE_COLOR: Record<string, string> = {
  A: 'text-green-400 bg-green-900/30',
  B: 'text-cyan-400 bg-cyan-900/30',
  C: 'text-yellow-400 bg-yellow-900/30',
  D: 'text-orange-400 bg-orange-900/30',
  F: 'text-red-400 bg-red-900/30',
};

function ThumbnailScoreCard({ result, label }: { result: ThumbnailResult; label?: string }) {
  return (
    <div className="space-y-4 rounded-xl bg-gray-800 p-5">
      {label && (
        <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">{label}</p>
      )}
      <div className="flex items-center gap-4">
        <ScoreRing score={result.ctr_score} size={88} />
        <div>
          <p className="text-sm text-gray-400">CTR Score</p>
          <p className="text-3xl font-bold text-white">{result.ctr_score}</p>
          <span
            className={`mt-1 inline-block rounded px-2 py-0.5 text-xs font-bold ${GRADE_COLOR[result.grade] ?? 'text-gray-400'}`}
          >
            Grade {result.grade}
          </span>
        </div>
      </div>

      {/* Dimension bars */}
      <div className="space-y-2">
        {Object.entries(result.breakdown).map(([key, dim]) => (
          <div key={key}>
            <div className="mb-0.5 flex justify-between text-xs">
              <span className="text-gray-400">{DIM_LABELS[key] ?? key}</span>
              <span className="text-gray-300">
                {Math.round(dim.score)}/100 · {dim.weight_pct}%
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-gray-700">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${dim.score}%`,
                  backgroundColor:
                    dim.score >= 70 ? '#22c55e' : dim.score >= 45 ? '#eab308' : '#ef4444',
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ThumbnailResultPanel({ result }: { result: ThumbnailResult }) {
  const isAB = Boolean(result.winner && result.thumbnail_a && result.thumbnail_b);

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 text-purple-400">
        <Camera size={18} />
        <h3 className="font-semibold">Thumbnail Analysis</h3>
      </div>

      {isAB ? (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <ThumbnailScoreCard result={result.thumbnail_a!} label="Thumbnail A" />
            <ThumbnailScoreCard result={result.thumbnail_b!} label="Thumbnail B" />
          </div>
          <div
            className={`rounded-xl border p-4 ${result.winner === 'A' ? 'border-green-500/50 bg-green-900/20' : 'border-cyan-500/50 bg-cyan-900/20'}`}
          >
            <div className="mb-1 flex items-center gap-2">
              <ThumbsUp size={16} className="text-green-400" />
              <span className="font-semibold text-white">
                Thumbnail {result.winner} wins by {result.score_difference} points
              </span>
            </div>
            <p className="text-sm text-gray-300">{result.explanation}</p>
          </div>
        </div>
      ) : (
        <ThumbnailScoreCard result={result} />
      )}

      {/* Tips */}
      {result.tips && result.tips.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold uppercase tracking-wider text-gray-300">
            Improvement Tips
          </h4>
          {result.tips.map((tip, i) => (
            <div key={i} className="rounded-lg border border-gray-700 bg-gray-800/60 p-4">
              <p className="mb-1 text-xs font-semibold text-purple-400">{tip.dimension}</p>
              <p className="mb-1 text-sm text-gray-300">⚠ {tip.issue}</p>
              <p className="text-sm text-green-300">✓ {tip.fix}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// CaptionLensResultPanel
// ─────────────────────────────────────────────────────────────────────────────

interface InstagramCaption {
  style: string;
  caption: string;
  hashtags: string[];
}

interface CaptionLensResult {
  image_description: string;
  platforms: {
    instagram?: { captions: InstagramCaption[] };
    twitter?: { tweets: string[] };
    linkedin?: { caption: string };
  };
}

const PLATFORM_CONFIG = {
  instagram: { label: 'Instagram', icon: Instagram, color: 'text-pink-400' },
  twitter: { label: 'Twitter / X', icon: Twitter, color: 'text-sky-400' },
  linkedin: { label: 'LinkedIn', icon: Linkedin, color: 'text-blue-400' },
} as const;

export function CaptionLensResultPanel({ result }: { result: CaptionLensResult }) {
  const platforms = Object.keys(result.platforms ?? {}) as (keyof typeof PLATFORM_CONFIG)[];
  const [activeTab, setActiveTab] = useState<string>(platforms[0] ?? 'instagram');

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 text-purple-400">
        <Sparkles size={18} />
        <h3 className="font-semibold">Caption Lens</h3>
      </div>

      {result.image_description && (
        <div className="rounded-lg bg-gray-800/50 px-4 py-3 text-sm italic text-gray-400">
          "{result.image_description}"
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-700">
        {platforms.map((p) => {
          const cfg = PLATFORM_CONFIG[p];
          if (!cfg) return null;
          const Icon = cfg.icon;
          return (
            <button
              key={p}
              onClick={() => setActiveTab(p)}
              className={`flex items-center gap-1.5 border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === p
                  ? `${cfg.color} border-current`
                  : 'border-transparent text-gray-500 hover:text-gray-300'
              }`}
            >
              <Icon size={14} />
              {cfg.label}
            </button>
          );
        })}
      </div>

      {/* Instagram */}
      {activeTab === 'instagram' && result.platforms.instagram && (
        <div className="space-y-4">
          {result.platforms.instagram.captions?.map((cap, i) => (
            <div key={i} className="space-y-3 rounded-xl bg-gray-800 p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase capitalize tracking-wider text-pink-400">
                  {cap.style}
                </span>
                <CopyButton
                  text={cap.caption + '\n\n' + cap.hashtags.map((h) => `#${h}`).join(' ')}
                />
              </div>
              <p className="text-sm leading-relaxed text-gray-200">{cap.caption}</p>
              <div className="flex flex-wrap gap-1">
                {cap.hashtags?.map((tag, j) => (
                  <span
                    key={j}
                    className="flex items-center gap-0.5 rounded-full bg-pink-900/20 px-2 py-0.5 text-xs text-pink-300"
                  >
                    <Hash size={9} />
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Twitter */}
      {activeTab === 'twitter' && result.platforms.twitter && (
        <div className="space-y-3">
          {result.platforms.twitter.tweets?.map((tweet, i) => (
            <div key={i} className="rounded-xl bg-gray-800 p-4">
              <div className="flex items-start justify-between gap-2">
                <p className="flex-1 text-sm leading-relaxed text-gray-200">{tweet}</p>
                <CopyButton text={tweet} />
              </div>
              <p className="mt-2 text-xs text-gray-500">{tweet.length}/280 characters</p>
            </div>
          ))}
        </div>
      )}

      {/* LinkedIn */}
      {activeTab === 'linkedin' && result.platforms.linkedin && (
        <div className="space-y-3 rounded-xl bg-gray-800 p-4">
          <div className="flex items-start justify-between gap-2">
            <p className="flex-1 text-sm leading-relaxed text-gray-200">
              {result.platforms.linkedin.caption}
            </p>
            <CopyButton text={result.platforms.linkedin.caption} />
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MemeResultPanel
// ─────────────────────────────────────────────────────────────────────────────

interface MemeSuggestion {
  top: string;
  bottom: string;
}

interface MemeResult {
  scene_description?: string;
  emotions_detected?: string[];
  suggestions?: MemeSuggestion[];
  // compose result
  result_image_b64?: string;
  format?: string;
}

interface MemeResultPanelProps {
  result: MemeResult;
  originalFileId?: string;
  onCompose?: (fileId: string, top: string, bottom: string) => void;
}

export function MemeResultPanel({ result, originalFileId, onCompose }: MemeResultPanelProps) {
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [topText, setTopText] = useState(result.suggestions?.[0]?.top ?? '');
  const [bottomText, setBottomText] = useState(result.suggestions?.[0]?.bottom ?? '');

  const suggestions = result.suggestions ?? [];
  const composed = result.result_image_b64;

  const selectSuggestion = (idx: number) => {
    setSelectedIdx(idx);
    setTopText(suggestions[idx]?.top ?? '');
    setBottomText(suggestions[idx]?.bottom ?? '');
  };

  const handleDownload = () => {
    if (!composed) return;
    const link = document.createElement('a');
    link.href = `data:image/png;base64,${composed}`;
    link.download = 'meme.png';
    link.click();
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 text-purple-400">
        <Sparkles size={18} />
        <h3 className="font-semibold">Meme Generator Pro</h3>
      </div>

      {result.emotions_detected && (
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <span>Detected:</span>
          {result.emotions_detected.map((em, i) => (
            <span
              key={i}
              className="rounded-full bg-purple-900/40 px-2 py-0.5 text-xs capitalize text-purple-300"
            >
              {em}
            </span>
          ))}
        </div>
      )}

      {/* Composed preview */}
      {composed && (
        <div className="space-y-3">
          <img
            src={`data:image/png;base64,${composed}`}
            alt="Composed meme"
            className="max-h-80 w-full rounded-xl object-contain"
          />
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-700"
          >
            <Download size={14} /> Download Meme
          </button>
        </div>
      )}

      {/* Suggestions carousel */}
      {suggestions.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-gray-300">Caption Suggestions</h4>
          <div className="flex items-center gap-2">
            <button
              onClick={() =>
                selectSuggestion((selectedIdx - 1 + suggestions.length) % suggestions.length)
              }
              className="rounded-lg bg-gray-700 p-1.5 text-gray-300 hover:bg-gray-600"
            >
              <ChevronLeft size={16} />
            </button>
            <div className="flex-1 rounded-xl bg-gray-800 p-4 text-center">
              <p className="text-sm font-medium uppercase text-white">
                {suggestions[selectedIdx]?.top}
              </p>
              <p className="my-1 text-xs text-gray-400">———</p>
              <p className="text-sm font-medium uppercase text-white">
                {suggestions[selectedIdx]?.bottom}
              </p>
              <p className="mt-2 text-xs text-gray-500">
                {selectedIdx + 1} / {suggestions.length}
              </p>
            </div>
            <button
              onClick={() => selectSuggestion((selectedIdx + 1) % suggestions.length)}
              className="rounded-lg bg-gray-700 p-1.5 text-gray-300 hover:bg-gray-600"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Custom text inputs */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-gray-300">Customise Text</h4>
        <div className="space-y-2">
          <input
            value={topText}
            onChange={(e) => setTopText(e.target.value)}
            placeholder="TOP TEXT"
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm uppercase text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none"
          />
          <input
            value={bottomText}
            onChange={(e) => setBottomText(e.target.value)}
            placeholder="BOTTOM TEXT"
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm uppercase text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none"
          />
        </div>
        {onCompose && originalFileId && (
          <button
            onClick={() => onCompose(originalFileId, topText, bottomText)}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-purple-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-purple-700"
          >
            <Play size={14} /> Generate Meme
          </button>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// VideoThumbnailResultPanel
// ─────────────────────────────────────────────────────────────────────────────

interface VideoFrame {
  frame_index: number;
  timestamp_seconds: number;
  timestamp_formatted: string;
  ctr_score: number;
  image_b64: string;
}

interface VideoThumbnailResult {
  total_frames_extracted: number;
  duration_seconds: number;
  fps: number;
  frames: VideoFrame[];
  recommended_frame?: VideoFrame | null;
  error?: string;
}

export function VideoThumbnailResultPanel({ result }: { result: VideoThumbnailResult }) {
  const [selectedFrame, setSelectedFrame] = useState<VideoFrame | null>(
    result.recommended_frame ?? result.frames?.[0] ?? null
  );

  if (result.error) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-900/20 p-4 text-sm text-red-400">
        {result.error}
      </div>
    );
  }

  const handleDownload = (frame: VideoFrame) => {
    const link = document.createElement('a');
    link.href = `data:image/jpeg;base64,${frame.image_b64}`;
    link.download = `thumbnail_${frame.timestamp_formatted.replace(':', '-')}.jpg`;
    link.click();
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 text-purple-400">
        <Film size={18} />
        <h3 className="font-semibold">Video Thumbnail Extractor</h3>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Duration', value: `${Math.round(result.duration_seconds)}s` },
          { label: 'Frames analysed', value: result.total_frames_extracted },
          { label: 'Top picks', value: result.frames?.length ?? 0 },
        ].map((s) => (
          <div key={s.label} className="rounded-lg bg-gray-800 p-3 text-center">
            <p className="text-lg font-bold text-white">{s.value}</p>
            <p className="text-xs text-gray-400">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Selected frame preview */}
      {selectedFrame && (
        <div className="space-y-3">
          <div className="relative overflow-hidden rounded-xl">
            <img
              src={`data:image/jpeg;base64,${selectedFrame.image_b64}`}
              alt={`Frame at ${selectedFrame.timestamp_formatted}`}
              className="max-h-64 w-full object-contain"
            />
            {result.recommended_frame?.frame_index === selectedFrame.frame_index && (
              <div className="absolute left-2 top-2 rounded bg-green-600 px-2 py-1 text-xs font-bold text-white">
                ★ Recommended
              </div>
            )}
            <div className="absolute bottom-2 right-2 rounded bg-black/70 px-2 py-1 text-xs text-white">
              {selectedFrame.timestamp_formatted} · CTR {Math.round(selectedFrame.ctr_score)}
            </div>
          </div>
          <button
            onClick={() => handleDownload(selectedFrame)}
            className="flex items-center gap-2 rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-700"
          >
            <Download size={14} /> Download Frame
          </button>
        </div>
      )}

      {/* Frame grid */}
      <div>
        <h4 className="mb-3 text-sm font-semibold text-gray-300">
          Top {result.frames?.length} Frames
        </h4>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {result.frames?.map((frame) => (
            <button
              key={frame.frame_index}
              onClick={() => setSelectedFrame(frame)}
              className={`relative overflow-hidden rounded-lg border-2 transition-all ${
                selectedFrame?.frame_index === frame.frame_index
                  ? 'border-purple-500'
                  : 'border-gray-700 hover:border-gray-500'
              }`}
            >
              <img
                src={`data:image/jpeg;base64,${frame.image_b64}`}
                alt={`Frame ${frame.timestamp_formatted}`}
                className="h-24 w-full object-cover"
              />
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 px-2 py-1">
                <p className="text-xs text-white">{frame.timestamp_formatted}</p>
                <p className="text-xs font-semibold text-green-400">
                  CTR {Math.round(frame.ctr_score)}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
