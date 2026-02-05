import React from 'react';
import {
  Dialog,
  DialogProps,
  DialogTitle,
  DialogTitleProps,
  DialogContent,
  DialogContentProps,
  DialogContentText,
  DialogContentTextProps,
  DialogActions,
  DialogActionsProps,
} from '@mui/material';

/**
 * Интерфейс свойств компонента Dialog
 *
 * Расширяет стандартные свойства MUI Dialog,
 * позволяя использовать все доступные опции
 */
export interface MuiDialogProps extends DialogProps {}

/**
 * Интерфейс свойств компонента DialogTitle
 *
 * Расширяет стандартные свойства MUI DialogTitle
 */
export interface MuiDialogTitleProps extends DialogTitleProps {}

/**
 * Интерфейс свойств компонента DialogContent
 *
 * Расширяет стандартные свойства MUI DialogContent
 */
export interface MuiDialogContentProps extends DialogContentProps {}

/**
 * Интерфейс свойств компонента DialogContentText
 *
 * Расширяет стандартные свойства MUI DialogContentText
 */
export interface MuiDialogContentTextProps extends DialogContentTextProps {}

/**
 * Интерфейс свойств компонента DialogActions
 *
 * Расширяет стандартные свойства MUI DialogActions
 */
export interface MuiDialogActionsProps extends DialogActionsProps {}

/**
 * Компонент Dialog - обёртка над MUI Dialog
 *
 * Предоставляет стандартизированное модальное окно с возможностью
 * кастомизации через свойства MUI. Все комментарии на русском языке.
 *
 * Основные возможности:
 * - Модальное окно для отображения важной информации
 * - Поддержка различных размеров (xs, sm, md, lg, xl, false)
 * - Полная настройка через sx prop
 * - Управление открытым/закрытым состоянием через open prop
 * - Поддержка fullscreen режима
 * - Полная поддержка accessibility
 *
 * @example
 * ```tsx
 * // Базовое использование
 * <Dialog open={open} onClose={handleClose}>
 *   <DialogTitle>Заголовок диалога</DialogTitle>
 *   <DialogContent>
 *     <DialogContentText>
 *       Содержимое диалогового окна
 *     </DialogContentText>
 *   </DialogContent>
 *   <DialogActions>
 *     <Button onClick={handleClose}>Отмена</Button>
 *     <Button onClick={handleConfirm}>Подтвердить</Button>
 *   </DialogActions>
 * </Dialog>
 *
 * // С настройкой размера и отступов
 * <Dialog
 *   open={open}
 *   onClose={handleClose}
 *   maxWidth="md"
 *   fullWidth
 *   PaperProps={{ sx: { borderRadius: 2 } }}
 * >
 *   <DialogContent>
 *     Контент в диалоге среднего размера
 *   </DialogContent>
 * </Dialog>
 *
 * // Полноэкранный режим (для мобильных устройств)
 * <Dialog
 *   open={open}
 *   onClose={handleClose}
 *   fullScreen
 * >
 *   <DialogTitle>Полноэкранный диалог</DialogTitle>
 *   <DialogContent>Контент на весь экран</DialogContent>
 * </Dialog>
 * ```
 */
export const DialogWrapper: React.FC<MuiDialogProps> = ({
  children,
  ...rest
}) => {
  return (
    <Dialog {...rest}>
      {children}
    </Dialog>
  );
};

/**
 * Компонент DialogTitle - обёртка над MUI DialogTitle
 *
 * Предоставляет заголовок для диалогового окна с возможностью
 * кастомизации через свойства MUI.
 *
 * @example
 * ```tsx
 * <DialogTitle>Заголовок диалога</DialogTitle>
 *
 * // С дополнительным действием (например, кнопка закрытия)
 * <DialogTitle>
 *   <Box display="flex" alignItems="center" justifyContent="space-between">
 *     <Typography variant="h6">Заголовок</Typography>
 *     <IconButton onClick={handleClose}>
 *       <CloseIcon />
 *     </IconButton>
 *   </Box>
 * </DialogTitle>
 * ```
 */
export const DialogTitleWrapper: React.FC<MuiDialogTitleProps> = ({
  children,
  ...rest
}) => {
  return (
    <DialogTitle {...rest}>
      {children}
    </DialogTitle>
  );
};

/**
 * Компонент DialogContent - обёртка над MUI DialogContent
 *
 * Предоставляет контейнер для содержимого диалогового окна.
 *
 * @example
 * ```tsx
 * <DialogContent>
 *   <DialogContentText>
 *     Описание действия в диалоге
 *   </DialogContentText>
 *   <TextField
 *     autoFocus
 *     margin="dense"
 *     label="Email"
 *     fullWidth
 *   />
 * </DialogContent>
 * ```
 */
export const DialogContentWrapper: React.FC<MuiDialogContentProps> = ({
  children,
  ...rest
}) => {
  return (
    <DialogContent {...rest}>
      {children}
    </DialogContent>
  );
};

/**
 * Компонент DialogContentText - обёртка над MUI DialogContentText
 *
 * Предоставляет стандартизированный текст для содержимого диалога.
 *
 * @example
 * ```tsx
 * <DialogContent>
 *   <DialogContentText>
 *     Подтвердите удаление элемента. Это действие нельзя отменить.
 *   </DialogContentText>
 * </DialogContent>
 * ```
 */
export const DialogContentTextWrapper: React.FC<MuiDialogContentTextProps> = ({
  children,
  ...rest
}) => {
  return (
    <DialogContentText {...rest}>
      {children}
    </DialogContentText>
  );
};

/**
 * Компонент DialogActions - обёртка над MUI DialogActions
 *
 * Предоставляет контейнер для кнопок действий в диалоговом окне.
 * Кнопки автоматически выравниваются по правому краю.
 *
 * @example
 * ```tsx
 * <DialogActions>
 *   <Button onClick={handleClose}>Отмена</Button>
 *   <Button onClick={handleSave} variant="contained">
 *     Сохранить
 *   </Button>
 * </DialogActions>
 *
 * // С настраиваемым выравниванием
 * <DialogActions sx={{ justifyContent: 'space-between' }}>
 *   <Button color="error">Удалить</Button>
 *   <Box>
 *     <Button onClick={handleClose}>Отмена</Button>
 *     <Button onClick={handleConfirm}>Подтвердить</Button>
 *   </Box>
 * </DialogActions>
 * ```
 */
export const DialogActionsWrapper: React.FC<MuiDialogActionsProps> = ({
  children,
  ...rest
}) => {
  return (
    <DialogActions {...rest}>
      {children}
    </DialogActions>
  );
};

/**
 * Экспорт компонентов по умолчанию
 * Позволяет импортировать как: import Dialog from './Dialog'
 */
export default DialogWrapper;

/**
 * Именованный экспорт главного компонента Dialog для удобства
 */
export { DialogWrapper as Dialog };
