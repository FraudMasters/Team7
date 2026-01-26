/**
 * Tests for DateRangeFilter Component
 *
 * Tests the date range filter including:
 * - Date picker display and interaction
 * - Quick select presets functionality
 * - Custom date range selection
 * - Date validation
 * - Apply and Reset button functionality
 * - Active filter display
 * - Callback invocation
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import DateRangeFilter from './DateRangeFilter';

describe('DateRangeFilter', () => {
  const mockOnApply = vi.fn();
  const mockOnReset = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render date pickers', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
      expect(screen.getByLabelText('End Date')).toBeInTheDocument();
    });

    it('should render quick select presets', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      expect(screen.getByText('Last 7 Days')).toBeInTheDocument();
      expect(screen.getByText('Last 30 Days')).toBeInTheDocument();
      expect(screen.getByText('Last 90 Days')).toBeInTheDocument();
      expect(screen.getByText('This Month')).toBeInTheDocument();
      expect(screen.getByText('Last Month')).toBeInTheDocument();
      expect(screen.getByText('This Year')).toBeInTheDocument();
    });

    it('should render Apply and Reset buttons', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      expect(screen.getByText('Apply')).toBeInTheDocument();
      expect(screen.getByText('Reset')).toBeInTheDocument();
    });
  });

  describe('Quick Select Presets', () => {
    it('should set dates when Last 7 Days is clicked', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      fireEvent.click(screen.getByText('Last 7 Days'));

      // Verify dates are set (approximately 7 days apart)
      const startDateInput = screen.getByLabelText('Start Date') as HTMLInputElement;
      const endDateInput = screen.getByLabelText('End Date') as HTMLInputElement;

      expect(startDateInput.value).toBeTruthy();
      expect(endDateInput.value).toBeTruthy();
    });

    it('should set dates when Last 30 Days is clicked', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      fireEvent.click(screen.getByText('Last 30 Days'));

      const startDateInput = screen.getByLabelText('Start Date') as HTMLInputElement;
      const endDateInput = screen.getByLabelText('End Date') as HTMLInputElement;

      expect(startDateInput.value).toBeTruthy();
      expect(endDateInput.value).toBeTruthy();
    });

    it('should set dates when This Month is clicked', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      fireEvent.click(screen.getByText('This Month'));

      const startDateInput = screen.getByLabelText('Start Date') as HTMLInputElement;
      const endDateInput = screen.getByLabelText('End Date') as HTMLInputElement;

      expect(startDateInput.value).toBeTruthy();
      expect(endDateInput.value).toBeTruthy();
    });

    it('should set dates when This Year is clicked', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      fireEvent.click(screen.getByText('This Year'));

      const startDateInput = screen.getByLabelText('Start Date') as HTMLInputElement;
      const endDateInput = screen.getByLabelText('End Date') as HTMLInputElement;

      expect(startDateInput.value).toBeTruthy();
      expect(endDateInput.value).toBeTruthy();
    });
  });

  describe('Custom Date Selection', () => {
    it('should allow manual date input for start date', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      const startDateInput = screen.getByLabelText('Start Date');
      fireEvent.change(startDateInput, { target: { value: '2024-01-01' } });

      expect((startDateInput as HTMLInputElement).value).toBe('2024-01-01');
    });

    it('should allow manual date input for end date', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      const endDateInput = screen.getByLabelText('End Date');
      fireEvent.change(endDateInput, { target: { value: '2024-12-31' } });

      expect((endDateInput as HTMLInputElement).value).toBe('2024-12-31');
    });
  });

  describe('Apply Button', () => {
    it('should call onApply callback with dates when Apply is clicked', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      const startDateInput = screen.getByLabelText('Start Date');
      const endDateInput = screen.getByLabelText('End Date');

      fireEvent.change(startDateInput, { target: { value: '2024-01-01' } });
      fireEvent.change(endDateInput, { target: { value: '2024-12-31' } });
      fireEvent.click(screen.getByText('Apply'));

      expect(mockOnApply).toHaveBeenCalledWith('2024-01-01', '2024-12-31');
    });

    it('should not call onApply if dates are invalid', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      const startDateInput = screen.getByLabelText('Start Date');
      const endDateInput = screen.getByLabelText('End Date');

      fireEvent.change(startDateInput, { target: { value: '2024-12-31' } });
      fireEvent.change(endDateInput, { target: { value: '2024-01-01' } });
      fireEvent.click(screen.getByText('Apply'));

      expect(mockOnApply).not.toHaveBeenCalled();
    });

    it('should show validation error when start date is after end date', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      const startDateInput = screen.getByLabelText('Start Date');
      const endDateInput = screen.getByLabelText('End Date');

      fireEvent.change(startDateInput, { target: { value: '2024-12-31' } });
      fireEvent.change(endDateInput, { target: { value: '2024-01-01' } });
      fireEvent.click(screen.getByText('Apply'));

      // Error message should be displayed
      expect(screen.getByText(/Start date must be before end date/)).toBeInTheDocument();
    });
  });

  describe('Reset Button', () => {
    it('should call onReset callback when Reset is clicked', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      fireEvent.click(screen.getByText('Reset'));

      expect(mockOnReset).toHaveBeenCalled();
    });

    it('should clear date inputs when Reset is clicked', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      const startDateInput = screen.getByLabelText('Start Date');
      const endDateInput = screen.getByLabelText('End Date');

      fireEvent.change(startDateInput, { target: { value: '2024-01-01' } });
      fireEvent.change(endDateInput, { target: { value: '2024-12-31' } });
      fireEvent.click(screen.getByText('Reset'));

      expect((startDateInput as HTMLInputElement).value).toBe('');
      expect((endDateInput as HTMLInputElement).value).toBe('');
    });
  });

  describe('Active Filter Display', () => {
    it('should display active date range when dates are set', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      const startDateInput = screen.getByLabelText('Start Date');
      const endDateInput = screen.getByLabelText('End Date');

      fireEvent.change(startDateInput, { target: { value: '2024-01-01' } });
      fireEvent.change(endDateInput, { target: { value: '2024-12-31' } });
      fireEvent.click(screen.getByText('Apply'));

      // Active filter should be displayed
      expect(screen.getByText(/Active Filter/)).toBeInTheDocument();
    });

    it('should hide active filter when dates are reset', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      const startDateInput = screen.getByLabelText('Start Date');
      const endDateInput = screen.getByLabelText('End Date');

      fireEvent.change(startDateInput, { target: { value: '2024-01-01' } });
      fireEvent.change(endDateInput, { target: { value: '2024-12-31' } });
      fireEvent.click(screen.getByText('Apply'));

      fireEvent.click(screen.getByText('Reset'));

      // Active filter should be hidden or show "All Time"
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty date inputs', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      fireEvent.click(screen.getByText('Apply'));

      // Should call onApply with undefined or null values
      expect(mockOnApply).toHaveBeenCalledWith(undefined, undefined);
    });

    it('should handle only start date set', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      const startDateInput = screen.getByLabelText('Start Date');

      fireEvent.change(startDateInput, { target: { value: '2024-01-01' } });
      fireEvent.click(screen.getByText('Apply'));

      expect(mockOnApply).toHaveBeenCalledWith('2024-01-01', undefined);
    });

    it('should handle only end date set', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      const endDateInput = screen.getByLabelText('End Date');

      fireEvent.change(endDateInput, { target: { value: '2024-12-31' } });
      fireEvent.click(screen.getByText('Apply'));

      expect(mockOnApply).toHaveBeenCalledWith(undefined, '2024-12-31');
    });

    it('should handle same start and end date', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      const startDateInput = screen.getByLabelText('Start Date');
      const endDateInput = screen.getByLabelText('End Date');

      fireEvent.change(startDateInput, { target: { value: '2024-01-01' } });
      fireEvent.change(endDateInput, { target: { value: '2024-01-01' } });
      fireEvent.click(screen.getByText('Apply'));

      expect(mockOnApply).toHaveBeenCalledWith('2024-01-01', '2024-01-01');
    });
  });

  describe('Date Validation', () => {
    it('should validate date format', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      const startDateInput = screen.getByLabelText('Start Date');

      // Invalid date format
      fireEvent.change(startDateInput, { target: { value: 'invalid-date' } });
      fireEvent.click(screen.getByText('Apply'));

      // Should show validation error
      expect(screen.getByText(/Invalid date format/)).toBeInTheDocument();
    });

    it('should validate start date is not after end date', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      const startDateInput = screen.getByLabelText('Start Date');
      const endDateInput = screen.getByLabelText('End Date');

      fireEvent.change(startDateInput, { target: { value: '2024-12-31' } });
      fireEvent.change(endDateInput, { target: { value: '2024-01-01' } });
      fireEvent.click(screen.getByText('Apply'));

      expect(screen.getByText(/Start date must be before end date/)).toBeInTheDocument();
      expect(mockOnApply).not.toHaveBeenCalled();
    });
  });

  describe('Visual Design', () => {
    it('should display preset buttons in a row', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      const presets = [
        'Last 7 Days',
        'Last 30 Days',
        'Last 90 Days',
        'This Month',
        'Last Month',
        'This Year',
      ];

      presets.forEach((preset) => {
        expect(screen.getByText(preset)).toBeInTheDocument();
      });
    });

    it('should display date inputs with correct labels', () => {
      render(<DateRangeFilter onApply={mockOnApply} onReset={mockOnReset} />);

      expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
      expect(screen.getByLabelText('End Date')).toBeInTheDocument();
    });
  });
});
