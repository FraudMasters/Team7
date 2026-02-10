/**
 * Candidate Tags Manager Component
 *
 * Manage tags for candidates with color coding and assignment capabilities.
 */

import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  IconButton,
  Grid,
  Paper,
  Alert,
  CircularProgress,
  FormControlLabel,
  Switch,
  Menu,
  MenuItem,
  Divider,
  Select,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { candidateTagsClient } from '../api/candidateTags';
import type { IntelligentTagSuggestion } from '@/types/api';

// Predefined colors for tags
const TAG_COLORS = [
  { name: 'Blue', value: '#1976D2', light: '#BBDEFB' },
  { name: 'Green', value: '#388E3C', light: '#C8E6C9' },
  { name: 'Orange', value: '#F57C00', light: '#FFE0B2' },
  { name: 'Purple', value: '#7B1FA2', light: '#E1BEE7' },
  { name: 'Red', value: '#D32F2F', light: '#FFCDD2' },
  { name: 'Teal', value: '#00796B', light: '#B2DFDB' },
  { name: 'Pink', value: '#C2185B', light: '#F8BBD0' },
  { name: 'Gray', value: '#616161', light: '#E0E0E0' },
];

interface Tag {
  id: string;
  name: string;
  color: string;
  candidate_count?: number;
}

interface CandidateTagsManagerProps {
  candidateId?: string;
  assignedTags?: Tag[];
  onTagsChange?: (tags: Tag[]) => void;
  readOnly?: boolean;
}

export function CandidateTagsManager({
  candidateId,
  assignedTags = [],
  onTagsChange,
  readOnly = false,
}: CandidateTagsManagerProps) {
  const queryClient = useQueryClient();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [mergeDialogOpen, setMergeDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [selectedTag, setSelectedTag] = useState<Tag | null>(null);
  const [targetTagId, setTargetTagId] = useState('');
  const [tagName, setTagName] = useState('');
  const [tagColor, setTagColor] = useState(TAG_COLORS[0].value);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);

  // Fetch all available tags
  const { data: tagsData, isLoading: tagsLoading } = useQuery({
    queryKey: ['candidate-tags'],
    queryFn: async () => {
      return await candidateTagsClient.listTags();
    },
  });

  const allTags = tagsData?.tags || [];

  // Compute popular tags (tags with candidate_count, sorted by usage)
  const popularTags = allTags
    .filter((tag) => tag.candidate_count !== undefined && tag.candidate_count > 0)
    .sort((a, b) => (b.candidate_count || 0) - (a.candidate_count || 0))
    .slice(0, 5);

  // Fetch intelligent tag suggestions when candidateId is provided
  const { data: intelligentSuggestionsData, isLoading: intelligentLoading, error: intelligentError } = useQuery({
    queryKey: ['intelligent-tag-suggestions', candidateId],
    queryFn: async () => {
      if (!candidateId) return null;
      // Use default organization ID - in production this would come from user context
      return await candidateTagsClient.getIntelligentSuggestions('default-org', candidateId, 5);
    },
    enabled: !!candidateId && dialogOpen, // Only fetch when dialog is open and candidateId exists
    retry: 1, // Retry once on failure
  });

  const intelligentSuggestions = intelligentSuggestionsData?.suggestions || [];

  // Create tag mutation
  const createMutation = useMutation({
    mutationFn: async ({ name, color }: { name: string; color: string }) => {
      return await candidateTagsClient.createTag({
        organization_id: 'default-org',
        tag_name: name,
        color,
        is_active: true,
      });
    },
    onSuccess: () => {
      setDialogOpen(false);
      setTagName('');
      queryClient.invalidateQueries({ queryKey: ['candidate-tags'] });
    },
  });

  // Update tag mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, name, color }: { id: string; name?: string; color?: string }) => {
      const updateData: { tag_name?: string; color?: string } = {};
      if (name !== undefined) updateData.tag_name = name;
      if (color !== undefined) updateData.color = color;
      return await candidateTagsClient.updateTag(id, updateData);
    },
    onSuccess: () => {
      setDialogOpen(false);
      setSelectedTag(null);
      queryClient.invalidateQueries({ queryKey: ['candidate-tags'] });
    },
  });

  // Delete tag mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await candidateTagsClient.deleteTag(id);
    },
    onSuccess: () => {
      setDeleteDialogOpen(false);
      setSelectedTag(null);
      queryClient.invalidateQueries({ queryKey: ['candidate-tags'] });
    },
  });

  // Assign tag to candidate mutation
  const assignMutation = useMutation({
    mutationFn: async (tagId: string) => {
      if (candidateId) {
        await candidateTagsClient.assignTagToResume(candidateId, { tag_id: tagId, recruiter_id: '' });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidate-tags'] });
      queryClient.invalidateQueries({ queryKey: ['candidate', candidateId, 'tags'] });
      queryClient.invalidateQueries({ queryKey: ['intelligent-tag-suggestions', candidateId] });
    },
  });

  // Remove tag from candidate mutation
  const removeMutation = useMutation({
    mutationFn: async (tagId: string) => {
      if (candidateId) {
        await candidateTagsClient.removeTagFromResume(candidateId, tagId);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidate-tags'] });
      queryClient.invalidateQueries({ queryKey: ['candidate', candidateId, 'tags'] });
    },
  });

  // Merge tags mutation
  const mergeMutation = useMutation({
    mutationFn: async ({ sourceTagId, targetTagId }: { sourceTagId: string; targetTagId: string }) => {
      return await candidateTagsClient.mergeTags(sourceTagId, targetTagId);
    },
    onSuccess: () => {
      setMergeDialogOpen(false);
      setSelectedTag(null);
      setTargetTagId('');
      queryClient.invalidateQueries({ queryKey: ['candidate-tags'] });
    },
  });

  const handleOpenCreateDialog = () => {
    setEditMode(false);
    setSelectedTag(null);
    setTagName('');
    setTagColor(TAG_COLORS[0].value);
    setDialogOpen(true);
  };

  const handleOpenEditDialog = (tag: Tag) => {
    setEditMode(true);
    setSelectedTag(tag);
    setTagName(tag.name);
    setTagColor(tag.color);
    setDialogOpen(true);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, tag: Tag) => {
    setMenuAnchor(event.currentTarget);
    setSelectedTag(tag);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedTag(null);
  };

  const handleSaveTag = () => {
    if (!tagName.trim()) return;

    if (editMode && selectedTag) {
      updateMutation.mutate({ id: selectedTag.id, name: tagName, color: tagColor });
    } else {
      createMutation.mutate({ name: tagName, color: tagColor });
    }
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleDeleteConfirm = () => {
    if (selectedTag) {
      deleteMutation.mutate(selectedTag.id);
    }
  };

  const handleMergeClick = () => {
    setMergeDialogOpen(true);
    setTargetTagId('');
    handleMenuClose();
  };

  const handleMergeConfirm = () => {
    if (selectedTag && targetTagId && selectedTag.id !== targetTagId) {
      mergeMutation.mutate({ sourceTagId: selectedTag.id, targetTagId });
    }
  };

  const handleMergeDialogClose = () => {
    setMergeDialogOpen(false);
    setTargetTagId('');
  };

  const getAvailableTargetTags = () => {
    if (!selectedTag) return [];
    return allTags.filter((tag) => tag.id !== selectedTag.id);
  };

  const handleToggleTag = (tag: Tag) => {
    const isAssigned = assignedTags.some((t) => t.id === tag.id);
    if (isAssigned) {
      removeMutation.mutate(tag.id);
    } else {
      assignMutation.mutate(tag.id);
    }
  };

  const handleSuggestionClick = (tag: Tag) => {
    // Check if already assigned
    const isAssigned = assignedTags.some((t) => t.id === tag.id);
    if (isAssigned) {
      // Already assigned, just close dialog
      setDialogOpen(false);
    } else {
      // Assign the tag and close dialog
      assignMutation.mutate(tag.id, {
        onSuccess: () => {
          setDialogOpen(false);
        },
      });
    }
  };

  const isAssigned = (tag: Tag) => assignedTags.some((t) => t.id === tag.id);

  return (
    <Box>
      {/* Tags Display */}
      <Stack direction="row" alignItems="center" spacing={1} flexWrap="wrap">
        {assignedTags.map((tag) => (
          <Chip
            key={tag.id}
            label={tag.name}
            sx={{
              bgcolor: tag.color,
              color: 'white',
              fontWeight: 500,
            }}
            onDelete={!readOnly ? () => removeMutation.mutate(tag.id) : undefined}
            size="small"
          />
        ))}
        {!readOnly && (
          <Chip
            icon={<Icon name="plus" size={16} />}
            label="Add Tag"
            onClick={handleOpenCreateDialog}
            size="small"
            variant="outlined"
            sx={{ cursor: 'pointer' }}
          />
        )}
      </Stack>

      {/* All Tags Management (when not in candidate context) */}
      {!candidateId && (
        <Box sx={{ mt: 3 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
            <Typography variant="h6">All Tags</Typography>
            {!readOnly && (
              <Button
                startIcon={<Icon name="plus" size={16} />}
                onClick={handleOpenCreateDialog}
                size="small"
              >
                New Tag
              </Button>
            )}
          </Stack>

          {tagsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : allTags.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Icon name="tag" size={48} color="disabled" style={{ marginBottom: '8px' }} />
              <Typography variant="body2" color="secondary">
                No tags created yet
              </Typography>
            </Paper>
          ) : (
            <Grid container spacing={2}>
              {allTags.map((tag) => (
                <Grid item xs={12} sm={6} md={4} lg={3} key={tag.id}>
                  <Paper
                    sx={{
                      p: 2,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      borderLeft: 4,
                      borderLeftColor: tag.color,
                    }}
                  >
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle2" noWrap>
                        {tag.name}
                      </Typography>
                      {tag.candidate_count !== undefined && (
                        <Typography variant="caption" color="secondary">
                          {tag.candidate_count} {tag.candidate_count === 1 ? 'candidate' : 'candidates'}
                        </Typography>
                      )}
                    </Box>
                    {!readOnly && (
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, tag)}
                        aria-label="Tag options"
                      >
                        <Icon name="more-vertical" size={16} />
                      </IconButton>
                    )}
                  </Paper>
                </Grid>
              ))}
            </Grid>
          )}
        </Box>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editMode ? 'Edit Tag' : 'Create Tag'}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Tag Name"
            value={tagName}
            onChange={(e) => setTagName(e.target.value)}
            sx={{ mt: 2 }}
            inputProps={{ maxLength: 30 }}
            helperText={`${tagName.length}/30 characters`}
          />

          <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>
            Color
          </Typography>
          <Grid container spacing={1}>
            {TAG_COLORS.map((color) => (
              <Grid key={color.value}>
                <Paper
                  sx={{
                    width: 36,
                    height: 36,
                    bgcolor: color.value,
                    cursor: 'pointer',
                    border: tagColor === color.value ? 3 : 0,
                    borderColor: 'primary',
                    '&:hover': {
                      transform: 'scale(1.1)',
                    },
                    transition: 'transform 0.2s',
                  }}
                  onClick={() => setTagColor(color.value)}
                  aria-label={`Select ${color.name} color`}
                  role="button"
                  tabIndex={0}
                />
              </Grid>
            ))}
          </Grid>

          {/* Popular Tags Suggestions */}
          {!editMode && popularTags.length > 0 && (
            <>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
                Popular Tags
                <Typography component="span" variant="caption" color="secondary" sx={{ ml: 1 }}>
                  (Quick add)
                </Typography>
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                {popularTags.map((tag) => {
                  const isAssigned = assignedTags.some((t) => t.id === tag.id);
                  return (
                    <Chip
                      key={tag.id}
                      label={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <span>{tag.name}</span>
                          <Typography
                            component="span"
                            variant="caption"
                            sx={{
                              opacity: 0.8,
                              fontSize: '0.75rem',
                            }}
                          >
                            ({tag.candidate_count})
                          </Typography>
                        </Box>
                      }
                      sx={{
                        bgcolor: tag.color,
                        color: 'white',
                        fontWeight: 500,
                        opacity: isAssigned ? 0.6 : 1,
                        cursor: 'pointer',
                        '&:hover': {
                          transform: 'scale(1.05)',
                          boxShadow: 2,
                        },
                        transition: 'transform 0.2s',
                      }}
                      onClick={() => handleSuggestionClick(tag)}
                      size="small"
                      disabled={assignMutation.isPending}
                    />
                  );
                })}
              </Box>
            </>
          )}

          {/* Intelligent Tag Suggestions (when candidateId is provided) */}
          {!editMode && candidateId && (intelligentSuggestions.length > 0 || intelligentLoading || intelligentError) && (
            <>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
                Suggested Tags
                <Typography component="span" variant="caption" color="secondary" sx={{ ml: 1 }}>
                  (Based on resume content)
                </Typography>
              </Typography>
              {intelligentLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              ) : intelligentError ? (
                <Alert severity="warning" sx={{ mt: 1 }}>
                  Unable to load intelligent suggestions. You can still use Popular Tags above.
                </Alert>
              ) : intelligentSuggestions.length > 0 ? (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                  {intelligentSuggestions.map((suggestion: IntelligentTagSuggestion) => {
                    const isAssigned = assignedTags.some((t) => t.id === suggestion.id);
                    return (
                      <Chip
                        key={suggestion.id}
                        label={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <span>{suggestion.tag_name}</span>
                            <Typography
                              component="span"
                              variant="caption"
                              sx={{
                                opacity: 0.9,
                                fontSize: '0.7rem',
                                fontWeight: 600,
                              }}
                            >
                              ({Math.round(suggestion.relevance_score * 100)}%)
                            </Typography>
                          </Box>
                        }
                        sx={{
                          bgcolor: suggestion.color || '#757575',
                          color: 'white',
                          fontWeight: 500,
                          opacity: isAssigned ? 0.6 : 1,
                          cursor: 'pointer',
                          '&:hover': {
                            transform: 'scale(1.05)',
                            boxShadow: 2,
                          },
                          transition: 'transform 0.2s',
                        }}
                        onClick={() => handleSuggestionClick({
                          id: suggestion.id,
                          name: suggestion.tag_name,
                          color: suggestion.color || '#757575',
                        } as Tag)}
                        size="small"
                        disabled={assignMutation.isPending}
                      />
                    );
                  })}
                </Box>
              ) : null}
            </>
          )}

          {/* Preview */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="caption" color="secondary">
              Preview
            </Typography>
            <Box sx={{ mt: 1 }}>
              <Chip
                label={tagName || 'Tag Name'}
                sx={{
                  bgcolor: tagColor,
                  color: 'white',
                  fontWeight: 500,
                }}
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSaveTag}
            variant="contained"
            disabled={!tagName.trim() || (createMutation.isPending || updateMutation.isPending)}
          >
            {editMode ? 'Save' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Options Menu */}
      <Menu anchorEl={menuAnchor} open={Boolean(menuAnchor)} onClose={handleMenuClose}>
        <MenuItem onClick={() => { handleMenuClose(); if (selectedTag) handleOpenEditDialog(selectedTag); }}>
          <Icon name="edit" size={16} style={{ marginRight: '4px' }} />
          Edit
        </MenuItem>
        <MenuItem onClick={handleMergeClick}>
          <Icon name="merge" size={16} style={{ marginRight: '4px' }} />
          Merge
        </MenuItem>
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error' }}>
          <Icon name="trash-2" size={16} style={{ marginRight: '4px' }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Delete Tag</DialogTitle>
        <DialogContent>
          {selectedTag && selectedTag.candidate_count && selectedTag.candidate_count > 0 ? (
            <Alert severity="warning" sx={{ mb: 2 }}>
              This tag is assigned to {selectedTag.candidate_count} {selectedTag.candidate_count === 1 ? 'candidate' : 'candidates'}. It will be removed from all of them.
            </Alert>
          ) : null}
          <Typography variant="body1">
            Are you sure you want to delete "{selectedTag?.name}"?
          </Typography>
          <Typography variant="body2" color="secondary" sx={{ mt: 1 }}>
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Merge Dialog */}
      <Dialog open={mergeDialogOpen} onClose={handleMergeDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>Merge Tags</DialogTitle>
        <DialogContent>
          {selectedTag && selectedTag.candidate_count && selectedTag.candidate_count > 0 ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              Merging "{selectedTag.name}" will transfer all {selectedTag.candidate_count} {selectedTag.candidate_count === 1 ? 'candidate' : 'candidates'} to the target tag. The source tag will be deleted.
            </Alert>
          ) : null}
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Source Tag (will be deleted)
            </Typography>
            {selectedTag && (
              <Chip
                label={selectedTag.name}
                sx={{
                  bgcolor: selectedTag.color,
                  color: 'white',
                  fontWeight: 500,
                }}
                size="small"
              />
            )}
          </Box>
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Target Tag (will be kept)
            </Typography>
            <Select
              label="Select target tag"
              value={targetTagId}
              onChange={(e) => setTargetTagId(e.target.value)}
              options={getAvailableTargetTags().map((tag) => ({
                value: tag.id,
                label: tag.name,
              }))}
              fullWidth
              displayEmpty
              placeholder="Select a tag to merge into"
            />
          </Box>
          <Typography variant="body2" color="secondary">
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleMergeDialogClose}>Cancel</Button>
          <Button
            onClick={handleMergeConfirm}
            variant="contained"
            disabled={!targetTagId || mergeMutation.isPending || selectedTag?.id === targetTagId}
          >
            Merge Tags
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default CandidateTagsManager;
