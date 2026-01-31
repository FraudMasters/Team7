import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Alert,
  AlertTitle,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
  MenuItem,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

/**
 * Public taxonomy response from backend
 */
interface PublicTaxonomy {
  id: string;
  industry: string;
  skill_name: string;
  variants: string[];
  context?: string;
  extra_metadata?: Record<string, unknown>;
  is_active: boolean;
  organization_id?: string;
  source_organization?: string;
  created_at: string;
  updated_at: string;
}

/**
 * List response from backend
 */
interface PublicTaxonomyListResponse {
  industry: string | null;
  taxonomies: PublicTaxonomy[];
  total_count: number;
}

/**
 * Public taxonomy browser component props
 */
interface PublicTaxonomyBrowserProps {
  /** Organization ID for forking taxonomies */
  organizationId?: string;
  /** API endpoint URL for taxonomy sharing */
  apiUrl?: string;
}

/**
 * PublicTaxonomyBrowser Component
 *
 * Provides an interface for browsing and forking public taxonomies
 * shared by other organizations. Features include:
 * - List all public taxonomies with optional industry filter
 * - Industry selector dropdown
 * - Fork public taxonomies to your organization
 * - Real-time updates
 *
 * @example
 * ```tsx
 * <PublicTaxonomyBrowser organizationId="org123" />
 * ```
 */
const PublicTaxonomyBrowser: React.FC<PublicTaxonomyBrowserProps> = ({
  organizationId = 'default',
  apiUrl = 'http://localhost:8000/api/taxonomy-sharing',
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [taxonomies, setTaxonomies] = useState<PublicTaxonomy[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState<string>('all');
  const [forking, setForking] = useState<string | null>(null);
  const [forkDialogOpen, setForkDialogOpen] = useState(false);
  const [taxonomyToFork, setTaxonomyToFork] = useState<PublicTaxonomy | null>(null);

  // Available industries
  const industries = [
    'all',
    'tech',
    'healthcare',
    'finance',
    'marketing',
    'manufacturing',
    'sales',
    'design',
  ];

  /**
   * Fetch public taxonomies from backend
   */
  const fetchTaxonomies = async () => {
    setLoading(true);
    setError(null);

    try {
      const url =
        selectedIndustry === 'all'
          ? `${apiUrl}/public`
          : `${apiUrl}/public?industry=${selectedIndustry}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch public taxonomies: ${response.statusText}`);
      }

      const result: PublicTaxonomyListResponse = await response.json();
      setTaxonomies(result.taxonomies || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load public taxonomies';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTaxonomies();
  }, [selectedIndustry]);

  /**
   * Handle industry change
   */
  const handleIndustryChange = (event: SelectChangeEvent<string>) => {
    setSelectedIndustry(event.target.value as string);
  };

  /**
   * Open fork confirmation dialog
   */
  const handleForkClick = (taxonomy: PublicTaxonomy) => {
    setTaxonomyToFork(taxonomy);
    setForkDialogOpen(true);
  };

  /**
   * Fork taxonomy to organization
   */
  const handleForkConfirm = async () => {
    if (!taxonomyToFork) return;

    setForking(taxonomyToFork.id);
    try {
      const response = await fetch(`${apiUrl}/${taxonomyToFork.id}/fork`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          organization_id: organizationId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to fork taxonomy: ${response.statusText}`);
      }

      // Show success message
      setForkDialogOpen(false);
      setTaxonomyToFork(null);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to fork taxonomy';
      setError(errorMessage);
    } finally {
      setForking(null);
    }
  };

  /**
   * Get context color for display
   */
  const getContextColor = (context?: string) => {
    switch (context) {
      case 'web_framework':
        return 'primary' as const;
      case 'language':
        return 'success' as const;
      case 'database':
        return 'warning' as const;
      case 'tool':
        return 'info' as const;
      default:
        return 'default' as const;
    }
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 8,
        }}
      >
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6" color="text.secondary">
          Loading public taxonomies...
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" onClick={fetchTaxonomies} startIcon={<RefreshIcon />}>
            Try Again
          </Button>
        }
      >
        <AlertTitle>Error</AlertTitle>
        {error}
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            Browse Public Taxonomies
          </Typography>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchTaxonomies} size="small">
            Refresh
          </Button>
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Browse and fork skill taxonomies shared by the community
        </Typography>

        {/* Industry Selector */}
        <FormControl fullWidth size="small">
          <InputLabel>Filter by Industry</InputLabel>
          <Select
            value={selectedIndustry}
            label="Filter by Industry"
            onChange={handleIndustryChange}
          >
            {industries.map((industry) => (
              <MenuItem key={industry} value={industry}>
                {industry === 'all' ? 'All Industries' : industry.charAt(0).toUpperCase() + industry.slice(1)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Summary Statistics */}
        <Box sx={{ mt: 3 }}>
          <Typography variant="body2" color="text.secondary">
            Showing {taxonomies.length} public {taxonomies.length === 1 ? 'taxonomy' : 'taxonomies'}
            {selectedIndustry !== 'all' && ` in ${selectedIndustry}`}
          </Typography>
        </Box>
      </Paper>

      {/* Taxonomies List */}
      {taxonomies.length === 0 ? (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No public taxonomies found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {selectedIndustry === 'all'
              ? 'No taxonomies have been shared publicly yet.'
              : `No taxonomies have been shared publicly for ${selectedIndustry} yet.`}
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          {taxonomies.map((taxonomy) => (
            <Grid item xs={12} md={6} key={taxonomy.id}>
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" fontWeight={600}>
                      {taxonomy.skill_name}
                    </Typography>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={
                        forking === taxonomy.id ? <CircularProgress size={14} /> : <DownloadIcon />
                      }
                      onClick={() => handleForkClick(taxonomy)}
                      disabled={forking !== null}
                    >
                      Fork
                    </Button>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Chip
                      label={taxonomy.industry}
                      size="small"
                      color="primary"
                      variant="outlined"
                      sx={{ mr: 1 }}
                    />
                    {taxonomy.context && (
                      <Chip
                        label={taxonomy.context}
                        size="small"
                        color={getContextColor(taxonomy.context)}
                        variant="outlined"
                        sx={{ mr: 1 }}
                      />
                    )}
                    <Chip
                      label={taxonomy.is_active ? 'Active' : 'Inactive'}
                      size="small"
                      color={taxonomy.is_active ? 'success' : 'default'}
                      variant="filled"
                    />
                  </Box>

                  <Divider sx={{ my: 1 }} />

                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                      Variants
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {taxonomy.variants.map((variant, index) => (
                        <Chip
                          key={index}
                          label={variant}
                          size="small"
                          variant="filled"
                          color="primary"
                        />
                      ))}
                    </Box>
                  </Box>

                  {taxonomy.source_organization && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="caption" color="text.secondary">
                        Source: {taxonomy.source_organization}
                      </Typography>
                    </Box>
                  )}

                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
                    Created: {new Date(taxonomy.created_at).toLocaleDateString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Fork Confirmation Dialog */}
      <Dialog open={forkDialogOpen} onClose={() => !forking && setForkDialogOpen(false)}>
        <DialogTitle>Fork Taxonomy</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            Fork "{taxonomyToFork?.skill_name}" to your organization?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This will create a copy of this taxonomy in your organization's collection.
            You can modify it after forking.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setForkDialogOpen(false)} disabled={forking !== null}>
            Cancel
          </Button>
          <Button
            onClick={handleForkConfirm}
            variant="contained"
            disabled={forking !== null}
            startIcon={forking ? <CircularProgress size={16} /> : <DownloadIcon />}
          >
            {forking ? 'Forking...' : 'Fork'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default PublicTaxonomyBrowser;
