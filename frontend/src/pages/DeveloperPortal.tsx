import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Card,
  CardContent,
  Stack,
  Box,
  Typography,
  useMediaQuery,
  useTheme,
  Grid,
} from '@mui/material';
import {
  VpnKey as ApiKeysIcon,
  Webhook as WebhooksIcon,
  Extension as PluginsIcon,
  AccountTree as WorkflowsIcon,
  Code as CodeIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';

interface FeatureCard {
  title: string;
  description: string;
  icon: React.ReactElement;
  gradient: string;
  path: string;
  actionText: string;
}

const features: FeatureCard[] = [
  {
    title: 'API Keys',
    description: 'Manage your API keys for secure access to the AgentHR API. Create, rotate, and revoke keys as needed.',
    icon: <ApiKeysIcon sx={{ fontSize: 36 }} />,
    gradient: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    path: '/developer/api-keys',
    actionText: 'Manage Keys',
  },
  {
    title: 'Webhooks',
    description: 'Configure webhooks to receive real-time notifications about events in your AgentHR account.',
    icon: <WebhooksIcon sx={{ fontSize: 36 }} />,
    gradient: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
    path: '/developer/webhooks',
    actionText: 'Configure',
  },
  {
    title: 'Plugins',
    description: 'Extend AgentHR functionality with custom plugins. Build, test, and deploy your own integrations.',
    icon: <PluginsIcon sx={{ fontSize: 36 }} />,
    gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    path: '/developer/plugins',
    actionText: 'Explore Plugins',
  },
  {
    title: 'Workflows',
    description: 'Create and manage custom workflows to automate your recruitment processes with AI-powered agents.',
    icon: <WorkflowsIcon sx={{ fontSize: 36 }} />,
    gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    path: '/developer/workflows',
    actionText: 'Build Workflows',
  },
];

const DeveloperPortal: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleCardClick = (path: string) => {
    navigate(path);
  };

  return (
    <Container maxWidth="xl">
      {/* Header */}
      <Box sx={{ mb: 6 }}>
        <Typography
          variant="h3"
          fontWeight={700}
          gutterBottom
          sx={{
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Developer Portal
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Build, integrate, and extend AgentHR with powerful APIs and developer tools
        </Typography>
      </Box>

      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mb: 6 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
              border: '1px solid',
              borderColor: 'divider',
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
                  <CodeIcon />
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight={700}>
                    3
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active API Keys
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
              background: 'linear-gradient(135deg, rgba(14, 165, 233, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%)',
              border: '1px solid',
              borderColor: 'divider',
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                  }}
                >
                  <WebhooksIcon />
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight={700}>
                    5
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
              borderColor: 'divider',
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
                  <PluginsIcon />
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight={700}>
                    2
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Installed Plugins
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
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%)',
              border: '1px solid',
              borderColor: 'divider',
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                  }}
                >
                  <WorkflowsIcon />
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight={700}>
                    4
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Workflows
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Feature Cards */}
      <Typography variant="h5" fontWeight={600} gutterBottom>
        Developer Tools
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Get started with our developer tools to integrate and extend AgentHR
      </Typography>

      <Grid container spacing={3}>
        {features.map((feature, index) => (
          <Grid item xs={12} md={6} key={feature.title}>
            <Card
              component="article"
              onClick={() => handleCardClick(feature.path)}
              tabIndex={0}
              role="button"
              aria-label={`Navigate to ${feature.title}: ${feature.description}`}
              sx={{
                height: '100%',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                border: '1px solid',
                borderColor: 'divider',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
                '&:focus-visible': {
                  outline: '3px solid',
                  outlineColor: 'primary.main',
                  outlineOffset: '4px',
                },
              }}
              onKeyPress={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleCardClick(feature.path);
                }
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box
                  sx={{
                    width: 56,
                    height: 56,
                    borderRadius: 2,
                    background: feature.gradient,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mb: 2,
                    color: 'white',
                  }}
                  aria-hidden="true"
                >
                  {feature.icon}
                </Box>
                <Typography variant="h5" fontWeight={600} gutterBottom>
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3, minHeight: 48 }}>
                  {feature.description}
                </Typography>
                <Box
                  component="span"
                  sx={{
                    py: 1,
                    px: 2,
                    borderRadius: 1.5,
                    background: feature.gradient,
                    color: 'white',
                    textAlign: 'center',
                    fontWeight: 600,
                    fontSize: '0.875rem',
                    display: 'inline-block',
                  }}
                >
                  {feature.actionText}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Getting Started Section */}
      <Box sx={{ mt: 8, p: 4, borderRadius: 3, bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 3 }}>
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: 2,
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              flexShrink: 0,
            }}
          >
            <SecurityIcon />
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h5" fontWeight={600} gutterBottom>
              Getting Started
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              New to the AgentHR Developer Portal? Follow our quick start guide to set up your first API integration
              and start building powerful recruitment workflows.
            </Typography>
            <Box
              component="span"
              sx={{
                py: 1,
                px: 2,
                borderRadius: 1.5,
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                color: 'white',
                fontWeight: 600,
                fontSize: '0.875rem',
                display: 'inline-block',
                cursor: 'pointer',
              }}
            >
              View Documentation
            </Box>
          </Box>
        </Box>
      </Box>
    </Container>
  );
};

export default DeveloperPortal;
