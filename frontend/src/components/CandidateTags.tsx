import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  TextField,
  Button,
  Stack,
  CircularProgress,
  Alert,
  IconButton,
  Menu,
  MenuItem,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Close as CloseIcon,
  Label as LabelIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { candidateTagsClient } from '@/api/candidateTags';
import type {
  CandidateTagResponse,
  CandidateTagsResponse,
  ApiError,
} from '@/types/api';

/**
 * CandidateTags Component Props
 */
interface CandidateTagsProps {
  /** Resume ID for the candidate */
  resumeId: string;
  /** Organization ID for fetching available tags */
  organizationId: string;
  /** Whether the component is read-only (no add/remove) */
  readOnly?: boolean;
  /** Callback when tags change */
  onTagsChange?: (tags: CandidateTagResponse[]) => void;
  /** Maximum number of tags allowed (0 = unlimited) */
  maxTags?: number;
  /** Custom size for chips ('small' | 'medium') */
  chipSize?: 'small' | 'medium';
  /** Show tag count */
  showCount?: boolean;
}

/**
 * CandidateTags Component
 *
 * Displays candidate tags as color-coded chips with add/remove functionality:
 * - Shows currently assigned tags with custom colors
 * - Allows adding new tags from available organization tags
 * - Supports removing tags with confirmation
 * - Provides read-only mode for display-only scenarios
 * - Handles loading and error states gracefully
 *
 * @example
 * ```tsx
 * <CandidateTags
 *   resumeId="resume-uuid"
 *   organizationId="org-uuid"
 *   onTagsChange={(tags) => console.log('Tags updated:', tags)}
 * />
 *
 * <CandidateTags
 *   resumeId="resume-uuid"
 *   organizationId="org-uuid"
 *   readOnly
 *   chipSize="small"
 * />
 * ```
 */
const CandidateTags: React.FC<CandidateTagsProps> = ({
  resumeId,
  organizationId,
  readOnly = false,
  onTagsChange,
  maxTags = 0,
  chipSize = 'small',
  showCount = true,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [assignedTags, setAssignedTags] = useState<CandidateTagResponse[]>([]);
  const [availableTags, setAvailableTags] = useState<CandidateTagResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [assigning, setAssigning] = useState<string | null>(null);
  const [removing, setRemoving] = useState<string | null>(null);

  /**
   * Fetch assigned tags and available tags
   */
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch assigned tags for this resume
      const assignedResponse: CandidateTagsResponse = await candidateTagsClient.getResumeTags(resumeId);

      // Fetch available tags for the organization
      const availableResponse = await candidateTagsClient.listTags(organizationId, true);

      setAssignedTags(assignedResponse.tags);
      setAvailableTags(
        availableResponse.tags.filter(
          (tag) => !assignedResponse.tags.some((assigned) => assigned.id === tag.id)
        )
      );
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load tags. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [resumeId, organizationId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  /**
   * Handle adding a tag to the candidate
   */
  const handleAddTag = useCallback(
    async (tag: CandidateTagResponse) => {
      if (maxTags > 0 && assignedTags.length >= maxTags) {
        setError(`Maximum ${maxTags} tags allowed.`);
        return;
      }

      try {
        setAssigning(tag.id);
        setError(null);

        await candidateTagsClient.assignTagToResume(resumeId, {
          tag_id: tag.id,
        });

        // Refresh data
        await fetchData();

        setSuccessMessage(`Tag "${tag.tag_name}" added successfully.`);
        setTimeout(() => setSuccessMessage(null), 3000);

        handleCloseMenu();
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to add tag. Please try again.');
      } finally {
        setAssigning(null);
      }
    },
    [resumeId, assignedTags.length, maxTags, fetchData]
  );

  /**
   * Handle removing a tag from the candidate
   */
  const handleRemoveTag = useCallback(
    async (tagId: string, tagName: string) => {
      try {
        setRemoving(tagId);
        setError(null);

        await candidateTagsClient.removeTagFromResume(resumeId, tagId);

        // Refresh data
        await fetchData();

        setSuccessMessage(`Tag "${tagName}" removed successfully.`);
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to remove tag. Please try again.');
      } finally {
        setRemoving(null);
      }
    },
    [resumeId, fetchData]
  );

  /**
   * Notify parent when tags change
   */
  useEffect(() => {
    onTagsChange?.(assignedTags);
  }, [assignedTags, onTagsChange]);

  /**
   * Menu handlers
   */
  const handleOpenMenu = useCallback((event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  }, []);

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
   * Check if tag can be added
   */
  const canAddTag = useCallback(() => {
    if (readOnly) return false;
    if (maxTags > 0 && assignedTags.length >= maxTags) return false;
    return availableTags.length > 0;
  }, [readOnly, maxTags, assignedTags.length, availableTags.length]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 1 }}>
        <CircularProgress size={20} />
        <Typography variant="body2" color="text.secondary">
          {t('tags.loading')}
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 1 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Success Message */}
      {successMessage && (
        <Alert
          severity="success"
          sx={{ mb: 1 }}
          icon={<CheckCircleIcon fontSize="inherit" />}
          onClose={() => setSuccessMessage(null)}
        >
          {successMessage}
        </Alert>
      )}

      {/* Tags Display */}
      <Paper
        variant="outlined"
        sx={{
          p: 2,
          minHeight: 60,
          display: 'flex',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 1,
        }}
      >
        {/* Label Icon */}
        <LabelIcon
          sx={{
            color: 'text.secondary',
            fontSize: chipSize === 'small' ? 20 : 24,
            mr: 0.5,
          }}
        />

        {/* Assigned Tags */}
        {assignedTags.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            {t('tags.noTags')}
          </Typography>
        ) : (
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {assignedTags.map((tag) => (
              <Chip
                key={tag.id}
                label={tag.tag_name}
                size={chipSize}
                sx={{
                  backgroundColor: getTagColor(tag),
                  color: 'white',
                  fontWeight: 500,
                  ...(removing === tag.id && {
                    opacity: 0.5,
                    pointerEvents: 'none',
                  }),
                }}
                title={tag.description || undefined}
                onDelete={
                  readOnly
                    ? undefined
                    : () => handleRemoveTag(tag.id, tag.tag_name)
                }
                deleteIcon={
                  removing === tag.id ? (
                    <CircularProgress size={14} sx={{ color: 'white' }} />
                  ) : (
                    <CloseIcon sx={{ fontSize: chipSize === 'small' ? 16 : 18 }} />
                  )
                }
              />
            ))}
          </Stack>
        )}

        {/* Add Tag Button */}
        {!readOnly && canAddTag() && (
          <>
            <Button
              size="small"
              startIcon={<AddIcon />}
              onClick={handleOpenMenu}
              sx={{ ml: 'auto' }}
              disabled={maxTags > 0 && assignedTags.length >= maxTags}
            >
              {t('tags.add')}
            </Button>

            {/* Available Tags Menu */}
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleCloseMenu}
              PaperProps={{
                sx: { maxHeight: 300, minWidth: 200 },
              }}
            >
              <MenuItem disabled sx={{ opacity: 1 }}>
                <Typography variant="subtitle2" fontWeight={600}>
                  {t('tags.available')}
                </Typography>
              </MenuItem>
              <Divider />
              {availableTags.map((tag) => (
                <MenuItem
                  key={tag.id}
                  onClick={() => handleAddTag(tag)}
                  disabled={assigning === tag.id}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        backgroundColor: getTagColor(tag),
                      }}
                    />
                    <Typography variant="body2">{tag.tag_name}</Typography>
                  </Box>
                  {assigning === tag.id && (
                    <CircularProgress size={16} sx={{ ml: 1 }} />
                  )}
                </MenuItem>
              ))}
              {availableTags.length === 0 && (
                <MenuItem disabled>
                  <Typography variant="body2" color="text.secondary">
                    {t('tags.noAvailable')}
                  </Typography>
                </MenuItem>
              )}
            </Menu>
          </>
        )}

        {/* Tag Count */}
        {showCount && assignedTags.length > 0 && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ ml: 'auto', pl: 1 }}
          >
            {assignedTags.length} {assignedTags.length === 1 ? 'tag' : 'tags'}
          </Typography>
        )}
      </Paper>

      {/* Tag Limit Warning */}
      {maxTags > 0 && assignedTags.length >= maxTags && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          {t('tags.maxReached', { max: maxTags })}
        </Typography>
      )}
    </Box>
  );
};

export default CandidateTags;
