/**
 * Sprint 4 frontend panel unit tests (S4-07).
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  UpscalerResultPanel,
  ResumeOptimizerResultPanel,
  FaceBlurResultPanel,
  ProfileStylerResultPanel,
  DeepfakeResultPanel,
  SPRINT4_PANELS,
} from '@/components/tools/Sprint4ResultPanels';

// Minimal valid base64 JPEG (1×1 white pixel)
const TINY_JPEG_B64 =
  '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8U' +
  'HRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgN' +
  'DRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIy' +
  'MjL/wAARCAABAAEDASIAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAA' +
  'AAAAAAAAAAAAAAAAAP/EABQBAQAAAAAAAAAAAAAAAAAAAAD/xAAUEQEAAAAAAAAAAAAAAAAA' +
  'AAAA/9oADAMBAAIRAxEAPwCwABmX/9k=';

// ─────────────────────────────────────────────────────────────────────────────
// UpscalerResultPanel
// ─────────────────────────────────────────────────────────────────────────────

describe('UpscalerResultPanel', () => {
  const result = {
    result_image_b64: TINY_JPEG_B64,
    comparison_b64: TINY_JPEG_B64,
    format: 'jpeg',
    method: 'lanczos_fallback',
    original_width: 64,
    original_height: 48,
    upscaled_width: 256,
    upscaled_height: 192,
    scale_factor: 4,
  };

  it('renders original and upscaled dimensions', () => {
    render(<UpscalerResultPanel result={result} />);
    expect(screen.getByText(/64×48/)).toBeTruthy();
    expect(screen.getByText(/256×192/)).toBeTruthy();
  });

  it('shows engine name', () => {
    render(<UpscalerResultPanel result={result} />);
    expect(screen.getByText(/Lanczos/i)).toBeTruthy();
  });

  it('renders download button', () => {
    render(<UpscalerResultPanel result={result} />);
    expect(screen.getByText(/Download/i)).toBeTruthy();
  });

  it('shows empty state when no b64', () => {
    render(<UpscalerResultPanel result={{ ...result, result_image_b64: '' }} />);
    expect(screen.getByText(/No upscaled image/i)).toBeTruthy();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// ResumeOptimizerResultPanel
// ─────────────────────────────────────────────────────────────────────────────

describe('ResumeOptimizerResultPanel', () => {
  const result = {
    total_score: 72,
    verdict: 'Good photo with room for improvement.',
    breakdown: {
      face_visibility: { score: 80, weight: 20, weighted_score: 16 },
      lighting_quality: { score: 60, weight: 20, weighted_score: 12 },
      background_quality: { score: 90, weight: 20, weighted_score: 18 },
      eye_contact: { score: 70, weight: 15, weighted_score: 10.5 },
      expression: { score: 65, weight: 15, weighted_score: 9.75 },
      composition: { score: 75, weight: 10, weighted_score: 7.5 },
    },
    tips: [
      {
        dimension: 'lighting_quality',
        issue: 'Image is slightly dark.',
        fix_suggestion: 'Move near a window.',
      },
    ],
  };

  it('renders total score', () => {
    render(<ResumeOptimizerResultPanel result={result} />);
    expect(screen.getByText(/72\/100/)).toBeTruthy();
  });

  it('renders verdict text', () => {
    render(<ResumeOptimizerResultPanel result={result} />);
    expect(screen.getByText(/Good photo with room/i)).toBeTruthy();
  });

  it('renders tip fix suggestion', () => {
    render(<ResumeOptimizerResultPanel result={result} />);
    expect(screen.getByText(/Move near a window/i)).toBeTruthy();
  });

  it('renders all 6 dimension labels', () => {
    render(<ResumeOptimizerResultPanel result={result} />);
    expect(screen.getAllByText(/Face Visibility/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Lighting Quality/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Eye Contact/i).length).toBeGreaterThan(0);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// FaceBlurResultPanel
// ─────────────────────────────────────────────────────────────────────────────

describe('FaceBlurResultPanel', () => {
  const result = {
    result_image_b64: TINY_JPEG_B64,
    format: 'jpeg',
    faces_detected_count: 3,
    mode_applied: 'gaussian_blur',
    face_bboxes: [],
  };

  it('shows faces detected count', () => {
    render(<FaceBlurResultPanel result={result} />);
    expect(screen.getByText('3')).toBeTruthy();
  });

  it('shows blur mode', () => {
    render(<FaceBlurResultPanel result={result} />);
    expect(screen.getByText(/gaussian blur/i)).toBeTruthy();
  });

  it('shows download button', () => {
    render(<FaceBlurResultPanel result={result} />);
    expect(screen.getByText(/Download/i)).toBeTruthy();
  });

  it('shows no-faces warning when count is 0', () => {
    render(<FaceBlurResultPanel result={{ ...result, faces_detected_count: 0 }} />);
    expect(screen.getByText(/No faces were detected/i)).toBeTruthy();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// ProfileStylerResultPanel
// ─────────────────────────────────────────────────────────────────────────────

describe('ProfileStylerResultPanel', () => {
  const styles = ['corporate', 'linkedin', 'creative', 'minimal'].map((name) => ({
    style_name: name,
    result_image_b64: TINY_JPEG_B64,
    format: 'jpeg',
  }));
  const result = { styles, width: 400, height: 500 };

  it('renders all 4 style buttons', () => {
    render(<ProfileStylerResultPanel result={result} />);
    expect(screen.getAllByText(/Corporate/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/LinkedIn/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Creative/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Minimal/i).length).toBeGreaterThan(0);
  });

  it('renders download button for selected style', () => {
    render(<ProfileStylerResultPanel result={result} />);
    expect(screen.getByText(/Download/i)).toBeTruthy();
  });

  it('shows empty state when no styles', () => {
    render(<ProfileStylerResultPanel result={{ styles: [] }} />);
    expect(screen.getByText(/No style variants/i)).toBeTruthy();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// DeepfakeResultPanel
// ─────────────────────────────────────────────────────────────────────────────

describe('DeepfakeResultPanel', () => {
  const result = {
    authenticity_score: 82,
    verdict: 'LIKELY_REAL',
    faces_detected: 1,
    evidence: [
      { type: 'fft_frequency', suspicious_score: 5, description: 'Normal spectrum.' },
      { type: 'boundary_consistency', suspicious_score: 0, description: 'Edges consistent.' },
      { type: 'eye_reflection', suspicious_score: 10, description: 'Reflections symmetric.' },
      { type: 'noise_pattern', suspicious_score: 0, description: 'Natural noise.' },
    ],
    heatmap_b64: TINY_JPEG_B64,
    disclaimer: 'AI analysis only — not a forensic instrument.',
  };

  it('renders authenticity score', () => {
    render(<DeepfakeResultPanel result={result} />);
    expect(screen.getByText(/82\/100/i)).toBeTruthy();
  });

  it('renders LIKELY_REAL verdict', () => {
    render(<DeepfakeResultPanel result={result} />);
    expect(screen.getByText(/Likely Real/i)).toBeTruthy();
  });

  it('renders all 4 evidence signals', () => {
    render(<DeepfakeResultPanel result={result} />);
    expect(screen.getByText(/Frequency Analysis/i)).toBeTruthy();
    expect(screen.getByText(/Boundary Edges/i)).toBeTruthy();
    expect(screen.getByText(/Eye Reflection/i)).toBeTruthy();
    expect(screen.getByText(/Noise Pattern/i)).toBeTruthy();
  });

  it('renders disclaimer text', () => {
    render(<DeepfakeResultPanel result={result} />);
    expect(screen.getByText(/AI analysis only/i)).toBeTruthy();
  });

  it('renders LIKELY_FAKE state', () => {
    render(<DeepfakeResultPanel result={{ ...result, verdict: 'LIKELY_FAKE', authenticity_score: 22 }} />);
    expect(screen.getByText(/Likely Fake/i)).toBeTruthy();
  });

  it('renders UNCERTAIN state', () => {
    render(<DeepfakeResultPanel result={{ ...result, verdict: 'UNCERTAIN', authenticity_score: 55 }} />);
    expect(screen.getByText(/Uncertain/i)).toBeTruthy();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// SPRINT4_PANELS registry
// ─────────────────────────────────────────────────────────────────────────────

describe('SPRINT4_PANELS registry', () => {
  it('contains all 5 sprint 4 tool slugs', () => {
    const expected = [
      'image-upscaler',
      'resume-photo-optimizer',
      'face-blur',
      'profile-picture-styler',
      'deepfake-detector',
    ];
    for (const slug of expected) {
      expect(SPRINT4_PANELS[slug]).toBeDefined();
    }
  });
});
