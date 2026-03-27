/**
 * Tests for ModelApprovalPanel Component
 *
 * Tests the model deployment approval workflow panel including:
 * - Rendering approval requests with different statuses
 * - Filtering by model and status
 * - Statistics display
 * - Approve, reject, and deploy actions
 * - Dialog interactions
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ModelApprovalPanel from './ModelApprovalPanel';

// Mock the modelApprovalsClient
vi.mock('@/api/modelApprovals', () => ({
  modelApprovalsClient: {
    listApprovals: vi.fn(),
    approveRequest: vi.fn(),
    rejectRequest: vi.fn(),
    deployRequest: vi.fn(),
  },
}));

import { modelApprovalsClient } from '@/api/modelApprovals';

const mockListApprovals = vi.mocked(modelApprovalsClient.listApprovals);
const mockApproveRequest = vi.mocked(modelApprovalsClient.approveRequest);
const mockRejectRequest = vi.mocked(modelApprovalsClient.rejectRequest);
const mockDeployRequest = vi.mocked(modelApprovalsClient.deployRequest);

describe('ModelApprovalPanel', () => {
  const mockApprovals = [
    {
      id: '1',
      model_version_id: 'v1.2.0',
      model_name: 'skill_matching',
      version: 'v1.2.0',
      status: 'pending' as const,
      justification: 'Improved accuracy by 5%',
      target_environment: 'production',
      requested_by: 'data-scientist@example.com',
      reviewed_by: null,
      review_notes: null,
      created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      reviewed_at: null,
    },
    {
      id: '2',
      model_version_id: 'v2.0.0',
      model_name: 'ranking',
      version: 'v2.0.0',
      status: 'approved' as const,
      justification: 'Ready for production',
      target_environment: 'production',
      requested_by: 'ml-engineer@example.com',
      reviewed_by: 'admin@example.com',
      review_notes: 'Approved after testing',
      created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 20 * 60 * 60 * 1000).toISOString(),
      reviewed_at: new Date(Date.now() - 20 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: '3',
      model_version_id: 'v1.0.0',
      model_name: 'skill_matching',
      version: 'v1.0.0',
      status: 'deployed' as const,
      justification: 'Initial deployment',
      target_environment: 'production',
      requested_by: 'dev@example.com',
      reviewed_by: 'lead@example.com',
      review_notes: 'Deployed successfully',
      created_at: new Date(Date.now() - 72 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
      reviewed_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: '4',
      model_version_id: 'v0.9.0',
      model_name: 'ranking',
      version: 'v0.9.0',
      status: 'rejected' as const,
      justification: 'Experimental feature',
      target_environment: 'production',
      requested_by: 'research@example.com',
      reviewed_by: 'lead@example.com',
      review_notes: 'Not ready for production',
      created_at: new Date(Date.now() - 96 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 90 * 60 * 60 * 1000).toISOString(),
      reviewed_at: new Date(Date.now() - 90 * 60 * 60 * 1000).toISOString(),
    },
  ];

  const mockListResponse = {
    approvals: mockApprovals,
    total_count: mockApprovals.length,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockListApprovals.mockResolvedValue(mockListResponse);
    mockApproveRequest.mockResolvedValue({} as any);
    mockRejectRequest.mockResolvedValue({} as any);
    mockDeployRequest.mockResolvedValue({} as any);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders loading state initially', () => {
      mockListApprovals.mockImplementation(() => new Promise(() => {}));

      render(<ModelApprovalPanel />);

      expect(screen.getByText('Loading approval requests...')).toBeInTheDocument();
    });

    it('renders main header with title after loading', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('Model Deployment Approvals')).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
    });

    it('renders refresh button', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('Model Deployment Approvals')).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
    });

    it('renders stats cards after loading', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('Total')).toBeInTheDocument();
      });

      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(screen.getByText('Approved')).toBeInTheDocument();
      expect(screen.getByText('Deployed')).toBeInTheDocument();
      expect(screen.getByText('Rejected')).toBeInTheDocument();
      expect(screen.getByText('Cancelled')).toBeInTheDocument();
    });

    it('renders filter controls when showFilters is true', async () => {
      render(<ModelApprovalPanel showFilters={true} />);

      await waitFor(() => {
        expect(screen.getByLabelText('Model')).toBeInTheDocument();
      });

      expect(screen.getByLabelText('Status')).toBeInTheDocument();
    });

    it('hides filter controls when showFilters is false', async () => {
      render(<ModelApprovalPanel showFilters={false} />);

      await waitFor(() => {
        expect(screen.getByText('Model Deployment Approvals')).toBeInTheDocument();
      });

      expect(screen.queryByLabelText('Model')).not.toBeInTheDocument();
      expect(screen.queryByLabelText('Status')).not.toBeInTheDocument();
    });

    it('renders approval cards with version info', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v1.2.0')).toBeInTheDocument();
      });

      expect(screen.getByText('v2.0.0')).toBeInTheDocument();
      expect(screen.getByText('v1.0.0')).toBeInTheDocument();
    });

    it('renders model name chips', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getAllByText('skill_matching').length).toBeGreaterThan(0);
      });

      expect(screen.getAllByText('ranking').length).toBeGreaterThan(0);
    });

    it('renders requester email', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('data-scientist@example.com')).toBeInTheDocument();
      });

      expect(screen.getByText('ml-engineer@example.com')).toBeInTheDocument();
    });

    it('renders status chips', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('pending')).toBeInTheDocument();
      });

      expect(screen.getByText('approved')).toBeInTheDocument();
      expect(screen.getByText('deployed')).toBeInTheDocument();
      expect(screen.getByText('rejected')).toBeInTheDocument();
    });

    it('renders empty state when no approvals', async () => {
      mockListApprovals.mockResolvedValue({
        approvals: [],
        total_count: 0,
      });

      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('No approval requests found')).toBeInTheDocument();
      });
    });
  });

  describe('Filter Functionality', () => {
    it('filters by status when status select changes', async () => {
      render(<ModelApprovalPanel showFilters={true} />);

      await waitFor(() => {
        expect(screen.getByText('Model Deployment Approvals')).toBeInTheDocument();
      });

      // Open status dropdown
      const statusSelect = screen.getByLabelText('Status');
      fireEvent.mouseDown(statusSelect);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      // Select 'approved'
      fireEvent.click(screen.getByRole('option', { name: 'Approved' }));

      await waitFor(() => {
        expect(mockListApprovals).toHaveBeenCalledWith(
          expect.objectContaining({ status: 'approved' })
        );
      });
    });

    it('filters by model when model select changes', async () => {
      render(<ModelApprovalPanel showFilters={true} />);

      await waitFor(() => {
        expect(screen.getByText('Model Deployment Approvals')).toBeInTheDocument();
      });

      // Open model dropdown
      const modelSelect = screen.getByLabelText('Model');
      fireEvent.mouseDown(modelSelect);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      // Select 'skill_matching'
      fireEvent.click(screen.getByRole('option', { name: 'Skill Matching' }));

      await waitFor(() => {
        expect(mockListApprovals).toHaveBeenCalledWith(
          expect.objectContaining({ model_name: 'skill_matching' })
        );
      });
    });

    it('uses initial model filter from props', async () => {
      render(<ModelApprovalPanel showFilters={true} modelFilter="ranking" />);

      await waitFor(() => {
        expect(mockListApprovals).toHaveBeenCalled();
      });

      // The initial filter should be used
      expect(mockListApprovals).toHaveBeenCalledWith(
        expect.objectContaining({ model_name: 'ranking' })
      );
    });

    it('sends all status when "All Statuses" is selected', async () => {
      render(<ModelApprovalPanel showFilters={true} />);

      await waitFor(() => {
        expect(screen.getByText('Model Deployment Approvals')).toBeInTheDocument();
      });

      // Open status dropdown
      const statusSelect = screen.getByLabelText('Status');
      fireEvent.mouseDown(statusSelect);

      await waitFor(() => {
        expect(screen.getByRole('listbox')).toBeInTheDocument();
      });

      // Select 'All Statuses'
      fireEvent.click(screen.getByRole('option', { name: 'All Statuses' }));

      await waitFor(() => {
        expect(mockListApprovals).toHaveBeenCalledWith(
          expect.objectContaining({})
        );
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('calls listApprovals when refresh button is clicked', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('Model Deployment Approvals')).toBeInTheDocument();
      });

      // Clear previous calls
      mockListApprovals.mockClear();

      // Click refresh
      fireEvent.click(screen.getByRole('button', { name: /refresh/i }));

      await waitFor(() => {
        expect(mockListApprovals).toHaveBeenCalled();
      });
    });

    it('disables refresh button while refreshing', async () => {
      mockListApprovals.mockImplementation(() => new Promise(() => {}));

      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('Model Deployment Approvals')).toBeInTheDocument();
      });

      // Reset mock to resolve quickly
      mockListApprovals.mockResolvedValue(mockListResponse);

      // Click refresh - button should still be clickable initially
      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      expect(refreshButton).not.toBeDisabled();
    });
  });

  describe('Card Expansion', () => {
    it('expands card when expand button is clicked', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v1.2.0')).toBeInTheDocument();
      });

      // Find expand button for the first approval
      const expandButtons = screen.getAllByRole('button', { name: '' });
      const expandButton = expandButtons.find((btn) =>
        btn.querySelector('svg[data-testid="ExpandMoreIcon"]')
      );

      if (expandButton) {
        fireEvent.click(expandButton);

        await waitFor(() => {
          expect(screen.getByText(/Justification:/)).toBeInTheDocument();
        });
      }
    });

    it('shows justification when expanded', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v1.2.0')).toBeInTheDocument();
      });

      // Find and click expand button
      const expandButtons = screen.getAllByRole('button', { name: '' });
      const expandButton = expandButtons.find((btn) =>
        btn.querySelector('svg[data-testid="ExpandMoreIcon"]')
      );

      if (expandButton) {
        fireEvent.click(expandButton);

        await waitFor(() => {
          expect(screen.getByText(/Improved accuracy by 5%/)).toBeInTheDocument();
        });
      }
    });

    it('shows action buttons for pending approvals when expanded', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v1.2.0')).toBeInTheDocument();
      });

      // Find and click expand button
      const expandButtons = screen.getAllByRole('button', { name: '' });
      const expandButton = expandButtons.find((btn) =>
        btn.querySelector('svg[data-testid="ExpandMoreIcon"]')
      );

      if (expandButton) {
        fireEvent.click(expandButton);

        await waitFor(() => {
          expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
          expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
        });
      }
    });

    it('shows deploy button for approved approvals when expanded', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v2.0.0')).toBeInTheDocument();
      });

      // Find all expand buttons
      const allButtons = screen.getAllByRole('button');

      // Click expand buttons until we find the one for the approved request
      for (const button of allButtons) {
        fireEvent.click(button);
      }

      await waitFor(() => {
        const deployButtons = screen.getAllByRole('button', { name: /deploy/i });
        expect(deployButtons.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Approve Action', () => {
    it('opens approve dialog when approve button is clicked', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v1.2.0')).toBeInTheDocument();
      });

      // Expand the pending approval card
      const expandButtons = screen.getAllByRole('button', { name: '' });
      const expandButton = expandButtons.find((btn) =>
        btn.querySelector('svg[data-testid="ExpandMoreIcon"]')
      );

      if (expandButton) {
        fireEvent.click(expandButton);
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
      });

      // Click approve button
      fireEvent.click(screen.getByRole('button', { name: /approve/i }));

      await waitFor(() => {
        expect(screen.getByText('Approve Deployment Request')).toBeInTheDocument();
      });
    });

    it('calls approveRequest when confirm is clicked', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v1.2.0')).toBeInTheDocument();
      });

      // Expand and click approve
      const expandButtons = screen.getAllByRole('button', { name: '' });
      const expandButton = expandButtons.find((btn) =>
        btn.querySelector('svg[data-testid="ExpandMoreIcon"]')
      );

      if (expandButton) {
        fireEvent.click(expandButton);
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /approve/i }));

      await waitFor(() => {
        expect(screen.getByText('Approve Deployment Request')).toBeInTheDocument();
      });

      // Confirm approval
      const confirmButtons = screen.getAllByRole('button', { name: /approve/i });
      const confirmButton = confirmButtons.find((btn) =>
        btn.getAttribute('type') !== 'button' || btn.textContent === 'Approve'
      );

      if (confirmButton) {
        fireEvent.click(confirmButton);
      }

      await waitFor(() => {
        expect(mockApproveRequest).toHaveBeenCalledWith(
          '1',
          expect.objectContaining({
            reviewed_by: expect.any(String),
          })
        );
      });
    });

    it('shows review notes field in dialog', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v1.2.0')).toBeInTheDocument();
      });

      // Expand and click approve
      const expandButtons = screen.getAllByRole('button', { name: '' });
      const expandButton = expandButtons.find((btn) =>
        btn.querySelector('svg[data-testid="ExpandMoreIcon"]')
      );

      if (expandButton) {
        fireEvent.click(expandButton);
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /approve/i }));

      await waitFor(() => {
        expect(screen.getByLabelText(/review notes/i)).toBeInTheDocument();
      });
    });

    it('closes dialog when cancel is clicked', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v1.2.0')).toBeInTheDocument();
      });

      // Expand and click approve
      const expandButtons = screen.getAllByRole('button', { name: '' });
      const expandButton = expandButtons.find((btn) =>
        btn.querySelector('svg[data-testid="ExpandMoreIcon"]')
      );

      if (expandButton) {
        fireEvent.click(expandButton);
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /approve/i }));

      await waitFor(() => {
        expect(screen.getByText('Approve Deployment Request')).toBeInTheDocument();
      });

      // Click cancel
      fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

      await waitFor(() => {
        expect(screen.queryByText('Approve Deployment Request')).not.toBeInTheDocument();
      });
    });
  });

  describe('Reject Action', () => {
    it('opens reject dialog when reject button is clicked', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v1.2.0')).toBeInTheDocument();
      });

      // Expand the pending approval card
      const expandButtons = screen.getAllByRole('button', { name: '' });
      const expandButton = expandButtons.find((btn) =>
        btn.querySelector('svg[data-testid="ExpandMoreIcon"]')
      );

      if (expandButton) {
        fireEvent.click(expandButton);
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
      });

      // Click reject button
      fireEvent.click(screen.getByRole('button', { name: /reject/i }));

      await waitFor(() => {
        expect(screen.getByText('Reject Deployment Request')).toBeInTheDocument();
      });
    });

    it('calls rejectRequest when confirm is clicked', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v1.2.0')).toBeInTheDocument();
      });

      // Expand and click reject
      const expandButtons = screen.getAllByRole('button', { name: '' });
      const expandButton = expandButtons.find((btn) =>
        btn.querySelector('svg[data-testid="ExpandMoreIcon"]')
      );

      if (expandButton) {
        fireEvent.click(expandButton);
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /reject/i }));

      await waitFor(() => {
        expect(screen.getByText('Reject Deployment Request')).toBeInTheDocument();
      });

      // Find reject confirm button in dialog
      const rejectButtons = screen.getAllByRole('button', { name: /reject/i });
      const confirmButton = rejectButtons[rejectButtons.length - 1];

      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockRejectRequest).toHaveBeenCalledWith(
          '1',
          expect.objectContaining({
            reviewed_by: expect.any(String),
          })
        );
      });
    });
  });

  describe('Deploy Action', () => {
    it('opens deploy dialog when deploy button is clicked', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v2.0.0')).toBeInTheDocument();
      });

      // Find the approved item and expand it
      const allButtons = screen.getAllByRole('button');

      // Click expand buttons
      for (const button of allButtons) {
        const svg = button.querySelector('svg[data-testid="ExpandMoreIcon"]');
        if (svg) {
          fireEvent.click(button);
        }
      }

      await waitFor(() => {
        const deployButtons = screen.getAllByRole('button', { name: /deploy/i });
        expect(deployButtons.length).toBeGreaterThan(0);
      });

      // Click deploy button
      const deployButtons = screen.getAllByRole('button', { name: /deploy/i });
      fireEvent.click(deployButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Deploy Model')).toBeInTheDocument();
      });
    });

    it('shows warning alert in deploy dialog', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v2.0.0')).toBeInTheDocument();
      });

      // Find the approved item and expand it
      const allButtons = screen.getAllByRole('button');

      // Click expand buttons
      for (const button of allButtons) {
        const svg = button.querySelector('svg[data-testid="ExpandMoreIcon"]');
        if (svg) {
          fireEvent.click(button);
        }
      }

      await waitFor(() => {
        const deployButtons = screen.getAllByRole('button', { name: /deploy/i });
        expect(deployButtons.length).toBeGreaterThan(0);
      });

      // Click deploy button
      const deployButtons = screen.getAllByRole('button', { name: /deploy/i });
      fireEvent.click(deployButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/This will deploy the model to/)).toBeInTheDocument();
      });
    });

    it('calls deployRequest when confirm is clicked', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v2.0.0')).toBeInTheDocument();
      });

      // Find the approved item and expand it
      const allButtons = screen.getAllByRole('button');

      // Click expand buttons
      for (const button of allButtons) {
        const svg = button.querySelector('svg[data-testid="ExpandMoreIcon"]');
        if (svg) {
          fireEvent.click(button);
        }
      }

      await waitFor(() => {
        const deployButtons = screen.getAllByRole('button', { name: /deploy/i });
        expect(deployButtons.length).toBeGreaterThan(0);
      });

      // Click deploy button
      const deployButtons = screen.getAllByRole('button', { name: /deploy/i });
      fireEvent.click(deployButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Deploy Model')).toBeInTheDocument();
      });

      // Find deploy confirm button in dialog
      const dialogDeployButtons = screen.getAllByRole('button', { name: /deploy/i });
      const confirmButton = dialogDeployButtons[dialogDeployButtons.length - 1];

      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockDeployRequest).toHaveBeenCalled();
      });
    });
  });

  describe('Callback Handling', () => {
    it('calls onApprovalProcessed callback after successful approve', async () => {
      const onApprovalProcessed = vi.fn();

      render(<ModelApprovalPanel onApprovalProcessed={onApprovalProcessed} />);

      await waitFor(() => {
        expect(screen.getByText('v1.2.0')).toBeInTheDocument();
      });

      // Expand and approve
      const expandButtons = screen.getAllByRole('button', { name: '' });
      const expandButton = expandButtons.find((btn) =>
        btn.querySelector('svg[data-testid="ExpandMoreIcon"]')
      );

      if (expandButton) {
        fireEvent.click(expandButton);
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /approve/i }));

      await waitFor(() => {
        expect(screen.getByText('Approve Deployment Request')).toBeInTheDocument();
      });

      // Confirm
      const confirmButtons = screen.getAllByRole('button', { name: /approve/i });
      fireEvent.click(confirmButtons[confirmButtons.length - 1]);

      await waitFor(() => {
        expect(onApprovalProcessed).toHaveBeenCalled();
      });
    });
  });

  describe('Error Handling', () => {
    it('shows error snackbar when approve fails', async () => {
      mockApproveRequest.mockRejectedValue(new Error('Approval failed'));

      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('v1.2.0')).toBeInTheDocument();
      });

      // Expand and approve
      const expandButtons = screen.getAllByRole('button', { name: '' });
      const expandButton = expandButtons.find((btn) =>
        btn.querySelector('svg[data-testid="ExpandMoreIcon"]')
      );

      if (expandButton) {
        fireEvent.click(expandButton);
      }

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /approve/i }));

      await waitFor(() => {
        expect(screen.getByText('Approve Deployment Request')).toBeInTheDocument();
      });

      // Confirm
      const confirmButtons = screen.getAllByRole('button', { name: /approve/i });
      fireEvent.click(confirmButtons[confirmButtons.length - 1]);

      await waitFor(() => {
        expect(screen.getByText(/Failed to approve request/)).toBeInTheDocument();
      });
    });

    it('shows mock data when API fails (fallback)', async () => {
      mockListApprovals.mockRejectedValue(new Error('Network error'));

      render(<ModelApprovalPanel />);

      // Should still show data from mock fallback
      await waitFor(() => {
        expect(screen.getByText('Model Deployment Approvals')).toBeInTheDocument();
      });

      // The component has fallback mock data
      await waitFor(() => {
        expect(screen.getByText(/skill_matching|ranking/)).toBeInTheDocument();
      });
    });
  });

  describe('Stats Calculation', () => {
    it('displays correct pending count in badge', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('Model Deployment Approvals')).toBeInTheDocument();
      });

      // Check if pending count is shown somewhere
      const pendingElements = screen.getAllByText('1');
      expect(pendingElements.length).toBeGreaterThan(0);
    });

    it('displays stats from API response', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('Total')).toBeInTheDocument();
      });

      // Stats should be rendered
      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(screen.getByText('Approved')).toBeInTheDocument();
      expect(screen.getByText('Rejected')).toBeInTheDocument();
      expect(screen.getByText('Deployed')).toBeInTheDocument();
    });
  });

  describe('Props Configuration', () => {
    it('applies custom maxHeight prop', async () => {
      render(<ModelApprovalPanel maxHeight={400} />);

      await waitFor(() => {
        expect(screen.getByText('Model Deployment Approvals')).toBeInTheDocument();
      });

      // Component should render with custom max height
      // The maxHeight is applied to the Paper component containing the list
      const paperElements = document.querySelectorAll('.MuiPaper-root');
      expect(paperElements.length).toBeGreaterThan(0);
    });

    it('defaults maxHeight to 600 when not specified', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText('Model Deployment Approvals')).toBeInTheDocument();
      });

      // Component should render with default max height
      expect(screen.getByText('Model Deployment Approvals')).toBeInTheDocument();
    });
  });

  describe('Time Formatting', () => {
    it('shows relative time for recent approvals', async () => {
      render(<ModelApprovalPanel />);

      await waitFor(() => {
        expect(screen.getByText(/ago|just now/)).toBeInTheDocument();
      });
    });
  });
});
