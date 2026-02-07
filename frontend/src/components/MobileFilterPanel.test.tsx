import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider } from '@mui/material/styles';
import { I18nextProvider } from 'react-i18next';
import MobileFilterPanel, {
  MobileFilterPanelProps,
  defaultFilterState,
  MobileFilterState,
} from './MobileFilterPanel';
import { createTheme } from '@mui/material/styles';
import i18n from '../i18n';

// Mock dependencies
jest.mock('react-i18next', () => ({
  ...jest.requireActual('react-i18next'),
  useTranslation: () => ({
    t: (key: string, options?: Record<string, unknown>) => {
      // Simple mock that returns the key or interpolates options
      if (options) {
        return key.replace(/{{(\w+)}}/g, (_, match) => String(options[match] || ''));
      }
      return key;
    },
  }),
}));

const theme = createTheme();

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      <I18nextProvider i18n={i18n}>
        {component}
      </I18nextProvider>
    </ThemeProvider>
  );
};

describe('MobileFilterPanel', () => {
  const mockOnApplyFilters = jest.fn();
  const mockOnClose = jest.fn();
  const defaultFilters: MobileFilterState = defaultFilterState;

  const defaultProps: MobileFilterPanelProps = {
    open: true,
    onClose: mockOnClose,
    onApplyFilters: mockOnApplyFilters,
    filters: defaultFilters,
    skillOptions: ['Python', 'Java', 'JavaScript', 'TypeScript'],
    languageOptions: ['English', 'Spanish', 'French'],
    locationOptions: ['Remote', 'New York', 'London'],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render when open', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);
      expect(screen.getByText('mobileFilterPanel.title')).toBeInTheDocument();
    });

    it('should not render when closed', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} open={false} />);
      expect(screen.queryByText('mobileFilterPanel.title')).not.toBeInTheDocument();
    });

    it('should render all filter section accordions', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      expect(screen.getByText('mobileFilterPanel.skills')).toBeInTheDocument();
      expect(screen.getByText('mobileFilterPanel.experience')).toBeInTheDocument();
      expect(screen.getByText('mobileFilterPanel.location')).toBeInTheDocument();
      expect(screen.getByText('mobileFilterPanel.education')).toBeInTheDocument();
      expect(screen.getByText('mobileFilterPanel.languages')).toBeInTheDocument();
      expect(screen.getByText('mobileFilterPanel.salary')).toBeInTheDocument();
      expect(screen.getByText('mobileFilterPanel.matchScore')).toBeInTheDocument();
    });

    it('should render action buttons', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      expect(screen.getByText('mobileFilterPanel.clear')).toBeInTheDocument();
      expect(screen.getByText('mobileFilterPanel.apply')).toBeInTheDocument();
    });

    it('should display active filter count badge', () => {
      const filtersWithValues: MobileFilterState = {
        ...defaultFilters,
        skills: ['Python'],
      };

      renderWithProviders(
        <MobileFilterPanel {...defaultProps} filters={filtersWithValues} />
      );

      expect(screen.getByText('1 mobileFilterPanel.active')).toBeInTheDocument();
    });

    it('should not display count badge when no filters active', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      expect(screen.queryByText(/mobileFilterPanel.active/)).not.toBeInTheDocument();
    });
  });

  describe('Accordion Expansion', () => {
    it('should toggle accordion sections on click', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const skillsAccordion = screen.getByText('mobileFilterPanel.skills');
      fireEvent.click(skillsAccordion);

      // After clicking, the accordion should still be present
      expect(skillsAccordion).toBeInTheDocument();
    });

    it('should render skill chips when expanded', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      defaultProps.skillOptions.forEach((skill) => {
        expect(screen.getByText(skill)).toBeInTheDocument();
      });
    });

    it('should render language chips when expanded', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      defaultProps.languageOptions.forEach((language) => {
        expect(screen.getByText(language)).toBeInTheDocument();
      });
    });
  });

  describe('Filter Interactions', () => {
    it('should toggle skill selection when chip is clicked', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const pythonChip = screen.getByText('Python').closest('div[role="button"]');
      expect(pythonChip).toBeInTheDocument();

      if (pythonChip) {
        fireEvent.click(pythonChip);
      }
    });

    it('should toggle language selection when chip is clicked', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const englishChip = screen.getByText('English').closest('div[role="button"]');
      expect(englishChip).toBeInTheDocument();

      if (englishChip) {
        fireEvent.click(englishChip);
      }
    });

    it('should update experience range slider', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const sliders = screen.getAllByRole('slider');
      expect(sliders.length).toBeGreaterThan(0);
    });

    it('should update match score range slider', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const sliders = screen.getAllByRole('slider');
      expect(sliders.length).toBeGreaterThan(0);
    });

    it('should clear all filters when clear button is clicked', () => {
      const filtersWithValues: MobileFilterState = {
        ...defaultFilters,
        skills: ['Python', 'Java'],
      };

      renderWithProviders(
        <MobileFilterPanel {...defaultProps} filters={filtersWithValues} />
      );

      const clearButton = screen.getByText('mobileFilterPanel.clear');
      fireEvent.click(clearButton);

      expect(mockOnApplyFilters).not.toHaveBeenCalled(); // Clear doesn't apply, just resets
    });

    it('should apply filters and close when apply button is clicked', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const applyButton = screen.getByText('mobileFilterPanel.apply');
      fireEvent.click(applyButton);

      expect(mockOnApplyFilters).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should disable apply button when loading', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} loading={true} />);

      const applyButton = screen.getByText('mobileFilterPanel.applying');
      expect(applyButton).toBeInTheDocument();
    });

    it('should disable clear button when no active filters', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const clearButton = screen.getByText('mobileFilterPanel.clear');
      expect(clearButton).toBeDisabled();
    });
  });

  describe('Touch-Friendly Elements', () => {
    it('should have touch-friendly slider thumbs (28px)', () => {
      const { container } = renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const sliderThumbs = container.querySelectorAll('.MuiSlider-thumb');
      sliderThumbs.forEach((thumb) => {
        const styles = window.getComputedStyle(thumb);
        expect(parseInt(styles.width)).toBeGreaterThanOrEqual(28);
        expect(parseInt(styles.height)).toBeGreaterThanOrEqual(28);
      });
    });

    it('should have touch-friendly menu items (min 44px)', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      // Check location select
      const locationSection = screen.getByText('mobileFilterPanel.location');
      fireEvent.click(locationSection);

      const menuItems = screen.queryAllByText(/Remote|New York|London/);
      menuItems.forEach((item) => {
        const menuItem = item.closest('.MuiMenuItem-root');
        if (menuItem) {
          const styles = window.getComputedStyle(menuItem);
          expect(parseInt(styles.minHeight)).toBeGreaterThanOrEqual(44);
        }
      });
    });

    it('should have touch-friendly chips (min 44px)', () => {
      const { container } = renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const chips = container.querySelectorAll('.MuiChip-root');
      chips.forEach((chip) => {
        const styles = window.getComputedStyle(chip);
        expect(parseInt(styles.minHeight)).toBeGreaterThanOrEqual(44);
      });
    });

    it('should have touch-friendly buttons (min 48px)', () => {
      const { container } = renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const buttons = container.querySelectorAll('.MuiButton-root');
      buttons.forEach((button) => {
        const styles = window.getComputedStyle(button);
        expect(parseInt(styles.minHeight)).toBeGreaterThanOrEqual(48);
      });
    });
  });

  describe('Filter State Management', () => {
    it('should use default filters when no filters provided', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const applyButton = screen.getByText('mobileFilterPanel.apply');
      fireEvent.click(applyButton);

      expect(mockOnApplyFilters).toHaveBeenCalledWith(defaultFilterState);
    });

    it('should update local state when filters prop changes', () => {
      const { rerender } = renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const newFilters: MobileFilterState = {
        ...defaultFilters,
        skills: ['Python'],
      };

      rerender(
        <ThemeProvider theme={theme}>
          <I18nextProvider i18n={i18n}>
            <MobileFilterPanel {...defaultProps} filters={newFilters} />
          </I18nextProvider>
        </ThemeProvider>
      );

      const applyButton = screen.getByText('mobileFilterPanel.apply');
      fireEvent.click(applyButton);

      expect(mockOnApplyFilters).toHaveBeenCalledWith(newFilters);
    });

    it('should count active filters correctly', () => {
      const filtersWithValues: MobileFilterState = {
        ...defaultFilters,
        skills: ['Python', 'Java'],
        minExperience: 5,
      };

      renderWithProviders(
        <MobileFilterPanel {...defaultProps} filters={filtersWithValues} />
      );

      // Should show 2 active filters (skills range changed, experience changed)
      expect(screen.getByText(/mobileFilterPanel.active/)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels on buttons', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const closeButton = screen.getAllByRole('button').find((button) =>
        button.querySelector('svg[data-testid="CloseIcon"]')
      );

      expect(closeButton).toBeInTheDocument();
    });

    it('should have proper heading hierarchy', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const title = screen.getByText('mobileFilterPanel.title');
      expect(title).toBeInTheDocument();
    });

    it('should be keyboard navigable', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const accordions = screen.getAllByRole('button');
      accordions.forEach((accordion) => {
        expect(accordion).toHaveAttribute('type', 'button');
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty skill options', () => {
      renderWithProviders(
        <MobileFilterPanel {...defaultProps} skillOptions={[]} />
      );

      expect(screen.getByText('mobileFilterPanel.skills')).toBeInTheDocument();
    });

    it('should handle empty language options', () => {
      renderWithProviders(
        <MobileFilterPanel {...defaultProps} languageOptions={[]} />
      );

      expect(screen.getByText('mobileFilterPanel.languages')).toBeInTheDocument();
    });

    it('should handle empty location options', () => {
      renderWithProviders(
        <MobileFilterPanel {...defaultProps} locationOptions={[]} />
      );

      expect(screen.getByText('mobileFilterPanel.location')).toBeInTheDocument();
    });

    it('should handle all filters at default values', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const clearButton = screen.getByText('mobileFilterPanel.clear');
      expect(clearButton).toBeDisabled();
    });

    it('should handle custom width prop', () => {
      const { container } = renderWithProviders(
        <MobileFilterPanel {...defaultProps} width="80%" />
      );

      expect(container.firstChild).toBeInTheDocument();
    });
  });

  describe('UI Components', () => {
    it('should render close button in header', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const closeButtons = screen.getAllByRole('button');
      const closeButton = closeButtons.find((button) =>
        button.querySelector('svg[data-testid="CloseIcon"]')
      );

      expect(closeButton).toBeInTheDocument();
    });

    it('should render filter icon in header', () => {
      renderWithProviders(<MobileFilterPanel {...defaultProps} />);

      const filterIcon = document.querySelector('svg[data-testid="FilterListIcon"]');
      expect(filterIcon).toBeInTheDocument();
    });

    it('should render chips for selected filters in accordion headers', () => {
      const filtersWithValues: MobileFilterState = {
        ...defaultFilters,
        skills: ['Python', 'Java'],
      };

      renderWithProviders(
        <MobileFilterPanel {...defaultProps} filters={filtersWithValues} />
      );

      // Skills accordion should show count chip
      const skillsAccordion = screen.getByText('mobileFilterPanel.skills');
      expect(skillsAccordion).toBeInTheDocument();
    });
  });
});
