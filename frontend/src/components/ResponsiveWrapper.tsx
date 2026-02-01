import React, { ReactNode } from 'react';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

/**
 * ResponsiveWrapper Component
 *
 * Provides responsive breakpoint detection for child components.
 * Wraps content and makes mobile/desktop state available via render props.
 */
interface ResponsiveWrapperProps {
  /**
   * Render function that receives mobile state
   * @param isMobile - true if screen width < 900px
   */
  children: (isMobile: boolean) => ReactNode;
}

const ResponsiveWrapper: React.FC<ResponsiveWrapperProps> = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  return <>{children(isMobile)}</>;
};

export default ResponsiveWrapper;
