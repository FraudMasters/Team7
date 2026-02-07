import React from 'react';
import {
  Select,
  SelectProps,
  MenuItem,
  MenuItemProps,
  FormControl,
  FormControlProps,
  InputLabel,
  InputLabelProps,
  SelectChangeEvent,
} from '@mui/material';

/**
 * Интерфейс свойств компонента Select
 *
 * Расширяет стандартные свойства MUI Select,
 * позволяя использовать все доступные опции
 */
export interface MuiSelectProps<T = unknown> extends Omit<SelectProps<T>, 'variant'> {
  /**
   * Вариант отображения выпадающего списка
   * @default 'outlined'
   */
  variant?: 'filled' | 'outlined' | 'standard';
}

/**
 * Интерфейс свойств компонента MenuItem
 *
 * Расширяет стандартные свойства MUI MenuItem
 */
export interface MuiMenuItemProps extends MenuItemProps {}

/**
 * Интерфейс свойств компонента FormControl
 *
 * Расширяет стандартные свойства MUI FormControl
 */
export interface MuiFormControlProps extends FormControlProps {}

/**
 * Интерфейс свойств компонента InputLabel
 *
 * Расширяет стандартные свойства MUI InputLabel
 */
export interface MuiInputLabelProps extends InputLabelProps {}

/**
 * Компонент Select - обёртка над MUI Select
 *
 * Предоставляет стандартизированный выпадающий список с возможностью
 * кастомизации через свойства MUI. Все комментарии на русском языке.
 *
 * Основные возможности:
 * - Три варианта отображения: filled, outlined, standard
 * - Поддержка одиночного и множественного выбора
 * - Автоматическая ширина или fullWidth режим
 * - Размеры: small, medium
 * - Поддержка группировки опций
 * - Виртуализация для больших списков
 * - Доступность (accessibility) из коробки
 * - Интеграция с FormControl для форм
 *
 * @example
 * ```tsx
 * // Базовое использование
 * <FormControl fullWidth>
 *   <InputLabel>Выберите опцию</InputLabel>
 *   <Select value={value} label="Выберите опцию" onChange={handleChange}>
 *     <MenuItem value="option1">Опция 1</MenuItem>
 *     <MenuItem value="option2">Опция 2</MenuItem>
 *     <MenuItem value="option3">Опция 3</MenuItem>
 *   </Select>
 * </FormControl>
 *
 * // С использованием компонентов из этого файла
 * <FormControl fullWidth>
 *   <InputLabel>Статус</InputLabel>
 *   <Select
 *     value={status}
 *     label="Статус"
 *     onChange={(e) => setStatus(e.target.value)}
 *   >
 *     <MenuItem value="active">Активен</MenuItem>
 *     <MenuItem value="inactive">Неактивен</MenuItem>
 *     <MenuItem value="pending">В ожидании</MenuItem>
 *   </Select>
 * </FormControl>
 *
 * // Множественный выбор
 * <Select
 *   multiple
 *   value={selectedItems}
 *   onChange={handleMultipleChange}
 *   label="Выберите элементы"
 * >
 *   <MenuItem value="item1">Элемент 1</MenuItem>
 *   <MenuItem value="item2">Элемент 2</MenuItem>
 *   <MenuItem value="item3">Элемент 3</MenuItem>
 * </Select>
 *
 * // С иконками и дополнительным содержимым
 * <Select value={user} label="Пользователь" onChange={handleUserChange}>
 *   <MenuItem value="user1">
 *     <Stack direction="row" spacing={1} alignItems="center">
 *       <Avatar src="/avatar1.jpg" />
 *       <ListItemText primary="Иван Иванов" secondary="ivan@example.com" />
 *     </Stack>
 *   </MenuItem>
 *   <MenuItem value="user2">
 *     <Stack direction="row" spacing={1} alignItems="center">
 *       <Avatar src="/avatar2.jpg" />
 *       <ListItemText primary="Мария Петрова" secondary="maria@example.com" />
 *     </Stack>
 *   </MenuItem>
 * </Select>
 *
 * // Отключённый селект
 * <Select
 *   disabled
 *   value={value}
 *   label="Недоступно"
 * />
 *
 * // Компактный размер
 * <Select
 *   size="small"
 *   value={priority}
 *   label="Приоритет"
 *   onChange={handlePriorityChange}
 * >
 *   <MenuItem value="low">Низкий</MenuItem>
 *   <MenuItem value="medium">Средний</MenuItem>
 *   <MenuItem value="high">Высокий</MenuItem>
 * </Select>
 *
 * // С отображением текста по умолчанию
 * <Select value="" displayEmpty>
 *   <MenuItem value="" disabled>
 *     <em>Выберите значение</em>
 *   </MenuItem>
 *   <MenuItem value="option1">Опция 1</MenuItem>
 *   <MenuItem value="option2">Опция 2</MenuItem>
 * </Select>
 *
 * // С вариантом filled
 * <FormControl>
 *   <InputLabel>Категория</InputLabel>
 *   <Select
 *     variant="filled"
 *     value={category}
 *     label="Категория"
 *     onChange={handleCategoryChange}
 *   >
 *     <MenuItem value="tech">Технологии</MenuItem>
 *     <MenuItem value="design">Дизайн</MenuItem>
 *     <MenuItem value="marketing">Маркетинг</MenuItem>
 *   </Select>
 * </FormControl>
 * ```
 */
export const SelectWrapper = <T extends unknown = string>({
  variant = 'outlined',
  children,
  ...rest
}: MuiSelectProps<T>) => {
  return (
    <Select<T>
      variant={variant}
      {...rest}
    >
      {children}
    </Select>
  );
};

/**
 * Компонент MenuItem - обёртка над MUI MenuItem
 *
 * Предоставляет стандартизированный пункт выпадающего списка.
 *
 * @example
 * ```tsx
 * // Базовое использование
 * <MenuItem value="option1">Опция 1</MenuItem>
 *
 * // С дополнительными свойствами
 * <MenuItem value="option2" disabled>
 *   Отключённая опция
 * </MenuItem>
 *
 * // С автоматическим фокусом
 * <MenuItem value="option3" autoFocus>
 *   Опция с автофокусом
 * </MenuItem>
 *
 * // С иконкой
 * <MenuItem value="settings">
 *   <ListItemIcon>
 *     <SettingsIcon />
 *   </ListItemIcon>
 *   <ListItemText>Настройки</ListItemText>
 * </MenuItem>
 * ```
 */
export const MenuItemWrapper: React.FC<MuiMenuItemProps> = ({
  children,
  ...rest
}) => {
  return (
    <MenuItem {...rest}>
      {children}
    </MenuItem>
  );
};

/**
 * Компонент FormControl - обёртка над MUI FormControl
 *
 * Предоставляет контейнер для компонентов формы (Select, TextField и др.).
 * Обеспечивает правильное расположение label, helper text и ошибок.
 *
 * @example
 * ```tsx
 * // Базовое использование
 * <FormControl fullWidth>
 *   <InputLabel>Имя</InputLabel>
 *   <Select value={name} label="Имя" onChange={handleChange}>
 *     <MenuItem value="Иван">Иван</MenuItem>
 *     <MenuItem value="Мария">Мария</MenuItem>
 *   </Select>
 *   <FormHelperText>Введите ваше имя</FormHelperText>
 * </FormControl>
 *
 * // С обязательным полем
 * <FormControl required fullWidth>
 *   <InputLabel>Email</InputLabel>
 *   <Select value={email} label="Email" onChange={handleChange}>
 *     <MenuItem value="email1">email1@example.com</MenuItem>
 *     <MenuItem value="email2">email2@example.com</MenuItem>
 *   </Select>
 * </FormControl>
 *
 * // С ошибкой
 * <FormControl error fullWidth>
 *   <InputLabel>Страна</InputLabel>
 *   <Select value={country} label="Страна" onChange={handleChange}>
 *     <MenuItem value="ru">Россия</MenuItem>
 *     <MenuItem value="us">США</MenuItem>
 *   </Select>
 *   <FormHelperText>Обязательное поле</FormHelperText>
 * </FormControl>
 *
 * // Компактный размер
 * <FormControl size="small" fullWidth>
 *   <InputLabel>Статус</InputLabel>
 *   <Select value={status} label="Статус" onChange={handleChange}>
 *     <MenuItem value="active">Активен</MenuItem>
 *     <MenuItem value="inactive">Неактивен</MenuItem>
 *   </Select>
 * </FormControl>
 * ```
 */
export const FormControlWrapper: React.FC<MuiFormControlProps> = ({
  children,
  ...rest
}) => {
  return (
    <FormControl {...rest}>
      {children}
    </FormControl>
  );
};

/**
 * Компонент InputLabel - обёртка над MUI InputLabel
 *
 * Предоставляет стандартизированную метку для полей ввода и селектов.
 *
 * @example
 * ```tsx
 * // Базовое использование
 * <InputLabel htmlFor="my-select">Выберите опцию</InputLabel>
 * <Select id="my-select" value={value} label="Выберите опцию">
 *   <MenuItem value="option1">Опция 1</MenuItem>
 * </Select>
 *
 * // Обязательное поле
 * <InputLabel required>Email</InputLabel>
 *
 * // Уменьшенный размер
 * <InputLabel size="small">Имя пользователя</InputLabel>
 *
 * // Отключённая метка
 * <InputLabel disabled>Недоступно</InputLabel>
 * ```
 */
export const InputLabelWrapper: React.FC<MuiInputLabelProps> = ({
  children,
  ...rest
}) => {
  return (
    <InputLabel {...rest}>
      {children}
    </InputLabel>
  );
};

/**
 * Экспорт компонентов по умолчанию
 * Позволяет импортировать как: import Select from './Select'
 */
export default SelectWrapper;

/**
 * Именованный экспорт главного компонента Select для удобства
 */
export { SelectWrapper as Select };

/**
 * Экспорт типа события изменения для использования в компонентах
 */
export type { SelectChangeEvent };
