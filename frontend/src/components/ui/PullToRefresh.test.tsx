/**
 * PullToRefresh Component Tests
 *
 * Basic smoke tests to verify the component can be imported and renders.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import PullToRefresh from './PullToRefresh';

// Mock the useSwipeGesture hook
jest.mock('../../hooks/useSwipeGesture', () => ({
  useSwipeGesture: () => ({
    ref: jest.fn(),
  }),
}));

describe('PullToRefresh Component', () => {
  it('should import without errors', () => {
    expect(PullToRefresh).toBeDefined();
  });

  it('should render children correctly', () => {
    const mockRefresh = jest.fn().mockResolvedValue(undefined);

    render(
      <PullToRefresh onRefresh={mockRefresh}>
        <div>Test Content</div>
      </PullToRefresh>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should render with custom props', () => {
    const mockRefresh = jest.fn().mockResolvedValue(undefined);

    render(
      <PullToRefresh
        onRefresh={mockRefresh}
        threshold={100}
        maxPullDistance={150}
        loadingMessage="Loading..."
        pullMessage="Pull to refresh"
        releaseMessage="Release to refresh"
      >
        <div>Test Content</div>
      </PullToRefresh>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should handle refreshing state', () => {
    const mockRefresh = jest.fn().mockResolvedValue(undefined);

    const { rerender } = render(
      <PullToRefresh onRefresh={mockRefresh} refreshing={false}>
        <div>Test Content</div>
      </PullToRefresh>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();

    rerender(
      <PullToRefresh onRefresh={mockRefresh} refreshing={true}>
        <div>Test Content</div>
      </PullToRefresh>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should be disabled when enabled is false', () => {
    const mockRefresh = jest.fn().mockResolvedValue(undefined);

    render(
      <PullToRefresh onRefresh={mockRefresh} enabled={false}>
        <div>Test Content</div>
      </PullToRefresh>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });
});
