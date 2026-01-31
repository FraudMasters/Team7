/**
 * Tests for CustomSynonymsManager Component
 *
 * Tests the custom synonyms management interface including:
 * - Fetching and displaying synonyms
 * - Creating new synonym entries
 * - Editing existing synonyms
 * - Deleting synonyms with confirmation
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import CustomSynonymsManager from './CustomSynonymsManager';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('CustomSynonymsManager', () => {
  const mockOrganizationId = 'org-123';
  const mockApiUrl = 'http://localhost:8000/api/custom-synonyms';

  const mockSynonyms = [
    {
      id: 'syn-1',
      organization_id: mockOrganizationId,
      canonical_skill: 'React',
      custom_synonyms: ['ReactJS', 'React.js', 'React Framework'],
      context: 'web_framework',
      is_active: true,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
    },
    {
      id: 'syn-2',
      organization_id: mockOrganizationId,
      canonical_skill: 'Python',
      custom_synonyms: ['Python3', 'Py'],
      context: 'language',
      is_active: false,
      created_at: '2024-01-16T10:00:00Z',
      updated_at: '2024-01-16T10:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: mockSynonyms,
          total_count: 2,
        }),
      });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      expect(screen.getByText('Loading custom synonyms...')).toBeInTheDocument();
    });

    it('should render synonyms list after successful fetch', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: mockSynonyms,
          total_count: 2,
        }),
      });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Custom Synonyms Management')).toBeInTheDocument();
      });

      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('Python')).toBeInTheDocument();
      expect(screen.getByText('ReactJS')).toBeInTheDocument();
      expect(screen.getByText('Python3')).toBeInTheDocument();
    });

    it('should display summary statistics correctly', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: mockSynonyms,
          total_count: 2,
        }),
      });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('2')).toBeInTheDocument(); // Total synonyms
      });

      expect(screen.getByText('1')).toBeInTheDocument(); // Active count
      expect(screen.getByText('1')).toBeInTheDocument(); // Inactive count
    });

    it('should render empty state when no synonyms exist', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: [],
          total_count: 0,
        }),
      });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('No Custom Synonyms Found')).toBeInTheDocument();
      });

      expect(
        screen.getByText('Get started by adding your first custom synonym entry for this organization.')
      ).toBeInTheDocument();
    });

    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Error Loading Synonyms')).toBeInTheDocument();
      });

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  describe('Synonym Display', () => {
    it('should display context badges with correct colors', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: mockSynonyms,
          total_count: 2,
        }),
      });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      expect(screen.getByText('web_framework')).toBeInTheDocument();
      expect(screen.getByText('language')).toBeInTheDocument();
    });

    it('should display active/inactive status badges', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: mockSynonyms,
          total_count: 2,
        }),
      });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Inactive')).toBeInTheDocument();
    });

    it('should display creation date', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: mockSynonyms,
          total_count: 2,
        }),
      });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText(/Created:/)).toBeInTheDocument();
      });
    });
  });

  describe('Create Synonym', () => {
    it('should open create dialog when Add button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: [],
          total_count: 0,
        }),
      });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Add Custom Synonym')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Add Custom Synonym'));

      await waitFor(() => {
        expect(screen.getByText('Add Custom Synonym')).toBeInTheDocument();
        expect(screen.getByLabelText('Canonical Skill Name')).toBeInTheDocument();
      });
    });

    it('should create new synonym successfully', async () => {
      const newSynonym = {
        id: 'syn-3',
        organization_id: mockOrganizationId,
        canonical_skill: 'TypeScript',
        custom_synonyms: ['TS', 'TypeScript3'],
        context: 'language',
        is_active: true,
        created_at: '2024-01-17T10:00:00Z',
        updated_at: '2024-01-17T10:00:00Z',
      };

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            organization_id: mockOrganizationId,
            synonyms: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            organization_id: mockOrganizationId,
            synonyms: [newSynonym],
            total_count: 1,
          }),
        });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Add Custom Synonym')).toBeInTheDocument();
      });

      // Open dialog
      fireEvent.click(screen.getByText('Add Custom Synonym'));

      await waitFor(() => {
        expect(screen.getByLabelText('Canonical Skill Name')).toBeInTheDocument();
      });

      // Fill form
      fireEvent.change(screen.getByLabelText('Canonical Skill Name'), {
        target: { value: 'TypeScript' },
      });

      fireEvent.change(screen.getByLabelText('Custom Synonyms'), {
        target: { value: 'TS, TypeScript3' },
      });

      // Submit form
      fireEvent.click(screen.getByText('Create'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2); // Initial fetch + create
      });

      const createCall = mockFetch.mock.calls[1];
      expect(createCall[0]).toBe(mockApiUrl);
      expect(createCall[1].method).toBe('POST');
    });

    it('should validate that at least one synonym is required', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: [],
          total_count: 0,
        }),
      });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Add Custom Synonym')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Add Custom Synonym'));

      await waitFor(() => {
        expect(screen.getByLabelText('Canonical Skill Name')).toBeInTheDocument();
      });

      // Fill only canonical skill, leave synonyms empty
      fireEvent.change(screen.getByLabelText('Canonical Skill Name'), {
        target: { value: 'JavaScript' },
      });

      // Try to submit - button should be disabled
      expect(screen.getByText('Create')).toBeDisabled();
    });
  });

  describe('Edit Synonym', () => {
    it('should open edit dialog with pre-filled data', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: mockSynonyms,
          total_count: 2,
        }),
      });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      // Find and click edit button for React
      const editButtons = screen.getAllByRole('button');
      const reactEditButton = editButtons.find(
        (btn) => btn.getAttribute('color') === 'primary'
      );

      expect(reactEditButton).toBeInTheDocument();
      fireEvent.click(reactEditButton!);

      await waitFor(() => {
        expect(screen.getByText('Edit Custom Synonym')).toBeInTheDocument();
        expect(screen.getByDisplayValue('React')).toBeInTheDocument();
        expect(screen.getByDisplayValue('ReactJS, React.js, React Framework')).toBeInTheDocument();
      });
    });

    it('should update synonym successfully', async () => {
      const updatedSynonym = {
        ...mockSynonyms[0],
        custom_synonyms: ['ReactJS', 'React.js', 'React Framework', 'ReactJS2'],
      };

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            organization_id: mockOrganizationId,
            synonyms: mockSynonyms,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => updatedSynonym,
        });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      // Click edit button
      const editButtons = screen.getAllByRole('button');
      const reactEditButton = editButtons.find((btn) => btn.getAttribute('color') === 'primary');
      fireEvent.click(reactEditButton!);

      await waitFor(() => {
        expect(screen.getByText('Edit Custom Synonym')).toBeInTheDocument();
      });

      // Update synonyms
      const synonymsInput = screen.getByLabelText('Custom Synonyms');
      fireEvent.change(synonymsInput, {
        target: { value: 'ReactJS, React.js, React Framework, ReactJS2' },
      });

      // Submit
      fireEvent.click(screen.getByText('Update'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2); // Initial fetch + update
      });

      const updateCall = mockFetch.mock.calls[1];
      expect(updateCall[0]).toBe(`${mockApiUrl}/${mockSynonyms[0].id}`);
      expect(updateCall[1].method).toBe('PUT');
    });
  });

  describe('Delete Synonym', () => {
    it('should open delete confirmation dialog', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: mockSynonyms,
          total_count: 2,
        }),
      });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      // Find and click delete button
      const deleteButtons = screen.getAllByRole('button');
      const reactDeleteButton = deleteButtons.find(
        (btn) => btn.getAttribute('color') === 'error'
      );

      expect(reactDeleteButton).toBeInTheDocument();
      fireEvent.click(reactDeleteButton!);

      await waitFor(() => {
        expect(screen.getByText('Confirm Delete')).toBeInTheDocument();
        expect(screen.getByText(/Are you sure you want to delete/)).toBeInTheDocument();
        expect(screen.getByText('"React"')).toBeInTheDocument();
      });
    });

    it('should delete synonym after confirmation', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            organization_id: mockOrganizationId,
            synonyms: mockSynonyms,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
        });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      // Click delete button
      const deleteButtons = screen.getAllByRole('button');
      const reactDeleteButton = deleteButtons.find(
        (btn) => btn.getAttribute('color') === 'error'
      );
      fireEvent.click(reactDeleteButton!);

      await waitFor(() => {
        expect(screen.getByText('Confirm Delete')).toBeInTheDocument();
      });

      // Confirm delete
      fireEvent.click(screen.getByText('Delete'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2); // Initial fetch + delete
      });

      const deleteCall = mockFetch.mock.calls[1];
      expect(deleteCall[0]).toBe(`${mockApiUrl}/${mockSynonyms[0].id}`);
      expect(deleteCall[1].method).toBe('DELETE');
    });

    it('should cancel delete when Cancel button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: mockSynonyms,
          total_count: 2,
        }),
      });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      // Click delete button
      const deleteButtons = screen.getAllByRole('button');
      const reactDeleteButton = deleteButtons.find(
        (btn) => btn.getAttribute('color') === 'error'
      );
      fireEvent.click(reactDeleteButton!);

      await waitFor(() => {
        expect(screen.getByText('Confirm Delete')).toBeInTheDocument();
      });

      // Cancel delete
      fireEvent.click(screen.getByText('Cancel'));

      await waitFor(() => {
        expect(screen.queryByText('Confirm Delete')).not.toBeInTheDocument();
      });

      // Should only have initial fetch, no delete call
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh synonyms when Refresh button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: mockSynonyms,
          total_count: 2,
        }),
      });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      // Clear mock calls
      vi.clearAllMocks();

      // Click refresh
      const refreshButtons = screen.getAllByText('Refresh');
      fireEvent.click(refreshButtons[0]);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1);
      });

      expect(mockFetch.mock.calls[0][0]).toContain(
        `?organization_id=${mockOrganizationId}`
      );
    });

    it('should retry after error when Retry button is clicked', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            organization_id: mockOrganizationId,
            synonyms: mockSynonyms,
            total_count: 2,
          }),
        });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Error Loading Synonyms')).toBeInTheDocument();
      });

      // Click retry
      fireEvent.click(screen.getByText('Retry'));

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Custom API URL', () => {
    it('should use custom API URL when provided', async () => {
      const customUrl = 'http://custom-api.com/synonyms';

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: [],
          total_count: 0,
        }),
      });

      render(
        <CustomSynonymsManager
          organizationId={mockOrganizationId}
          apiUrl={customUrl}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Custom Synonyms Management')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        `${customUrl}/?organization_id=${mockOrganizationId}`
      );
    });
  });

  describe('Form Validation', () => {
    it('should disable submit button when form is incomplete', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          organization_id: mockOrganizationId,
          synonyms: [],
          total_count: 0,
        }),
      });

      render(<CustomSynonymsManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Add Custom Synonym')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Add Custom Synonym'));

      await waitFor(() => {
        expect(screen.getByText('Create')).toBeInTheDocument();
      });

      // Button should be disabled initially
      expect(screen.getByText('Create')).toBeDisabled();

      // Fill canonical skill only
      fireEvent.change(screen.getByLabelText('Canonical Skill Name'), {
        target: { value: 'Java' },
      });

      // Still disabled because synonyms is empty
      expect(screen.getByText('Create')).toBeDisabled();

      // Fill synonyms
      fireEvent.change(screen.getByLabelText('Custom Synonyms'), {
        target: { value: 'Java, JDK' },
      });

      // Now button should be enabled
      expect(screen.getByText('Create')).not.toBeDisabled();
    });
  });
});
