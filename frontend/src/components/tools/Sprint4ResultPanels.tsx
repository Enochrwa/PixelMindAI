/**
 * Sprint 4 result panels — Photo Intelligence Advanced (S4-07)
 *
 * Panels for: ImageUpscaler, ResumePhotoOptimizer, FaceBlur,
 *             ProfilePictureStyler, DeepfakeDetector.
 */

import { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Download,
  Eye,
  EyeOff,
  Shield,
  Sliders,
  XCircle,
} from 'lucide-react';

// ─────────────────────────────────────────────────────────────────────────────
// Shared helpers
// ─────────────────────────────────────────────────────────────────────────────

function B64Image({ b64, alt, className = '' }: { b64: string; alt: string; className?: string }) {
  if (!b64) return null;
  return (
    <img
      src={`data:image/jpeg;base64,${b64}`}
      alt={alt}
      className={`rounded-lg object-contain ${className}`}
    />
  );
}

function DownloadB64Button({
  b64,
  filename,
  label = 'Download',
}: {
  b64: string;
  filename: string;
  label?: string;
}) {
  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = `data:image/jpeg;base64,${b64}`;
    link.download = filename;
    link.click();
  };
  return (
    <button
      onClick={handleDownload}
      className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
    >
      <Download size={14} />
      {label}
    </button>
  );
}

function ScoreDial({ score, size = 96 }: { score: number; size?: number }) {
  const radius = size / 2 - 8;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color =
    score >= 80 ? '#22c55e' : score >= 60 ? '#eab308' : score >= 40 ? '#f97316' : '#ef4444';
  return (
    <svg width={size} height={size} className="rotate-[-90deg]">
      <circle cx={size / 2} cy={size / 2} r={radius} stroke="#374151" strokeWidth={8} fill="none" />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        stroke={color}
        strokeWidth={8}
        fill="none"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.6s ease' }}
      />
      <text
        x="50%"
        y="50%"
        textAnchor="middle"
        dominantBaseline="middle"
        style={{ rotate: '90deg', transformOrigin: 'center' }}
        fontSize={size * 0.22}
        fontWeight={700}
        fill={color}
        transform={`rotate(90, ${size / 2}, ${size / 2})`}
      >
        {score}
      </text>
    </svg>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. Upscaler Result Panel
// ─────────────────────────────────────────────────────────────────────────────

export function UpscalerResultPanel({ result }: { result: Record<string, unknown> }) {
  const [showComparison, setShowComparison] = useState(false);

  const resultB64 = result.result_image_b64 as string | undefined;
  const comparisonB64 = result.comparison_b64 as string | undefined;
  const origW = result.original_width as number | undefined;
  const origH = result.original_height as number | undefined;
  const upW = result.upscaled_width as number | undefined;
  const upH = result.upscaled_height as number | undefined;
  const method = result.method as string | undefined;

  if (!resultB64) {
    return <p className="text-gray-400">No upscaled image returned.</p>;
  }

  return (
    <div className="space-y-4">
      {/* Stats row */}
      <div className="flex flex-wrap gap-3">
        <div className="rounded-lg bg-gray-800 px-3 py-2 text-sm">
          <span className="text-gray-400">Original </span>
          <span className="font-semibold text-white">
            {origW}×{origH}
          </span>
        </div>
        <div className="rounded-lg bg-indigo-900/60 px-3 py-2 text-sm">
          <span className="text-indigo-300">Upscaled </span>
          <span className="font-semibold text-white">
            {upW}×{upH}
          </span>
        </div>
        <div className="rounded-lg bg-gray-800 px-3 py-2 text-sm text-gray-400">
          Engine:{' '}
          <span className="capitalize text-gray-200">
            {method === 'realesrgan_onnx' ? 'Real-ESRGAN AI' : 'Lanczos (Fallback)'}
          </span>
        </div>
      </div>

      {/* Result image */}
      <B64Image b64={resultB64} alt="Upscaled image" className="max-h-96 w-full" />

      {/* Comparison toggle */}
      {comparisonB64 && (
        <button
          onClick={() => setShowComparison((v) => !v)}
          className="flex items-center gap-1.5 text-sm text-indigo-400 hover:text-indigo-300"
        >
          <Sliders size={14} />
          {showComparison ? 'Hide' : 'Show'} side-by-side comparison
          {showComparison ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      )}
      {showComparison && comparisonB64 && (
        <div>
          <p className="mb-1 text-xs text-gray-500">Original (left) vs Upscaled (right)</p>
          <B64Image b64={comparisonB64} alt="Side-by-side comparison" className="w-full" />
        </div>
      )}

      {/* Download */}
      <DownloadB64Button b64={resultB64} filename="upscaled_4x.jpg" label="Download 4× Image" />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. Resume Photo Optimizer Panel
// ─────────────────────────────────────────────────────────────────────────────

const DIMENSION_LABELS: Record<string, string> = {
  face_visibility: 'Face Visibility',
  lighting_quality: 'Lighting Quality',
  background_quality: 'Background',
  eye_contact: 'Eye Contact',
  expression: 'Expression',
  composition: 'Composition',
};

export function ResumeOptimizerResultPanel({ result }: { result: Record<string, unknown> }) {
  const score = result.total_score as number;
  const verdict = result.verdict as string;
  const breakdown = result.breakdown as Record<string, Record<string, unknown>> | undefined;
  const tips = result.tips as Array<Record<string, string>> | undefined;

  return (
    <div className="space-y-5">
      {/* Score header */}
      <div className="flex items-center gap-5">
        <ScoreDial score={score} size={100} />
        <div>
          <p className="text-2xl font-bold text-white">{score}/100</p>
          <p className="mt-1 text-sm text-gray-400">{verdict}</p>
        </div>
      </div>

      {/* Dimension bars */}
      {breakdown && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400">Breakdown</h3>
          {Object.entries(breakdown).map(([key, info]) => {
            const dimScore = info.score as number;
            const weight = info.weight as number;
            const barColor =
              dimScore >= 80 ? 'bg-green-500' : dimScore >= 60 ? 'bg-yellow-400' : 'bg-red-500';
            return (
              <div key={key}>
                <div className="mb-0.5 flex justify-between text-xs text-gray-400">
                  <span>{DIMENSION_LABELS[key] ?? key}</span>
                  <span>
                    {dimScore}/100 <span className="text-gray-600">· {weight}% weight</span>
                  </span>
                </div>
                <div className="h-2 rounded-full bg-gray-700">
                  <div
                    className={`h-2 rounded-full ${barColor} transition-all duration-500`}
                    style={{ width: `${dimScore}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Tips */}
      {tips && tips.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400">
            Improvement Tips
          </h3>
          {tips.map((tip, i) => (
            <div key={i} className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-3">
              <p className="text-xs font-medium text-yellow-400">
                {DIMENSION_LABELS[tip.dimension ?? ''] ?? tip.dimension}
              </p>
              <p className="mt-0.5 text-sm text-gray-200">{tip.issue}</p>
              <p className="mt-1 text-xs text-gray-400">💡 {tip.fix_suggestion}</p>
            </div>
          ))}
        </div>
      )}

      {tips && tips.length === 0 && (
        <div className="flex items-center gap-2 rounded-lg bg-green-500/10 p-3 text-green-400">
          <CheckCircle size={16} />
          <span className="text-sm">Great photo! No major issues found.</span>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. Face Blur Panel
// ─────────────────────────────────────────────────────────────────────────────

export function FaceBlurResultPanel({ result }: { result: Record<string, unknown> }) {
  const resultB64 = result.result_image_b64 as string | undefined;
  const facesCount = result.faces_detected_count as number;
  const mode = result.mode_applied as string;

  if (!resultB64) return <p className="text-gray-400">No result image returned.</p>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <div className="flex items-center gap-1.5 rounded-lg bg-gray-800 px-3 py-2 text-sm">
          <Shield size={14} className="text-cyan-400" />
          <span className="text-gray-400">Faces blurred: </span>
          <span className="font-semibold text-white">{facesCount}</span>
        </div>
        <div className="rounded-lg bg-gray-800 px-3 py-2 text-sm text-gray-400">
          Mode: <span className="capitalize text-gray-200">{mode.replace(/_/g, ' ')}</span>
        </div>
      </div>

      <B64Image b64={resultB64} alt="Face-blurred image" className="max-h-96 w-full" />

      {facesCount === 0 && (
        <div className="rounded-lg bg-yellow-500/10 p-3 text-sm text-yellow-400">
          No faces were detected. The image was returned unmodified.
        </div>
      )}

      <DownloadB64Button
        b64={resultB64}
        filename="privacy_protected.jpg"
        label="Download Protected Image"
      />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. Profile Picture Styler Panel
// ─────────────────────────────────────────────────────────────────────────────

const STYLE_LABELS: Record<string, string> = {
  corporate: '🏢 Corporate',
  linkedin: '💼 LinkedIn Studio',
  creative: '🎨 Creative',
  minimal: '✨ Minimal',
};

export function ProfileStylerResultPanel({ result }: { result: Record<string, unknown> }) {
  const styles = result.styles as Array<Record<string, string>> | undefined;
  const [selectedStyle, setSelectedStyle] = useState<string | null>(
    styles && styles.length > 0 ? (styles[0]?.style_name ?? null) : null
  );

  if (!styles || styles.length === 0) {
    return <p className="text-gray-400">No style variants returned.</p>;
  }

  const current = styles.find((s) => s.style_name === selectedStyle) ?? styles[0];
  const currentName: string = current?.style_name ?? '';
  const currentB64: string = current?.result_image_b64 ?? '';

  return (
    <div className="space-y-4">
      {/* Style selector -- 2x2 grid thumbnails */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {styles.map((style) => (
          <button
            key={style.style_name}
            onClick={() => setSelectedStyle(style.style_name ?? null)}
            className={`rounded-lg border-2 p-1 transition-all ${
              selectedStyle === style.style_name
                ? 'border-indigo-500'
                : 'border-transparent hover:border-gray-600'
            }`}
          >
            <img
              src={`data:image/jpeg;base64,${style.result_image_b64}`}
              alt={style.style_name}
              className="aspect-square w-full rounded object-cover"
            />
            <p className="mt-1 text-center text-xs text-gray-400">
              {STYLE_LABELS[style.style_name ?? ''] ?? style.style_name}
            </p>
          </button>
        ))}
      </div>

      {/* Large preview */}
      <B64Image b64={currentB64} alt="Profile preview" className="max-h-80 w-full" />

      <DownloadB64Button
        b64={currentB64}
        filename={`profile_${currentName}.jpg`}
        label={`Download ${STYLE_LABELS[currentName] ?? currentName}`}
      />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. Deepfake Detector Panel
// ─────────────────────────────────────────────────────────────────────────────

type EvidenceItem = {
  type: string;
  suspicious_score: number;
  description: string;
};

const VERDICT_CONFIG = {
  LIKELY_REAL: {
    icon: CheckCircle,
    color: 'text-green-400',
    bg: 'bg-green-500/10',
    label: 'Likely Real',
  },
  UNCERTAIN: {
    icon: AlertTriangle,
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    label: 'Uncertain',
  },
  LIKELY_FAKE: {
    icon: XCircle,
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    label: 'Likely Fake / AI-Generated',
  },
} as const;

const SIGNAL_LABELS: Record<string, string> = {
  fft_frequency: 'Frequency Analysis (FFT)',
  boundary_consistency: 'Facial Boundary Edges',
  eye_reflection: 'Eye Reflection Symmetry',
  noise_pattern: 'Camera Noise Pattern',
};

export function DeepfakeResultPanel({ result }: { result: Record<string, unknown> }) {
  const [showHeatmap, setShowHeatmap] = useState(false);

  const authScore = result.authenticity_score as number;
  const verdict = result.verdict as keyof typeof VERDICT_CONFIG;
  const facesDetected = result.faces_detected as number;
  const evidence = result.evidence as EvidenceItem[] | undefined;
  const heatmapB64 = result.heatmap_b64 as string | undefined;
  const disclaimer = result.disclaimer as string;

  const verdictCfg = VERDICT_CONFIG[verdict] ?? VERDICT_CONFIG.UNCERTAIN;
  const VerdictIcon = verdictCfg.icon;

  return (
    <div className="space-y-5">
      {/* Score + verdict */}
      <div className={`flex items-center gap-4 rounded-lg p-4 ${verdictCfg.bg}`}>
        <ScoreDial score={authScore} size={88} />
        <div>
          <div className={`flex items-center gap-2 ${verdictCfg.color}`}>
            <VerdictIcon size={20} />
            <span className="text-lg font-bold">{verdictCfg.label}</span>
          </div>
          <p className="mt-1 text-sm text-gray-400">Authenticity score: {authScore}/100</p>
          <p className="text-xs text-gray-500">Faces detected: {facesDetected}</p>
        </div>
      </div>

      {/* Evidence signals */}
      {evidence && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400">
            Detection Signals
          </h3>
          {evidence.map((ev) => {
            const suspicious = ev.suspicious_score;
            const barColor =
              suspicious >= 60 ? 'bg-red-500' : suspicious >= 30 ? 'bg-yellow-400' : 'bg-green-500';
            return (
              <div key={ev.type} className="rounded-lg bg-gray-800/60 p-3">
                <div className="mb-1 flex justify-between text-xs">
                  <span className="text-gray-300">{SIGNAL_LABELS[ev.type] ?? ev.type}</span>
                  <span className={suspicious > 20 ? 'text-red-400' : 'text-green-400'}>
                    {suspicious > 20 ? `${suspicious}% suspicious` : 'Normal'}
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-gray-700">
                  <div
                    className={`h-1.5 rounded-full ${barColor} transition-all duration-500`}
                    style={{ width: `${suspicious}%` }}
                  />
                </div>
                <p className="mt-1 text-xs text-gray-500">{ev.description}</p>
              </div>
            );
          })}
        </div>
      )}

      {/* Heatmap toggle */}
      {heatmapB64 && (
        <>
          <button
            onClick={() => setShowHeatmap((v) => !v)}
            className="flex items-center gap-1.5 text-sm text-indigo-400 hover:text-indigo-300"
          >
            {showHeatmap ? <EyeOff size={14} /> : <Eye size={14} />}
            {showHeatmap ? 'Hide' : 'Show'} analysis overlay
          </button>
          {showHeatmap && (
            <B64Image
              b64={heatmapB64}
              alt="Deepfake detection heatmap"
              className="max-h-80 w-full"
            />
          )}
        </>
      )}

      {/* Disclaimer — always shown */}
      <div className="rounded-lg border border-gray-700 bg-gray-900/50 p-3 text-xs text-gray-500">
        ⚠️ {disclaimer}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Registry — maps tool slug → panel component
// ─────────────────────────────────────────────────────────────────────────────

// Re-export type so ToolPage can use it
export type Sprint4Panel = typeof UpscalerResultPanel;

export const SPRINT4_PANELS: Record<
  string,
  (props: { result: Record<string, unknown> }) => JSX.Element
> = {
  'image-upscaler': UpscalerResultPanel,
  'resume-photo-optimizer': ResumeOptimizerResultPanel,
  'face-blur': FaceBlurResultPanel,
  'profile-picture-styler': ProfileStylerResultPanel,
  'deepfake-detector': DeepfakeResultPanel,
};
