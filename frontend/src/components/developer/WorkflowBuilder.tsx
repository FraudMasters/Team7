/**
 * Workflow Builder Component
 *
 * Visual editor for creating and editing workflow automations.
 *
 * @module components/developer/WorkflowBuilder
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Alert,
  Divider,
  Grid,
  Card,
  CardContent,
  CardActions,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Add as AddIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import WorkflowCanvas from './WorkflowCanvas';
import {
  workflowsClient,
  type TriggerConfig,
  type ActionConfig,
  type WorkflowDetail,
  WorkflowTriggerType,
  ActionType,
} from '@/api/workflows';

interface WorkflowBuilderProps {
  workflowId?: string;
  onSuccess: () => void;
  onCancel: () => void;
}

/**
 * Available trigger events
 */
const TRIGGER_EVENTS = [
  { value: 'candidate.created', label: 'Candidate Created', category: 'Candidate' },
  { value: 'candidate.updated', label: 'Candidate Updated', category: 'Candidate' },
  { value: 'stage.changed', label: 'Stage Changed', category: 'Workflow' },
  { value: 'ranking.created', label: 'Ranking Created', category: 'Ranking' },
  { value: 'vacancy.created', label: 'Vacancy Created', category: 'Vacancy' },
  { value: 'webhook.received', label: 'Webhook Received', category: 'Webhook' },
];

/**
 * Available action types with configuration
 */
const ACTION_TYPES = [
  { value: ActionType.Log, label: 'Log Message', category: 'Debug', icon: '📝' },
  { value: ActionType.SendEmail, label: 'Send Email', category: 'Notification', icon: '📧' },
  { value: ActionType.SendWebhook, label: 'Send Webhook', category: 'Integration', icon: '🔗' },
  { value: ActionType.SendSlack, label: 'Send Slack', category: 'Notification', icon: '💬' },
  { value: ActionType.AddTag, label: 'Add Tag', category: 'Candidate', icon: '🏷️' },
  { value: ActionType.RemoveTag, label: 'Remove Tag', category: 'Candidate', icon: '🏷️' },
  { value: ActionType.AddNote, label: 'Add Note', category: 'Candidate', icon: '📝' },
  { value: ActionType.MoveStage, label: 'Move Stage', category: 'Workflow', icon: '➡️' },
  { value: ActionType.Conditional, label: 'Conditional', category: 'Logic', icon: '🔀' },
  { value: ActionType.Delay, label: 'Delay', category: 'Timing', icon: '⏱️' },
];

/**
 * WorkflowBuilder Component
 *
 * Provides a visual interface for building workflow automations:
 * - Configure triggers (webhook, schedule, manual)
 * - Add and configure actions
 * - Visual canvas showing workflow flow
 * - Save and activate workflows
 */
const WorkflowBuilder: React.FC<WorkflowBuilderProps> = ({
  workflowId,
  onSuccess,
  onCancel,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [triggerType, setTriggerType] = useState<WorkflowTriggerType>(WorkflowTriggerType.Webhook);
  const [triggerEvent, setTriggerEvent] = useState('candidate.created');
  const [cronExpression, setCronExpression] = useState('');
  const [actions, setActions] = useState<ActionConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [existingWorkflow, setExistingWorkflow] = useState<WorkflowDetail | null>(null);

  // Load existing workflow if editing
  useEffect(() => {
    if (workflowId) {
      const loadWorkflow = async () => {
        try {
          const workflow = await workflowsClient.getWorkflow(workflowId);
          setExistingWorkflow(workflow);
          setName(workflow.name);
          setDescription(workflow.description || '');
          setTriggerType(workflow.trigger_config.type as WorkflowTriggerType);
          setTriggerEvent(workflow.trigger_config.event as string || 'candidate.created');
          setCronExpression(workflow.trigger_config.cron_expression as string || '');
          setActions(workflow.actions as ActionConfig[]);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to load workflow');
        }
      };
      loadWorkflow();
    } else {
      // Add default log action for new workflows
      setActions([{ type: ActionType.Log, config: { message: 'Workflow executed' }, label: 'Log Message' }]);
    }
  }, [workflowId]);

  const handleAddAction = useCallback((actionType: ActionType) => {
    const newAction: ActionConfig = {
      type: actionType,
      config: {},
      label: ACTION_TYPES.find((t) => t.value === actionType)?.label || actionType,
    };

    // Set default config based on action type
    switch (actionType) {
      case ActionType.Log:
        newAction.config = { message: 'Log message here' };
        break;
      case ActionType.SendEmail:
        newAction.config = { to: '', subject: '', body: '' };
        break;
      case ActionType.SendWebhook:
        newAction.config = { url: '', method: 'POST', headers: {}, body: {} };
        break;
      case ActionType.AddTag:
        newAction.config = { tag_name: '' };
        break;
      case ActionType.AddNote:
        newAction.config = { content: '' };
        break;
      case ActionType.MoveStage:
        newAction.config = { stage_id: '' };
        break;
      case ActionType.Delay:
        newAction.config = { seconds: 60 };
        break;
      case ActionType.Conditional:
        newAction.config = {
          condition: { field: '', operator: 'equals', value: '' },
          then_actions: [],
          else_actions: [],
        };
        break;
    }

    setActions((prev) => [...prev, newAction]);
  }, []);

  const handleRemoveAction = useCallback((index: number) => {
    setActions((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleUpdateAction = useCallback((index: number, updatedAction: ActionConfig) => {
    setActions((prev) => {
      const newActions = [...prev];
      newActions[index] = updatedAction;
      return newActions;
    });
  }, []);

  const handleSave = useCallback(async () => {
    if (!name.trim()) {
      setError('Workflow name is required');
      return;
    }

    if (actions.length === 0) {
      setError('At least one action is required');
      return;
    }

    if (triggerType === WorkflowTriggerType.Webhook && !triggerEvent) {
      setError('Trigger event is required for webhook triggers');
      return;
    }

    if (triggerType === WorkflowTriggerType.Schedule && !cronExpression) {
      setError('Cron expression is required for schedule triggers');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const trigger: TriggerConfig = {
        type: triggerType,
      };

      if (triggerType === WorkflowTriggerType.Webhook) {
        trigger.event = triggerEvent;
      } else if (triggerType === WorkflowTriggerType.Schedule) {
        trigger.cron_expression = cronExpression;
      }

      if (workflowId) {
        // Update existing workflow
        await workflowsClient.updateWorkflow(workflowId, {
          name,
          description,
          trigger,
          actions,
        });
      } else {
        // Create new workflow
        await workflowsClient.createWorkflow({
          name,
          description,
          trigger,
          actions,
        });
      }

      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save workflow');
    } finally {
      setLoading(false);
    }
  }, [name, description, triggerType, triggerEvent, cronExpression, actions, workflowId, onSuccess]);

  const triggerActionsGrouped = ACTION_TYPES.reduce((acc, action) => {
    if (!acc[action.category]) {
      acc[action.category] = [];
    }
    acc[action.category].push(action);
    return acc;
  }, {} as Record<string, typeof ACTION_TYPES>);

  return (
    <Box sx={{ height: '70vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 3, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Workflow Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Automation Workflow"
              error={!name.trim()}
              helperText={!name.trim() ? 'Name is required' : ''}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this workflow does"
              multiline
              rows={2}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Trigger Type</InputLabel>
              <Select
                value={triggerType}
                onChange={(e) => setTriggerType(e.target.value as WorkflowTriggerType)}
                label="Trigger Type"
              >
                <MenuItem value={WorkflowTriggerType.Webhook}>Webhook Event</MenuItem>
                <MenuItem value={WorkflowTriggerType.Schedule}>Schedule</MenuItem>
                <MenuItem value={WorkflowTriggerType.Manual}>Manual</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          {triggerType === WorkflowTriggerType.Webhook && (
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Event Type</InputLabel>
                <Select
                  value={triggerEvent}
                  onChange={(e) => setTriggerEvent(e.target.value)}
                  label="Event Type"
                >
                  {TRIGGER_EVENTS.map((event) => (
                    <MenuItem key={event.value} value={event.value}>
                      {event.category} - {event.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          )}
          {triggerType === WorkflowTriggerType.Schedule && (
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Cron Expression"
                value={cronExpression}
                onChange={(e) => setCronExpression(e.target.value)}
                placeholder="0 9 * * 1-5"
                helperText="Example: 0 9 * * 1-5 (9 AM on weekdays)"
              />
            </Grid>
          )}
        </Grid>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
      </Box>

      {/* Main Content */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Action Palette */}
        <Paper
          sx={{
            width: 280,
            borderRight: '1px solid',
            borderColor: 'divider',
            overflow: 'auto',
            borderRadius: 0,
          }}
          elevation={0}
        >
          <Box sx={{ p: 2 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Add Action
            </Typography>
            <Stack spacing={2}>
              {Object.entries(triggerActionsGrouped).map(([category, actions]) => (
                <Box key={category}>
                  <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', fontWeight: 600 }}>
                    {category}
                  </Typography>
                  <Stack spacing={0.5} sx={{ mt: 1 }}>
                    {actions.map((action) => (
                      <Button
                        key={action.value}
                        fullWidth
                        variant="outlined"
                        size="small"
                        startIcon={<span>{action.icon}</span>}
                        onClick={() => handleAddAction(action.value as ActionType)}
                        sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
                      >
                        {action.label}
                      </Button>
                    ))}
                  </Stack>
                </Box>
              ))}
            </Stack>
          </Box>
        </Paper>

        {/* Canvas */}
        <Box sx={{ flex: 1, overflow: 'auto', bgcolor: 'background.default' }}>
          <WorkflowCanvas
            actions={actions}
            onUpdateAction={handleUpdateAction}
            onRemoveAction={handleRemoveAction}
          />
        </Box>
      </Box>

      {/* Footer */}
      <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: 'background.paper' }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="caption" color="text.secondary">
            {actions.length} action{actions.length !== 1 ? 's' : ''}
          </Typography>
          <Stack direction="row" spacing={2}>
            <Button
              onClick={onCancel}
              startIcon={<CancelIcon />}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              onClick={handleSave}
              startIcon={<SaveIcon />}
              disabled={loading}
            >
              {loading ? 'Saving...' : workflowId ? 'Update Workflow' : 'Create Workflow'}
            </Button>
          </Stack>
        </Stack>
      </Box>
    </Box>
  );
};

export default WorkflowBuilder;
