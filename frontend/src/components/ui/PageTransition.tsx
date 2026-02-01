import { ReactNode } from 'react';
import { motion } from 'framer-motion';

/**
 * PageTransition Props
 *
 * Wrapper component for smooth page transitions using Framer Motion.
 * Designed to work with AnimatePresence for route-level transitions.
 */
export interface PageTransitionProps {
  /** Content to animate */
  children: ReactNode;
  /** Animation duration in milliseconds (default: 350ms) */
  duration?: number;
  /** Animation delay in milliseconds (default: 0ms) */
  delay?: number;
  /** Enable exit animation (default: true) */
  exit?: boolean;
  /** Optional className for the motion div */
  className?: string;
}

/**
 * PageTransition Component
 *
 * Provides smooth fade + slide animations for page transitions.
 * Uses subtle animations (300-400ms) that are not jarring for users.
 *
 * @example
 * // Basic usage in a route component
 * <PageTransition>
 *   <YourPageContent />
 * </PageTransition>
 *
 * @example
 * // With AnimatePresence for route transitions (in Layout or Router)
 * <AnimatePresence mode="wait">
 *   <PageTransition key={location.pathname}>
 *     <Outlet />
 *   </PageTransition>
 * </AnimatePresence>
 */
const PageTransition: React.FC<PageTransitionProps> = ({
  children,
  duration = 350,
  delay = 0,
  exit = true,
  className,
}) => {
  // Convert milliseconds to seconds for Framer Motion
  const durationSec = duration / 1000;
  const delaySec = delay / 1000;

  const variants = {
    initial: {
      opacity: 0,
      y: 10,
    },
    animate: {
      opacity: 1,
      y: 0,
      transition: {
        duration: durationSec,
        delay: delaySec,
        ease: 'easeOut',
      },
    },
    exit: {
      opacity: 0,
      y: -10,
      transition: {
        duration: durationSec * 0.8, // Exit is slightly faster
        ease: 'easeIn',
      },
    },
  };

  const MotionDiv = motion.div;

  return (
    <MotionDiv
      initial="initial"
      animate="animate"
      exit={exit ? "exit" : undefined}
      variants={variants}
      className={className}
    >
      {children}
    </MotionDiv>
  );
};

export default PageTransition;
