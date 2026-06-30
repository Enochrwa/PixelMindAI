import type { JobStatus } from './types';

const styles: Record<JobStatus, string> = {
  QUEUED: 'bg-gray-700 text-gray-300',
  PROCESSING: 'bg-indigo-700/30 text-indigo-300',
  COMPLETED: 'bg-green-700/30 text-green-300',
  FAILED: 'bg-red-700/30 text-red-300',
};

interface StatusBadgeProps {
  status: JobStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[status]}`}
    >
      {status}
    </span>
  );
}
