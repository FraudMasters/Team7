import { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  Paper,
  Button,
  Switch,
  Chip,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Email as EmailIcon,
  NotificationsActive as PushIcon,
} from '@mui/icons-material';
import { PageTransition } from '../../components/ui/PageTransition';

interface JobAlert {
  id: string;
  name: string;
  keywords: string[];
  location: string;
  workFormat: string;
  frequency: 'instant' | 'daily' | 'weekly';
  active: boolean;
  emailEnabled: boolean;
  pushEnabled: boolean;
  lastTriggered?: string;
  matchesCount: number;
}

const mockAlerts: JobAlert[] = [
  {
    id: '1',
    name: 'React Developer Roles',
    keywords: ['React', 'TypeScript', 'Frontend'],
    location: 'Remote',
    workFormat: 'remote',
    frequency: 'daily',
    active: true,
    emailEnabled: true,
    pushEnabled: true,
    lastTriggered: '2 hours ago',
    matchesCount: 12,
  },
  {
    id: '2',
    name: 'Senior Engineering Positions',
    keywords: ['Senior', 'Lead', 'Staff', 'Principal'],
    location: 'San Francisco, CA',
    workFormat: 'hybrid',
    frequency: 'instant',
    active: true,
    emailEnabled: true,
    pushEnabled: false,
    lastTriggered: '1 day ago',
    matchesCount: 5,
  },
  {
    id: '3',
    name: 'Data Science Jobs',
    keywords: ['Data Scientist', 'ML', 'Python', 'TensorFlow'],
    location: 'New York, NY',
    workFormat: 'office',
    frequency: 'weekly',
    active: false,
    emailEnabled: true,
    pushEnabled: false,
    lastTriggered: '1 week ago',
    matchesCount: 8,
  },
];

export function JobAlertsPage() {
  const [alerts, setAlerts] = useState<JobAlert[]>(mockAlerts);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newAlert, setNewAlert] = useState({
    name: '',
    keywords: '',
    location: '',
    workFormat: 'any',
    frequency: 'daily' as 'instant' | 'daily' | 'weekly',
  });

  const handleToggleAlert = (id: string) => {
    setAlerts((prev) =>
      prev.map((alert) =>
        alert.id === id ? { ...alert, active: !alert.active } : alert
      )
    );
  };

  const handleToggleEmail = (id: string) => {
    setAlerts((prev) =>
      prev.map((alert) =>
        alert.id === id ? { ...alert, emailEnabled: !alert.emailEnabled } : alert
      )
    );
  };

  const handleTogglePush = (id: string) => {
    setAlerts((prev) =>
      prev.map((alert) =>
        alert.id === id ? { ...alert, pushEnabled: !alert.pushEnabled } : alert
      )
    );
  };

  const handleDeleteAlert = (id: string) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== id));
  };

  const handleCreateAlert = () => {
    const alert: JobAlert = {
      id: Date.now().toString(),
      name: newAlert.name,
      keywords: newAlert.keywords.split(',').map((k) => k.trim()),
      location: newAlert.location,
      workFormat: newAlert.workFormat,
      frequency: newAlert.frequency,
      active: true,
      emailEnabled: true,
      pushEnabled: false,
      matchesCount: 0,
    };
    setAlerts((prev) => [...prev, alert]);
    setCreateDialogOpen(false);
    setNewAlert({
      name: '',
      keywords: '',
      location: '',
      workFormat: 'any',
      frequency: 'daily',
    });
  };

  return (
    <PageTransition>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 4 }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <NotificationsIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              <Box>
                <Typography variant="h4" fontWeight={700}>
                  Job Alerts
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Get notified when matching jobs are posted
                </Typography>
              </Box>
            </Box>
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Alert
          </Button>
        </Box>

        {/* Stats */}
        <Grid container spacing={2} sx={{ mb: 4 }}>
          <Grid item xs={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" fontWeight={700}>
                {alerts.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Total Alerts
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" fontWeight={700} color="success.main">
                {alerts.filter((a) => a.active).length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Active
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" fontWeight={700} color="primary">
                {alerts.reduce((acc, a) => acc + a.matchesCount, 0)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Total Matches
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Alerts List */}
        <Paper>
          <List>
            {alerts.map((alert, index) => (
              <Box key={alert.id}>
                <ListItem alignItems="flex-start">
                  <Box sx={{ flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                      <Typography variant="subtitle1" fontWeight={600}>
                        {alert.name}
                      </Typography>
                      <Chip
                        label={alert.active ? 'Active' : 'Paused'}
                        size="small"
                        color={alert.active ? 'success' : 'default'}
                      />
                      <Chip
                        label={alert.frequency}
                        size="small"
                        variant="outlined"
                        sx={{ textTransform: 'capitalize' }}
                      />
                    </Box>

                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1 }}>
                      {alert.keywords.map((keyword) => (
                        <Chip key={keyword} label={keyword} size="small" variant="outlined" />
                      ))}
                    </Box>

                <Box sx={{ display: 'flex', gap: 3, mt: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      Location:
                    </Typography>
                    <Typography variant="body2">{alert.location}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      Format:
                    </Typography>
                    <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                      {alert.workFormat}
                    </Typography>
                  </Box>
                  {alert.lastTriggered && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        Last triggered:
                      </Typography>
                      <Typography variant="body2">{alert.lastTriggered}</Typography>
                    </Box>
                  )}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      Matches:
                    </Typography>
                    <Typography variant="body2" color="primary" fontWeight={600}>
                      {alert.matchesCount}
                    </Typography>
                  </Box>
                </Box>
              </Box>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, ml: 2 }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 0.5,
                  }}
                >
                  <EmailIcon fontSize="small" color="action" />
                  <Switch
                    size="small"
                    checked={alert.emailEnabled}
                    onChange={() => handleToggleEmail(alert.id)}
                  />
                </Box>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 0.5,
                  }}
                >
                  <PushIcon fontSize="small" color="action" />
                  <Switch
                    size="small"
                    checked={alert.pushEnabled}
                    onChange={() => handleTogglePush(alert.id)}
                  />
                </Box>
              </Box>

              <ListItemSecondaryAction>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Switch
                    checked={alert.active}
                    onChange={() => handleToggleAlert(alert.id)}
                  />
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteAlert(alert.id)}
                    color="error"
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Box>
              </ListItemSecondaryAction>
            </ListItem>
                {index < alerts.length - 1 && <Divider />}
              </Box>
            ))}
          </List>

          {alerts.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <NotificationsIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No job alerts yet
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Create alerts to get notified about matching jobs
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setCreateDialogOpen(true)}
              >
                Create Your First Alert
              </Button>
            </Box>
          )}
        </Paper>

        {/* Create Alert Dialog */}
        <Dialog
          open={createDialogOpen}
          onClose={() => setCreateDialogOpen(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>Create Job Alert</DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <TextField
                label="Alert Name"
                fullWidth
                value={newAlert.name}
                onChange={(e) => setNewAlert({ ...newAlert, name: e.target.value })}
                placeholder="e.g., React Developer Roles"
              />
              <TextField
                label="Keywords"
                fullWidth
                value={newAlert.keywords}
                onChange={(e) => setNewAlert({ ...newAlert, keywords: e.target.value })}
                placeholder="e.g., React, TypeScript, Frontend"
                helperText="Separate keywords with commas"
              />
              <TextField
                label="Location"
                fullWidth
                value={newAlert.location}
                onChange={(e) => setNewAlert({ ...newAlert, location: e.target.value })}
                placeholder="e.g., Remote, San Francisco, CA"
              />
              <FormControl fullWidth>
                <InputLabel>Work Format</InputLabel>
                <Select
                  value={newAlert.workFormat}
                  label="Work Format"
                  onChange={(e) => setNewAlert({ ...newAlert, workFormat: e.target.value })}
                >
                  <MenuItem value="any">Any</MenuItem>
                  <MenuItem value="remote">Remote</MenuItem>
                  <MenuItem value="hybrid">Hybrid</MenuItem>
                  <MenuItem value="office">Office</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Frequency</InputLabel>
                <Select
                  value={newAlert.frequency}
                  label="Frequency"
                  onChange={(e) =>
                    setNewAlert({ ...newAlert, frequency: e.target.value as 'instant' | 'daily' | 'weekly' })
                  }
                >
                  <MenuItem value="instant">Instant</MenuItem>
                  <MenuItem value="daily">Daily Digest</MenuItem>
                  <MenuItem value="weekly">Weekly Digest</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
            <Button variant="contained" onClick={handleCreateAlert}>
              Create Alert
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </PageTransition>
  );
}
