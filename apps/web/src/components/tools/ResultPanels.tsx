/**
 * Sprint 1 result panels: Receipt, Invoice, Business Card (S1-07)
 */

import { Download, Copy, CheckCircle, User, Mail, Phone, Globe, MapPin } from 'lucide-react';
import { useState } from 'react';
import { api } from '@/lib/api';

// ─────────────────────────────────────────────────────────────────────────────
// Shared helpers
// ─────────────────────────────────────────────────────────────────────────────

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      onClick={() => { void copy(); }}
      className="flex items-center gap-1 rounded px-2 py-1 text-xs text-gray-400 hover:bg-gray-700 hover:text-white"
    >
      {copied ? <CheckCircle size={12} className="text-green-400" /> : <Copy size={12} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  );
}

function ConfidenceBadge({ score }: { score: number }) {
  const color =
    score >= 80 ? 'text-green-400 bg-green-400/10' :
    score >= 60 ? 'text-yellow-400 bg-yellow-400/10' :
    'text-red-400 bg-red-400/10';
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${color}`}>
      {score}% confidence
    </span>
  );
}

function DownloadButton({
  jobId,
  slug,
  format,
  label,
}: {
  jobId: string;
  slug: string;
  format: string;
  label: string;
}) {
  const [loading, setLoading] = useState(false);
  const download = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/tools/${slug}/export/${jobId}?format=${format}`, {
        responseType: 'blob',
      });
      const url = URL.createObjectURL(response.data as Blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${slug}_${jobId.slice(0, 8)}.${format === 'qb_csv' ? 'csv' : format}`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setLoading(false);
    }
  };
  return (
    <button
      onClick={() => { void download(); }}
      disabled={loading}
      className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
    >
      <Download size={12} />
      {loading ? 'Downloading…' : label}
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Receipt Result Panel
// ─────────────────────────────────────────────────────────────────────────────

interface LineItem {
  name: string;
  qty?: number;
  price: number;
}

interface ReceiptResult {
  merchant?: string;
  date?: string | null;
  currency?: string;
  line_items?: LineItem[];
  subtotal?: number | null;
  tax?: number | null;
  total?: number | null;
  confidence_score?: number;
}

export function ReceiptResultPanel({ result, jobId }: { result: ReceiptResult; jobId: string }) {
  const fmt = (v: number | null | undefined) =>
    v != null ? `${result.currency ?? ''} ${v.toFixed(2)}` : '—';

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-white">{result.merchant ?? 'Unknown Merchant'}</h3>
          {result.date && <p className="text-xs text-gray-500">{result.date}</p>}
        </div>
        {result.confidence_score != null && <ConfidenceBadge score={result.confidence_score} />}
      </div>

      {(result.line_items ?? []).length > 0 && (
        <div className="overflow-hidden rounded-lg border border-gray-700/50">
          <table className="w-full text-sm">
            <thead className="bg-gray-800/50">
              <tr>
                <th className="px-3 py-2 text-left text-xs text-gray-400">Item</th>
                <th className="px-3 py-2 text-right text-xs text-gray-400">Price</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/30">
              {result.line_items?.map((item, i) => (
                <tr key={i} className="hover:bg-gray-800/30">
                  <td className="px-3 py-2 text-gray-300">{item.name}</td>
                  <td className="px-3 py-2 text-right text-gray-300">{fmt(item.price)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="space-y-1.5 rounded-lg bg-gray-800/50 p-3">
        <div className="flex justify-between text-sm text-gray-400">
          <span>Subtotal</span><span>{fmt(result.subtotal)}</span>
        </div>
        <div className="flex justify-between text-sm text-gray-400">
          <span>Tax</span><span>{fmt(result.tax)}</span>
        </div>
        <div className="flex justify-between border-t border-gray-700 pt-1.5 text-sm font-semibold text-white">
          <span>Total</span><span>{fmt(result.total)}</span>
        </div>
      </div>

      <div className="flex gap-2">
        <DownloadButton jobId={jobId} slug="receipt-scanner" format="csv" label="CSV" />
        <DownloadButton jobId={jobId} slug="receipt-scanner" format="qb_csv" label="QuickBooks CSV" />
        <DownloadButton jobId={jobId} slug="receipt-scanner" format="json" label="JSON" />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Invoice Result Panel
// ─────────────────────────────────────────────────────────────────────────────

interface InvoiceLineItem {
  name: string;
  qty?: number;
  unit_price?: number;
  amount?: number;
}

interface InvoiceResult {
  invoice_number?: string | null;
  supplier_name?: string;
  buyer_name?: string | null;
  date?: string | null;
  due_date?: string | null;
  payment_terms?: string | null;
  line_items?: InvoiceLineItem[];
  subtotal?: number | null;
  tax?: number | null;
  total?: number | null;
  confidence_score?: number;
}

export function InvoiceResultPanel({ result, jobId }: { result: InvoiceResult; jobId: string }) {
  const fmt = (v: number | null | undefined) =>
    v != null ? v.toFixed(2) : '—';

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold text-white">
            {result.invoice_number ? `Invoice #${result.invoice_number}` : 'Invoice'}
          </h3>
          <p className="text-xs text-gray-500">{result.supplier_name}</p>
        </div>
        {result.confidence_score != null && <ConfidenceBadge score={result.confidence_score} />}
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        {[
          ['Issue Date', result.date],
          ['Due Date', result.due_date],
          ['Payment Terms', result.payment_terms],
          ['Buyer', result.buyer_name],
        ].map(([label, value]) =>
          value ? (
            <div key={String(label)} className="rounded-lg bg-gray-800/50 p-2.5">
              <p className="text-xs text-gray-500">{label}</p>
              <p className="mt-0.5 font-medium text-gray-200">{value}</p>
            </div>
          ) : null
        )}
      </div>

      {(result.line_items ?? []).length > 0 && (
        <div className="overflow-hidden rounded-lg border border-gray-700/50">
          <table className="w-full text-sm">
            <thead className="bg-gray-800/50">
              <tr>
                <th className="px-3 py-2 text-left text-xs text-gray-400">Description</th>
                <th className="px-3 py-2 text-right text-xs text-gray-400">Qty</th>
                <th className="px-3 py-2 text-right text-xs text-gray-400">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/30">
              {result.line_items?.map((item, i) => (
                <tr key={i} className="hover:bg-gray-800/30">
                  <td className="px-3 py-2 text-gray-300">{item.name}</td>
                  <td className="px-3 py-2 text-right text-gray-400">{item.qty ?? 1}</td>
                  <td className="px-3 py-2 text-right text-gray-300">{fmt(item.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="space-y-1.5 rounded-lg bg-gray-800/50 p-3">
        <div className="flex justify-between text-sm text-gray-400">
          <span>Subtotal</span><span>{fmt(result.subtotal)}</span>
        </div>
        <div className="flex justify-between text-sm text-gray-400">
          <span>Tax</span><span>{fmt(result.tax)}</span>
        </div>
        <div className="flex justify-between border-t border-gray-700 pt-1.5 text-sm font-semibold text-white">
          <span>Total Due</span><span>{fmt(result.total)}</span>
        </div>
      </div>

      <div className="flex gap-2">
        <DownloadButton jobId={jobId} slug="invoice-reader" format="csv" label="CSV" />
        <DownloadButton jobId={jobId} slug="invoice-reader" format="json" label="JSON" />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Business Card Result Panel
// ─────────────────────────────────────────────────────────────────────────────

interface BizCardResult {
  full_name?: string | null;
  job_title?: string | null;
  company?: string | null;
  emails?: string[];
  phones?: string[];
  websites?: string[];
  address?: string | null;
  social_handles?: Record<string, string>;
  confidence_score?: number;
}

export function BusinessCardResultPanel({ result, jobId }: { result: BizCardResult; jobId: string }) {
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-500/20">
            <User size={20} className="text-indigo-400" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">{result.full_name ?? 'Unknown'}</h3>
            {result.job_title && <p className="text-sm text-gray-400">{result.job_title}</p>}
            {result.company && <p className="text-xs text-gray-500">{result.company}</p>}
          </div>
        </div>
        {result.confidence_score != null && <ConfidenceBadge score={result.confidence_score} />}
      </div>

      <div className="space-y-2">
        {result.emails?.map((email) => (
          <div key={email} className="flex items-center justify-between gap-2 rounded-lg bg-gray-800/50 px-3 py-2">
            <div className="flex items-center gap-2 text-sm text-gray-300">
              <Mail size={14} className="text-indigo-400" />
              <a href={`mailto:${email}`} className="hover:text-white">{email}</a>
            </div>
            <CopyButton text={email} />
          </div>
        ))}

        {result.phones?.map((phone) => (
          <div key={phone} className="flex items-center justify-between gap-2 rounded-lg bg-gray-800/50 px-3 py-2">
            <div className="flex items-center gap-2 text-sm text-gray-300">
              <Phone size={14} className="text-green-400" />
              <a href={`tel:${phone}`} className="hover:text-white">{phone}</a>
            </div>
            <CopyButton text={phone} />
          </div>
        ))}

        {result.websites?.map((url) => (
          <div key={url} className="flex items-center gap-2 rounded-lg bg-gray-800/50 px-3 py-2 text-sm text-gray-300">
            <Globe size={14} className="text-cyan-400" />
            <a href={url} target="_blank" rel="noopener noreferrer" className="hover:text-white">{url}</a>
          </div>
        ))}

        {result.address && (
          <div className="flex items-center gap-2 rounded-lg bg-gray-800/50 px-3 py-2 text-sm text-gray-300">
            <MapPin size={14} className="text-red-400" />
            {result.address}
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <DownloadButton jobId={jobId} slug="business-card-scanner" format="vcf" label="vCard (.vcf)" />
        <DownloadButton jobId={jobId} slug="business-card-scanner" format="csv" label="CSV" />
        <DownloadButton jobId={jobId} slug="business-card-scanner" format="json" label="JSON" />
      </div>
    </div>
  );
}
