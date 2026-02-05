// Импорт хуков для управления состоянием
import { useState } from 'react';
// Импорт компонентов MUI для UI
import {
  Container,       // Контейнер для ограничения ширины содержимого
  Typography,      // Компонент для текста с различными стилями
  Box,             // Универсальный контейнер для верстки
  Paper,           // Контейнер с эффектом elevated (карточка)
  Grid,            // Сетка для адаптивной верстки
  TextField,       // Поле ввода текста
  Button,          // Кнопки
  Slider,          // Ползунок выбора значения
  Card,            // Карточка
  CardContent,     // Содержимое карточки
  Chip,            // Метки/теги
} from '@mui/material';
// Импорт иконок из MUI
import {
  AttachMoney as SalaryIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  LocationOn as LocationIcon,
  Work as WorkIcon,
} from '@mui/icons-material';
// Импорт MUI компонентов
import { PageTransition } from '@components/mui/PageTransition';

// Интерфейс описывающий результат расчета зарплаты
interface SalaryData {
  role: string;
  location: string;
  experience: number;
  min: number;
  max: number;
  average: number;
  currency: string;
}

// Базовые диапазоны зарплат по должностям
const salaryRanges: Record<string, { min: number; max: number; average: number }> = {
  'Software Engineer': { min: 80000, max: 180000, average: 120000 },
  'Senior Software Engineer': { min: 120000, max: 250000, average: 175000 },
  'Tech Lead': { min: 150000, max: 300000, average: 210000 },
  'Product Manager': { min: 100000, max: 200000, average: 145000 },
  'Designer': { min: 70000, max: 150000, average: 105000 },
  'Data Scientist': { min: 110000, max: 220000, average: 160000 },
  'DevOps Engineer': { min: 100000, max: 200000, average: 145000 },
};

// Список локаций с коэффициентами стоимости жизни
const locations = [
  { name: 'San Francisco, CA', multiplier: 1.4 },
  { name: 'New York, NY', multiplier: 1.3 },
  { name: 'Seattle, WA', multiplier: 1.2 },
  { name: 'Austin, TX', multiplier: 1.0 },
  { name: 'Chicago, IL', multiplier: 1.0 },
  { name: 'Remote', multiplier: 1.1 },
  { name: 'London, UK', multiplier: 0.9 },
  { name: 'Berlin, Germany', multiplier: 0.85 },
];

// Список доступных должностей
const roles = Object.keys(salaryRanges);

/**
 * Страница калькулятора зарплаты
 * Позволяет оценить рыночную стоимость на основе должности, локации и опыта
 */
export function SalaryCalculatorPage() {
  // Состояние выбранной должности
  const [role, setRole] = useState('Software Engineer');
  // Состояние выбранной локации
  const [location, setLocation] = useState(locations[4]);
  // Состояние опыта (в годах)
  const [experience, setExperience] = useState(3);
  // Состояние результата расчета
  const [result, setResult] = useState<SalaryData | null>(null);

  /**
   * Вычисление оценки зарплаты
   * Учитывает базовую зарплату, локацию и опыт
   */
  const calculateSalary = () => {
    const baseSalary = salaryRanges[role];
    // Множитель опыта: +10% за каждый год сверх первого
    const experienceMultiplier = 1 + (experience - 1) * 0.1;

    const min = Math.round(baseSalary.min * location.multiplier * experienceMultiplier);
    const max = Math.round(baseSalary.max * location.multiplier * experienceMultiplier);
    const average = Math.round(baseSalary.average * location.multiplier * experienceMultiplier);

    setResult({
      role,
      location: location.name,
      experience,
      min,
      max,
      average,
      currency: 'USD',
    });
  };

  return (
    <PageTransition>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Заголовок страницы */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <SalaryIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" fontWeight={700}>
                Salary Calculator
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Estimate your market value based on role, location, and experience
              </Typography>
            </Box>
          </Box>
        </Box>

        <Grid container spacing={3}>
          {/* Форма калькулятора */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Calculate Your Salary
              </Typography>

              <Box sx={{ mt: 3 }}>
                {/* Выбор должности */}
                <Typography variant="subtitle2" gutterBottom>
                  Role
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
                  {roles.map((r) => (
                    <Chip
                      key={r}
                      label={r}
                      onClick={() => setRole(r)}
                      color={role === r ? 'primary' : 'default'}
                      variant={role === r ? 'filled' : 'outlined'}
                    />
                  ))}
                </Box>

                {/* Выбор локации */}
                <Typography variant="subtitle2" gutterBottom>
                  Location
                </Typography>
                <TextField
                  select
                  fullWidth
                  value={location.name}
                  onChange={(e) => setLocation(locations.find((l) => l.name === e.target.value) || location)}
                  SelectProps={{ native: true }}
                  sx={{ mb: 3 }}
                >
                  {locations.map((l) => (
                    <option key={l.name} value={l.name}>
                      {l.name}
                    </option>
                  ))}
                </TextField>

                {/* Выбор опыта */}
                <Typography variant="subtitle2" gutterBottom>
                  Experience: {experience} {experience === 1 ? 'year' : 'years'}
                </Typography>
                <Slider
                  value={experience}
                  onChange={(_, value) => setExperience(value as number)}
                  min={0}
                  max={15}
                  marks
                  valueLabelDisplay="auto"
                  sx={{ mb: 3 }}
                />

                <Button fullWidth variant="contained" size="large" onClick={calculateSalary}>
                  Calculate Salary
                </Button>
              </Box>
            </Paper>
          </Grid>

          {/* Результаты расчета */}
          <Grid item xs={12} md={6}>
            {result ? (
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Salary Estimate
                </Typography>

                {/* Основная карточка с оценкой */}
                <Card sx={{ mt: 2, bgcolor: 'primary.50' }}>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Estimated Annual Salary
                    </Typography>
                    <Typography variant="h3" fontWeight={700} color="primary">
                      ${result.average.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      ${result.min.toLocaleString()} - ${result.max.toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>

                {/* Детали расчета */}
                <Grid container spacing={2} sx={{ mt: 2 }}>
                  <Grid item xs={6}>
                    <Card>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <WorkIcon fontSize="small" color="action" />
                          <Typography variant="caption" color="text.secondary">
                            Role
                          </Typography>
                        </Box>
                        <Typography variant="body2" fontWeight={600}>
                          {result.role}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6}>
                    <Card>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <LocationIcon fontSize="small" color="action" />
                          <Typography variant="caption" color="text.secondary">
                            Location
                          </Typography>
                        </Box>
                        <Typography variant="body2" fontWeight={600}>
                          {result.location}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                {/* Сравнение с рынком */}
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Market Comparison
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="body2">Below Market</Typography>
                        <Typography variant="body2" color="error">
                          ${result.min.toLocaleString()}
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          height: 8,
                          bgcolor: 'error.100',
                          borderRadius: 1,
                          overflow: 'hidden',
                        }}
                      >
                        <Box
                          sx={{
                            height: '100%',
                            width: '20%',
                            bgcolor: 'error.main',
                          }}
                        />
                      </Box>
                    </Box>
                    <Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="body2">Market Average</Typography>
                        <Typography variant="body2" color="primary">
                          ${result.average.toLocaleString()}
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          height: 8,
                          bgcolor: 'primary.100',
                          borderRadius: 1,
                          overflow: 'hidden',
                        }}
                      >
                        <Box
                          sx={{
                            height: '100%',
                            width: '50%',
                            bgcolor: 'primary.main',
                          }}
                        />
                      </Box>
                    </Box>
                    <Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="body2">Above Market</Typography>
                        <Typography variant="body2" color="success.main">
                          ${result.max.toLocaleString()}
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          height: 8,
                          bgcolor: 'success.100',
                          borderRadius: 1,
                          overflow: 'hidden',
                        }}
                      >
                        <Box
                          sx={{
                            height: '100%',
                            width: '80%',
                            bgcolor: 'success.main',
                          }}
                        />
                      </Box>
                    </Box>
                  </Box>
                </Box>

                <Button fullWidth variant="outlined" sx={{ mt: 3 }} href="/jobs">
                  Find Jobs at This Level
                </Button>
              </Paper>
            ) : (
              // Состояние: введите данные для расчета
              <Paper sx={{ p: 3, textAlign: 'center', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Box>
                  <SalaryIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    Enter your details
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Calculate your estimated salary based on market data
                  </Typography>
                </Box>
              </Paper>
            )}
          </Grid>
        </Grid>

        {/* Тренды зарплат по должностям */}
        <Paper sx={{ p: 3, mt: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Salary Trends by Role
          </Typography>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            {roles.slice(0, 4).map((r) => {
              const data = salaryRanges[r];
              return (
                <Grid item xs={12} sm={6} md={3} key={r}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                        {r}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <TrendingUpIcon fontSize="small" color="success" />
                        <Typography variant="body2" color="success.main" fontWeight={600}>
                          ${data.average.toLocaleString()}
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        ${data.min.toLocaleString()} - ${data.max.toLocaleString()}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </Paper>
      </Container>
    </PageTransition>
  );
}
