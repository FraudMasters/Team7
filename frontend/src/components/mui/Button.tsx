import React from 'react';
import { Button, ButtonProps } from '@mui/material';

/**
 * Интерфейс свойств компонента Button
 *
 * Расширяет стандартные свойства MUI Button,
 * позволяя использовать все доступные опции
 */
export interface MuiButtonProps extends Omit<ButtonProps, 'variant'> {
  /**
   * Вариант отображения кнопки
   * @default 'contained'
   */
  variant?: 'text' | 'contained' | 'outlined';
}

/**
 * Компонент Button - обёртка над MUI Button
 *
 * Предоставляет стандартизированную кнопку с возможностью
 * кастомизации через свойства MUI. Все комментарии на русском языке.
 *
 * Основные возможности:
 * - Три варианта отображения: text, contained, outlined
 * - Поддержка всех цветов MUI (primary, secondary, success, error, warning, info)
 * - Размеры: small, medium, large
 * - Полная поддержка accessibility
 *
 * @example
 * ```tsx
 * // Базовое использование
 * <Button variant="contained" color="primary">
 *   Нажать
 * </Button>
 *
 * // С иконкой
 * <Button
 *   variant="outlined"
 *   startIcon={<AddIcon />}
 *   onClick={handleClick}
 * >
 *   Добавить
 * </Button>
 *
 * // Отключённая кнопка
 * <Button disabled variant="text">
 *   Недоступно
 * </Button>
 * ```
 */
export const Button: React.FC<MuiButtonProps> = ({
  variant = 'contained',
  children,
  ...rest
}) => {
  return (
    <Button
      variant={variant}
      {...rest}
    >
      {children}
    </Button>
  );
};

/**
 * Экспорт компонента по умолчанию
 * Позволяет импортировать как: import Button from './Button'
 */
export default Button;
