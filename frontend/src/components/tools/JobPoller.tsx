import { useEffect, useRef, useState } from 'react';
import { Loader2, Clock } from 'lucide-react';
import { api } from '@/lib/api';
import type { Job } from '@/types';

interface JobPollerProps {
  jobId: string;
  onComplete: (result: Record<string, unknown>) => void;
  onError: (error: string) => void;
}

// Polling strategy: exponential backoff
// Starts at 1s, doubles each time up to 8s max, total timeout ~5 minutes
const BASE_INTERVAL_MS = 1000;
const MAX_INTERVAL_MS = 8000;
const TOTAL_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

const STATUS_MESSAGES = [
  'Sending to AI engine…',
  'Warming up model…',
  'Analysing image…',
  'Running inference…',
  'Almost there…',
  'Finalising results…',
];

export function JobPoller({ jobId, onComplete, onError }: JobPollerProps) {
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState(STATUS_MESSAGES[0]);
  const [elapsedSec, setElapsedSec] = useState(0);
  const startTimeRef = useRef(Date.now());
  const pollCountRef = useRef(0);
  const intervalMsRef = useRef(BASE_INTERVAL_MS);

  // Tick elapsed timer every second for display
  useEffect(() => {
    const ticker = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);
    return () => clearInterval(ticker);
  }, []);

  useEffect(() => {
    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout>;

    const poll = async () => {
      if (cancelled) return;

      const elapsed = Date.now() - startTimeRef.current;
      if (elapsed >= TOTAL_TIMEOUT_MS) {
        if (!cancelled) onError('Processing timed out after 5 minutes. Please try again.');
        return;
      }

      try {
        const { data } = await api.get<Job>(`/jobs/${jobId}`);

        if (data.status === 'COMPLETED') {
          if (!cancelled) {
            setProgress(100);
            onComplete(data.result as Record<string, unknown>);
          }
          return;
        }

        if (data.status === 'FAILED') {
          if (!cancelled) onError(data.error ?? 'Processing failed. Please try again.');
          return;
        }

        // Update progress and message
        pollCountRef.current += 1;
        const rawProgress = Math.min(
          Math.round((elapsed / TOTAL_TIMEOUT_MS) * 95),
          95
        );
        // Clamp to a minimum that grows steadily based on poll count too
        const minProgress = Math.min(pollCountRef.current * 4, 85);
        const displayProgress = Math.max(rawProgress, minProgress);
        setProgress(displayProgress);

        const msgIdx = Math.min(
          Math.floor(displayProgress / (100 / STATUS_MESSAGES.length)),
          STATUS_MESSAGES.length - 1
        );
        setStatusMsg(
          data.status === 'PROCESSING'
            ? STATUS_MESSAGES[msgIdx]
            : `Queued — waiting for worker…`
        );

        // Exponential backoff
        intervalMsRef.current = Math.min(intervalMsRef.current * 1.5, MAX_INTERVAL_MS);
        timeoutId = setTimeout(() => { void poll(); }, intervalMsRef.current);
      } catch {
        // Network hiccup — retry with backoff instead of failing immediately
        if (Date.now() - startTimeRef.current >= TOTAL_TIMEOUT_MS) {
          if (!cancelled) onError('Connection lost. Please check your network and try again.');
          return;
        }
        intervalMsRef.current = Math.min(intervalMsRef.current * 2, MAX_INTERVAL_MS);
        if (!cancelled) {
          setStatusMsg('Connection issue — retrying…');
          timeoutId = setTimeout(() => { void poll(); }, intervalMsRef.current);
        }
      }
    };

    // First poll after a short delay
    timeoutId = setTimeout(() => { void poll(); }, BASE_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [jobId, onComplete, onError]);

  const formatTime = (sec: number) => {
    if (sec < 60) return `${sec}s`;
    return `${Math.floor(sec / 60)}m ${sec % 60}s`;
  };

  return (
    <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/5 p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <Loader2 size={16} className="animate-spin text-indigo-400 shrink-0" />
          <div>
            <p className="text-sm font-medium text-indigo-300">{statusMsg}</p>
            <p className="text-xs text-gray-500 mt-0.5">
              AI processing usually takes 5–30 seconds
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Clock size={11} />
          <span>{formatTime(elapsedSec)}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="space-y-1.5">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-800">
          <div
            className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-cyan-500 transition-all duration-700 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-600">
          <span>Processing</span>
          <span>{progress}%</span>
        </div>
      </div>
    </div>
  );
}
