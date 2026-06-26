import { useEffect, useRef, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import type { Job } from '@/types';

interface JobPollerProps {
  jobId: string;
  onComplete: (result: Record<string, unknown>) => void;
  onError: (error: string) => void;
}

const POLL_INTERVAL_MS = 2000;
const MAX_POLLS = 90; // 3 minutes max

export function JobPoller({ jobId, onComplete, onError }: JobPollerProps) {
  const pollCount = useRef(0);
  const [statusMsg, setStatusMsg] = useState('Processing…');

  useEffect(() => {
    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout>;

    const poll = async () => {
      if (cancelled) return;
      try {
        const { data } = await api.get<Job>(`/jobs/${jobId}`);

        if (data.status === 'COMPLETED') {
          if (!cancelled) onComplete(data.result as Record<string, unknown>);
          return;
        }

        if (data.status === 'FAILED') {
          if (!cancelled) onError(data.error ?? 'Processing failed');
          return;
        }

        pollCount.current += 1;
        if (pollCount.current >= MAX_POLLS) {
          onError('Processing timed out. Please try again.');
          return;
        }

        const pct = Math.min(Math.round((pollCount.current / MAX_POLLS) * 100), 95);
        setStatusMsg(`Processing… ${pct}%`);
        timeoutId = setTimeout(() => {
          void poll();
        }, POLL_INTERVAL_MS);
      } catch {
        if (!cancelled) onError('Failed to check job status');
      }
    };

    timeoutId = setTimeout(() => {
      void poll();
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [jobId, onComplete, onError]);

  return (
    <div className="flex items-center gap-3 rounded-xl border border-indigo-500/30 bg-indigo-500/5 p-4 text-sm text-gray-300">
      <Loader2 size={16} className="animate-spin text-indigo-400" />
      <div>
        <p className="font-medium text-indigo-300">{statusMsg}</p>
        <p className="text-xs text-gray-500">This may take up to 30 seconds</p>
      </div>
    </div>
  );
}
