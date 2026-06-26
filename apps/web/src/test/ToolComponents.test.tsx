import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// Mock api module
vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// Mock react-dropzone
vi.mock('react-dropzone', () => ({
  useDropzone: () => ({
    getRootProps: () => ({}),
    getInputProps: () => ({}),
    isDragActive: false,
    fileRejections: [],
  }),
}));

describe('ReceiptResultPanel', () => {
  it('renders merchant name', () => {
    const { ReceiptResultPanel } = await import('@/components/tools/ResultPanels');
    const result = {
      merchant: 'Test Market',
      date: '2024-06-15',
      currency: 'RWF',
      line_items: [{ name: 'Bread', price: 1500 }],
      subtotal: 1500,
      tax: 270,
      total: 1770,
      confidence_score: 85,
    };
    render(
      <MemoryRouter>
        <ReceiptResultPanel result={result} jobId="test-job-123" />
      </MemoryRouter>
    );
    expect(screen.getByText('Test Market')).toBeDefined();
    expect(screen.getByText('85% confidence')).toBeDefined();
  });
});

describe('BusinessCardResultPanel', () => {
  it('renders contact name and email', async () => {
    const { BusinessCardResultPanel } = await import('@/components/tools/ResultPanels');
    const result = {
      full_name: 'Alice Mutoni',
      job_title: 'Software Engineer',
      company: 'EnochLabs',
      emails: ['alice@enochlabs.com'],
      phones: ['+250788123456'],
      websites: [],
      address: null,
      social_handles: {},
      confidence_score: 90,
    };
    render(
      <MemoryRouter>
        <BusinessCardResultPanel result={result} jobId="test-job-456" />
      </MemoryRouter>
    );
    expect(screen.getByText('Alice Mutoni')).toBeDefined();
    expect(screen.getByText('alice@enochlabs.com')).toBeDefined();
  });
});

describe('FileDropzone', () => {
  it('renders drop zone text', async () => {
    const { FileDropzone } = await import('@/components/tools/FileDropzone');
    render(<FileDropzone onFileDrop={vi.fn()} />);
    expect(screen.getByText(/drag & drop/i)).toBeDefined();
  });
});

describe('InvoiceResultPanel', () => {
  it('renders invoice number', async () => {
    const { InvoiceResultPanel } = await import('@/components/tools/ResultPanels');
    const result = {
      invoice_number: 'INV-001',
      supplier_name: 'Supplier Co',
      buyer_name: 'Client Inc',
      date: '2024-06-15',
      due_date: '2024-07-15',
      payment_terms: 'Net 30',
      line_items: [],
      subtotal: 900,
      tax: 162,
      total: 1062,
      confidence_score: 80,
    };
    render(
      <MemoryRouter>
        <InvoiceResultPanel result={result} jobId="test-job-789" />
      </MemoryRouter>
    );
    expect(screen.getByText(/INV-001/)).toBeDefined();
  });
});
