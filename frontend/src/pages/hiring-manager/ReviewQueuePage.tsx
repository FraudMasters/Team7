import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Container,
  Box,
  Typography,
  TextField,
  Paper,
  Card,
  CardContent,
  Chip,
  Stack,
  Grid,
  IconButton,
  Tooltip,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Avatar,
  alpha,
  useTheme,
  Divider,
  Button,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  Star as StarIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Visibility as VisibilityIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingUpIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useHiringManagerReviewQueue, ReviewQueueFilters, ReviewQueueCandidate } from '../../hooks/useHiringManagerData';
import LoadingSpinner from '../../components/LoadingSpinner';

/**
 * Get color for priority chip
 */
function getPriorityColor(priority: string | null): 'error' | 'warning' | 'info' | 'default' {
  switch (priority) {
    case 'urgent':
      return 'error';
    case 'high':
      return 'warning';
    case 'normal':
      return 'info';
    default:
      return 'default';
  }
}

/**
 * Get color for consensus chip
 */
function getConsensusColor(consensus: string | null): 'success' | 'error' | 'warning' | 'default' {
  switch (consensus) {
    case 'approve':
      return 'success';
    case 'reject':
      return 'error';
    case 'mixed':
      return 'warning';
    default:
      return 'default';
  }
}

/**
 * Generate avatar color from candidate name
 */
function getAvatarColor(name: string): string {
  const colors = [
    '#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5',
    '#2196f3', '#00bcd4', '#009688', '#4caf50', '#8bc34a',
    '#cddc39', '#ffeb3b', '#ffc107', '#ff9800', '#ff5722'
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

/**
 * Get candidate initials for avatar
 */
function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
}

/**
 * Review Queue Candidate Card Component
 */
interface CandidateCardProps {
  candidate: ReviewQueueCandidate;
  onViewDetails: (id: string) => void;
}

function CandidateCard({ candidate, onViewDetails }: CandidateCardProps) {
  const theme = useTheme();
  const { t } = useTranslation();

  const candidateName = candidate.candidate_name || candidate.filename || 'Unknown Candidate';
  const avatarColor = getAvatarColor(candidateName);

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'transform 0.2s, box-shadow 0.2s',
        border: candidate.priority === 'urgent' ? `2px solid ${theme.palette.error.main}` : undefined,
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: theme.shadows[4],
        },
      }}
    >
      <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 2.5 }}>
        {/* Header Row */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
          {/* Avatar */}
          <Avatar
            sx={{
              width: 48,
              height: 48,
              bgcolor: avatarColor,
              fontSize: '1rem',
              fontWeight: 600,
            }}
          >
            {getInitials(candidateName)}
          </Avatar>

          {/* Candidate Info */}
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography
              variant="subtitle1"
              fontWeight={600}
              sx={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {candidateName}
            </Typography>
            {candidate.vacancy_title && (
              <Typography variant="body2" color="text.secondary" noWrap>
                {candidate.vacancy_title}
              </Typography>
            )}
          </Box>

          {/* Priority Badge */}
          {candidate.priority && (
            <Chip
              label={candidate.priority.toUpperCase()}
              size="small"
              color={getPriorityColor(candidate.priority)}
              sx={{ height: 24, fontSize: '0.7rem', fontWeight: 600 }}
            />
          )}
        </Box>

        {/* Stats Row */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
          {/* Stage */}
          <Chip
            label={candidate.stage_name || candidate.current_stage}
            size="small"
            variant="outlined"
            sx={{ height: 24, fontSize: '0.75rem' }}
          />

          {/* Days in Stage */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <ScheduleIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              {candidate.days_in_stage}d
            </Typography>
          </Box>

          {/* Match Score */}
          {candidate.match_score !== null && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <TrendingUpIcon sx={{ fontSize: 16, color: 'success.main' }} />
              <Typography variant="caption" fontWeight={600} color="success.main">
                {Math.round(candidate.match_score * 100)}%
              </Typography>
            </Box>
          )}
        </Box>

        {/* Team Consensus */}
        {candidate.team_consensus && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
              {t('reviewQueue.teamConsensus', 'Team Consensus')}
            </Typography>
            <Chip
              icon={candidate.team_consensus === 'approve' ? <CheckCircleIcon /> :
                    candidate.team_consensus === 'reject' ? <CancelIcon /> : undefined}
              label={candidate.team_consensus.charAt(0).toUpperCase() + candidate.team_consensus.slice(1)}
              size="small"
              color={getConsensusColor(candidate.team_consensus)}
              variant="outlined"
              sx={{ height: 24 }}
            />
          </Box>
        )}

        {/* Recruiter Feedback Preview */}
        {candidate.recruiter_feedback && candidate.recruiter_feedback.length > 0 && (
          <Box sx={{ mb: 2, flexGrow: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
              {t('reviewQueue.recruiterFeedback', 'Recruiter Feedback')} ({candidate.recruiter_feedback.length})
            </Typography>
            {candidate.recruiter_feedback.slice(0, 2).map((feedback, index) => (
              <Box
                key={index}
                sx={{
                  p: 1,
                  bgcolor: alpha(theme.palette.primary.main, 0.05),
                  borderRadius: 1,
                  mb: 0.5,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="caption" fontWeight={600}>
                    {feedback.recruiter_name}
                  </Typography>
                  {feedback.rating && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
                      <StarIcon sx={{ fontSize: 12, color: 'warning.main' }} />
                      <Typography variant="caption">{feedback.rating}</Typography>
                    </Box>
                  )}
                </Box>
                {feedback.notes && (
                  <Typography variant="caption" color="text.secondary" sx={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    display: 'block'
                  }}>
                    {feedback.notes}
                  </Typography>
                )}
              </Box>
            ))}
            {candidate.recruiter_feedback.length > 2 && (
              <Typography variant="caption" color="text.secondary">
                +{candidate.recruiter_feedback.length - 2} more
              </Typography>
            )}
          </Box>
        )}

        {/* Tags */}
        {candidate.tags && candidate.tags.length > 0 && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
            {candidate.tags.slice(0, 3).map((tag) => (
              <Chip
                key={tag}
                label={tag}
                size="small"
                sx={{
                  height: 20,
                  fontSize: '0.65rem',
                  bgcolor: alpha(theme.palette.grey[500], 0.1),
                }}
              />
            ))}
            {candidate.tags.length > 3 && (
              <Chip
                label={`+${candidate.tags.length - 3}`}
                size="small"
                sx={{ height: 20, fontSize: '0.65rem' }}
              />
            )}
          </Box>
        )}

        {/* Action Button */}
        <Button
          variant="contained"
          fullWidth
          startIcon={<VisibilityIcon />}
          onClick={() => onViewDetails(candidate.id)}
          sx={{
            mt: 'auto',
            minHeight: 44, // Touch target accessibility
          }}
        >
          {t('reviewQueue.viewDetails', 'View Details')}
        </Button>
      </CardContent>
    </Card>
  );
}

/**
 * Hiring Manager Review Queue Page
 *
 * Displays candidates pending manager review with filtering and search capabilities.
 * Mobile-optimized with touch-friendly targets.
 */
export function ReviewQueuePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const theme = useTheme();

  // State for filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedVacancy, setSelectedVacancy] = useState<string>('');
  const [selectedPriority, setSelectedPriority] = useState<string>('');
  const [showFilters, setShowFilters] = useState(false);

  // Build filters object
  const filters: ReviewQueueFilters | undefined = useMemo(() => {
    if (!searchTerm && !selectedVacancy && !selectedPriority) {
      return undefined;
    }
    return {
      search: searchTerm || undefined,
      vacancy_id: selectedVacancy || undefined,
      priority: selectedPriority as ReviewQueueFilters['priority'] || undefined,
    };
  }, [searchTerm, selectedVacancy, selectedPriority]);

  // Fetch review queue
  const { data: reviewQueueData, isLoading, isError, refetch } = useHiringManagerReviewQueue(filters);

  // Extract data with defaults
  const candidates = reviewQueueData?.candidates || [];
  const totalCandidates = reviewQueueData?.total_candidates || 0;
  const pagination = reviewQueueData?.pagination;

  // Get unique vacancies for filter dropdown
  const uniqueVacancies = useMemo(() => {
    const vacancies = new Map<string, string>();
    candidates.forEach(c => {
      if (c.vacancy_id && c.vacancy_title) {
        vacancies.set(c.vacancy_id, c.vacancy_title);
      }
    });
    return Array.from(vacancies.entries());
  }, [candidates]);

  // Handle viewing candidate details
  const handleViewDetails = (candidateId: string) => {
    navigate(`/hiring-manager/candidates/${candidateId}`);
  };

  // Clear all filters
  const handleClearFilters = () => {
    setSearchTerm('');
    setSelectedVacancy('');
    setSelectedPriority('');
  };

  // Check if any filters are active
  const hasActiveFilters = searchTerm || selectedVacancy || selectedPriority;

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Page Header */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h4" fontWeight={700}>
              {t('reviewQueue.title', 'Review Queue')}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {t('reviewQueue.subtitle', 'Candidates awaiting your review and decision')}
            </Typography>
          </Box>
          <Tooltip title={t('common.refresh', 'Refresh')}>
            <IconButton onClick={() => refetch()} size="large">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Search and Filter Row */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack spacing={2}>
          {/* Main Search Row */}
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            {/* Search Input */}
            <TextField
              placeholder={t('reviewQueue.searchPlaceholder', 'Search candidates...')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon color="action" />
                  </InputAdornment>
                ),
              }}
              sx={{ minWidth: 280, flexGrow: { xs: 1, md: 0 } }}
              size="small"
            />

            {/* Filter Toggle */}
            <Button
              variant={showFilters ? 'contained' : 'outlined'}
              startIcon={<FilterIcon />}
              onClick={() => setShowFilters(!showFilters)}
              sx={{ minHeight: 40 }}
            >
              {t('common.filters', 'Filters')}
              {hasActiveFilters && (
                <Chip
                  size="small"
                  label="!"
                  color="secondary"
                  sx={{ ml: 1, height: 20, minWidth: 20 }}
                />
              )}
            </Button>

            {/* Clear Filters */}
            {hasActiveFilters && (
              <Button
                variant="text"
                onClick={handleClearFilters}
                sx={{ minHeight: 40 }}
              >
                {t('common.clearAll', 'Clear All')}
              </Button>
            )}

            {/* Candidate Count */}
            <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
              {totalCandidates} {totalCandidates === 1 ? t('reviewQueue.candidate', 'candidate') : t('reviewQueue.candidates', 'candidates')}
            </Typography>
          </Box>

          {/* Expandable Filters */}
          {showFilters && (
            <>
              <Divider />
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                {/* Vacancy Filter */}
                {uniqueVacancies.length > 0 && (
                  <FormControl size="small" sx={{ minWidth: 200 }}>
                    <InputLabel>{t('reviewQueue.filterByVacancy', 'Vacancy')}</InputLabel>
                    <Select
                      value={selectedVacancy}
                      label={t('reviewQueue.filterByVacancy', 'Vacancy')}
                      onChange={(e) => setSelectedVacancy(e.target.value)}
                    >
                      <MenuItem value="">
                        <em>{t('common.all', 'All')}</em>
                      </MenuItem>
                      {uniqueVacancies.map(([id, title]) => (
                        <MenuItem key={id} value={id}>
                          {title}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}

                {/* Priority Filter */}
                <FormControl size="small" sx={{ minWidth: 150 }}>
                  <InputLabel>{t('reviewQueue.filterByPriority', 'Priority')}</InputLabel>
                  <Select
                    value={selectedPriority}
                    label={t('reviewQueue.filterByPriority', 'Priority')}
                    onChange={(e) => setSelectedPriority(e.target.value)}
                  >
                    <MenuItem value="">
                      <em>{t('common.all', 'All')}</em>
                    </MenuItem>
                    <MenuItem value="urgent">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <WarningIcon sx={{ fontSize: 16, color: 'error.main' }} />
                        {t('priority.urgent', 'Urgent')}
                      </Box>
                    </MenuItem>
                    <MenuItem value="high">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <TrendingUpIcon sx={{ fontSize: 16, color: 'warning.main' }} />
                        {t('priority.high', 'High')}
                      </Box>
                    </MenuItem>
                    <MenuItem value="normal">{t('priority.normal', 'Normal')}</MenuItem>
                    <MenuItem value="low">{t('priority.low', 'Low')}</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </>
          )}
        </Stack>
      </Paper>

      {/* Loading State */}
      {isLoading && (
        <LoadingSpinner variant="cards" count={6} message={t('reviewQueue.loading', 'Loading candidates...')} />
      )}

      {/* Error State */}
      {isError && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="error" variant="h6" gutterBottom>
            {t('reviewQueue.errorTitle', 'Failed to load candidates')}
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            {t('reviewQueue.errorMessage', 'Please try again or contact support if the problem persists.')}
          </Typography>
          <Button variant="contained" onClick={() => refetch()}>
            {t('common.retry', 'Retry')}
          </Button>
        </Paper>
      )}

      {/* Empty State */}
      {!isLoading && !isError && candidates.length === 0 && (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <PersonIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {hasActiveFilters
              ? t('reviewQueue.noMatches', 'No candidates match your filters')
              : t('reviewQueue.emptyTitle', 'No candidates pending review')}
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>
            {hasActiveFilters
              ? t('reviewQueue.clearFiltersHint', 'Try adjusting your search criteria')
              : t('reviewQueue.emptyMessage', 'All caught up! New candidates will appear here when they need your review.')}
          </Typography>
          {hasActiveFilters && (
            <Button variant="outlined" onClick={handleClearFilters}>
              {t('common.clearFilters', 'Clear Filters')}
            </Button>
          )}
        </Paper>
      )}

      {/* Candidate Cards Grid */}
      {!isLoading && !isError && candidates.length > 0 && (
        <Grid container spacing={2}>
          {candidates.map((candidate) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={candidate.id}>
              <CandidateCard
                candidate={candidate}
                onViewDetails={handleViewDetails}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Load More / Pagination Info */}
      {!isLoading && !isError && pagination && pagination.total > pagination.limit && (
        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            {t('reviewQueue.showing', 'Showing {{count}} of {{total}} candidates', {
              count: candidates.length,
              total: pagination.total
            })}
          </Typography>
        </Box>
      )}

      {/* Mobile-optimized tip */}
      <Box sx={{ mt: 4, p: 2, bgcolor: alpha(theme.palette.info.main, 0.1), borderRadius: 2 }}>
        <Typography variant="body2" color="text.secondary">
          <strong>💡 {t('reviewQueue.tip.title', 'Tip:')}</strong>{' '}
          {t(
            'reviewQueue.tip.content',
            'Click "View Details" to see the full candidate profile, recruiter feedback, and make your approval or rejection decision.'
          )}
        </Typography>
      </Box>
    </Container>
  );
}

export default ReviewQueuePage;
