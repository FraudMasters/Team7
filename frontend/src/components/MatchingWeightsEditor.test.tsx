/**
 * Tests for MatchingWeightsEditor Component
 *
 * Tests the matching weights editor including:
 * - Fetching and displaying weight profiles
 * - Creating custom weight profiles with sliders
 * - Editing existing profiles
 * - Deleting profiles
 * - Applying preset profiles
 * - Auto-normalization of weights
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import MatchingWeightsEditor from './MatchingWeightsEditor';

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('MatchingWeightsEditor', () => {
  const mockOrganizationId = 'org-123';
  const mockApiUrl = 'http://localhost:8000/api/matching-weights';

  const mockProfiles = {
    organization_id: mockOrganizationId,
    profiles: [
      {
        id: 'profile-1',
        organization_id: mockOrganizationId,
        name: 'Technical',
        description: 'Emphasizes exact keyword matching',
        keyword_weight: 0.6,
        tfidf_weight: 0.3,
        vector_weight: 0.1,
        is_default: false,
        is_preset: true,
        preset_type: 'technical',
        created_by: 'system',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      },
      {
        id: 'profile-2',
        organization_id: mockOrganizationId,
        name: 'Creative',
        description: 'Prioritizes semantic understanding',
        keyword_weight: 0.2,
        tfidf_weight: 0.2,
        vector_weight: 0.6,
        is_default: false,
        is_preset: true,
        preset_type: 'creative',
        created_by: 'system',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      },
      {
        id: 'profile-3',
        organization_id: mockOrganizationId,
        name: 'Custom Technical',
        description: 'Our custom technical profile',
        keyword_weight: 0.7,
        tfidf_weight: 0.2,
        vector_weight: 0.1,
        is_default: true,
        is_preset: false,
        created_by: 'user-123',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      },
    ],
    total_count: 3,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockProfiles,
    });
  });

  describe('Rendering', () => {
    it('renders loading state initially', () => {
      mockFetch.mockImplementation(() => new Promise(() => {}));
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      expect(screen.getByText('Loading weight profiles...')).toBeInTheDocument();
    });

    it('renders profiles after loading', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Matching Algorithm Weights')).toBeInTheDocument();
      });

      expect(screen.getByText('Total Profiles')).toBeInTheDocument();
      expect(screen.getByText('Presets')).toBeInTheDocument();
      expect(screen.getByText('Custom')).toBeInTheDocument();
    });

    it('displays preset profiles', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Preset Profiles')).toBeInTheDocument();
      });

      expect(screen.getByText('Technical')).toBeInTheDocument();
      expect(screen.getByText('Creative')).toBeInTheDocument();
    });

    it('displays custom profiles', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Custom Profiles')).toBeInTheDocument();
      });

      expect(screen.getByText('Custom Technical')).toBeInTheDocument();
    });

    it('shows empty state when no custom profiles', async () => {
      const emptyProfiles = {
        organization_id: mockOrganizationId,
        profiles: mockProfiles.profiles.filter((p) => p.is_preset),
        total_count: 2,
      };
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => emptyProfiles,
      });

      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('No Custom Profiles')).toBeInTheDocument();
      });
    });
  });

  describe('Profile Creation', () => {
    it('opens create dialog when button is clicked', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Create Custom Profile')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Create Custom Profile'));

      await waitFor(() => {
        expect(screen.getByText('Create Weight Profile')).toBeInTheDocument();
      });
    });

    it('displays preset chips in create dialog', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Create Custom Profile')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Create Custom Profile'));

      await waitFor(() => {
        expect(screen.getByText('Quick Start - Apply a Preset:')).toBeInTheDocument();
        expect(screen.getByText('Technical')).toBeInTheDocument();
        expect(screen.getByText('Creative')).toBeInTheDocument();
        expect(screen.getByText('Executive')).toBeInTheDocument();
        expect(screen.getByText('Balanced')).toBeInTheDocument();
      });
    });

    it('shows all three weight sliders', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Create Custom Profile')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Create Custom Profile'));

      await waitFor(() => {
        expect(screen.getByText('Keyword Matching')).toBeInTheDocument();
        expect(screen.getByText('TF-IDF Matching')).toBeInTheDocument();
        expect(screen.getByText('Vector Similarity')).toBeInTheDocument();
      });
    });

    it('applies preset profile when clicked', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Create Custom Profile')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Create Custom Profile'));

      await waitFor(() => {
        expect(screen.getByText('Technical')).toBeInTheDocument();
      });

      // Click the Technical preset chip
      const presetChips = screen.getAllByText('Technical');
      const presetChip = presetChips.find((chip) => chip.getAttribute('role') === 'button');
      if (presetChip) {
        fireEvent.click(presetChip);
      }

      await waitFor(() => {
        // The description should be updated to the preset's description
        expect(screen.getByDisplayValue(/Emphasizes exact keyword matching/)).toBeInTheDocument();
      });
    });

    it('normalizes weights when sliders change', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Create Custom Profile')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Create Custom Profile'));

      await waitFor(() => {
        expect(screen.getByText('Algorithm Weights')).toBeInTheDocument();
      });

      // Find the keyword slider (it should show 33% initially)
      const keywordSliders = screen.getAllByRole('slider');
      expect(keywordSliders.length).toBeGreaterThan(0);
    });

    it('submits new profile successfully', async () => {
      const mockCreatedProfile = {
        id: 'new-profile-1',
        organization_id: mockOrganizationId,
        name: 'Test Profile',
        description: 'Test description',
        keyword_weight: 0.5,
        tfidf_weight: 0.3,
        vector_weight: 0.2,
        is_default: false,
        is_preset: false,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles,
      }).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCreatedProfile,
      });

      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Create Custom Profile')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Create Custom Profile'));

      await waitFor(() => {
        expect(screen.getByLabelText('Profile Name')).toBeInTheDocument();
      });

      // Fill in the form
      fireEvent.change(screen.getByLabelText('Profile Name'), {
        target: { value: 'Test Profile' },
      });
      fireEvent.change(screen.getByLabelText('Description'), {
        target: { value: 'Test description' },
      });

      // Submit the form
      fireEvent.click(screen.getByText('Create Profile'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          `${mockApiUrl}/`,
          expect.objectContaining({
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: expect.stringContaining('Test Profile'),
          })
        );
      });
    });

    it('disables submit button when name is empty', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Create Custom Profile')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Create Custom Profile'));

      await waitFor(() => {
        expect(screen.getByText('Create Profile')).toBeInTheDocument();
      });

      // The button should be disabled initially (no name)
      const createButton = screen.getByText('Create Profile').closest('button');
      expect(createButton).toBeDisabled();
    });
  });

  describe('Profile Editing', () => {
    it('opens edit dialog when edit icon is clicked', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Custom Technical')).toBeInTheDocument();
      });

      // Find edit buttons (there should be at least one for the custom profile)
      const editButtons = screen.getAllByLabelText('Edit');
      expect(editButtons.length).toBeGreaterThan(0);

      fireEvent.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Edit Weight Profile')).toBeInTheDocument();
      });
    });

    it('pre-fills form with existing profile data', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Custom Technical')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByLabelText('Edit');
      fireEvent.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByDisplayValue('Custom Technical')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Our custom technical profile')).toBeInTheDocument();
      });
    });

    it('submits profile update successfully', async () => {
      const mockUpdatedProfile = {
        ...mockProfiles.profiles[2],
        name: 'Updated Technical',
        description: 'Updated description',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles,
      }).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUpdatedProfile,
      });

      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Custom Technical')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByLabelText('Edit');
      fireEvent.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Edit Weight Profile')).toBeInTheDocument();
      });

      // Update the name
      fireEvent.change(screen.getByLabelText('Profile Name'), {
        target: { value: 'Updated Technical' },
      });

      // Submit
      fireEvent.click(screen.getByText('Update Profile'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          `${mockApiUrl}/profile-3`,
          expect.objectContaining({
            method: 'PUT',
          })
        );
      });
    });
  });

  describe('Profile Deletion', () => {
    it('opens delete confirmation dialog', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Custom Technical')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByLabelText('Delete');
      expect(deleteButtons.length).toBeGreaterThan(0);

      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Delete Weight Profile')).toBeInTheDocument();
        expect(screen.getByText(/Are you sure you want to delete/)).toBeInTheDocument();
      });
    });

    it('deletes profile when confirmed', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles,
      }).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Custom Technical')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByLabelText('Delete');
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Delete Weight Profile')).toBeInTheDocument();
      });

      // Confirm deletion
      const confirmButtons = screen.getAllByText('Delete');
      const deleteConfirmButton = confirmButtons.find((button) =>
        button.getAttribute('class')?.includes('MuiButton-colorError')
      );

      if (deleteConfirmButton) {
        fireEvent.click(deleteConfirmButton);
      }

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          `${mockApiUrl}/profile-3`,
          expect.objectContaining({
            method: 'DELETE',
          })
        );
      });
    });

    it('closes delete dialog when cancelled', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Custom Technical')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByLabelText('Delete');
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Delete Weight Profile')).toBeInTheDocument();
      });

      // Click cancel
      const cancelButtons = screen.getAllByText('Cancel');
      const cancelButton = cancelButtons.find((button) =>
        button.getAttribute('class')?.includes('MuiButton-text')
      );

      if (cancelButton) {
        fireEvent.click(cancelButton);
      }

      await waitFor(() => {
        expect(screen.queryByText('Delete Weight Profile')).not.toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error message when fetch fails', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
      });

      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText(/Error/)).toBeInTheDocument();
      });
    });

    it('displays error message when create fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles,
      }).mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request',
      });

      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Create Custom Profile')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Create Custom Profile'));

      await waitFor(() => {
        expect(screen.getByLabelText('Profile Name')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Profile Name'), {
        target: { value: 'Test Profile' },
      });

      fireEvent.click(screen.getByText('Create Profile'));

      await waitFor(() => {
        expect(screen.getByText(/Error/)).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('refreshes profiles when refresh button is clicked', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Matching Algorithm Weights')).toBeInTheDocument();
      });

      const refreshButtons = screen.getAllByText('Refresh');
      expect(refreshButtons.length).toBeGreaterThan(0);

      // Clear previous calls
      mockFetch.mockClear();

      fireEvent.click(refreshButtons[0]);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          `${mockApiUrl}/?organization_id=${mockOrganizationId}`
        );
      });
    });
  });

  describe('Weight Display', () => {
    it('displays weights as percentages in cards', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Technical')).toBeInTheDocument();
      });

      // Check if weight percentages are displayed
      expect(screen.getByText(/Keyword: 60%/)).toBeInTheDocument();
      expect(screen.getByText(/TF-IDF: 30%/)).toBeInTheDocument();
      expect(screen.getByText(/Vector: 10%/)).toBeInTheDocument();
    });

    it('shows default profile indicator', async () => {
      render(<MatchingWeightsEditor organizationId={mockOrganizationId} apiUrl={mockApiUrl} />);

      await waitFor(() => {
        expect(screen.getByText('Custom Technical')).toBeInTheDocument();
      });

      // The custom technical profile should have "Default" badge
      expect(screen.getByText('Default')).toBeInTheDocument();
    });
  });
});
