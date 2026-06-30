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
      onClick={() => {
        void copy();
      }}
      className="flex items-center gap-1 rounded px-2 py-1 text-xs text-gray-400 hover:bg-gray-700 hover:text-white"
    >
      {copied ? <CheckCircle size={12} className="text-green-400" /> : <Copy size={12} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  );
}

function ConfidenceBadge({ score }: { score: number }) {
  const color =
    score >= 80
      ? 'text-green-400 bg-green-400/10'
      : score >= 60
        ? 'text-yellow-400 bg-yellow-400/10'
        : 'text-red-400 bg-red-400/10';
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
      onClick={() => {
        void download();
      }}
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
          <h3 className="text-base font-semibold text-white">
            {result.merchant ?? 'Unknown Merchant'}
          </h3>
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
          <span>Subtotal</span>
          <span>{fmt(result.subtotal)}</span>
        </div>
        <div className="flex justify-between text-sm text-gray-400">
          <span>Tax</span>
          <span>{fmt(result.tax)}</span>
        </div>
        <div className="flex justify-between border-t border-gray-700 pt-1.5 text-sm font-semibold text-white">
          <span>Total</span>
          <span>{fmt(result.total)}</span>
        </div>
      </div>

      <div className="flex gap-2">
        <DownloadButton jobId={jobId} slug="receipt-scanner" format="csv" label="CSV" />
        <DownloadButton
          jobId={jobId}
          slug="receipt-scanner"
          format="qb_csv"
          label="QuickBooks CSV"
        />
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
  const fmt = (v: number | null | undefined) => (v != null ? v.toFixed(2) : '—');

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
          <span>Subtotal</span>
          <span>{fmt(result.subtotal)}</span>
        </div>
        <div className="flex justify-between text-sm text-gray-400">
          <span>Tax</span>
          <span>{fmt(result.tax)}</span>
        </div>
        <div className="flex justify-between border-t border-gray-700 pt-1.5 text-sm font-semibold text-white">
          <span>Total Due</span>
          <span>{fmt(result.total)}</span>
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

export function BusinessCardResultPanel({
  result,
  jobId,
}: {
  result: BizCardResult;
  jobId: string;
}) {
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
          <div
            key={email}
            className="flex items-center justify-between gap-2 rounded-lg bg-gray-800/50 px-3 py-2"
          >
            <div className="flex items-center gap-2 text-sm text-gray-300">
              <Mail size={14} className="text-indigo-400" />
              <a href={`mailto:${email}`} className="hover:text-white">
                {email}
              </a>
            </div>
            <CopyButton text={email} />
          </div>
        ))}

        {result.phones?.map((phone) => (
          <div
            key={phone}
            className="flex items-center justify-between gap-2 rounded-lg bg-gray-800/50 px-3 py-2"
          >
            <div className="flex items-center gap-2 text-sm text-gray-300">
              <Phone size={14} className="text-green-400" />
              <a href={`tel:${phone}`} className="hover:text-white">
                {phone}
              </a>
            </div>
            <CopyButton text={phone} />
          </div>
        ))}

        {result.websites?.map((url) => (
          <div
            key={url}
            className="flex items-center gap-2 rounded-lg bg-gray-800/50 px-3 py-2 text-sm text-gray-300"
          >
            <Globe size={14} className="text-cyan-400" />
            <a href={url} target="_blank" rel="noopener noreferrer" className="hover:text-white">
              {url}
            </a>
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
        <DownloadButton
          jobId={jobId}
          slug="business-card-scanner"
          format="vcf"
          label="vCard (.vcf)"
        />
        <DownloadButton jobId={jobId} slug="business-card-scanner" format="csv" label="CSV" />
        <DownloadButton jobId={jobId} slug="business-card-scanner" format="json" label="JSON" />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Sprint 2 — Handwriting OCR Result Panel
// ─────────────────────────────────────────────────────────────────────────────

interface HandwritingParagraph {
  text: string;
  confidence: number;
}

interface HandwritingBlock {
  type: 'heading' | 'bullet_list' | 'numbered_list' | 'paragraph';
  text: string;
  confidence: number;
}

interface HandwritingResult {
  raw_text?: string;
  paragraphs?: HandwritingParagraph[];
  word_count?: number;
  language_detected?: string;
  confidence_score?: number;
  structured_blocks?: HandwritingBlock[];
}

export function HandwritingResultPanel({
  result,
  jobId,
}: {
  result: HandwritingResult;
  jobId: string;
}) {
  const [view, setView] = useState<'text' | 'structured'>('text');
  const rawText = result.raw_text ?? '';

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {result.word_count != null && (
            <span className="rounded-full bg-gray-700 px-2 py-0.5 text-xs text-gray-300">
              {result.word_count} words
            </span>
          )}
          {result.language_detected && (
            <span className="rounded-full bg-gray-700 px-2 py-0.5 text-xs uppercase text-gray-300">
              {result.language_detected}
            </span>
          )}
        </div>
        {result.confidence_score != null && <ConfidenceBadge score={result.confidence_score} />}
      </div>

      {result.structured_blocks && result.structured_blocks.length > 0 && (
        <div className="flex rounded-lg bg-gray-800/50 p-1">
          {(['text', 'structured'] as const).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`flex-1 rounded-md py-1.5 text-xs font-medium capitalize transition-colors ${
                view === v ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              {v === 'text' ? 'Plain Text' : 'Structured'}
            </button>
          ))}
        </div>
      )}

      {view === 'text' ? (
        <div className="relative">
          <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-lg bg-gray-900 p-4 text-sm leading-relaxed text-gray-300">
            {rawText || '(no text detected)'}
          </pre>
          {rawText && <CopyButton text={rawText} />}
        </div>
      ) : (
        <div className="space-y-2">
          {result.structured_blocks?.map((block, i) => (
            <div key={i} className="rounded-lg bg-gray-800/50 p-3">
              <span className="mb-1 inline-block rounded bg-indigo-500/10 px-1.5 py-0.5 text-xs text-indigo-400">
                {block.type.replace('_', ' ')}
              </span>
              <p className="mt-1 whitespace-pre-wrap text-sm text-gray-300">{block.text}</p>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <DownloadButton jobId={jobId} slug="handwriting-ocr" format="csv" label=".txt" />
        <DownloadButton jobId={jobId} slug="handwriting-ocr" format="json" label="JSON" />
        <CopyButton text={rawText} />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Sprint 2 — Menu Scanner Result Panel
// ─────────────────────────────────────────────────────────────────────────────

interface MenuItem {
  name: string;
  description?: string;
  price?: number;
}

interface MenuCategory {
  name: string;
  items: MenuItem[];
}

interface MenuResult {
  restaurant_name?: string;
  currency?: string;
  categories?: MenuCategory[];
  total_items?: number;
  confidence_score?: number;
}

export function MenuResultPanel({ result, jobId }: { result: MenuResult; jobId: string }) {
  const [openCat, setOpenCat] = useState<number | null>(0);
  const fmt = (v: number | undefined) =>
    v != null ? `${result.currency ?? ''} ${v.toLocaleString()}` : '—';

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">{result.restaurant_name ?? 'Menu'}</h3>
          <p className="text-xs text-gray-500">
            {result.total_items ?? 0} items · {result.currency ?? 'USD'}
          </p>
        </div>
        {result.confidence_score != null && <ConfidenceBadge score={result.confidence_score} />}
      </div>

      <div className="space-y-2">
        {(result.categories ?? []).map((cat, ci) => (
          <div key={ci} className="overflow-hidden rounded-lg border border-gray-700/50">
            <button
              className="flex w-full items-center justify-between px-4 py-2.5 text-left text-sm font-medium text-gray-200 hover:bg-gray-800/50"
              onClick={() => setOpenCat(openCat === ci ? null : ci)}
            >
              <span>{cat.name}</span>
              <span className="text-xs text-gray-500">{cat.items.length} items</span>
            </button>
            {openCat === ci && (
              <div className="divide-y divide-gray-700/30">
                {cat.items.map((item, ii) => (
                  <div key={ii} className="flex items-start justify-between px-4 py-2">
                    <div>
                      <p className="text-sm text-gray-200">{item.name}</p>
                      {item.description && (
                        <p className="text-xs text-gray-500">{item.description}</p>
                      )}
                    </div>
                    <span className="ml-4 whitespace-nowrap text-sm text-indigo-300">
                      {fmt(item.price)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <DownloadButton jobId={jobId} slug="menu-scanner" format="csv" label="CSV" />
        <DownloadButton jobId={jobId} slug="menu-scanner" format="json" label="JSON" />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Sprint 2 — Document Scanner Result Panel
// ─────────────────────────────────────────────────────────────────────────────

interface DocumentScanResult {
  result_image_b64?: string;
  format?: string;
  mode?: string;
  width_px?: number;
  height_px?: number;
  quality_score?: number;
  // multi-page PDF
  pdf_b64?: string;
  page_count?: number;
}

export function DocumentScannerResultPanel({ result }: { result: DocumentScanResult }) {
  const downloadImg = () => {
    if (!result.result_image_b64) return;
    const a = document.createElement('a');
    a.href = `data:image/jpeg;base64,${result.result_image_b64}`;
    a.download = `scanned_document.jpg`;
    a.click();
  };

  const downloadPdf = () => {
    if (!result.pdf_b64) return;
    const bytes = atob(result.pdf_b64);
    const arr = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
    const blob = new Blob([arr], { type: 'application/pdf' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'scanned_document.pdf';
    a.click();
    URL.revokeObjectURL(a.href);
  };

  if (result.pdf_b64) {
    return (
      <div className="space-y-4 text-center">
        <div className="rounded-lg bg-gray-800/50 p-6">
          <p className="text-2xl font-bold text-white">{result.page_count ?? '?'}</p>
          <p className="text-sm text-gray-400">pages scanned</p>
        </div>
        <button
          onClick={downloadPdf}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          <Download size={14} /> Download PDF
        </button>
      </div>
    );
  }

  if (!result.result_image_b64) {
    return <p className="text-sm text-gray-400">No result image available.</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-xs text-gray-400">
        <span className="rounded-full bg-gray-700 px-2 py-0.5 capitalize">
          {result.mode?.replace('_', ' ') ?? 'enhanced'}
        </span>
        <span>
          {result.width_px} × {result.height_px}px
        </span>
        {result.quality_score != null && <ConfidenceBadge score={result.quality_score} />}
      </div>

      <img
        src={`data:image/jpeg;base64,${result.result_image_b64}`}
        alt="Scanned document"
        className="w-full rounded-lg border border-gray-700/50 object-contain"
      />

      <button
        onClick={downloadImg}
        className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
      >
        <Download size={14} /> Download Image
      </button>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Sprint 2 — Signature Extractor Result Panel
// ─────────────────────────────────────────────────────────────────────────────

interface SignatureBbox {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface Signature {
  bbox: SignatureBbox;
  image_b64: string;
  confidence: number;
  format: string;
}

interface SignatureResult {
  signatures?: Signature[];
  signature_count?: number;
  image_width?: number;
  image_height?: number;
}

export function SignatureExtractorResultPanel({ result }: { result: SignatureResult }) {
  const sigs = result.signatures ?? [];

  const downloadSig = (sig: Signature, idx: number) => {
    const a = document.createElement('a');
    a.href = `data:image/png;base64,${sig.image_b64}`;
    a.download = `signature_${idx + 1}.png`;
    a.click();
  };

  const downloadAll = () => {
    sigs.forEach((sig, i) => downloadSig(sig, i));
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-300">
          {result.signature_count ?? 0} signature{result.signature_count !== 1 ? 's' : ''} detected
        </p>
        {sigs.length > 1 && (
          <button
            onClick={downloadAll}
            className="flex items-center gap-1.5 rounded-lg bg-gray-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-600"
          >
            <Download size={12} /> Download All
          </button>
        )}
      </div>

      {sigs.length === 0 ? (
        <p className="rounded-lg bg-gray-800/50 p-4 text-center text-sm text-gray-400">
          No signatures detected in this document.
        </p>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {sigs.map((sig, i) => (
            <div key={i} className="space-y-2 rounded-lg border border-gray-700/50 p-3">
              <img
                src={`data:image/png;base64,${sig.image_b64}`}
                alt={`Signature ${i + 1}`}
                className="w-full rounded bg-white object-contain"
              />
              <div className="flex items-center justify-between">
                <ConfidenceBadge score={sig.confidence} />
                <button
                  onClick={() => downloadSig(sig, i)}
                  className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300"
                >
                  <Download size={10} /> PNG
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Sprint 2 — Form Field Reader Result Panel
// ─────────────────────────────────────────────────────────────────────────────

interface FormField {
  field_bbox: { x: number; y: number; width: number; height: number };
  label_text: string;
  value_text: string;
  confidence: number;
  zone?: string;
  row?: number;
}

interface FormFieldResult {
  fields?: FormField[];
  field_count?: number;
  image_width?: number;
  image_height?: number;
  lines_detected?: number;
}

export function FormFieldResultPanel({ result }: { result: FormFieldResult }) {
  const fields = result.fields ?? [];
  const filled = fields.filter((f) => f.value_text?.trim());

  const copyAll = () => {
    const text = fields.map((f) => `${f.label_text || 'Field'}: ${f.value_text}`).join('\n');
    void navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-3">
          <span className="rounded-full bg-gray-700 px-2 py-0.5 text-xs text-gray-300">
            {result.field_count ?? 0} fields
          </span>
          <span className="rounded-full bg-green-500/10 px-2 py-0.5 text-xs text-green-400">
            {filled.length} with values
          </span>
        </div>
        <button
          onClick={copyAll}
          className="flex items-center gap-1 text-xs text-gray-400 hover:text-white"
        >
          <Copy size={12} /> Copy All
        </button>
      </div>

      {fields.length === 0 ? (
        <p className="rounded-lg bg-gray-800/50 p-4 text-center text-sm text-gray-400">
          No form fields detected.
        </p>
      ) : (
        <div className="space-y-2">
          {fields.map((field, i) => (
            <div
              key={i}
              className="flex items-start justify-between gap-4 rounded-lg bg-gray-800/50 px-3 py-2.5"
            >
              <div className="min-w-0">
                {field.label_text && <p className="text-xs text-gray-500">{field.label_text}</p>}
                <p className="mt-0.5 text-sm text-gray-200">
                  {field.value_text || <span className="italic text-gray-600">empty</span>}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <ConfidenceBadge score={field.confidence} />
                {field.value_text && <CopyButton text={field.value_text} />}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Sprint 3 — Background Remover Result Panel (S3-06)
// ─────────────────────────────────────────────────────────────────────────────

export interface BackgroundRemoverResult {
  result_image_b64: string;
  format: 'png' | 'jpeg';
  method: 'u2net' | 'grabcut';
  background_mode: string;
  width_px: number;
  height_px: number;
}

export function BackgroundRemoverResultPanel({
  result,
  jobId,
}: {
  result: BackgroundRemoverResult;
  jobId: string;
}) {
  const [sliderX, setSliderX] = useState(50);
  const [activeBgMode, setActiveBgMode] = useState(result.background_mode ?? 'transparent');
  const [currentResult, setCurrentResult] = useState(result);
  const [reprocessing, setReprocessing] = useState(false);

  const mimeType = currentResult.format === 'png' ? 'image/png' : 'image/jpeg';
  const dataUrl = `data:${mimeType};base64,${currentResult.result_image_b64}`;
  const fileSizeKb = Math.round((currentResult.result_image_b64.length * 3) / 4 / 1024);

  const bgModes = [
    { key: 'transparent', label: 'Transparent' },
    { key: 'white', label: 'White' },
    { key: 'color', label: 'Color' },
    { key: 'blur', label: 'Blur' },
  ] as const;

  const resubmit = async (newMode: string) => {
    setReprocessing(true);
    setActiveBgMode(newMode);
    try {
      const { data: jobData } = await api.post<{ job_id: string }>(
        '/tools/background-remover/process',
        { file_id: jobId, options: { bg_mode: newMode } }
      );
      // Poll for result
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        const { data: job } = await api.get<{ status: string; result: BackgroundRemoverResult }>(
          `/jobs/${jobData.job_id}`
        );
        if (job.status === 'COMPLETED' && job.result) {
          clearInterval(poll);
          setCurrentResult(job.result);
          setReprocessing(false);
        } else if (job.status === 'FAILED' || attempts > 30) {
          clearInterval(poll);
          setReprocessing(false);
        }
      }, 2000);
    } catch {
      setReprocessing(false);
    }
  };

  const downloadImage = () => {
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = `bg-removed.${currentResult.format}`;
    a.click();
  };

  return (
    <div className="space-y-4">
      {/* Method badge + dimensions */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
            currentResult.method === 'u2net'
              ? 'bg-indigo-500/15 text-indigo-300'
              : 'bg-amber-500/15 text-amber-300'
          }`}
        >
          {currentResult.method === 'u2net' ? '✨ U2Net AI' : '⚙️ OpenCV GrabCut'}
        </span>
        <span className="text-xs text-gray-500">
          {currentResult.width_px} × {currentResult.height_px}px · ~{fileSizeKb}KB
        </span>
      </div>

      {/* Before/After slider */}
      <div
        className="bg-checkered relative overflow-hidden rounded-xl border border-gray-700/50"
        style={{
          background: 'repeating-conic-gradient(#374151 0% 25%, #1f2937 0% 50%) 0 0 / 20px 20px',
        }}
      >
        <div className="relative select-none" style={{ minHeight: '200px' }}>
          {/* After (result) — full width behind */}
          <img
            src={dataUrl}
            alt="Background removed"
            className="w-full rounded-xl object-contain"
            style={{ maxHeight: '400px' }}
          />
          {/* Before (gray overlay simulating original) */}
          <div
            className="absolute inset-0 overflow-hidden"
            style={{ clipPath: `inset(0 ${100 - sliderX}% 0 0)` }}
          >
            <div className="absolute inset-0 flex items-center justify-center bg-gray-600/60">
              <span className="text-xs font-medium text-white/70">Original</span>
            </div>
          </div>
          {/* Slider handle */}
          <div
            className="absolute bottom-0 top-0 w-0.5 cursor-ew-resize bg-white"
            style={{ left: `${sliderX}%` }}
          >
            <div className="absolute top-1/2 flex h-7 w-7 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-white text-xs font-bold text-gray-800 shadow-lg">
              ↔
            </div>
          </div>
          {/* Drag area */}
          <input
            type="range"
            min={0}
            max={100}
            value={sliderX}
            onChange={(e) => setSliderX(Number(e.target.value))}
            className="absolute inset-0 h-full w-full cursor-ew-resize opacity-0"
          />
        </div>
      </div>

      {/* Background mode selector */}
      <div>
        <p className="mb-2 text-xs font-medium text-gray-400">Background replacement</p>
        <div className="grid grid-cols-4 gap-1.5">
          {bgModes.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => {
                void resubmit(key);
              }}
              disabled={reprocessing}
              className={`rounded-lg px-2 py-1.5 text-xs font-medium transition-colors ${
                activeBgMode === key
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              } disabled:opacity-50`}
            >
              {reprocessing && activeBgMode === key ? (
                <span className="inline-flex items-center gap-1">
                  <span className="h-2.5 w-2.5 animate-spin rounded-full border border-white border-t-transparent" />
                </span>
              ) : (
                label
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Download buttons */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={downloadImage}
          className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500"
        >
          <Download size={12} />
          Download {currentResult.format.toUpperCase()}
        </button>
        <DownloadButton jobId={jobId} slug="background-remover" format="json" label="JSON" />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Sprint 3 — Passport Photo Result Panel (S3-06)
// ─────────────────────────────────────────────────────────────────────────────

export interface PassportPhotoSpec {
  width_mm: number;
  height_mm: number;
  width_px: number;
  height_px: number;
  dpi: number;
  bg_color: string;
}

export interface PassportPhotoResult {
  result_image_b64: string;
  format: 'jpeg';
  country_code: string;
  country_name: string;
  spec_applied: PassportPhotoSpec;
  face_detected: boolean;
  quality_warnings: string[];
  print_guide: string;
}

export function PassportPhotoResultPanel({
  result,
  jobId,
}: {
  result: PassportPhotoResult;
  jobId: string;
}) {
  const dataUrl = `data:image/jpeg;base64,${result.result_image_b64}`;
  const spec = result.spec_applied;

  const downloadPhoto = () => {
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = `passport-photo-${result.country_code}.jpg`;
    a.click();
  };

  return (
    <div className="space-y-4">
      {/* Country badge */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl" role="img" aria-label={result.country_name}>
            {/* flag emoji is in country name, show country_name */}
          </span>
          <div>
            <h3 className="text-base font-semibold text-white">{result.country_name}</h3>
            <p className="text-xs text-gray-400">
              {spec.width_mm}×{spec.height_mm}mm @ {spec.dpi}DPI
            </p>
          </div>
        </div>
        <span className="rounded-full bg-green-500/10 px-2 py-0.5 text-xs text-green-400">
          {result.face_detected ? '✓ Face detected' : '⚠ No face'}
        </span>
      </div>

      {/* Photo preview with spec overlay */}
      <div className="relative inline-block">
        <img
          src={dataUrl}
          alt={`${result.country_name} passport photo`}
          className="max-h-72 w-auto rounded-lg border border-gray-700/50 object-contain"
          style={{ background: spec.bg_color }}
        />
        <div className="absolute bottom-1 right-1 rounded bg-black/60 px-1.5 py-0.5 text-xs text-white">
          {spec.width_mm}×{spec.height_mm}mm · {spec.dpi}DPI
        </div>
      </div>

      {/* Quality warnings */}
      {result.quality_warnings.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-yellow-400">⚠ Quality Warnings</p>
          {result.quality_warnings.map((warning, i) => (
            <div
              key={i}
              className="flex items-start gap-2 rounded-lg border border-yellow-800/40 bg-yellow-900/10 px-3 py-2 text-xs text-yellow-300"
            >
              <span className="mt-0.5 shrink-0">⚠</span>
              <span>{warning}</span>
            </div>
          ))}
        </div>
      )}

      {/* Spec breakdown grid */}
      <div className="grid grid-cols-3 gap-2">
        {[
          { label: 'Width', value: `${spec.width_mm}mm` },
          { label: 'Height', value: `${spec.height_mm}mm` },
          { label: 'DPI', value: String(spec.dpi) },
          { label: 'Pixels', value: `${spec.width_px}×${spec.height_px}` },
          { label: 'Country', value: result.country_code.toUpperCase() },
          {
            label: 'Background',
            value: (
              <span className="flex items-center gap-1">
                <span
                  className="inline-block h-3 w-3 rounded-full border border-gray-600"
                  style={{ backgroundColor: spec.bg_color }}
                />
                {spec.bg_color}
              </span>
            ),
          },
        ].map((item, i) => (
          <div key={i} className="rounded-lg bg-gray-800/50 p-2 text-center">
            <p className="text-xs text-gray-500">{item.label}</p>
            <p className="mt-0.5 text-xs font-medium text-gray-200">{item.value}</p>
          </div>
        ))}
      </div>

      {/* Print guide */}
      <div className="rounded-lg border border-gray-700/40 bg-gray-800/30 px-3 py-2 text-xs text-gray-400">
        🖨 {result.print_guide}
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={downloadPhoto}
          className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500"
        >
          <Download size={12} />
          Download JPEG
        </button>
        <DownloadButton jobId={jobId} slug="passport-photo" format="json" label="JSON" />
      </div>
    </div>
  );
}
