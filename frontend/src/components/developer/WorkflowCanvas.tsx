/**
 * Workflow Canvas Component
 *
 * Visual canvas for displaying and editing workflow actions in a flow diagram.
 *
 * @module components/developer/WorkflowCanvas
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Card,
  CardContent,
  CardActions,
  Chip,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import type { ActionConfig } from '@/api/workflows';
import { ActionType } from '@/api/workflows';

interface WorkflowCanvasProps {
  actions: ActionConfig[];
  onUpdateAction: (index: number, action: ActionConfig) => void;
  onRemoveAction: (index: number) => void;
}

/**
 * Action configuration form based on action type
 */
interface ActionConfigFormProps {
  action: ActionConfig;
  onChange: (config: Record<string, unknown>) => void;
}

const ActionConfigForm: React.FC<ActionConfigFormProps> = ({ action, onChange }) => {
  const config = action.config || {};

  switch (action.type) {
    case ActionType.Log:
      return (
        <TextField
          fullWidth
          label="Log Message"
          value={config.message || ''}
          onChange={(e) => onChange({ ...config, message: e.target.value })}
          placeholder="Enter log message"
          multiline
          rows={2}
          size="small"
        />
      );

    case ActionType.SendEmail:
      return (
        <Stack spacing={2}>
          <TextField
            fullWidth
            label="To"
            value={config.to || ''}
            onChange={(e) => onChange({ ...config, to: e.target.value })}
            placeholder="recipient@example.com"
            size="small"
          />
          <TextField
            fullWidth
            label="Subject"
            value={config.subject || ''}
            onChange={(e) => onChange({ ...config, subject: e.target.value })}
            placeholder="Email subject"
            size="small"
          />
          <TextField
            fullWidth
            label="Body"
            value={config.body || ''}
            onChange={(e) => onChange({ ...config, body: e.target.value })}
            placeholder="Email body"
            multiline
            rows={4}
            size="small"
          />
        </Stack>
      );

    case ActionType.SendWebhook:
      return (
        <Stack spacing={2}>
          <TextField
            fullWidth
            label="URL"
            value={config.url || ''}
            onChange={(e) => onChange({ ...config, url: e.target.value })}
            placeholder="https://example.com/webhook"
            size="small"
          />
          <FormControl fullWidth size="small">
            <InputLabel>Method</InputLabel>
            <Select
              value={config.method || 'POST'}
              onChange={(e) => onChange({ ...config, method: e.target.value })}
              label="Method"
            >
              <MenuItem value="GET">GET</MenuItem>
              <MenuItem value="POST">POST</MenuItem>
              <MenuItem value="PUT">PUT</MenuItem>
              <MenuItem value="PATCH">PATCH</MenuItem>
              <MenuItem value="DELETE">DELETE</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="Body (JSON)"
            value={typeof config.body === 'string' ? config.body : JSON.stringify(config.body || {}, null, 2)}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                onChange({ ...config, body: parsed });
              } catch {
                onChange({ ...config, body: e.target.value });
              }
            }}
            placeholder='{"key": "value"}'
            multiline
            rows={4}
            size="small"
          />
        </Stack>
      );

    case ActionType.AddTag:
      return (
        <TextField
          fullWidth
          label="Tag Name"
          value={config.tag_name || ''}
          onChange={(e) => onChange({ ...config, tag_name: e.target.value })}
          placeholder="Enter tag name"
          size="small"
        />
      );

    case ActionType.RemoveTag:
      return (
        <TextField
          fullWidth
          label="Tag Name"
          value={config.tag_name || ''}
          onChange={(e) => onChange({ ...config, tag_name: e.target.value })}
          placeholder="Enter tag name to remove"
          size="small"
        />
      );

    case ActionType.AddNote:
      return (
        <TextField
          fullWidth
          label="Note Content"
          value={config.content || ''}
          onChange={(e) => onChange({ ...config, content: e.target.value })}
          placeholder="Enter note content"
          multiline
          rows={3}
          size="small"
        />
      );

    case ActionType.MoveStage:
      return (
        <TextField
          fullWidth
          label="Stage ID"
          value={config.stage_id || ''}
          onChange={(e) => onChange({ ...config, stage_id: e.target.value })}
          placeholder="Enter target stage ID"
          size="small"
        />
      );

    case ActionType.Delay:
      return (
        <TextField
          fullWidth
          type="number"
          label="Delay (seconds)"
          value={config.seconds || 60}
          onChange={(e) => onChange({ ...config, seconds: parseInt(e.target.value) || 60 })}
          inputProps={{ min: 1 }}
          size="small"
        />
      );

    case ActionType.Conditional:
      return (
        <Stack spacing={2}>
          <Grid container spacing={2}>
            <Grid item xs={5}>
              <TextField
                fullWidth
                label="Field"
                value={config.condition?.field || ''}
                onChange={(e) => onChange({
                  ...config,
                  condition: { ...config.condition, field: e.target.value }
                })}
                placeholder="data.field"
                size="small"
              />
            </Grid>
            <Grid item xs={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Operator</InputLabel>
                <Select
                  value={config.condition?.operator || 'equals'}
                  onChange={(e) => onChange({
                    ...config,
                    condition: { ...config.condition, operator: e.target.value }
                  })}
                  label="Operator"
                >
                  <MenuItem value="equals">Equals</MenuItem>
                  <MenuItem value="not_equals">Not Equals</MenuItem>
                  <MenuItem value="contains">Contains</MenuItem>
                  <MenuItem value="greater_than">Greater Than</MenuItem>
                  <MenuItem value="less_than">Less Than</MenuItem>
                  <MenuItem value="exists">Exists</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={4}>
              <TextField
                fullWidth
                label="Value"
                value={config.condition?.value || ''}
                onChange={(e) => onChange({
                  ...config,
                  condition: { ...config.condition, value: e.target.value }
                })}
                placeholder="Value"
                size="small"
              />
            </Grid>
          </Grid>
        </Stack>
      );

    case ActionType.SendSlack:
      return (
        <Stack spacing={2}>
          <TextField
            fullWidth
            label="Channel"
            value={config.channel || ''}
            onChange={(e) => onChange({ ...config, channel: e.target.value })}
            placeholder="#channel-name"
            size="small"
          />
          <TextField
            fullWidth
            label="Message"
            value={config.message || ''}
            onChange={(e) => onChange({ ...config, message: e.target.value })}
            placeholder="Slack message"
            multiline
            rows={3}
            size="small"
          />
        </Stack>
      );

    default:
      return (
        <Typography variant="body2" color="text.secondary">
          No configuration options available for this action type.
        </Typography>
      );
  }
};

/**
 * Action Card Component
 */
interface ActionCardProps {
  action: ActionConfig;
  index: number;
  isFirst: boolean;
  isLast: boolean;
  onUpdate: (index: number, action: ActionConfig) => void;
  onRemove: (index: number) => void;
}

const ActionCard: React.FC<ActionCardProps> = ({
  action,
  index,
  isFirst,
  isLast,
  onUpdate,
  onRemove,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [localConfig, setLocalConfig] = useState(action.config);

  const handleSave = useCallback(() => {
    onUpdate(index, { ...action, config: localConfig });
    setIsEditing(false);
  }, [action, index, localConfig, onUpdate]);

  const handleCancel = useCallback(() => {
    setLocalConfig(action.config);
    setIsEditing(false);
  }, [action.config]);

  const getActionIcon = (type: string): string => {
    const icons: Record<string, string> = {
      [ActionType.Log]: '📝',
      [ActionType.SendEmail]: '📧',
      [ActionType.SendWebhook]: '🔗',
      [ActionType.SendSlack]: '💬',
      [ActionType.AddTag]: '🏷️',
      [ActionType.RemoveTag]: '🏷️',
      [ActionType.AddNote]: '📝',
      [ActionType.MoveStage]: '➡️',
      [ActionType.Conditional]: '🔀',
      [ActionType.Delay]: '⏱️',
    };
    return icons[type] || '⚙️';
  };

  const getCategoryColor = (type: string): string => {
    const colors: Record<string, string> = {
      [ActionType.Log]: 'default',
      [ActionType.SendEmail]: 'primary',
      [ActionType.SendWebhook]: 'info',
      [ActionType.SendSlack]: 'secondary',
      [ActionType.AddTag]: 'success',
      [ActionType.RemoveTag]: 'warning',
      [ActionType.AddNote]: 'default',
      [ActionType.MoveStage]: 'success',
      [ActionType.Conditional]: 'error',
      [ActionType.Delay]: 'default',
    };
    return colors[type] || 'default';
  };

  return (
    <Box sx={{ position: 'relative', mb: isLast ? 0 : 8 }}>
      {/* Connection Line */}
      {!isLast && (
        <Box
          sx={{
            position: 'absolute',
            left: 24,
            top: 80,
            width: 2,
            height: 32,
            bgcolor: 'divider',
          }}
        />
      )}

      <Card
        variant="outlined"
        sx={{
          maxWidth: 400,
          ml: isFirst ? 0 : 4,
          borderLeft: '4px solid',
          borderLeftColor: getCategoryColor(action.type) === 'primary' ? 'primary.main' :
                          getCategoryColor(action.type) === 'success' ? 'success.main' :
                          getCategoryColor(action.type) === 'info' ? 'info.main' :
                          getCategoryColor(action.type) === 'warning' ? 'warning.main' :
                          getCategoryColor(action.type) === 'error' ? 'error.main' :
                          'divider',
        }}
      >
        <CardContent>
          <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
            <Typography variant="h4" sx={{ fontSize: 24 }}>
              {getActionIcon(action.type)}
            </Typography>
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle1" fontWeight={600}>
                {action.label || action.type}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Step {index + 1}
              </Typography>
            </Box>
            <Chip label={action.type} size="small" color={getCategoryColor(action.type) as any} />
          </Stack>

          {isEditing ? (
            <Box>
              <ActionConfigForm
                action={action}
                onChange={(newConfig) => setLocalConfig(newConfig)}
              />
              <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                <Button size="small" onClick={handleCancel}>
                  Cancel
                </Button>
                <Button size="small" variant="contained" onClick={handleSave}>
                  Save
                </Button>
              </Stack>
            </Box>
          ) : (
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="body2" color="text.secondary">
                  Click to view configuration
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box
                  sx={{
                    bgcolor: 'background.paper',
                    p: 1.5,
                    borderRadius: 1,
                    fontFamily: 'monospace',
                    fontSize: '0.75rem',
                    overflow: 'auto',
                    maxHeight: 150,
                  }}
                >
                  <pre>{JSON.stringify(config, null, 2)}</pre>
                </Box>
              </AccordionDetails>
            </Accordion>
          )}
        </CardContent>
        <CardActions>
          <IconButton size="small" onClick={() => setIsEditing(!isEditing)}>
            <EditIcon fontSize="small" />
          </IconButton>
          <IconButton size="small" color="error" onClick={() => onRemove(index)}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </CardActions>
      </Card>
    </Box>
  );
};

/**
 * WorkflowCanvas Component
 *
 * Visual representation of workflow flow:
 * - Displays actions in a connected flow diagram
 * - Edit action configuration
 * - Remove actions
 * - Shows connections between actions
 */
const WorkflowCanvas: React.FC<WorkflowCanvasProps> = ({
  actions,
  onUpdateAction,
  onRemoveAction,
}) => {
  if (actions.length === 0) {
    return (
      <Box
        sx={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        <Typography variant="h6" color="text.secondary" textAlign="center">
          No Actions Yet
        </Typography>
        <Typography variant="body2" color="text.secondary" textAlign="center">
          Add actions from the palette to build your workflow
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 4 }}>
      {actions.map((action, index) => (
        <ActionCard
          key={index}
          action={action}
          index={index}
          isFirst={index === 0}
          isLast={index === actions.length - 1}
          onUpdate={onUpdateAction}
          onRemove={onRemoveAction}
        />
      ))}
    </Box>
  );
};

export default WorkflowCanvas;
