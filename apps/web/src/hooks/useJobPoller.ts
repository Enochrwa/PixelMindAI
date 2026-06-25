import { useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api';
import type { Job, JobStatus } from '@/types';

interface UseJobPollerOptions {
  jobId: string | null;
  intervalMs?: number;
  maxAttempts?: number;
}

interface UseJobPollerResult {
  job: Job | null;
  status: JobStatus | null;
  isPolling: boolean;
  error: string | null;
}

export function useJobPoller({
  jobId,
  intervalMs = 2000,
  maxAttempts = 60,
}: UseJobPollerOptions): UseJobPollerResult {
  const [job, setJob] = useState<Job | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const attemptsRef = useRef(0);

  useEffect(() => {
    if (!jobId) return;

    setIsPolling(true);
    attemptsRef.current = 0;

    const interval = setInterval(async () => {
      attemptsRef.current += 1;
      try {
        const { data } = await api.get<Job>(`/jobs/${jobId}`);
        setJob(data);
        if (data.status === 'COMPLETED' || data.status === 'FAILED') {
          clearInterval(interval);
          setIsPolling(false);
          if (data.status === 'FAILED') {
            setError(data.error ?? 'Processing failed');
          }
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Polling error');
        clearInterval(interval);
        setIsPolling(false);
      }
      if (attemptsRef.current >= maxAttempts) {
        clearInterval(interval);
        setIsPolling(false);
        setError('Processing timed out');
      }
    }, intervalMs);

    return () => clearInterval(interval);
  }, [jobId, intervalMs, maxAttempts]);

  return { job, status: job?.status ?? null, isPolling, error };
}
