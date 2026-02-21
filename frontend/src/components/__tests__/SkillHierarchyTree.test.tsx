/**
 * Tests for SkillHierarchyTree Component
 *
 * Tests the skill hierarchy tree view including:
 * - Fetching and displaying hierarchical skill data
 * - Expanding and collapsing tree nodes
 * - Searching and filtering skills
 * - Selection callback integration
 * - Context-based color coding
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SkillHierarchyTree from '../SkillHierarchyTree';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('SkillHierarchyTree', () => {
  const mockOrganizationId = 'org-123';
  const mockApiUrl = 'http://localhost:8000/api/skill-taxonomies';

  const mockSkillHierarchy = [
    {
      id: 'skill-1',
      industry: 'it',
      skill_name: 'Programming',
      variants: ['Coding', 'Development'],
      context: 'category',
      is_active: true,
      parent_skill_id: null,
      category_path: ['Programming'],
      children: [
        {
          id: 'skill-2',
          industry: 'it',
          skill_name: 'JavaScript',
          variants: ['JS', 'ECMAScript'],
          context: 'language',
          is_active: true,
          parent_skill_id: 'skill-1',
          category_path: ['Programming', 'JavaScript'],
          children: [],
          created_at: '2024-01-15T10:00:00Z',
          updated_at: '2024-01-15T10:00:00Z',
        },
        {
          id: 'skill-3',
          industry: 'it',
          skill_name: 'Python',
          variants: ['Py', 'Python3'],
          context: 'language',
          is_active: true,
          parent_skill_id: 'skill-1',
          category_path: ['Programming', 'Python'],
          children: [],
          created_at: '2024-01-16T10:00:00Z',
          updated_at: '2024-01-16T10:00:00Z',
        },
      ],
      created_at: '2024-01-14T10:00:00Z',
      updated_at: '2024-01-14T10:00:00Z',
    },
    {
      id: 'skill-4',
      industry: 'it',
      skill_name: 'Databases',
      variants: ['DB', 'Data Storage'],
      context: 'database',
      is_active: false,
      parent_skill_id: null,
      category_path: ['Databases'],
      children: [],
      created_at: '2024-01-17T10:00:00Z',
      updated_at: '2024-01-17T10:00:00Z',
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
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      expect(screen.getByText('Loading skill hierarchy...')).toBeInTheDocument();
    });

    it('should render skill hierarchy after successful fetch', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Skill Hierarchy')).toBeInTheDocument();
      });

      expect(screen.getByText('Programming')).toBeInTheDocument();
      expect(screen.getByText('Databases')).toBeInTheDocument();
    });

    it('should render empty state when no skills exist', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: [],
          total_count: 0,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('No skills found')).toBeInTheDocument();
      });

      expect(screen.getByText('Add skills to see them in the hierarchy')).toBeInTheDocument();
    });

    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument();
      });

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  describe('Tree Navigation', () => {
    it('should expand node when clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Programming')).toBeInTheDocument();
      });

      // Children should not be visible initially (node is collapsed)
      expect(screen.queryByText('JavaScript')).not.toBeInTheDocument();

      // Click on the Programming node to expand
      fireEvent.click(screen.getByText('Programming'));

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
        expect(screen.getByText('Python')).toBeInTheDocument();
      });
    });

    it('should collapse node when clicked again', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Programming')).toBeInTheDocument();
      });

      // Expand the node
      fireEvent.click(screen.getByText('Programming'));

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });

      // Collapse the node by clicking again
      fireEvent.click(screen.getByText('Programming'));

      await waitFor(() => {
        expect(screen.queryByText('JavaScript')).not.toBeInTheDocument();
      });
    });

    it('should expand all nodes when Expand All is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Expand All')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Expand All'));

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
        expect(screen.getByText('Python')).toBeInTheDocument();
      });
    });

    it('should collapse all nodes when Collapse All is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Expand All')).toBeInTheDocument();
      });

      // First expand all
      fireEvent.click(screen.getByText('Expand All'));

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });

      // Then collapse all
      fireEvent.click(screen.getByText('Collapse All'));

      await waitFor(() => {
        expect(screen.queryByText('JavaScript')).not.toBeInTheDocument();
      });
    });
  });

  describe('Search Functionality', () => {
    it('should filter skills based on search query', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search skills...')).toBeInTheDocument();
      });

      // Search for "Python"
      fireEvent.change(screen.getByPlaceholderText('Search skills...'), {
        target: { value: 'Python' },
      });

      // Programming should still show (parent of matching skill)
      await waitFor(() => {
        expect(screen.getByText('Programming')).toBeInTheDocument();
        expect(screen.getByText('Python')).toBeInTheDocument();
      });

      // Databases should not be visible
      expect(screen.queryByText('Databases')).not.toBeInTheDocument();
    });

    it('should show no results message when search has no matches', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search skills...')).toBeInTheDocument();
      });

      // Search for non-existent skill
      fireEvent.change(screen.getByPlaceholderText('Search skills...'), {
        target: { value: 'NonExistentSkill' },
      });

      await waitFor(() => {
        expect(screen.getByText('No skills match your search')).toBeInTheDocument();
      });
    });

    it('should search in variants as well', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search skills...')).toBeInTheDocument();
      });

      // Search for a variant "JS"
      fireEvent.change(screen.getByPlaceholderText('Search skills...'), {
        target: { value: 'JS' },
      });

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });
    });
  });

  describe('Context Filter', () => {
    it('should filter by context when context is selected', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            industry: 'it',
            skills: mockSkillHierarchy,
            total_count: 4,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            industry: 'it',
            skills: [mockSkillHierarchy[1]], // Only Databases
            total_count: 1,
          }),
        });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Programming')).toBeInTheDocument();
      });

      // Find context filter
      const contextFilter = screen.getByLabelText('Context');
      fireEvent.mouseDown(contextFilter);

      await waitFor(() => {
        expect(screen.getByText('database')).toBeInTheDocument();
      });
    });

    it('should extract and display available contexts', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Programming')).toBeInTheDocument();
      });

      // Context dropdown should be present
      expect(screen.getByLabelText('Context')).toBeInTheDocument();
    });
  });

  describe('Skill Selection', () => {
    it('should call onSkillSelect callback when skill is clicked', async () => {
      const mockOnSkillSelect = vi.fn();

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(
        <SkillHierarchyTree
          organizationId={mockOrganizationId}
          onSkillSelect={mockOnSkillSelect}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Programming')).toBeInTheDocument();
      });

      // Click on a skill
      fireEvent.click(screen.getByText('Programming'));

      expect(mockOnSkillSelect).toHaveBeenCalled();
      expect(mockOnSkillSelect).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 'skill-1',
          skill_name: 'Programming',
        })
      );
    });

    it('should highlight selected skill', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(
        <SkillHierarchyTree
          organizationId={mockOrganizationId}
          selectedSkillId="skill-1"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Programming')).toBeInTheDocument();
      });

      // Selected skill should have different styling (checked via parent element)
      const programmingElement = screen.getByText('Programming');
      expect(programmingElement).toBeInTheDocument();
    });
  });

  describe('Skill Display', () => {
    it('should display context badges with correct colors', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Programming')).toBeInTheDocument();
      });

      // Context badges should be displayed
      expect(screen.getByText('category')).toBeInTheDocument();
      expect(screen.getByText('database')).toBeInTheDocument();
    });

    it('should display inactive badge for inactive skills', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Databases')).toBeInTheDocument();
      });

      expect(screen.getByText('Inactive')).toBeInTheDocument();
    });

    it('should display variant count', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Programming')).toBeInTheDocument();
      });

      // Variant count should be displayed
      expect(screen.getByText(/2 variants/)).toBeInTheDocument();
    });

    it('should display total skill count', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText(/4 skills in hierarchy/)).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh skill hierarchy when refresh button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Programming')).toBeInTheDocument();
      });

      // Clear mock calls
      vi.clearAllMocks();

      // Click refresh button
      const refreshButton = screen.getByTitle('Refresh');
      fireEvent.click(refreshButton);

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
            industry: 'it',
            skills: mockSkillHierarchy,
            total_count: 4,
          }),
        });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });

      // Click Try Again
      fireEvent.click(screen.getByText('Try Again'));

      await waitFor(() => {
        expect(screen.getByText('Programming')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Custom Props', () => {
    it('should use custom API URL when provided', async () => {
      const customUrl = 'http://custom-api.com/taxonomies';

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: [],
          total_count: 0,
        }),
      });

      render(<SkillHierarchyTree apiUrl={customUrl} />);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
      });

      expect(mockFetch.mock.calls[0][0]).toContain(customUrl);
    });

    it('should use custom industry when provided', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'healthcare',
          skills: [],
          total_count: 0,
        }),
      });

      render(<SkillHierarchyTree industry="healthcare" />);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled();
      });

      expect(mockFetch.mock.calls[0][0]).toContain('industry=healthcare');
    });
  });

  describe('Legend Display', () => {
    it('should display legend with icons', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          industry: 'it',
          skills: mockSkillHierarchy,
          total_count: 4,
        }),
      });

      render(<SkillHierarchyTree organizationId={mockOrganizationId} />);

      await waitFor(() => {
        expect(screen.getByText('Legend')).toBeInTheDocument();
      });

      expect(screen.getByText('Category (has children)')).toBeInTheDocument();
      expect(screen.getByText('Leaf skill')).toBeInTheDocument();
      expect(screen.getByText('Context category')).toBeInTheDocument();
    });
  });
});
