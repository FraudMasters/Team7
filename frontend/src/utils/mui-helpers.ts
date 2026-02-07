/**
 * MUI Helpers - Утилиты и вспомогательные функции для Material-UI
 *
 * Предоставляет набор вспомогательных функций для работы с MUI компонентами,
 * включая стилизацию, адаптивность, анимации и общие паттерны.
 *
 * @module utils/mui-helpers
 */

import { SxProps, Theme } from '@mui/material/styles';
import { Breakpoint } from '@mui/material/styles';

/**
 * Вспомогательный тип для функции, возвращающей SxProps на основе темы
 */
export type SxPropsFn = (theme: Theme) => SxProps<Theme>;

/**
 * Объединенный тип для статических или динамических SxProps
 */
export type ResponsiveStyle = SxProps<Theme> | SxPropsFn;

/**
 * Создает объект стилей, адаптированный под разные размеры экрана
 *
 * @param styles - Объект с стилями для различных breakpoint'ов
 * @returns Объект SxProps для MUI компонентов
 *
 * @example
 * ```ts
 * const responsiveStyles = createResponsiveStyles({
 *   xs: { fontSize: '14px', padding: 1 },
 *   sm: { fontSize: '16px', padding: 2 },
 *   md: { fontSize: '18px', padding: 3 },
 * });
 *
 * <Box sx={responsiveStyles}>Контент</Box>
 * ```
 */
export function createResponsiveStyles(
  styles: Partial<Record<Breakpoint, SxProps<Theme>>>
): SxProps<Theme> {
  const mergedStyles: SxProps<Theme> = {};

  for (const [breakpoint, style] of Object.entries(styles)) {
    if (style) {
      // @ts-ignore - динамический ключ breakpoint'а
      mergedStyles[breakpoint] = style;
    }
  }

  return mergedStyles;
}

/**
 * Создает flexbox-контейнер с заданными параметрами
 *
 * @param options - Параметры flexbox контейнера
 * @returns Объект SxProps с flexbox стилями
 *
 * @example
 * ```ts
 * const flexContainer = createFlexContainer({
 *   direction: 'row',
 *   justifyContent: 'center',
 *   alignItems: 'center',
 *   gap: 2,
 * });
 *
 * <Box sx={flexContainer}>Элементы</Box>
 * ```
 */
export function createFlexContainer(options: {
  /** Направление flex контейнера */
  direction?: 'row' | 'column' | 'row-reverse' | 'column-reverse';
  /** Выравнивание по главной оси */
  justifyContent?: 'flex-start' | 'center' | 'flex-end' | 'space-between' | 'space-around';
  /** Выравнивание по поперечной оси */
  alignItems?: 'flex-start' | 'center' | 'flex-end' | 'stretch';
  /** Перенос элементов */
  wrap?: 'nowrap' | 'wrap' | 'wrap-reverse';
  /** Расстояние между элементами (использует spacing) */
  gap?: number | string;
}): SxProps<Theme> {
  const {
    direction = 'row',
    justifyContent = 'flex-start',
    alignItems = 'stretch',
    wrap = 'nowrap',
    gap = 0,
  } = options;

  return {
    display: 'flex',
    flexDirection: direction,
    justifyContent,
    alignItems,
    flexWrap: wrap,
    gap,
  };
}

/**
 * Создает grid-контейнер с заданными параметрами
 *
 * @param options - Параметры grid контейнера
 * @returns Объект SxProps с grid стилями
 *
 * @example
 * ```ts
 * const gridContainer = createGridContainer({
 *   columns: { xs: 1, sm: 2, md: 3 },
 *   spacing: 2,
 * });
 *
 * <Box sx={gridContainer}>Элементы</Box>
 * ```
 */
export function createGridContainer(options: {
  /** Количество колонок для различных breakpoint'ов */
  columns?: number | Partial<Record<Breakpoint, number>>;
  /** Расстояние между элементами (использует spacing) */
  spacing?: number;
}): SxProps<Theme> {
  const { columns = 1, spacing = 0 } = options;

  return {
    display: 'grid',
    gridTemplateColumns: typeof columns === 'number'
      ? `repeat(${columns}, 1fr)`
      : undefined,
    gap: spacing,
  };
}

/**
 * Создает стили для центрирования контента
 *
 * @param options - Опции центрирования
 * @returns Объект SxProps для центрирования
 *
 * @example
 * ```ts
 * <Box sx={centerContent()}>
 *   Центрированный контент
 * </Box>
 * ```
 */
export function centerContent(options: {
  /** Центрировать по горизонтали */
  horizontal?: boolean;
  /** Центрировать по вертикали */
  vertical?: boolean;
} = {}): SxProps<Theme> {
  const { horizontal = true, vertical = true } = options;

  return {
    display: 'flex',
    ...(horizontal && { justifyContent: 'center' }),
    ...(vertical && { alignItems: 'center' }),
  };
}

/**
 * Создает стили для абсолютно позиционированного элемента
 *
 * @param position - Параметры позиционирования
 * @returns Объект SxProps с позиционированием
 *
 * @example
 * ```ts
 * const closeButton = createAbsolutePosition({
 *   top: 8,
 *   right: 8,
 * });
 *
 * <IconButton sx={closeButton}>
 *   <CloseIcon />
 * </IconButton>
 * ```
 */
export function createAbsolutePosition(position: {
  top?: number | string;
  right?: number | string;
  bottom?: number | string;
  left?: number | string;
}): SxProps<Theme> {
  return {
    position: 'absolute',
    ...position,
  };
}

/**
 * Создает стили для фиксированного позиционирования
 *
 * @param position - Параметры позиционирования
 * @returns Объект SxProps с фиксированным позиционированием
 *
 * @example
 * ```ts
 * const fixedHeader = createFixedPosition({
 *   top: 0,
 *   left: 0,
 *   right: 0,
 * });
 *
 * <Box sx={fixedHeader}>Фиксированный заголовок</Box>
 * ```
 */
export function createFixedPosition(position: {
  top?: number | string;
  right?: number | string;
  bottom?: number | string;
  left?: number | string;
}): SxProps<Theme> {
  return {
    position: 'fixed',
    ...position,
  };
}

/**
 * Создает стили для переходов/анимаций
 *
 * @param properties - Свойства для анимации
 * @param duration - Длительность перехода в секундах
 * @param easing - Функция плавности
 * @returns Объект SxProps с анимацией
 *
 * @example
 * ```ts
 * const hoverTransition = createTransition(
 *   ['color', 'background-color'],
 *   0.3,
 *   'ease-in-out'
 * );
 *
 * <Button sx={hoverTransition}>Кнопка</Button>
 * ```
 */
export function createTransition(
  properties: string[],
  duration: number = 0.3,
  easing: string = 'ease-in-out'
): SxProps<Theme> {
  return {
    transition: properties.map(prop => `${prop} ${duration}s ${easing}`).join(', '),
  };
}

/**
 * Создает стили для карточки с тенями и скругленными углами
 *
 * @param elevation - Уровень elevation (0-24)
 * @param borderRadius - Радиус скругления (использует spacing)
 * @returns Объект SxProps для карточки
 *
 * @example
 * ```ts
 * <Card sx={createCardStyles(2, 2)}>
 *   Содержимое карточки
 * </Card>
 * ```
 */
export function createCardStyles(
  elevation: number = 1,
  borderRadius: number = 1
): SxProps<Theme> {
  return {
    borderRadius,
    boxShadow: (theme: Theme) => theme.shadows[elevation],
  };
}

/**
 * Создает стили для адаптивного текста
 *
 * @param options - Опции текста
 * @returns Объект SxProps с адаптивным текстом
 *
 * @example
 * ```ts
 * <Typography sx={createResponsiveText({
 *   xs: 'h6',
 *   sm: 'h5',
 *   md: 'h4',
 * })}>
 *   Заголовок
 * </Typography>
 * ```
 */
export function createResponsiveText(options: {
  /** Размер шрифта для различных breakpoint'ов */
  variant?: Partial<Record<Breakpoint, string>>;
}): SxProps<Theme> {
  const styles: SxProps<Theme> = {};

  for (const [breakpoint, variant] of Object.entries(options.variant || {})) {
    if (variant) {
      // @ts-ignore - динамический ключ breakpoint'а
      styles[breakpoint] = {
        typography: variant,
      };
    }
  }

  return styles;
}

/**
 * Создает стили для скрытия элемента на определенных breakpoint'ах
 *
 * @param breakpoints - Массив breakpoint'ов для скрытия
 * @returns Объект SxProps для условного отображения
 *
 * @example
 * ```ts
 * // Скрыть на мобильных, показать на планшетах и выше
 * <Box sx={createHidden(['xs'])}>
 *   Скрыто на мобильных
 * </Box>
 * ```
 */
export function createHidden(breakpoints: Breakpoint[]): SxProps<Theme> {
  const styles: SxProps<Theme> = {};

  for (const breakpoint of breakpoints) {
    // @ts-ignore - динамический ключ breakpoint'а
    styles[breakpoint] = {
      display: 'none',
    };
  }

  return styles;
}

/**
 * Создает стили для показа элемента только на определенных breakpoint'ах
 *
 * @param breakpoints - Массив breakpoint'ов для показа
 * @returns Объект SxProps для условного отображения
 *
 * @example
 * ```ts
 * // Показать только на мобильных
 * <Box sx={createVisibleOnly(['xs'])}>
 *   Только на мобильных
 * </Box>
 * ```
 */
export function createVisibleOnly(breakpoints: Breakpoint[]): SxProps<Theme> {
  const allBreakpoints: Breakpoint[] = ['xs', 'sm', 'md', 'lg', 'xl'];
  const hiddenBreakpoints = allBreakpoints.filter(bp => !breakpoints.includes(bp));

  return createHidden(hiddenBreakpoints);
}

/**
 * Создает объект с颜色 из темы MUI
 *
 * @param color - Имя цвета из палитры темы
 * @returns Функция, возвращающая цвет из темы
 *
 * @example
 * ```ts
 * const primaryColor = getThemeColor('primary');
 * const errorColor = getThemeColor('error');
 *
 * <Box sx={{ color: primaryColor }}>Текст основным цветом</Box>
 * ```
 */
export function getThemeColor(color: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success') {
  return (theme: Theme) => theme.palette[color].main;
}

/**
 * Создает объект с фоновым цветом из темы MUI
 *
 * @param color - Имя цвета из палитры темы
 * @param variant - Вариант цвета (main, light, dark)
 * @returns Функция, возвращающая фоновый цвет из темы
 *
 * @example
 * ```ts
 * <Box sx={{ bgcolor: getThemeBgColor('primary') }}>
 *   Фон основным цветом
 * </Box>
 * ```
 */
export function getThemeBgColor(
  color: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' | 'background',
  variant: 'main' | 'light' | 'dark' = 'main'
) {
  return (theme: Theme) => {
    if (color === 'background') {
      return theme.palette.background.paper;
    }
    return theme.palette[color][variant];
  };
}

/**
 * Создает стили для кнопки с иконкой
 *
 * @param spacing - Расстояние между текстом и иконкой
 * @returns Объект SxProps для кнопки
 *
 * @example
 * ```ts
 * <Button sx={createButtonWithIcon()} startIcon={<AddIcon />}>
 *   Добавить
 * </Button>
 * ```
 */
export function createButtonWithIcon(spacing: number = 1): SxProps<Theme> {
  return {
    gap: spacing,
  };
}

/**
 * Создает стили для чипа (badge)
 *
 * @param options - Опции чипа
 * @returns Объект SxProps для чипа
 *
 * @example
 * ```ts
 * <Badge sx={createBadgeStyles()}>
 *   Содержимое
 * </Badge>
 * ```
 */
export function createBadgeStyles(options: {
  /** Фоновый цвет */
  bgColor?: string;
  /** Цвет текста */
  color?: string;
  /** Размер шрифта */
  fontSize?: number | string;
  /** Минимальная ширина */
  minWidth?: number | string;
  /** Высота */
  height?: number | string;
  /** Радиус скругления */
  borderRadius?: number | string;
}): SxProps<Theme> {
  const {
    bgColor = 'error.main',
    color = 'error.contrastText',
    fontSize = 10,
    minWidth = 20,
    height = 20,
    borderRadius = 10,
  } = options;

  return {
    bgcolor: bgColor,
    color: color,
    fontSize,
    minWidth,
    height,
    borderRadius,
  };
}

/**
 * Создает стили для divider (разделителя)
 *
 * @param options - Опции разделителя
 * @returns Объект SxProps для разделителя
 *
 * @example
 * ```ts
 * <Divider sx={createDividerStyles({ orientation: 'vertical' })} />
 * ```
 */
export function createDividerStyles(options: {
  /** Ориентация разделителя */
  orientation?: 'horizontal' | 'vertical';
  /** Толщина разделителя */
  thickness?: number;
  /** Цвет разделителя */
  color?: string;
}): SxProps<Theme> {
  const {
    orientation = 'horizontal',
    thickness = 1,
    color = 'divider',
  } = options;

  return {
    ...(orientation === 'horizontal' ? {
      borderBottomWidth: thickness,
      borderBottomColor: color,
    } : {
      borderLeftWidth: thickness,
      borderLeftColor: color,
    }),
  };
}

/**
 * Создает стили для прогресс-бара
 *
 * @param options - Опции прогресс-бара
 * @returns Объект SxProps для прогресс-бара
 *
 * @example
 * ```ts
 * <LinearProgress sx={createProgressStyles({ color: 'primary' })} />
 * ```
 */
export function createProgressStyles(options: {
  /** Цвет прогресс-бара */
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  /** Высота прогресс-бара */
  height?: number;
}): SxProps<Theme> {
  const {
    color = 'primary',
    height = 4,
  } = options;

  return {
    height,
    backgroundColor: (theme: Theme) => theme.palette[color].main,
    '& .MuiLinearProgress-bar': {
      backgroundColor: (theme: Theme) => theme.palette[color].main,
    },
  };
}

/**
 * Создает стили для скроллируемого контейнера
 *
 * @param options - Опции скролла
 * @returns Объект SxProps для скроллируемого контейнера
 *
 * @example
 * ```ts
 * <Box sx={createScrollableContainer({ maxHeight: 300 })}>
 *   Длинный контент
 * </Box>
 * ```
 */
export function createScrollableContainer(options: {
  /** Максимальная высота */
  maxHeight?: number | string;
  /** Показывать скроллбар по горизонтали */
  overflowX?: 'auto' | 'hidden' | 'scroll' | 'visible';
  /** Показывать скроллбар по вертикали */
  overflowY?: 'auto' | 'hidden' | 'scroll' | 'visible';
}): SxProps<Theme> {
  const {
    maxHeight = '100%',
    overflowX = 'auto',
    overflowY = 'auto',
  } = options;

  return {
    maxHeight,
    overflowX,
    overflowY,
  };
}

/**
 * Создает стили для tooltip (всплывающей подсказки)
 *
 * @param options - Опции tooltip
 * @returns Объект с настройками tooltip
 *
 * @example
 * ```ts
 * <Tooltip {...createTooltipOptions({ title: 'Подсказка' })}>
 *   <Button>Кнопка</Button>
 * </Tooltip>
 * ```
 */
export function createTooltipOptions(options: {
  /** Текст подсказки */
  title: string;
  /** Положение tooltip */
  placement?: 'top' | 'bottom' | 'left' | 'right';
  /** Задержка перед показом */
  enterDelay?: number;
  /** Задержка перед скрытием */
  leaveDelay?: number;
}): Record<string, unknown> {
  const {
    title,
    placement = 'top',
    enterDelay = 500,
    leaveDelay = 0,
  } = options;

  return {
    title,
    placement,
    enterDelay,
    leaveDelay,
    arrow: true,
  };
}

/**
 * Создает стили для hover-эффекта
 *
 * @param styles - Стили при наведении
 * @returns Объект SxProps с hover-эффектом
 *
 * @example
 * ```ts
 * <Box sx={createHoverEffect({ bgcolor: 'action.hover' })}>
 *   Контент с hover-эффектом
 * </Box>
 * ```
 */
export function createHoverEffect(styles: SxProps<Theme>): SxProps<Theme> {
  return {
    '&:hover': styles,
  };
}

/**
 * Создает стили для focus-эффекта
 *
 * @param styles - Стили при фокусе
 * @returns Объект SxProps с focus-эффектом
 *
 * @example
 * ```ts
 * <Button sx={createFocusEffect({ outline: '2px solid primary.main' })}>
 *   Кнопка с focus-эффектом
 * </Button>
 * ```
 */
export function createFocusEffect(styles: SxProps<Theme>): SxProps<Theme> {
  return {
    '&:focus': styles,
    '&:focus-visible': styles,
  };
}

/**
 * Создает стили для disabled-состояния
 *
 * @param styles - Стили для отключенного состояния
 * @returns Объект SxProps для disabled
 *
 * @example
 * ```ts
 * <Button sx={createDisabledStyles({ opacity: 0.5 })} disabled>
 *   Отключенная кнопка
 * </Button>
 * ```
 */
export function createDisabledStyles(styles: SxProps<Theme>): SxProps<Theme> {
  return {
    '&:disabled': styles,
    '&.Mui-disabled': styles,
  };
}

/**
 * Создает z-index для общих слоев приложения
 *
 * @param layer - Имя слоя приложения
 * @returns Z-index значение
 *
 * @example
 * ```ts
 * <Box sx={{ zIndex: getZIndex('modal') }}>
 *   Модальное окно
 * </Box>
 * ```
 */
export function getZIndex(
  layer: 'mobileStepper' | 'speedDial' | 'appBar' | 'drawer' | 'modal' | 'snackbar' | 'tooltip'
): number {
  const zIndexMap = {
    mobileStepper: 1000,
    speedDial: 1050,
    appBar: 1100,
    drawer: 1200,
    modal: 1300,
    snackbar: 1400,
    tooltip: 1500,
  };

  return zIndexMap[layer];
}

/**
 * Объединяет несколько SxProps в один
 *
 * @param styles - Массив SxProps для объединения
 * @returns Объединенный SxProps
 *
 * @example
 * ```ts
 * const combinedStyles = mergeSxProps([
 *   createFlexContainer({ direction: 'column' }),
 *   centerContent(),
 *   { gap: 2 }
 * ]);
 *
 * <Box sx={combinedStyles}>Контент</Box>
 * ```
 */
export function mergeSxProps(...styles: (SxProps<Theme> | undefined)[]): SxProps<Theme> {
  return styles.reduce<SxProps<Theme>>((acc, style) => {
    if (style) {
      return { ...acc, ...style };
    }
    return acc;
  }, {});
}
