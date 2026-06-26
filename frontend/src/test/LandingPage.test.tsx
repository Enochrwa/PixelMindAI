import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { LandingPage } from '@/pages/LandingPage';

describe('LandingPage', () => {
  it('renders the brand name', () => {
    render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );
    expect(
      screen.getByText((_, element) => element?.textContent === 'PixelMind AI')
    ).toBeInTheDocument();
  });

  it('shows CTA buttons', () => {
    render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );
    expect(screen.getByText('Get Started Free')).toBeInTheDocument();
    expect(screen.getByText('View Pricing')).toBeInTheDocument();
  });
});
