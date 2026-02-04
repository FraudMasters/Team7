/**
 * UI Primitive Components
 *
 * Core layout, typography, and icon components built with Emotion.
 * These are foundational components used throughout the application.
 *
 * @example
 * ```tsx
 * import { Box, Typography, Container, Icon } from '@/components/ui/primitives';
 *
 * <Container maxWidth="lg">
 *   <Box p={2}>
 *     <Typography variant="h1">Heading</Typography>
 *     <Typography variant="body1">Body text</Typography>
 *     <Icon name="User" size={24} color="primary" />
 *   </Box>
 * </Container>
 * ```
 */

export { default as Box } from './Box';
export type { BoxProps, SystemStyleProps, SpacingValue } from './Box';

export { default as Typography } from './Typography';
export type { TypographyProps, TypographyVariant, TypographyColor } from './Typography';

export { default as Container } from './Container';
export type { ContainerProps } from './Container';

export { default as Icon } from './Icon';
export type { IconProps, IconSize, IconColor } from './Icon';
