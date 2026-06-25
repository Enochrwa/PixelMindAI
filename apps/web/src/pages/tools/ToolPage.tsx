import { useParams } from 'react-router-dom';
import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';
import type { Job, UploadedFile } from '@/types';

type Phase = 'idle' | 'uploading' | 'processing' | 'done' | 'error';

export function ToolPage() {
  const { slug } = useParams<{ slug: string }>();
  const [phase, setPhase] = useState<Phase>('idle');
  const [result, setResult] = useState<unknown>(null);
  const [errorMsg, setErrorMsg] = useState('');

  const onDrop = useCallback(
    async (files: File[]) => {
      const file = files[0];
      if (!file || !slug) return;

      setPhase('uploading');
      setErrorMsg('');

      try {
        const form = new FormData();
        form.append('file', file);
        const { data: uploaded } = await api.post<UploadedFile>('/files/upload', form, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        setPhase('processing');
        const { data: jobData } = await api.post<{ job_id: string }>(
          `/tools/${slug}/process`,
          { file_id: uploaded.file_id }
        );

        // Poll for completion
        const jobId = jobData.job_id;
        let job: Job | null = null;
        for (let i = 0; i < 60; i++) {
          await new Promise((r) => setTimeout(r, 2000));
          const { data } = await api.get<Job>(`/jobs/${jobId}`);
          job = data;
          if (data.status === 'COMPLETED' || data.status === 'FAILED') break;
        }

        if (job?.status === 'COMPLETED') {
          setResult(job.result);
          setPhase('done');
        } else {
          throw new Error(job?.error ?? 'Processing failed');
        }
      } catch (e) {
        setErrorMsg(e instanceof Error ? e.message : 'An error occurred');
        setPhase('error');
      }
    },
    [slug]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (f) => { void onDrop(f); },
    accept: { 'image/*': [], 'application/pdf': [] },
    maxFiles: 1,
    maxSize: 25 * 1024 * 1024,
  });

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-bold capitalize text-white">
          {slug?.replace(/-/g, ' ')}
        </h1>
        <p className="mt-1 text-sm text-gray-400">Upload an image or PDF to get started</p>
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`card flex cursor-pointer flex-col items-center justify-center gap-3 p-12 text-center transition ${
          isDragActive ? 'border-indigo-500 bg-indigo-500/5' : 'hover:border-gray-600'
        }`}
      >
        <input {...getInputProps()} />
        <Upload size={32} className="text-gray-500" />
        <p className="text-sm text-gray-400">
          {isDragActive ? 'Drop it here…' : 'Drag & drop an image or PDF, or click to browse'}
        </p>
        <p className="text-xs text-gray-600">Max 25MB · JPEG, PNG, WebP, HEIC, PDF</p>
      </div>

      {/* Status */}
      {phase === 'uploading' && (
        <div className="card flex items-center gap-3 p-4 text-sm text-gray-300">
          <Loader2 size={16} className="animate-spin text-indigo-400" />
          Uploading file…
        </div>
      )}
      {phase === 'processing' && (
        <div className="card flex items-center gap-3 p-4 text-sm text-gray-300">
          <Loader2 size={16} className="animate-spin text-indigo-400" />
          Processing with AI… this may take up to 30s
        </div>
      )}
      {phase === 'error' && (
        <div className="card flex items-center gap-3 border-red-800/50 bg-red-900/10 p-4 text-sm text-red-400">
          <AlertCircle size={16} />
          {errorMsg}
        </div>
      )}
      {phase === 'done' && (
        <div className="card space-y-3 p-6">
          <div className="flex items-center gap-2 text-green-400">
            <CheckCircle size={16} />
            <span className="text-sm font-medium">Processing complete</span>
          </div>
          <pre className="overflow-auto rounded-lg bg-gray-950 p-4 text-xs text-gray-300">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
