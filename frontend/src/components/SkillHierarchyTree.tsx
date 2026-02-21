import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { config } from '@/config';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Alert,
  AlertTitle,
  Stack,
  CircularProgress,
  Button,
  IconButton,
  TextField,
  InputAdornment,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  MenuItem,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Folder as FolderIcon,
  Label as LabelIcon,
  FilterList as FilterListIcon,
} from '@mui/icons-material';

/**
 * Skill taxonomy node in the hierarchy tree
 */
interface SkillTaxonomyNode {
  id: string;
  industry: string;
  skill_name: string;
  variants: string[];
  context?: string;
  extra_metadata?: Record<string, unknown>;
  is_active: boolean;
  parent_skill_id?: string;
  category_path: string[];
  children?: SkillTaxonomyNode[];
  created_at: string;
  updated_at: string;
}

/**
 * List response from backend with hierarchy support
 */
interface SkillHierarchyResponse {
  industry: string;
  skills: SkillTaxonomyNode[];
  total_count: number;
  filters?: {
    context?: string;
    parent_id?: string;
    root_only?: boolean;
    include_children?: boolean;
  };
}

/**
 * SkillHierarchyTree component props
 */
interface SkillHierarchyTreeProps {
  /** Organization ID to fetch taxonomies for */
  organizationId?: string;
  /** API endpoint URL for skill taxonomies */
  apiUrl?: string;
  /** Industry filter */
  industry?: string;
  /** Callback when a skill is selected */
  onSkillSelect?: (skill: SkillTaxonomyNode) => void;
  /** Selected skill ID */
  selectedSkillId?: string;
}

/**
 * Get context color for display
 */
const getContextColor = (context?: string): 'primary' | 'success' | 'warning' | 'info' | 'default' => {
  switch (context) {
    case 'web_framework':
      return 'primary';
    case 'language':
    case 'programming_language':
      return 'success';
    case 'database':
      return 'warning';
    case 'tool':
    case 'devops':
      return 'info';
    default:
      return 'default';
  }
};

/**
 * SkillTreeItem - Recursive tree item component
 */
interface SkillTreeItemProps {
  skill: SkillTaxonomyNode;
  level: number;
  selectedSkillId?: string;
  expandedNodes: Set<string>;
  onToggleExpand: (nodeId: string) => void;
  onSelect: (skill: SkillTaxonomyNode) => void;
}

const SkillTreeItem: React.FC<SkillTreeItemProps> = ({
  skill,
  level,
  selectedSkillId,
  expandedNodes,
  onToggleExpand,
  onSelect,
}) => {
  const hasChildren = skill.children && skill.children.length > 0;
  const isExpanded = expandedNodes.has(skill.id);
  const isSelected = skill.id === selectedSkillId;

  const handleClick = () => {
    if (hasChildren) {
      onToggleExpand(skill.id);
    }
    onSelect(skill);
  };

  return (
    <>
      <ListItem
        disablePadding
        sx={{
          pl: level * 2,
          bgcolor: isSelected ? 'action.selected' : 'transparent',
          borderLeft: level > 0 ? '1px dashed' : 'none',
          borderColor: 'divider',
          '&:hover': {
            bgcolor: 'action.hover',
          },
        }}
      >
        <ListItemButton
          onClick={handleClick}
          dense
          sx={{
            py: 0.5,
          }}
        >
          <ListItemIcon sx={{ minWidth: 28 }}>
            {hasChildren ? (
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleExpand(skill.id);
                }}
                sx={{ p: 0.5 }}
              >
                {isExpanded ? (
                  <ExpandMoreIcon fontSize="small" />
                ) : (
                  <ChevronRightIcon fontSize="small" />
                )}
              </IconButton>
            ) : (
              <LabelIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
            )}
          </ListItemIcon>
          <ListItemText
            primary={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {hasChildren && (
                  <FolderIcon sx={{ fontSize: 16, color: 'primary.main' }} />
                )}
                <Typography
                  variant="body2"
                  fontWeight={skill.is_active ? 500 : 400}
                  sx={{
                    textDecoration: skill.is_active ? 'none' : 'line-through',
                    opacity: skill.is_active ? 1 : 0.7,
                  }}
                >
                  {skill.skill_name}
                </Typography>
                {skill.context && (
                  <Chip
                    label={skill.context}
                    size="small"
                    color={getContextColor(skill.context)}
                    variant="outlined"
                    sx={{ fontSize: 10, height: 18 }}
                  />
                )}
                {!skill.is_active && (
                  <Chip
                    label="Inactive"
                    size="small"
                    color="default"
                    variant="filled"
                    sx={{ fontSize: 10, height: 18 }}
                  />
                )}
                {skill.variants.length > 0 && (
                  <Typography variant="caption" color="text.secondary">
                    ({skill.variants.length} variants)
                  </Typography>
                )}
              </Box>
            }
          />
        </ListItemButton>
      </ListItem>

      {/* Render children */}
      {hasChildren && (
        <Collapse in={isExpanded} timeout="auto" unmountOnExit>
          <List disablePadding>
            {skill.children!.map((child) => (
              <SkillTreeItem
                key={child.id}
                skill={child}
                level={level + 1}
                selectedSkillId={selectedSkillId}
                expandedNodes={expandedNodes}
                onToggleExpand={onToggleExpand}
                onSelect={onSelect}
              />
            ))}
          </List>
        </Collapse>
      )}
    </>
  );
};

/**
 * SkillHierarchyTree Component
 *
 * Provides a tree view for visualizing skill categories in a hierarchical structure.
 * Features include:
 * - Collapsible tree structure for skill categories
 * - Search/filter functionality
 * - Context-based color coding
 * - Lazy loading of child skills
 * - Selection callback for integration with other components
 *
 * @example
 * ```tsx
 * <SkillHierarchyTree
 *   industry="it"
 *   onSkillSelect={(skill) => console.log('Selected:', skill.skill_name)}
 * />
 * ```
 */
const SkillHierarchyTree: React.FC<SkillHierarchyTreeProps> = ({
  organizationId = 'default',
  apiUrl = `${config.api.url}/api/skill-taxonomies`,
  industry = 'it',
  onSkillSelect,
  selectedSkillId,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [skills, setSkills] = useState<SkillTaxonomyNode[]>([]);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [contextFilter, setContextFilter] = useState<string>('');
  const [availableContexts, setAvailableContexts] = useState<string[]>([]);

  /**
   * Fetch skill hierarchy from backend
   */
  const fetchSkillHierarchy = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        include_children: 'true',
        root_only: 'true',
      });

      if (industry) {
        params.append('industry', industry);
      }

      if (contextFilter) {
        params.append('context', contextFilter);
      }

      const response = await fetch(`${apiUrl}/?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch skill hierarchy: ${response.statusText}`);
      }

      const result: SkillHierarchyResponse = await response.json();
      setSkills(result.skills || []);

      // Extract unique contexts from skills
      const contexts = new Set<string>();
      const extractContexts = (skillList: SkillTaxonomyNode[]) => {
        skillList.forEach((skill) => {
          if (skill.context) {
            contexts.add(skill.context);
          }
          if (skill.children) {
            extractContexts(skill.children);
          }
        });
      };
      extractContexts(result.skills || []);
      setAvailableContexts(Array.from(contexts).sort());
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('skillHierarchy.errors.failedToLoad', 'Failed to load skill hierarchy');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [apiUrl, industry, contextFilter, t]);

  useEffect(() => {
    fetchSkillHierarchy();
  }, [fetchSkillHierarchy]);

  /**
   * Filter skills based on search query
   */
  const filterSkills = useCallback(
    (skillList: SkillTaxonomyNode[]): SkillTaxonomyNode[] => {
      if (!searchQuery.trim()) {
        return skillList;
      }

      const query = searchQuery.toLowerCase();
      return skillList
        .map((skill) => {
          const matchesSelf =
            skill.skill_name.toLowerCase().includes(query) ||
            skill.variants.some((v) => v.toLowerCase().includes(query)) ||
            (skill.context && skill.context.toLowerCase().includes(query));

          const filteredChildren = skill.children ? filterSkills(skill.children) : [];

          if (matchesSelf || filteredChildren.length > 0) {
            return {
              ...skill,
              children: filteredChildren.length > 0 ? filteredChildren : skill.children,
            };
          }

          return null;
        })
        .filter((skill): skill is SkillTaxonomyNode => skill !== null);
    },
    [searchQuery]
  );

  /**
   * Handle node toggle
   */
  const handleToggleExpand = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  }, []);

  /**
   * Handle skill selection
   */
  const handleSelect = useCallback(
    (skill: SkillTaxonomyNode) => {
      if (onSkillSelect) {
        onSkillSelect(skill);
      }
    },
    [onSkillSelect]
  );

  /**
   * Expand all nodes
   */
  const handleExpandAll = useCallback(() => {
    const getAllNodeIds = (skillList: SkillTaxonomyNode[]): string[] => {
      const ids: string[] = [];
      skillList.forEach((skill) => {
        if (skill.children && skill.children.length > 0) {
          ids.push(skill.id);
          ids.push(...getAllNodeIds(skill.children));
        }
      });
      return ids;
    };
    setExpandedNodes(new Set(getAllNodeIds(skills)));
  }, [skills]);

  /**
   * Collapse all nodes
   */
  const handleCollapseAll = useCallback(() => {
    setExpandedNodes(new Set());
  }, []);

  /**
   * Count total skills in tree
   */
  const countSkills = (skillList: SkillTaxonomyNode[]): number => {
    return skillList.reduce((count, skill) => {
      const childCount = skill.children ? countSkills(skill.children) : 0;
      return count + 1 + childCount;
    }, 0);
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 8,
        }}
      >
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6" color="text.secondary">
          {t('skillHierarchy.loading', 'Loading skill hierarchy...')}
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" onClick={fetchSkillHierarchy} startIcon={<RefreshIcon />}>
            {t('common.tryAgain', 'Try Again')}
          </Button>
        }
      >
        <AlertTitle>{t('skillHierarchy.errorTitle', 'Error')}</AlertTitle>
        {error}
      </Alert>
    );
  }

  const filteredSkills = filterSkills(skills);
  const totalSkills = countSkills(skills);
  const filteredCount = countSkills(filteredSkills);

  return (
    <Stack spacing={2}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            {t('skillHierarchy.title', 'Skill Hierarchy')}
          </Typography>
          <Stack direction="row" spacing={1}>
            <Button size="small" onClick={handleExpandAll} disabled={skills.length === 0}>
              {t('skillHierarchy.expandAll', 'Expand All')}
            </Button>
            <Button size="small" onClick={handleCollapseAll} disabled={expandedNodes.size === 0}>
              {t('skillHierarchy.collapseAll', 'Collapse All')}
            </Button>
            <IconButton size="small" onClick={fetchSkillHierarchy} title={t('skillHierarchy.refresh', 'Refresh')}>
              <RefreshIcon />
            </IconButton>
          </Stack>
        </Box>

        {/* Search and Filter */}
        <Stack direction="row" spacing={2}>
          <TextField
            size="small"
            placeholder={t('skillHierarchy.searchPlaceholder', 'Search skills...')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            sx={{ flexGrow: 1 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
          {availableContexts.length > 0 && (
            <TextField
              select
              size="small"
              label={t('skillHierarchy.filterByContext', 'Context')}
              value={contextFilter}
              onChange={(e) => setContextFilter(e.target.value)}
              sx={{ minWidth: 150 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <FilterListIcon fontSize="small" />
                  </InputAdornment>
                ),
              }}
            >
              <MenuItem value="">{t('skillHierarchy.allContexts', 'All')}</MenuItem>
              {availableContexts.map((context) => (
                <MenuItem key={context} value={context}>
                  {context}
                </MenuItem>
              ))}
            </TextField>
          )}
        </Stack>

        {/* Statistics */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary">
            {searchQuery || contextFilter
              ? t('skillHierarchy.filteredCount', 'Showing {{count}} of {{total}} skills', {
                  count: filteredCount,
                  total: totalSkills,
                })
              : t('skillHierarchy.totalCount', '{{count}} skills in hierarchy', { count: totalSkills })}
          </Typography>
        </Box>
      </Paper>

      {/* Tree View */}
      <Paper elevation={1} sx={{ maxHeight: 500, overflow: 'auto' }}>
        {filteredSkills.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4, px: 2 }}>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              {searchQuery
                ? t('skillHierarchy.noSearchResults', 'No skills match your search')
                : t('skillHierarchy.noSkills', 'No skills found')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {searchQuery
                ? t('skillHierarchy.tryDifferentSearch', 'Try a different search term')
                : t('skillHierarchy.addSkillsPrompt', 'Add skills to see them in the hierarchy')}
            </Typography>
          </Box>
        ) : (
          <List disablePadding>
            {filteredSkills.map((skill) => (
              <SkillTreeItem
                key={skill.id}
                skill={skill}
                level={0}
                selectedSkillId={selectedSkillId}
                expandedNodes={expandedNodes}
                onToggleExpand={handleToggleExpand}
                onSelect={handleSelect}
              />
            ))}
          </List>
        )}
      </Paper>

      {/* Legend */}
      <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
        <Typography variant="caption" color="text.secondary" gutterBottom display="block">
          {t('skillHierarchy.legend', 'Legend')}
        </Typography>
        <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
          <Stack direction="row" alignItems="center" spacing={0.5}>
            <FolderIcon sx={{ fontSize: 16, color: 'primary.main' }} />
            <Typography variant="caption" color="text.secondary">
              {t('skillHierarchy.categoryWithChildren', 'Category (has children)')}
            </Typography>
          </Stack>
          <Stack direction="row" alignItems="center" spacing={0.5}>
            <LabelIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              {t('skillHierarchy.leafSkill', 'Leaf skill')}
            </Typography>
          </Stack>
          <Stack direction="row" alignItems="center" spacing={0.5}>
            <Chip size="small" label="context" sx={{ fontSize: 10, height: 18 }} />
            <Typography variant="caption" color="text.secondary">
              {t('skillHierarchy.contextLabel', 'Context category')}
            </Typography>
          </Stack>
        </Stack>
      </Paper>
    </Stack>
  );
};

export default SkillHierarchyTree;
