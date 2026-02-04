/**
 * IP Whitelist Configuration Page
 *
 * Provides IP whitelist management functionality including:
 * - List all IP whitelist entries for the organization
 * - Add new IP ranges (CIDR notation or IP range)
 * - Edit existing whitelist entries
 * - Delete whitelist entries
 * - Toggle active/inactive status
 */
import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Container,
  Typography,
  Paper,
  Alert,
  Stack,
} from '@mui/material';
import {
  Security as SecurityIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import IPWhitelistManager from '@/components/IPWhitelistManager';

const IPWhitelistPage: React.FC = () => {
  const { t } = useTranslation();

  // TODO: Get organization ID from auth context
  const organizationId = 'org-123';

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
        <SecurityIcon fontSize="large" color="primary" />
        <Typography variant="h4" fontWeight={600}>
          IP Whitelist Configuration
        </Typography>
      </Box>

      {/* Info Alert */}
      <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 3 }}>
        <Typography variant="body2">
          Configure IP whitelist rules to restrict access to your organization. Only users from
          whitelisted IP addresses will be able to access the system when IP whitelist enforcement is enabled.
        </Typography>
      </Alert>

      {/* IP Whitelist Manager */}
      <IPWhitelistManager organizationId={organizationId} />
    </Container>
  );
};

export default IPWhitelistPage;
