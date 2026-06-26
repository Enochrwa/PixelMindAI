/**
 * Universal ToolPage — wraps the full upload → process → result flow.
 * Sprint 1 adds specialized ResultPanels for OCR tools.
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
};

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
  // Generic JSON fallback for other tools
  return (
    <pre className="overflow-auto rounded-lg bg-gray-950 p-4 text-xs text-gray-300">
      {JSON.stringify(result, null, 2)}
    </pre>
  );
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
