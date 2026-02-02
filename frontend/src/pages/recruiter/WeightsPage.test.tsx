/**
 * Tests for WeightsPage Component
 *
 * Tests the matching weights customization page including:
 * - Weight sliders and validation
 * - Loading and error states
 * - Preset application (technical, creative, executive, balanced)
 * - Profile saving functionality
 * - Weight normalization
 * - Tab navigation (Presets, Custom, Saved Profiles)
 * - Progress bar visualization
 * - Success and error alerts
 * - Dialog for saving profiles
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import WeightsPage from './WeightsPage';

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: any) => {
      if (options?.defaultValue) return options.defaultValue;
      return key;
    },
  }),
}));

// Mock API client
const mockListWeightProfiles = vi.fn();
const mockGetPresetProfiles = vi.fn();
const mockCreateWeightProfile = vi.fn();

vi.mock('@/api/client', () => ({
  apiClient: {
    listWeightProfiles: mockListWeightProfiles,
    getPresetProfiles: mockGetPresetProfiles,
    createWeightProfile: mockCreateWeightProfile,
  },
}));

// Mock WeightSliderCardStack component
vi.mock('@/components/WeightSliderCard', () => ({
  WeightSliderCardStack: ({ weights, onWeightChange, disabled }: any) => (
    <div data-testid="weight-sliders">
      <button
        onClick={() => onWeightChange('keyword', weights.keyword + 5)}
        disabled={disabled}
      >
        Increase Keyword
      </button>
      <button
        onClick={() => onWeightChange('tfidf', weights.tfidf + 5)}
        disabled={disabled}
      >
        Increase TF-IDF
      </button>
      <button
        onClick={() => onWeightChange('vector', weights.vector + 5)}
        disabled={disabled}
      >
        Increase Vector
      </button>
      <div>Keyword: {weights.keyword}%</div>
      <div>TF-IDF: {weights.tfidf}%</div>
      <div>Vector: {weights.vector}%</div>
    </div>
  ),
}));

describe('WeightsPage', () => {
  const mockProfiles = [
    {
      id: 'profile-1',
      name: 'My Technical Profile',
      description: 'For technical roles',
      weights_percentage: { keyword: 60, tfidf: 25, vector: 15 },
      is_preset: false,
    },
    {
      id: 'profile-2',
      name: 'Executive Role',
      description: 'For executive positions',
      weights_percentage: { keyword: 33, tfidf: 34, vector: 33 },
      is_preset: false,
    },
  ];

  const mockPresets = [
    {
      id: 'preset-1',
      name: 'Technical',
      weights_percentage: { keyword: 60, tfidf: 25, vector: 15 },
      description: 'Best for technical roles',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    mockListWeightProfiles.mockResolvedValue({ profiles: mockProfiles });
    mockGetPresetProfiles.mockResolvedValue({ presets: mockPresets });
    mockCreateWeightProfile.mockResolvedValue({ success: true });
  });

  describe('Component Rendering', () => {
    it('should render the page with header', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Matching Algorithm Weights')).toBeInTheDocument();
      });
    });

    it('should display subtitle', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(
          screen.getByText(/Customize how the matching algorithm scores candidates/)
        ).toBeInTheDocument();
      });
    });

    it('should render current weight distribution section', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weight Distribution')).toBeInTheDocument();
      });
    });

    it('should display total weight chip', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Total Weight')).toBeInTheDocument();
        const chip = screen.getByText('100%');
        expect(chip).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should render loading state initially', () => {
      mockListWeightProfiles.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ profiles: [] }), 100))
      );

      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      expect(document.querySelector('.MuiCircularProgress-root')).toBeInTheDocument();
    });

    it('should hide loading state after data loads', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(document.querySelector('.MuiCircularProgress-root')).not.toBeInTheDocument();
      });
    });
  });

  describe('Weight Validation', () => {
    it('should show validation warning when weights do not sum to 100', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Total Weight')).toBeInTheDocument();
      });

      // Increase keyword to make total > 100
      fireEvent.click(screen.getByText('Increase Keyword'));

      await waitFor(() => {
        expect(screen.getByText(/Weights must sum to 100%/)).toBeInTheDocument();
      });
    });

    it('should display normalize button when weights are invalid', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Total Weight')).toBeInTheDocument();
      });

      // Make weights invalid
      fireEvent.click(screen.getByText('Increase Keyword'));

      await waitFor(() => {
        expect(screen.getByText('Normalize to 100%')).toBeInTheDocument();
      });
    });

    it('should show success chip when weights sum to 100', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const chip = screen.getByText('100%');
        expect(chip).toBeInTheDocument();
        expect(chip).toHaveClass('MuiChip-colorSuccess');
      });
    });

    it('should show warning chip when weights do not sum to 100', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Total Weight')).toBeInTheDocument();
      });

      // Make weights invalid
      fireEvent.click(screen.getByText('Increase Keyword'));

      await waitFor(() => {
        const chip = screen.getByText(/%/);
        expect(chip).toHaveClass('MuiChip-colorWarning');
      });
    });
  });

  describe('Weight Normalization', () => {
    it('should normalize weights when normalize button is clicked', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Total Weight')).toBeInTheDocument();
      });

      // Make weights invalid (increase keyword)
      fireEvent.click(screen.getByText('Increase Keyword'));

      await waitFor(() => {
        expect(screen.getByText('Normalize to 100%')).toBeInTheDocument();
      });

      // Click normalize
      fireEvent.click(screen.getByText('Normalize to 100%'));

      await waitFor(() => {
        // After normalization, should return to 100%
        expect(screen.getByText('100%')).toBeInTheDocument();
      });
    });

    it('should disable normalize button when weights are valid', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const normalizeButton = screen.queryByText('Normalize');
        expect(normalizeButton).not.toBeInTheDocument();
      });
    });
  });

  describe('Tab Navigation', () => {
    it('should display all three tabs', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
        expect(screen.getByText('Custom')).toBeInTheDocument();
        expect(screen.getByText('Saved Profiles')).toBeInTheDocument();
      });
    });

    it('should switch to Custom tab when clicked', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom'));

      await waitFor(() => {
        expect(screen.getByTestId('weight-sliders')).toBeInTheDocument();
      });
    });

    it('should switch to Saved Profiles tab when clicked', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Saved Profiles'));

      await waitFor(() => {
        expect(screen.getByText('My Technical Profile')).toBeInTheDocument();
        expect(screen.getByText('Executive Role')).toBeInTheDocument();
      });
    });

    it('should disable Saved Profiles tab when no profiles exist', async () => {
      mockListWeightProfiles.mockResolvedValue({ profiles: [] });

      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const savedProfilesTab = screen.getByText('Saved Profiles');
        expect(savedProfilesTab).toHaveClass('Mui-disabled');
      });
    });
  });

  describe('Preset Application', () => {
    it('should display preset cards', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Technical')).toBeInTheDocument();
        expect(screen.getByText('Creative')).toBeInTheDocument();
        expect(screen.getByText('Executive')).toBeInTheDocument();
        expect(screen.getByText('Balanced')).toBeInTheDocument();
      });
    });

    it('should apply technical preset when clicked', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Technical')).toBeInTheDocument();
      });

      // Click on Technical preset card
      const technicalCard = screen
        .getAllByText('Technical')
        .find((el) => el.textContent === 'Technical');
      if (technicalCard) {
        fireEvent.click(technicalCard);

        await waitFor(() => {
          expect(screen.getByText('Keyword: 60%')).toBeInTheDocument();
          expect(screen.getByText('TF-IDF: 25%')).toBeInTheDocument();
          expect(screen.getByText('Vector: 15%')).toBeInTheDocument();
        });
      }
    });

    it('should apply creative preset when clicked', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Creative')).toBeInTheDocument();
      });

      // Click on Creative preset card
      const creativeCard = screen
        .getAllByText('Creative')
        .find((el) => el.textContent === 'Creative');
      if (creativeCard) {
        fireEvent.click(creativeCard);

        await waitFor(() => {
          expect(screen.getByText('Keyword: 20%')).toBeInTheDocument();
          expect(screen.getByText('TF-IDF: 25%')).toBeInTheDocument();
          expect(screen.getByText('Vector: 55%')).toBeInTheDocument();
        });
      }
    });
  });

  describe('Profile Saving', () => {
    it('should open save dialog when Save as Profile button is clicked', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      // Switch to Custom tab
      fireEvent.click(screen.getByText('Custom'));

      await waitFor(() => {
        expect(screen.getByText('Save as Profile')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save as Profile'));

      await waitFor(() => {
        expect(screen.getByText('Save as Custom Profile')).toBeInTheDocument();
      });
    });

    it('should display profile name and description fields in dialog', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom'));
      fireEvent.click(screen.getByText('Save as Profile'));

      await waitFor(() => {
        expect(screen.getByText('Profile Name')).toBeInTheDocument();
        expect(screen.getByText('Description (Optional)')).toBeInTheDocument();
      });
    });

    it('should disable save button when profile name is empty', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom'));
      fireEvent.click(screen.getByText('Save as Profile'));

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: 'Save' });
        expect(saveButton).toBeDisabled();
      });
    });

    it('should enable save button when profile name is entered', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom'));
      fireEvent.click(screen.getByText('Save as Profile'));

      await waitFor(() => {
        const nameInput = screen.getByPlaceholderText('e.g., My Technical Role Profile');
        fireEvent.change(nameInput, { target: { value: 'My Profile' } });
      });

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: 'Save' });
        expect(saveButton).not.toBeDisabled();
      });
    });

    it('should call API with correct data when saving profile', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom'));
      fireEvent.click(screen.getByText('Save as Profile'));

      await waitFor(() => {
        const nameInput = screen.getByPlaceholderText('e.g., My Technical Role Profile');
        fireEvent.change(nameInput, { target: { value: 'Test Profile' } });
      });

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: 'Save' });
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(mockCreateWeightProfile).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Test Profile',
            keyword_weight: expect.any(Number),
            tfidf_weight: expect.any(Number),
            vector_weight: expect.any(Number),
          })
        );
      });
    });

    it('should close dialog after successful save', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom'));
      fireEvent.click(screen.getByText('Save as Profile'));

      await waitFor(() => {
        const nameInput = screen.getByPlaceholderText('e.g., My Technical Role Profile');
        fireEvent.change(nameInput, { target: { value: 'Test Profile' } });
      });

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: 'Save' });
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(screen.queryByText('Save as Custom Profile')).not.toBeInTheDocument();
      });
    });

    it('should show success alert after successful save', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom'));
      fireEvent.click(screen.getByText('Save as Profile'));

      await waitFor(() => {
        const nameInput = screen.getByPlaceholderText('e.g., My Technical Role Profile');
        fireEvent.change(nameInput, { target: { value: 'Test Profile' } });
      });

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: 'Save' });
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Weights saved successfully!')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error alert when API call fails', async () => {
      mockListWeightProfiles.mockRejectedValue(new Error('API Error'));

      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('API Error')).toBeInTheDocument();
      });
    });

    it('should allow closing error alert', async () => {
      mockListWeightProfiles.mockRejectedValue(new Error('Test Error'));

      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Error')).toBeInTheDocument();
      });

      const closeButton = screen.getByRole('button', { name: /close/i });
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText('Test Error')).not.toBeInTheDocument();
      });
    });

    it('should display error when save fails', async () => {
      mockCreateWeightProfile.mockRejectedValue(new Error('Save failed'));

      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom'));
      fireEvent.click(screen.getByText('Save as Profile'));

      await waitFor(() => {
        const nameInput = screen.getByPlaceholderText('e.g., My Technical Role Profile');
        fireEvent.change(nameInput, { target: { value: 'Test Profile' } });
      });

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: 'Save' });
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Save failed')).toBeInTheDocument();
      });
    });
  });

  describe('Saved Profiles Tab', () => {
    it('should display saved profiles', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Saved Profiles'));

      await waitFor(() => {
        expect(screen.getByText('My Technical Profile')).toBeInTheDocument();
        expect(screen.getByText('Executive Role')).toBeInTheDocument();
      });
    });

    it('should load profile when clicked', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Saved Profiles'));

      await waitFor(() => {
        const profileCard = screen.getByText('My Technical Profile').closest('.MuiCard-root');
        if (profileCard) {
          fireEvent.click(profileCard);
        }
      });

      // The weights should update to the profile's weights
      await waitFor(() => {
        expect(screen.getByText('Keyword: 60%')).toBeInTheDocument();
        expect(screen.getByText('TF-IDF: 25%')).toBeInTheDocument();
        expect(screen.getByText('Vector: 15%')).toBeInTheDocument();
      });
    });

    it('should display profile descriptions', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Saved Profiles'));

      await waitFor(() => {
        expect(screen.getByText('For technical roles')).toBeInTheDocument();
        expect(screen.getByText('For executive positions')).toBeInTheDocument();
      });
    });
  });

  describe('Progress Bar Visualization', () => {
    it('should display progress bars for each weight', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const progressBars = document.querySelectorAll('.MuiLinearProgress-root');
        expect(progressBars.length).toBe(3);
      });
    });

    it('should display correct percentages for each weight', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Keyword: 50%/)).toBeInTheDocument();
        expect(screen.getByText(/TF-IDF: 30%/)).toBeInTheDocument();
        expect(screen.getByText(/Vector: 20%/)).toBeInTheDocument();
      });
    });
  });

  describe('Explanation Section', () => {
    it('should display explanation section', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Understanding the Weights')).toBeInTheDocument();
      });
    });

    it('should display keyword matching explanation', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Keyword Matching')).toBeInTheDocument();
        expect(
          screen.getByText(/Direct skill matching including synonyms/)
        ).toBeInTheDocument();
      });
    });

    it('should display TF-IDF matching explanation', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('TF-IDF Matching')).toBeInTheDocument();
        expect(
          screen.getByText(/Weighted scoring based on keyword importance/)
        ).toBeInTheDocument();
      });
    });

    it('should display vector similarity explanation', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Vector Similarity')).toBeInTheDocument();
        expect(
          screen.getByText(/Semantic similarity using AI embeddings/)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Layout and Structure', () => {
    it('should use Container component', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const containers = document.querySelectorAll('.MuiContainer-root');
        expect(containers.length).toBeGreaterThan(0);
      });
    });

    it('should use Stack layout', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const stacks = document.querySelectorAll('.MuiStack-root');
        expect(stacks.length).toBeGreaterThan(0);
      });
    });

    it('should use Paper components', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const papers = document.querySelectorAll('.MuiPaper-root');
        expect(papers.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle very long profile names', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom'));
      fireEvent.click(screen.getByText('Save as Profile'));

      const longName = 'a'.repeat(200);
      const nameInput = screen.getByPlaceholderText('e.g., My Technical Role Profile');

      await waitFor(() => {
        fireEvent.change(nameInput, { target: { value: longName } });
        expect(nameInput).toHaveValue(longName);
      });
    });

    it('should handle special characters in profile name', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom'));
      fireEvent.click(screen.getByText('Save as Profile'));

      const specialName = 'Test Profile @#$%';
      const nameInput = screen.getByPlaceholderText('e.g., My Technical Role Profile');

      await waitFor(() => {
        fireEvent.change(nameInput, { target: { value: specialName } });
        expect(nameInput).toHaveValue(specialName);
      });
    });

    it('should handle empty profile description', async () => {
      render(
        <BrowserRouter>
          <WeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom'));
      fireEvent.click(screen.getByText('Save as Profile'));

      await waitFor(() => {
        const nameInput = screen.getByPlaceholderText('e.g., My Technical Role Profile');
        fireEvent.change(nameInput, { target: { value: 'Test' } });
      });

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: 'Save' });
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(mockCreateWeightProfile).toHaveBeenCalledWith(
          expect.objectContaining({
            description: undefined,
          })
        );
      });
    });
  });
});
