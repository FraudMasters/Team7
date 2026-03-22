/**
 * Template Type Definitions
 *
 * This module contains TypeScript type definitions for the notification template system,
 * including template blocks, conditional logic, variable definitions, and template structures.
 *
 * @example
 * ```ts
 * import type {
 *   TemplateBlock,
 *   ConditionalBlock,
 *   TemplateVariable,
 *   NotificationTemplateType
 * } from '@/types/templates';
 *
 * const conditionalBlock: ConditionalBlock = {
 *   id: 'block-1',
 *   type: 'conditional',
 *   condition: {
 *     field: 'pipeline_stage',
 *     operator: 'eq',
 *     value: 'interview_scheduled'
 *   },
 *   true_blocks: [
 *     {
 *       id: 'block-2',
 *       type: 'text',
 *       content: 'Your interview is scheduled for {{interview_date}}'
 *     }
 *   ]
 * };
 * ```
 */

/**
 * Notification template type enum
 *
 * Defines the delivery channel for a notification template.
 */
export type NotificationTemplateType = 'email' | 'sms';

/**
 * Template category enum
 *
 * Categorizes templates by their purpose in the recruitment workflow.
 */
export type NotificationTemplateCategory =
  | 'outreach'
  | 'interview'
  | 'rejection'
  | 'offer'
  | 'follow_up'
  | 'feedback'
  | 'other';

/**
 * Pipeline stage enum
 *
 * Represents stages in the candidate hiring pipeline.
 * Templates can be associated with specific pipeline stages
 * for automatic triggering.
 */
export type PipelineStage =
  | 'application_received'
  | 'screening'
  | 'interview_scheduled'
  | 'interview_completed'
  | 'offer_extended'
  | 'offer_accepted'
  | 'rejected'
  | 'withdrawn';

/**
 * Conditional operator enum
 *
 * Operators used for evaluating conditional logic in template blocks.
 */
export type ConditionalOperator =
  | 'eq'        // Equal to
  | 'ne'        // Not equal to
  | 'gt'        // Greater than
  | 'lt'        // Less than
  | 'gte'       // Greater than or equal to
  | 'lte'       // Less than or equal to
  | 'in'        // Value is in array
  | 'not_in'    // Value is not in array
  | 'contains'; // String contains substring

/**
 * Template block type enum
 *
 * Defines the different types of content blocks available in templates.
 */
export type TemplateBlockType = 'text' | 'heading' | 'button' | 'conditional';

/**
 * Template variable value type
 *
 * Supported types for template variable values.
 */
export type TemplateVariableValue = string | number | boolean | string[];

/**
 * Conditional logic configuration
 *
 * Defines a condition that can be evaluated to show/hide content blocks.
 */
export interface TemplateCondition {
  /**
   * The field/variable to evaluate
   * @example 'pipeline_stage', 'candidate_score', 'has_referral'
   */
  field: string;

  /**
   * The comparison operator to use
   */
  operator: ConditionalOperator;

  /**
   * The value to compare against
   * Can be a single value or array of values (for 'in' and 'not_in' operators)
   */
  value: TemplateVariableValue;
}

/**
 * Base template block interface
 *
 * Common properties shared by all template block types.
 */
export interface BaseTemplateBlock {
  /**
   * Unique identifier for the block
   */
  id: string;

  /**
   * The type of block
   */
  type: TemplateBlockType;

  /**
   * Optional content for text, heading, and button blocks
   * Supports template variable syntax: {{variable_name}}
   */
  content?: string;

  /**
   * Optional additional properties (e.g., href for buttons, level for headings)
   */
  [key: string]: unknown;
}

/**
 * Text block
 *
 * A simple text content block with variable support.
 */
export interface TextBlock extends BaseTemplateBlock {
  type: 'text';
  content: string;
}

/**
 * Heading block
 *
 * A heading content block with optional level specification.
 */
export interface HeadingBlock extends BaseTemplateBlock {
  type: 'heading';
  content: string;
  level?: 1 | 2 | 3 | 4 | 5 | 6;
}

/**
 * Button block
 *
 * An interactive button block with optional link.
 */
export interface ButtonBlock extends BaseTemplateBlock {
  type: 'button';
  content: string;
  href?: string;
  style?: 'primary' | 'secondary' | 'outline';
}

/**
 * Conditional block
 *
 * A block that conditionally shows/hides nested content blocks
 * based on variable values.
 */
export interface ConditionalBlock extends BaseTemplateBlock {
  type: 'conditional';

  /**
   * The condition to evaluate
   */
  condition: TemplateCondition;

  /**
   * Blocks to show if condition evaluates to true
   */
  true_blocks?: TemplateBlock[];

  /**
   * Blocks to show if condition evaluates to false
   */
  false_blocks?: TemplateBlock[];
}

/**
 * Template block union type
 *
 * Represents any valid template block type.
 */
export type TemplateBlock = TextBlock | HeadingBlock | ButtonBlock | ConditionalBlock;

/**
 * Template variable definition
 *
 * Describes a variable that can be used in a template.
 */
export interface TemplateVariable {
  /**
   * Variable name (used in {{variable_name}} syntax)
   */
  name: string;

  /**
   * Human-readable label for the variable
   */
  label?: string;

  /**
   * Description of what the variable represents
   */
  description?: string;

  /**
   * The data type of the variable
   */
  type?: 'string' | 'number' | 'boolean' | 'date' | 'array';

  /**
   * Whether the variable is required for rendering
   */
  required?: boolean;

  /**
   * Default value if not provided
   */
  default_value?: TemplateVariableValue;

  /**
   * Example value for preview/documentation
   */
  example?: TemplateVariableValue;
}

/**
 * Template variable context
 *
 * A collection of variable values to be substituted in a template.
 */
export type TemplateVariableContext = Record<string, TemplateVariableValue>;

/**
 * Template validation error
 *
 * Describes a validation error in a template configuration.
 */
export interface TemplateValidationError {
  /**
   * The field or block ID where the error occurred
   */
  field: string;

  /**
   * Error message
   */
  message: string;

  /**
   * Error code for programmatic handling
   */
  code?: string;
}

/**
 * Template validation result
 *
 * Result of validating a template configuration.
 */
export interface TemplateValidationResult {
  /**
   * Whether the template is valid
   */
  valid: boolean;

  /**
   * Array of validation errors (empty if valid)
   */
  errors: TemplateValidationError[];

  /**
   * Array of warning messages (non-blocking issues)
   */
  warnings?: string[];
}
