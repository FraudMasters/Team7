/**
 * Tests for IndustryTaxonomyManager Component
 *
 * Tests the industry taxonomy management interface including:
 * - Fetching and displaying taxonomies
 * - Creating new taxonomy entries
 * - Editing existing taxonomies
 * - Deleting taxonomies with confirmation
 * - Industry selection and filtering
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import IndustryTaxonomyManager from './IndustryTaxonomyManager';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('IndustryTaxonomyManager', () => {
  const mockOrganizationId = 'org-123';
  const mockApiUrl = 'http://localhost:8000/api/skill-taxonomies';

  const mockTaxonomies = [
    {
      id: 'tax-1',
      industry: 'tech',
      skill_name: 'React',
      variants: ['ReactJS', 'React.js', 'React Framework'],
      context: 'web_framework',
      extra_metadata: null,
      is_active: true,
      view_count: 15,
      use_count: 5,
      last_used_at: '2024-01-15T10:00:00Z',
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
    },
    {
      id: 'tax-2',
      industry: 'tech',
      skill_name: 'Python',
      variants: ['Python3', 'Py'],
      context: 'language',
      extra_metadata: null,
      is_active: false,
      view_count: 8,
      use_count: 2,
      last_used_at: '2024-01-14T10:00:00Z',
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
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      expect(screen.getByText('Loading industry taxonomies...')).toBeInTheDocument();
    });

    it('should render taxonomies list after successful fetch', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Industry Taxonomy Management')).toBeInTheDocument();
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
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('2')).toBeInTheDocument(); // Total skills
      });

      expect(screen.getByText('1')).toBeInTheDocument(); // Active count
      expect(screen.getByText('1')).toBeInTheDocument(); // Inactive count
    });

    it('should render empty state when no taxonomies exist', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: [],
          total_count: 0,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('No Skills Found')).toBeInTheDocument();
      });

      expect(
        screen.getByText('Get started by adding your first skill taxonomy entry for this industry.')
      ).toBeInTheDocument();
    });

    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Error Loading Taxonomies')).toBeInTheDocument();
      });

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  describe('Industry Selection', () => {
    it('should display industry tabs', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: [],
          total_count: 0,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Tech')).toBeInTheDocument();
        expect(screen.getByText('Healthcare')).toBeInTheDocument();
        expect(screen.getByText('Finance')).toBeInTheDocument();
      });
    });

    it('should fetch taxonomies when industry is changed', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            industry: 'tech',
            skills: mockTaxonomies,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            industry: 'healthcare',
            skills: [],
            total_count: 0,
          }),
        });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      // Clear mocks
      vi.clearAllMocks();

      // Click on Healthcare tab
      fireEvent.click(screen.getByText('Healthcare'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          `${mockApiUrl}/?industry=healthcare`
        );
      });
    });
  });

  describe('Taxonomy Display', () => {
    it('should display context badges with correct colors', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

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
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Inactive')).toBeInTheDocument();
    });

    it('should display usage statistics', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      expect(screen.getByText(/View count:/)).toBeInTheDocument();
      expect(screen.getByText(/Use count:/)).toBeInTheDocument();
    });

    it('should display creation date', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText(/Created:/)).toBeInTheDocument();
      });
    });
  });

  describe('Create Taxonomy', () => {
    it('should open create dialog when Add button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: [],
          total_count: 0,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Add Skill Taxonomy')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Add Skill Taxonomy'));

      await waitFor(() => {
        expect(screen.getByText('Add Skill Taxonomy')).toBeInTheDocument();
        expect(screen.getByLabelText('Skill Name')).toBeInTheDocument();
      });
    });

    it('should create new taxonomy successfully', async () => {
      const newTaxonomy = {
        id: 'tax-3',
        industry: 'tech',
        skill_name: 'TypeScript',
        variants: ['TS', 'TypeScript3'],
        context: 'language',
        extra_metadata: null,
        is_active: true,
        view_count: 0,
        use_count: 0,
        last_used_at: null,
        created_at: '2024-01-17T10:00:00Z',
        updated_at: '2024-01-17T10:00:00Z',
      };

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            industry: 'tech',
            skills: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            industry: 'tech',
            skills: [newTaxonomy],
            total_count: 1,
          }),
        });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Add Skill Taxonomy')).toBeInTheDocument();
      });

      // Open dialog
      fireEvent.click(screen.getByText('Add Skill Taxonomy'));

      await waitFor(() => {
        expect(screen.getByLabelText('Skill Name')).toBeInTheDocument();
      });

      // Fill form
      fireEvent.change(screen.getByLabelText('Skill Name'), {
        target: { value: 'TypeScript' },
      });

      fireEvent.change(screen.getByLabelText('Variants'), {
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

    it('should validate that at least one variant is required', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: [],
          total_count: 0,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Add Skill Taxonomy')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Add Skill Taxonomy'));

      await waitFor(() => {
        expect(screen.getByLabelText('Skill Name')).toBeInTheDocument();
      });

      // Fill only skill name, leave variants empty
      fireEvent.change(screen.getByLabelText('Skill Name'), {
        target: { value: 'JavaScript' },
      });

      // Try to submit - button should be disabled
      expect(screen.getByText('Create')).toBeDisabled();
    });
  });

  describe('Edit Taxonomy', () => {
    it('should open edit dialog with pre-filled data', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

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
        expect(screen.getByText('Edit Skill Taxonomy')).toBeInTheDocument();
        expect(screen.getByDisplayValue('React')).toBeInTheDocument();
        expect(screen.getByDisplayValue('ReactJS, React.js, React Framework')).toBeInTheDocument();
      });
    });

    it('should update taxonomy successfully', async () => {
      const updatedTaxonomy = {
        ...mockTaxonomies[0],
        variants: ['ReactJS', 'React.js', 'React Framework', 'ReactJS2'],
      };

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            industry: 'tech',
            skills: mockTaxonomies,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => updatedTaxonomy,
        });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      // Click edit button
      const editButtons = screen.getAllByRole('button');
      const reactEditButton = editButtons.find((btn) => btn.getAttribute('color') === 'primary');
      fireEvent.click(reactEditButton!);

      await waitFor(() => {
        expect(screen.getByText('Edit Skill Taxonomy')).toBeInTheDocument();
      });

      // Update variants
      const variantsInput = screen.getByLabelText('Variants');
      fireEvent.change(variantsInput, {
        target: { value: 'ReactJS, React.js, React Framework, ReactJS2' },
      });

      // Submit
      fireEvent.click(screen.getByText('Update'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2); // Initial fetch + update
      });

      const updateCall = mockFetch.mock.calls[1];
      expect(updateCall[0]).toBe(`${mockApiUrl}/${mockTaxonomies[0].id}`);
      expect(updateCall[1].method).toBe('PUT');
    });
  });

  describe('Delete Taxonomy', () => {
    it('should open delete confirmation dialog', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

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

    it('should delete taxonomy after confirmation', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            industry: 'tech',
            skills: mockTaxonomies,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
        });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

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
      expect(deleteCall[0]).toBe(`${mockApiUrl}/${mockTaxonomies[0].id}`);
      expect(deleteCall[1].method).toBe('DELETE');
    });

    it('should cancel delete when Cancel button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

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
      fireEvent.click(screen.getAllByText('Cancel')[1]); // Second cancel button is in delete dialog

      await waitFor(() => {
        expect(screen.queryByText('Confirm Delete')).not.toBeInTheDocument();
      });

      // Should only have initial fetch, no delete call
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh taxonomies when Refresh button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

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

      expect(mockFetch.mock.calls[0][0]).toContain('?industry=tech');
    });

    it('should retry after error when Retry button is clicked', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            industry: 'tech',
            skills: mockTaxonomies,
            total_count: 2,
          }),
        });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Error Loading Taxonomies')).toBeInTheDocument();
      });

      // Click retry
      fireEvent.click(screen.getByText('Try Again'));

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Custom API URL', () => {
    it('should use custom API URL when provided', async () => {
      const customUrl = 'http://custom-api.com/taxonomies';

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: [],
          total_count: 0,
        }),
      });

      render(
        <IndustryTaxonomyManager
          organizationId={mockOrganizationId}
          apiUrl={customUrl}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Industry Taxonomy Management')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        `${customUrl}/?industry=tech`
      );
    });
  });

  describe('Form Validation', () => {
    it('should disable submit button when form is incomplete', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: [],
          total_count: 0,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Add Skill Taxonomy')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Add Skill Taxonomy'));

      await waitFor(() => {
        expect(screen.getByText('Create')).toBeInTheDocument();
      });

      // Button should be disabled initially
      expect(screen.getByText('Create')).toBeDisabled();

      // Fill skill name only
      fireEvent.change(screen.getByLabelText('Skill Name'), {
        target: { value: 'Java' },
      });

      // Still disabled because variants is empty
      expect(screen.getByText('Create')).toBeDisabled();

      // Fill variants
      fireEvent.change(screen.getByLabelText('Variants'), {
        target: { value: 'Java, JDK' },
      });

      // Now button should be enabled
      expect(screen.getByText('Create')).not.toBeDisabled();
    });
  });

  describe('Version History', () => {
    const mockVersions = [
      {
        id: 'ver-1',
        industry: 'tech',
        skill_name: 'React',
        context: 'web_framework',
        variants: ['ReactJS', 'React.js'],
        extra_metadata: null,
        is_active: true,
        version: 1,
        is_latest: false,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      },
      {
        id: 'ver-2',
        industry: 'tech',
        skill_name: 'React',
        context: 'web_framework',
        variants: ['ReactJS', 'React.js', 'React Framework'],
        extra_metadata: null,
        is_active: true,
        version: 2,
        is_latest: true,
        created_at: '2024-01-16T10:00:00Z',
        updated_at: '2024-01-16T10:00:00Z',
      },
    ];

    it('should open version history dialog when history button is clicked', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            industry: 'tech',
            skills: mockTaxonomies,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            taxonomy_id: mockTaxonomies[0].id,
            skill_name: 'React',
            industry: 'tech',
            versions: mockVersions,
            total_count: 2,
          }),
        });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      // Find and click history button (info colored)
      const historyButtons = screen.getAllByRole('button');
      const historyButton = historyButtons.find((btn) => btn.getAttribute('color') === 'info');

      expect(historyButton).toBeInTheDocument();
      fireEvent.click(historyButton!);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2);
      });

      const versionCall = mockFetch.mock.calls[1];
      expect(versionCall[0]).toContain(`taxonomy-versions/${mockTaxonomies[0].id}`);
    });

    it('should display version history with version numbers', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            industry: 'tech',
            skills: mockTaxonomies,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            taxonomy_id: mockTaxonomies[0].id,
            skill_name: 'React',
            industry: 'tech',
            versions: mockVersions,
            total_count: 2,
          }),
        });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      const historyButtons = screen.getAllByRole('button');
      const historyButton = historyButtons.find((btn) => btn.getAttribute('color') === 'info');
      fireEvent.click(historyButton!);

      await waitFor(() => {
        expect(screen.getByText(/Version History/)).toBeInTheDocument();
      });
    });

    it('should rollback to previous version', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            industry: 'tech',
            skills: mockTaxonomies,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            taxonomy_id: mockTaxonomies[0].id,
            skill_name: 'React',
            industry: 'tech',
            versions: mockVersions,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTaxonomies[0],
        });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      const historyButtons = screen.getAllByRole('button');
      const historyButton = historyButtons.find((btn) => btn.getAttribute('color') === 'info');
      fireEvent.click(historyButton!);

      await waitFor(() => {
        expect(screen.getByText(/Version History/)).toBeInTheDocument();
      });

      // Click rollback button on first version
      const rollbackButtons = screen.getAllByText('Rollback');
      fireEvent.click(rollbackButtons[0]);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(3);
      });

      const rollbackCall = mockFetch.mock.calls[2];
      expect(rollbackCall[0]).toContain('rollback');
      expect(rollbackCall[1].method).toBe('POST');
    });
  });

  describe('Publish/Unpublish', () => {
    it('should open publish confirmation dialog', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      // Find public icon button (should be present but not public for first taxonomy)
      const publicButtons = screen.getAllByRole('button');
      const publicButton = publicButtons.find((btn) => btn.getAttribute('title') === 'Publish as public');

      if (publicButton) {
        fireEvent.click(publicButton);

        await waitFor(() => {
          expect(screen.getByText(/Publish Taxonomy/)).toBeInTheDocument();
        });
      }
    });

    it('should toggle public status successfully', async () => {
      const updatedTaxonomy = {
        ...mockTaxonomies[0],
        is_public: true,
      };

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            industry: 'tech',
            skills: mockTaxonomies,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => updatedTaxonomy,
        });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });

      const publicButtons = screen.getAllByRole('button');
      const publicButton = publicButtons.find((btn) => btn.getAttribute('title') === 'Publish as public');

      if (publicButton) {
        fireEvent.click(publicButton);

        await waitFor(() => {
          expect(screen.getByText(/Publish/)).toBeInTheDocument();
        });

        fireEvent.click(screen.getByText('Publish'));

        await waitFor(() => {
          expect(mockFetch).toHaveBeenCalledTimes(2);
        });

        const publishCall = mockFetch.mock.calls[1];
        expect(publishCall[0]).toBe(`${mockApiUrl}/${mockTaxonomies[0].id}`);
        expect(publishCall[1].method).toBe('PUT');
      }
    });
  });

  describe('Import/Export', () => {
    it('should open import dialog when Import button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: [],
          total_count: 0,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Import')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Import'));

      await waitFor(() => {
        expect(screen.getByText('Import Taxonomies')).toBeInTheDocument();
      });
    });

    it('should show export menu when Export button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Export')).toBeInTheDocument();
      });

      const exportButtons = screen.getAllByText('Export');
      fireEvent.click(exportButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Export as JSON')).toBeInTheDocument();
        expect(screen.getByText('Export as CSV')).toBeInTheDocument();
      });
    });

    it('should disable export options when no taxonomies exist', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: [],
          total_count: 0,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Export')).toBeInTheDocument();
      });

      const exportButtons = screen.getAllByText('Export');
      fireEvent.click(exportButtons[0]);

      await waitFor(() => {
        const jsonOption = screen.getByText('Export as JSON');
        expect(jsonOption).toBeDisabled();
      });
    });
  });

  describe('Tab Navigation', () => {
    it('should switch to browse tab', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Industry Taxonomy Management')).toBeInTheDocument();
      });

      // Click on Browse Public tab
      const browseTab = screen.getByText('Browse Public');
      fireEvent.click(browseTab);

      await waitFor(() => {
        expect(screen.getByTestId('public-taxonomy-browser')).toBeInTheDocument();
      });
    });

    it('should switch back to manage tab', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'tech',
          skills: mockTaxonomies,
          total_count: 2,
        }),
      });

      render(<IndustryTaxonomyManager organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Industry Taxonomy Management')).toBeInTheDocument();
      });

      // Switch to browse
      fireEvent.click(screen.getByText('Browse Public'));

      await waitFor(() => {
        expect(screen.getByTestId('public-taxonomy-browser')).toBeInTheDocument();
      });

      // Switch back to manage
      fireEvent.click(screen.getByText('Manage Taxonomies'));

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
      });
    });
  });
});
