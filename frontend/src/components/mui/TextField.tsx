import React from 'react';
import { TextField, TextFieldProps } from '@mui/material';

/**
 * Интерфейс свойств компонента TextField
 *
 * Расширяет стандартные свойства MUI TextField,
 * позволяя использовать все доступные опции
 */
export interface MuiTextFieldProps extends Omit<TextFieldProps, 'variant'> {
  /**
   * Вариант отображения текстового поля
   * @default 'outlined'
   */
  variant?: 'filled' | 'outlined' | 'standard';
}

/**
 * Компонент TextField - обёртка над MUI TextField
 *
 * Предоставляет стандартизированное текстовое поле с возможностью
 * кастомизации через свойства MUI. Все комментарии на русском языке.
 *
 * Основные возможности:
 * - Три варианта отображения: filled, outlined, standard
 * - Поддержка всех типов ввода: text, password, email, number, tel и др.
 * - Валидация с отображением ошибок и вспомогательного текста
 * - Поддержка multiline и textarea режимов
 * - Адаптивный размер (size): small, medium
 * - Иконки (начальная и конечная): startIcon, endIcon, InputProps/adornments
 * - Полная поддержка accessibility
 * - Интеграция с формами через FormControl
 *
 * @example
 * ```tsx
 * // Базовое использование
 * <TextField
 *   label="Имя"
 *   placeholder="Введите ваше имя"
 *   value={name}
 *   onChange={(e) => setName(e.target.value)}
 * />
 *
 * // С валидацией
 * <TextField
 *   label="Email"
 *   type="email"
 *   value={email}
 *   onChange={handleEmailChange}
 *   error={hasError}
 *   helperText={hasError ? 'Некорректный email' : 'example@mail.com'}
 *   required
 * />
 *
 * // Многострочное текстовое поле
 * <TextField
 *   label="Описание"
 *   multiline
 *   rows={4}
 *   fullWidth
 *   value={description}
 *   onChange={(e) => setDescription(e.target.value)}
 * />
 *
 * // Поле пароля с иконкой
 * <TextField
 *   label="Пароль"
 *   type={showPassword ? 'text' : 'password'}
 *   value={password}
 *   onChange={(e) => setPassword(e.target.value)}
 *   InputProps={{
 *     endAdornment: (
 *       <InputAdornment position="end">
 *         <IconButton onClick={() => setShowPassword(!showPassword)}>
 *           {showPassword ? <VisibilityOff /> : <Visibility />}
 *         </IconButton>
 *       </InputAdornment>
 *     ),
 *   }}
 * />
 *
 * // Компактный размер
 * <TextField
 *   label="Код"
 *   size="small"
 *   variant="filled"
 *   value={code}
 *   onChange={(e) => setCode(e.target.value)}
 * />
 *
 * // Числовое поле с ограничениями
 * <TextField
 *   label="Возраст"
 *   type="number"
 *   InputProps={{ inputProps: { min: 18, max: 100 } }}
 *   value={age}
 *   onChange={(e) => setAge(e.target.value)}
 * />
 *
 * // Автофокус и только чтение
 * <TextField
 *   label="Username"
 *   defaultValue="@user"
 *   autoFocus
 *   InputProps={{
 *     readOnly: true,
 *   }}
 * />
 * ```
 */
export const TextFieldWrapper: React.FC<MuiTextFieldProps> = ({
  variant = 'outlined',
  children,
  ...rest
}) => {
  return (
    <TextField
      variant={variant}
      {...rest}
    >
      {children}
    </TextField>
  );
};

/**
 * Экспорт компонента по умолчанию
 * Позволяет импортировать как: import TextField from './TextField'
 */
export default TextFieldWrapper;

/**
 * Именованный экспорт главного компонента TextField для удобства
 */
export { TextFieldWrapper as TextField };
