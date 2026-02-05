// Импорт хуков для управления состоянием
import { useState } from 'react';
// Импорт компонентов MUI для UI
import {
  Container,       // Контейнер для ограничения ширины содержимого
  Typography,      // Компонент для текста с различными стилями
  Box,             // Универсальный контейнер для верстки
  Grid,            // Сетка для адаптивной верстки
  Paper,           // Контейнер с эффектом elevated (карточка)
  Card,            // Карточка
  CardContent,     // Содержимое карточки
  Chip,            // Метки/теги
  Button,          // Кнопки
  TextField,       // Поле ввода текста
  InputAdornment,  // Декоративный элемент в поле ввода
} from '@mui/material';
// Импорт иконок из MUI
import {
  School as LearningIcon,
  Search as SearchIcon,
  PlayArrow as PlayIcon,
  CheckCircle as CompletedIcon,
  Schedule as DurationIcon,
  TrendingUp as LevelIcon,
} from '@mui/icons-material';
// Импорт MUI компонентов
import { PageTransition } from '@components/mui/PageTransition';

// Интерфейс описывающий курс обучения
interface Course {
  id: string;
  title: string;
  description: string;
  category: string;
  level: 'beginner' | 'intermediate' | 'advanced'; // Уровень сложности
  duration: string;   // Продолжительность
  modules: number;    // Количество модулей
  progress?: number;  // Прогресс прохождения
  completed?: boolean; // Завершен ли курс
  thumbnail?: string;
  skills: string[];   // Приобретаемые навыки
}

// Демо-данные курсов
const mockCourses: Course[] = [
  {
    id: '1',
    title: 'React Fundamentals',
    description: 'Master the basics of React including components, hooks, and state management.',
    category: 'Frontend',
    level: 'beginner',
    duration: '4 hours',
    modules: 8,
    progress: 75,
    skills: ['React', 'JavaScript', 'Hooks'],
  },
  {
    id: '2',
    title: 'TypeScript Deep Dive',
    description: 'Learn advanced TypeScript concepts for building type-safe applications.',
    category: 'Frontend',
    level: 'intermediate',
    duration: '6 hours',
    modules: 12,
    progress: 30,
    skills: ['TypeScript', 'Types', 'Generics'],
  },
  {
    id: '3',
    title: 'Node.js Backend Development',
    description: 'Build scalable backend services with Node.js and Express.',
    category: 'Backend',
    level: 'intermediate',
    duration: '8 hours',
    modules: 15,
    skills: ['Node.js', 'Express', 'API Design'],
  },
  {
    id: '4',
    title: 'Docker & Kubernetes',
    description: 'Container orchestration and deployment strategies.',
    category: 'DevOps',
    level: 'advanced',
    duration: '10 hours',
    modules: 20,
    skills: ['Docker', 'Kubernetes', 'CI/CD'],
  },
  {
    id: '5',
    title: 'AWS Cloud Practitioner',
    description: 'Foundational AWS cloud computing skills.',
    category: 'Cloud',
    level: 'beginner',
    duration: '6 hours',
    modules: 10,
    completed: true,
    skills: ['AWS', 'Cloud Computing', 'Lambda'],
  },
  {
    id: '6',
    title: 'Python for Data Science',
    description: 'Data analysis and visualization with Python.',
    category: 'Data Science',
    level: 'intermediate',
    duration: '12 hours',
    modules: 18,
    skills: ['Python', 'Pandas', 'NumPy'],
  },
];

// Список категорий курсов
const categories = ['All', 'Frontend', 'Backend', 'DevOps', 'Cloud', 'Data Science'];
// Список уровней сложности
const levels = ['All', 'beginner', 'intermediate', 'advanced'];

/**
 * Страница учебного центра
 * Отображает доступные курсы для повышения квалификации
 */
export function LearningPage() {
  // Состояние поискового запроса
  const [searchQuery, setSearchQuery] = useState('');
  // Состояние выбранной категории
  const [selectedCategory, setSelectedCategory] = useState('All');
  // Состояние выбранного уровня
  const [selectedLevel, setSelectedLevel] = useState('All');

  // Фильтрация курсов по поиску, категории и уровню
  const filteredCourses = mockCourses.filter((course) => {
    const matchesSearch =
      searchQuery === '' ||
      course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCategory = selectedCategory === 'All' || course.category === selectedCategory;
    const matchesLevel = selectedLevel === 'All' || course.level === selectedLevel;

    return matchesSearch && matchesCategory && matchesLevel;
  });

  // Курсы в процессе прохождения
  const inProgressCourses = mockCourses.filter((c) => c.progress && c.progress > 0 && !c.completed);
  // Завершенные курсы
  const completedCourses = mockCourses.filter((c) => c.completed);

  return (
    <PageTransition>
      <Container maxWidth="xl" sx={{ py: 2 }}>
        {/* Заголовок страницы */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <LearningIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" fontWeight={700}>
                Learning Center
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Upskill with curated courses and certifications
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Статистика обучения */}
        <Grid container spacing={2} sx={{ mb: 4 }}>
          <Grid item xs={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" fontWeight={700} color="primary">
                {inProgressCourses.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                In Progress
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" fontWeight={700} color="success.main">
                {completedCourses.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Completed
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" fontWeight={700}>
                {mockCourses.reduce((acc, c) => acc + (c.progress || 0), 0) / mockCourses.length}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg Progress
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Поиск и фильтры */}
        <Paper sx={{ p: 2, mb: 4 }}>
          <TextField
            fullWidth
            placeholder="Search courses..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ mb: 2 }}
          />
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Typography variant="body2" color="text.secondary" sx={{ alignSelf: 'center' }}>
              Category:
            </Typography>
            {categories.map((cat) => (
              <Chip
                key={cat}
                label={cat}
                onClick={() => setSelectedCategory(cat)}
                color={selectedCategory === cat ? 'primary' : 'default'}
                variant={selectedCategory === cat ? 'filled' : 'outlined'}
              />
            ))}
          </Box>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ alignSelf: 'center' }}>
              Level:
            </Typography>
            {levels.map((level) => (
              <Chip
                key={level}
                label={level}
                onClick={() => setSelectedLevel(level)}
                color={selectedLevel === level ? 'primary' : 'default'}
                variant={selectedLevel === level ? 'filled' : 'outlined'}
                sx={{ textTransform: 'capitalize' }}
              />
            ))}
          </Box>
        </Paper>

        {/* Курсы в процессе прохождения */}
        {inProgressCourses.length > 0 && (
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Continue Learning
            </Typography>
            <Grid container spacing={2}>
              {inProgressCourses.map((course) => (
                <Grid item xs={12} sm={6} md={4} key={course.id}>
                  <Card
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      position: 'relative',
                    }}
                  >
                    {/* Индикатор прогресса */}
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        bgcolor: 'background.paper',
                        borderRadius: 1,
                        px: 1,
                        fontSize: '0.75rem',
                        fontWeight: 600,
                      }}
                    >
                      {course.progress}%
                    </Box>
                    <Box
                      sx={{
                        height: 120,
                        bgcolor: 'primary.100',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <LearningIcon sx={{ fontSize: 48, color: 'primary.main' }} />
                    </Box>
                    <CardContent sx={{ flexGrow: 1 }}>
                      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                        {course.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {course.description}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                        {course.skills.slice(0, 3).map((skill) => (
                          <Chip key={skill} label={skill} size="small" variant="outlined" />
                        ))}
                      </Box>
                      <Button fullWidth variant="contained" startIcon={<PlayIcon />}>
                        Continue
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}

        {/* Все курсы */}
        <Typography variant="h6" fontWeight={600} gutterBottom>
          All Courses ({filteredCourses.length})
        </Typography>
        <Grid container spacing={2}>
          {filteredCourses.map((course) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={course.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  opacity: course.completed ? 0.7 : 1,
                }}
              >
                {/* Бейдж завершенного курса */}
                {course.completed && (
                  <Chip
                    icon={<CompletedIcon />}
                    label="Completed"
                    color="success"
                    size="small"
                    sx={{ position: 'absolute', top: 8, right: 8, zIndex: 1 }}
                  />
                )}
                <Box
                  sx={{
                    height: 100,
                    bgcolor: course.completed ? 'success.100' : 'primary.100',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {course.completed ? (
                    <CompletedIcon sx={{ fontSize: 40, color: 'success.main' }} />
                  ) : (
                    <LearningIcon sx={{ fontSize: 40, color: 'primary.main' }} />
                  )}
                </Box>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    {course.category}
                  </Typography>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    {course.title}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <LevelIcon fontSize="small" color="action" />
                      <Typography variant="caption" sx={{ textTransform: 'capitalize' }}>
                        {course.level}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <DurationIcon fontSize="small" color="action" />
                      <Typography variant="caption">{course.duration}</Typography>
                    </Box>
                  </Box>
                  <Button
                    fullWidth
                    variant={course.completed ? 'outlined' : 'contained'}
                    size="small"
                    sx={{ mt: 1 }}
                  >
                    {course.completed ? 'Review' : course.progress ? 'Continue' : 'Start'}
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Состояние: курсы не найдены */}
        {filteredCourses.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <LearningIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              No courses found
            </Typography>
          </Box>
        )}
      </Container>
    </PageTransition>
  );
}
