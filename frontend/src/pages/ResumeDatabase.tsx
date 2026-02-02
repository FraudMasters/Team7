import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Container,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  TextField,
  InputAdornment,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  ToggleButtonGroup,
  ToggleButton,
  Stack,
  Tooltip,
  Collapse,
  useMediaQuery,
  useTheme,
  Snackbar,
  Alert,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Work as WorkIcon,
  Search as SearchIcon,
  Delete as DeleteIcon,
  Sort as SortIcon,
  AccessTime as RecentIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Email as EmailIcon,
  Event as EventIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import LoadingSpinner from '../components/LoadingSpinner';

interface Resume {
  id: string;
  filename: string;
  status: string;
  created_at: string;
  language?: string;
  skills: string[];
  starred?: boolean;
}

/**
 * Resume Database Page (Recruiter Module)
 *
 * Allows recruiters to browse the resume database.
 * Shows candidate profiles with their skills and experience.
 */
type SortBy = 'name' | 'date' | 'status';

const ResumeDatabasePage: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [filteredResumes, setFilteredResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortBy>('date');
  const [quickFilter, setQuickFilter] = useState<'all' | 'starred' | 'recent'>('all');
  const [filtersExpanded, setFiltersExpanded] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [resumeToDelete, setResumeToDelete] = useState<string | null>(null);
  const [interviewDialogOpen, setInterviewDialogOpen] = useState(false);
  const [resumeForInterview, setResumeForInterview] = useState<Resume | null>(null);
  const [interviewDate, setInterviewDate] = useState('');
  const [interviewTime, setInterviewTime] = useState('');
  const [interviewType, setInterviewType] = useState('screening');
  const [interviewNotes, setInterviewNotes] = useState('');
  const [actionFeedback, setActionFeedback] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const fetchResumes = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/resumes/?limit=100');
      // Map technical_skills to skills for compatibility
      const resumesWithSkills = response.data.map((r: any) => ({
        ...r,
        skills: r.technical_skills || [],
      }));
      setResumes(resumesWithSkills);
      setFilteredResumes(resumesWithSkills);
    } catch (error) {
      console.error('Error fetching resumes:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  // Filter and sort resumes based on search query, quick filter, and sort order
  useEffect(() => {
    let filtered = [...resumes];

    // Apply quick filter
    if (quickFilter === 'starred') {
      filtered = filtered.filter((resume) => resume.starred);
    } else if (quickFilter === 'recent') {
      // Filter resumes from the last 7 days
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      filtered = filtered.filter((resume) => new Date(resume.created_at) >= sevenDaysAgo);
    }

    // Apply search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((resume) =>
        resume.skills?.some((skill) => skill.toLowerCase().includes(query)) ||
        resume.filename?.toLowerCase().includes(query)
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.filename.localeCompare(b.filename);
        case 'date':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'status':
          return a.status.localeCompare(b.status);
        default:
          return 0;
      }
    });

    setFilteredResumes(filtered);
  }, [searchQuery, resumes, sortBy, quickFilter]);

  const getTitleFromFilename = (filename: string) => {
    // Extract CV number from filename like "CV_1.docx"
    const match = filename.match(/CV_(\d+)\.docx/);
    return match ? t('resumeDatabase.candidate', { number: match[1] }) : filename;
  };

  const handleDeleteClick = (id: string) => {
    setResumeToDelete(id);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!resumeToDelete) return;

    try {
      await axios.delete(`/api/resumes/${resumeToDelete}`);
      // Remove from list
      setResumes(resumes.filter((r) => r.id !== resumeToDelete));
      setFilteredResumes(filteredResumes.filter((r) => r.id !== resumeToDelete));
      setDeleteDialogOpen(false);
      setResumeToDelete(null);
    } catch (error) {
      console.error('Error deleting resume:', error);
      alert('Failed to delete resume');
    }
  };

  const handleToggleStar = async (resume: Resume) => {
    try {
      const newStarredValue = !resume.starred;
      await axios.patch(`/api/resumes/${resume.id}`, { starred: newStarredValue });
      // Update local state
      setResumes(resumes.map((r) => (r.id === resume.id ? { ...r, starred: newStarredValue } : r)));
      setFilteredResumes(filteredResumes.map((r) => (r.id === resume.id ? { ...r, starred: newStarredValue } : r)));
      setActionFeedback({
        open: true,
        message: newStarredValue ? t('resumeDatabase.starredSuccess') : t('resumeDatabase.unstarredSuccess'),
        severity: 'success',
      });
    } catch (error) {
      console.error('Error toggling star:', error);
      setActionFeedback({
        open: true,
        message: t('errors.somethingWentWrong'),
        severity: 'error',
      });
    }
  };

  const handleEmail = (resume: Resume) => {
    const subject = encodeURIComponent(t('resumeDatabase.emailSubject'));
    const body = encodeURIComponent(t('resumeDatabase.emailBody'));
    const mailtoLink = `mailto:?subject=${subject}&body=${body}`;
    window.location.href = mailtoLink;
    setActionFeedback({
      open: true,
      message: t('resumeDatabase.emailSent'),
      severity: 'success',
    });
  };

  const handleOpenInterviewDialog = (resume: Resume) => {
    setResumeForInterview(resume);
    setInterviewDate('');
    setInterviewTime('');
    setInterviewType('screening');
    setInterviewNotes('');
    setInterviewDialogOpen(true);
  };

  const handleCloseInterviewDialog = () => {
    setInterviewDialogOpen(false);
    setResumeForInterview(null);
  };

  const handleScheduleInterview = async () => {
    if (!resumeForInterview) return;

    // Placeholder for backend integration
    // TODO: Integrate with backend API when available
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 500));
      setActionFeedback({
        open: true,
        message: t('resumeDatabase.interviewDialog.success', {
          date: interviewDate || 'TBD',
          time: interviewTime || 'TBD',
        }),
        severity: 'success',
      });
      setInterviewDialogOpen(false);
    } catch (error) {
      console.error('Error scheduling interview:', error);
      setActionFeedback({
        open: true,
        message: t('resumeDatabase.interviewDialog.error'),
        severity: 'error',
      });
    }
  };

  return (
    <Container maxWidth="lg" sx={{ px: { xs: 1, sm: 2, md: 3 } }}>
      <Box sx={{ mt: { xs: 2, sm: 3, md: 4 }, mb: 2, overflowX: 'hidden' }}>
        <Typography
          variant={isMobile ? 'h5' : 'h4'}
          component="h1"
          gutterBottom
          fontWeight={600}
        >
          {t('resumeDatabase.title')}
        </Typography>
        <Typography
          variant={isMobile ? 'body2' : 'body1'}
          color="text.secondary"
          paragraph
        >
          {t('resumeDatabase.subtitle', { count: resumes.length })}
        </Typography>

        {/* Search and Filter Panel */}
        <Paper sx={{ mb: { xs: 2, sm: 3, md: 4 } }}>
          {/* Mobile Toggle Header */}
          {isMobile && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                px: 2,
                py: 1.5,
                borderBottom: filtersExpanded ? 1 : 0,
                borderColor: 'divider',
              }}
            >
              <Typography variant="subtitle1" fontWeight={600}>
                {t('resumeDatabase.filters')}
              </Typography>
              <IconButton
                onClick={() => setFiltersExpanded(!filtersExpanded)}
                size="small"
                aria-label={filtersExpanded ? 'collapse filters' : 'expand filters'}
              >
                {filtersExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>
          )}

          <Collapse in={!isMobile || filtersExpanded}>
            <Box sx={{ p: { xs: 1.5, sm: 2 } }}>
              {/* Search Bar */}
              <TextField
                fullWidth
                placeholder={t('resumeDatabase.searchPlaceholder')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                size={isMobile ? 'small' : 'medium'}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 2 }}
              />

              {/* Sort and Quick Filter Options */}
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: { xs: 'column', sm: 'row' },
                  gap: 2,
                  alignItems: { xs: 'flex-start', sm: 'center' },
                  justifyContent: { xs: 'flex-start', sm: 'space-between' },
                  overflowX: 'hidden',
                }}
              >
                {/* Sort Options */}
                <Box sx={{ flex: { xs: '1', sm: '1 1 auto' }, minWidth: 0, overflowX: 'auto' }}>
                  <ToggleButtonGroup
                    value={sortBy}
                    exclusive
                    onChange={(_, value) => value && setSortBy(value)}
                    size="small"
                  >
                    <ToggleButton value="name" aria-label="sort by name">
                      <Tooltip title={t('resumeDatabase.sortByName')}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <SortIcon fontSize="small" />
                          <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: 'body2' } }}>{t('resumeDatabase.name')}</Typography>
                        </Box>
                      </Tooltip>
                    </ToggleButton>
                    <ToggleButton value="date" aria-label="sort by date">
                      <Tooltip title={t('resumeDatabase.sortByDate')}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <RecentIcon fontSize="small" />
                          <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: 'body2' } }}>{t('resumeDatabase.date')}</Typography>
                        </Box>
                      </Tooltip>
                    </ToggleButton>
                    <ToggleButton value="status" aria-label="sort by status">
                      <Tooltip title={t('resumeDatabase.sortByStatus')}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: 'body2' } }}>{t('resumeDatabase.status')}</Typography>
                        </Box>
                      </Tooltip>
                    </ToggleButton>
                  </ToggleButtonGroup>
                </Box>

                {/* Quick Filters */}
                <Box sx={{ flex: { xs: '1', sm: '1 1 auto' }, minWidth: 0, overflowX: 'auto' }}>
                  <ToggleButtonGroup
                    value={quickFilter}
                    exclusive
                    onChange={(_, value) => value && setQuickFilter(value)}
                    size="small"
                  >
                    <ToggleButton value="all" aria-label="show all">
                      <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: 'body2' } }}>{t('resumeDatabase.all')}</Typography>
                    </ToggleButton>
                    <ToggleButton value="starred" aria-label="show starred only">
                      <Tooltip title={t('resumeDatabase.starredOnly')}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <StarIcon fontSize="small" />
                          <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: 'body2' } }}>{t('resumeDatabase.starred')}</Typography>
                        </Box>
                      </Tooltip>
                    </ToggleButton>
                    <ToggleButton value="recent" aria-label="show recent only">
                      <Tooltip title={t('resumeDatabase.recentOnly')}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <RecentIcon fontSize="small" />
                          <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: 'body2' } }}>{t('resumeDatabase.recent')}</Typography>
                        </Box>
                      </Tooltip>
                    </ToggleButton>
                  </ToggleButtonGroup>
                </Box>
              </Box>

              {/* Results Count */}
              <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                <Typography variant="body2" color="text.secondary">
                  {t('resumeDatabase.showing', { count: filteredResumes.length, total: resumes.length })}
                </Typography>
              </Box>
            </Box>
          </Collapse>
        </Paper>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: { xs: 2, sm: 4 } }}>
            <LoadingSpinner size={isMobile ? 40 : 50} />
          </Box>
        ) : filteredResumes.length === 0 ? (
          <Paper sx={{ p: { xs: 2, sm: 3, md: 4 }, textAlign: 'center' }}>
            <Typography variant={isMobile ? 'body2' : 'body1'} color="text.secondary">
              {searchQuery ? t('resumeDatabase.noResumesSearch') : t('resumeDatabase.noResumes')}
            </Typography>
          </Paper>
        ) : (
          <Grid container spacing={{ xs: 2, sm: 3 }}>
            {filteredResumes.map((resume) => (
              <Grid item xs={12} sm={6} lg={4} xl={3} key={resume.id}>
                <Card
                  sx={{
                    height: '100%',
                    cursor: 'pointer',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4,
                    },
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                  onClick={() => (window.location.href = `/results/${resume.id}`)}
                >
                  <CardContent sx={{ pb: 1, flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
                      <WorkIcon sx={{ mr: 1, color: 'primary.main', fontSize: isMobile ? '1.2rem' : '1.5rem' }} />
                      <Typography
                        variant={isMobile ? 'body1' : 'h6'}
                        sx={{ flex: 1, minWidth: 0 }}
                        noWrap
                      >
                        {getTitleFromFilename(resume.filename)}
                      </Typography>
                      <Chip
                        label={resume.status}
                        size="small"
                        color={resume.status === 'COMPLETED' ? 'success' : 'default'}
                        sx={{ fontSize: isMobile ? '0.7rem' : '0.75rem' }}
                      />
                    </Box>

                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                      ID: {resume.id.slice(0, 8)}...
                    </Typography>

                    {resume.skills && resume.skills.length > 0 ? (
                      <Box sx={{ mt: 2 }}>
                        {resume.skills.slice(0, isMobile ? 5 : 8).map((skill) => (
                          <Chip
                            key={skill}
                            label={skill}
                            size="small"
                            variant="outlined"
                            sx={{
                              mr: 0.5,
                              mb: 0.5,
                              fontSize: isMobile ? '0.7rem' : '0.75rem',
                              height: isMobile ? 24 : 'auto',
                            }}
                          />
                        ))}
                        {resume.skills.length > (isMobile ? 5 : 8) && (
                          <Chip
                            label={t('resumeDatabase.moreSkills', { count: resume.skills.length - (isMobile ? 5 : 8) })}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: isMobile ? '0.7rem' : '0.75rem', height: isMobile ? 24 : 'auto' }}
                          />
                        )}
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1, fontStyle: 'italic' }}>
                        {t('resumeDatabase.noSkills')}
                      </Typography>
                    )}
                  </CardContent>
                  <CardActions sx={{ justifyContent: 'space-between', px: { xs: 1, sm: 2 }, pb: { xs: 1, sm: 2 } }}>
                    {/* Quick Actions */}
                    <Stack direction="row" spacing={0.5}>
                      <Tooltip title={resume.starred ? t('resumeDatabase.unstar') : t('resumeDatabase.star')}>
                        <IconButton
                          color={resume.starred ? 'primary' : 'default'}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleToggleStar(resume);
                          }}
                          size="small"
                          sx={{
                            minWidth: 36,
                            minHeight: 36,
                          }}
                          aria-label={resume.starred ? t('resumeDatabase.unstar') : t('resumeDatabase.star')}
                        >
                          {resume.starred ? <StarIcon /> : <StarBorderIcon />}
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={t('resumeDatabase.email')}>
                        <IconButton
                          color="primary"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEmail(resume);
                          }}
                          size="small"
                          sx={{
                            minWidth: 36,
                            minHeight: 36,
                          }}
                          aria-label={t('resumeDatabase.email')}
                        >
                          <EmailIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={t('resumeDatabase.scheduleInterview')}>
                        <IconButton
                          color="success"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenInterviewDialog(resume);
                          }}
                          size="small"
                          sx={{
                            minWidth: 36,
                            minHeight: 36,
                          }}
                          aria-label={t('resumeDatabase.scheduleInterview')}
                        >
                          <EventIcon />
                        </IconButton>
                      </Tooltip>
                    </Stack>

                    {/* Delete Action */}
                    <IconButton
                      color="error"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteClick(resume.id);
                      }}
                      size="small"
                      sx={{
                        minWidth: 36,
                        minHeight: 36,
                      }}
                      aria-label={t('resumeDatabase.delete')}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

        {/* Delete Confirmation Dialog */}
        <Dialog
          open={deleteDialogOpen}
          onClose={() => setDeleteDialogOpen(false)}
          fullWidth
          maxWidth="xs"
          PaperProps={{
            sx: {
              mx: { xs: 1, sm: 2 },
            }
          }}
        >
          <DialogTitle>{t('resumeDatabase.deleteDialog.title')}</DialogTitle>
          <DialogContent>
            <Typography variant={isMobile ? 'body2' : 'body1'}>
              {t('resumeDatabase.deleteDialog.message')}
            </Typography>
          </DialogContent>
          <DialogActions sx={{ flexDirection: { xs: 'column', sm: 'row' }, gap: 1, px: 2, pb: 2 }}>
            <Button
              onClick={() => setDeleteDialogOpen(false)}
              fullWidth={isMobile}
              sx={{ minWidth: isMobile ? '100%' : 100 }}
            >
              {t('common.cancel')}
            </Button>
            <Button
              onClick={handleDeleteConfirm}
              color="error"
              variant="contained"
              fullWidth={isMobile}
              sx={{ minWidth: isMobile ? '100%' : 100 }}
            >
              {t('common.delete')}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Interview Scheduling Dialog */}
        <Dialog
          open={interviewDialogOpen}
          onClose={handleCloseInterviewDialog}
          fullWidth
          maxWidth="sm"
          PaperProps={{
            sx: {
              mx: { xs: 1, sm: 2 },
            }
          }}
        >
          <DialogTitle>{t('resumeDatabase.interviewDialog.title')}</DialogTitle>
          <DialogContent>
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                {t('resumeDatabase.interviewDialog.candidate')}: {resumeForInterview?.getTitleFromFilename?.(resumeForInterview.filename) || getTitleFromFilename(resumeForInterview?.filename || '')}
              </Typography>
            </Box>
            <Stack spacing={2}>
              <TextField
                fullWidth
                type="date"
                label={t('resumeDatabase.interviewDialog.date')}
                value={interviewDate}
                onChange={(e) => setInterviewDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
                size={isMobile ? 'small' : 'medium'}
              />
              <TextField
                fullWidth
                type="time"
                label={t('resumeDatabase.interviewDialog.time')}
                value={interviewTime}
                onChange={(e) => setInterviewTime(e.target.value)}
                InputLabelProps={{ shrink: true }}
                size={isMobile ? 'small' : 'medium'}
              />
              <FormControl fullWidth size={isMobile ? 'small' : 'medium'}>
                <InputLabel id="interview-type-label">{t('resumeDatabase.interviewDialog.type')}</InputLabel>
                <Select
                  labelId="interview-type-label"
                  value={interviewType}
                  label={t('resumeDatabase.interviewDialog.type')}
                  onChange={(e) => setInterviewType(e.target.value)}
                >
                  <MenuItem value="screening">{t('resumeDatabase.interviewDialog.types.screening')}</MenuItem>
                  <MenuItem value="technical">{t('resumeDatabase.interviewDialog.types.technical')}</MenuItem>
                  <MenuItem value="onsite">{t('resumeDatabase.interviewDialog.types.onsite')}</MenuItem>
                  <MenuItem value="panel">{t('resumeDatabase.interviewDialog.types.panel')}</MenuItem>
                </Select>
              </FormControl>
              <TextField
                fullWidth
                multiline
                rows={3}
                label={t('resumeDatabase.interviewDialog.notes')}
                value={interviewNotes}
                onChange={(e) => setInterviewNotes(e.target.value)}
                placeholder={t('resumeDatabase.interviewDialog.notes')}
                size={isMobile ? 'small' : 'medium'}
              />
            </Stack>
          </DialogContent>
          <DialogActions sx={{ flexDirection: { xs: 'column', sm: 'row' }, gap: 1, px: 2, pb: 2 }}>
            <Button
              onClick={handleCloseInterviewDialog}
              fullWidth={isMobile}
              sx={{ minWidth: isMobile ? '100%' : 100 }}
            >
              {t('common.cancel')}
            </Button>
            <Button
              onClick={handleScheduleInterview}
              color="success"
              variant="contained"
              fullWidth={isMobile}
              sx={{ minWidth: isMobile ? '100%' : 100 }}
            >
              {t('resumeDatabase.interviewDialog.confirm')}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Action Feedback Snackbar */}
        <Snackbar
          open={actionFeedback.open}
          autoHideDuration={4000}
          onClose={() => setActionFeedback({ ...actionFeedback, open: false })}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert
            onClose={() => setActionFeedback({ ...actionFeedback, open: false })}
            severity={actionFeedback.severity}
            sx={{ width: '100%' }}
          >
            {actionFeedback.message}
          </Alert>
        </Snackbar>
      </Box>
    </Container>
  );
};

export default ResumeDatabasePage;
