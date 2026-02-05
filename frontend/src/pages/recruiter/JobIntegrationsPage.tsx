/**
 * Страница интеграций с job-платформами
 *
 * Управление интеграциями с внешними платформами публикации вакансий:
 * - LinkedIn, Indeed, Glassdoor и др.
 * - Настройка автоматической публикации
 * - Мониторинг статуса публикаций
 * - Синхронизация вакансий
 */

// Импорт хука состояния React
import { useState } from 'react';

// Импорт компонентов MUI
import {
  Box,
  Container,
  Typography,
  Paper,
  Stack,
  Grid,
  Card,
  CardContent,
  Button,
  Switch,
  FormControlLabel,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';

// Импорт иконок MUI
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Link as LinkIcon,
  Sync as SyncIcon,
  Settings as SettingsIcon,
  Launch as LaunchIcon,
} from '@mui/icons-material';

// Интерфейс интеграции с платформой
interface JobPlatform {
  id: string;
  name: string;
  icon: string;
  connected: boolean;
  auto_publish: boolean;
  last_sync: string | null;
  status: 'active' | 'error' | 'pending';
  jobs_posted: number;
}

/**
 * Страница интеграций с job-платформами
 */
export function JobIntegrationsPage() {
  // Состояние диалога настроек
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<JobPlatform | null>(null);

  // Состояние синхронизации
  const [syncing, setSyncing] = useState<string | null>(null);

  // Состояние уведомлений
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Тестовые данные платформ
  const [platforms, setPlatforms] = useState<JobPlatform[]>([
    {
      id: 'linkedin',
      name: 'LinkedIn',
      icon: 'in',
      connected: true,
      auto_publish: true,
      last_sync: '2025-01-15T10:30:00Z',
      status: 'active',
      jobs_posted: 12,
    },
    {
      id: 'indeed',
      name: 'Indeed',
      icon: 'indeed',
      connected: true,
      auto_publish: false,
      last_sync: '2025-01-14T15:45:00Z',
      status: 'active',
      jobs_posted: 8,
    },
    {
      id: 'glassdoor',
      name: 'Glassdoor',
      icon: 'glassdoor',
      connected: false,
      auto_publish: false,
      last_sync: null,
      status: 'pending',
      jobs_posted: 0,
    },
  ]);

  // Обработчик переключения автопубликации
  const handleAutoPublishToggle = (platformId: string) => {
    setPlatforms((prev) =>
      prev.map((p) =>
        p.id === platformId ? { ...p, auto_publish: !p.auto_publish } : p
      )
    );
  };

  // Обработчик подключения платформы
  const handleConnect = (platform: JobPlatform) => {
    setSelectedPlatform(platform);
    setSettingsDialogOpen(true);
  };

  // Обработчик отключения платформы
  const handleDisconnect = (platformId: string) => {
    setPlatforms((prev) =>
      prev.map((p) =>
        p.id === platformId
          ? { ...p, connected: false, auto_publish: false, status: 'pending' as const, jobs_posted: 0 }
          : p
      )
    );
    setNotification({ type: 'success', message: 'Platform disconnected successfully' });
  };

  // Обработчик синхронизации
  const handleSync = (platformId: string) => {
    setSyncing(platformId);
    // Имитация синхронизации
    setTimeout(() => {
      setPlatforms((prev) =>
        prev.map((p) =>
          p.id === platformId
            ? { ...p, last_sync: new Date().toISOString(), status: 'active' as const }
            : p
        )
      );
      setSyncing(null);
      setNotification({ type: 'success', message: 'Sync completed successfully' });
    }, 2000);
  };

  // Получить цвет статуса
  const getStatusColor = (status: JobPlatform['status']) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'error':
        return 'error';
      case 'pending':
        return 'default';
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 } }}>
      <Stack spacing={4}>
        {/* Заголовок страницы */}
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Job Platform Integrations
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Connect and manage job posting platforms to automatically publish your vacancies
          </Typography>
        </Box>

        {/* Уведомление */}
        {notification && (
          <Alert
            severity={notification.type}
            onClose={() => setNotification(null)}
            sx={{ mb: 2 }}
          >
            {notification.message}
          </Alert>
        )}

        {/* Информация о подключенных платформах */}
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" fontWeight={700} color="primary.main">
                  {platforms.filter((p) => p.connected).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Connected Platforms
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" fontWeight={700} color="success.main">
                  {platforms.reduce((sum, p) => sum + p.jobs_posted, 0)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Jobs Posted
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" fontWeight={700} color="info.main">
                  {platforms.filter((p) => p.auto_publish).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Auto-Publish Enabled
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Список платформ */}
        <Paper>
          <List>
            {platforms.map((platform) => (
              <React.Fragment key={platform.id}>
                <ListItem>
                  <ListItemIcon>
                    <Box
                      sx={{
                        width: 40,
                        height: 40,
                        borderRadius: 2,
                        bgcolor: platform.connected ? 'primary.main' : 'grey.300',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontWeight: 700,
                      }}
                    >
                      {platform.icon.substring(0, 2).toUpperCase()}
                    </Box>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Typography variant="subtitle1" fontWeight={600}>
                          {platform.name}
                        </Typography>
                        <Chip
                          label={platform.connected ? platform.status : 'Not Connected'}
                          color={getStatusColor(platform.connected ? platform.status : 'pending') as any}
                          size="small"
                        />
                      </Stack>
                    }
                    secondary={
                      <Stack spacing={0.5}>
                        {platform.connected && platform.last_sync && (
                          <Typography variant="caption">
                            Last sync: {new Date(platform.last_sync).toLocaleString()}
                          </Typography>
                        )}
                        <Typography variant="caption" color="text.secondary">
                          {platform.jobs_posted} jobs posted
                        </Typography>
                      </Stack>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Stack direction="row" spacing={1}>
                      {platform.connected && (
                        <>
                          <FormControlLabel
                            control={
                              <Switch
                                checked={platform.auto_publish}
                                onChange={() => handleAutoPublishToggle(platform.id)}
                                size="small"
                              />
                            }
                            label="Auto"
                          />
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={syncing === platform.id ? <CircularProgress size={16} /> : <SyncIcon />}
                            onClick={() => handleSync(platform.id)}
                            disabled={syncing !== null}
                          >
                            Sync
                          </Button>
                          <Button
                            size="small"
                            color="error"
                            onClick={() => handleDisconnect(platform.id)}
                          >
                            Disconnect
                          </Button>
                        </>
                      )}
                      {!platform.connected && (
                        <Button
                          variant="contained"
                          startIcon={<LinkIcon />}
                          onClick={() => handleConnect(platform)}
                        >
                          Connect
                        </Button>
                      )}
                      <Button
                        size="small"
                        startIcon={<LaunchIcon />}
                        href={`https://${platform.id.toLowerCase()}.com`}
                        target="_blank"
                      >
                        Visit
                      </Button>
                    </Stack>
                  </ListItemSecondaryAction>
                </ListItem>
                {platforms.indexOf(platform) < platforms.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </Paper>

        {/* Диалог настроек подключения */}
        <Dialog open={settingsDialogOpen} onClose={() => setSettingsDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            Connect to {selectedPlatform?.name}
          </DialogTitle>
          <DialogContent>
            <Stack spacing={3} sx={{ mt: 2 }}>
              <Alert severity="info">
                To connect your {selectedPlatform?.name} account, you'll need to provide your API credentials.
              </Alert>
              <TextField
                fullWidth
                label="API Key"
                type="password"
                placeholder="Enter your API key"
              />
              <TextField
                fullWidth
                label="API Secret"
                type="password"
                placeholder="Enter your API secret"
              />
              <Typography variant="caption" color="text.secondary">
                Don't have an API key? Visit the {selectedPlatform?.name} developer portal to generate one.
              </Typography>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSettingsDialogOpen(false)}>Cancel</Button>
            <Button
              variant="contained"
              onClick={() => {
                if (selectedPlatform) {
                  setPlatforms((prev) =>
                    prev.map((p) =>
                      p.id === selectedPlatform.id
                        ? { ...p, connected: true, status: 'active' as const }
                        : p
                    )
                  );
                }
                setSettingsDialogOpen(false);
                setNotification({ type: 'success', message: 'Platform connected successfully' });
              }}
            >
              Connect
            </Button>
          </DialogActions>
        </Dialog>
      </Stack>
    </Container>
  );
}

export default JobIntegrationsPage;
