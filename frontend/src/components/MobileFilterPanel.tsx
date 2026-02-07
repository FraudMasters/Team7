import React, { useState } from 'react';
import {
  Typography,
  Box,
  Paper,
  Button,
  FormControlLabel,
  Stack,
  Collapse,
  IconButton,
  Divider,
  Slider,
  Switch,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

/**
 * Education level options
 */
type EducationLevel = 'high_school' | 'bachelor' | 'master' | 'phd' | 'any';

/**
 * Search filters interface
 */
interface SearchFilters {
  skills: string[];
  minExperienceYears: number;
  maxExperienceYears: number;
  location: string;
  educationLevel: EducationLevel;
  languages: string[];
  minMatchScore: number;
  maxMatchScore: number;
  minSalaryExpectation?: number;
  maxSalaryExpectation?: number;
}

/**
 * Props for MobileFilterPanel component
 */
interface MobileFilterPanelProps {
  onApplyFilters: (filters: SearchFilters) => void;
  loading?: boolean;
  defaultFilters?: Partial<SearchFilters>;
  open?: boolean;
  onClose?: () => void;
}

/**
 * Filter section state
 */
interface FilterSectionState {
  skills: boolean;
  experience: boolean;
  location: boolean;
  education: boolean;
  languages: boolean;
  salary: boolean;
  matchScore: boolean;
}

/**
 * Mobile Filter Panel Component
 *
 * Provides mobile-optimized filtering capabilities with:
 * - Collapsible accordion sections for each filter category
 * - Touch-friendly toggles and sliders (44x44px minimum)
 * - Single-column layout optimized for mobile screens
 * - Quick filter chips for common filter combinations
 * - Clear filters functionality
 */
const MobileFilterPanel: React.FC<MobileFilterPanelProps> = ({
  onApplyFilters,
  loading = false,
  defaultFilters = {},
  open = true,
  onClose,
}) => {
  const { t } = useTranslation();

  // Filter state
  const [selectedSkills, setSelectedSkills] = useState<string[]>(defaultFilters.skills || []);
  const [minExperience, setMinExperience] = useState<number>(defaultFilters.minExperienceYears || 0);
  const [maxExperience, setMaxExperience] = useState<number>(defaultFilters.maxExperienceYears || 20);
  const [location, setLocation] = useState<string>(defaultFilters.location || '');
  const [educationLevel, setEducationLevel] = useState<EducationLevel>(
    defaultFilters.educationLevel || 'any'
  );
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>(defaultFilters.languages || []);
  const [minSalary, setMinSalary] = useState<number | undefined>(defaultFilters.minSalaryExpectation);
  const [maxSalary, setMaxSalary] = useState<number | undefined>(defaultFilters.maxSalaryExpectation);
  const [minMatchScore, setMinMatchScore] = useState<number>(defaultFilters.minMatchScore || 0);
  const [maxMatchScore, setMaxMatchScore] = useState<number>(defaultFilters.maxMatchScore || 100);

  // Accordion expansion state (all open by default on mobile)
  const [expandedSections, setExpandedSections] = useState<FilterSectionState>({
    skills: true,
    experience: true,
    location: true,
    education: true,
    languages: true,
    salary: true,
    matchScore: true,
  });

  // Available options (these could come from API in the future)
  const skillOptions = [
    'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Angular', 'Vue.js',
    'Node.js', 'Django', 'Flask', 'Spring', 'AWS', 'Azure', 'Docker', 'Kubernetes',
    'SQL', 'PostgreSQL', 'MongoDB', 'Redis', 'GraphQL', 'REST', 'Git', 'CI/CD',
  ];

  const languageOptions = [
    'English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese', 'Portuguese',
    'Russian', 'Arabic', 'Hindi', 'Italian', 'Dutch', 'Polish', 'Korean',
  ];

  const locationOptions = [
    'Remote', 'New York', 'San Francisco', 'London', 'Berlin', 'Paris',
    'Tokyo', 'Singapore', 'Sydney', 'Toronto', 'Chicago', 'Boston',
  ];

  /**
   * Toggle accordion section expansion
   */
  const toggleSection = (section: keyof FilterSectionState) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  /**
   * Toggle skill selection
   */
  const toggleSkill = (skill: string) => {
    setSelectedSkills((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]
    );
  };

  /**
   * Toggle language selection
   */
  const toggleLanguage = (language: string) => {
    setSelectedLanguages((prev) =>
      prev.includes(language) ? prev.filter((l) => l !== language) : [...prev, language]
    );
  };

  /**
   * Clear all filters
   */
  const clearFilters = () => {
    setSelectedSkills([]);
    setMinExperience(0);
    setMaxExperience(20);
    setLocation('');
    setEducationLevel('any');
    setSelectedLanguages([]);
    setMinSalary(undefined);
    setMaxSalary(undefined);
    setMinMatchScore(0);
    setMaxMatchScore(100);
  };

  /**
   * Apply filters and trigger search
   */
  const handleApplyFilters = () => {
    const filters: SearchFilters = {
      skills: selectedSkills,
      minExperienceYears: minExperience,
      maxExperienceYears: maxExperience,
      location,
      educationLevel,
      languages: selectedLanguages,
      minMatchScore,
      maxMatchScore,
      minSalaryExpectation: minSalary,
      maxSalaryExpectation: maxSalary,
    };

    onApplyFilters(filters);
    onClose?.();
  };

  /**
   * Get active filter count
   */
  const getActiveFilterCount = () => {
    let count = 0;
    if (selectedSkills.length > 0) count++;
    if (minExperience > 0 || maxExperience < 20) count++;
    if (location) count++;
    if (educationLevel !== 'any') count++;
    if (selectedLanguages.length > 0) count++;
    if (minSalary || maxSalary) count++;
    if (minMatchScore > 0 || maxMatchScore < 100) count++;
    return count;
  };

  /**
   * Render touch-friendly skill chip
   */
  const renderSkillChip = (skill: string) => {
    const isSelected = selectedSkills.includes(skill);
    return (
      <Chip
        key={skill}
        label={skill}
        onClick={() => toggleSkill(skill)}
        clickable
        color={isSelected ? 'primary' : 'default'}
        variant={isSelected ? 'filled' : 'outlined'}
        sx={{
          minHeight: 44, // Touch-friendly height
          px: 1,
          '& .MuiChip-label': {
            px: 1,
          },
        }}
      />
    );
  };

  /**
   * Render touch-friendly language chip
   */
  const renderLanguageChip = (language: string) => {
    const isSelected = selectedLanguages.includes(language);
    return (
      <Chip
        key={language}
        label={language}
        onClick={() => toggleLanguage(language)}
        clickable
        color={isSelected ? 'secondary' : 'default'}
        variant={isSelected ? 'filled' : 'outlined'}
        sx={{
          minHeight: 44, // Touch-friendly height
          px: 1,
          '& .MuiChip-label': {
            px: 1,
          },
        }}
      />
    );
  };

  const activeFilterCount = getActiveFilterCount();

  return (
    <Paper
      sx={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        top: 0,
        bgcolor: 'background.paper',
        zIndex: (theme) => theme.zIndex.drawer,
        display: open ? 'flex' : 'none',
        flexDirection: 'column',
      }}
      elevation={8}
    >
      {/* Header */}
      <Box
        sx={{
          px: 2,
          py: 2,
          bgcolor: 'primary.main',
          color: 'primary.contrastText',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Stack direction="row" spacing={2} alignItems="center">
          <FilterIcon />
          <Typography variant="h6" fontWeight={600}>
            {t('mobileFilterPanel.title')}
          </Typography>
          {activeFilterCount > 0 && (
            <Chip
              label={`${activeFilterCount} ${t('mobileFilterPanel.active')}`}
              size="small"
              color="secondary"
              sx={{
                minHeight: 28,
                bgcolor: 'secondary.main',
                color: 'secondary.contrastText',
              }}
            />
          )}
        </Stack>
        <IconButton
          size="small"
          onClick={onClose}
          sx={{ color: 'inherit', minWidth: 44, minHeight: 44 }}
        >
          <ClearIcon />
        </IconButton>
      </Box>

      {/* Filter Sections */}
      <Box sx={{ flex: 1, overflowY: 'auto', pb: 20 }}>
        {/* Skills Section */}
        <Accordion
          expanded={expandedSections.skills}
          onChange={() => toggleSection('skills')}
          elevation={0}
          sx={{ '&:before': { display: 'none' } }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{ minHeight: 56, '& .MuiAccordionSummary-content.Mui-expanded': { margin: '12px 0' } }}
          >
            <Typography variant="subtitle1" fontWeight={600}>
              {t('mobileFilterPanel.skills')}
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {skillOptions.map(renderSkillChip)}
            </Box>
          </AccordionDetails>
        </Accordion>
        <Divider />

        {/* Experience Section */}
        <Accordion
          expanded={expandedSections.experience}
          onChange={() => toggleSection('experience')}
          elevation={0}
          sx={{ '&:before': { display: 'none' } }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{ minHeight: 56, '& .MuiAccordionSummary-content.Mui-expanded': { margin: '12px 0' } }}
          >
            <Typography variant="subtitle1" fontWeight={600}>
              {t('mobileFilterPanel.experience')}
            </Typography>
            <Chip
              label={`${minExperience}-${maxExperience} ${t('mobileFilterPanel.years')}`}
              size="small"
              sx={{ ml: 1 }}
            />
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ px: 1 }}>
              <Slider
                value={[minExperience, maxExperience]}
                onChange={(_, value) => {
                  setMinExperience(value[0]);
                  setMaxExperience(value[1]);
                }}
                min={0}
                max={20}
                marks={[
                  { value: 0, label: '0' },
                  { value: 10, label: '10' },
                  { value: 20, label: '20+' },
                ]}
                valueLabelDisplay="auto"
                sx={{
                  '& .MuiSlider-thumb': {
                    width: 28,
                    height: 28, // Touch-friendly thumb
                  },
                }}
              />
            </Box>
          </AccordionDetails>
        </Accordion>
        <Divider />

        {/* Location Section */}
        <Accordion
          expanded={expandedSections.location}
          onChange={() => toggleSection('location')}
          elevation={0}
          sx={{ '&:before': { display: 'none' } }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{ minHeight: 56, '& .MuiAccordionSummary-content.Mui-expanded': { margin: '12px 0' } }}
          >
            <Typography variant="subtitle1" fontWeight={600}>
              {t('mobileFilterPanel.location')}
            </Typography>
            {location && (
              <Chip label={location} size="small" sx={{ ml: 1 }} />
            )}
          </AccordionSummary>
          <AccordionDetails>
            <Stack spacing={2}>
              <FormControl fullWidth>
                <InputLabel>{t('mobileFilterPanel.selectLocation')}</InputLabel>
                <Select
                  value={location}
                  label={t('mobileFilterPanel.selectLocation')}
                  onChange={(e) => setLocation(e.target.value)}
                  MenuProps={{
                    PaperProps: {
                      sx: {
                        maxHeight: 300,
                      },
                    },
                  }}
                >
                  <MenuItem value="">{t('mobileFilterPanel.anyLocation')}</MenuItem>
                  {locationOptions.map((loc) => (
                    <MenuItem key={loc} value={loc} sx={{ minHeight: 44 }}>
                      {loc}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Stack>
          </AccordionDetails>
        </Accordion>
        <Divider />

        {/* Education Section */}
        <Accordion
          expanded={expandedSections.education}
          onChange={() => toggleSection('education')}
          elevation={0}
          sx={{ '&:before': { display: 'none' } }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{ minHeight: 56, '& .MuiAccordionSummary-content.Mui-expanded': { margin: '12px 0' } }}
          >
            <Typography variant="subtitle1" fontWeight={600}>
              {t('mobileFilterPanel.education')}
            </Typography>
            {educationLevel !== 'any' && (
              <Chip
                label={t(`mobileFilterPanel.${educationLevel}`)}
                size="small"
                sx={{ ml: 1 }}
              />
            )}
          </AccordionSummary>
          <AccordionDetails>
            <FormControl fullWidth>
              <InputLabel>{t('mobileFilterPanel.selectEducation')}</InputLabel>
              <Select
                value={educationLevel}
                label={t('mobileFilterPanel.selectEducation')}
                onChange={(e) => setEducationLevel(e.target.value as EducationLevel)}
              >
                <MenuItem value="any" sx={{ minHeight: 44 }}>
                  {t('mobileFilterPanel.any')}
                </MenuItem>
                <MenuItem value="high_school" sx={{ minHeight: 44 }}>
                  {t('mobileFilterPanel.highSchool')}
                </MenuItem>
                <MenuItem value="bachelor" sx={{ minHeight: 44 }}>
                  {t('mobileFilterPanel.bachelor')}
                </MenuItem>
                <MenuItem value="master" sx={{ minHeight: 44 }}>
                  {t('mobileFilterPanel.master')}
                </MenuItem>
                <MenuItem value="phd" sx={{ minHeight: 44 }}>
                  {t('mobileFilterPanel.phd')}
                </MenuItem>
              </Select>
            </FormControl>
          </AccordionDetails>
        </Accordion>
        <Divider />

        {/* Languages Section */}
        <Accordion
          expanded={expandedSections.languages}
          onChange={() => toggleSection('languages')}
          elevation={0}
          sx={{ '&:before': { display: 'none' } }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{ minHeight: 56, '& .MuiAccordionSummary-content.Mui-expanded': { margin: '12px 0' } }}
          >
            <Typography variant="subtitle1" fontWeight={600}>
              {t('mobileFilterPanel.languages')}
            </Typography>
            {selectedLanguages.length > 0 && (
              <Chip
                label={`${selectedLanguages.length} ${t('mobileFilterPanel.selected')}`}
                size="small"
                sx={{ ml: 1 }}
              />
            )}
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {languageOptions.map(renderLanguageChip)}
            </Box>
          </AccordionDetails>
        </Accordion>
        <Divider />

        {/* Salary Section */}
        <Accordion
          expanded={expandedSections.salary}
          onChange={() => toggleSection('salary')}
          elevation={0}
          sx={{ '&:before': { display: 'none' } }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{ minHeight: 56, '& .MuiAccordionSummary-content.Mui-expanded': { margin: '12px 0' } }}
          >
            <Typography variant="subtitle1" fontWeight={600}>
              {t('mobileFilterPanel.salary')}
            </Typography>
            {(minSalary || maxSalary) && (
              <Chip
                label={`$${minSalary || '0'} - $${maxSalary || 'Any'}`}
                size="small"
                sx={{ ml: 1 }}
              />
            )}
          </AccordionSummary>
          <AccordionDetails>
            <Stack spacing={2}>
              <FormControl fullWidth>
                <InputLabel>{t('mobileFilterPanel.minSalary')}</InputLabel>
                <Select
                  value={minSalary || ''}
                  label={t('mobileFilterPanel.minSalary')}
                  onChange={(e) => setMinSalary(e.target.value ? parseInt(e.target.value) : undefined)}
                >
                  <MenuItem value="" sx={{ minHeight: 44 }}>
                    {t('mobileFilterPanel.any')}
                  </MenuItem>
                  <MenuItem value="30000" sx={{ minHeight: 44 }}>
                    $30,000
                  </MenuItem>
                  <MenuItem value="50000" sx={{ minHeight: 44 }}>
                    $50,000
                  </MenuItem>
                  <MenuItem value="75000" sx={{ minHeight: 44 }}>
                    $75,000
                  </MenuItem>
                  <MenuItem value="100000" sx={{ minHeight: 44 }}>
                    $100,000
                  </MenuItem>
                  <MenuItem value="150000" sx={{ minHeight: 44 }}>
                    $150,000
                  </MenuItem>
                  <MenuItem value="200000" sx={{ minHeight: 44 }}>
                    $200,000
                  </MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>{t('mobileFilterPanel.maxSalary')}</InputLabel>
                <Select
                  value={maxSalary || ''}
                  label={t('mobileFilterPanel.maxSalary')}
                  onChange={(e) => setMaxSalary(e.target.value ? parseInt(e.target.value) : undefined)}
                >
                  <MenuItem value="" sx={{ minHeight: 44 }}>
                    {t('mobileFilterPanel.any')}
                  </MenuItem>
                  <MenuItem value="50000" sx={{ minHeight: 44 }}>
                    $50,000
                  </MenuItem>
                  <MenuItem value="75000" sx={{ minHeight: 44 }}>
                    $75,000
                  </MenuItem>
                  <MenuItem value="100000" sx={{ minHeight: 44 }}>
                    $100,000
                  </MenuItem>
                  <MenuItem value="150000" sx={{ minHeight: 44 }}>
                    $150,000
                  </MenuItem>
                  <MenuItem value="200000" sx={{ minHeight: 44 }}>
                    $200,000
                  </MenuItem>
                  <MenuItem value="300000" sx={{ minHeight: 44 }}>
                    $300,000+
                  </MenuItem>
                </Select>
              </FormControl>
            </Stack>
          </AccordionDetails>
        </Accordion>
        <Divider />

        {/* Match Score Section */}
        <Accordion
          expanded={expandedSections.matchScore}
          onChange={() => toggleSection('matchScore')}
          elevation={0}
          sx={{ '&:before': { display: 'none' } }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{ minHeight: 56, '& .MuiAccordionSummary-content.Mui-expanded': { margin: '12px 0' } }}
          >
            <Typography variant="subtitle1" fontWeight={600}>
              {t('mobileFilterPanel.matchScore')}
            </Typography>
            <Chip
              label={`${minMatchScore}% - ${maxMatchScore}%`}
              size="small"
              sx={{ ml: 1 }}
            />
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ px: 1 }}>
              <Slider
                value={[minMatchScore, maxMatchScore]}
                onChange={(_, value) => {
                  setMinMatchScore(value[0]);
                  setMaxMatchScore(value[1]);
                }}
                min={0}
                max={100}
                marks={[
                  { value: 0, label: '0%' },
                  { value: 50, label: '50%' },
                  { value: 100, label: '100%' },
                ]}
                valueLabelDisplay="auto"
                sx={{
                  '& .MuiSlider-thumb': {
                    width: 28,
                    height: 28, // Touch-friendly thumb
                  },
                }}
              />
            </Box>
          </AccordionDetails>
        </Accordion>
        <Divider />
      </Box>

      {/* Footer Actions */}
      <Box
        sx={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          p: 2,
          bgcolor: 'background.paper',
          borderTop: 1,
          borderColor: 'divider',
          boxShadow: 3,
        }}
      >
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            onClick={clearFilters}
            startIcon={<ClearIcon />}
            disabled={activeFilterCount === 0}
            sx={{ minHeight: 48, flex: 1 }}
          >
            {t('mobileFilterPanel.clear')}
          </Button>
          <Button
            variant="contained"
            onClick={handleApplyFilters}
            startIcon={<CheckIcon />}
            disabled={loading}
            sx={{ minHeight: 48, flex: 1 }}
          >
            {loading ? t('mobileFilterPanel.applying') : t('mobileFilterPanel.apply')}
          </Button>
        </Stack>
      </Box>
    </Paper>
  );
};

export default MobileFilterPanel;
