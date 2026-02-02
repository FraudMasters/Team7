import { ReactNode } from 'react';
import { Box, BoxProps } from '@mui/material';

/**
 * PageTransition Props
 *
 * Wrapper component for smooth page transitions using CSS animations.
 * Provides fade + slide animations without external dependencies.
 */
export interface PageTransitionProps extends BoxProps {
  /** Content to animate */
  children: ReactNode;
  /** Animation duration in milliseconds (default: 350ms) */
  duration?: number;
  /** Animation delay in milliseconds (default: 0ms) */
  delay?: number;
  /** Enable exit animation (default: true) - note: exit animation requires React transition group */
  exit?: boolean;
}

/**
 * PageTransition Component
 *
 * Provides smooth fade + slide animations for page transitions.
 * Uses subtle animations (300-400ms) that are not jarring for users.
 * Uses CSS animations for lightweight transitions.
 *
 * @example
 * // Basic usage in a route component
 * <PageTransition>
 *   <YourPageContent />
 * </PageTransition>
 */
const PageTransition: React.FC<PageTransitionProps> = ({
  children,
  duration = 350,
  delay = 0,
  className,
  sx,
  ...boxProps
}) => {
  return (
    <Box
      className={className}
      sx={{
        animation: `pageFadeIn ${duration}ms ease-out ${delay}ms both`,
        '@keyframes pageFadeIn': {
          '0%': {
            opacity: 0,
            transform: 'translateY(10px)',
          },
          '100%': {
            opacity: 1,
            transform: 'translateY(0)',
          },
        },
        ...sx,
      }}
      {...boxProps}
    >
      {children}
    </Box>
  );
};

export default PageTransition;
export { PageTransition };
