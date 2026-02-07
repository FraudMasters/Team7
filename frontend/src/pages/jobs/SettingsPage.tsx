// Импорт хуков для управления состоянием
import { useState } from 'react';
// Импорт компонентов MUI для UI
import {
  Container,          // Контейнер для ограничения ширины содержимого
  Typography,         // Компонент для текста с различными стилями
  Box,                // Универсальный контейнер для верстки
  Paper,              // Контейнер с эффектом elevated (карточка)
  Grid,               // Сетка для адаптивной верстки
  TextField,          // Поле ввода текста
  Button,             // Кнопки
  Switch,             // Переключатель
  FormControlLabel,   // Метка с контролом
  Divider,            // Разделитель
  List,               // Список
  ListItem,           // Элемент списка
  ListItemText,       // Текст элемента списка
  ListItemSecondaryAction, // Вторичное действие элемента списка
  Card,               // Карточка
  CardContent,        // Содержимое карточки
  Select,             // Выпадающий список
  MenuItem,           // Пункт выпадающего списка
  FormControl,        // Контейнер для элементов форм
  InputLabel,         // Метка поля ввода
} from '@mui/material';
// Импорт иконок из MUI
import {
  Settings as SettingsIcon,
  Language as LanguageIcon,
  Notifications as NotificationsIcon,
  Lock as LockIcon,
  Palette as PaletteIcon,
  Visibility as VisibilityIcon,
  Email as EmailIcon,
} from '@mui/icons-material';
// Импорт MUI компонентов
import { PageTransition } from '@components/mui/PageTransition';
// Импорт хуков для работы с данными
import { useQuery } from '@tanstack/react-query';
// Импорт API функций
import { getLanguagePreference, updateLanguagePreference } from '../../api/preferences';

/**
 * Страница настроек
 * Позволяет управлять предпочтениями аккаунта и конфиденциальностью
 */
export function SettingsPage() {
  // Состояние выбранного языка
  const [language, setLanguage] = useState<'en' | 'ru'>('en');
  // Состояние настроек уведомлений
  const [notifications, setNotifications] = useState({
    emailNewJobs: true,
    emailApplicationUpdates: true,
    emailMessages: false,
    pushNewJobs: true,
    pushApplicationUpdates: true,
    pushMessages: true,
  });
  // Состояние настроек приватности
  const [privacy, setPrivacy] = useState({
    profileVisible: true,
    showSalary: false,
    allowRecruitersContact: true,
  });

  // Получение текущего языка с сервера
  const { data: langPref } = useQuery({
    queryKey: ['language-preference'],
    queryFn: getLanguagePreference,
  });

  /**
   * Обработчик изменения языка
   * @param newLang - Новый язык (en или ru)
   */
  const handleLanguageChange = async (newLang: 'en' | 'ru') => {
    setLanguage(newLang);
    try {
      await updateLanguagePreference(newLang);
    } catch (error) {
      console.error('Failed to update language preference:', error);
    }
  };

  return (
    <PageTransition>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Заголовок страницы */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <SettingsIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" fontWeight={700}>
                Settings
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Manage your account preferences and privacy
              </Typography>
            </Box>
          </Box>
        </Box>

        <Grid container spacing={3}>
          {/* Язык и регион */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <LanguageIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Language & Region
                </Typography>
              </Box>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Language</InputLabel>
                <Select
                  value={langPref?.language || language}
                  label="Language"
                  onChange={(e) => handleLanguageChange(e.target.value as 'en' | 'ru')}
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="ru">Русский</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Timezone"
                defaultValue="America/Los_Angeles"
                select
                sx={{ mb: 2 }}
              >
                <MenuItem value="America/Los_Angeles">Pacific Time (PT)</MenuItem>
                <MenuItem value="America/New_York">Eastern Time (ET)</MenuItem>
                <MenuItem value="America/Chicago">Central Time (CT)</MenuItem>
                <MenuItem value="Europe/London">GMT (London)</MenuItem>
                <MenuItem value="Europe/Moscow">MSK (Moscow)</MenuItem>
              </TextField>

              <TextField
                fullWidth
                label="Currency"
                select
              >
                <MenuItem value="USD">USD ($)</MenuItem>
                <MenuItem value="EUR">EUR (€)</MenuItem>
                <MenuItem value="GBP">GBP (£)</MenuItem>
                <MenuItem value="RUB">RUB (₽)</MenuItem>
              </TextField>
            </Paper>
          </Grid>

          {/* Оформление */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <PaletteIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Appearance
                </Typography>
              </Box>

              <TextField
                fullWidth
                label="Theme"
                select
                sx={{ mb: 2 }}
              >
                <MenuItem value="light">Light</MenuItem>
                <MenuItem value="dark">Dark</MenuItem>
                <MenuItem value="auto">System Default</MenuItem>
              </TextField>

              <TextField
                fullWidth
                label="Font Size"
                select
              >
                <MenuItem value="small">Small</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="large">Large</MenuItem>
              </TextField>

              <Box sx={{ mt: 2 }}>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Reduce animations"
                />
              </Box>
            </Paper>
          </Grid>

          {/* Уведомления */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <NotificationsIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Notifications
                </Typography>
              </Box>

              {/* Email-уведомления */}
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Email Notifications
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText primary="New job matches" secondary="Receive emails about new jobs" />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={notifications.emailNewJobs}
                      onChange={(e) =>
                        setNotifications({ ...notifications, emailNewJobs: e.target.checked })
                      }
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Application updates"
                    secondary="Status changes on your applications"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={notifications.emailApplicationUpdates}
                      onChange={(e) =>
                        setNotifications({
                          ...notifications,
                          emailApplicationUpdates: e.target.checked,
                        })
                      }
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText primary="Messages from recruiters" />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={notifications.emailMessages}
                      onChange={(e) =>
                        setNotifications({ ...notifications, emailMessages: e.target.checked })
                      }
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>

              <Divider sx={{ my: 2 }} />

              {/* Push-уведомления */}
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Push Notifications
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText primary="New job matches" />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={notifications.pushNewJobs}
                      onChange={(e) =>
                        setNotifications({ ...notifications, pushNewJobs: e.target.checked })
                      }
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText primary="Application updates" />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={notifications.pushApplicationUpdates}
                      onChange={(e) =>
                        setNotifications({
                          ...notifications,
                          pushApplicationUpdates: e.target.checked,
                        })
                      }
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText primary="Messages" />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={notifications.pushMessages}
                      onChange={(e) =>
                        setNotifications({ ...notifications, pushMessages: e.target.checked })
                      }
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>
            </Paper>
          </Grid>

          {/* Приватность */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <LockIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Privacy
                </Typography>
              </Box>

              <List>
                <ListItem>
                  <ListItemText
                    primary="Profile Visibility"
                    secondary="Allow recruiters to find your profile"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={privacy.profileVisible}
                      onChange={(e) =>
                        setPrivacy({ ...privacy, profileVisible: e.target.checked })
                      }
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Salary Expectations"
                    secondary="Show desired salary in profile"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={privacy.showSalary}
                      onChange={(e) => setPrivacy({ ...privacy, showSalary: e.target.checked })}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Recruiter Contact"
                    secondary="Allow recruiters to contact you directly"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={privacy.allowRecruitersContact}
                      onChange={(e) =>
                        setPrivacy({ ...privacy, allowRecruitersContact: e.target.checked })
                      }
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>

              <Divider sx={{ my: 2 }} />

              <TextField
                fullWidth
                label="Email Address"
                defaultValue="john.doe@example.com"
                sx={{ mb: 2 }}
                InputProps={{
                  startAdornment: <EmailIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />

              <Button variant="outlined" fullWidth startIcon={<VisibilityIcon />}>
                Change Password
              </Button>
            </Paper>
          </Grid>

          {/* Опасная зона */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3, border: '1px solid', borderColor: 'error.main' }}>
              <Typography variant="h6" fontWeight={600} color="error" gutterBottom>
                Danger Zone
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Irreversible actions that affect your account
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button variant="outlined" color="error">
                  Deactivate Account
                </Button>
                <Button variant="contained" color="error">
                  Delete Account
                </Button>
                <Button variant="outlined">Download My Data</Button>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </PageTransition>
  );
}
