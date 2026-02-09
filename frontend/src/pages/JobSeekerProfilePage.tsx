import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Container,
  Typography,
  Paper,
  Tabs,
  Tab,
  Stack,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Person as PersonIcon,
  Work as WorkIcon,
  School as SchoolIcon,
  Psychology as SkillsIcon,
} from '@mui/icons-material';
import { PageTransition } from '@components/mui/PageTransition';
import { LoadingState } from '@components/mui/LoadingState';
import { ErrorState } from '@components/mui/ErrorState';
import { profilesClient } from '@/api/profiles';
import type {
  JobSeekerProfile,
  WorkHistoryItem,
  EducationItem,
  SkillItem,
} from '@/types/api';

/**
 * Интерфейс таба
 */
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

/**
 * Компонент панели таба
 *
 * Отображает содержимое таба, когда он активен.
 */
function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div
      role="tabpanel"
      id={`profile-tabpanel-${index}`}
      aria-labelledby={`profile-tab-${index}`}
      hidden={value !== index}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * Свойства таба
 */
interface TabProps {
  label: string;
  icon: React.ReactElement;
  index: number;
}

/**
 * Компонент таба с доступностью
 */
function a11yProps(index: number) {
  return {
    id: `profile-tab-${index}`,
    'aria-controls': `profile-tabpanel-${index}`,
  };
}

/**
 * Страница профиля соискателя
 *
 * Отображает профиль пользователя с табированным интерфейсом для управления
 * базовой информацией, историей работы, образованием и навыками.
 */
export function JobSeekerProfilePage() {
  const [currentTab, setCurrentTab] = useState(0);

  // Загружаем профиль пользователя
  const {
    data: profile,
    isLoading: isLoadingProfile,
    error: profileError,
  } = useQuery({
    queryKey: ['profile'],
    queryFn: () => profilesClient.getMyProfile(),
  });

  // Загружаем историю работы
  const {
    data: workHistoryData,
    isLoading: isLoadingWorkHistory,
    error: workHistoryError,
  } = useQuery({
    queryKey: ['work-history'],
    queryFn: () => profilesClient.getWorkHistory(),
  });

  // Загружаем образование
  const {
    data: educationData,
    isLoading: isLoadingEducation,
    error: educationError,
  } = useQuery({
    queryKey: ['education'],
    queryFn: () => profilesClient.getEducation(),
  });

  // Загружаем навыки
  const {
    data: skillsData,
    isLoading: isLoadingSkills,
    error: skillsError,
  } = useQuery({
    queryKey: ['skills'],
    queryFn: () => profilesClient.getSkills(),
  });

  const workHistory = workHistoryData?.work_history || [];
  const education = educationData?.education || [];
  const skills = skillsData?.skills || [];

  /**
   * Обработчик изменения таба
   */
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  // Состояние загрузки
  if (isLoadingProfile) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <LoadingState message="Loading profile..." />
        </Container>
      </PageTransition>
    );
  }

  // Состояние ошибки
  if (profileError) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <ErrorState
            title="Error Loading Profile"
            message={profileError.detail || 'Failed to load profile data'}
            onRetry={() => window.location.reload()}
          />
        </Container>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Заголовок страницы */}
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ mb: 4 }}
        >
          <Box>
            <Typography variant="h4" fontWeight={700} gutterBottom>
              My Profile
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Manage your professional information
            </Typography>
          </Box>
        </Stack>

        {/* Табированный интерфейс */}
        <Paper sx={{ width: '100%' }}>
          {/* Табы навигации */}
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            aria-label="Profile tabs"
            variant="scrollable"
            scrollButtons="auto"
            sx={{
              borderBottom: 1,
              borderColor: 'divider',
              px: 2,
            }}
          >
            <Tab
              label="Profile"
              icon={<PersonIcon />}
              {...a11yProps(0)}
              sx={{ minWidth: { xs: 80, sm: 120 } }}
            />
            <Tab
              label="Work History"
              icon={<WorkIcon />}
              {...a11yProps(1)}
              sx={{ minWidth: { xs: 80, sm: 120 } }}
            />
            <Tab
              label="Education"
              icon={<SchoolIcon />}
              {...a11yProps(2)}
              sx={{ minWidth: { xs: 80, sm: 120 } }}
            />
            <Tab
              label="Skills"
              icon={<SkillsIcon />}
              {...a11yProps(3)}
              sx={{ minWidth: { xs: 80, sm: 120 } }}
            />
          </Tabs>

          {/* Панель: Базовая информация профиля */}
          <TabPanel value={currentTab} index={0}>
            <Box sx={{ px: 3 }}>
              <Stack spacing={3}>
                <Box>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Basic Information
                  </Typography>
                  <Stack spacing={2} sx={{ mt: 2 }}>
                    {profile?.current_title && (
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Current Title
                        </Typography>
                        <Typography variant="body1">
                          {profile.current_title}
                        </Typography>
                      </Box>
                    )}
                    {profile?.location && (
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Location
                        </Typography>
                        <Typography variant="body1">
                          {profile.location}
                        </Typography>
                      </Box>
                    )}
                    {profile?.years_of_experience !== undefined && (
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Years of Experience
                        </Typography>
                        <Typography variant="body1">
                          {profile.years_of_experience} years
                        </Typography>
                      </Box>
                    )}
                    {profile?.status && (
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Status
                        </Typography>
                        <Typography variant="body1" sx={{ textTransform: 'capitalize' }}>
                          {profile.status.replace('_', ' ')}
                        </Typography>
                      </Box>
                    )}
                  </Stack>
                </Box>

                {profile?.bio && (
                  <>
                    <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 3 }}>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        About
                      </Typography>
                      <Typography
                        variant="body1"
                        color="text.secondary"
                        sx={{
                          whiteSpace: 'pre-wrap',
                          lineHeight: 1.8,
                          mt: 2,
                        }}
                      >
                        {profile.bio}
                      </Typography>
                    </Box>
                  </>
                )}

                <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Profile ID: {profile?.id}
                  </Typography>
                </Box>
              </Stack>
            </Box>
          </TabPanel>

          {/* Панель: История работы */}
          <TabPanel value={currentTab} index={1}>
            <Box sx={{ px: 3 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
                <Typography variant="h6" fontWeight={600}>
                  Work History
                </Typography>
                <Button variant="outlined" disabled>
                  Add Experience
                </Button>
              </Stack>

              {isLoadingWorkHistory ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
                  <CircularProgress />
                </Box>
              ) : workHistoryError ? (
                <Alert severity="error">
                  {workHistoryError.detail || 'Failed to load work history'}
                </Alert>
              ) : workHistory.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 6 }}>
                  <Typography variant="body1" color="text.secondary">
                    No work history added yet
                  </Typography>
                </Box>
              ) : (
                <Stack spacing={3}>
                  {workHistory.map((work: WorkHistoryItem) => (
                    <Box
                      key={work.id}
                      sx={{
                        p: 2,
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 2,
                      }}
                    >
                      <Typography variant="subtitle1" fontWeight={600}>
                        {work.position_title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {work.company_name}
                      </Typography>
                      <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
                        <Typography variant="body2" color="primary">
                          {work.start_date} - {work.end_date || 'Present'}
                        </Typography>
                        {work.employment_type && (
                          <Typography variant="body2" color="text.secondary">
                            • {work.employment_type.replace('_', ' ')}
                          </Typography>
                        )}
                      </Stack>
                      {work.description && (
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{ mt: 1, whiteSpace: 'pre-wrap' }}
                        >
                          {work.description}
                        </Typography>
                      )}
                    </Box>
                  ))}
                </Stack>
              )}
            </Box>
          </TabPanel>

          {/* Панель: Образование */}
          <TabPanel value={currentTab} index={2}>
            <Box sx={{ px: 3 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
                <Typography variant="h6" fontWeight={600}>
                  Education
                </Typography>
                <Button variant="outlined" disabled>
                  Add Education
                </Button>
              </Stack>

              {isLoadingEducation ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
                  <CircularProgress />
                </Box>
              ) : educationError ? (
                <Alert severity="error">
                  {educationError.detail || 'Failed to load education'}
                </Alert>
              ) : education.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 6 }}>
                  <Typography variant="body1" color="text.secondary">
                    No education added yet
                  </Typography>
                </Box>
              ) : (
                <Stack spacing={3}>
                  {education.map((edu: EducationItem) => (
                    <Box
                      key={edu.id}
                      sx={{
                        p: 2,
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 2,
                      }}
                    >
                      <Typography variant="subtitle1" fontWeight={600}>
                        {edu.degree}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {edu.institution_name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {edu.field_of_study}
                      </Typography>
                      <Typography variant="body2" color="primary" sx={{ mt: 1 }}>
                        {edu.start_date} - {edu.end_date || 'Present'}
                      </Typography>
                      {edu.degree_type && (
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                          Type: {edu.degree_type}
                        </Typography>
                      )}
                    </Box>
                  ))}
                </Stack>
              )}
            </Box>
          </TabPanel>

          {/* Панель: Навыки */}
          <TabPanel value={currentTab} index={3}>
            <Box sx={{ px: 3 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
                <Typography variant="h6" fontWeight={600}>
                  Skills
                </Typography>
                <Button variant="outlined" disabled>
                  Add Skill
                </Button>
              </Stack>

              {isLoadingSkills ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
                  <CircularProgress />
                </Box>
              ) : skillsError ? (
                <Alert severity="error">
                  {skillsError.detail || 'Failed to load skills'}
                </Alert>
              ) : skills.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 6 }}>
                  <Typography variant="body1" color="text.secondary">
                    No skills added yet
                  </Typography>
                </Box>
              ) : (
                <Stack spacing={2}>
                  {skills.map((skill: SkillItem) => (
                    <Box
                      key={skill.id}
                      sx={{
                        p: 2,
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 2,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        gap: 1,
                      }}
                    >
                      <Box>
                        <Typography variant="subtitle1" fontWeight={600}>
                          {skill.name}
                        </Typography>
                        {skill.category && (
                          <Typography variant="body2" color="text.secondary">
                            {skill.category}
                          </Typography>
                        )}
                      </Box>
                      <Stack direction="row" spacing={2} alignItems="center">
                        {skill.proficiency_level && (
                          <Typography variant="body2" color="primary" sx={{ textTransform: 'capitalize' }}>
                            {skill.proficiency_level}
                          </Typography>
                        )}
                        {skill.years_of_experience !== undefined && (
                          <Typography variant="body2" color="text.secondary">
                            {skill.years_of_experience} {skill.years_of_experience === 1 ? 'year' : 'years'}
                          </Typography>
                        )}
                      </Stack>
                    </Box>
                  ))}
                </Stack>
              )}
            </Box>
          </TabPanel>
        </Paper>
      </Container>
    </PageTransition>
  );
}

export default JobSeekerProfilePage;
