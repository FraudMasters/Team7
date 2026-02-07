import React from 'react';
import { Card, CardProps } from '@mui/material';

/**
 * Интерфейс свойств компонента Card
 *
 * Расширяет стандартные свойства MUI Card,
 * позволяя использовать все доступные опции
 */
export interface MuiCardProps extends CardProps {}

/**
 * Компонент Card - обёртка над MUI Card
 *
 * Предоставляет стандартизированный контейнер для содержимого с возможностью
 * кастомизации через свойства MUI. Все комментарии на русском языке.
 *
 * Основные возможности:
 * - Контейнер для группировки связанного содержимого
 * - Поддержка всех вариантов отображения MUI (elevated, outlined)
 * - Гибкая настройка через sx prop
 * - Полная поддержка accessibility
 * - Вложенные компоненты: CardHeader, CardContent, CardActions, CardMedia
 *
 * @example
 * ```tsx
 * // Базовое использование
 * import { CardContent } from '@mui/material';
 *
 * <Card>
 *   <CardContent>
 *     <Typography variant="h5">Заголовок карточки</Typography>
 *     <Typography variant="body2">Содержимое карточки</Typography>
 *   </CardContent>
 * </Card>
 *
 * // С настройкой стилей
 * <Card
 *   sx={{ minWidth: 275, bgcolor: 'background.paper' }}
 *   elevation={3}
 * >
 *   <CardContent>
 *     Контент
 *   </CardContent>
 * </Card>
 *
 * // С вариантами отображения
 * <Card variant="outlined">
 *   <CardContent>
 *     Контент в карточке с контуром
 *   </CardContent>
 * </Card>
 * ```
 */
export const Card: React.FC<MuiCardProps> = ({
  children,
  ...rest
}) => {
  return (
    <Card {...rest}>
      {children}
    </Card>
  );
};

/**
 * Экспорт компонента по умолчанию
 * Позволяет импортировать как: import Card from './Card'
 */
export default Card;
