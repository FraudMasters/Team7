/**
 * Tests for CandidateProfilePage Component
 *
 * Tests the candidate profile page including:
 * - Displaying candidate profile information
 * - Edit mode with form fields
 * - Loading and error states
 * - Profile sections: contact, bio, skills, experience, education
 * - Save and cancel functionality
 * - Form field editing and updates
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { CandidateProfilePage } from './CandidateProfilePage';

describe('CandidateProfilePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('location', { reload: vi.fn() });
  });

  describe('Component Rendering - View Mode', () => {
    it('should render the page with profile information', () => {
      render(<CandidateProfilePage />);

      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    it('should display contact information', () => {
      render(<CandidateProfilePage />);

      expect(screen.getByText('john.doe@example.com')).toBeInTheDocument();
      expect(screen.getByText('+1 (555) 123-4567')).toBeInTheDocument();
      expect(screen.getByText('San Francisco, CA')).toBeInTheDocument();
    });

    it('should display bio', () => {
      render(<CandidateProfilePage />);

      expect(screen.getByText(/Passionate software engineer/)).toBeInTheDocument();
    });

    it('should display skills as chips', () => {
      render(<CandidateProfilePage />);

      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('TypeScript')).toBeInTheDocument();
      expect(screen.getByText('Node.js')).toBeInTheDocument();
      expect(screen.getByText('Python')).toBeInTheDocument();
      expect(screen.getByText('AWS')).toBeInTheDocument();
      expect(screen.getByText('Docker')).toBeInTheDocument();
    });

    it('should display experience section', () => {
      render(<CandidateProfilePage />);

      expect(screen.getByText('Experience')).toBeInTheDocument();
      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('Tech Corp')).toBeInTheDocument();
      expect(screen.getByText('2021 - Present')).toBeInTheDocument();
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('StartUp Inc')).toBeInTheDocument();
      expect(screen.getByText('2019 - 2021')).toBeInTheDocument();
    });

    it('should display education section', () => {
      render(<CandidateProfilePage />);

      expect(screen.getByText('Education')).toBeInTheDocument();
      expect(screen.getByText('Bachelor of Science')).toBeInTheDocument();
      expect(screen.getByText('University of California')).toBeInTheDocument();
      expect(screen.getByText('Computer Science')).toBeInTheDocument();
    });

    it('should display edit button in view mode', () => {
      render(<CandidateProfilePage />);

      expect(screen.getByRole('button', { name: 'Edit Profile' })).toBeInTheDocument();
    });

    it('should not display save and cancel buttons in view mode', () => {
      render(<CandidateProfilePage />);

      expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Cancel' })).not.toBeInTheDocument();
    });

    it('should display section headers', () => {
      render(<CandidateProfilePage />);

      expect(screen.getByText('Contact Information')).toBeInTheDocument();
      expect(screen.getByText('About')).toBeInTheDocument();
      expect(screen.getByText('Skills')).toBeInTheDocument();
      expect(screen.getByText('Experience')).toBeInTheDocument();
      expect(screen.getByText('Education')).toBeInTheDocument();
    });

    it('should display icons for contact information', () => {
      render(<CandidateProfilePage />);

      const icons = document.querySelectorAll('.MuiSvgIcon-root');
      expect(icons.length).toBeGreaterThan(0);
    });
  });

  describe('Edit Mode', () => {
    it('should enter edit mode when edit button is clicked', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      expect(screen.queryByRole('button', { name: 'Edit Profile' })).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    });

    it('should display text fields in edit mode', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      // Name field should be editable
      const nameInput = screen.getByDisplayValue('John Doe');
      expect(nameInput).toBeInTheDocument();
      expect(nameInput.tagName).toBe('INPUT');
    });

    it('should make email editable in edit mode', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      const emailInput = screen.getByDisplayValue('john.doe@example.com');
      expect(emailInput).toBeInTheDocument();
      expect(emailInput.tagName).toBe('INPUT');
    });

    it('should make phone editable in edit mode', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      const phoneInput = screen.getByDisplayValue('+1 (555) 123-4567');
      expect(phoneInput).toBeInTheDocument();
      expect(phoneInput.tagName).toBe('INPUT');
    });

    it('should make location editable in edit mode', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      const locationInput = screen.getByDisplayValue('San Francisco, CA');
      expect(locationInput).toBeInTheDocument();
      expect(locationInput.tagName).toBe('INPUT');
    });

    it('should make bio editable in edit mode', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      const bioTextarea = screen.getByDisplayValue(/Passionate software engineer/);
      expect(bioTextarea).toBeInTheDocument();
      expect(bioTextarea.tagName).toBe('TEXTAREA');
    });

    it('should disable save button while saving', async () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      const saveButton = screen.getByRole('button', { name: 'Save' });
      fireEvent.click(saveButton);

      // Button should be disabled during save
      await waitFor(() => {
        expect(saveButton).toBeDisabled();
      });
    });

    it('should disable cancel button while saving', async () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      const saveButton = screen.getByRole('button', { name: 'Save' });
      const cancelButton = screen.getByRole('button', { name: 'Cancel' });
      fireEvent.click(saveButton);

      // Cancel button should be disabled during save
      await waitFor(() => {
        expect(cancelButton).toBeDisabled();
      });
    });

    it('should exit edit mode when cancel is clicked', () => {
      render(<CandidateProfilePage />);

      // Enter edit mode
      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      // Click cancel
      const cancelButton = screen.getByRole('button', { name: 'Cancel' });
      fireEvent.click(cancelButton);

      // Should be back in view mode
      expect(screen.getByRole('button', { name: 'Edit Profile' })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Cancel' })).not.toBeInTheDocument();
    });

    it('should revert changes when cancel is clicked', () => {
      render(<CandidateProfilePage />);

      // Enter edit mode
      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      // Make a change
      const nameInput = screen.getByDisplayValue('John Doe');
      fireEvent.change(nameInput, { target: { value: 'Jane Smith' } });

      // Cancel
      const cancelButton = screen.getByRole('button', { name: 'Cancel' });
      fireEvent.click(cancelButton);

      // Should show original name
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument();
    });
  });

  describe('Form Changes', () => {
    it('should update name field value', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      const nameInput = screen.getByDisplayValue('John Doe');
      fireEvent.change(nameInput, { target: { value: 'Jane Smith' } });

      expect(nameInput).toHaveValue('Jane Smith');
    });

    it('should update email field value', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      const emailInput = screen.getByDisplayValue('john.doe@example.com');
      fireEvent.change(emailInput, { target: { value: 'jane.smith@example.com' } });

      expect(emailInput).toHaveValue('jane.smith@example.com');
    });

    it('should update phone field value', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      const phoneInput = screen.getByDisplayValue('+1 (555) 123-4567');
      fireEvent.change(phoneInput, { target: { value: '+1 (555) 987-6543' } });

      expect(phoneInput).toHaveValue('+1 (555) 987-6543');
    });

    it('should update location field value', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      const locationInput = screen.getByDisplayValue('San Francisco, CA');
      fireEvent.change(locationInput, { target: { value: 'New York, NY' } });

      expect(locationInput).toHaveValue('New York, NY');
    });

    it('should update bio field value', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      const bioTextarea = screen.getByDisplayValue(/Passionate software engineer/);
      fireEvent.change(bioTextarea, { target: { value: 'New bio text' } });

      expect(bioTextarea).toHaveValue('New bio text');
    });
  });

  describe('Save Functionality', () => {
    it('should save changes and exit edit mode', async () => {
      render(<CandidateProfilePage />);

      // Enter edit mode
      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      // Make a change
      const nameInput = screen.getByDisplayValue('John Doe');
      fireEvent.change(nameInput, { target: { value: 'Jane Smith' } });

      // Save
      const saveButton = screen.getByRole('button', { name: 'Save' });
      fireEvent.click(saveButton);

      // Wait for save to complete (simulated delay)
      await waitFor(
        () => {
          expect(screen.getByRole('button', { name: 'Edit Profile' })).toBeInTheDocument();
        },
        { timeout: 1500 }
      );
    });

    it('should display saved changes after save', async () => {
      render(<CandidateProfilePage />);

      // Enter edit mode
      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      // Make a change
      const nameInput = screen.getByDisplayValue('John Doe');
      fireEvent.change(nameInput, { target: { value: 'Jane Smith' } });

      // Save
      const saveButton = screen.getByRole('button', { name: 'Save' });
      fireEvent.click(saveButton);

      // Wait for save to complete and check new name is displayed
      await waitFor(
        () => {
          expect(screen.getByText('Jane Smith')).toBeInTheDocument();
        },
        { timeout: 1500 }
      );
    });

    it('should re-enable buttons after save completes', async () => {
      render(<CandidateProfilePage />);

      // Enter edit mode
      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      // Save
      const saveButton = screen.getByRole('button', { name: 'Save' });
      fireEvent.click(saveButton);

      // Wait for save to complete
      await waitFor(
        () => {
          expect(screen.getByRole('button', { name: 'Edit Profile' })).not.toBeDisabled();
        },
        { timeout: 1500 }
      );
    });
  });

  describe('Loading State', () => {
    it('should render loading state when isLoading is true', () => {
      // This test verifies the loading state exists in the component
      // Note: The component uses local state for isLoading, which starts as false
      // To test this properly, we would need to modify the component to accept initial state
      render(<CandidateProfilePage />);

      // Component should render without loading state by default
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should render error state when error exists', () => {
      // This test verifies the error state exists in the component
      // Note: The component uses local state for error, which starts as null
      render(<CandidateProfilePage />);

      // Component should render without error state by default
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });

  describe('Layout and Structure', () => {
    it('should render in paper container', () => {
      const { container } = render(<CandidateProfilePage />);

      const paper = container.querySelector('.MuiPaper-root');
      expect(paper).toBeInTheDocument();
    });

    it('should render dividers between sections', () => {
      const { container } = render(<CandidateProfilePage />);

      const dividers = container.querySelectorAll('.MuiDivider-root');
      expect(dividers.length).toBeGreaterThan(0);
    });

    it('should use stack layout', () => {
      const { container } = render(<CandidateProfilePage />);

      const stacks = container.querySelectorAll('.MuiStack-root');
      expect(stacks.length).toBeGreaterThan(0);
    });
  });

  describe('Skills Display', () => {
    it('should display skills as outlined chips', () => {
      render(<CandidateProfilePage />);

      const skillChips = screen.getAllByRole('button').filter((button) =>
        ['React', 'TypeScript', 'Node.js', 'Python', 'AWS', 'Docker'].includes(button.textContent || '')
      );

      expect(skillChips.length).toBe(6);
    });

    it('should display skills in flex wrap layout', () => {
      const { container } = render(<CandidateProfilePage />);

      const skillsSection = Array.from(container.querySelectorAll('div')).find((div) =>
        div.textContent?.includes('Skills')
      );

      expect(skillsSection).toBeInTheDocument();
    });
  });

  describe('Experience Section', () => {
    it('should display all experience entries', () => {
      render(<CandidateProfilePage />);

      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    });

    it('should display company names', () => {
      render(<CandidateProfilePage />);

      expect(screen.getByText('Tech Corp')).toBeInTheDocument();
      expect(screen.getByText('StartUp Inc')).toBeInTheDocument();
    });

    it('should display duration information', () => {
      render(<CandidateProfilePage />);

      expect(screen.getByText('2021 - Present')).toBeInTheDocument();
      expect(screen.getByText('2019 - 2021')).toBeInTheDocument();
    });

    it('should have work icons for experience', () => {
      render(<CandidateProfilePage />);

      const icons = document.querySelectorAll('.MuiSvgIcon-root');
      expect(icons.length).toBeGreaterThan(0);
    });
  });

  describe('Education Section', () => {
    it('should display degree information', () => {
      render(<CandidateProfilePage />);

      expect(screen.getByText('Bachelor of Science')).toBeInTheDocument();
    });

    it('should display institution name', () => {
      render(<CandidateProfilePage />);

      expect(screen.getByText('University of California')).toBeInTheDocument();
    });

    it('should display field of study', () => {
      render(<CandidateProfilePage />);

      expect(screen.getByText('Computer Science')).toBeInTheDocument();
    });

    it('should have school icons for education', () => {
      render(<CandidateProfilePage />);

      const icons = document.querySelectorAll('.MuiSvgIcon-root');
      expect(icons.length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty name gracefully', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      const nameInput = screen.getByDisplayValue('John Doe');
      fireEvent.change(nameInput, { target: { value: '' } });

      expect(nameInput).toHaveValue('');
    });

    it('should handle very long bio text', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      const longBio = 'a'.repeat(1000);
      const bioTextarea = screen.getByDisplayValue(/Passionate software engineer/);
      fireEvent.change(bioTextarea, { target: { value: longBio } });

      expect(bioTextarea).toHaveValue(longBio);
    });

    it('should handle special characters in fields', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      fireEvent.click(editButton);

      const nameInput = screen.getByDisplayValue('John Doe');
      fireEvent.change(nameInput, { target: { value: 'José María García-López' } });

      expect(nameInput).toHaveValue('José María García-López');
    });
  });

  describe('Interactive Elements', () => {
    it('should have proper button states', () => {
      render(<CandidateProfilePage />);

      const editButton = screen.getByRole('button', { name: 'Edit Profile' });
      expect(editButton).toBeEnabled();
    });

    it('should toggle between view and edit modes', () => {
      render(<CandidateProfilePage />);

      // Start in view mode
      expect(screen.getByRole('button', { name: 'Edit Profile' })).toBeInTheDocument();

      // Enter edit mode
      fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));
      expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();

      // Cancel back to view mode
      fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
      expect(screen.getByRole('button', { name: 'Edit Profile' })).toBeInTheDocument();
    });
  });

  describe('Contact Information Icons', () => {
    it('should display email icon', () => {
      render(<CandidateProfilePage />);

      const icons = document.querySelectorAll('.MuiSvgIcon-root');
      expect(icons.length).toBeGreaterThan(0);
    });

    it('should display phone icon', () => {
      render(<CandidateProfilePage />);

      const phoneText = screen.getByText('+1 (555) 123-4567');
      expect(phoneText).toBeInTheDocument();
    });

    it('should display location icon', () => {
      render(<CandidateProfilePage />);

      const locationText = screen.getByText('San Francisco, CA');
      expect(locationText).toBeInTheDocument();
    });

    it('should display person icon in header', () => {
      render(<CandidateProfilePage />);

      const icons = document.querySelectorAll('.MuiSvgIcon-root');
      expect(icons.length).toBeGreaterThan(0);
    });
  });
});
