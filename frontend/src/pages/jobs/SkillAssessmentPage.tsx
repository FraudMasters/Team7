// Импорт хуков для управления состоянием
import { useState } from 'react';
// Импорт компонентов MUI для UI
import {
  Container,       // Контейнер для ограничения ширины содержимого
  Typography,      // Компонент для текста с различными стилями
  Box,             // Универсальный контейнер для верстки
  Paper,           // Контейнер с эффектом elevated (карточка)
  Button,          // Кнопки
  LinearProgress,  // Линейный индикатор прогресса
  Chip,            // Метки/теги
  Grid,            // Сетка для адаптивной верстки
  Card,            // Карточка
  CardContent,     // Содержимое карточки
  Divider,         // Разделитель
  Alert,           // Предупреждающее сообщение
} from '@mui/material';
// Импорт иконок из MUI
import {
  Assessment as AssessmentIcon,
  School as LearningIcon,
  CheckCircle as CheckedIcon,
  RadioButtonUnchecked as UncheckedIcon,
} from '@mui/icons-material';
// Импорт MUI компонентов
import { PageTransition } from '@components/mui/PageTransition';

// Интерфейс описывающий навык
interface Skill {
  name: string;
  category: string;
  proficiency: 'beginner' | 'intermediate' | 'advanced' | 'expert'; // Уровень владения
  verified: boolean; // Подтвержден ли навык
}

// Интерфейс описывающий категорию навыков
interface SkillCategory {
  name: string;
  skills: Skill[];
}

const mockSkillCategories: SkillCategory[] = [
  {
    name: 'Programming Languages',
    skills: [
      { name: 'JavaScript', category: 'Programming', proficiency: 'advanced', verified: true },
      { name: 'TypeScript', category: 'Programming', proficiency: 'intermediate', verified: true },
      { name: 'Python', category: 'Programming', proficiency: 'intermediate', verified: false },
      { name: 'Java', category: 'Programming', proficiency: 'beginner', verified: false },
    ],
  },
  {
    name: 'Frameworks & Libraries',
    skills: [
      { name: 'React', category: 'Frameworks', proficiency: 'advanced', verified: true },
      { name: 'Node.js', category: 'Frameworks', proficiency: 'intermediate', verified: true },
      { name: 'Next.js', category: 'Frameworks', proficiency: 'intermediate', verified: false },
      { name: 'Vue.js', category: 'Frameworks', proficiency: 'beginner', verified: false },
    ],
  },
  {
    name: 'Tools & Platforms',
    skills: [
      { name: 'Git', category: 'Tools', proficiency: 'advanced', verified: true },
      { name: 'Docker', category: 'Tools', proficiency: 'intermediate', verified: true },
      { name: 'AWS', category: 'Tools', proficiency: 'beginner', verified: false },
    ],
  },
];

// Цвета для уровней владения навыками
const proficiencyColors = {
  beginner: '#ef4444',
  intermediate: '#f59e0b',
  advanced: '#22c55e',
  expert: '#6366f1',
};

// Числовые значения для уровней владения
const proficiencyValues = {
  beginner: 25,
  intermediate: 50,
  advanced: 75,
  expert: 100,
};

/**
 * Страница оценки навыков
 * Отображает и позволяет оценить профессиональные навыки пользователя
 */
export function SkillAssessmentPage() {
  // Состояние категорий навыков
  const [categories, setCategories] = useState<SkillCategory[]>(mockSkillCategories);
  // Состояние выбранной категории
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Подсчет общего количества навыков
  const totalSkills = categories.reduce((acc, cat) => acc + cat.skills.length, 0);
  // Подсчет подтвержденных навыков
  const verifiedSkills = categories.reduce(
    (acc, cat) => acc + cat.skills.filter((s) => s.verified).length,
    0
  );

  /**
   * Обработчик переключения подтверждения навыка
   * @param categoryName - Название категории
   * @param skillName - Название навыка
   */
  const handleToggleVerified = (categoryName: string, skillName: string) => {
    setCategories((prev) =>
      prev.map((cat) =>
        cat.name === categoryName
          ? {
              ...cat,
              skills: cat.skills.map((skill) =>
                skill.name === skillName ? { ...skill, verified: !skill.verified } : skill
              ),
            }
          : cat
      )
    );
  };

  /**
   * Вычисление общего уровня владения навыками
   * @returns Процент общего уровня владения
   */
  const getOverallProficiency = () => {
    const totalValue = categories.reduce(
      (acc, cat) =>
        acc + cat.skills.reduce((sAcc, s) => sAcc + proficiencyValues[s.proficiency], 0),
      0
    );
    return Math.round(totalValue / totalSkills);
  };

  return (
    <PageTransition>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Заголовок страницы */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <AssessmentIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" fontWeight={700}>
                Skill Assessment
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Evaluate and track your professional skills
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Обзорные карточки со статистикой */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Total Skills
                </Typography>
                <Typography variant="h3" fontWeight={700}>
                  {totalSkills}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Verified Skills
                </Typography>
                <Typography variant="h3" fontWeight={700} color="primary">
                  {verifiedSkills}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Overall Level
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Typography variant="h3" fontWeight={700} color="success.main">
                    {getOverallProficiency()}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={getOverallProficiency()}
                    sx={{ flexGrow: 1, height: 10, borderRadius: 5 }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Информационное сообщение */}
        <Alert severity="info" sx={{ mb: 4 }}>
          <Typography variant="body2">
            Verified skills are confirmed through your resume, assessments, or endorsements. Complete
            skill assessments to verify your expertise.
          </Typography>
        </Alert>

        {/* Категории навыков */}
        <Grid container spacing={3}>
          {/* Список категорий */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Categories
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {categories.map((category) => (
                  <Button
                    key={category.name}
                    fullWidth
                    variant={selectedCategory === category.name ? 'contained' : 'outlined'}
                    onClick={() => setSelectedCategory(category.name)}
                    sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                      <span>{category.name}</span>
                      <Chip
                        label={category.skills.length}
                        size="small"
                        variant={selectedCategory === category.name ? 'filled' : 'outlined'}
                      />
                    </Box>
                  </Button>
                ))}
              </Box>
            </Paper>
          </Grid>

          {/* Детали навыков */}
          <Grid item xs={12} md={8}>
            {(selectedCategory
              ? categories.filter((c) => c.name === selectedCategory)
              : categories
            ).map((category) => (
              <Paper key={category.name} sx={{ p: 3, mb: 2 }}>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  {category.name}
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {category.skills.map((skill) => (
                    <Box
                      key={skill.name}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 2,
                        p: 2,
                        borderRadius: 2,
                        bgcolor: 'background.paper',
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      {/* Иконка статуса подтверждения */}
                      <Box
                        sx={{
                          width: 40,
                          height: 40,
                          borderRadius: '50%',
                          bgcolor: proficiencyColors[skill.proficiency] + '20',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        {skill.verified ? (
                          <CheckedIcon sx={{ color: proficiencyColors[skill.proficiency] }} />
                        ) : (
                          <UncheckedIcon sx={{ color: 'text.secondary' }} />
                        )}
                      </Box>
                      <Box sx={{ flexGrow: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                          <Typography variant="subtitle1" fontWeight={600}>
                            {skill.name}
                          </Typography>
                          {skill.verified && (
                            <Chip label="Verified" size="small" color="success" variant="outlined" />
                          )}
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{
                              textTransform: 'capitalize',
                              color: proficiencyColors[skill.proficiency],
                              fontWeight: 500,
                            }}
                          >
                            {skill.proficiency}
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={proficiencyValues[skill.proficiency]}
                            sx={{ flexGrow: 1, height: 6, borderRadius: 3 }}
                          />
                        </Box>
                      </Box>
                      <Button
                        size="small"
                        variant={skill.verified ? 'contained' : 'outlined'}
                        onClick={() => handleToggleVerified(category.name, skill.name)}
                      >
                        {skill.verified ? 'Verified' : 'Verify'}
                      </Button>
                    </Box>
                  ))}
                </Box>
              </Paper>
            ))}
          </Grid>
        </Grid>

        {/* Кнопка прохождения оценки навыков */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Button variant="contained" size="large" startIcon={<LearningIcon />}>
            Take Skill Assessment
          </Button>
        </Box>
      </Container>
    </PageTransition>
  );
}
