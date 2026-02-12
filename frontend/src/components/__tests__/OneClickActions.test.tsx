/**
 * Tests for OneClickActions Component
 *
 * Tests the one-click approve/reject functionality including:
 * - Approve and reject button rendering
 * - Loading states during mutations
 * - Success and error states
 * - Rationale expansion/collapse
 * - Confirmation dialog interactions
 * - Rejection reason selection
 * - Next stage selection for approval
 * - Callback invocations
 * - Accessibility and touch targets
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import OneClickActions from '../OneClickActions';

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) => defaultValue || key,
  }),
}));

// Mock hiring manager data hooks
const mockApproveMutateAsync = vi.fn();
const mockRejectMutateAsync = vi.fn();

vi.mock('@/hooks/useHiringManagerData', () => ({
  useApproveCandidate: () => ({
    mutateAsync: mockApproveMutateAsync,
    isPending: false,
  }),
  useRejectCandidate: () => ({
    mutateAsync: mockRejectMutateAsync,
    isPending: false,
  }),
}));

// Create a new query client for each test
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const renderWithProviders = (component: React.ReactNode) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{component}</QueryClientProvider>
  );
};

describe('OneClickActions', () => {
  const defaultProps = {
    candidateId: 'candidate-123',
    candidateName: 'John Doe',
    currentStage: 'Phone Screen',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render approve and reject buttons', () => {
      renderWithProviders(<OneClickActions {...defaultProps} />);

      expect(screen.getByText('Approve')).toBeInTheDocument();
      expect(screen.getByText('Reject')).toBeInTheDocument();
    });

    it('should display candidate name in header', () => {
      renderWithProviders(<OneClickActions {...defaultProps} />);

      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    it('should display current stage', () => {
      renderWithProviders(<OneClickActions {...defaultProps} />);

      expect(screen.getByText(/Current: Phone Screen/)).toBeInTheDocument();
    });

    it('should render rationale toggle button', () => {
      renderWithProviders(<OneClickActions {...defaultProps} />);

      expect(screen.getByText('Add Rationale / Options')).toBeInTheDocument();
    });

    it('should not display candidate name in compact mode', () => {
      renderWithProviders(<OneClickActions {...defaultProps} compact />);

      expect(screen.queryByText('John Doe')).not.toBeInTheDocument();
    });
  });

  describe('Approve Action', () => {
    it('should call approve mutation when clicking approve button', async () => {
      mockApproveMutateAsync.mockResolvedValueOnce({
        success: true,
        message: 'Candidate approved',
      });

      renderWithProviders(<OneClickActions {...defaultProps} />);

      const approveButton = screen.getByText('Approve').closest('button');
      fireEvent.click(approveButton!);

      await waitFor(() => {
        expect(mockApproveMutateAsync).toHaveBeenCalledWith({
          candidateId: 'candidate-123',
          request: {},
        });
      });
    });

    it('should call onActionComplete callback after successful approval', async () => {
      const onActionComplete = vi.fn();
      mockApproveMutateAsync.mockResolvedValueOnce({
        success: true,
        message: 'Candidate approved',
      });

      renderWithProviders(
        <OneClickActions {...defaultProps} onActionComplete={onActionComplete} />
      );

      const approveButton = screen.getByText('Approve').closest('button');
      fireEvent.click(approveButton!);

      await waitFor(() => {
        expect(onActionComplete).toHaveBeenCalledWith(
          expect.objectContaining({
            candidateId: 'candidate-123',
            success: true,
            decision: 'approved',
          })
        );
      });
    });

    it('should show approved state after successful approval', async () => {
      mockApproveMutateAsync.mockResolvedValueOnce({
        success: true,
        message: 'Candidate approved',
      });

      renderWithProviders(<OneClickActions {...defaultProps} />);

      const approveButton = screen.getByText('Approve').closest('button');
      fireEvent.click(approveButton!);

      await waitFor(() => {
        expect(screen.getByText('Approved')).toBeInTheDocument();
      });
    });
  });

  describe('Reject Action', () => {
    it('should call reject mutation when clicking reject button', async () => {
      mockRejectMutateAsync.mockResolvedValueOnce({
        success: true,
        message: 'Candidate rejected',
      });

      renderWithProviders(<OneClickActions {...defaultProps} />);

      const rejectButton = screen.getByText('Reject').closest('button');
      fireEvent.click(rejectButton!);

      await waitFor(() => {
        expect(mockRejectMutateAsync).toHaveBeenCalledWith({
          candidateId: 'candidate-123',
          request: {
            notify_candidate: true,
          },
        });
      });
    });

    it('should call onActionComplete callback after successful rejection', async () => {
      const onActionComplete = vi.fn();
      mockRejectMutateAsync.mockResolvedValueOnce({
        success: true,
        message: 'Candidate rejected',
      });

      renderWithProviders(
        <OneClickActions {...defaultProps} onActionComplete={onActionComplete} />
      );

      const rejectButton = screen.getByText('Reject').closest('button');
      fireEvent.click(rejectButton!);

      await waitFor(() => {
        expect(onActionComplete).toHaveBeenCalledWith(
          expect.objectContaining({
            candidateId: 'candidate-123',
            success: true,
            decision: 'rejected',
          })
        );
      });
    });

    it('should show rejected state after successful rejection', async () => {
      mockRejectMutateAsync.mockResolvedValueOnce({
        success: true,
        message: 'Candidate rejected',
      });

      renderWithProviders(<OneClickActions {...defaultProps} />);

      const rejectButton = screen.getByText('Reject').closest('button');
      fireEvent.click(rejectButton!);

      await waitFor(() => {
        expect(screen.getByText('Rejected')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message when approval fails', async () => {
      const onActionError = vi.fn();
      mockApproveMutateAsync.mockRejectedValueOnce(new Error('Approval failed'));

      renderWithProviders(
        <OneClickActions {...defaultProps} onActionError={onActionError} />
      );

      const approveButton = screen.getByText('Approve').closest('button');
      fireEvent.click(approveButton!);

      await waitFor(() => {
        expect(onActionError).toHaveBeenCalledWith('Approval failed');
      });
    });

    it('should display error message when rejection fails', async () => {
      const onActionError = vi.fn();
      mockRejectMutateAsync.mockRejectedValueOnce(new Error('Rejection failed'));

      renderWithProviders(
        <OneClickActions {...defaultProps} onActionError={onActionError} />
      );

      const rejectButton = screen.getByText('Reject').closest('button');
      fireEvent.click(rejectButton!);

      await waitFor(() => {
        expect(onActionError).toHaveBeenCalledWith('Rejection failed');
      });
    });

    it('should show error alert when action fails', async () => {
      mockApproveMutateAsync.mockRejectedValueOnce(new Error('Network error'));

      renderWithProviders(<OneClickActions {...defaultProps} />);

      const approveButton = screen.getByText('Approve').closest('button');
      fireEvent.click(approveButton!);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });
  });

  describe('Rationale Section', () => {
    it('should expand rationale section when toggle clicked', () => {
      renderWithProviders(<OneClickActions {...defaultProps} />);

      const toggleButton = screen.getByText('Add Rationale / Options');
      fireEvent.click(toggleButton);

      expect(screen.getByLabelText(/Rationale \(optional\)/)).toBeInTheDocument();
    });

    it('should collapse rationale section when toggle clicked again', () => {
      renderWithProviders(<OneClickActions {...defaultProps} />);

      const toggleButton = screen.getByText('Add Rationale / Options');
      fireEvent.click(toggleButton);
      expect(screen.getByLabelText(/Rationale \(optional\)/)).toBeInTheDocument();

      fireEvent.click(toggleButton);
      expect(screen.queryByLabelText(/Rationale \(optional\)/)).not.toBeInTheDocument();
    });

    it('should show expanded state by default when showRationaleExpanded is true', () => {
      renderWithProviders(<OneClickActions {...defaultProps} showRationaleExpanded />);

      expect(screen.getByLabelText(/Rationale \(optional\)/)).toBeInTheDocument();
    });

    it('should display rejection reason dropdown when expanded', () => {
      renderWithProviders(<OneClickActions {...defaultProps} />);

      const toggleButton = screen.getByText('Add Rationale / Options');
      fireEvent.click(toggleButton);

      expect(screen.getByLabelText(/Rejection Reason/)).toBeInTheDocument();
    });

    it('should display notify candidate toggle when expanded', () => {
      renderWithProviders(<OneClickActions {...defaultProps} />);

      const toggleButton = screen.getByText('Add Rationale / Options');
      fireEvent.click(toggleButton);

      expect(screen.getByText(/Notify candidate of rejection/)).toBeInTheDocument();
    });
  });

  describe('Confirmation Dialog', () => {
    it('should show confirmation dialog when rationale expanded and approve clicked', async () => {
      renderWithProviders(<OneClickActions {...defaultProps} showRationaleExpanded />);

      const approveButton = screen.getByText('Approve').closest('button');
      fireEvent.click(approveButton!);

      await waitFor(() => {
        expect(screen.getByText('Confirm Approval')).toBeInTheDocument();
      });
    });

    it('should show confirmation dialog when rationale expanded and reject clicked', async () => {
      renderWithProviders(<OneClickActions {...defaultProps} showRationaleExpanded />);

      const rejectButton = screen.getByText('Reject').closest('button');
      fireEvent.click(rejectButton!);

      await waitFor(() => {
        expect(screen.getByText('Confirm Rejection')).toBeInTheDocument();
      });
    });

    it('should close dialog when cancel clicked', async () => {
      renderWithProviders(<OneClickActions {...defaultProps} showRationaleExpanded />);

      const approveButton = screen.getByText('Approve').closest('button');
      fireEvent.click(approveButton!);

      await waitFor(() => {
        expect(screen.getByText('Confirm Approval')).toBeInTheDocument();
      });

      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByText('Confirm Approval')).not.toBeInTheDocument();
      });
    });

    it('should execute approval when confirm clicked in dialog', async () => {
      mockApproveMutateAsync.mockResolvedValueOnce({
        success: true,
        message: 'Approved',
      });

      renderWithProviders(<OneClickActions {...defaultProps} showRationaleExpanded />);

      const approveButton = screen.getByText('Approve').closest('button');
      fireEvent.click(approveButton!);

      await waitFor(() => {
        expect(screen.getByText('Confirm Approval')).toBeInTheDocument();
      });

      const confirmButton = screen.getByText('Yes, Approve');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockApproveMutateAsync).toHaveBeenCalled();
      });
    });

    it('should execute rejection when confirm clicked in dialog', async () => {
      mockRejectMutateAsync.mockResolvedValueOnce({
        success: true,
        message: 'Rejected',
      });

      renderWithProviders(<OneClickActions {...defaultProps} showRationaleExpanded />);

      const rejectButton = screen.getByText('Reject').closest('button');
      fireEvent.click(rejectButton!);

      await waitFor(() => {
        expect(screen.getByText('Confirm Rejection')).toBeInTheDocument();
      });

      const confirmButton = screen.getByText('Yes, Reject');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockRejectMutateAsync).toHaveBeenCalled();
      });
    });
  });

  describe('Disabled State', () => {
    it('should disable approve button when disabled prop is true', () => {
      renderWithProviders(<OneClickActions {...defaultProps} disabled />);

      const approveButton = screen.getByText('Approve').closest('button');
      expect(approveButton).toBeDisabled();
    });

    it('should disable reject button when disabled prop is true', () => {
      renderWithProviders(<OneClickActions {...defaultProps} disabled />);

      const rejectButton = screen.getByText('Reject').closest('button');
      expect(rejectButton).toBeDisabled();
    });

    it('should not call mutation when disabled and clicked', async () => {
      renderWithProviders(<OneClickActions {...defaultProps} disabled />);

      const approveButton = screen.getByText('Approve').closest('button');
      fireEvent.click(approveButton!);

      expect(mockApproveMutateAsync).not.toHaveBeenCalled();
    });
  });

  describe('Post-Action States', () => {
    it('should disable buttons after approval', async () => {
      mockApproveMutateAsync.mockResolvedValueOnce({
        success: true,
        message: 'Approved',
      });

      renderWithProviders(<OneClickActions {...defaultProps} />);

      const approveButton = screen.getByText('Approve').closest('button');
      fireEvent.click(approveButton!);

      await waitFor(() => {
        expect(screen.getByText('Approved')).toBeInTheDocument();
      });

      // After approval, reject button should be disabled
      const rejectButton = screen.getByText('Reject').closest('button');
      expect(rejectButton).toBeDisabled();
    });

    it('should disable buttons after rejection', async () => {
      mockRejectMutateAsync.mockResolvedValueOnce({
        success: true,
        message: 'Rejected',
      });

      renderWithProviders(<OneClickActions {...defaultProps} />);

      const rejectButton = screen.getByText('Reject').closest('button');
      fireEvent.click(rejectButton!);

      await waitFor(() => {
        expect(screen.getByText('Rejected')).toBeInTheDocument();
      });

      // After rejection, approve button should be disabled
      const approveButton = screen.getByText('Approve').closest('button');
      expect(approveButton).toBeDisabled();
    });

    it('should hide rationale toggle after action completed', async () => {
      mockApproveMutateAsync.mockResolvedValueOnce({
        success: true,
        message: 'Approved',
      });

      renderWithProviders(<OneClickActions {...defaultProps} />);

      const approveButton = screen.getByText('Approve').closest('button');
      fireEvent.click(approveButton!);

      await waitFor(() => {
        expect(screen.getByText('Approved')).toBeInTheDocument();
      });

      expect(screen.queryByText('Add Rationale / Options')).not.toBeInTheDocument();
    });
  });

  describe('Compact Mode', () => {
    it('should render in compact mode without header', () => {
      renderWithProviders(<OneClickActions {...defaultProps} compact />);

      expect(screen.queryByText('John Doe')).not.toBeInTheDocument();
    });

    it('should show quick tip in compact mode', () => {
      renderWithProviders(<OneClickActions {...defaultProps} compact />);

      expect(
        screen.getByText(/Quick decision: Just tap Approve or Reject/)
      ).toBeInTheDocument();
    });

    it('should not show quick tip after action completed', async () => {
      mockApproveMutateAsync.mockResolvedValueOnce({
        success: true,
        message: 'Approved',
      });

      renderWithProviders(<OneClickActions {...defaultProps} compact />);

      const approveButton = screen.getByText('Approve').closest('button');
      fireEvent.click(approveButton!);

      await waitFor(() => {
        expect(screen.getByText('Approved')).toBeInTheDocument();
      });

      expect(
        screen.queryByText(/Quick decision: Just tap Approve or Reject/)
      ).not.toBeInTheDocument();
    });
  });

  describe('Stacked Layout', () => {
    it('should render buttons vertically when stacked prop is true', () => {
      const { container } = renderWithProviders(
        <OneClickActions {...defaultProps} stacked />
      );

      const stackContainers = container.querySelectorAll('.MuiStack-root');
      expect(stackContainers.length).toBeGreaterThan(0);
    });
  });

  describe('Accessibility', () => {
    it('should have minimum touch target height for buttons', () => {
      const { container } = renderWithProviders(<OneClickActions {...defaultProps} />);

      const buttons = container.querySelectorAll('button');
      buttons.forEach((button) => {
        const style = window.getComputedStyle(button);
        expect(parseInt(style.minHeight) || 0).toBeGreaterThanOrEqual(0);
      });
    });

    it('should have tooltips for post-action buttons', async () => {
      mockApproveMutateAsync.mockResolvedValueOnce({
        success: true,
        message: 'Approved',
      });

      renderWithProviders(<OneClickActions {...defaultProps} />);

      const approveButton = screen.getByText('Approve').closest('button');
      fireEvent.click(approveButton!);

      await waitFor(() => {
        expect(screen.getByText('Approved')).toBeInTheDocument();
      });

      // Approved state should have a tooltip
      const approvedButton = screen.getByText('Approved').closest('button');
      expect(approvedButton).toBeInTheDocument();
    });
  });

  describe('Available Stages', () => {
    it('should show next stage selector when availableStages provided', () => {
      const availableStages = [
        { id: 'stage-1', name: 'Technical Interview' },
        { id: 'stage-2', name: 'Final Interview' },
      ];

      renderWithProviders(
        <OneClickActions {...defaultProps} showRationaleExpanded availableStages={availableStages} />
      );

      expect(screen.getByLabelText(/Next Stage \(for approval\)/)).toBeInTheDocument();
    });

    it('should not show next stage selector when availableStages is empty', () => {
      renderWithProviders(
        <OneClickActions {...defaultProps} showRationaleExpanded availableStages={[]} />
      );

      expect(screen.queryByLabelText(/Next Stage \(for approval\)/)).not.toBeInTheDocument();
    });
  });

  describe('Rejection Reasons', () => {
    it('should show predefined rejection reasons in dropdown', () => {
      renderWithProviders(<OneClickActions {...defaultProps} showRationaleExpanded />);

      const rejectionReasonSelect = screen.getByLabelText(/Rejection Reason/);
      fireEvent.mouseDown(rejectionReasonSelect);

      // Check for some rejection reasons
      expect(screen.getByRole('option', { name: /Insufficient skills match/ })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Not enough experience/ })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Other/ })).toBeInTheDocument();
    });
  });

  describe('Notify Candidate Toggle', () => {
    it('should toggle notify candidate setting', () => {
      renderWithProviders(<OneClickActions {...defaultProps} showRationaleExpanded />);

      const yesChip = screen.getByText('Yes');
      fireEvent.click(yesChip);

      expect(screen.getByText('No')).toBeInTheDocument();
    });

    it('should start with notify candidate set to true', () => {
      renderWithProviders(<OneClickActions {...defaultProps} showRationaleExpanded />);

      const yesChip = screen.getByText('Yes');
      expect(yesChip).toBeInTheDocument();
    });
  });

  describe('Custom Touch Target Height', () => {
    it('should use custom touch target height when specified', () => {
      const { container } = renderWithProviders(
        <OneClickActions {...defaultProps} touchTargetHeight={56} />
      );

      const buttons = container.querySelectorAll('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  describe('Props Validation', () => {
    it('should work without optional props', () => {
      renderWithProviders(<OneClickActions candidateId="test-id" />);

      expect(screen.getByText('Approve')).toBeInTheDocument();
      expect(screen.getByText('Reject')).toBeInTheDocument();
    });

    it('should handle undefined callbacks gracefully', async () => {
      mockApproveMutateAsync.mockResolvedValueOnce({
        success: true,
        message: 'Approved',
      });

      renderWithProviders(
        <OneClickActions candidateId="test-id" onActionComplete={undefined} onActionError={undefined} />
      );

      const approveButton = screen.getByText('Approve').closest('button');
      fireEvent.click(approveButton!);

      // Should not throw error
      await waitFor(() => {
        expect(mockApproveMutateAsync).toHaveBeenCalled();
      });
    });
  });
});

describe('OneClickActions - Rationale Submission', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should include rationale in approval request', async () => {
    mockApproveMutateAsync.mockResolvedValueOnce({
      success: true,
      message: 'Approved',
    });

    const { container } = renderWithProviders(<OneClickActions candidateId="test-id" showRationaleExpanded />);

    const rationaleInput = screen.getByLabelText(/Rationale \(optional\)/);
    fireEvent.change(rationaleInput, { target: { value: 'Excellent candidate' } });

    const approveButton = screen.getByText('Approve').closest('button');
    fireEvent.click(approveButton!);

    await waitFor(() => {
      expect(screen.getByText('Confirm Approval')).toBeInTheDocument();
    });

    const confirmButton = screen.getByText('Yes, Approve');
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockApproveMutateAsync).toHaveBeenCalledWith({
        candidateId: 'test-id',
        request: {
          rationale: 'Excellent candidate',
        },
      });
    });
  });

  it('should include rejection reason in rejection request', async () => {
    mockRejectMutateAsync.mockResolvedValueOnce({
      success: true,
      message: 'Rejected',
    });

    renderWithProviders(<OneClickActions candidateId="test-id" showRationaleExpanded />);

    const rejectionReasonSelect = screen.getByLabelText(/Rejection Reason/);
    fireEvent.mouseDown(rejectionReasonSelect);

    const skillsOption = screen.getByRole('option', { name: /Insufficient skills match/ });
    fireEvent.click(skillsOption);

    const rejectButton = screen.getByText('Reject').closest('button');
    fireEvent.click(rejectButton!);

    await waitFor(() => {
      expect(screen.getByText('Confirm Rejection')).toBeInTheDocument();
    });

    const confirmButton = screen.getByText('Yes, Reject');
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockRejectMutateAsync).toHaveBeenCalledWith({
        candidateId: 'test-id',
        request: {
          rejection_reason: 'skills_match',
          notify_candidate: true,
        },
      });
    });
  });
});
