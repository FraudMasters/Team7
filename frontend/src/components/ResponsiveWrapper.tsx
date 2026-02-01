import React from 'react';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

/**
 * ResponsiveWrapper Component
 *
 * Provides responsive breakpoint detection for child components.
 * Makes mobile/desktop state available via render prop.
 *
 * @example
 * // Using render prop (recommended for conditional rendering based on screen size)
 * <ResponsiveWrapper render={(isMobile) => isMobile ? <MobileView /> : <DesktopView />} />
 *
 * @example
 * // Direct children (always rendered)
 * <ResponsiveWrapper><StaticContent /></ResponsiveWrapper>
 */
interface ResponsiveWrapperProps {
  /** Render function that receives mobile state - use this for conditional rendering */
  render?: (isMobile: boolean) => React.ReactNode;
  /** Direct children to render (not responsive) */
  children?: React.ReactNode;
}

const ResponsiveWrapper: React.FC<ResponsiveWrapperProps> = ({ render, children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Use render prop if provided, otherwise use direct children
  const content = render ? render(isMobile) : children;

  return <>{content}</>;
};

export default ResponsiveWrapper;
