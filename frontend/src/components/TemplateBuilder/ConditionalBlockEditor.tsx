/**
 * Conditional Block Editor Component
 *
 * Provides an interface for creating and editing conditional logic blocks
 * with if/else branches based on pipeline stage or candidate attributes.
 *
 * Features:
 * - Field/operator/value condition builder
 * - Support for various comparison operators (eq, ne, gt, lt, in, contains, etc.)
 * - True/false branch editing with nested blocks
 * - Visual distinction between true and false branches
 * - Read-only mode support
 */

import { useState } from 'react';
import {
  Box,
  TextField,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Button,
  IconButton,
  Paper,
  Divider,
  Chip,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import type {
  TemplateBlock,
  TextBlock,
  ConditionalBlock,
  ConditionalOperator,
} from '../../types/templates';

interface ConditionalBlockEditorProps {
  block: ConditionalBlock;
  onUpdate: (updates: Partial<ConditionalBlock>) => void;
  onDelete?: () => void;
  readOnly?: boolean;
}

/**
 * Conditional Block Editor
 *
 * Editor for conditional logic with if/else branches.
 * Allows users to define conditions based on candidate or pipeline data
 * and specify different content for true/false outcomes.
 */
export function ConditionalBlockEditor({
  block,
  onUpdate,
  onDelete,
  readOnly = false,
}: ConditionalBlockEditorProps) {
  const [showTrueBlocks, setShowTrueBlocks] = useState(true);
  const [showFalseBlocks, setShowFalseBlocks] = useState(false);

  const condition = block.condition || {
    field: 'pipeline_stage',
    operator: 'eq',
    value: '',
  };

  const handleConditionUpdate = (updates: Partial<typeof condition>) => {
    onUpdate({
      condition: { ...condition, ...updates },
    });
  };

  const handleAddTrueBlock = () => {
    const trueBlocks = block.true_blocks || [];
    const newBlock: TextBlock = {
      id: `block-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: 'text',
      content: 'Enter content to show when condition is true...',
    };
    onUpdate({
      true_blocks: [...trueBlocks, newBlock],
    });
  };

  const handleAddFalseBlock = () => {
    const falseBlocks = block.false_blocks || [];
    const newBlock: TextBlock = {
      id: `block-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: 'text',
      content: 'Enter content to show when condition is false...',
    };
    onUpdate({
      false_blocks: [...falseBlocks, newBlock],
    });
  };

  const handleDeleteTrueBlock = (index: number) => {
    const trueBlocks = block.true_blocks || [];
    onUpdate({
      true_blocks: trueBlocks.filter((_, i) => i !== index),
    });
  };

  const handleDeleteFalseBlock = (index: number) => {
    const falseBlocks = block.false_blocks || [];
    onUpdate({
      false_blocks: falseBlocks.filter((_, i) => i !== index),
    });
  };

  const handleUpdateTrueBlock = (index: number, updates: Partial<TemplateBlock>) => {
    const trueBlocks = block.true_blocks || [];
    onUpdate({
      true_blocks: trueBlocks.map((b, i) => (i === index ? { ...b, ...updates } : b)),
    });
  };

  const handleUpdateFalseBlock = (index: number, updates: Partial<TemplateBlock>) => {
    const falseBlocks = block.false_blocks || [];
    onUpdate({
      false_blocks: falseBlocks.map((b, i) => (i === index ? { ...b, ...updates } : b)),
    });
  };

  return (
    <Stack spacing={2}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="caption" color="text.secondary" fontWeight="medium">
          CONDITIONAL BLOCK
        </Typography>
        {onDelete && !readOnly && (
          <IconButton size="small" color="error" onClick={onDelete}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        )}
      </Box>

      {/* Condition Configuration */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="body2" fontWeight="medium" gutterBottom>
          Condition
        </Typography>
        <Stack spacing={2}>
          <TextField
            fullWidth
            label="Field"
            value={condition.field}
            onChange={(e) => handleConditionUpdate({ field: e.target.value })}
            placeholder="pipeline_stage"
            variant="outlined"
            size="small"
            disabled={readOnly}
            helperText="Variable to check (e.g., pipeline_stage, candidate_score)"
          />

          <FormControl fullWidth size="small">
            <InputLabel>Operator</InputLabel>
            <Select
              value={condition.operator}
              label="Operator"
              onChange={(e) =>
                handleConditionUpdate({ operator: e.target.value as ConditionalOperator })
              }
              disabled={readOnly}
            >
              <MenuItem value="eq">Equal to (=)</MenuItem>
              <MenuItem value="ne">Not equal to (≠)</MenuItem>
              <MenuItem value="gt">Greater than (&gt;)</MenuItem>
              <MenuItem value="lt">Less than (&lt;)</MenuItem>
              <MenuItem value="gte">Greater than or equal to (≥)</MenuItem>
              <MenuItem value="lte">Less than or equal to (≤)</MenuItem>
              <MenuItem value="in">In array</MenuItem>
              <MenuItem value="not_in">Not in array</MenuItem>
              <MenuItem value="contains">Contains</MenuItem>
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Value"
            value={
              Array.isArray(condition.value)
                ? condition.value.join(', ')
                : String(condition.value)
            }
            onChange={(e) => {
              const val = e.target.value;
              // If operator is 'in' or 'not_in', treat as comma-separated array
              if (condition.operator === 'in' || condition.operator === 'not_in') {
                handleConditionUpdate({
                  value: val.split(',').map((v) => v.trim()),
                });
              } else {
                handleConditionUpdate({ value: val });
              }
            }}
            placeholder={
              condition.operator === 'in' || condition.operator === 'not_in'
                ? 'value1, value2, value3'
                : 'value'
            }
            variant="outlined"
            size="small"
            disabled={readOnly}
            helperText={
              condition.operator === 'in' || condition.operator === 'not_in'
                ? 'Comma-separated values for array comparison'
                : 'Single value to compare against'
            }
          />
        </Stack>
      </Paper>

      <Divider />

      {/* True Branch */}
      <Box>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 1,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip label="IF TRUE" size="small" color="success" />
            <Typography variant="caption" color="text.secondary">
              {block.true_blocks?.length || 0} block(s)
            </Typography>
          </Box>
          <Button
            size="small"
            startIcon={<AddIcon />}
            onClick={handleAddTrueBlock}
            disabled={readOnly}
          >
            Add Block
          </Button>
        </Box>

        {block.true_blocks && block.true_blocks.length > 0 ? (
          <Stack spacing={1}>
            {block.true_blocks.map((nestedBlock, index) => (
              <Paper key={nestedBlock.id} variant="outlined" sx={{ p: 1.5, bgcolor: 'success.50' }}>
                <Stack spacing={1}>
                  <Typography variant="caption" color="text.secondary">
                    {nestedBlock.type.toUpperCase()}
                  </Typography>
                  <TextField
                    fullWidth
                    size="small"
                    multiline
                    rows={2}
                    value={nestedBlock.content || ''}
                    onChange={(e) =>
                      handleUpdateTrueBlock(index, { content: e.target.value })
                    }
                    placeholder={`Enter ${nestedBlock.type} content...`}
                    disabled={readOnly}
                  />
                  {!readOnly && (
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteTrueBlock(index)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  )}
                </Stack>
              </Paper>
            ))}
          </Stack>
        ) : (
          <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', bgcolor: 'action.hover' }}>
            <Typography variant="body2" color="text.secondary">
              No blocks added yet. Click "Add Block" to add content for true condition.
            </Typography>
          </Paper>
        )}
      </Box>

      <Divider />

      {/* False Branch */}
      <Box>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 1,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip label="IF FALSE" size="small" color="error" />
            <Typography variant="caption" color="text.secondary">
              {block.false_blocks?.length || 0} block(s)
            </Typography>
          </Box>
          <Button
            size="small"
            startIcon={<AddIcon />}
            onClick={handleAddFalseBlock}
            disabled={readOnly}
          >
            Add Block
          </Button>
        </Box>

        {block.false_blocks && block.false_blocks.length > 0 ? (
          <Stack spacing={1}>
            {block.false_blocks.map((nestedBlock, index) => (
              <Paper key={nestedBlock.id} variant="outlined" sx={{ p: 1.5, bgcolor: 'error.50' }}>
                <Stack spacing={1}>
                  <Typography variant="caption" color="text.secondary">
                    {nestedBlock.type.toUpperCase()}
                  </Typography>
                  <TextField
                    fullWidth
                    size="small"
                    multiline
                    rows={2}
                    value={nestedBlock.content || ''}
                    onChange={(e) =>
                      handleUpdateFalseBlock(index, { content: e.target.value })
                    }
                    placeholder={`Enter ${nestedBlock.type} content...`}
                    disabled={readOnly}
                  />
                  {!readOnly && (
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteFalseBlock(index)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  )}
                </Stack>
              </Paper>
            ))}
          </Stack>
        ) : (
          <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', bgcolor: 'action.hover' }}>
            <Typography variant="body2" color="text.secondary">
              No blocks added yet. Click "Add Block" to add content for false condition.
            </Typography>
          </Paper>
        )}
      </Box>
    </Stack>
  );
}

export default ConditionalBlockEditor;
