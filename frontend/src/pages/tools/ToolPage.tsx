/**
 * Universal ToolPage — wraps the full upload → process → result flow.
 */
import { useParams } from 'react-router-dom';
import { useState, useCallback, type ReactNode } from 'react';
import { CheckCircle, AlertCircle, RotateCcw } from 'lucide-react';
import { FileDropzone } from '@/components/tools/FileDropzone';
import { JobPoller } from '@/components/tools/JobPoller';
import {
  ReceiptResultPanel,
  InvoiceResultPanel,
  BusinessCardResultPanel,
} from '@/components/tools/ResultPanels';
import { api } from '@/lib/api';
import type { UploadedFile } from '@/types';

type Phase = 'idle' | 'uploading' | 'queued' | 'done' | 'error';

// Tool metadata for display
const TOOL_META: Record<string, { name: string; description: string; credits: number }> = {
  'receipt-scanner': {
    name: 'Receipt Scanner',
    description: 'Extract merchant, line items, totals, and more from any receipt photo.',
    credits: 1,
  },
  'invoice-reader': {
    name: 'Invoice Reader',
    description: 'Parse invoice number, supplier, buyer, line items, and payment info.',
    credits: 2,
  },
  'business-card-scanner': {
    name: 'Business Card Scanner',
    description: 'Extract contact info and export as vCard (.vcf) or CSV.',
    credits: 1,
  },
  'background-remover': {
    name: 'Background Remover',
    description: 'Instantly remove the background from any photo with AI precision.',
    credits: 2,
  },
  'caption-lens': {
    name: 'Caption Lens',
    description: 'Auto-generate descriptive captions and tags for your images.',
    credits: 1,
  },
  'shelf-counter': {
    name: 'Shelf Counter',
    description: 'Count products on retail shelves automatically using computer vision.',
    credits: 2,
  },
  'plant-disease-detector': {
    name: 'Plant Disease Detector',
    description: 'Detect and diagnose diseases in plant images with AI-powered analysis.',
    credits: 1,
  },
  'age-predictor': {
    name: 'Age Predictor',
    description: 'Predict apparent age, gender, and emotion from face photos.',
    credits: 1,
  },
};

function GenericResultPanel({ result }: { result: Record<string, unknown> }) {
  return (
    <pre className="overflow-auto rounded-lg bg-gray-950 p-4 text-xs text-gray-300 whitespace-pre-wrap">
      {JSON.stringify(result, null, 2)}
    </pre>
  );
}

function BackgroundRemoverPanel({ result }: { result: Record<string, unknown> }) {
  const b64 = result['result_image_b64'] as string | undefined;
  const method = result['method'] as string | undefined;
  if (!b64) return <GenericResultPanel result={result} />;
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-xs text-gray-400">
        <span className="rounded-full bg-indigo-500/10 px-2 py-0.5 text-indigo-300">
          Method: {method ?? 'AI'}
        </span>
      </div>
      <img
        src={`data:image/png;base64,${b64}`}
        alt="Background removed"
        className="max-h-96 w-auto rounded-lg border border-gray-700 bg-checkered"
        style={{ background: 'repeating-conic-gradient(#374151 0% 25%, #1f2937 0% 50%) 0 0 / 20px 20px' }}
      />
      <a
        href={`data:image/png;base64,${b64}`}
        download="background-removed.png"
        className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
      >
        Download PNG
      </a>
    </div>
  );
}

function CaptionLensPanel({ result }: { result: Record<string, unknown> }) {
  const caption = result['caption'] as string | undefined;
  const tags = result['tags'] as string[] | undefined;
  const confidence = result['confidence'] as number | undefined;
  return (
    <div className="space-y-4">
      {caption && (
        <div className="rounded-lg border border-gray-700 bg-gray-900 p-4">
          <p className="text-sm font-medium text-gray-300 mb-1">Generated Caption</p>
          <p className="text-white">{caption}</p>
        </div>
      )}
      {tags && tags.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-300 mb-2">Tags</p>
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <span key={tag} className="rounded-full bg-gray-800 px-3 py-1 text-xs text-gray-300">
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}
      {confidence !== undefined && (
        <p className="text-xs text-gray-500">Confidence: {Math.round(confidence * 100)}%</p>
      )}
    </div>
  );
}

function ShelfCounterPanel({ result }: { result: Record<string, unknown> }) {
  const count = result['item_count'] as number | undefined;
  const boxes = result['bounding_boxes'] as unknown[] | undefined;
  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-amber-800/40 bg-amber-900/10 p-5 text-center">
        <p className="text-4xl font-bold text-amber-400">{count ?? 0}</p>
        <p className="mt-1 text-sm text-gray-400">Items detected on shelf</p>
      </div>
      {boxes && boxes.length > 0 && (
        <p className="text-xs text-gray-500">{boxes.length} bounding boxes found</p>
      )}
    </div>
  );
}

function PlantDiseasePanel({ result }: { result: Record<string, unknown> }) {
  const health = result['overall_health'] as string | undefined;
  const diseases = result['diseases_detected'] as Array<{ disease: string; severity: string; coverage_ratio: number }> | undefined;
  const recommendations = result['recommendations'] as string[] | undefined;
  const healthColor = health === 'healthy' ? 'text-green-400' : health === 'diseased' ? 'text-red-400' : 'text-yellow-400';
  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-gray-700 bg-gray-900 p-4 text-center">
        <p className={`text-2xl font-bold capitalize ${healthColor}`}>{health ?? 'Unknown'}</p>
        <p className="mt-1 text-sm text-gray-400">Overall Plant Health</p>
      </div>
      {diseases && diseases.length > 0 && (
        <div>
          <p className="mb-2 text-sm font-medium text-gray-300">Diseases Detected</p>
          {diseases.map((d, i) => (
            <div key={i} className="mb-2 rounded-lg border border-red-800/30 bg-red-900/10 p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-red-300">{d.disease}</span>
                <span className="rounded-full bg-red-900/40 px-2 py-0.5 text-xs text-red-400 capitalize">{d.severity}</span>
              </div>
              <p className="mt-1 text-xs text-gray-500">Coverage: {Math.round(d.coverage_ratio * 100)}%</p>
            </div>
          ))}
        </div>
      )}
      {recommendations && recommendations.length > 0 && (
        <div>
          <p className="mb-2 text-sm font-medium text-gray-300">Recommendations</p>
          <ul className="space-y-1">
            {recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
                <span className="mt-0.5 text-green-400">•</span>
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function AgePredictorPanel({ result }: { result: Record<string, unknown> }) {
  const age = result['predicted_age'] as number | null | undefined;
  const range = result['age_range'] as string | undefined;
  const gender = result['gender'] as string | undefined;
  const emotion = result['emotion'] as string | undefined;
  const facesDetected = result['faces_detected'] as number | undefined;
  const message = result['message'] as string | undefined;

  if (facesDetected === 0 || age === null) {
    return (
      <div className="rounded-lg border border-yellow-800/40 bg-yellow-900/10 p-4 text-center">
        <p className="text-yellow-400">{message ?? 'No face detected in the image'}</p>
      </div>
    );
  }
  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="rounded-lg border border-gray-700 bg-gray-900 p-4 text-center">
        <p className="text-3xl font-bold text-pink-400">{age}</p>
        <p className="text-xs text-gray-400">Predicted Age</p>
        {range && <p className="mt-1 text-xs text-gray-500">{range}</p>}
      </div>
      {gender && (
        <div className="rounded-lg border border-gray-700 bg-gray-900 p-4 text-center">
          <p className="text-lg font-semibold capitalize text-white">{gender}</p>
          <p className="text-xs text-gray-400">Gender</p>
          {emotion && <p className="mt-1 text-xs capitalize text-gray-500">{emotion}</p>}
        </div>
      )}
    </div>
  );
}

function renderResult(slug: string, result: Record<string, unknown>, jobId: string): ReactNode {
  if (slug === 'receipt-scanner') {
    return <ReceiptResultPanel result={result as never} jobId={jobId} />;
  }
  if (slug === 'invoice-reader') {
    return <InvoiceResultPanel result={result as never} jobId={jobId} />;
  }
  if (slug === 'business-card-scanner') {
    return <BusinessCardResultPanel result={result as never} jobId={jobId} />;
  }
  if (slug === 'background-remover') {
    return <BackgroundRemoverPanel result={result} />;
  }
  if (slug === 'caption-lens') {
    return <CaptionLensPanel result={result} />;
  }
  if (slug === 'shelf-counter') {
    return <ShelfCounterPanel result={result} />;
  }
  if (slug === 'plant-disease-detector') {
    return <PlantDiseasePanel result={result} />;
  }
  if (slug === 'age-predictor') {
    return <AgePredictorPanel result={result} />;
  }
  // Generic JSON fallback for other tools
  return <GenericResultPanel result={result} />;
}

export function ToolPage() {
  const { slug = '' } = useParams<{ slug: string }>();
  const [phase, setPhase] = useState<Phase>('idle');
  const [jobId, setJobId] = useState('');
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [filePreview, setFilePreview] = useState<string | null>(null);

  const meta = TOOL_META[slug];

  const handleFileDrop = useCallback(
    async (file: File) => {
      setPhase('uploading');
      setErrorMsg('');
      setResult(null);

      // Preview
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => setFilePreview(e.target?.result as string);
        reader.readAsDataURL(file);
      }

      try {
        // 1. Upload file
        const form = new FormData();
        form.append('file', file);
        const { data: uploaded } = await api.post<UploadedFile>('/files/upload', form, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        // 2. Enqueue processing job
        const { data: jobData } = await api.post<{ job_id: string }>(
          `/tools/${slug}/process`,
          { file_id: uploaded.file_id }
        );

        setJobId(jobData.job_id);
        setPhase('queued');
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : 'Upload failed';
        setErrorMsg(msg);
        setPhase('error');
      }
    },
    [slug]
  );

  const handleComplete = useCallback((res: Record<string, unknown>) => {
    setResult(res);
    setPhase('done');
  }, []);

  const handleError = useCallback((err: string) => {
    setErrorMsg(err);
    setPhase('error');
  }, []);

  const reset = () => {
    setPhase('idle');
    setJobId('');
    setResult(null);
    setErrorMsg('');
    setFilePreview(null);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">
            {meta?.name ?? slug.replace(/-/g, ' ')}
          </h1>
          {meta?.description && (
            <p className="mt-1 text-sm text-gray-400">{meta.description}</p>
          )}
        </div>
        {meta?.credits && (
          <span className="rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
            {meta.credits} credit{meta.credits > 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Drop zone — shown unless done */}
      {phase !== 'done' && (
        <FileDropzone
          onFileDrop={(f) => { void handleFileDrop(f); }}
          disabled={phase === 'uploading' || phase === 'queued'}
          preview={filePreview}
        />
      )}

      {/* Uploading state */}
      {phase === 'uploading' && (
        <div className="flex items-center gap-3 rounded-xl border border-gray-700 bg-gray-800/40 p-4 text-sm text-gray-300">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          Uploading file…
        </div>
      )}

      {/* Processing — polling */}
      {phase === 'queued' && jobId && (
        <JobPoller
          jobId={jobId}
          onComplete={handleComplete}
          onError={handleError}
        />
      )}

      {/* Error */}
      {phase === 'error' && (
        <div className="space-y-3">
          <div className="flex items-start gap-3 rounded-xl border border-red-800/50 bg-red-900/10 p-4 text-sm text-red-400">
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button
            onClick={reset}
            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white"
          >
            <RotateCcw size={12} />
            Try again
          </button>
        </div>
      )}

      {/* Result */}
      {phase === 'done' && result && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium text-green-400">
              <CheckCircle size={16} />
              Processing complete
            </div>
            <button
              onClick={reset}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-gray-400 hover:bg-gray-700 hover:text-white"
            >
              <RotateCcw size={12} />
              Process another
            </button>
          </div>
          <div className="rounded-xl border border-gray-700/50 bg-gray-800/30 p-5">
            {renderResult(slug, result, jobId)}
          </div>
        </div>
      )}
    </div>
  );
}
