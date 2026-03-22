/**
 * Template Builder Component
 *
 * Visual drag-and-drop template builder for creating email and SMS templates
 * with dynamic variables, conditional blocks, and real-time preview.
 */

import { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Stack,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  Divider,
  Switch,
  FormControlLabel,
  Grid2,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  DragIndicator as DragIcon,
  Save as SaveIcon,
  Preview as PreviewIcon,
  Settings as SettingsIcon,
  TextFields as TextIcon,
  Title as HeadingIcon,
  SmartButton as ButtonIcon,
  QuestionMark as ConditionalIcon,
} from '@mui/icons-material';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationTemplatesClient } from '../../api/notificationTemplates';
import { BlockEditor } from './BlockEditor';
import type {
  TemplateBlock,
  TextBlock,
  HeadingBlock,
  ButtonBlock,
  ConditionalBlock,
  NotificationTemplateType,
  NotificationTemplateCategory,
  PipelineStage,
} from '../../types/templates';

interface TemplateBuilderProps {
  templateId?: string;
  initialType?: NotificationTemplateType;
  onSave?: (templateId: string) => void;
  onCancel?: () => void;
}

// Block type definitions for the palette
const BLOCK_TYPES = [
  {
    id: 'text',
    type: 'text' as const,
    label: 'Text Block',
    icon: TextIcon,
    description: 'Add a paragraph of text',
  },
  {
    id: 'heading',
    type: 'heading' as const,
    label: 'Heading',
    icon: HeadingIcon,
    description: 'Add a heading',
  },
  {
    id: 'button',
    type: 'button' as const,
    label: 'Button',
    icon: ButtonIcon,
    description: 'Add a clickable button',
  },
  {
    id: 'conditional',
    type: 'conditional' as const,
    label: 'Conditional',
    icon: ConditionalIcon,
    description: 'Show content based on conditions',
  },
];

const TEMPLATE_CATEGORIES: NotificationTemplateCategory[] = [
  'outreach',
  'interview',
  'rejection',
  'offer',
  'follow_up',
  'feedback',
  'other',
];

const PIPELINE_STAGES: PipelineStage[] = [
  'application_received',
  'screening',
  'interview_scheduled',
  'interview_completed',
  'offer_extended',
  'offer_accepted',
  'rejected',
  'withdrawn',
];

export function TemplateBuilder({
  templateId,
  initialType = 'email',
  onSave,
  onCancel,
}: TemplateBuilderProps) {
  const queryClient = useQueryClient();

  // Template metadata
  const [templateName, setTemplateName] = useState('');
  const [templateType, setTemplateType] = useState<NotificationTemplateType>(initialType);
  const [category, setCategory] = useState<NotificationTemplateCategory>('other');
  const [pipelineStage, setPipelineStage] = useState<PipelineStage | ''>('');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [language, setLanguage] = useState('en');

  // Template blocks
  const [blocks, setBlocks] = useState<TemplateBlock[]>([]);
  const [variables, setVariables] = useState<string[]>([]);

  // UI state
  const [showSettings, setShowSettings] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generate unique ID for new blocks
  const generateBlockId = () => {
    return `block-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  // Handle drag end
  const handleDragEnd = useCallback((result: DropResult) => {
    const { source, destination, draggableId } = result;

    if (!destination) {
      return;
    }

    // Dropping from palette to canvas
    if (source.droppableId === 'palette' && destination.droppableId === 'canvas') {
      const blockType = draggableId.replace('palette-', '');
      const newBlock = createNewBlock(blockType as TemplateBlock['type']);

      const newBlocks = Array.from(blocks);
      newBlocks.splice(destination.index, 0, newBlock);
      setBlocks(newBlocks);
      return;
    }

    // Reordering within canvas
    if (source.droppableId === 'canvas' && destination.droppableId === 'canvas') {
      const newBlocks = Array.from(blocks);
      const [reorderedBlock] = newBlocks.splice(source.index, 1);
      newBlocks.splice(destination.index, 0, reorderedBlock);
      setBlocks(newBlocks);
      return;
    }
  }, [blocks]);

  // Create a new block of the specified type
  const createNewBlock = (type: TemplateBlock['type']): TemplateBlock => {
    const id = generateBlockId();

    switch (type) {
      case 'text':
        return {
          id,
          type: 'text',
          content: 'Enter your text here. Use {{variable_name}} for dynamic content.',
        } as TextBlock;

      case 'heading':
        return {
          id,
          type: 'heading',
          content: 'Heading Text',
          level: 2,
        } as HeadingBlock;

      case 'button':
        return {
          id,
          type: 'button',
          content: 'Click Here',
          href: 'https://example.com',
          style: 'primary',
        } as ButtonBlock;

      case 'conditional':
        return {
          id,
          type: 'conditional',
          condition: {
            field: 'pipeline_stage',
            operator: 'eq',
            value: 'interview_scheduled',
          },
          true_blocks: [],
          false_blocks: [],
        } as ConditionalBlock;

      default:
        return {
          id,
          type: 'text',
          content: 'New block',
        } as TextBlock;
    }
  };

  // Delete a block
  const handleDeleteBlock = (blockId: string) => {
    setBlocks(blocks.filter(block => block.id !== blockId));
  };

  // Update block content
  const handleUpdateBlock = (blockId: string, updates: Partial<TemplateBlock>) => {
    setBlocks(blocks.map(block =>
      block.id === blockId ? { ...block, ...updates } : block
    ));
  };

  // Save template mutation
  const saveMutation = useMutation({
    mutationFn: async () => {
      const templateData = {
        name: templateName,
        type: templateType,
        category: category || undefined,
        pipeline_stage: pipelineStage || undefined,
        subject: templateType === 'email' ? subject : undefined,
        body: blocks.map(b => b.content || '').join('\n\n'),
        variables,
        template_blocks: blocks,
        description: description || undefined,
        is_active: isActive,
        language,
      };

      if (templateId) {
        return await notificationTemplatesClient.updateTemplate(templateId, templateData);
      } else {
        return await notificationTemplatesClient.createTemplate(templateData);
      }
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['notification-templates'] });
      if (onSave) {
        onSave(data.id);
      }
    },
    onError: (error: Error) => {
      setError(error.message || 'Failed to save template');
    },
  });

  const handleSave = () => {
    // Validation
    if (!templateName.trim()) {
      setError('Template name is required');
      return;
    }

    if (templateType === 'email' && !subject.trim()) {
      setError('Email subject is required');
      return;
    }

    if (blocks.length === 0) {
      setError('Template must have at least one block');
      return;
    }

    setError(null);
    saveMutation.mutate();
  };

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 3, gap: 2 }}>
        {/* Header */}
        <Paper sx={{ p: 2 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="h5" component="h1">
              {templateId ? 'Edit Template' : 'Create New Template'}
            </Typography>
            <Stack direction="row" spacing={2}>
              <Button
                startIcon={<SettingsIcon />}
                onClick={() => setShowSettings(!showSettings)}
                variant={showSettings ? 'contained' : 'outlined'}
              >
                Settings
              </Button>
              <Button
                startIcon={<PreviewIcon />}
                variant="outlined"
                disabled={blocks.length === 0}
              >
                Preview
              </Button>
              <Button
                startIcon={<SaveIcon />}
                variant="contained"
                onClick={handleSave}
                disabled={saveMutation.isPending}
              >
                {saveMutation.isPending ? 'Saving...' : 'Save'}
              </Button>
              {onCancel && (
                <Button variant="outlined" onClick={onCancel}>
                  Cancel
                </Button>
              )}
            </Stack>
          </Stack>

          {/* Settings Panel */}
          {showSettings && (
            <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
              <Grid2 container spacing={2}>
                <Grid2 size={{ xs: 12, md: 6 }}>
                  <TextField
                    fullWidth
                    label="Template Name"
                    value={templateName}
                    onChange={(e) => setTemplateName(e.target.value)}
                    required
                  />
                </Grid2>
                <Grid2 size={{ xs: 12, md: 6 }}>
                  <FormControl fullWidth>
                    <InputLabel>Template Type</InputLabel>
                    <Select
                      value={templateType}
                      label="Template Type"
                      onChange={(e) => setTemplateType(e.target.value as NotificationTemplateType)}
                    >
                      <MenuItem value="email">Email</MenuItem>
                      <MenuItem value="sms">SMS</MenuItem>
                    </Select>
                  </FormControl>
                </Grid2>
                {templateType === 'email' && (
                  <Grid2 size={{ xs: 12 }}>
                    <TextField
                      fullWidth
                      label="Email Subject"
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      placeholder="Use {{variable_name}} for dynamic content"
                      required
                    />
                  </Grid2>
                )}
                <Grid2 size={{ xs: 12, md: 4 }}>
                  <FormControl fullWidth>
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={category}
                      label="Category"
                      onChange={(e) => setCategory(e.target.value as NotificationTemplateCategory)}
                    >
                      {TEMPLATE_CATEGORIES.map((cat) => (
                        <MenuItem key={cat} value={cat}>
                          {cat.replace('_', ' ').toUpperCase()}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid2>
                <Grid2 size={{ xs: 12, md: 4 }}>
                  <FormControl fullWidth>
                    <InputLabel>Pipeline Stage</InputLabel>
                    <Select
                      value={pipelineStage}
                      label="Pipeline Stage"
                      onChange={(e) => setPipelineStage(e.target.value as PipelineStage)}
                    >
                      <MenuItem value="">
                        <em>None</em>
                      </MenuItem>
                      {PIPELINE_STAGES.map((stage) => (
                        <MenuItem key={stage} value={stage}>
                          {stage.replace(/_/g, ' ').toUpperCase()}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid2>
                <Grid2 size={{ xs: 12, md: 4 }}>
                  <FormControl fullWidth>
                    <InputLabel>Language</InputLabel>
                    <Select
                      value={language}
                      label="Language"
                      onChange={(e) => setLanguage(e.target.value)}
                    >
                      <MenuItem value="en">English</MenuItem>
                      <MenuItem value="ru">Russian</MenuItem>
                    </Select>
                  </FormControl>
                </Grid2>
                <Grid2 size={{ xs: 12 }}>
                  <TextField
                    fullWidth
                    multiline
                    rows={2}
                    label="Description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Describe the purpose of this template"
                  />
                </Grid2>
                <Grid2 size={{ xs: 12 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={isActive}
                        onChange={(e) => setIsActive(e.target.checked)}
                      />
                    }
                    label="Active"
                  />
                </Grid2>
              </Grid2>
            </Box>
          )}
        </Paper>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Main Content Area */}
        <Box sx={{ flex: 1, display: 'flex', gap: 2, minHeight: 0 }}>
          {/* Block Palette */}
          <Paper sx={{ width: 280, p: 2, flexShrink: 0 }}>
            <Typography variant="h6" gutterBottom>
              Block Palette
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Drag blocks to the canvas to build your template
            </Typography>

            <Droppable droppableId="palette" isDropDisabled>
              {(provided, snapshot) => (
                <Stack
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  spacing={1}
                  sx={{
                    minHeight: 200,
                    opacity: snapshot.isDraggingOver ? 0.5 : 1,
                  }}
                >
                  {BLOCK_TYPES.map((blockType, index) => (
                    <Draggable
                      key={blockType.id}
                      draggableId={`palette-${blockType.type}`}
                      index={index}
                    >
                      {(provided, snapshot) => (
                        <Paper
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          elevation={snapshot.isDragging ? 8 : 1}
                          sx={{
                            p: 1.5,
                            cursor: 'grab',
                            border: 1,
                            borderColor: 'divider',
                            bgcolor: snapshot.isDragging ? 'action.hover' : 'background.paper',
                            '&:hover': {
                              bgcolor: 'action.hover',
                              borderColor: 'primary.main',
                            },
                          }}
                        >
                          <Stack direction="row" spacing={1} alignItems="center">
                            <blockType.icon fontSize="small" color="primary" />
                            <Box sx={{ flex: 1 }}>
                              <Typography variant="body2" fontWeight="medium">
                                {blockType.label}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {blockType.description}
                              </Typography>
                            </Box>
                            <DragIcon fontSize="small" color="action" />
                          </Stack>
                        </Paper>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </Stack>
              )}
            </Droppable>
          </Paper>

          {/* Template Canvas */}
          <Paper
            sx={{
              flex: 1,
              p: 3,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'auto',
            }}
          >
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6">Template Canvas</Typography>
              {blocks.length > 0 && (
                <Chip label={`${blocks.length} block${blocks.length !== 1 ? 's' : ''}`} size="small" />
              )}
            </Box>

            <Droppable droppableId="canvas">
              {(provided, snapshot) => (
                <Box
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  sx={{
                    flex: 1,
                    minHeight: 400,
                    p: 2,
                    border: 2,
                    borderStyle: 'dashed',
                    borderColor: snapshot.isDraggingOver ? 'primary.main' : 'divider',
                    borderRadius: 1,
                    bgcolor: snapshot.isDraggingOver ? 'action.hover' : 'background.default',
                    transition: 'all 0.2s',
                  }}
                >
                  {blocks.length === 0 ? (
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        height: '100%',
                        color: 'text.secondary',
                      }}
                    >
                      <Stack alignItems="center" spacing={1}>
                        <AddIcon sx={{ fontSize: 48, opacity: 0.3 }} />
                        <Typography variant="body1">
                          Drag blocks from the palette to start building
                        </Typography>
                      </Stack>
                    </Box>
                  ) : (
                    <Stack spacing={2}>
                      {blocks.map((block, index) => (
                        <Draggable key={block.id} draggableId={block.id} index={index}>
                          {(provided, snapshot) => (
                            <Paper
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              elevation={snapshot.isDragging ? 8 : 2}
                              sx={{
                                p: 2,
                                bgcolor: snapshot.isDragging ? 'action.selected' : 'background.paper',
                                border: 1,
                                borderColor: snapshot.isDragging ? 'primary.main' : 'divider',
                              }}
                            >
                              <Stack direction="row" spacing={2} alignItems="flex-start">
                                <Box {...provided.dragHandleProps} sx={{ pt: 0.5 }}>
                                  <DragIcon color="action" sx={{ cursor: 'grab' }} />
                                </Box>
                                <Box sx={{ flex: 1 }}>
                                  <BlockEditor
                                    block={block}
                                    onUpdate={(updates) => handleUpdateBlock(block.id, updates)}
                                    onDelete={() => handleDeleteBlock(block.id)}
                                  />
                                </Box>
                              </Stack>
                            </Paper>
                          )}
                        </Draggable>
                      ))}
                    </Stack>
                  )}
                  {provided.placeholder}
                </Box>
              )}
            </Droppable>
          </Paper>
        </Box>
      </Box>
    </DragDropContext>
  );
}
