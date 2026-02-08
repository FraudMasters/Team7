import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Stack,
  CircularProgress,
  Alert,
  IconButton,
  Menu,
  MenuItem,
  Divider,
  Checkbox,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { useTranslation } from 'react-i18next';
import { candidateTagsClient } from '@/api/candidateTags';
import type {
  CandidateTagResponse,
  CandidateTagListResponse,
  ApiError,
} from '@/types/api';

/**
 * TagFilter Component Props
 */
interface TagFilterProps {
  /** Organization ID for fetching available tags */
  organizationId: string;
  /** Callback when selected tags change */
  onChange?: (selectedTagIds: string[]) => void;
  /** Initially selected tag IDs */
  value?: string[];
  /** Custom size for chips ('small' | 'medium') */
  chipSize?: 'small' | 'medium';
  /** Disable the component */
  disabled?: boolean;
  /** Maximum number of tags that can be selected (0 = unlimited) */
  maxSelections?: number;
  /** Placeholder text when no tags selected */
  placeholder?: string;
}

/**
 * TagFilter Component
 *
 * Multi-select dropdown component for filtering candidates by tags:
 * - Shows available tags with their custom colors
 * - Supports multiple tag selection (OR logic for filtering)
 * - Displays selected tags as removable chips
 * - Provides clear button to remove all filters
 * - Handles loading and error states gracefully
 *
 * @example
 * ```tsx
 * <TagFilter
 *   organizationId="org-uuid"
 *   onChange={(tagIds) => console.log('Selected tags:', tagIds)}
 * />
 *
 * <TagFilter
 *   organizationId="org-uuid"
 *   value={['tag-1', 'tag-2']}
 *   maxSelections={3}
 *   chipSize="small"
 *   onChange={(tagIds) => filterCandidates(tagIds)}
 * />
 * ```
 */
const TagFilter: React.FC<TagFilterProps> = ({
  organizationId,
  onChange,
  value: externalValue = [],
  chipSize = 'small',
  disabled = false,
  maxSelections = 0,
  placeholder = 'Filter by tags...',
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [availableTags, setAvailableTags] = useState<CandidateTagResponse[]>([]);
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>(externalValue);
  const [error, setError] = useState<string | null>(null);
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  /**
   * Fetch available tags for the organization
   */
  const fetchTags = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response: CandidateTagListResponse = await candidateTagsClient.listTags(
        organizationId,
        true, // Only active tags
        undefined
      );

      setAvailableTags(response.tags);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load tags. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  useEffect(() => {
    fetchTags();
  }, [fetchTags]);

  /**
   * Sync internal state with external value prop
   */
  useEffect(() => {
    setSelectedTagIds(externalValue);
  }, [externalValue]);

  /**
   * Notify parent when selection changes
   */
  const notifyChange = useCallback(
    (newSelection: string[]) => {
      setSelectedTagIds(newSelection);
      onChange?.(newSelection);
    },
    [onChange]
  );

  /**
   * Handle tag selection toggle
   */
  const handleToggleTag = useCallback(
    (tagId: string) => {
      const isSelected = selectedTagIds.includes(tagId);

      if (isSelected) {
        // Remove tag from selection
        const newSelection = selectedTagIds.filter((id) => id !== tagId);
        notifyChange(newSelection);
      } else {
        // Check max selections limit
        if (maxSelections > 0 && selectedTagIds.length >= maxSelections) {
          setError(`Maximum ${maxSelections} tags can be selected.`);
          setTimeout(() => setError(null), 3000);
          return;
        }
        // Add tag to selection
        const newSelection = [...selectedTagIds, tagId];
        notifyChange(newSelection);
      }
    },
    [selectedTagIds, maxSelections, notifyChange]
  );

  /**
   * Handle removing a tag from selection
   */
  const handleRemoveTag = useCallback(
    (tagId: string) => {
      const newSelection = selectedTagIds.filter((id) => id !== tagId);
      notifyChange(newSelection);
    },
    [selectedTagIds, notifyChange]
  );

  /**
   * Handle clearing all selections
   */
  const handleClearAll = useCallback(() => {
    notifyChange([]);
  }, [notifyChange]);

  /**
   * Menu handlers
   */
  const handleOpenMenu = useCallback((event: React.MouseEvent<HTMLElement>) => {
    if (!disabled) {
      setAnchorEl(event.currentTarget);
    }
  }, [disabled]);

  const handleCloseMenu = useCallback(() => {
    setAnchorEl(null);
  }, []);

  /**
   * Get tag color with fallback
   */
  const getTagColor = useCallback((tag: CandidateTagResponse): string => {
    if (tag.color) return tag.color;
    // Default colors based on tag order
    const defaultColors = ['#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#6B7280'];
    return defaultColors[(tag.tag_order ?? 0) % defaultColors.length];
  }, []);

  /**
   * Get selected tag objects
   */
  const selectedTags = availableTags.filter((tag) =>
    selectedTagIds.includes(tag.id)
  );

  /**
   * Check if a tag is selected
   */
  const isTagSelected = useCallback(
    (tagId: string) => selectedTagIds.includes(tagId),
    [selectedTagIds]
  );

  /**
   * Check if max selections reached
   */
  const isMaxReached = useCallback(() => {
    return maxSelections > 0 && selectedTagIds.length >= maxSelections;
  }, [maxSelections, selectedTagIds.length]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 1 }}>
        <CircularProgress size={20} />
        <Typography variant="body2" color="secondary">
          {t('tags.loading')}
        </Typography>
      </Box>
    );
  }

  const menuOpen = Boolean(anchorEl);

  return (
    <Box>
      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 1 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Filter Display */}
      <Paper
        variant="outlined"
        sx={{
          p: 2,
          minHeight: 48,
          display: 'flex',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 1,
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.6 : 1,
          ...(menuOpen && {
            borderColor: 'primary.main',
            borderWidth: 2,
          }),
        }}
        onClick={handleOpenMenu}
      >
        {/* Filter Icon */}
        <Icon
          name="filter"
          size={chipSize === 'small' ? 18 : 20}
          color="muted"
          style={{ marginRight: '4px' }}
        />

        {/* Selected Tags or Placeholder */}
        {selectedTags.length === 0 ? (
          <Typography variant="body2" color="secondary">
            {placeholder}
          </Typography>
        ) : (
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {selectedTags.map((tag) => (
              <Chip
                key={tag.id}
                label={tag.tag_name}
                size={chipSize}
                sx={{
                  backgroundColor: getTagColor(tag),
                  color: 'white',
                  fontWeight: 500,
                }}
                title={tag.description || undefined}
                deleteIcon={
                  <Icon
                    name="x"
                    size={chipSize === 'small' ? 14 : 16}
                    onClick={(event: React.MouseEvent) => {
                      event.stopPropagation();
                      handleRemoveTag(tag.id);
                    }}
                  />
                }
                onDelete={() => handleRemoveTag(tag.id)}
              />
            ))}
          </Stack>
        )}

        {/* Clear Button (only when tags selected) */}
        {!disabled && selectedTags.length > 0 && (
          <IconButton
            size="small"
            onClick={(event) => {
              event.stopPropagation();
              handleClearAll();
            }}
            sx={{ ml: 'auto' }}
            title={t('tags.clearAll')}
          >
            <Icon name="x-circle" size={16} color="muted" />
          </IconButton>
        )}

        {/* Dropdown Arrow */}
        {!disabled && (
          <Icon
            name="chevron-down"
            size={16}
            color="muted"
            style={{ marginLeft: '4px', transition: 'transform 0.2s', transform: menuOpen ? 'rotate(180deg)' : 'rotate(0)' }}
          />
        )}
      </Paper>

      {/* Tag Selection Menu */}
      <Menu
        anchorEl={anchorEl}
        open={menuOpen}
        onClose={handleCloseMenu}
        PaperProps={{
          sx: { maxHeight: 300, minWidth: 220 },
        }}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'left',
        }}
      >
        {/* Menu Header */}
        <MenuItem disabled sx={{ opacity: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
            <Typography variant="subtitle2" fontWeight={600}>
              {t('tags.filterBy')}
            </Typography>
            {selectedTags.length > 0 && (
              <Typography variant="caption" color="secondary">
                {selectedTags.length} {selectedTags.length === 1 ? 'selected' : 'selected'}
              </Typography>
            )}
          </Box>
        </MenuItem>
        <Divider />

        {/* Tag Options */}
        {availableTags.map((tag) => {
          const isSelected = isTagSelected(tag.id);
          const isDisabled = !isSelected && isMaxReached();

          return (
            <MenuItem
              key={tag.id}
              onClick={() => !isDisabled && handleToggleTag(tag.id)}
              disabled={isDisabled}
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                py: 0.75,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                <Checkbox
                  checked={isSelected}
                  size="small"
                  disabled={isDisabled}
                  sx={{ p: 0 }}
                />
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: getTagColor(tag),
                    flexShrink: 0,
                  }}
                />
                <Typography variant="body2" sx={{ flex: 1 }}>
                  {tag.tag_name}
                </Typography>
              </Box>
            </MenuItem>
          );
        })}

        {/* No Tags Available */}
        {availableTags.length === 0 && (
          <MenuItem disabled>
            <Typography variant="body2" color="secondary">
              {t('tags.noAvailable')}
            </Typography>
          </MenuItem>
        )}

        {/* Menu Footer */}
        {selectedTags.length > 0 && (
          <>
            <Divider />
            <MenuItem
              onClick={handleClearAll}
              sx={{ justifyContent: 'center' }}
            >
              <Typography variant="body2" color="error">
                {t('tags.clearAll')}
              </Typography>
            </MenuItem>
          </>
        )}
      </Menu>

      {/* Selection Count */}
      {selectedTags.length > 0 && maxSelections > 0 && (
        <Typography variant="caption" color="secondary" sx={{ mt: 1, display: 'block' }}>
          {selectedTags.length} of {maxSelections} selected
        </Typography>
      )}
    </Box>
  );
};

export default TagFilter;
