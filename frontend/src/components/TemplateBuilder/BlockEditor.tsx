/**
 * Block Editor Component
 *
 * Provides specialized editing interfaces for different template block types:
 * - Text blocks: multiline text editor with variable insertion
 * - Heading blocks: text editor with heading level selector
 * - Button blocks: text, URL, and style editor
 * - Conditional blocks: condition builder with nested block support
 */

import { useState, useRef } from 'react';
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
  TextFields as TextIcon,
} from '@mui/icons-material';
import { VariableSelectorButton } from './VariableSelector';
import type {
  TemplateBlock,
  TextBlock,
  HeadingBlock,
  ButtonBlock,
  ConditionalBlock,
  ConditionalOperator,
} from '../../types/templates';

interface BlockEditorProps {
  block: TemplateBlock;
  onUpdate: (updates: Partial<TemplateBlock>) => void;
  onDelete?: () => void;
  readOnly?: boolean;
}

/**
 * Main BlockEditor component
 *
 * Routes to the appropriate specialized editor based on block type
 */
export function BlockEditor({
  block,
  onUpdate,
  onDelete,
  readOnly = false,
}: BlockEditorProps) {
  switch (block.type) {
    case 'text':
      return (
        <TextBlockEditor
          block={block as TextBlock}
          onUpdate={onUpdate}
          onDelete={onDelete}
          readOnly={readOnly}
        />
      );
    case 'heading':
      return (
        <HeadingBlockEditor
          block={block as HeadingBlock}
          onUpdate={onUpdate}
          onDelete={onDelete}
          readOnly={readOnly}
        />
      );
    case 'button':
      return (
        <ButtonBlockEditor
          block={block as ButtonBlock}
          onUpdate={onUpdate}
          onDelete={onDelete}
          readOnly={readOnly}
        />
      );
    case 'conditional':
      return (
        <ConditionalBlockEditor
          block={block as ConditionalBlock}
          onUpdate={onUpdate}
          onDelete={onDelete}
          readOnly={readOnly}
        />
      );
    default:
      return (
        <Box sx={{ p: 2 }}>
          <Typography color="error">
            Unknown block type: {(block as TemplateBlock).type}
          </Typography>
        </Box>
      );
  }
}

/**
 * Text Block Editor
 *
 * Multiline text editor with support for variable syntax {{variable_name}}
 */
function TextBlockEditor({
  block,
  onUpdate,
  onDelete,
  readOnly,
}: {
  block: TextBlock;
  onUpdate: (updates: Partial<TextBlock>) => void;
  onDelete?: () => void;
  readOnly?: boolean;
}) {
  const textFieldRef = useRef<HTMLTextAreaElement>(null);

  const handleVariableSelect = (variableTag: string) => {
    const textarea = textFieldRef.current;
    if (!textarea) {
      // Fallback: append to end
      onUpdate({ content: (block.content || '') + variableTag });
      return;
    }

    const start = textarea.selectionStart || 0;
    const end = textarea.selectionEnd || 0;
    const currentContent = block.content || '';
    const newContent =
      currentContent.substring(0, start) +
      variableTag +
      currentContent.substring(end);

    onUpdate({ content: newContent });

    // Set cursor position after the inserted variable
    setTimeout(() => {
      const newCursorPos = start + variableTag.length;
      textarea.setSelectionRange(newCursorPos, newCursorPos);
      textarea.focus();
    }, 0);
  };

  return (
    <Stack spacing={2}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="caption" color="text.secondary" fontWeight="medium">
          TEXT BLOCK
        </Typography>
        {onDelete && !readOnly && (
          <IconButton size="small" color="error" onClick={onDelete}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        )}
      </Box>

      <TextField
        inputRef={textFieldRef}
        fullWidth
        multiline
        rows={4}
        value={block.content || ''}
        onChange={(e) => onUpdate({ content: e.target.value })}
        placeholder="Enter text content. Use {{variable_name}} for dynamic content."
        variant="outlined"
        disabled={readOnly}
        helperText="Tip: Use the button below to insert variables"
      />

      {!readOnly && (
        <Box>
          <VariableSelectorButton onVariableSelect={handleVariableSelect} />
        </Box>
      )}
    </Stack>
  );
}

/**
 * Heading Block Editor
 *
 * Text editor with heading level selector (H1-H6)
 */
function HeadingBlockEditor({
  block,
  onUpdate,
  onDelete,
  readOnly,
}: {
  block: HeadingBlock;
  onUpdate: (updates: Partial<HeadingBlock>) => void;
  onDelete?: () => void;
  readOnly?: boolean;
}) {
  const level = block.level || 2;
  const textFieldRef = useRef<HTMLInputElement>(null);

  const handleVariableSelect = (variableTag: string) => {
    const input = textFieldRef.current;
    if (!input) {
      // Fallback: append to end
      onUpdate({ content: (block.content || '') + variableTag });
      return;
    }

    const start = input.selectionStart || 0;
    const end = input.selectionEnd || 0;
    const currentContent = block.content || '';
    const newContent =
      currentContent.substring(0, start) +
      variableTag +
      currentContent.substring(end);

    onUpdate({ content: newContent });

    // Set cursor position after the inserted variable
    setTimeout(() => {
      const newCursorPos = start + variableTag.length;
      input.setSelectionRange(newCursorPos, newCursorPos);
      input.focus();
    }, 0);
  };

  return (
    <Stack spacing={2}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="caption" color="text.secondary" fontWeight="medium">
          HEADING BLOCK
        </Typography>
        {onDelete && !readOnly && (
          <IconButton size="small" color="error" onClick={onDelete}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        )}
      </Box>

      <Box sx={{ display: 'flex', gap: 2 }}>
        <TextField
          inputRef={textFieldRef}
          fullWidth
          value={block.content || ''}
          onChange={(e) => onUpdate({ content: e.target.value })}
          placeholder="Enter heading text"
          variant="outlined"
          disabled={readOnly}
        />
        <FormControl sx={{ minWidth: 100 }}>
          <InputLabel>Level</InputLabel>
          <Select
            value={level}
            label="Level"
            onChange={(e) => onUpdate({ level: e.target.value as HeadingBlock['level'] })}
            disabled={readOnly}
          >
            <MenuItem value={1}>H1</MenuItem>
            <MenuItem value={2}>H2</MenuItem>
            <MenuItem value={3}>H3</MenuItem>
            <MenuItem value={4}>H4</MenuItem>
            <MenuItem value={5}>H5</MenuItem>
            <MenuItem value={6}>H6</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {!readOnly && (
        <Box>
          <VariableSelectorButton onVariableSelect={handleVariableSelect} />
        </Box>
      )}
    </Stack>
  );
}

/**
 * Button Block Editor
 *
 * Editor for button text, URL, and style
 */
function ButtonBlockEditor({
  block,
  onUpdate,
  onDelete,
  readOnly,
}: {
  block: ButtonBlock;
  onUpdate: (updates: Partial<ButtonBlock>) => void;
  onDelete?: () => void;
  readOnly?: boolean;
}) {
  const style = block.style || 'primary';
  const contentFieldRef = useRef<HTMLInputElement>(null);
  const hrefFieldRef = useRef<HTMLInputElement>(null);

  const handleContentVariableSelect = (variableTag: string) => {
    const input = contentFieldRef.current;
    if (!input) {
      onUpdate({ content: (block.content || '') + variableTag });
      return;
    }

    const start = input.selectionStart || 0;
    const end = input.selectionEnd || 0;
    const currentContent = block.content || '';
    const newContent =
      currentContent.substring(0, start) +
      variableTag +
      currentContent.substring(end);

    onUpdate({ content: newContent });

    setTimeout(() => {
      const newCursorPos = start + variableTag.length;
      input.setSelectionRange(newCursorPos, newCursorPos);
      input.focus();
    }, 0);
  };

  const handleHrefVariableSelect = (variableTag: string) => {
    const input = hrefFieldRef.current;
    if (!input) {
      onUpdate({ href: (block.href || '') + variableTag });
      return;
    }

    const start = input.selectionStart || 0;
    const end = input.selectionEnd || 0;
    const currentHref = block.href || '';
    const newHref =
      currentHref.substring(0, start) +
      variableTag +
      currentHref.substring(end);

    onUpdate({ href: newHref });

    setTimeout(() => {
      const newCursorPos = start + variableTag.length;
      input.setSelectionRange(newCursorPos, newCursorPos);
      input.focus();
    }, 0);
  };

  return (
    <Stack spacing={2}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="caption" color="text.secondary" fontWeight="medium">
          BUTTON BLOCK
        </Typography>
        {onDelete && !readOnly && (
          <IconButton size="small" color="error" onClick={onDelete}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        )}
      </Box>

      <Box>
        <TextField
          inputRef={contentFieldRef}
          fullWidth
          label="Button Text"
          value={block.content || ''}
          onChange={(e) => onUpdate({ content: e.target.value })}
          placeholder="Click Here"
          variant="outlined"
          disabled={readOnly}
        />
        {!readOnly && (
          <Box sx={{ mt: 1 }}>
            <VariableSelectorButton onVariableSelect={handleContentVariableSelect} />
          </Box>
        )}
      </Box>

      <Box>
        <TextField
          inputRef={hrefFieldRef}
          fullWidth
          label="Button URL"
          value={block.href || ''}
          onChange={(e) => onUpdate({ href: e.target.value })}
          placeholder="https://example.com"
          variant="outlined"
          disabled={readOnly}
          helperText="Supports variables like {{application_url}}, {{interview_link}}, etc."
        />
        {!readOnly && (
          <Box sx={{ mt: 1 }}>
            <VariableSelectorButton onVariableSelect={handleHrefVariableSelect} />
          </Box>
        )}
      </Box>

      <FormControl fullWidth>
        <InputLabel>Button Style</InputLabel>
        <Select
          value={style}
          label="Button Style"
          onChange={(e) => onUpdate({ style: e.target.value as ButtonBlock['style'] })}
          disabled={readOnly}
        >
          <MenuItem value="primary">Primary (Solid)</MenuItem>
          <MenuItem value="secondary">Secondary (Muted)</MenuItem>
          <MenuItem value="outline">Outline</MenuItem>
        </Select>
      </FormControl>
    </Stack>
  );
}

/**
 * Conditional Block Editor
 *
 * Editor for conditional logic with if/else branches
 */
function ConditionalBlockEditor({
  block,
  onUpdate,
  onDelete,
  readOnly,
}: {
  block: ConditionalBlock;
  onUpdate: (updates: Partial<ConditionalBlock>) => void;
  onDelete?: () => void;
  readOnly?: boolean;
}) {
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

export default BlockEditor;
