import React, { useState, useCallback, forwardRef, useImperativeHandle, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  Alert,
  Chip,
  Stack,
  Stepper,
  Step,
  StepLabel,
  StepIconProps,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Description as FileIcon,
  Analytics as AnalyzingIcon,
  EmojiEvents as RankingIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
} from '@mui/icons-material';
import type {
  ResumeProgressStage,
  ResumeProcessingState,
  BatchProcessingState,
} from '@/types/resume-progress';

/**
 * Stage display configuration for each processing stage
 */
interface StageConfig {
  label: string;
  description: string;
  icon: React.ComponentType<StepIconProps>;
  color: 'info' | 'success' | 'warning' | 'error' | 'default';
}

/**
 * ProcessingProgressIndicator Component Props
 */
interface ProcessingProgressIndicatorProps {
  /** Current processing stage */
  stage?: ResumeProgressStage;
  /** Progress percentage (0-100) */
  progress?: number;
  /** Current status message */
  message?: string;
  /** Whether processing has completed */
  isComplete?: boolean;
  /** Whether processing has failed */
  hasError?: boolean;
  /** Error message if processing failed */
  error?: string;
  /** Resume ID being processed */
  resumeId?: string;
  /** Batch processing state (if processing multiple resumes) */
  batchState?: BatchProcessingState;
  /** Callback when user clicks to dismiss (on complete/error) */
  onDismiss?: () => void;
  /** Whether to show detailed step-by-step progress */
  showStepper?: boolean;
  /** Custom title for the progress indicator */
  title?: string;
  /** Size variant */
  size?: 'small' | 'medium' | 'large';
}

/**
 * Imperative handle exposed by ProcessingProgressIndicator
 */
export interface ProcessingProgressIndicatorHandle {
  /**
   * Update the progress state
   */
  updateProgress: (state: Partial<ResumeProcessingState>) => void;
  /**
   * Reset the indicator to initial state
   */
  reset: () => void;
  /**
   * Set error state
   */
  setError: (error: string) => void;
  /**
   * Set complete state
   */
  setComplete: (message?: string) => void;
}

/**
 * Get stage configuration for display
 */
const getStageConfig = (stage: ResumeProgressStage): StageConfig => {
  const configs: Record<ResumeProgressStage, StageConfig> = {
    parsing: {
      label: 'Parsers',
      description: 'Extracting text and metadata from resume',
      icon: PendingIcon,
      color: 'info',
    },
    analyzing: {
      label: 'Analyzing',
      description: 'Running ML/NLP analysis and extracting insights',
      icon: AnalyzingIcon,
      color: 'warning',
    },
    ranking: {
      label: 'Ranking',
      description: 'Calculating match scores and rankings',
      icon: RankingIcon,
      color: 'info',
    },
    complete: {
      label: 'Complete',
      description: 'Processing finished successfully',
      icon: CheckIcon,
      color: 'success',
    },
    failed: {
      label: 'Failed',
      description: 'Processing encountered an error',
      icon: ErrorIcon,
      color: 'error',
    },
  };
  return configs[stage];
};

/**
 * Get step index from stage
 */
const getStepIndex = (stage: ResumeProgressStage): number => {
  const stageMap: Record<ResumeProgressStage, number> = {
    parsing: 0,
    analyzing: 1,
    ranking: 2,
    complete: 3,
    failed: 0,
  };
  return stageMap[stage];
};

/**
 * ProcessingProgressIndicator Component
 *
 * Displays real-time progress during resume processing with:
 * - Linear progress bar with percentage
 * - Step-by-step stepper showing processing stages
 * - Stage-specific icons and colors
 * - Error handling and display
 * - Success state with completion message
 * - Batch processing support
 *
 * @example
 * ```tsx
 * const indicatorRef = useRef<ProcessingProgressIndicatorHandle>(null);
 * <ProcessingProgressIndicator
 *   ref={indicatorRef}
 *   stage="analyzing"
 *   progress={45}
 *   message="Extracting skills and experience..."
 *   showStepper={true}
 * />
 *
 * // Programmatic control
 * indicatorRef.current?.updateProgress({ stage: 'ranking', progress: 75 });
 * indicatorRef.current?.setComplete('Resume processed successfully!');
 * ```
 */
const ProcessingProgressIndicator = forwardRef<
  ProcessingProgressIndicatorHandle,
  ProcessingProgressIndicatorProps
>(
  (
    {
      stage: propStage = 'parsing',
      progress: propProgress = 0,
      message: propMessage = '',
      isComplete: propIsComplete = false,
      hasError: propHasError = false,
      error: propError,
      resumeId,
      batchState,
      onDismiss,
      showStepper = true,
      title,
      size = 'medium',
    },
    ref
  ) => {
    const { t } = useTranslation();

    // Internal state for controlled/uncontrolled behavior
    const [internalState, setInternalState] = useState({
      stage: propStage,
      progress: propProgress,
      message: propMessage,
      isComplete: propIsComplete,
      hasError: propHasError,
      error: propError,
    });

    // Use internal state unless props are provided (controlled mode)
    const stage = propStage !== undefined ? propStage : internalState.stage;
    const progress = propProgress !== undefined ? propProgress : internalState.progress;
    const message = propMessage !== undefined ? propMessage : internalState.message;
    const isComplete = propIsComplete !== undefined ? propIsComplete : internalState.isComplete;
    const hasError = propHasError !== undefined ? propHasError : internalState.hasError;
    const error = propError !== undefined ? propError : internalState.error;

    /**
     * Update internal state when props change (controlled mode)
     */
    useEffect(() => {
      if (propStage !== undefined) {
        setInternalState((prev) => ({ ...prev, stage: propStage }));
      }
    }, [propStage]);

    useEffect(() => {
      if (propProgress !== undefined) {
        setInternalState((prev) => ({ ...prev, progress: propProgress }));
      }
    }, [propProgress]);

    useEffect(() => {
      if (propMessage !== undefined) {
        setInternalState((prev) => ({ ...prev, message: propMessage }));
      }
    }, [propMessage]);

    useEffect(() => {
      if (propIsComplete !== undefined) {
        setInternalState((prev) => ({ ...prev, isComplete: propIsComplete }));
      }
    }, [propIsComplete]);

    useEffect(() => {
      if (propHasError !== undefined) {
        setInternalState((prev) => ({ ...prev, hasError: propHasError }));
      }
    }, [propHasError]);

    useEffect(() => {
      if (propError !== undefined) {
        setInternalState((prev) => ({ ...prev, error: propError }));
      }
    }, [propError]);

    /**
     * Reset indicator to initial state
     */
    const handleReset = useCallback(() => {
      setInternalState({
        stage: 'parsing',
        progress: 0,
        message: '',
        isComplete: false,
        hasError: false,
        error: undefined,
      });
    }, []);

    /**
     * Expose methods via ref for parent component access
     */
    useImperativeHandle(
      ref,
      () => ({
        updateProgress: (state: Partial<ResumeProcessingState>) => {
          setInternalState((prev) => ({
            ...prev,
            ...state,
            stage: state.stage || prev.stage,
            progress: state.progress ?? prev.progress,
            message: state.message ?? prev.message,
          }));
        },
        reset: handleReset,
        setError: (errorMessage: string) => {
          setInternalState((prev) => ({
            ...prev,
            hasError: true,
            error: errorMessage,
            stage: 'failed',
          }));
        },
        setComplete: (completionMessage?: string) => {
          setInternalState((prev) => ({
            ...prev,
            isComplete: true,
            hasError: false,
            stage: 'complete',
            progress: 100,
            message: completionMessage || t('progress.complete'),
          }));
        },
      }),
      [handleReset, t]
    );

    /**
     * Get current step index for stepper
     */
    const currentStep = getStepIndex(stage);

    /**
     * Size configurations
     */
    const sizeConfig = {
      small: {
        paperPadding: 2,
        progressBarHeight: 4,
        titleVariant: 'body1' as const,
        messageVariant: 'caption' as const,
        iconSize: 'small' as const,
      },
      medium: {
        paperPadding: 3,
        progressBarHeight: 6,
        titleVariant: 'h6' as const,
        messageVariant: 'body2' as const,
        iconSize: 'medium' as const,
      },
      large: {
        paperPadding: 4,
        progressBarHeight: 8,
        titleVariant: 'h5' as const,
        messageVariant: 'body1' as const,
        iconSize: 'large' as const,
      },
    };

    const config = sizeConfig[size];

    /**
     * Get stage icon component for custom step icon
     */
    const StageIcon = (props: StepIconProps) => {
      const { active, completed, icon } = props;
      const currentStageConfig = getStageConfig(stage);

      if (completed) {
        return <CheckIcon color="success" fontSize={config.iconSize} />;
      }

      if (active) {
        const ActiveIcon = currentStageConfig.icon;
        return <ActiveIcon color={currentStageConfig.color} fontSize={config.iconSize} />;
      }

      return <FileIcon color="disabled" fontSize={config.iconSize} />;
    };

    /**
     * Stepper steps
     */
    const steps = [
      { label: 'Parsing', description: 'Extracting content' },
      { label: 'Analyzing', description: 'Processing data' },
      { label: 'Ranking', description: 'Calculating scores' },
      { label: 'Complete', description: 'Finished' },
    ];

    /**
     * Batch processing info
     */
    const renderBatchInfo = () => {
      if (!batchState) return null;

      const { total_resumes, completed_count, failed_count, progress: batchProgress } = batchState;

      return (
        <Box sx={{ mb: 2 }}>
          <Stack direction="row" spacing={1} alignItems="center" justifyContent="center">
            <Chip label={`Total: ${total_resumes}`} size="small" variant="outlined" />
            <Chip
              label={`Completed: ${completed_count}`}
              size="small"
              color="success"
              variant="outlined"
            />
            {failed_count > 0 && (
              <Chip
                label={`Failed: ${failed_count}`}
                size="small"
                color="error"
                variant="outlined"
              />
            )}
          </Stack>
        </Box>
      );
    };

    return (
      <Box sx={{ width: '100%' }}>
        <Paper
          elevation={2}
          sx={{
            p: config.paperPadding,
            border: '1px solid',
            borderColor: hasError
              ? 'error.main'
              : isComplete
                ? 'success.main'
                : 'divider',
            bgcolor: hasError ? 'error.1' : isComplete ? 'success.1' : 'background.paper',
            transition: 'all 0.3s ease-in-out',
          }}
        >
          {/* Title */}
          {title && (
            <Typography variant={config.titleVariant} gutterBottom fontWeight={600}>
              {title}
            </Typography>
          )}

          {/* Batch processing info */}
          {renderBatchInfo()}

          {/* Error Alert */}
          {hasError && error && (
            <Alert
              severity="error"
              icon={<ErrorIcon />}
              sx={{ mb: 2 }}
              action={
                onDismiss && (
                  <Typography
                    component="button"
                    onClick={onDismiss}
                    sx={{
                      background: 'none',
                      border: 'none',
                      color: 'inherit',
                      cursor: 'pointer',
                      fontSize: 'inherit',
                    }}
                  >
                    Dismiss
                  </Typography>
                )
              }
            >
              {error}
            </Alert>
          )}

          {/* Success Alert */}
          {isComplete && !hasError && (
            <Alert
              severity="success"
              icon={<CheckIcon />}
              sx={{ mb: 2 }}
              action={
                onDismiss && (
                  <Typography
                    component="button"
                    onClick={onDismiss}
                    sx={{
                      background: 'none',
                      border: 'none',
                      color: 'inherit',
                      cursor: 'pointer',
                      fontSize: 'inherit',
                    }}
                  >
                    Dismiss
                  </Typography>
                )
              }
            >
              {message || t('progress.complete')}
            </Alert>
          )}

          {/* Progress Stepper */}
          {showStepper && !hasError && !isComplete && (
            <Box sx={{ mb: 3 }}>
              <Stepper
                activeStep={currentStep}
                alternativeLabel
                sx={{
                  '& .MuiStepLabel-root .Mui-completed': {
                    color: 'success.main',
                  },
                  '& .MuiStepLabel-root .Mui-active': {
                    color: 'primary.main',
                  },
                }}
              >
                {steps.map((step, index) => (
                  <Step key={index} completed={index < currentStep}>
                    <StepLabel StepIconComponent={StageIcon}>{step.label}</StepLabel>
                  </Step>
                ))}
              </Stepper>
            </Box>
          )}

          {/* Progress Bar */}
          {!hasError && !isComplete && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress
                variant="determinate"
                value={progress}
                sx={{
                  height: config.progressBarHeight,
                  borderRadius: config.progressBarHeight / 2,
                  backgroundColor: 'action.hover',
                  '& .MuiLinearProgress-bar': {
                    transition: 'transform 0.3s ease',
                  },
                }}
              />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                <Typography variant={config.messageVariant} color="text.secondary">
                  {message || getStageConfig(stage).description}
                </Typography>
                <Typography variant={config.messageVariant} color="text.secondary" fontWeight={600}>
                  {progress}%
                </Typography>
              </Box>
            </Box>
          )}

          {/* Resume ID */}
          {resumeId && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
              {t('progress.resumeId')}: {resumeId}
            </Typography>
          )}
        </Paper>
      </Box>
    );
  }
);

ProcessingProgressIndicator.displayName = 'ProcessingProgressIndicator';

export default ProcessingProgressIndicator;
