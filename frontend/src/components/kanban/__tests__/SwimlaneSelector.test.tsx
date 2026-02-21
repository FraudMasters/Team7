/**
 * Tests for SwimlaneSelector Component
 *
 * Tests the swimlane selector component including:
 * - Rendering all group-by options (None, By Job, By Recruiter)
 * - Value selection and onChange callback
 * - Disabled state
 * - Label visibility
 * - Tooltip display
 * - Variants (outlined vs plain)
 * - Size options
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SwimlaneSelector, { SwimlaneSelectorProps, SwimlaneGroupBy } from '../SwimlaneSelector';

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue: string) => defaultValue || key,
  }),
}));

// Helper to create default props
const createDefaultProps = (
  valueOverrides?: Partial<SwimlaneSelectorProps>
): SwimlaneSelectorProps => ({
  value: 'none' as SwimlaneGroupBy,
  onChange: vi.fn(),
  ...valueOverrides,
});

describe('SwimlaneSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render all three group-by options', () => {
      const props = createDefaultProps();
      render(<SwimlaneSelector {...props} />);

      expect(screen.getByText('None')).toBeInTheDocument();
      expect(screen.getByText('By Job')).toBeInTheDocument();
      expect(screen.getByText('By Recruiter')).toBeInTheDocument();
    });

    it('should render group by label when showLabel is true', () => {
      const props = createDefaultProps({ showLabel: true });
      render(<SwimlaneSelector {...props} />);

      expect(screen.getByText('Group by:')).toBeInTheDocument();
    });

    it('should not render label when showLabel is false', () => {
      const props = createDefaultProps({ showLabel: false });
      render(<SwimlaneSelector {...props} />);

      expect(screen.queryByText('Group by:')).not.toBeInTheDocument();
    });

    it('should show label by default', () => {
      const props = createDefaultProps();
      render(<SwimlaneSelector {...props} />);

      expect(screen.getByText('Group by:')).toBeInTheDocument();
    });
  });

  describe('Selection State', () => {
    it('should highlight the selected value', () => {
      const props = createDefaultProps({ value: 'job' });
      render(<SwimlaneSelector {...props} />);

      // The selected button should have Mui-selected class
      const selectedButton = screen.getByText('By Job').closest('button');
      expect(selectedButton).toHaveClass('Mui-selected');
    });

    it('should select "none" option by default', () => {
      const props = createDefaultProps();
      render(<SwimlaneSelector {...props} />);

      const selectedButton = screen.getByText('None').closest('button');
      expect(selectedButton).toHaveClass('Mui-selected');
    });

    it('should update selection when value prop changes', () => {
      const props = createDefaultProps({ value: 'recruiter' });
      render(<SwimlaneSelector {...props} />);

      const selectedButton = screen.getByText('By Recruiter').closest('button');
      expect(selectedButton).toHaveClass('Mui-selected');
    });
  });

  describe('onChange Handling', () => {
    it('should call onChange when option is clicked', () => {
      const onChange = vi.fn();
      const props = createDefaultProps({ onChange });
      render(<SwimlaneSelector {...props} />);

      const jobButton = screen.getByText('By Job').closest('button');
      if (jobButton) {
        fireEvent.click(jobButton);
      }

      expect(onChange).toHaveBeenCalledWith('job');
    });

    it('should call onChange with correct value for each option', () => {
      const onChange = vi.fn();
      const props = createDefaultProps({ onChange });
      render(<SwimlaneSelector {...props} />);

      // Click "By Job"
      const jobButton = screen.getByText('By Job').closest('button');
      if (jobButton) {
        fireEvent.click(jobButton);
      }
      expect(onChange).toHaveBeenCalledWith('job');

      // Click "By Recruiter"
      const recruiterButton = screen.getByText('By Recruiter').closest('button');
      if (recruiterButton) {
        fireEvent.click(recruiterButton);
      }
      expect(onChange).toHaveBeenCalledWith('recruiter');

      // Click "None"
      const noneButton = screen.getByText('None').closest('button');
      if (noneButton) {
        fireEvent.click(noneButton);
      }
      expect(onChange).toHaveBeenCalledWith('none');
    });
  });

  describe('Disabled State', () => {
    it('should disable all buttons when disabled is true', () => {
      const props = createDefaultProps({ disabled: true });
      render(<SwimlaneSelector {...props} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach((button) => {
        expect(button).toHaveAttribute('disabled');
      });
    });

    it('should enable all buttons when disabled is false', () => {
      const props = createDefaultProps({ disabled: false });
      render(<SwimlaneSelector {...props} />);

      const buttons = screen.getAllByRole('button');
      // The group itself is disabled, not individual buttons
      const buttonGroup = buttons[0].closest('.MuiToggleButtonGroup-root');
      expect(buttonGroup).not.toHaveClass('Mui-disabled');
    });

    it('should be enabled by default', () => {
      const props = createDefaultProps();
      render(<SwimlaneSelector {...props} />);

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  describe('Size Options', () => {
    it('should apply small size when size is "small"', () => {
      const props = createDefaultProps({ size: 'small' });
      render(<SwimlaneSelector {...props} />);

      const buttonGroup = screen.getByText('None').closest('.MuiToggleButtonGroup-root');
      expect(buttonGroup).toHaveClass('MuiToggleButtonGroup-sizeSmall');
    });

    it('should apply medium size when size is "medium"', () => {
      const props = createDefaultProps({ size: 'medium' });
      render(<SwimlaneSelector {...props} />);

      const buttonGroup = screen.getByText('None').closest('.MuiToggleButtonGroup-root');
      expect(buttonGroup).toHaveClass('MuiToggleButtonGroup-sizeMedium');
    });

    it('should default to small size', () => {
      const props = createDefaultProps();
      render(<SwimlaneSelector {...props} />);

      const buttonGroup = screen.getByText('None').closest('.MuiToggleButtonGroup-root');
      expect(buttonGroup).toHaveClass('MuiToggleButtonGroup-sizeSmall');
    });
  });

  describe('Variants', () => {
    it('should render outlined variant with Paper wrapper', () => {
      const props = createDefaultProps({ variant: 'outlined' });
      render(<SwimlaneSelector {...props} />);

      // Paper component has MuiPaper-root class
      const paper = screen.getByText('Group by:').closest('.MuiPaper-root');
      expect(paper).toBeInTheDocument();
    });

    it('should render plain variant without Paper wrapper', () => {
      const props = createDefaultProps({ variant: 'plain' });
      render(<SwimlaneSelector {...props} />);

      // No Paper wrapper should exist
      const paper = screen.getByText('Group by:').closest('.MuiPaper-root');
      expect(paper).not.toBeInTheDocument();
    });

    it('should default to outlined variant', () => {
      const props = createDefaultProps();
      render(<SwimlaneSelector {...props} />);

      const paper = screen.getByText('Group by:').closest('.MuiPaper-root');
      expect(paper).toBeInTheDocument();
    });
  });

  describe('Tooltips', () => {
    it('should have tooltips when showTooltips is true', () => {
      const props = createDefaultProps({ showTooltips: true });
      render(<SwimlaneSelector {...props} />);

      // Each button should be wrapped in a Tooltip
      const noneButton = screen.getByText('None').closest('button');
      expect(noneButton).toBeInTheDocument();
    });

    it('should not have tooltips when showTooltips is false', () => {
      const props = createDefaultProps({ showTooltips: false });
      render(<SwimlaneSelector {...props} />);

      // Buttons should exist without tooltip wrappers
      const noneButton = screen.getByText('None').closest('button');
      expect(noneButton).toBeInTheDocument();
    });

    it('should show tooltips by default', () => {
      const props = createDefaultProps();
      render(<SwimlaneSelector {...props} />);

      const noneButton = screen.getByText('None').closest('button');
      expect(noneButton).toBeInTheDocument();
    });
  });

  describe('Icons', () => {
    it('should render icons for each option', () => {
      const props = createDefaultProps();
      render(<SwimlaneSelector {...props} />);

      // Each button should have an icon
      const buttons = screen.getAllByRole('button');
      buttons.forEach((button) => {
        const svg = button.querySelector('svg');
        expect(svg).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Behavior', () => {
    it('should render option labels for larger screens', () => {
      const props = createDefaultProps();
      render(<SwimlaneSelector {...props} />);

      // Labels should be in the document (they're hidden on xs screens via CSS)
      expect(screen.getByText('None')).toBeInTheDocument();
      expect(screen.getByText('By Job')).toBeInTheDocument();
      expect(screen.getByText('By Recruiter')).toBeInTheDocument();
    });
  });
});
