/**
 * Universal ToolPage — wraps the full upload → process → result flow.
 */
import { useParams } from 'react-router-dom';
import { useState, useCallback, useEffect, type ReactNode } from 'react';
import { CheckCircle, AlertCircle, RotateCcw } from 'lucide-react';
import { FileDropzone } from '@/components/tools/FileDropzone';
import { JobPoller } from '@/components/tools/JobPoller';
import {
  ReceiptResultPanel,
  InvoiceResultPanel,
  BusinessCardResultPanel,
  // Sprint 2
  HandwritingResultPanel,
  MenuResultPanel,
  DocumentScannerResultPanel,
  SignatureExtractorResultPanel,
  FormFieldResultPanel,
  // Sprint 3
  BackgroundRemoverResultPanel,
  PassportPhotoResultPanel,
} from '@/components/tools/ResultPanels';
// Sprint 5 Creator Studio panels
import {
  ThumbnailResultPanel,
  CaptionLensResultPanel,
  MemeResultPanel,
  VideoThumbnailResultPanel,
} from '@/components/tools/Sprint5ResultPanels';
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
  // Sprint 2
  'handwriting-ocr': {
    name: 'Handwriting OCR',
    description: 'Convert handwritten notes to digital text with structure detection.',
    credits: 2,
  },
  'menu-scanner': {
    name: 'Menu Scanner',
    description: 'Digitize physical restaurant menus to structured data with prices.',
    credits: 2,
  },
  'document-scanner': {
    name: 'Document Scanner',
    description: 'Crop, deskew, and enhance any document photo. Export as JPEG or PDF.',
    credits: 1,
  },
  'signature-extractor': {
    name: 'Signature Extractor',
    description: 'Isolate and export signatures from signed documents.',
    credits: 1,
  },
  'form-field-reader': {
    name: 'Form Field Reader',
    description: 'Extract handwritten responses from paper forms into structured JSON.',
    credits: 2,
  },
  'background-remover': {
    name: 'Background Remover',
    description:
      'Instantly remove the background from any photo. Choose transparent, white, color, or blur replacement.',
    credits: 2,
  },
  'passport-photo': {
    name: 'Passport Photo Generator',
    description: 'Generate country-compliant passport photos for 30+ countries with one click.',
    credits: 2,
  },
  'caption-lens': {
    name: 'Caption Lens',
    description:
      'AI-powered multi-platform social captions (Instagram, Twitter, LinkedIn) from any photo.',
    credits: 2,
  },
  // Sprint 5 — Creator Studio Core
  'thumbnail-analyzer': {
    name: 'Thumbnail Analyzer',
    description: 'Predict YouTube thumbnail CTR across 6 dimensions. A/B test two thumbnails.',
    credits: 2,
  },
  'meme-generator': {
    name: 'Meme Generator Pro',
    description:
      'AI-powered meme caption suggestions from face expressions + one-click composition.',
    credits: 2,
  },
  'video-thumbnail-extractor': {
    name: 'Video Thumbnail Extractor',
    description: 'Extract the best thumbnail frames from any video file, scored by CTR prediction.',
    credits: 3,
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
    <pre className="overflow-auto whitespace-pre-wrap rounded-lg bg-gray-950 p-4 text-xs text-gray-300">
      {JSON.stringify(result, null, 2)}
    </pre>
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
          <p className="mb-1 text-sm font-medium text-gray-300">Generated Caption</p>
          <p className="text-white">{caption}</p>
        </div>
      )}
      {tags && tags.length > 0 && (
        <div>
          <p className="mb-2 text-sm font-medium text-gray-300">Tags</p>
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
  const diseases = result['diseases_detected'] as
    | Array<{ disease: string; severity: string; coverage_ratio: number }>
    | undefined;
  const recommendations = result['recommendations'] as string[] | undefined;
  const healthColor =
    health === 'healthy'
      ? 'text-green-400'
      : health === 'diseased'
        ? 'text-red-400'
        : 'text-yellow-400';
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
                <span className="rounded-full bg-red-900/40 px-2 py-0.5 text-xs capitalize text-red-400">
                  {d.severity}
                </span>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Coverage: {Math.round(d.coverage_ratio * 100)}%
              </p>
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
    return <BackgroundRemoverResultPanel result={result as never} jobId={jobId} />;
  }
  if (slug === 'passport-photo') {
    return <PassportPhotoResultPanel result={result as never} jobId={jobId} />;
  }
  if (slug === 'caption-lens') {
    // Sprint 5: full multi-platform result
    if (result['platforms']) {
      return <CaptionLensResultPanel result={result as never} />;
    }
    return <CaptionLensPanel result={result} />;
  }
  // Sprint 5 — Creator Studio Core
  if (slug === 'thumbnail-analyzer') {
    return <ThumbnailResultPanel result={result as never} />;
  }
  if (slug === 'meme-generator') {
    return <MemeResultPanel result={result as never} />;
  }
  if (slug === 'video-thumbnail-extractor') {
    return <VideoThumbnailResultPanel result={result as never} />;
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
  // Sprint 2 — Document AI Advanced
  if (slug === 'handwriting-ocr') {
    return <HandwritingResultPanel result={result as never} jobId={jobId} />;
  }
  if (slug === 'menu-scanner') {
    return <MenuResultPanel result={result as never} jobId={jobId} />;
  }
  if (slug === 'document-scanner') {
    return <DocumentScannerResultPanel result={result as never} />;
  }
  if (slug === 'signature-extractor') {
    return <SignatureExtractorResultPanel result={result as never} />;
  }
  if (slug === 'form-field-reader') {
    return <FormFieldResultPanel result={result as never} />;
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
  const [passportCountry, setPassportCountry] = useState('us');
  const [passportCountries, setPassportCountries] = useState<
    Array<{ code: string; name: string; flag: string }>
  >([]);

  const meta = TOOL_META[slug];

  // Fetch passport countries when on passport-photo tool
  useEffect(() => {
    if (slug !== 'passport-photo') return;
    api
      .get<Array<{ code: string; name: string; flag: string }>>('/tools/passport-photo/countries')
      .then(({ data }) => setPassportCountries(data))
      .catch(() => {});
  }, [slug]);

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
        const processBody: Record<string, unknown> = { file_id: uploaded.file_id };
        if (slug === 'passport-photo') {
          processBody['options'] = { country_code: passportCountry };
        }
        const { data: jobData } = await api.post<{ job_id: string }>(
          `/tools/${slug}/process`,
          processBody
        );

        setJobId(jobData.job_id);
        setPhase('queued');
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : 'Upload failed';
        setErrorMsg(msg);
        setPhase('error');
      }
    },
    [slug, passportCountry]
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
          <h1 className="text-xl font-bold text-white">{meta?.name ?? slug.replace(/-/g, ' ')}</h1>
          {meta?.description && <p className="mt-1 text-sm text-gray-400">{meta.description}</p>}
        </div>
        {meta?.credits && (
          <span className="rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
            {meta.credits} credit{meta.credits > 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Passport photo country selector */}
      {slug === 'passport-photo' && phase !== 'done' && (
        <div className="rounded-xl border border-gray-700/50 bg-gray-800/30 p-4">
          <label
            className="mb-2 block text-sm font-medium text-gray-300"
            htmlFor="passport-country"
          >
            Select destination country
          </label>
          <select
            id="passport-country"
            value={passportCountry}
            onChange={(e) => setPassportCountry(e.target.value)}
            className="w-full rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-200 focus:border-indigo-500 focus:outline-none"
          >
            {passportCountries.length === 0 ? (
              <option value="us">United States (US)</option>
            ) : (
              passportCountries.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.flag} {c.name} ({c.code.toUpperCase()})
                </option>
              ))
            )}
          </select>
        </div>
      )}

      {/* Drop zone — shown unless done */}
      {phase !== 'done' && (
        <FileDropzone
          onFileDrop={(f) => {
            void handleFileDrop(f);
          }}
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
        <JobPoller jobId={jobId} onComplete={handleComplete} onError={handleError} />
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
