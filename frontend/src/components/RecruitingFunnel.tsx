import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Icon,
} from '@/components/ui';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

interface FunnelData {
  totalResumes: number;
  totalVacancies: number;
  highMatch: number;
  mediumMatch: number;
  lowMatch: number;
  avgMatchPercentage: number;
}

interface VacancyStats {
  vacancyId: string;
  title: string;
  highMatch: number;
  mediumMatch: number;
  totalMatch: number;
}

/**
 * RecruitingFunnel Component
 *
 * Displays a visual funnel of the hiring pipeline showing:
 * - Total resumes in database
 * - Total vacancies
 * - Resumes by match quality (high/medium/low)
 * - Average match percentage
 *
 * Note: Uses a sample of resumes for performance (limits API calls)
 */
const RecruitingFunnel: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [funnelData, setFunnelData] = useState<FunnelData | null>(null);
  const [vacancyStats, setVacancyStats] = useState<VacancyStats[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        // Fetch resumes and vacancies
        const [resumesResponse, vacanciesResponse] = await Promise.all([
          axios.get('/api/resumes/?limit=200'),
          axios.get('/api/vacancies/?limit=50'),
        ]);

        const resumes = resumesResponse.data;
        const vacancies = vacanciesResponse.data;

        // OPTIMIZATION: Only sample first 20 resumes for funnel calculation
        // This reduces API calls from 10,000+ to ~100 (20 resumes × 5 vacancies)
        const sampleSize = Math.min(resumes.length, 20);
        const sampleResumes = resumes.slice(0, sampleSize);

        // Calculate match statistics for each vacancy (using sample)
        const vacancyStatsData: VacancyStats[] = [];

        for (const vacancy of vacancies) {
          let highMatch = 0;
          let mediumMatch = 0;
          let totalMatch = 0;

          // Process match requests in parallel for better performance
          const matchPromises = sampleResumes.map((resume: any) =>
            axios.get(`/api/vacancies/match/${vacancy.id}?resume_id=${resume.id}`)
              .then((res) => res.data.match_percentage || 0)
              .catch(() => 0)
          );

          const matchResults = await Promise.all(matchPromises);

          for (const matchPct of matchResults) {
            if (matchPct >= 70) highMatch++;
            if (matchPct >= 50) mediumMatch++;
            if (matchPct > 0) totalMatch++;
          }

          vacancyStatsData.push({
            vacancyId: vacancy.id,
            title: vacancy.title,
            highMatch,
            mediumMatch,
            totalMatch,
          });
        }

        // Calculate overall funnel statistics (extrapolate from sample)
        const sampleHighMatch = vacancyStatsData.reduce((sum, v) => sum + v.highMatch, 0);
        const sampleMediumMatch = vacancyStatsData.reduce((sum, v) => sum + v.mediumMatch, 0);
        const sampleTotalMatch = vacancyStatsData.reduce((sum, v) => sum + v.totalMatch, 0);

        // Extrapolate to full dataset
        const multiplier = resumes.length / sampleSize;
        const highMatch = Math.round(sampleHighMatch * multiplier);
        const mediumMatch = Math.round(sampleMediumMatch * multiplier);
        const totalMatch = Math.round(sampleTotalMatch * multiplier);
        const avgMatchPercentage = totalMatch > 0 ? Math.round((highMatch + mediumMatch) / totalMatch * 100) : 0;

        setFunnelData({
          totalResumes: resumes.length,
          totalVacancies: vacancies.length,
          highMatch,
          mediumMatch,
          lowMatch: totalMatch - mediumMatch,
          avgMatchPercentage,
        });

        // Sort vacancies by high match count
        setVacancyStats(vacancyStatsData.sort((a, b) => b.highMatch - a.highMatch).slice(0, 5));
      } catch (error) {
        console.error('Error fetching funnel data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress />
        <Typography variant="body2" sx={{ mt: 2 }}>{t('funnel.loading')}</Typography>
      </Paper>
    );
  }

  if (!funnelData) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body1" color="secondary">
          {t('funnel.noData')}
        </Typography>
      </Paper>
    );
  }

  const funnelStages = [
    { label: t('funnel.allResumes'), count: funnelData.totalResumes, color: '#1976d2', iconName: 'file-text' },
    { label: t('funnel.activeVacancies'), count: funnelData.totalVacancies, color: '#9c27b0', iconName: 'briefcase' },
    { label: t('funnel.lowMatch'), count: funnelData.lowMatch, color: '#ff9800', iconName: 'trending-up' },
    { label: t('funnel.mediumMatch'), count: funnelData.mediumMatch, color: '#2196f3', iconName: 'trending-up' },
    { label: t('funnel.highMatch'), count: funnelData.highMatch, color: '#4caf50', iconName: 'check-circle-2' },
  ];

  const maxCount = Math.max(...funnelStages.map((s) => s.count), 1);

  return (
    <Box>
      {/* Funnel Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Icon name="filter" size={28} color="primary" sx={{ mr: 1 }} />
        <Typography variant="h5" fontWeight={600}>
          {t('funnel.title')}
        </Typography>
      </Box>

      {/* Visual Funnel */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle2" color="secondary" gutterBottom>
          {t('funnel.pipelineOverview')}
        </Typography>
        <Box sx={{ mt: 2 }}>
          {funnelStages.map((stage, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                alignItems: 'center',
                mb: 1.5,
                opacity: loading ? 0.5 : 1,
              }}
            >
              <Box sx={{ width: 160, flexShrink: 0 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Icon name={stage.iconName} size={18} sx={{ mr: 0.5, color: stage.color }} />
                  <Typography variant="body2" fontWeight={500}>
                    {stage.label}
                  </Typography>
                </Box>
              </Box>

              {/* Funnel Bar */}
              <Box
                sx={{
                  flex: 1,
                  height: 40,
                  backgroundColor: `${stage.color}20`,
                  borderRadius: 1,
                  position: 'relative',
                  overflow: 'hidden',
                  mx: 2,
                }}
              >
                <Box
                  sx={{
                    position: 'absolute',
                    left: 0,
                    top: 0,
                    height: '100%',
                    width: `${(stage.count / maxCount) * 100}%`,
                    backgroundColor: stage.color,
                    transition: 'width 0.5s ease',
                  }}
                />
                <Typography
                  variant="body2"
                  sx={{
                    position: 'absolute',
                    left: 10,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    fontWeight: 600,
                    color: stage.count > maxCount * 0.3 ? '#fff' : 'inherit',
                  }}
                >
                  {stage.count}
                </Typography>
              </Box>

              {/* Percentage */}
              <Typography
                variant="body2"
                fontWeight={600}
                sx={{ width: 60, textAlign: 'right', color: stage.color }}
              >
                {stage.count > 0 ? `${Math.round((stage.count / funnelData.totalResumes) * 100)}%` : '0%'}
              </Typography>
            </Box>
          ))}
        </Box>

        {/* Summary */}
        <Box
          sx={{
            mt: 3,
            p: 2,
            bgcolor: 'action.hover',
            borderRadius: 1,
            display: 'flex',
            justifyContent: 'space-around',
            flexWrap: 'wrap',
            gap: 2,
          }}
        >
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="primary" fontWeight={700}>
              {funnelData.avgMatchPercentage}%
            </Typography>
            <Typography variant="caption" color="secondary">
              {t('funnel.avgMatchRate')}
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="success" fontWeight={700}>
              {funnelData.highMatch}
            </Typography>
            <Typography variant="caption" color="secondary">
              {t('funnel.highQualityMatches')}
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="info" fontWeight={700}>
              {funnelData.mediumMatch}
            </Typography>
            <Typography variant="caption" color="secondary">
              {t('funnel.potentialCandidates')}
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Top Vacancies by High Matches */}
      {vacancyStats.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="subtitle2" color="secondary" gutterBottom>
            {t('funnel.topVacancies')}
          </Typography>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            {vacancyStats.map((stat) => (
              <Grid item xs={12} sm={6} md={4} key={stat.vacancyId}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    borderLeft: 3,
                    borderColor: stat.highMatch > 0 ? '#4caf50' : '#e0e0e0',
                  }}
                >
                  <CardContent sx={{ pb: 2 }}>
                    <Typography variant="subtitle2" fontWeight={600} noWrap>
                      {stat.title}
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h6" color="success" fontWeight={700}>
                          {stat.highMatch}
                        </Typography>
                        <Typography variant="caption" color="secondary">
                          70%+
                        </Typography>
                      </Box>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h6" color="info" fontWeight={700}>
                          {stat.mediumMatch}
                        </Typography>
                        <Typography variant="caption" color="secondary">
                          50%+
                        </Typography>
                      </Box>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h6" color="primary" fontWeight={700}>
                          {stat.totalMatch}
                        </Typography>
                        <Typography variant="caption" color="secondary">
                          Total
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}
    </Box>
  );
};

export default RecruitingFunnel;
