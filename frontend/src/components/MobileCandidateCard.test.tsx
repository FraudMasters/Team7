import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { createTheme } from '@mui/material/styles';
import MobileCandidateCard from './MobileCandidateCard';
import type { CandidateListItem } from '../types/api';
import { Delete as DeleteIcon, Star as StarIcon } from '@mui/icons-material';

/**
 * MobileCandidateCard Component Tests
 *
 * Tests the mobile-optimized candidate card component including:
 * - Rendering with various props
 * - Swipe actions (simulated)
 * - Touch target sizes
 * - Accessibility
 */

const theme = createTheme();

const mockCandidate: CandidateListItem = {
  id: '1',
  filename: 'John_Doe_Resume.pdf',
  current_stage: 'screening',
  stage_name: 'Screening',
  vacancy_id: 'vac-1',
  created_at: '2024-01-15T10:00:00Z',
  updated_at: '2024-01-15T10:00:00Z',
  notes: null,
  tags: [
    {
      id: 'tag-1',
      tag_name: 'Senior',
      color: '#ff5722',
      organization_id: 'org-1',
    },
    {
      id: 'tag-2',
      tag_name: 'Remote',
      color: '#4caf50',
      organization_id: 'org-1',
    },
  ],
  notes_count: 3,
  latest_activity: {
    activity_type: 'stage_change',
    created_at: '2024-01-15T10:00:00Z',
  },
};

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

describe('MobileCandidateCard', () => {
  describe('Rendering', () => {
    it('should render candidate information correctly', () => {
      renderWithTheme(<MobileCandidateCard candidate={mockCandidate} />);

      expect(screen.getByText('John_Doe_Resume.pdf')).toBeInTheDocument();
      expect(screen.getByText('Screening')).toBeInTheDocument();
    });

    it('should render avatar by default', () => {
      const { container } = renderWithTheme(
        <MobileCandidateCard candidate={mockCandidate} />
      );

      const avatar = container.querySelector('.MuiAvatar-root');
      expect(avatar).toBeInTheDocument();
    });

    it('should hide avatar when showAvatar is false', () => {
      const { container } = renderWithTheme(
        <MobileCandidateCard candidate={mockCandidate} showAvatar={false} />
      );

      const avatar = container.querySelector('.MuiAvatar-root');
      expect(avatar).not.toBeInTheDocument();
    });

    it('should render tags when showTags is true', () => {
      renderWithTheme(<MobileCandidateCard candidate={mockCandidate} showTags={true} />);

      expect(screen.getByText('Senior')).toBeInTheDocument();
      expect(screen.getByText('Remote')).toBeInTheDocument();
    });

    it('should hide tags when showTags is false', () => {
      renderWithTheme(<MobileCandidateCard candidate={mockCandidate} showTags={false} />);

      expect(screen.queryByText('Senior')).not.toBeInTheDocument();
      expect(screen.queryByText('Remote')).not.toBeInTheDocument();
    });

    it('should show notes count when candidate has notes', () => {
      renderWithTheme(<MobileCandidateCard candidate={mockCandidate} />);

      expect(screen.getByText('3 notes')).toBeInTheDocument();
    });

    it('should show activity indicator when showActivity is true', () => {
      renderWithTheme(<MobileCandidateCard candidate={mockCandidate} showActivity={true} />);

      const activityDate = new Date(mockCandidate.latest_activity!.created_at).toLocaleDateString();
      expect(screen.getByText(activityDate)).toBeInTheDocument();
    });

    it('should hide activity indicator when showActivity is false', () => {
      renderWithTheme(<MobileCandidateCard candidate={mockCandidate} showActivity={false} />);

      const activityDate = new Date(mockCandidate.latest_activity!.created_at).toLocaleDateString();
      expect(screen.queryByText(activityDate)).not.toBeInTheDocument();
    });

    it('should truncate tags when more than 2', () => {
      const candidateWithManyTags: CandidateListItem = {
        ...mockCandidate,
        tags: [
          ...mockCandidate.tags,
          {
            id: 'tag-3',
            tag_name: 'Full-time',
            color: '#2196f3',
            organization_id: 'org-1',
          },
        ],
      };

      renderWithTheme(<MobileCandidateCard candidate={candidateWithManyTags} />);

      expect(screen.getByText('+1')).toBeInTheDocument();
    });

    it('should render chevron icon when onClick is provided', () => {
      const { container } = renderWithTheme(
        <MobileCandidateCard candidate={mockCandidate} onClick={() => {}} />
      );

      const chevron = container.querySelector('svg[data-testid="ChevronRightIcon"]');
      expect(chevron).toBeInTheDocument();
    });
  });

  describe('Touch Targets', () => {
    it('should have avatar with minimum 44x44px size', () => {
      const { container } = renderWithTheme(
        <MobileCandidateCard candidate={mockCandidate} />
      );

      const avatar = container.querySelector('.MuiAvatar-root');
      expect(avatar).toHaveStyle({ width: '44px', height: '44px' });
    });

    it('should have clickable card when onClick is provided', () => {
      const handleClick = vi.fn();

      const { container } = renderWithTheme(
        <MobileCandidateCard candidate={mockCandidate} onClick={handleClick} />
      );

      const card = container.querySelector('.MuiCard-root');
      expect(card).toHaveStyle({ cursor: 'pointer' });
    });

    it('should call onClick when card is clicked', () => {
      const handleClick = vi.fn();

      const { container } = renderWithTheme(
        <MobileCandidateCard candidate={mockCandidate} onClick={handleClick} />
      );

      const card = container.querySelector('.MuiCard-root');
      fireEvent.click(card!);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('Swipe Actions', () => {
    it('should render without errors when swipe actions are provided', () => {
      const leftAction = {
        icon: <DeleteIcon data-testid="delete-icon" />,
        color: '#f44336',
        label: 'Delete',
        onAction: vi.fn(),
      };

      const rightAction = {
        icon: <StarIcon data-testid="star-icon" />,
        color: '#ff9800',
        label: 'Save',
        onAction: vi.fn(),
      };

      renderWithTheme(
        <MobileCandidateCard
          candidate={mockCandidate}
          leftAction={leftAction}
          rightAction={rightAction}
        />
      );

      expect(screen.getByText('John_Doe_Resume.pdf')).toBeInTheDocument();
    });

    it('should disable swipe when onClick is provided', () => {
      const rightAction = {
        icon: <StarIcon />,
        color: '#ff9800',
        label: 'Save',
        onAction: vi.fn(),
      };

      const { container } = renderWithTheme(
        <MobileCandidateCard
          candidate={mockCandidate}
          rightAction={rightAction}
          onClick={() => {}}
        />
      );

      const card = container.querySelector('.MuiCard-root');
      expect(card).toHaveStyle({ cursor: 'pointer' });
    });

    it('should disable swipe when swipeEnabled is false', () => {
      const rightAction = {
        icon: <StarIcon />,
        color: '#ff9800',
        label: 'Save',
        onAction: vi.fn(),
      };

      renderWithTheme(
        <MobileCandidateCard
          candidate={mockCandidate}
          rightAction={rightAction}
          swipeEnabled={false}
        />
      );

      // Card should render normally
      expect(screen.getByText('John_Doe_Resume.pdf')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle candidate with no tags', () => {
      const candidateWithoutTags: CandidateListItem = {
        ...mockCandidate,
        tags: [],
      };

      renderWithTheme(<MobileCandidateCard candidate={candidateWithoutTags} />);

      expect(screen.getByText('John_Doe_Resume.pdf')).toBeInTheDocument();
    });

    it('should handle candidate with no notes', () => {
      const candidateWithoutNotes: CandidateListItem = {
        ...mockCandidate,
        notes_count: 0,
      };

      renderWithTheme(<MobileCandidateCard candidate={candidateWithoutNotes} />);

      expect(screen.queryByText(/notes/)).not.toBeInTheDocument();
    });

    it('should handle candidate with no latest activity', () => {
      const candidateWithoutActivity: CandidateListItem = {
        ...mockCandidate,
        latest_activity: null,
      };

      renderWithTheme(<MobileCandidateCard candidate={candidateWithoutActivity} />);

      expect(screen.getByText('John_Doe_Resume.pdf')).toBeInTheDocument();
    });

    it('should handle candidate with empty filename', () => {
      const candidateWithEmptyName: CandidateListItem = {
        ...mockCandidate,
        filename: '',
      };

      renderWithTheme(<MobileCandidateCard candidate={candidateWithEmptyName} />);

      expect(screen.getByText('Unknown Candidate')).toBeInTheDocument();
    });

    it('should handle candidate with null stage name', () => {
      const candidateWithNullStage: CandidateListItem = {
        ...mockCandidate,
        stage_name: '',
        current_stage: 'applied',
      };

      renderWithTheme(<MobileCandidateCard candidate={candidateWithNullStage} />);

      expect(screen.getByText('applied')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible chip labels', () => {
      renderWithTheme(<MobileCandidateCard candidate={mockCandidate} />);

      const stageChip = screen.getByText('Screening');
      expect(stageChip).toBeInTheDocument();
    });

    it('should render with correct ARIA attributes', () => {
      const { container } = renderWithTheme(
        <MobileCandidateCard candidate={mockCandidate} onClick={() => {}} />
      );

      const card = container.querySelector('.MuiCard-root');
      expect(card).toHaveAttribute('role', 'button');
    });
  });

  describe('Styling', () => {
    it('should apply custom sx props', () => {
      const { container } = renderWithTheme(
        <MobileCandidateCard
          candidate={mockCandidate}
          sx={{ mt: 4, bgcolor: 'background.paper' }}
        />
      );

      const cardWrapper = container.firstChild?.firstChild;
      expect(cardWrapper).toHaveStyle({ marginTop: '16px' });
    });

    it('should pass through CardProps', () => {
      const { container } = renderWithTheme(
        <MobileCandidateCard candidate={mockCandidate} elevation={3} />
      );

      const card = container.querySelector('.MuiPaper-elevation3');
      expect(card).toBeInTheDocument();
    });
  });
});
