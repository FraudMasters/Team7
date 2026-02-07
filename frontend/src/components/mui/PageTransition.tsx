/**
 * Компонент для плавного перехода между страницами
 *
 * Обеспечивает анимацию появления контента при навигации.
 * Использует MUI Box с CSS-анимацией для fade-in эффекта.
 *
 * @example
 * ```tsx
 * <PageTransition>
 *   <Container>
 *     <Typography>Контент страницы</Typography>
 *   </Container>
 * </PageTransition>
 * ```
 */

import { Box, type BoxProps } from '@mui/material';

// Интерфейс для свойств компонента PageTransition
export interface PageTransitionProps extends BoxProps {
  /** Дочерние элементы, которые будут анимированы */
  children: React.ReactNode;
}

/**
 * Компонент для плавного перехода между страницами с fade-in анимацией
 */
export function PageTransition({ children, ...props }: PageTransitionProps) {
  return (
    <Box
      {...props}
      sx={{
        animation: 'fadeIn 0.3s ease-in-out',
        '@keyframes fadeIn': {
          '0%': { opacity: 0, transform: 'translateY(10px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        ...props.sx,
      }}
    >
      {children}
    </Box>
  );
}

export default PageTransition;
