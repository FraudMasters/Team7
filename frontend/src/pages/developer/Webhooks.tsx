/**
 * Webhooks Management Page
 *
 * Main page for managing webhook subscriptions for real-time event notifications.
 *
 * @module pages/developer/Webhooks
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  Stack,
  Grid,
  Card,
  CardContent,
  Alert,
  AlertTitle,
  Chip,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Webhook as WebhookIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  NotificationsActive as NotificationsIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import WebhookList from '@/components/developer/WebhookList';
import WebhookForm from '@/components/developer/WebhookForm';
import { webhooksClient, type WebhookStatistics } from '@/api/webhooks';

/**
 * Webhooks Page Component
 *
 * Provides a comprehensive interface for managing webhook subscriptions:
 * - View all webhook subscriptions
 * - Create new webhook subscriptions
 * - View delivery logs
 * - Enable/disable subscriptions
 * - Display usage statistics
 *
 * @example
 * ```tsx
 * // Routed at /developer/webhooks
 * import { Webhooks } from '@/pages/developer/Webhooks';
 * ```
 */
const Webhooks: React.FC = () => {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [statistics, setStatistics] = useState<WebhookStatistics | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  const fetchStatistics = useCallback(async () => {
    setStatsLoading(true);
    setStatsError(null);

    try {
      const stats = await webhooksClient.getStatistics();
      setStatistics(stats);
    } catch (err) {
      setStatsError(err instanceof Error ? err.message : 'Failed to load statistics');
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatistics();
  }, [fetchStatistics, refreshTrigger]);

  const handleCreateWebhook = useCallback(() => {
    setCreateDialogOpen(true);
  }, []);

  const handleCreateSuccess = useCallback(() => {
    setCreateDialogOpen(false);
    setRefreshTrigger((prev) => prev + 1);
    fetchStatistics();
  }, [fetchStatistics]);

  const handleDialogClose = useCallback(() => {
    setCreateDialogOpen(false);
  }, []);

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Webhooks
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Configure webhooks to receive real-time event notifications
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateWebhook}
          size="large"
        >
          Create Webhook
        </Button>
      </Stack>

      {/* Statistics Cards */}
      {!statsLoading && statistics && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
                border: '1px solid',
                borderColor: 'primary.main',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    <WebhookIcon />
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {statistics.total_subscriptions}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Webhooks
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)',
                border: '1px solid',
                borderColor: 'success.main',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    <CheckCircleIcon />
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {statistics.active_subscriptions}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Active Webhooks
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)',
                border: '1px solid',
                borderColor: 'success.main',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    <TrendingUpIcon />
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {statistics.successful_deliveries_today}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Successful Today
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%)',
                border: '1px solid',
                borderColor: 'error.main',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    <ErrorIcon />
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {statistics.failed_deliveries_today}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Failed Today
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Getting Started Section */}
      <Paper sx={{ p: 3, mb: 4, border: '1px solid', borderColor: 'divider' }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Getting Started with Webhooks
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Webhooks allow you to receive real-time notifications when events occur in AgentHR.
          Configure an endpoint URL and select which events you want to subscribe to.
        </Typography>

        <Box
          sx={{
            bgcolor: 'background.paper',
            p: 2,
            borderRadius: 1,
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            mb: 2,
            border: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Typography variant="body2" component="pre" sx={{ m: 0 }}>
{`POST {your_webhook_url}
Content-Type: application/json
X-AgentHR-Signature: sha256=hmac_signature

{
  "event": "candidate.created",
  "data": { ... },
  "timestamp": "2024-01-01T00:00:00Z"
}`}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip label="Real-time Events" size="small" variant="outlined" />
          <Chip label="Retry Logic" size="small" variant="outlined" />
          <Chip label="HMAC Signatures" size="small" variant="outlined" />
        </Box>
      </Paper>

      {/* Webhooks List */}
      <WebhookList refreshTrigger={refreshTrigger} onStatisticsUpdate={fetchStatistics} />

      {/* Create Webhook Dialog */}
      <WebhookForm
        open={createDialogOpen}
        onClose={handleDialogClose}
        onSuccess={handleCreateSuccess}
      />
    </Container>
  );
};

export default Webhooks;
