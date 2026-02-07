import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Button,
  Alert,
  AlertTitle,
  Stack,
  Grid,
  Chip,
  Switch,
  FormControlLabel,
  TextField,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Compare as CompareIcon,
  AttachMoney as MoneyIcon,
  TrendingUp as TrendingUpIcon,
  LocationOn as LocationIcon,
  Work as WorkIcon,
  Business as BusinessIcon,
  Star as StarIcon,
} from '@mui/icons-material';
import { salaryBenchmarking } from '@/api/salaryBenchmarking';

/**
 * Individual offer interface
 */
interface Offer {
  salary: number;
  location: string;
  currency: string;
  bonus?: number;
  equity?: number;
  job_title?: string;
  company?: string;
}

/**
 * Compared offer with adjustments from backend
 */
interface ComparedOffer {
  salary: number;
  location: string;
  currency: string;
  bonus: number;
  equity: number;
  total_compensation: number;
  adjusted_total: number;
  col_index: number | null;
  job_title?: string;
  company?: string;
}

/**
 * Analysis metadata from backend
 */
interface ComparisonAnalysis {
  total_offers: number;
  cost_of_living_applied: boolean;
  best_location: string | null;
  salary_range: {
    min: number;
    max: number;
  } | null;
}

/**
 * Offer comparison response from backend
 */
interface OfferComparisonResponse {
  resume_id: string;
  offers: ComparedOffer[];
  recommendation: string;
  analysis: ComparisonAnalysis;
  current_salary: number | null;
}

/**
 * OfferComparisonTool Component Props
 */
interface OfferComparisonToolProps {
  /** Resume ID for context (to fetch current salary) */
  resumeId?: string;
  /** API endpoint URL for offer comparison */
  apiUrl?: string;
  /** Initial offers to compare */
  initialOffers?: Offer[];
}

/**
 * OfferComparisonTool Component
 *
 * Interactive tool for comparing multiple job offers with:
 * - Add/remove offers dynamically
 * - Toggle cost-of-living adjustments
 * - Visual comparison of total compensation
 * - Side-by-side offer details
 * - Recommendation based on analysis
 * - Current salary comparison (if resume provided)
 *
 * @example
 * ```tsx
 * <OfferComparisonTool />
 * ```
 *
 * @example
 * ```tsx
 * <OfferComparisonTool
 *   resumeId="abc-123-def"
 *   initialOffers={[
 *     { salary: 100000, location: "New York, NY", currency: "USD" },
 *     { salary: 95000, location: "Austin, TX", currency: "USD" },
 *   ]}
 * />
 * ```
 */
const OfferComparisonTool: React.FC<OfferComparisonToolProps> = ({
  resumeId,
  initialOffers = [],
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [comparisonData, setComparisonData] = useState<OfferComparisonResponse | null>(null);
  const [offers, setOffers] = useState<Offer[]>(
    initialOffers.length > 0
      ? initialOffers
      : [
          { salary: 0, location: '', currency: 'USD', bonus: 0, equity: 0 },
          { salary: 0, location: '', currency: 'USD', bonus: 0, equity: 0 },
        ]
  );
  const [applyCostOfLiving, setApplyCostOfLiving] = useState(true);

  /**
   * Update offer field
   */
  const updateOffer = useCallback((index: number, field: keyof Offer, value: any) => {
    setOffers((prev) =>
      prev.map((offer, i) =>
        i === index ? { ...offer, [field]: field === 'salary' || field === 'bonus' || field === 'equity' ? Number(value) || 0 : value } : offer
      )
    );
  }, []);

  /**
   * Add new offer
   */
  const addOffer = useCallback(() => {
    if (offers.length >= 5) {
      setError('Maximum 5 offers can be compared at once');
      return;
    }
    setOffers((prev) => [...prev, { salary: 0, location: '', currency: 'USD', bonus: 0, equity: 0 }]);
    setError(null);
  }, [offers.length]);

  /**
   * Remove offer
   */
  const removeOffer = useCallback((index: number) => {
    if (offers.length <= 1) {
      setError('At least one offer is required');
      return;
    }
    setOffers((prev) => prev.filter((_, i) => i !== index));
    setError(null);
  }, [offers.length]);

  /**
   * Compare offers
   */
  const compareOffers = async () => {
    // Validate offers
    const validOffers = offers.filter((offer) => offer.salary > 0 && offer.location.length > 0);

    if (validOffers.length < 2) {
      setError('At least 2 valid offers are required for comparison (salary > 0 and location specified)');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await salaryBenchmarking.compareOffers({
        resume_id: resumeId || '00000000-0000-0000-0000-000000000000',
        offers: validOffers,
        apply_cost_of_living: applyCostOfLiving,
      });

      setComparisonData(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to compare offers';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Format currency amount
   */
  const formatCurrency = useCallback((amount: number, currency: string = 'USD'): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  }, []);

  /**
   * Render loading state
   */
  if (loading && !comparisonData) {
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
          Comparing offers...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Analyzing {offers.length} offers with cost-of-living adjustments
        </Typography>
      </Box>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CompareIcon fontSize="large" color="primary" />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Offer Comparison Tool
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Compare job offers with cost-of-living adjustments
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={applyCostOfLiving}
                  onChange={(e) => setApplyCostOfLiving(e.target.checked)}
                  color="primary"
                />
              }
              label="Cost-of-Living"
            />
            <Button
              variant="contained"
              startIcon={<CompareIcon />}
              onClick={compareOffers}
              disabled={loading || offers.some((o) => o.salary <= 0 || !o.location)}
            >
              Compare Offers
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Input Section - Add/Edit Offers */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            Enter Offer Details
          </Typography>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={addOffer}
            disabled={offers.length >= 5}
            size="small"
          >
            Add Offer
          </Button>
        </Box>

        <Stack spacing={2}>
          {offers.map((offer, index) => (
            <Card key={index} variant="outlined">
              <CardContent>
                <Grid container spacing={2} alignItems="center">
                  {/* Offer Header */}
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={`Offer ${index + 1}`}
                          color="primary"
                          size="small"
                          sx={{ fontWeight: 600 }}
                        />
                        {comparisonData && index === 0 && (
                          <Chip
                            icon={<StarIcon />}
                            label="Best"
                            color="success"
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        )}
                      </Box>
                      <IconButton
                        onClick={() => removeOffer(index)}
                        disabled={offers.length <= 1}
                        size="small"
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  </Grid>

                  {/* Company */}
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      label="Company"
                      size="small"
                      value={offer.company || ''}
                      onChange={(e) => updateOffer(index, 'company', e.target.value)}
                      placeholder="e.g., Tech Corp"
                      InputProps={{
                        startAdornment: <BusinessIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />,
                      }}
                    />
                  </Grid>

                  {/* Job Title */}
                  <Grid item xs={12} sm={6} md={3}>
                    <TextField
                      fullWidth
                      label="Job Title"
                      size="small"
                      value={offer.job_title || ''}
                      onChange={(e) => updateOffer(index, 'job_title', e.target.value)}
                      placeholder="e.g., Senior Developer"
                      InputProps={{
                        startAdornment: <WorkIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />,
                      }}
                    />
                  </Grid>

                  {/* Salary */}
                  <Grid item xs={12} sm={6} md={2}>
                    <TextField
                      fullWidth
                      label="Base Salary"
                      type="number"
                      size="small"
                      value={offer.salary || ''}
                      onChange={(e) => updateOffer(index, 'salary', e.target.value)}
                      placeholder="100000"
                      InputProps={{
                        startAdornment: <MoneyIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />,
                      }}
                      required
                    />
                  </Grid>

                  {/* Location */}
                  <Grid item xs={12} sm={6} md={2}>
                    <TextField
                      fullWidth
                      label="Location"
                      size="small"
                      value={offer.location}
                      onChange={(e) => updateOffer(index, 'location', e.target.value)}
                      placeholder="e.g., New York, NY"
                      InputProps={{
                        startAdornment: <LocationIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />,
                      }}
                      required
                    />
                  </Grid>

                  {/* Bonus */}
                  <Grid item xs={6} sm={3} md={1}>
                    <TextField
                      fullWidth
                      label="Bonus"
                      type="number"
                      size="small"
                      value={offer.bonus || ''}
                      onChange={(e) => updateOffer(index, 'bonus', e.target.value)}
                      placeholder="0"
                    />
                  </Grid>

                  {/* Equity */}
                  <Grid item xs={6} sm={3} md={1}>
                    <TextField
                      fullWidth
                      label="Equity"
                      type="number"
                      size="small"
                      value={offer.equity || ''}
                      onChange={(e) => updateOffer(index, 'equity', e.target.value)}
                      placeholder="0"
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          ))}
        </Stack>

        {/* Input Hints */}
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            At least 2 offers required for comparison. All fields marked with * are required.
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {offers.length}/5 offers
          </Typography>
        </Box>
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          <AlertTitle>Comparison Error</AlertTitle>
          {error}
        </Alert>
      )}

      {/* Comparison Results */}
      {comparisonData && (
        <>
          {/* Recommendation Banner */}
          <Paper
            elevation={2}
            sx={{
              p: 3,
              bgcolor: 'success.main',
              color: 'success.contrastText',
              background: (theme) =>
                `linear-gradient(135deg, ${theme.palette.success.main} 0%, ${theme.palette.success.dark} 100%)`,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <StarIcon sx={{ fontSize: 40, opacity: 0.9 }} />
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="h6" fontWeight={700} gutterBottom>
                  Recommendation
                </Typography>
                <Typography variant="body1">{comparisonData.recommendation}</Typography>
              </Box>
              <IconButton
                onClick={compareOffers}
                disabled={loading}
                sx={{ color: 'inherit' }}
                size="small"
              >
                <RefreshIcon />
              </IconButton>
            </Box>
          </Paper>

          {/* Comparison Summary Cards */}
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center', py: 1 }}>
                  <Typography variant="h4" color="primary.main" fontWeight={700}>
                    {comparisonData.analysis.total_offers}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Offers Compared
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center', py: 1 }}>
                  <Typography variant="h4" color="success.main" fontWeight={700}>
                    {formatCurrency(
                      Math.max(...comparisonData.offers.map((o) => o.adjusted_total)),
                      comparisonData.offers[0]?.currency || 'USD'
                    )}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Best Adjusted Total
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center', py: 1 }}>
                  <Typography variant="h4" fontWeight={700}>
                    {comparisonData.analysis.cost_of_living_applied ? 'Yes' : 'No'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    COL Applied
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center', py: 1 }}>
                  <Typography variant="h4" color="info.main" fontWeight={700}>
                    {comparisonData.analysis.salary_range
                      ? formatCurrency(
                          comparisonData.analysis.salary_range.max - comparisonData.analysis.salary_range.min,
                          comparisonData.offers[0]?.currency || 'USD'
                        )
                      : 'N/A'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Total Range
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Current Salary Comparison */}
          {comparisonData.current_salary && (
            <Paper elevation={1} sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <TrendingUpIcon color="info" />
                <Typography variant="h6" fontWeight={600}>
                  Current Salary Comparison
                </Typography>
              </Box>
              <Alert severity="info">
                <Typography variant="body2">
                  Current salary: <strong>{formatCurrency(comparisonData.current_salary, 'USD')}</strong>
                </Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Best offer increase:{' '}
                  <strong>
                    {formatCurrency(
                      Math.max(...comparisonData.offers.map((o) => o.adjusted_total)) - comparisonData.current_salary,
                      comparisonData.offers[0]?.currency || 'USD'
                    )}
                  </strong>
                  {' ('}
                    {(
                      ((Math.max(...comparisonData.offers.map((o) => o.adjusted_total)) - comparisonData.current_salary) /
                        comparisonData.current_salary) *
                      100
                    ).toFixed(1)}
                    %)
                  </Typography>
              </Alert>
            </Paper>
          )}

          {/* Detailed Comparison Table */}
          <Paper elevation={1} sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Detailed Comparison
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Offers ranked by adjusted total compensation (cost-of-living normalized)
            </Typography>

            <TableContainer sx={{ maxHeight: 500, overflow: 'auto' }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Rank</TableCell>
                    <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Company</TableCell>
                    <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Location</TableCell>
                    <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Base Salary</TableCell>
                    <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Bonus</TableCell>
                    <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Equity</TableCell>
                    <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Total Comp</TableCell>
                    <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>COL Index</TableCell>
                    <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Adjusted Total</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {comparisonData.offers.map((offer, index) => (
                    <TableRow
                      key={index}
                      sx={{
                        '&:nth-of-type(odd)': { bgcolor: 'action.hover' },
                        bgcolor: index === 0 ? 'success.50' : 'inherit',
                      }}
                    >
                      <TableCell>
                        <Chip
                          label={`#${index + 1}`}
                          color={index === 0 ? 'success' : 'default'}
                          size="small"
                          sx={{ fontWeight: 700 }}
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          {offer.company || 'N/A'}
                          {index === 0 && <StarIcon fontSize="small" color="success" />}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Tooltip title={offer.location}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <LocationIcon fontSize="small" color="action" />
                            <span>{offer.location}</span>
                          </Box>
                        </Tooltip>
                      </TableCell>
                      <TableCell>{formatCurrency(offer.salary, offer.currency)}</TableCell>
                      <TableCell>
                        {offer.bonus > 0 ? formatCurrency(offer.bonus, offer.currency) : '—'}
                      </TableCell>
                      <TableCell>
                        {offer.equity > 0 ? formatCurrency(offer.equity, offer.currency) : '—'}
                      </TableCell>
                      <TableCell>
                        <Typography fontWeight={600}>
                          {formatCurrency(offer.total_compensation, offer.currency)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {offer.col_index ? (
                          <Chip
                            label={`${offer.col_index.toFixed(1)}`}
                            size="small"
                            variant="outlined"
                            color={offer.col_index > 100 ? 'warning' : 'info'}
                          />
                        ) : (
                          '—'
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography
                          fontWeight={700}
                          color={index === 0 ? 'success.main' : 'text.primary'}
                          variant="body2"
                        >
                          {formatCurrency(offer.adjusted_total, offer.currency)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </>
      )}
    </Stack>
  );
};

export default OfferComparisonTool;
