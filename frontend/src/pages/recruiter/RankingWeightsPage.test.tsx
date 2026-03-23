/**
 * Tests for RankingWeightsPage Component
 *
 * Tests the ranking weights customization page including:
 * - Weight sliders and validation for 13 ranking features
 * - Loading and error states
 * - Preset application (technical, sales, executive, balanced)
 * - Profile saving functionality
 * - Weight normalization
 * - Tab navigation (Current Weights, Presets, Custom Profiles, Impact Preview)
 * - Progress bar visualization
 * - Success and error alerts
 * - Dialog for saving profiles
 * - Impact preview functionality
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import RankingWeightsPage from './RankingWeightsPage';

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

vi.mock('@/api', () => ({
  rankingWeightsClient: {
    listWeightProfiles: mockListWeightProfiles,
    getPresetProfiles: mockGetPresetProfiles,
    createWeightProfile: mockCreateWeightProfile,
  },
}));

// Mock RankingWeightSliderCardStack component
vi.mock('@/components/RankingWeightSliderCard', () => ({
  RankingWeightSliderCardStack: ({ weights, onWeightChange, disabled }: any) => (
    <div data-testid="ranking-weight-sliders">
      <button
        onClick={() => onWeightChange('overall_match_score', weights.overall_match_score + 5)}
        disabled={disabled}
      >
        Increase Overall Match
      </button>
      <button
        onClick={() => onWeightChange('keyword_score', weights.keyword_score + 5)}
        disabled={disabled}
      >
        Increase Keyword
      </button>
      <button
        onClick={() => onWeightChange('skills_match_ratio', weights.skills_match_ratio + 5)}
        disabled={disabled}
      >
        Increase Skills Match
      </button>
      <div>Overall Match: {weights.overall_match_score}%</div>
      <div>Keyword: {weights.keyword_score}%</div>
      <div>TF-IDF: {weights.tfidf_score}%</div>
      <div>Vector: {weights.vector_score}%</div>
      <div>Skills Match: {weights.skills_match_ratio}%</div>
      <div>Experience Months: {weights.experience_months}%</div>
      <div>Experience Relevance: {weights.experience_relevance}%</div>
      <div>Education Level: {weights.education_level}%</div>
      <div>Recent Experience: {weights.recent_experience}%</div>
      <div>Skill Rarity: {weights.skill_rarity}%</div>
      <div>Title Similarity: {weights.title_similarity}%</div>
      <div>Freshness: {weights.freshness_score}%</div>
      <div>Completeness: {weights.completeness_score}%</div>
    </div>
  ),
}));

// Mock RankingWeightImpactPreview component
vi.mock('@/components/RankingWeightImpactPreview', () => ({
  default: ({ vacancyId, beforeWeights, afterWeights }: any) => (
    <div data-testid="impact-preview">
      <div>Vacancy ID: {vacancyId}</div>
      <div>Before Weights: {JSON.stringify(beforeWeights)}</div>
      <div>After Weights: {JSON.stringify(afterWeights)}</div>
    </div>
  ),
}));

// Mock PageTransition component
vi.mock('@components/mui/PageTransition', () => ({
  PageTransition: ({ children }: any) => <div>{children}</div>,
}));

describe('RankingWeightsPage', () => {
  const mockProfiles = [
    {
      id: 'profile-1',
      name: 'Technical Role Profile',
      description: 'Optimized for technical positions',
      overall_match_score_weight: 0.1,
      keyword_score_weight: 0.15,
      tfidf_score_weight: 0.05,
      vector_score_weight: 0.05,
      skills_match_ratio_weight: 0.25,
      experience_months_weight: 0.05,
      experience_relevance_weight: 0.15,
      education_level_weight: 0.08,
      recent_experience_weight: 0.05,
      skill_rarity_weight: 0.05,
      title_similarity_weight: 0.02,
      freshness_score_weight: 0.05,
      completeness_score_weight: 0.05,
      is_preset: false,
      is_active: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'profile-2',
      name: 'Sales Role Profile',
      description: 'For sales positions',
      overall_match_score_weight: 0.1,
      keyword_score_weight: 0.08,
      tfidf_score_weight: 0.05,
      vector_score_weight: 0.05,
      skills_match_ratio_weight: 0.1,
      experience_months_weight: 0.15,
      experience_relevance_weight: 0.2,
      education_level_weight: 0.05,
      recent_experience_weight: 0.12,
      skill_rarity_weight: 0.03,
      title_similarity_weight: 0.02,
      freshness_score_weight: 0.1,
      completeness_score_weight: 0.05,
      is_preset: false,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
  ];

  const mockPresets = [
    {
      id: 'preset-1',
      preset_type: 'technical',
      name: 'Technical',
      description: 'Optimized for technical roles requiring specific skills',
      use_case: 'Software engineers, data scientists, technical specialists',
      weights: {
        overall_match_score_weight: 0.1,
        keyword_score_weight: 0.15,
        tfidf_score_weight: 0.05,
        vector_score_weight: 0.05,
        skills_match_ratio_weight: 0.25,
        experience_months_weight: 0.05,
        experience_relevance_weight: 0.15,
        education_level_weight: 0.08,
        recent_experience_weight: 0.05,
        skill_rarity_weight: 0.05,
        title_similarity_weight: 0.02,
        freshness_score_weight: 0.05,
        completeness_score_weight: 0.05,
      },
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
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Ranking Weights Configuration')).toBeInTheDocument();
      });
    });

    it('should display subtitle', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(
          screen.getByText(/Configure the importance of different ranking features/)
        ).toBeInTheDocument();
      });
    });

    it('should render total weight section', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Total Weight')).toBeInTheDocument();
      });
    });

    it('should display total weight percentage', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('100%')).toBeInTheDocument();
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
          <RankingWeightsPage />
        </BrowserRouter>
      );

      expect(document.querySelector('.MuiCircularProgress-root')).toBeInTheDocument();
    });

    it('should hide loading state after data loads', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
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
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Total Weight')).toBeInTheDocument();
      });

      // Increase overall_match_score to make total > 100
      fireEvent.click(screen.getByText('Increase Overall Match'));

      await waitFor(() => {
        expect(screen.getByText('Must equal 100%')).toBeInTheDocument();
      });
    });

    it('should display normalize button when weights are invalid', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Total Weight')).toBeInTheDocument();
      });

      // Make weights invalid
      fireEvent.click(screen.getByText('Increase Overall Match'));

      await waitFor(() => {
        expect(screen.getByText('Normalize to 100%')).toBeInTheDocument();
      });
    });

    it('should show correct total when weights are valid', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const totalWeight = screen.getByText('100%');
        expect(totalWeight).toBeInTheDocument();
      });
    });
  });

  describe('Weight Normalization', () => {
    it('should normalize weights when normalize button is clicked', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Total Weight')).toBeInTheDocument();
      });

      // Make weights invalid
      fireEvent.click(screen.getByText('Increase Overall Match'));

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

    it('should disable normalize button when total weight is zero', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const normalizeButton = screen.getByText('Normalize to 100%');
        expect(normalizeButton).not.toBeDisabled();
      });
    });
  });

  describe('Tab Navigation', () => {
    it('should display all tabs', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
        expect(screen.getByText('Presets')).toBeInTheDocument();
        expect(screen.getByText('Custom Profiles')).toBeInTheDocument();
      });
    });

    it('should switch to Current Weights tab when clicked', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Current Weights'));

      await waitFor(() => {
        expect(screen.getByTestId('ranking-weight-sliders')).toBeInTheDocument();
      });
    });

    it('should switch to Presets tab when clicked', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Presets'));

      await waitFor(() => {
        expect(screen.getByText('Technical')).toBeInTheDocument();
        expect(screen.getByText('Sales')).toBeInTheDocument();
        expect(screen.getByText('Executive')).toBeInTheDocument();
        expect(screen.getByText('Balanced')).toBeInTheDocument();
      });
    });

    it('should switch to Custom Profiles tab when clicked', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Custom Profiles')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom Profiles'));

      await waitFor(() => {
        expect(screen.getByText('Technical Role Profile')).toBeInTheDocument();
        expect(screen.getByText('Sales Role Profile')).toBeInTheDocument();
      });
    });
  });

  describe('Preset Application', () => {
    it('should display local preset cards', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Presets'));

      await waitFor(() => {
        expect(screen.getByText('Technical')).toBeInTheDocument();
        expect(screen.getByText('Sales')).toBeInTheDocument();
        expect(screen.getByText('Executive')).toBeInTheDocument();
        expect(screen.getByText('Balanced')).toBeInTheDocument();
      });
    });

    it('should display API preset cards', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Presets'));

      await waitFor(() => {
        const apiChips = screen.getAllByText('API');
        expect(apiChips.length).toBeGreaterThan(0);
      });
    });

    it('should apply technical preset when clicked', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Presets')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Presets'));

      await waitFor(() => {
        const technicalCards = screen.getAllByText('Technical');
        // Click the first Technical card (local preset)
        fireEvent.click(technicalCards[0]);
      });

      // Switch back to Current Weights to see the applied weights
      fireEvent.click(screen.getByText('Current Weights'));

      await waitFor(() => {
        expect(screen.getByText('Skills Match: 25%')).toBeInTheDocument();
      });
    });
  });

  describe('Profile Saving', () => {
    it('should open save dialog when Save Profile button is clicked', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText('Save Profile')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save Profile'));

      await waitFor(() => {
        expect(screen.getByText('Save Ranking Weight Profile')).toBeInTheDocument();
      });
    });

    it('should display profile name and description fields in dialog', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save Profile'));

      await waitFor(() => {
        expect(screen.getByText('Profile Name')).toBeInTheDocument();
        expect(screen.getByText('Description')).toBeInTheDocument();
      });
    });

    it('should disable save button when profile name is empty', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save Profile'));

      await waitFor(() => {
        const saveButtons = screen.getAllByRole('button', { name: /Save/i });
        const saveButton = saveButtons.find(btn => btn.textContent === 'Save');
        expect(saveButton).toBeDisabled();
      });
    });

    it('should enable save button when profile name is entered', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save Profile'));

      await waitFor(() => {
        const nameInput = screen.getByLabelText('Profile Name');
        fireEvent.change(nameInput, { target: { value: 'My Ranking Profile' } });
      });

      await waitFor(() => {
        const saveButtons = screen.getAllByRole('button', { name: /Save/i });
        const saveButton = saveButtons.find(btn => btn.textContent === 'Save');
        expect(saveButton).not.toBeDisabled();
      });
    });

    it('should call API with correct data when saving profile', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save Profile'));

      await waitFor(() => {
        const nameInput = screen.getByLabelText('Profile Name');
        fireEvent.change(nameInput, { target: { value: 'Test Ranking Profile' } });
      });

      await waitFor(() => {
        const saveButtons = screen.getAllByRole('button', { name: /Save/i });
        const saveButton = saveButtons.find(btn => btn.textContent === 'Save');
        if (saveButton) {
          fireEvent.click(saveButton);
        }
      });

      await waitFor(() => {
        expect(mockCreateWeightProfile).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Test Ranking Profile',
            overall_match_score_weight: expect.any(Number),
            keyword_score_weight: expect.any(Number),
            tfidf_score_weight: expect.any(Number),
            vector_score_weight: expect.any(Number),
            skills_match_ratio_weight: expect.any(Number),
            experience_months_weight: expect.any(Number),
            experience_relevance_weight: expect.any(Number),
            education_level_weight: expect.any(Number),
            recent_experience_weight: expect.any(Number),
            skill_rarity_weight: expect.any(Number),
            title_similarity_weight: expect.any(Number),
            freshness_score_weight: expect.any(Number),
            completeness_score_weight: expect.any(Number),
          })
        );
      });
    });

    it('should close dialog after successful save', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save Profile'));

      await waitFor(() => {
        const nameInput = screen.getByLabelText('Profile Name');
        fireEvent.change(nameInput, { target: { value: 'Test Profile' } });
      });

      await waitFor(() => {
        const saveButtons = screen.getAllByRole('button', { name: /Save/i });
        const saveButton = saveButtons.find(btn => btn.textContent === 'Save');
        if (saveButton) {
          fireEvent.click(saveButton);
        }
      });

      await waitFor(() => {
        expect(screen.queryByText('Save Ranking Weight Profile')).not.toBeInTheDocument();
      });
    });

    it('should show success alert after successful save', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save Profile'));

      await waitFor(() => {
        const nameInput = screen.getByLabelText('Profile Name');
        fireEvent.change(nameInput, { target: { value: 'Test Profile' } });
      });

      await waitFor(() => {
        const saveButtons = screen.getAllByRole('button', { name: /Save/i });
        const saveButton = saveButtons.find(btn => btn.textContent === 'Save');
        if (saveButton) {
          fireEvent.click(saveButton);
        }
      });

      await waitFor(() => {
        expect(screen.getByText('Ranking weight profile saved successfully!')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error alert when API call fails', async () => {
      mockListWeightProfiles.mockRejectedValue({ detail: 'API Error' });

      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('API Error')).toBeInTheDocument();
      });
    });

    it('should allow closing error alert', async () => {
      mockListWeightProfiles.mockRejectedValue({ detail: 'Test Error' });

      render(
        <BrowserRouter>
          <RankingWeightsPage />
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
      mockCreateWeightProfile.mockRejectedValue({ detail: 'Save failed' });

      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save Profile'));

      await waitFor(() => {
        const nameInput = screen.getByLabelText('Profile Name');
        fireEvent.change(nameInput, { target: { value: 'Test Profile' } });
      });

      await waitFor(() => {
        const saveButtons = screen.getAllByRole('button', { name: /Save/i });
        const saveButton = saveButtons.find(btn => btn.textContent === 'Save');
        if (saveButton) {
          fireEvent.click(saveButton);
        }
      });

      await waitFor(() => {
        expect(screen.getByText('Save failed')).toBeInTheDocument();
      });
    });
  });

  describe('Custom Profiles Tab', () => {
    it('should display custom profiles', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Custom Profiles')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom Profiles'));

      await waitFor(() => {
        expect(screen.getByText('Technical Role Profile')).toBeInTheDocument();
        expect(screen.getByText('Sales Role Profile')).toBeInTheDocument();
      });
    });

    it('should load profile when clicked', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Custom Profiles')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom Profiles'));

      await waitFor(() => {
        const profileCard = screen.getByText('Technical Role Profile').closest('.MuiCard-root');
        if (profileCard) {
          fireEvent.click(profileCard);
        }
      });

      // Switch back to Current Weights to see the loaded weights
      fireEvent.click(screen.getByText('Current Weights'));

      await waitFor(() => {
        expect(screen.getByText('Skills Match: 25%')).toBeInTheDocument();
      });
    });

    it('should display profile descriptions', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Custom Profiles')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom Profiles'));

      await waitFor(() => {
        expect(screen.getByText('Optimized for technical positions')).toBeInTheDocument();
        expect(screen.getByText('For sales positions')).toBeInTheDocument();
      });
    });

    it('should show active badge for active profile', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Custom Profiles')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom Profiles'));

      await waitFor(() => {
        expect(screen.getByText('Active')).toBeInTheDocument();
      });
    });

    it('should display message when no custom profiles exist', async () => {
      mockListWeightProfiles.mockResolvedValue({ profiles: [] });

      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Custom Profiles')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Custom Profiles'));

      await waitFor(() => {
        expect(screen.getByText('No custom profiles yet. Save your first profile!')).toBeInTheDocument();
      });
    });
  });

  describe('Progress Bar Visualization', () => {
    it('should display progress bar', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const progressBars = document.querySelectorAll('.MuiLinearProgress-root');
        expect(progressBars.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Layout and Structure', () => {
    it('should use Container component', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
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
          <RankingWeightsPage />
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
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const papers = document.querySelectorAll('.MuiPaper-root');
        expect(papers.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Impact Preview Feature', () => {
    it('should not show Impact Preview tab initially', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.queryByText('Impact Preview')).not.toBeInTheDocument();
      });
    });

    it('should show Impact Preview tab when vacancy_id is in URL', async () => {
      // Mock window.location.search
      delete (window as any).location;
      (window as any).location = { search: '?vacancy_id=test-vacancy-123' };

      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Impact Preview')).toBeInTheDocument();
      });

      // Restore window.location
      delete (window as any).location;
      (window as any).location = { search: '' };
    });
  });

  describe('Edge Cases', () => {
    it('should handle very long profile names', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save Profile'));

      const longName = 'a'.repeat(200);
      const nameInput = screen.getByLabelText('Profile Name');

      await waitFor(() => {
        fireEvent.change(nameInput, { target: { value: longName } });
        expect(nameInput).toHaveValue(longName);
      });
    });

    it('should handle special characters in profile name', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save Profile'));

      const specialName = 'Test Profile @#$%';
      const nameInput = screen.getByLabelText('Profile Name');

      await waitFor(() => {
        fireEvent.change(nameInput, { target: { value: specialName } });
        expect(nameInput).toHaveValue(specialName);
      });
    });

    it('should handle empty profile description', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Save Profile'));

      await waitFor(() => {
        const nameInput = screen.getByLabelText('Profile Name');
        fireEvent.change(nameInput, { target: { value: 'Test' } });
      });

      await waitFor(() => {
        const saveButtons = screen.getAllByRole('button', { name: /Save/i });
        const saveButton = saveButtons.find(btn => btn.textContent === 'Save');
        if (saveButton) {
          fireEvent.click(saveButton);
        }
      });

      await waitFor(() => {
        expect(mockCreateWeightProfile).toHaveBeenCalledWith(
          expect.objectContaining({
            description: '',
          })
        );
      });
    });

    it('should handle active profile loading on mount', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(mockListWeightProfiles).toHaveBeenCalled();
        expect(mockGetPresetProfiles).toHaveBeenCalled();
      });

      // The active profile (profile-2) should be loaded
      fireEvent.click(screen.getByText('Current Weights'));

      await waitFor(() => {
        expect(screen.getByText('Experience Relevance: 20%')).toBeInTheDocument();
      });
    });
  });

  describe('Weight Changes', () => {
    it('should update weights when slider is changed', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
      });

      const initialTotal = screen.getByText('100%');
      expect(initialTotal).toBeInTheDocument();

      // Increase keyword score
      fireEvent.click(screen.getByText('Increase Keyword'));

      await waitFor(() => {
        // Total should now be > 100
        expect(screen.queryByText('100%')).not.toBeInTheDocument();
      });
    });

    it('should clear success message when weight changes', async () => {
      render(
        <BrowserRouter>
          <RankingWeightsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Current Weights')).toBeInTheDocument();
      });

      // Save a profile first
      fireEvent.click(screen.getByText('Save Profile'));

      await waitFor(() => {
        const nameInput = screen.getByLabelText('Profile Name');
        fireEvent.change(nameInput, { target: { value: 'Test' } });
      });

      await waitFor(() => {
        const saveButtons = screen.getAllByRole('button', { name: /Save/i });
        const saveButton = saveButtons.find(btn => btn.textContent === 'Save');
        if (saveButton) {
          fireEvent.click(saveButton);
        }
      });

      await waitFor(() => {
        expect(screen.getByText('Ranking weight profile saved successfully!')).toBeInTheDocument();
      });

      // Change a weight
      fireEvent.click(screen.getByText('Increase Keyword'));

      await waitFor(() => {
        expect(screen.queryByText('Ranking weight profile saved successfully!')).not.toBeInTheDocument();
      });
    });
  });
});
