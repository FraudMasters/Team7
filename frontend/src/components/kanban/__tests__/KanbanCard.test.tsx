/**
 * Tests for KanbanCard Component
 *
 * Tests the candidate card component including:
 * - Rendering candidate information (name, email, vacancy)
 * - Match score display with color coding
 * - Tags display with visibility limits
 * - Activity information display
 * - Click handling
 * - Drag-and-drop visual states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import KanbanCard, { KanbanCandidate, KanbanCardProps } from '../KanbanCard';

// Mock @hello-pangea/dnd
const mockProvided = {
  innerRef: vi.fn(),
  draggableProps: {
    'data-rbd-draggable-context-id': 'test-context',
    'data-rbd-draggable-id': 'test-id',
  },
  dragHandleProps: {
    'data-rbd-drag-handle-draggable-id': 'test-id',
    'data-rbd-drag-handle-context-id': 'test-context',
    role: 'button',
    tabIndex: 0,
  },
};

const mockSnapshot = {
  isDragging: false,
  isDropAnimating: false,
  isCombineEnabled: false,
  combineWith: null,
  draggingOver: null,
  mode: null,
};

// Helper to create default props
const createDefaultProps = (
  candidateOverrides?: Partial<KanbanCandidate>
): KanbanCardProps => ({
  candidate: {
    id: 'candidate-1',
    name: 'John Doe',
    email: 'john.doe@example.com',
    match_score: 75,
    tags: [
      { id: 'tag-1', tag_name: 'React', color: '#61DAFB' },
      { id: 'tag-2', tag_name: 'TypeScript', color: '#3178C6' },
    ],
    vacancy_title: 'Senior Frontend Developer',
    latest_activity: {
      created_at: '2024-01-15T10:30:00Z',
      activity_type: 'status_change',
    },
    notes_count: 3,
    ...candidateOverrides,
  },
  provided: mockProvided as unknown as typeof mockProvided & { innerRef(element: HTMLElement): void },
  snapshot: mockSnapshot,
});

describe('KanbanCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render candidate name correctly', () => {
      const props = createDefaultProps();
      render(<KanbanCard {...props} />);

      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    it('should render filename when name is not available', () => {
      const props = createDefaultProps({
        name: undefined,
        filename: 'resume_john_doe.pdf',
      });
      render(<KanbanCard {...props} />);

      expect(screen.getByText('resume_john_doe.pdf')).toBeInTheDocument();
    });

    it('should render "Unknown Candidate" when neither name nor filename is available', () => {
      const props = createDefaultProps({
        name: undefined,
        filename: undefined,
      });
      render(<KanbanCard {...props} />);

      expect(screen.getByText('Unknown Candidate')).toBeInTheDocument();
    });

    it('should render email when available', () => {
      const props = createDefaultProps();
      render(<KanbanCard {...props} />);

      expect(screen.getByText('john.doe@example.com')).toBeInTheDocument();
    });

    it('should not render email when not available', () => {
      const props = createDefaultProps({ email: undefined });
      render(<KanbanCard {...props} />);

      expect(screen.queryByText('john.doe@example.com')).not.toBeInTheDocument();
    });

    it('should render vacancy title when available', () => {
      const props = createDefaultProps();
      render(<KanbanCard {...props} />);

      expect(screen.getByText('Senior Frontend Developer')).toBeInTheDocument();
    });

    it('should not render vacancy title when not available', () => {
      const props = createDefaultProps({ vacancy_title: undefined });
      render(<KanbanCard {...props} />);

      expect(screen.queryByText('Senior Frontend Developer')).not.toBeInTheDocument();
    });
  });

  describe('Match Score Display', () => {
    it('should render match score with correct value', () => {
      const props = createDefaultProps({ match_score: 85 });
      render(<KanbanCard {...props} />);

      expect(screen.getByText('85%')).toBeInTheDocument();
    });

    it('should round match score correctly', () => {
      const props = createDefaultProps({ match_score: 85.6 });
      render(<KanbanCard {...props} />);

      expect(screen.getByText('86%')).toBeInTheDocument();
    });

    it('should not render match score when undefined', () => {
      const props = createDefaultProps({ match_score: undefined });
      render(<KanbanCard {...props} />);

      // Check that no percentage element exists
      expect(screen.queryByText(/%\s*$/)).not.toBeInTheDocument();
    });

    it('should hide match score when showMatchScore is false', () => {
      const props = createDefaultProps({ match_score: 75 });
      render(<KanbanCard {...props} showMatchScore={false} />);

      expect(screen.queryByText('75%')).not.toBeInTheDocument();
    });

    it('should display success color for high match score (>=70)', () => {
      const props = createDefaultProps({ match_score: 85 });
      render(<KanbanCard {...props} />);

      const chip = screen.getByText('85%').closest('.MuiChip-root');
      expect(chip).toHaveClass('MuiChip-colorSuccess');
    });

    it('should display warning color for medium match score (40-69)', () => {
      const props = createDefaultProps({ match_score: 55 });
      render(<KanbanCard {...props} />);

      const chip = screen.getByText('55%').closest('.MuiChip-root');
      expect(chip).toHaveClass('MuiChip-colorWarning');
    });

    it('should display error color for low match score (<40)', () => {
      const props = createDefaultProps({ match_score: 25 });
      render(<KanbanCard {...props} />);

      const chip = screen.getByText('25%').closest('.MuiChip-root');
      expect(chip).toHaveClass('MuiChip-colorError');
    });
  });

  describe('Tags Display', () => {
    it('should render tags when available', () => {
      const props = createDefaultProps();
      render(<KanbanCard {...props} />);

      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('TypeScript')).toBeInTheDocument();
    });

    it('should hide tags when showTags is false', () => {
      const props = createDefaultProps();
      render(<KanbanCard {...props} showTags={false} />);

      expect(screen.queryByText('React')).not.toBeInTheDocument();
      expect(screen.queryByText('TypeScript')).not.toBeInTheDocument();
    });

    it('should limit visible tags based on maxTagsVisible', () => {
      const props = createDefaultProps({
        tags: [
          { id: 'tag-1', tag_name: 'React' },
          { id: 'tag-2', tag_name: 'TypeScript' },
          { id: 'tag-3', tag_name: 'Node.js' },
          { id: 'tag-4', tag_name: 'GraphQL' },
          { id: 'tag-5', tag_name: 'MongoDB' },
        ],
      });
      render(<KanbanCard {...props} maxTagsVisible={3} />);

      // Should show first 3 tags
      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('TypeScript')).toBeInTheDocument();
      expect(screen.getByText('Node.js')).toBeInTheDocument();

      // Should show counter for hidden tags
      expect(screen.getByText('+2')).toBeInTheDocument();
    });

    it('should not show hidden tags counter when all tags are visible', () => {
      const props = createDefaultProps({
        tags: [
          { id: 'tag-1', tag_name: 'React' },
          { id: 'tag-2', tag_name: 'TypeScript' },
        ],
      });
      render(<KanbanCard {...props} maxTagsVisible={3} />);

      expect(screen.queryByText(/+\d/)).not.toBeInTheDocument();
    });

    it('should render tags with custom colors', () => {
      const props = createDefaultProps({
        tags: [{ id: 'tag-1', tag_name: 'React', color: '#61DAFB' }],
      });
      render(<KanbanCard {...props} />);

      const tag = screen.getByText('React').closest('.MuiChip-root');
      expect(tag).toBeInTheDocument();
    });

    it('should not render tags section when tags array is empty', () => {
      const props = createDefaultProps({ tags: [] });
      render(<KanbanCard {...props} />);

      expect(screen.queryByText('React')).not.toBeInTheDocument();
    });

    it('should not render tags section when tags is undefined', () => {
      const props = createDefaultProps({ tags: undefined });
      render(<KanbanCard {...props} />);

      expect(screen.queryByText('React')).not.toBeInTheDocument();
    });
  });

  describe('Activity Display', () => {
    it('should show activity when showActivity is true', () => {
      const props = createDefaultProps();
      render(<KanbanCard {...props} />);

      // Should show notes count
      expect(screen.getByText(/3\s*note/)).toBeInTheDocument();
    });

    it('should hide activity when showActivity is false', () => {
      const props = createDefaultProps();
      render(<KanbanCard {...props} showActivity={false} />);

      expect(screen.queryByText(/3\s*note/)).not.toBeInTheDocument();
    });

    it('should display notes count with correct pluralization', () => {
      const props = createDefaultProps({ notes_count: 1 });
      render(<KanbanCard {...props} />);

      expect(screen.getByText('1 note')).toBeInTheDocument();
    });

    it('should display notes count with plural form', () => {
      const props = createDefaultProps({ notes_count: 5 });
      render(<KanbanCard {...props} />);

      expect(screen.getByText('5 notes')).toBeInTheDocument();
    });

    it('should not display notes when count is 0', () => {
      const props = createDefaultProps({ notes_count: 0 });
      render(<KanbanCard {...props} />);

      expect(screen.queryByText(/0\s*note/)).not.toBeInTheDocument();
    });
  });

  describe('Click Handling', () => {
    it('should call onClick when card is clicked', () => {
      const onClick = vi.fn();
      const props = createDefaultProps();
      render(<KanbanCard {...props} onClick={onClick} />);

      const card = screen.getByText('John Doe').closest('.MuiCard-root');
      if (card) {
        fireEvent.click(card);
      }

      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('should not fail when onClick is not provided', () => {
      const props = createDefaultProps();
      render(<KanbanCard {...props} />);

      const card = screen.getByText('John Doe').closest('.MuiCard-root');
      if (card) {
        // Should not throw
        expect(() => fireEvent.click(card)).not.toThrow();
      }
    });
  });

  describe('Drag-and-Drop States', () => {
    it('should apply dragging styles when isDragging is true', () => {
      const draggingSnapshot = { ...mockSnapshot, isDragging: true };
      const props = createDefaultProps();
      render(<KanbanCard {...props} snapshot={draggingSnapshot as typeof mockSnapshot} />);

      const card = screen.getByText('John Doe').closest('.MuiCard-root');
      expect(card).toBeInTheDocument();
    });

    it('should apply normal styles when isDragging is false', () => {
      const props = createDefaultProps();
      render(<KanbanCard {...props} snapshot={mockSnapshot} />);

      const card = screen.getByText('John Doe').closest('.MuiCard-root');
      expect(card).toBeInTheDocument();
    });
  });
});
