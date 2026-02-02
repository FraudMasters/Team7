/**
 * Candidate Tags Manager Component
 *
 * Manage tags for candidates with color coding and assignment capabilities.
 */

import { useState, useEffect } from 'react';
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
  Grid2,
  Paper,
  Alert,
  CircularProgress,
  FormControlLabel,
  Switch,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Label as LabelIcon,
  Close as CloseIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { candidateTagsClient } from '../api/candidateTags';

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
  const [editMode, setEditMode] = useState(false);
  const [selectedTag, setSelectedTag] = useState<Tag | null>(null);
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

  // Create tag mutation
  const createMutation = useMutation({
    mutationFn: async ({ name, color }: { name: string; color: string }) => {
      return await candidateTagsClient.createTag({ name, color });
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
      return await candidateTagsClient.updateTag(id, { name, color });
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
        await candidateTagsClient.assignTag(candidateId, tagId);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidate-tags'] });
      queryClient.invalidateQueries({ queryKey: ['candidate', candidateId, 'tags'] });
    },
  });

  // Remove tag from candidate mutation
  const removeMutation = useMutation({
    mutationFn: async (tagId: string) => {
      if (candidateId) {
        await candidateTagsClient.removeTag(candidateId, tagId);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidate-tags'] });
      queryClient.invalidateQueries({ queryKey: ['candidate', candidateId, 'tags'] });
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

  const handleToggleTag = (tag: Tag) => {
    const isAssigned = assignedTags.some((t) => t.id === tag.id);
    if (isAssigned) {
      removeMutation.mutate(tag.id);
    } else {
      assignMutation.mutate(tag.id);
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
            icon={<AddIcon />}
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
                startIcon={<AddIcon />}
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
              <LabelIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
              <Typography variant="body2" color="text.secondary">
                No tags created yet
              </Typography>
            </Paper>
          ) : (
            <Grid2 container spacing={2}>
              {allTags.map((tag) => (
                <Grid2 key={tag.id} size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
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
                        <Typography variant="caption" color="text.secondary">
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
                        <MoreVertIcon fontSize="small" />
                      </IconButton>
                    )}
                  </Paper>
                </Grid2>
              ))}
            </Grid2>
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
            slotProps={{
              input: {
                'aria-label': 'Tag name',
              },
            }}
          />

          <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>
            Color
          </Typography>
          <Grid2 container spacing={1}>
            {TAG_COLORS.map((color) => (
              <Grid2 key={color.value}>
                <Paper
                  sx={{
                    width: 36,
                    height: 36,
                    bgcolor: color.value,
                    cursor: 'pointer',
                    border: tagColor === color.value ? 3 : 0,
                    borderColor: 'primary.main',
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
              </Grid2>
            ))}
          </Grid2>

          {/* Preview */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="caption" color="text.secondary">
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
          <EditIcon fontSize="small" sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
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
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
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
    </Box>
  );
}

export default CandidateTagsManager;
