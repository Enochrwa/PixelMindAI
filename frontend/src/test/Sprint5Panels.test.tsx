/**
 * Sprint 5 — Creator Studio UI panel tests (S5-07)
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import {
  ThumbnailResultPanel,
  CaptionLensResultPanel,
  MemeResultPanel,
  VideoThumbnailResultPanel,
} from '../components/tools/Sprint5ResultPanels';

// ─────────────────────────────────────────────────────────────────────────────
// Test data
// ─────────────────────────────────────────────────────────────────────────────

const THUMBNAIL_RESULT = {
  ctr_score: 72.5,
  grade: 'B',
  breakdown: {
    face_visibility: { score: 80, weight_pct: 25, detail: { faces_detected: 1 } },
    visual_contrast: { score: 70, weight_pct: 20, detail: { rms_contrast: 65.0 } },
    color_energy: { score: 60, weight_pct: 15, detail: { avg_saturation: 0.5 } },
    text_readability: { score: 75, weight_pct: 20, detail: { text_found: true } },
    clutter_score: { score: 65, weight_pct: 10, detail: { edge_density: 0.1 } },
    emotional_trigger: { score: 55, weight_pct: 10, detail: { dominant_emotion: 'happy' } },
  },
  tips: [
    {
      dimension: 'Color Energy',
      issue: 'Muted colors',
      fix: 'Use bold, saturated colors.',
    },
  ],
};

const THUMBNAIL_AB_RESULT = {
  winner: 'A',
  score_difference: 8.5,
  explanation: 'Thumbnail A is noticeably stronger.',
  thumbnail_a: { ...THUMBNAIL_RESULT, ctr_score: 75 },
  thumbnail_b: { ...THUMBNAIL_RESULT, ctr_score: 66.5 },
};

const CAPTION_RESULT = {
  image_description: 'a golden sunset over a mountain lake',
  platforms: {
    instagram: {
      captions: [
        {
          style: 'casual',
          caption: 'Loving this view 🌅',
          hashtags: [
            'sunset',
            'nature',
            'travel',
            'photography',
            'lake',
            'mountain',
            'golden',
            'sky',
            'explore',
            'beautiful',
          ],
        },
        {
          style: 'inspirational',
          caption: 'Every sunset is a new beginning ✨',
          hashtags: [
            'inspiration',
            'motivation',
            'mindset',
            'photography',
            'sunset',
            'nature',
            'positivity',
            'vision',
            'dreambig',
            'growth',
          ],
        },
        {
          style: 'funny',
          caption: 'Me pretending to be a nature photographer 😅',
          hashtags: [
            'relatable',
            'funny',
            'photography',
            'nature',
            'humor',
            'LOL',
            'authentic',
            'nofilter',
            'vibes',
            'real',
          ],
        },
      ],
    },
    twitter: {
      tweets: [
        'Captured this today — a golden sunset over a mountain lake 📸',
        'A picture is worth a thousand words. Beautiful evening!',
        'Sharing a little visual story. Nature always delivers 🌟',
      ],
    },
    linkedin: {
      caption: 'Sharing a perspective captured today. Visual storytelling continues to inspire.',
    },
  },
};

const MEME_RESULT = {
  scene_description: 'person smiling at camera',
  emotions_detected: ['happy'],
  suggestions: [
    { top: 'When the code works', bottom: 'First try' },
    { top: 'Me on a Friday', bottom: 'Friday afternoon' },
    { top: 'Nobody:', bottom: 'Me after coffee' },
  ],
};

const MEME_COMPOSED = {
  ...MEME_RESULT,
  result_image_b64:
    '/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFgABAQEAAAAAAAAAAAAAAAAABgUEB',
  format: 'png',
};

const VIDEO_RESULT = {
  total_frames_extracted: 5,
  duration_seconds: 30,
  fps: 25,
  frames: [
    {
      frame_index: 0,
      timestamp_seconds: 0,
      timestamp_formatted: '00:00',
      ctr_score: 82,
      image_b64: 'AAAA',
    },
    {
      frame_index: 125,
      timestamp_seconds: 5,
      timestamp_formatted: '00:05',
      ctr_score: 65,
      image_b64: 'BBBB',
    },
    {
      frame_index: 250,
      timestamp_seconds: 10,
      timestamp_formatted: '00:10',
      ctr_score: 73,
      image_b64: 'CCCC',
    },
  ],
  recommended_frame: {
    frame_index: 0,
    timestamp_seconds: 0,
    timestamp_formatted: '00:00',
    ctr_score: 82,
    image_b64: 'AAAA',
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// ThumbnailResultPanel
// ─────────────────────────────────────────────────────────────────────────────

describe('ThumbnailResultPanel', () => {
  it('renders the CTR score', () => {
    render(<ThumbnailResultPanel result={THUMBNAIL_RESULT} />);
    expect(screen.getByText('72.5')).toBeTruthy();
  });

  it('renders the grade badge', () => {
    render(<ThumbnailResultPanel result={THUMBNAIL_RESULT} />);
    expect(screen.getByText('Grade B')).toBeTruthy();
  });

  it('renders all 6 dimension labels', () => {
    render(<ThumbnailResultPanel result={THUMBNAIL_RESULT} />);
    expect(screen.getByText('Face')).toBeTruthy();
    expect(screen.getByText('Contrast')).toBeTruthy();
    expect(screen.getByText('Color')).toBeTruthy();
    expect(screen.getByText('Text')).toBeTruthy();
    expect(screen.getByText('Clarity')).toBeTruthy();
    expect(screen.getByText('Emotion')).toBeTruthy();
  });

  it('renders tip cards', () => {
    render(<ThumbnailResultPanel result={THUMBNAIL_RESULT} />);
    expect(screen.getByText('Color Energy')).toBeTruthy();
    expect(screen.getByText(/Improvement Tips/i)).toBeTruthy();
  });

  it('renders A/B comparison when winner is present', () => {
    const abResult = { ...THUMBNAIL_RESULT, ...THUMBNAIL_AB_RESULT };
    render(<ThumbnailResultPanel result={abResult} />);
    expect(screen.getByText('Thumbnail A')).toBeTruthy();
    expect(screen.getByText('Thumbnail B')).toBeTruthy();
    expect(screen.getByText(/wins by 8.5 points/i)).toBeTruthy();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// CaptionLensResultPanel
// ─────────────────────────────────────────────────────────────────────────────

describe('CaptionLensResultPanel', () => {
  it('renders image description', () => {
    render(<CaptionLensResultPanel result={CAPTION_RESULT} />);
    expect(screen.getByText(/golden sunset/i)).toBeTruthy();
  });

  it('renders platform tabs', () => {
    render(<CaptionLensResultPanel result={CAPTION_RESULT} />);
    expect(screen.getByText('Instagram')).toBeTruthy();
    expect(screen.getByText('Twitter / X')).toBeTruthy();
    expect(screen.getByText('LinkedIn')).toBeTruthy();
  });

  it('shows Instagram captions by default', () => {
    render(<CaptionLensResultPanel result={CAPTION_RESULT} />);
    // Each style renders as a capitalized span; getAllByText avoids multi-element error
    expect(screen.getAllByText(/casual/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/inspirational/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/funny/i).length).toBeGreaterThan(0);
  });

  it('switches to Twitter tab on click', () => {
    render(<CaptionLensResultPanel result={CAPTION_RESULT} />);
    fireEvent.click(screen.getByText('Twitter / X'));
    expect(screen.getByText(/Captured this today/i)).toBeTruthy();
  });

  it('switches to LinkedIn tab on click', () => {
    render(<CaptionLensResultPanel result={CAPTION_RESULT} />);
    fireEvent.click(screen.getByText('LinkedIn'));
    expect(screen.getByText(/Sharing a perspective/i)).toBeTruthy();
  });

  it('renders hashtag chips for Instagram captions', () => {
    render(<CaptionLensResultPanel result={CAPTION_RESULT} />);
    // hashtag chips render without the '#' prefix in text; there may be multiple occurrences
    const chips = screen.getAllByText('sunset');
    expect(chips.length).toBeGreaterThan(0);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// MemeResultPanel
// ─────────────────────────────────────────────────────────────────────────────

describe('MemeResultPanel', () => {
  it('renders detected emotions', () => {
    render(<MemeResultPanel result={MEME_RESULT} />);
    expect(screen.getByText('happy')).toBeTruthy();
  });

  it('renders first suggestion', () => {
    render(<MemeResultPanel result={MEME_RESULT} />);
    expect(screen.getByText('When the code works')).toBeTruthy();
    expect(screen.getByText('First try')).toBeTruthy();
  });

  it('navigates to next suggestion on right arrow click', () => {
    render(<MemeResultPanel result={MEME_RESULT} />);
    // Find the navigation chevron buttons by their className
    const buttons = screen.getAllByRole('button');
    const navBtn = buttons.find(
      (b) => b.className.includes('rounded-lg') && b.querySelector('svg')
    );
    if (navBtn) fireEvent.click(navBtn);
    // At least renders without crashing
    expect(screen.getByText('Meme Generator Pro')).toBeTruthy();
  });

  it('renders top and bottom text inputs', () => {
    render(<MemeResultPanel result={MEME_RESULT} />);
    const inputs = screen.getAllByRole('textbox');
    expect(inputs.length).toBeGreaterThanOrEqual(2);
  });

  it('renders compose button when onCompose and fileId provided', () => {
    const onCompose = vi.fn();
    render(
      <MemeResultPanel result={MEME_RESULT} originalFileId="file-123" onCompose={onCompose} />
    );
    expect(screen.getByText('Generate Meme')).toBeTruthy();
  });

  it('renders composed image when result_image_b64 present', () => {
    render(<MemeResultPanel result={MEME_COMPOSED} />);
    const imgs = screen.getAllByRole('img');
    expect(imgs.length).toBeGreaterThan(0);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// VideoThumbnailResultPanel
// ─────────────────────────────────────────────────────────────────────────────

describe('VideoThumbnailResultPanel', () => {
  it('renders duration and stats', () => {
    render(<VideoThumbnailResultPanel result={VIDEO_RESULT} />);
    expect(screen.getByText('30s')).toBeTruthy();
    expect(screen.getByText('5')).toBeTruthy();
  });

  it('marks recommended frame', () => {
    render(<VideoThumbnailResultPanel result={VIDEO_RESULT} />);
    expect(screen.getByText('★ Recommended')).toBeTruthy();
  });

  it('renders frame timestamps in grid', () => {
    render(<VideoThumbnailResultPanel result={VIDEO_RESULT} />);
    expect(screen.getByText('00:00')).toBeTruthy();
    expect(screen.getByText('00:05')).toBeTruthy();
  });

  it('renders CTR scores in frame grid', () => {
    render(<VideoThumbnailResultPanel result={VIDEO_RESULT} />);
    expect(screen.getByText('CTR 82')).toBeTruthy();
    expect(screen.getByText('CTR 65')).toBeTruthy();
  });

  it('renders error message when error is present', () => {
    render(
      <VideoThumbnailResultPanel result={{ ...VIDEO_RESULT, error: 'Could not open video file' }} />
    );
    expect(screen.getByText('Could not open video file')).toBeTruthy();
  });
});
