/**
 * TouchCarousel Component
 *
 * A mobile-friendly carousel component that supports touch swipe gestures
 * for navigating through cards/items. Provides smooth animations, visual
 * indicators, and infinite cycling capabilities.
 *
 * @module components/ui/TouchCarousel
 */

import React, { useState, useCallback, useRef, useEffect, ReactNode } from 'react';
import { Box, IconButton, MobileStepper, Paper, SxProps, Theme } from '@mui/material';
import { KeyboardArrowLeft, KeyboardArrowRight } from '@mui/icons-material';
import { useSwipeGesture } from '../../hooks/useSwipeGesture';

/**
 * TouchCarousel component props
 */
export interface TouchCarouselProps {
  /**
   * Array of React nodes to render as carousel items
   */
  children: ReactNode[];

  /**
   * Optional CSS styles for the carousel container
   */
  sx?: SxProps<Theme>;

  /**
   * Enable infinite cycling (wrapping from last to first and vice versa)
   * @default true
   */
  infinite?: boolean;

  /**
   * Enable auto-play (automatic card advancement)
   * @default false
   */
  autoPlay?: boolean;

  /**
   * Auto-play interval in milliseconds
   * @default 5000
   */
  autoPlayInterval?: number;

  /**
   * Show navigation dots indicator
   * @default true
   */
  showDots?: boolean;

  /**
   * Show navigation arrows (hidden on mobile, visible on desktop)
   * @default true
   */
  showArrows?: boolean;

  /**
   * Enable swipe gestures on mobile devices
   * @default true
   */
  enableSwipe?: boolean;

  /**
   * Callback fired when the active item changes
   *
   * @param index - New active index
   * @param previousIndex - Previous active index
   */
  onChange?: (index: number, previousIndex: number) => void;

  /**
   * Callback fired when swiping to the next item
   */
  onNext?: () => void;

  /**
   * Callback fired when swiping to the previous item
   */
  onPrevious?: () => void;

  /**
   * Height of the carousel container
   * @default 'auto'
   */
  height?: number | string;

  /**
   * Enable touch-action CSS property for better swipe handling
   * @default true
   */
  enableTouchAction?: boolean;
}

/**
 * TouchCarousel Component
 *
 * A mobile-optimized carousel with touch swipe support.
 *
 * @example
 * ```tsx
 * <TouchCarousel>
 *   <Box>Card 1</Box>
 *   <Box>Card 2</Box>
 *   <Box>Card 3</Box>
 * </TouchCarousel>
 * ```
 *
 * @example
 * ```tsx
 * <TouchCarousel
 *   infinite={true}
 *   autoPlay={true}
 *   autoPlayInterval={3000}
 *   onChange={(index) => console.log('Active:', index)}
 *   sx={{ maxHeight: 400 }}
 * >
 *   {candidates.map(candidate => (
 *     <CandidateCard key={candidate.id} candidate={candidate} />
 *   ))}
 * </TouchCarousel>
 * ```
 */
const TouchCarousel: React.FC<TouchCarouselProps> = ({
  children,
  sx = {},
  infinite = true,
  autoPlay = false,
  autoPlayInterval = 5000,
  showDots = true,
  showArrows = true,
  enableSwipe = true,
  onChange,
  onNext,
  onPrevious,
  height = 'auto',
  enableTouchAction = true,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [direction, setDirection] = useState<'left' | 'right' | null>(null);
  const autoPlayRef = useRef<NodeJS.Timeout | null>(null);
  const maxSteps = children.length;

  /**
   * Validate that children array is not empty
   */
  if (maxSteps === 0) {
    return (
      <Box sx={{ ...sx, p: 2, textAlign: 'center' }}>
        No items to display
      </Box>
    );
  }

  /**
   * Handle next button click or swipe
   */
  const handleNext = useCallback(() => {
    setDirection('left');
    const newStep = infinite ? (activeStep + 1) % maxSteps : Math.min(activeStep + 1, maxSteps - 1);
    setActiveStep(newStep);
    onChange?.(newStep, activeStep);
    onNext?.();

    // Reset direction after animation completes
    setTimeout(() => setDirection(null), 300);
  }, [activeStep, maxSteps, infinite, onChange, onNext]);

  /**
   * Handle back button click or swipe
   */
  const handleBack = useCallback(() => {
    setDirection('right');
    const newStep = infinite ? (activeStep - 1 + maxSteps) % maxSteps : Math.max(activeStep - 1, 0);
    setActiveStep(newStep);
    onChange?.(newStep, activeStep);
    onPrevious?.();

    // Reset direction after animation completes
    setTimeout(() => setDirection(null), 300);
  }, [activeStep, maxSteps, infinite, onChange, onPrevious]);

  /**
   * Handle step change via dots indicator
   */
  const handleStepChange = useCallback(
    (step: number) => {
      setDirection(step > activeStep ? 'left' : 'right');
      setActiveStep(step);
      onChange?.(step, activeStep);

      // Reset direction after animation completes
      setTimeout(() => setDirection(null), 300);
    },
    [activeStep, onChange]
  );

  /**
   * Setup swipe gesture handlers
   */
  const swipeHandlers = useSwipeGesture({
    onSwipedLeft: enableSwipe ? handleNext : undefined,
    onSwipedRight: enableSwipe ? handleBack : undefined,
    trackMouse: false,
    touchEventOptions: { passive: true },
  });

  /**
   * Auto-play functionality
   */
  useEffect(() => {
    if (autoPlay && !swipeHandlers.isSwiping) {
      autoPlayRef.current = setInterval(handleNext, autoPlayInterval);
    }

    return () => {
      if (autoPlayRef.current) {
        clearInterval(autoPlayRef.current);
      }
    };
  }, [autoPlay, autoPlayInterval, handleNext, swipeHandlers.isSwiping]);

  /**
   * Pause auto-play on user interaction
   */
  const pauseAutoPlay = useCallback(() => {
    if (autoPlayRef.current) {
      clearInterval(autoPlayRef.current);
      autoPlayRef.current = null;
    }
  }, []);

  /**
   * Resume auto-play after user interaction
   */
  const resumeAutoPlay = useCallback(() => {
    if (autoPlay) {
      autoPlayRef.current = setInterval(handleNext, autoPlayInterval);
    }
  }, [autoPlay, autoPlayInterval, handleNext]);

  return (
    <Box
      {...(enableSwipe ? swipeHandlers : {})}
      onMouseEnter={pauseAutoPlay}
      onMouseLeave={resumeAutoPlay}
      onTouchStart={pauseAutoPlay}
      onTouchEnd={resumeAutoPlay}
      sx={{
        position: 'relative',
        width: '100%',
        height,
        ...sx,
      }}
    >
      {/* Navigation Arrow - Previous */}
      {showArrows && (infinite || activeStep > 0) && (
        <IconButton
          onClick={handleBack}
          disabled={!infinite && activeStep === 0}
          sx={{
            position: 'absolute',
            left: { xs: 4, sm: 8 },
            top: '50%',
            transform: 'translateY(-50%)',
            zIndex: 2,
            bgcolor: 'background.paper',
            boxShadow: 3,
            '&:hover': {
              bgcolor: 'background.default',
            },
            display: { xs: 'none', sm: 'flex' },
          }}
          aria-label="Previous item"
        >
          <KeyboardArrowLeft />
        </IconButton>
      )}

      {/* Carousel Content */}
      <Box
        sx={{
          overflow: 'hidden',
          width: '100%',
          height: '100%',
          position: 'relative',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            transition: 'transform 0.3s ease-in-out',
            transform: `translateX(-${activeStep * 100}%)`,
            height: '100%',
            touchAction: enableTouchAction ? 'pan-y' : 'auto',
          }}
        >
          {children.map((child, index) => (
            <Box
              key={index}
              sx={{
                minWidth: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {child}
            </Box>
          ))}
        </Box>
      </Box>

      {/* Navigation Arrow - Next */}
      {showArrows && (infinite || activeStep < maxSteps - 1) && (
        <IconButton
          onClick={handleNext}
          disabled={!infinite && activeStep === maxSteps - 1}
          sx={{
            position: 'absolute',
            right: { xs: 4, sm: 8 },
            top: '50%',
            transform: 'translateY(-50%)',
            zIndex: 2,
            bgcolor: 'background.paper',
            boxShadow: 3,
            '&:hover': {
              bgcolor: 'background.default',
            },
            display: { xs: 'none', sm: 'flex' },
          }}
          aria-label="Next item"
        >
          <KeyboardArrowRight />
        </IconButton>
      )}

      {/* Mobile Swipe Hint */}
      {enableSwipe && maxSteps > 1 && (
        <Box
          sx={{
            position: 'absolute',
            bottom: showDots ? 60 : 16,
            left: '50%',
            transform: 'translateX(-50%)',
            display: { xs: 'flex', sm: 'none' },
            alignItems: 'center',
            gap: 0.5,
            color: 'text.secondary',
            fontSize: '0.75rem',
            opacity: 0.6,
            pointerEvents: 'none',
          }}
        >
          <KeyboardArrowLeft sx={{ fontSize: 16 }} />
          Swipe
          <KeyboardArrowRight sx={{ fontSize: 16 }} />
        </Box>
      )}

      {/* Dots Indicator */}
      {showDots && maxSteps > 1 && (
        <MobileStepper
          steps={maxSteps}
          position="static"
          activeStep={activeStep}
          sx={{
            position: 'absolute',
            bottom: 8,
            left: '50%',
            transform: 'translateX(-50%)',
            bgcolor: 'transparent',
            '& .MuiMobileStepper-dot': {
              bgcolor: 'action.disabled',
            },
            '& .MuiMobileStepper-dotActive': {
              bgcolor: 'primary.main',
            },
          }}
          nextButton={<div />}
          backButton={<div />}
        />
      )}
    </Box>
  );
};

export default TouchCarousel;
