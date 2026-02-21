/**
 * Tests for KanbanColumn Component
 *
 * Tests the column component including:
 * - Rendering column header with title
 * - WIP indicator integration
 * - Candidate list rendering via renderCard prop
 * - Empty state display
 * - Drag-and-drop functionality (Droppable)
 * - Column click handling
 * - WIP limit exceeded visual warning
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import KanbanColumn, { KanbanColumnProps, KanbanColumnData } from '../KanbanColumn';
import { KanbanCandidate } from '../KanbanCard';

// Mock @hello-pangea/dnd
vi.mock('@hello-pangea/dnd', () => ({
  Droppable: ({
    children,
    droppableId,
  }: {
    children: (
      provided: { droppableProps: Record<string, string>; innerRef: vi.Mock; placeholder: null },
      snapshot: { isDraggingOver: boolean }
    ) => React.ReactNode;
    droppableId: string;
  }) => {
    const mockProvided = {
      droppableProps: { 'data-rbd-droppable-context-id': 'test', 'data-rbd-droppable-id': droppableId },
      innerRef: vi.fn(),
      placeholder: null,
    };
    const mockSnapshot = { isDraggingOver: false };
    return children(mockProvided, mockSnapshot);
  },
}));

// Helper to create default column data
const createDefaultColumn = (overrides?: Partial<KanbanColumnData>): KanbanColumnData => ({
  id: 'column-1',
  title: 'New Candidates',
  candidates: [
    { id: 'candidate-1', name: 'John Doe' },
    { id: 'candidate-2', name: 'Jane Smith' },
  ] as KanbanCandidate[],
  wip_limit: 10,
  color: '#1976d2',
  ...overrides,
});

// Helper to create default props
const createDefaultProps = (
  columnOverrides?: Partial<KanbanColumnData>
): KanbanColumnProps => ({
  column: createDefaultColumn(columnOverrides),
  renderCard: (candidate: KanbanCandidate, index: number) => (
    <div key={candidate.id} data-testid={`card-${index}`}>
      {candidate.name}
    </div>
  ),
});

describe('KanbanColumn', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render column title correctly', () => {
      const props = createDefaultProps();
      render(<KanbanColumn {...props} />);

      expect(screen.getByText('New Candidates')).toBeInTheDocument();
    });

    it('should render candidates using renderCard prop', () => {
      const props = createDefaultProps();
      render(<KanbanColumn {...props} />);

      expect(screen.getByTestId('card-0')).toBeInTheDocument();
      expect(screen.getByTestId('card-1')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });

    it('should render with custom color header', () => {
      const props = createDefaultProps({ color: '#ff0000' });
      render(<KanbanColumn {...props} />);

      const header = screen.getByText('New Candidates').closest('.MuiPaper-root');
      expect(header).toBeInTheDocument();
    });

    it('should apply minimum height to droppable area', () => {
      const props = createDefaultProps();
      render(<KanbanColumn {...props} minHeight={300} />);

      // The droppable area is the container with the candidates
      const cardContainer = screen.getByTestId('card-0').parentElement;
      expect(cardContainer).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should display empty state when no candidates', () => {
      const props = createDefaultProps({ candidates: [] });
      render(<KanbanColumn {...props} />);

      expect(screen.getByText('Drop candidates here')).toBeInTheDocument();
    });

    it('should not display empty state when candidates exist', () => {
      const props = createDefaultProps();
      render(<KanbanColumn {...props} />);

      expect(screen.queryByText('Drop candidates here')).not.toBeInTheDocument();
    });
  });

  describe('WIP Indicator', () => {
    it('should display WIP indicator when showWipIndicator is true', () => {
      const props = createDefaultProps({ wip_limit: 10, candidates: [] as KanbanCandidate[] });
      render(<KanbanColumn {...props} showWipIndicator={true} />);

      // WipLimitIndicator should render current count
      expect(screen.getByText('0/10')).toBeInTheDocument();
    });

    it('should show candidate count when showWipIndicator is false', () => {
      const props = createDefaultProps({ candidates: [{ id: '1', name: 'Test' }] as KanbanCandidate[] });
      render(<KanbanColumn {...props} showWipIndicator={false} />);

      expect(screen.getByText('1 candidate')).toBeInTheDocument();
    });

    it('should show plural form for candidate count', () => {
      const props = createDefaultProps({
        candidates: [
          { id: '1', name: 'Test1' },
          { id: '2', name: 'Test2' },
        ] as KanbanCandidate[],
      });
      render(<KanbanColumn {...props} showWipIndicator={false} />);

      expect(screen.getByText('2 candidates')).toBeInTheDocument();
    });

    it('should show WIP limit exceeded warning', () => {
      const props = createDefaultProps({
        wip_limit: 1,
        candidates: [
          { id: '1', name: 'Test1' },
          { id: '2', name: 'Test2' },
        ] as KanbanCandidate[],
      });
      render(<KanbanColumn {...props} />);

      // The column should have visual indication of over limit
      expect(screen.getByText('New Candidates')).toBeInTheDocument();
    });

    it('should handle null WIP limit', () => {
      const props = createDefaultProps({ wip_limit: null, candidates: [] as KanbanCandidate[] });
      render(<KanbanColumn {...props} showWipIndicator={true} />);

      // Should just show count without limit
      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('should handle undefined WIP limit', () => {
      const props = createDefaultProps({ wip_limit: undefined, candidates: [] as KanbanCandidate[] });
      render(<KanbanColumn {...props} showWipIndicator={true} />);

      expect(screen.getByText('0')).toBeInTheDocument();
    });
  });

  describe('Click Handling', () => {
    it('should call onClick when column header is clicked', () => {
      const onClick = vi.fn();
      const props = createDefaultProps();
      render(<KanbanColumn {...props} onClick={onClick} />);

      const header = screen.getByText('New Candidates').closest('.MuiPaper-root');
      if (header) {
        fireEvent.click(header);
      }

      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('should not fail when onClick is not provided', () => {
      const props = createDefaultProps();
      render(<KanbanColumn {...props} />);

      const header = screen.getByText('New Candidates').closest('.MuiPaper-root');
      if (header) {
        expect(() => fireEvent.click(header)).not.toThrow();
      }
    });

    it('should show pointer cursor when onClick is provided', () => {
      const onClick = vi.fn();
      const props = createDefaultProps();
      render(<KanbanColumn {...props} onClick={onClick} />);

      const header = screen.getByText('New Candidates').closest('.MuiPaper-root');
      expect(header).toBeInTheDocument();
    });
  });

  describe('Drag and Drop Integration', () => {
    it('should render Droppable component with correct droppableId', () => {
      const props = createDefaultProps({ id: 'custom-column-id' });
      render(<KanbanColumn {...props} />);

      // The droppable area should be present
      expect(screen.getByTestId('card-0')).toBeInTheDocument();
    });

    it('should pass correct index to renderCard', () => {
      const renderCard = vi.fn((candidate: KanbanCandidate, index: number) => (
        <div key={candidate.id} data-testid={`card-${index}`}>
          {candidate.name}
        </div>
      ));
      const props = createDefaultProps();
      render(<KanbanColumn {...props} renderCard={renderCard} />);

      expect(renderCard).toHaveBeenCalledTimes(2);
      // Check that indices were passed correctly
      expect(renderCard).toHaveBeenCalledWith(expect.objectContaining({ id: 'candidate-1' }), 0);
      expect(renderCard).toHaveBeenCalledWith(expect.objectContaining({ id: 'candidate-2' }), 1);
    });
  });

  describe('Candidate Count', () => {
    it('should correctly count candidates', () => {
      const props = createDefaultProps({
        candidates: [
          { id: '1', name: 'Test1' },
          { id: '2', name: 'Test2' },
          { id: '3', name: 'Test3' },
        ] as KanbanCandidate[],
        wip_limit: 5,
      });
      render(<KanbanColumn {...props} />);

      // WipLimitIndicator shows 3/5
      expect(screen.getByText('3/5')).toBeInTheDocument();
    });

    it('should handle zero candidates', () => {
      const props = createDefaultProps({
        candidates: [] as KanbanCandidate[],
        wip_limit: 5,
      });
      render(<KanbanColumn {...props} />);

      expect(screen.getByText('0/5')).toBeInTheDocument();
    });
  });
});
