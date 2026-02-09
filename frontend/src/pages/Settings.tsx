import React, { useState } from 'react';
import { Container, Typography, Box, Tabs, Tab, Paper } from '@mui/material';
import { useTranslation } from 'react-i18next';
import ProfileEditor from '@components/UserSettingsEditor';
import ApiKeysManager from '@components/ApiKeysManager';

/**
 * Tab Panel Props
 */
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

/**
 * TabPanel component for rendering tab content
 */
function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * Settings Page
 *
 * Provides a comprehensive interface for managing user settings across multiple categories:
 * - Profile: Personal information (name, email, role, avatar)
 * - Notifications: Email and in-app notification preferences
 * - Language: Language preference (English/Russian)
 *
 * This page is accessible at /settings and allows users to customize their experience.
 *
 * Features:
 * - Tabbed interface for organized settings
 * - Real-time updates and validation
 * - Persistent storage via backend API
 * - Optimistic UI updates
 */
const SettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const [tabValue, setTabValue] = useState(0);

  /**
   * Handle tab change
   */
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {t('settings.title', { defaultValue: 'Settings' })}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('settings.subtitle', { defaultValue: 'Manage your profile, notifications, and preferences' })}
        </Typography>
      </Box>

      {/* Settings Tabs */}
      <Paper elevation={2} sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="settings tabs"
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            px: 2,
            pt: 2,
          }}
        >
          <Tab
            label={t('settings.tabs.profile', { defaultValue: 'Profile' })}
            id="settings-tab-0"
            aria-controls="settings-tabpanel-0"
          />
          <Tab
            label={t('settings.tabs.notifications', { defaultValue: 'Notifications' })}
            id="settings-tab-1"
            aria-controls="settings-tabpanel-1"
          />
          <Tab
            label={t('settings.tabs.language', { defaultValue: 'Language' })}
            id="settings-tab-2"
            aria-controls="settings-tabpanel-2"
          />
          <Tab
            label={t('settings.tabs.apiKeys', { defaultValue: 'API Keys' })}
            id="settings-tab-3"
            aria-controls="settings-tabpanel-3"
          />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <TabPanel value={tabValue} index={0}>
        <ProfileEditor />
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <NotificationSettings />
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <LanguageSettings />
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <ApiKeysManager />
      </TabPanel>
    </Container>
  );
};

/**
 * Notification Settings Component
 *
 * Provides controls for managing email and in-app notification preferences.
 * Allows users to customize which notifications they receive and how frequently.
 */
const NotificationSettings: React.FC = () => {
  const { t } = useTranslation();

  return (
    <Paper elevation={1} sx={{ p: 3 }}>
      <Typography variant="h5" fontWeight={600} gutterBottom>
        {t('settings.notifications.title', { defaultValue: 'Notification Preferences' })}
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        {t('settings.notifications.description', {
          defaultValue: 'Customize how and when you receive notifications about candidate updates, application changes, and system alerts.'
        })}
      </Typography>

      <Box sx={{ mt: 3, p: 2, bgcolor: 'warning.lighter', borderRadius: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {t('settings.notifications.comingSoon', {
            defaultValue: 'Notification settings will be available in an upcoming release. For now, all notifications are enabled by default.'
          })}
        </Typography>
      </Box>

      {/* Future implementation will include:
          - Email notification toggles
          - In-app notification preferences
          - Notification frequency controls
          - Notification type filters
      */}
    </Paper>
  );
};

/**
 * Language Settings Component
 *
 * Provides interface for changing application language preference.
 * Supports English and Russian languages with automatic persistence.
 */
const LanguageSettings: React.FC = () => {
  const { t } = useTranslation();

  return (
    <Paper elevation={1} sx={{ p: 3 }}>
      <Typography variant="h5" fontWeight={600} gutterBottom>
        {t('settings.language.title', { defaultValue: 'Language Preference' })}
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        {t('settings.language.description', {
          defaultValue: 'Select your preferred language for the interface. This preference will be applied across all pages and persist between sessions.'
        })}
      </Typography>

      <Box sx={{ mt: 3, p: 2, bgcolor: 'info.lighter', borderRadius: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {t('settings.language.useHeaderSwitcher', {
            defaultValue: 'Use the language selector in the top navigation bar to change your language preference. Changes take effect immediately and are saved automatically.'
          })}
        </Typography>
      </Box>

      {/* Future implementation could include:
          - Direct language selection dropdown
          - Preview of selected language
          - Additional language options
      */}
    </Paper>
  );
};

export default SettingsPage;
