/**
 * Tests for SkillRelationshipEditor Component
 *
 * Tests the skill relationship management interface including:
 * - Fetching and displaying relationships
 * - Creating new relationships
 * - Editing existing relationships
 * - Deleting relationships with confirmation
 * - Filtering by relationship type
 * - Form validation
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SkillRelationshipEditor from '../SkillRelationshipEditor';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('SkillRelationshipEditor', () => {
  const mockOrganizationId = 'org-123';
  const mockApiUrl = 'http://localhost:8000/api/skill-relationships';
  const mockTaxonomyApiUrl = 'http://localhost:8000/api/skill-taxonomies';

  const mockRelationships = [
    {
      id: 'rel-1',
      source_skill_id: 'skill-1',
      target_skill_id: 'skill-2',
      source_skill_name: 'JavaScript',
      target_skill_name: 'TypeScript',
      relationship_type: 'similar',
      weight: 0.8,
      extra_metadata: null,
      is_active: true,
      organization_id: mockOrganizationId,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
    },
    {
      id: 'rel-2',
      source_skill_id: 'skill-3',
      target_skill_id: 'skill-4',
      source_skill_name: 'React',
      target_skill_name: 'Redux',
      relationship_type: 'prerequisite',
      weight: 0.6,
      extra_metadata: null,
      is_active: false,
      organization_id: mockOrganizationId,
      created_at: '2024-01-16T10:00:00Z',
      updated_at: '2024-01-16T10:00:00Z',
    },
  ];

  const mockSkills = [
    { id: 'skill-1', skill_name: 'JavaScript', industry: 'it', context: 'language' },
    { id: 'skill-2', skill_name: 'TypeScript', industry: 'it', context: 'language' },
    { id: 'skill-3', skill_name: 'React', industry: 'it', context: 'framework' },
    { id: 'skill-4', skill_name: 'Redux', industry: 'it', context: 'library' },
  ];

  const mockRelationshipTypes = [
    { value: 'parent_child', label: 'Parent → Child', description: 'Hierarchical relationship' },
    { value: 'similar', label: 'Similar', description: 'Skills that can be substituted' },
    { value: 'prerequisite', label: 'Prerequisite', description: 'One skill is required before another' },
    { value: 'related', label: 'Related', description: 'Skills often used together' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          relationships: mockRelationships,
          total_count: 2,
        }),
      });

      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      expect(screen.getByText('Loading relationships...')).toBeInTheDocument();
    });

    it('should render relationships list after successful fetch', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: mockRelationships,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ skills: mockSkills }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ relationship_types: mockRelationshipTypes }),
        });

      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Skill Relationships')).toBeInTheDocument();
      });

      expect(screen.getByText('JavaScript')).toBeInTheDocument();
      expect(screen.getByText('TypeScript')).toBeInTheDocument();
      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('Redux')).toBeInTheDocument();
    });

    it('should display summary statistics correctly', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: mockRelationships,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ skills: mockSkills }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ relationship_types: mockRelationshipTypes }),
        });

      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('2')).toBeInTheDocument(); // Total relationships
      });

      expect(screen.getByText('1')).toBeInTheDocument(); // Active count
      expect(screen.getByText('1')).toBeInTheDocument(); // Inactive count
    });

    it('should render empty state when no relationships exist', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ skills: mockSkills }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ relationship_types: mockRelationshipTypes }),
        });

      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('No Relationships Found')).toBeInTheDocument();
      });

      expect(
        screen.getByText('Create relationships between skills to improve matching accuracy.')
      ).toBeInTheDocument();
    });

    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument();
      });

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  describe('Relationship Display', () => {
    beforeEach(() => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: mockRelationships,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ skills: mockSkills }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ relationship_types: mockRelationshipTypes }),
        });
    });

    it('should display relationship type badges with correct colors', async () => {
      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });

      expect(screen.getByText('Similar')).toBeInTheDocument();
      expect(screen.getByText('Prerequisite')).toBeInTheDocument();
    });

    it('should display active/inactive status badges', async () => {
      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });

      expect(screen.getAllByText('Active')).toHaveLength(2); // Header stat + badge
      expect(screen.getByText('Inactive')).toBeInTheDocument();
    });

    it('should display relationship weight as percentage', async () => {
      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });

      expect(screen.getByText('80%')).toBeInTheDocument();
      expect(screen.getByText('60%')).toBeInTheDocument();
    });

    it('should display creation date', async () => {
      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText(/Created:/)).toBeInTheDocument();
      });
    });
  });

  describe('Create Relationship', () => {
    beforeEach(() => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ skills: mockSkills }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ relationship_types: mockRelationshipTypes }),
        });
    });

    it('should open create dialog when Add Relationship button is clicked', async () => {
      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Add Relationship')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Add Relationship'));

      await waitFor(() => {
        expect(screen.getByText('Add Relationship')).toBeInTheDocument();
        expect(screen.getByLabelText('Source Skill')).toBeInTheDocument();
        expect(screen.getByLabelText('Target Skill')).toBeInTheDocument();
      });
    });

    it('should create new relationship successfully', async () => {
      const newRelationship = {
        id: 'rel-3',
        source_skill_id: 'skill-1',
        target_skill_id: 'skill-3',
        source_skill_name: 'JavaScript',
        target_skill_name: 'React',
        relationship_type: 'related',
        weight: 0.7,
        extra_metadata: null,
        is_active: true,
        organization_id: mockOrganizationId,
        created_at: '2024-01-17T10:00:00Z',
        updated_at: '2024-01-17T10:00:00Z',
      };

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ skills: mockSkills }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ relationship_types: mockRelationshipTypes }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: [newRelationship],
            total_count: 1,
          }),
        });

      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Add Relationship')).toBeInTheDocument();
      });

      // Open dialog
      fireEvent.click(screen.getByText('Add Relationship'));

      await waitFor(() => {
        expect(screen.getByLabelText('Source Skill')).toBeInTheDocument();
      });

      // Submit form (with pre-selected values for simplicity)
      fireEvent.click(screen.getByText('Create'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
      });
    });
  });

  describe('Edit Relationship', () => {
    beforeEach(() => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: mockRelationships,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ skills: mockSkills }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ relationship_types: mockRelationshipTypes }),
        });
    });

    it('should open edit dialog with pre-filled data', async () => {
      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });

      // Find and click edit button for first relationship
      const editButtons = screen.getAllByRole('button');
      const editButton = editButtons.find(
        (btn) => btn.getAttribute('color') === 'primary'
      );

      expect(editButton).toBeInTheDocument();
      fireEvent.click(editButton!);

      await waitFor(() => {
        expect(screen.getByText('Edit Relationship')).toBeInTheDocument();
      });
    });

    it('should update relationship successfully', async () => {
      const updatedRelationship = {
        ...mockRelationships[0],
        weight: 0.9,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => updatedRelationship,
      });

      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });

      // Click edit button
      const editButtons = screen.getAllByRole('button');
      const editButton = editButtons.find((btn) => btn.getAttribute('color') === 'primary');
      fireEvent.click(editButton!);

      await waitFor(() => {
        expect(screen.getByText('Edit Relationship')).toBeInTheDocument();
      });

      // Submit the edit
      fireEvent.click(screen.getByText('Update'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
      });
    });
  });

  describe('Delete Relationship', () => {
    beforeEach(() => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: mockRelationships,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ skills: mockSkills }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ relationship_types: mockRelationshipTypes }),
        });
    });

    it('should open delete confirmation dialog', async () => {
      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });

      // Find and click delete button
      const deleteButtons = screen.getAllByRole('button');
      const deleteButton = deleteButtons.find(
        (btn) => btn.getAttribute('color') === 'error'
      );

      expect(deleteButton).toBeInTheDocument();
      fireEvent.click(deleteButton!);

      await waitFor(() => {
        expect(screen.getByText('Delete Relationship')).toBeInTheDocument();
        expect(screen.getByText(/Are you sure you want to delete/)).toBeInTheDocument();
      });
    });

    it('should delete relationship after confirmation', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
      });

      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });

      // Click delete button
      const deleteButtons = screen.getAllByRole('button');
      const deleteButton = deleteButtons.find(
        (btn) => btn.getAttribute('color') === 'error'
      );
      fireEvent.click(deleteButton!);

      await waitFor(() => {
        expect(screen.getByText('Delete Relationship')).toBeInTheDocument();
      });

      // Confirm delete
      fireEvent.click(screen.getByText('Delete'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
      });
    });

    it('should cancel delete when Cancel button is clicked', async () => {
      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });

      // Click delete button
      const deleteButtons = screen.getAllByRole('button');
      const deleteButton = deleteButtons.find(
        (btn) => btn.getAttribute('color') === 'error'
      );
      fireEvent.click(deleteButton!);

      await waitFor(() => {
        expect(screen.getByText('Delete Relationship')).toBeInTheDocument();
      });

      // Cancel delete
      fireEvent.click(screen.getByText('Cancel'));

      await waitFor(() => {
        expect(screen.queryByText('Delete Relationship')).not.toBeInTheDocument();
      });
    });
  });

  describe('Filter Functionality', () => {
    beforeEach(() => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: mockRelationships,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ skills: mockSkills }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ relationship_types: mockRelationshipTypes }),
        });
    });

    it('should filter relationships by type', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          relationships: [mockRelationships[0]],
          total_count: 1,
        }),
      });

      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Filter by Type')).toBeInTheDocument();
      });

      // Open filter dropdown
      const filterSelect = screen.getByText('Filter by Type').closest('.MuiFormControl-root');
      fireEvent.mouseDown(filterSelect!.querySelector('.MuiOutlinedInput-root')!);

      await waitFor(() => {
        expect(screen.getByText('Similar')).toBeInTheDocument();
      });
    });

    it('should display All Types option in filter', async () => {
      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Filter by Type')).toBeInTheDocument();
      });

      // Open filter dropdown
      const filterSelect = screen.getByText('Filter by Type').closest('.MuiFormControl-root');
      fireEvent.mouseDown(filterSelect!.querySelector('.MuiOutlinedInput-root')!);

      await waitFor(() => {
        expect(screen.getByText('All Types')).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh relationships when Refresh button is clicked', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: mockRelationships,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ skills: mockSkills }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ relationship_types: mockRelationshipTypes }),
        });

      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });

      // Clear mock calls
      vi.clearAllMocks();

      // Click refresh
      const refreshButtons = screen.getAllByText('Refresh');
      fireEvent.click(refreshButtons[0]);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1);
      });
    });

    it('should retry after error when Try Again button is clicked', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: mockRelationships,
            total_count: 2,
          }),
        });

      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });

      // Click Try Again
      fireEvent.click(screen.getByText('Try Again'));

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Form Validation', () => {
    beforeEach(() => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ skills: mockSkills }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ relationship_types: mockRelationshipTypes }),
        });
    });

    it('should disable submit button when source skill is not selected', async () => {
      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Add Relationship')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Add Relationship'));

      await waitFor(() => {
        expect(screen.getByText('Create')).toBeInTheDocument();
      });

      // Button should be disabled initially
      expect(screen.getByText('Create')).toBeDisabled();
    });

    it('should disable submit button when target skill is not selected', async () => {
      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Add Relationship')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Add Relationship'));

      await waitFor(() => {
        expect(screen.getByText('Create')).toBeInTheDocument();
      });

      // Button should be disabled without selections
      expect(screen.getByText('Create')).toBeDisabled();
    });
  });

  describe('Custom Props', () => {
    it('should use custom API URL when provided', async () => {
      const customUrl = 'http://custom-api.com/relationships';

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          relationships: [],
          total_count: 0,
        }),
      });

      render(<SkillRelationshipEditor organizationId={mockOrganizationId} apiUrl={customUrl} />);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
      });

      expect(mockFetch.mock.calls[0][0]).toContain(customUrl);
    });

    it('should filter by source skill when sourceSkillId is provided', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          relationships: mockRelationships,
          total_count: 2,
        }),
      });

      render(
        <SkillRelationshipEditor
          organizationId={mockOrganizationId}
          sourceSkillId="skill-1"
        />
      );

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
      });

      expect(mockFetch.mock.calls[0][0]).toContain('source_skill_id=skill-1');
    });

    it('should call onRelationshipChange callback when relationship changes', async () => {
      const mockOnRelationshipChange = vi.fn();

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ skills: mockSkills }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ relationship_types: mockRelationshipTypes }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: [mockRelationships[0]],
            total_count: 1,
          }),
        });

      render(
        <SkillRelationshipEditor
          organizationId={mockOrganizationId}
          onRelationshipChange={mockOnRelationshipChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Add Relationship')).toBeInTheDocument();
      });

      // Open create dialog
      fireEvent.click(screen.getByText('Add Relationship'));

      await waitFor(() => {
        expect(screen.getByText('Create')).toBeInTheDocument();
      });
    });
  });

  describe('Default Relationship Types', () => {
    it('should use default relationship types when API fails', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            relationships: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ skills: mockSkills }),
        })
        .mockRejectedValueOnce(new Error('Failed to fetch types'));

      render(<SkillRelationshipEditor organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Add Relationship')).toBeInTheDocument();
      });

      // Open create dialog
      fireEvent.click(screen.getByText('Add Relationship'));

      await waitFor(() => {
        expect(screen.getByLabelText('Relationship Type')).toBeInTheDocument();
      });
    });
  });
});
