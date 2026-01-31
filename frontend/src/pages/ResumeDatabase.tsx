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
  CircularProgress,
  TextField,
  InputAdornment,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  Work as WorkIcon,
  Search as SearchIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

interface Resume {
  id: string;
  filename: string;
  status: string;
  created_at: string;
  language?: string;
  skills: string[];
}

/**
 * Resume Database Page (Recruiter Module)
 *
 * Allows recruiters to browse the resume database.
 * Shows candidate profiles with their skills and experience.
 */
const ResumeDatabasePage: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [filteredResumes, setFilteredResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [resumeToDelete, setResumeToDelete] = useState<string | null>(null);

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

  // Filter resumes based on search query
  useEffect(() => {
    if (!searchQuery) {
      setFilteredResumes(resumes);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = resumes.filter((resume) =>
      resume.skills?.some((skill) => skill.toLowerCase().includes(query)) ||
      resume.filename?.toLowerCase().includes(query)
    );
    setFilteredResumes(filtered);
  }, [searchQuery, resumes]);

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

  return (
    <Container maxWidth="lg" sx={{ px: { xs: 1, sm: 2, md: 3 } }}>
      <Box sx={{ mt: { xs: 2, sm: 3, md: 4 }, mb: 2 }}>
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

        {/* Search Bar */}
        <Paper sx={{ p: { xs: 1.5, sm: 2 }, mb: { xs: 2, sm: 3, md: 4 } }}>
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
          />
        </Paper>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: { xs: 2, sm: 4 } }}>
            <CircularProgress size={isMobile ? 40 : 50} />
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
                  <CardActions sx={{ justifyContent: 'flex-end', px: { xs: 1, sm: 2 }, pb: { xs: 1, sm: 2 } }}>
                    <IconButton
                      color="error"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteClick(resume.id);
                      }}
                      sx={{
                        // Ensure minimum touch target size of 44x44px
                        minWidth: 44,
                        minHeight: 44,
                        padding: 1,
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
      </Box>
    </Container>
  );
};

export default ResumeDatabasePage;
