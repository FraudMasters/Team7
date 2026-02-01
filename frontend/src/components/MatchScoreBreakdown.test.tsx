/**
 * Tests for MatchScoreBreakdown Component
 *
 * Tests the match score breakdown visualization including:
 * - Displaying individual algorithm scores (Keyword, TF-IDF, Vector)
 * - Showing weighted contribution calculations
 * - Overall score display with formula breakdown
 * - Color-coded progress bars based on score values
 * - Responsive layout for different screen sizes
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MatchScoreBreakdown from './MatchScoreBreakdown';

describe('MatchScoreBreakdown', () => {
  describe('Component Rendering', () => {
    it('should render the component with header', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.7}
          vectorScore={0.6}
        />
      );

      expect(screen.getByText('Score Breakdown')).toBeInTheDocument();
      expect(
        screen.getByText('Detailed view of how each algorithm contributes to the overall match score')
      ).toBeInTheDocument();
    });

    it('should display overall match score', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.7}
          vectorScore={0.6}
        />
      );

      expect(screen.getByText('Overall Match Score')).toBeInTheDocument();
      // Overall = (0.8 * 0.5) + (0.7 * 0.3) + (0.6 * 0.2) = 0.4 + 0.21 + 0.12 = 0.73 = 73%
      expect(screen.getByText('73%')).toBeInTheDocument();
    });

    it('should use provided overall score when available', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.7}
          vectorScore={0.6}
          overallScore={0.85}
        />
      );

      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.queryByText('73%')).not.toBeInTheDocument();
    });

    it('should display weighted formula breakdown', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.7}
          vectorScore={0.6}
        />
      );

      // Check for formula components
      expect(screen.getByText('Weighted Formula')).toBeInTheDocument();
      expect(screen.getByText('40% + 21% + 12% = 73%')).toBeInTheDocument();
    });
  });

  describe('Algorithm Score Displays', () => {
    it('should display keyword matching score with correct weight', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.85}
          tfidfScore={0.7}
          vectorScore={0.6}
        />
      );

      expect(screen.getByText('Keyword Matching')).toBeInTheDocument();
      expect(screen.getByText('50% weight')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('+43%')).toBeInTheDocument(); // 0.85 * 0.5 = 0.425
    });

    it('should display TF-IDF weighting score with correct weight', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.75}
          vectorScore={0.6}
        />
      );

      expect(screen.getByText('TF-IDF Weighting')).toBeInTheDocument();
      expect(screen.getByText('30% weight')).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
      expect(screen.getByText('+23%')).toBeInTheDocument(); // 0.75 * 0.3 = 0.225
    });

    it('should display vector similarity score with correct weight', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.7}
          vectorScore={0.65}
        />
      );

      expect(screen.getByText('Vector Similarity')).toBeInTheDocument();
      expect(screen.getByText('20% weight')).toBeInTheDocument();
      expect(screen.getByText('65%')).toBeInTheDocument();
      expect(screen.getByText('+13%')).toBeInTheDocument(); // 0.65 * 0.2 = 0.13
    });

    it('should display algorithm weight percentages', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.7}
          vectorScore={0.6}
        />
      );

      expect(screen.getByText('50%')).toBeInTheDocument(); // Keyword
      expect(screen.getByText('30%')).toBeInTheDocument(); // TF-IDF
      expect(screen.getByText('20%')).toBeInTheDocument(); // Vector
    });
  });

  describe('Score Visualization', () => {
    it('should display progress bars for each algorithm', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.7}
          vectorScore={0.6}
        />
      );

      const progressBars = document.querySelectorAll('.MuiLinearProgress-root');
      expect(progressBars.length).toBeGreaterThanOrEqual(3); // At least 3 progress bars
    });

    it('should display raw score labels', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.7}
          vectorScore={0.6}
        />
      );

      expect(screen.getAllByText('Raw Score').length).toBeGreaterThanOrEqual(3);
    });

    it('should display contribution labels', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.7}
          vectorScore={0.6}
        />
      );

      expect(screen.getAllByText('Contribution to overall').length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('Formula Explanation', () => {
    it('should display formula explanation at bottom', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.7}
          vectorScore={0.6}
        />
      );

      expect(screen.getByText(/Formula:/)).toBeInTheDocument();
      expect(
        screen.getByText(/Overall = \(Keyword × 0\.5\) \+ \(TF-IDF × 0\.3\) \+ \(Vector × 0\.2\)/)
      ).toBeInTheDocument();
      expect(screen.getByText(/Weights:/)).toBeInTheDocument();
      expect(screen.getByText(/Keyword 50%, TF-IDF 30%, Vector 20%/)).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero scores', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0}
          tfidfScore={0}
          vectorScore={0}
        />
      );

      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('should handle perfect scores', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={1}
          tfidfScore={1}
          vectorScore={1}
        />
      );

      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('should handle decimal scores correctly', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.856}
          tfidfScore={0.723}
          vectorScore={0.689}
        />
      );

      // Should round to nearest percent
      expect(screen.getByText('86%')).toBeInTheDocument();
      expect(screen.getByText('72%')).toBeInTheDocument();
      expect(screen.getByText('69%')).toBeInTheDocument();
    });

    it('should handle very low scores', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.1}
          tfidfScore={0.2}
          vectorScore={0.15}
        />
      );

      expect(screen.getByText('10%')).toBeInTheDocument();
      expect(screen.getByText('20%')).toBeInTheDocument();
      expect(screen.getByText('15%')).toBeInTheDocument();
    });
  });

  describe('Score Calculations', () => {
    it('should calculate overall score correctly with equal mid-range scores', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.5}
          tfidfScore={0.5}
          vectorScore={0.5}
        />
      );

      // Overall = 0.5*0.5 + 0.5*0.3 + 0.5*0.2 = 0.25 + 0.15 + 0.10 = 0.50 = 50%
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('should calculate weighted contributions correctly', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={1.0}
          tfidfScore={0.5}
          vectorScore={0.0}
        />
      );

      // Keyword: 1.0 * 0.5 = 0.5 = 50%
      // TF-IDF: 0.5 * 0.3 = 0.15 = 15%
      // Vector: 0.0 * 0.2 = 0.0 = 0%
      // Overall: 50 + 15 + 0 = 65%
      expect(screen.getByText('50%')).toBeInTheDocument(); // Keyword contribution
      expect(screen.getByText('15%')).toBeInTheDocument(); // TF-IDF contribution
      expect(screen.getByText('0%')).toBeInTheDocument(); // Vector contribution
      expect(screen.getByText('65%')).toBeInTheDocument(); // Overall
    });

    it('should prioritize provided overall score over calculated', () => {
      const { rerender } = render(
        <MatchScoreBreakdown
          keywordScore={0.5}
          tfidfScore={0.5}
          vectorScore={0.5}
          overallScore={0.9}
        />
      );

      expect(screen.getByText('90%')).toBeInTheDocument();

      rerender(
        <MatchScoreBreakdown
          keywordScore={0.5}
          tfidfScore={0.5}
          vectorScore={0.5}
          overallScore={0.3}
        />
      );

      expect(screen.getByText('30%')).toBeInTheDocument();
    });
  });

  describe('Layout and Structure', () => {
    it('should render cards for each algorithm breakdown', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.7}
          vectorScore={0.6}
        />
      );

      const cards = document.querySelectorAll('.MuiCard-root');
      expect(cards.length).toBeGreaterThanOrEqual(3);
    });

    it('should display algorithm icons', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.7}
          vectorScore={0.6}
        />
      );

      // Icons are rendered but might not have accessible text
      // Check that component has visual elements
      const iconContainers = document.querySelectorAll('[class*="p: 1"]');
      expect(iconContainers.length).toBeGreaterThan(0);
    });

    it('should display algorithm weight in large text', () => {
      render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.7}
          vectorScore={0.6}
        />
      );

      expect(screen.getByText('Algorithm Weight')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('should render in stack layout', () => {
      const { container } = render(
        <MatchScoreBreakdown
          keywordScore={0.8}
          tfidfScore={0.7}
          vectorScore={0.6}
        />
      );

      // Check for stack layout
      const stacks = container.querySelectorAll('.MuiStack-root');
      expect(stacks.length).toBeGreaterThan(0);
    });
  });
});
