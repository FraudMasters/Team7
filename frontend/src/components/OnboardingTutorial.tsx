/**
 * OnboardingTutorial Component
 *
 * Interactive step-by-step tutorial for new hiring managers to learn
 * the key features of the Hiring Manager Portal.
 *
 * Features:
 * - Multi-step guided tour with progress indicator
 * - Mobile-optimized with 44px touch targets
 * - Persistent completion state (localStorage)
 * - Optional auto-start for first-time users
 * - Keyboard navigation support
 * - Skip and restart functionality
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Paper,
  Stack,
  IconButton,
  LinearProgress,
  Chip,
  Fade,
  Slide,
  useTheme,
  useMediaQuery,
} from '@/components/ui';
import { useTranslation } from 'react-i18next';
import {
  Close as CloseIcon,
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  Dashboard as DashboardIcon,
  RateReview as ReviewIcon,
  CheckCircle as ApproveIcon,
  Schedule as ScheduleIcon,
  PlayArrow as PlayArrowIcon,
  Replay as ReplayIcon,
  TouchApp as TouchAppIcon,
  Help as HelpIcon,
} from '@mui/icons-material';

/**
 * Tutorial step interface
 */
interface TutorialStep {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  tips: string[];
  highlight?: string;
}

/**
 * OnboardingTutorial Component Props
 */
interface OnboardingTutorialProps {
  /** Whether the tutorial is open */
  open: boolean;
  /** Callback when tutorial is closed */
  onClose: () => void;
  /** Callback when tutorial is completed */
  onComplete?: () => void;
  /** Whether to auto-start on first visit */
  autoStart?: boolean;
  /** Storage key for completion state */
  storageKey?: string;
}

/**
 * Local storage key for tutorial completion
 */
const TUTORIAL_COMPLETED_KEY = 'hiring_manager_tutorial_completed';

/**
 * Default tutorial steps for hiring manager portal
 */
const getTutorialSteps = (t: (key: string, options?: Record<string, unknown>) => string): TutorialStep[] => [
  {
    id: 'welcome',
    title: t('onboarding.welcomeTitle', { defaultValue: 'Welcome to Hiring Manager Portal' }),
    description: t('onboarding.welcomeDesc', {
      defaultValue: 'This quick tutorial will guide you through the essential features to help you review candidates efficiently.',
    }),
    icon: <HelpIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
    tips: [
      t('onboarding.welcomeTip1', { defaultValue: 'Review candidates pending your approval' }),
      t('onboarding.welcomeTip2', { defaultValue: 'View recruiter feedback and team consensus' }),
      t('onboarding.welcomeTip3', { defaultValue: 'Schedule and manage interviews' }),
    ],
  },
  {
    id: 'dashboard',
    title: t('onboarding.dashboardTitle', { defaultValue: 'Dashboard Overview' }),
    description: t('onboarding.dashboardDesc', {
      defaultValue: 'Your dashboard provides a quick overview of candidates awaiting your review and upcoming interviews.',
    }),
    icon: <DashboardIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
    tips: [
      t('onboarding.dashboardTip1', { defaultValue: 'See pending review count at a glance' }),
      t('onboarding.dashboardTip2', { defaultValue: 'Quick access to urgent candidates' }),
      t('onboarding.dashboardTip3', { defaultValue: 'View recent activity and statistics' }),
    ],
    highlight: '/hiring-manager/dashboard',
  },
  {
    id: 'review-queue',
    title: t('onboarding.reviewQueueTitle', { defaultValue: 'Candidate Review Queue' }),
    description: t('onboarding.reviewQueueDesc', {
      defaultValue: 'Browse candidates that need your review. Each card shows key information to help you make quick decisions.',
    }),
    icon: <ReviewIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
    tips: [
      t('onboarding.reviewQueueTip1', { defaultValue: 'View match scores and recruiter feedback' }),
      t('onboarding.reviewQueueTip2', { defaultValue: 'Filter by vacancy, priority, or search by name' }),
      t('onboarding.reviewQueueTip3', { defaultValue: 'Tap a card to see full candidate details' }),
    ],
    highlight: '/hiring-manager/review-queue',
  },
  {
    id: 'one-click-actions',
    title: t('onboarding.actionsTitle', { defaultValue: 'One-Click Approve/Reject' }),
    description: t('onboarding.actionsDesc', {
      defaultValue: 'Make quick decisions with one-click approve or reject buttons. Add optional rationale for detailed feedback.',
    }),
    icon: <ApproveIcon sx={{ fontSize: 48, color: 'success.main' }} />,
    tips: [
      t('onboarding.actionsTip1', { defaultValue: 'Tap Approve or Reject for quick decisions' }),
      t('onboarding.actionsTip2', { defaultValue: 'Add rationale to explain your decision' }),
      t('onboarding.actionsTip3', { defaultValue: 'Select rejection reasons from predefined options' }),
    ],
  },
  {
    id: 'swipe-gestures',
    title: t('onboarding.swipeTitle', { defaultValue: 'Mobile Swipe Gestures' }),
    description: t('onboarding.swipeDesc', {
      defaultValue: 'On tablets, you can swipe candidate cards left to reject or right to approve for faster mobile review.',
    }),
    icon: <TouchAppIcon sx={{ fontSize: 48, color: 'info.main' }} />,
    tips: [
      t('onboarding.swipeTip1', { defaultValue: 'Swipe right to approve a candidate' }),
      t('onboarding.swipeTip2', { defaultValue: 'Swipe left to reject a candidate' }),
      t('onboarding.swipeTip3', { defaultValue: 'Tap to view full candidate details first' }),
    ],
  },
  {
    id: 'interviews',
    title: t('onboarding.interviewsTitle', { defaultValue: 'Interview Scheduling' }),
    description: t('onboarding.interviewsDesc', {
      defaultValue: 'View your upcoming interviews and schedule new ones with candidates directly from the portal.',
    }),
    icon: <ScheduleIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
    tips: [
      t('onboarding.interviewsTip1', { defaultValue: 'View interviews in calendar or list format' }),
      t('onboarding.interviewsTip2', { defaultValue: 'Schedule interviews with approved candidates' }),
      t('onboarding.interviewsTip3', { defaultValue: 'Sync with your calendar application' }),
    ],
    highlight: '/hiring-manager/schedule',
  },
  {
    id: 'ready',
    title: t('onboarding.readyTitle', { defaultValue: "You're All Set!" }),
    description: t('onboarding.readyDesc', {
      defaultValue: "You're ready to start reviewing candidates. Remember, you can always access this tutorial from the Help menu.",
    }),
    icon: <PlayArrowIcon sx={{ fontSize: 48, color: 'success.main' }} />,
    tips: [
      t('onboarding.readyTip1', { defaultValue: 'Start with your Review Queue' }),
      t('onboarding.readyTip2', { defaultValue: 'Use the mobile app for on-the-go reviews' }),
      t('onboarding.readyTip3', { defaultValue: 'Access Help anytime from Settings' }),
    ],
  },
];

/**
 * Slide transition for Dialog
 */
const SlideTransition = React.forwardRef(function Transition(
  props: { children: React.ReactElement } & { in?: boolean },
  ref: React.Ref<unknown>
) {
  return <Slide direction="up" ref={ref} {...props} />;
});

/**
 * OnboardingTutorial Component
 *
 * @example
 * ```tsx
 * <OnboardingTutorial
 *   open={showTutorial}
 *   onClose={() => setShowTutorial(false)}
 *   onComplete={() => trackTutorialCompletion()}
 *   autoStart
 * />
 * ```
 */
const OnboardingTutorial: React.FC<OnboardingTutorialProps> = ({
  open,
  onClose,
  onComplete,
  autoStart = false,
  storageKey = TUTORIAL_COMPLETED_KEY,
}) => {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  // Get tutorial steps with translations
  const steps = getTutorialSteps(t);

  // State
  const [currentStep, setCurrentStep] = useState(0);
  const [hasCompleted, setHasCompleted] = useState(false);

  // Check if tutorial was previously completed
  useEffect(() => {
    const completed = localStorage.getItem(storageKey) === 'true';
    setHasCompleted(completed);
  }, [storageKey]);

  // Current step data
  const step = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === steps.length - 1;

  /**
   * Handle next step
   */
  const handleNext = useCallback(() => {
    if (currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
    }
  }, [currentStep, steps.length]);

  /**
   * Handle previous step
   */
  const handlePrevious = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  }, [currentStep]);

  /**
   * Handle skip tutorial
   */
  const handleSkip = useCallback(() => {
    localStorage.setItem(storageKey, 'true');
    setHasCompleted(true);
    onClose();
  }, [storageKey, onClose]);

  /**
   * Handle complete tutorial
   */
  const handleComplete = useCallback(() => {
    localStorage.setItem(storageKey, 'true');
    setHasCompleted(true);
    onComplete?.();
    onClose();
  }, [storageKey, onComplete, onClose]);

  /**
   * Handle restart tutorial
   */
  const handleRestart = useCallback(() => {
    localStorage.removeItem(storageKey);
    setHasCompleted(false);
    setCurrentStep(0);
  }, [storageKey]);

  /**
   * Handle keyboard navigation
   */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!open) return;

      switch (event.key) {
        case 'ArrowRight':
        case 'Enter':
          if (!isLastStep) {
            handleNext();
          } else {
            handleComplete();
          }
          break;
        case 'ArrowLeft':
          handlePrevious();
          break;
        case 'Escape':
          handleSkip();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, isLastStep, handleNext, handlePrevious, handleSkip, handleComplete]);

  /**
   * Reset step when dialog opens
   */
  useEffect(() => {
    if (open) {
      setCurrentStep(0);
    }
  }, [open]);

  return (
    <Dialog
      open={open}
      onClose={handleSkip}
      maxWidth="sm"
      fullWidth
      fullScreen={isMobile}
      TransitionComponent={SlideTransition}
      aria-labelledby="onboarding-tutorial-title"
      aria-describedby="onboarding-tutorial-description"
      PaperProps={{
        sx: {
          borderRadius: isMobile ? 0 : 3,
          overflow: 'hidden',
        },
      }}
    >
      {/* Progress Bar */}
      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{
          height: 4,
          bgcolor: 'grey.200',
          '& .MuiLinearProgress-bar': {
            transition: 'transform 0.3s ease',
          },
        }}
      />

      {/* Header */}
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          pb: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            label={t('onboarding.stepOf', {
              defaultValue: 'Step {{current}} of {{total}}',
              current: currentStep + 1,
              total: steps.length,
            })}
            size="small"
            color="primary"
            variant="outlined"
          />
        </Box>
        <IconButton
          onClick={handleSkip}
          aria-label={t('onboarding.skip', { defaultValue: 'Skip tutorial' })}
          sx={{
            minWidth: 44,
            minHeight: 44,
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      {/* Content */}
      <DialogContent sx={{ px: { xs: 2, sm: 4 }, py: 2 }}>
        <Fade in key={step.id} timeout={300}>
          <Box>
            {/* Step Icon */}
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                mb: 3,
              }}
            >
              <Paper
                elevation={0}
                sx={{
                  width: 100,
                  height: 100,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  bgcolor: 'grey.100',
                }}
              >
                {step.icon}
              </Paper>
            </Box>

            {/* Step Title */}
            <Typography
              id="onboarding-tutorial-title"
              variant="h5"
              component="h2"
              textAlign="center"
              fontWeight={600}
              gutterBottom
            >
              {step.title}
            </Typography>

            {/* Step Description */}
            <Typography
              id="onboarding-tutorial-description"
              variant="body1"
              color="text.secondary"
              textAlign="center"
              sx={{ mb: 3, maxWidth: 480, mx: 'auto' }}
            >
              {step.description}
            </Typography>

            {/* Tips List */}
            <Paper
              variant="outlined"
              sx={{
                p: 2,
                bgcolor: 'grey.50',
                borderRadius: 2,
              }}
            >
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                {t('onboarding.keyPoints', { defaultValue: 'Key Points' })}
              </Typography>
              <Stack component="ul" spacing={1} sx={{ m: 0, pl: 2 }}>
                {step.tips.map((tip, index) => (
                  <Box
                    key={index}
                    component="li"
                    sx={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 1.5,
                      minHeight: 44,
                      py: 0.5,
                    }}
                  >
                    <Chip
                      label={index + 1}
                      size="small"
                      color="primary"
                      sx={{ minWidth: 24, height: 24, fontSize: '0.75rem' }}
                    />
                    <Typography variant="body2" sx={{ pt: 0.25 }}>
                      {tip}
                    </Typography>
                  </Box>
                ))}
              </Stack>
            </Paper>

            {/* Highlight Link */}
            {step.highlight && (
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">
                  {t('onboarding.findThisAt', { defaultValue: 'Find this at:' })}{' '}
                  <Typography component="span" variant="caption" color="primary.main" fontFamily="monospace">
                    {step.highlight}
                  </Typography>
                </Typography>
              </Box>
            )}
          </Box>
        </Fade>
      </DialogContent>

      {/* Footer Actions */}
      <DialogActions
        sx={{
          px: { xs: 2, sm: 4 },
          py: 2,
          flexDirection: isMobile ? 'column' : 'row',
          gap: 1,
        }}
      >
        {/* Left side - Previous/Skip */}
        <Box
          sx={{
            display: 'flex',
            gap: 1,
            flex: isMobile ? '1 1 auto' : 1,
            width: isMobile ? '100%' : 'auto',
          }}
        >
          {!isFirstStep && (
            <Button
              onClick={handlePrevious}
              startIcon={<ArrowBackIcon />}
              sx={{
                minHeight: 44,
                minWidth: isMobile ? undefined : 100,
              }}
            >
              {t('onboarding.previous', { defaultValue: 'Previous' })}
            </Button>
          )}
          {isFirstStep && (
            <Button
              onClick={handleSkip}
              color="inherit"
              sx={{
                minHeight: 44,
              }}
            >
              {t('onboarding.skipTutorial', { defaultValue: 'Skip Tutorial' })}
            </Button>
          )}
        </Box>

        {/* Right side - Next/Complete */}
        <Box
          sx={{
            display: 'flex',
            gap: 1,
            flex: isMobile ? '1 1 auto' : 1,
            width: isMobile ? '100%' : 'auto',
            justifyContent: 'flex-end',
          }}
        >
          {isLastStep ? (
            <Button
              variant="contained"
              color="success"
              onClick={handleComplete}
              endIcon={<PlayArrowIcon />}
              sx={{
                minHeight: 44,
                minWidth: isMobile ? undefined : 160,
                width: isMobile ? '100%' : 'auto',
              }}
            >
              {t('onboarding.getStarted', { defaultValue: "Let's Get Started" })}
            </Button>
          ) : (
            <Button
              variant="contained"
              onClick={handleNext}
              endIcon={<ArrowForwardIcon />}
              sx={{
                minHeight: 44,
                minWidth: isMobile ? undefined : 100,
                width: isMobile ? '100%' : 'auto',
              }}
            >
              {t('onboarding.next', { defaultValue: 'Next' })}
            </Button>
          )}
        </Box>
      </DialogActions>

      {/* Restart Button (if already completed) */}
      {hasCompleted && (
        <Box
          sx={{
            position: 'absolute',
            bottom: 8,
            left: 8,
          }}
        >
          <Tooltip title={t('onboarding.restart', { defaultValue: 'Restart tutorial' })}>
            <IconButton
              size="small"
              onClick={handleRestart}
              sx={{
                bgcolor: 'grey.100',
                '&:hover': { bgcolor: 'grey.200' },
              }}
            >
              <ReplayIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      )}
    </Dialog>
  );
};

/**
 * Hook to manage tutorial state
 *
 * @example
 * ```tsx
 * const { showTutorial, startTutorial, closeTutorial, hasCompleted } = useOnboardingTutorial();
 *
 * return (
 *   <>
 *     <Button onClick={startTutorial}>Show Tutorial</Button>
 *     <OnboardingTutorial open={showTutorial} onClose={closeTutorial} />
 *   </>
 * );
 * ```
 */
export function useOnboardingTutorial(storageKey = TUTORIAL_COMPLETED_KEY) {
  const [showTutorial, setShowTutorial] = useState(false);

  const hasCompleted = localStorage.getItem(storageKey) === 'true';

  const startTutorial = useCallback(() => {
    setShowTutorial(true);
  }, []);

  const closeTutorial = useCallback(() => {
    setShowTutorial(false);
  }, []);

  const resetTutorial = useCallback(() => {
    localStorage.removeItem(storageKey);
  }, [storageKey]);

  return {
    showTutorial,
    startTutorial,
    closeTutorial,
    resetTutorial,
    hasCompleted,
  };
}

export default OnboardingTutorial;

// Export types for external use
export type { OnboardingTutorialProps, TutorialStep };
