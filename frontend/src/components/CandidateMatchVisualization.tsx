import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
} from '@mui/material';
import {
  TrendingUp as TrendingIcon,
  Work as WorkIcon,
  School as SchoolIcon,
  Star as StarIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface CandidateMatchVisualizationProps {
  resumeId: string;
  skills: string[];
}

interface VacancyMatch {
  vacancyId: string;
  vacancyTitle: string;
  matchPercentage: number;
  matchedSkills: string[];
  missingSkills: string[];
  location?: string;
}

interface SkillCategory {
  category: string;
  skills: string[];
  color: string;
}

/**
 * CandidateMatchVisualization Component
 *
 * Shows job seeker visualizations including:
 * - Top matching vacancies
 * - Skills categorization
 * - Recommended positions
 */
const CandidateMatchVisualization: React.FC<CandidateMatchVisualizationProps> = ({
  resumeId,
  skills,
}) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [vacancies, setVacancies] = useState<VacancyMatch[]>([]);
  const [skillCategories, setSkillCategories] = useState<SkillCategory[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        // Fetch all vacancies
        const vacanciesResponse = await axios.get('/api/vacancies/?limit=50');
        const allVacancies = vacanciesResponse.data;

        // Get matches for all vacancies
        const matches: VacancyMatch[] = [];

        for (const vacancy of allVacancies) {
          try {
            const matchResponse = await axios.get(
              `/api/vacancies/match/${vacancy.id}?resume_id=${resumeId}`
            );

            if (matchResponse.data && matchResponse.data.match_percentage > 0) {
              matches.push({
                vacancyId: vacancy.id,
                vacancyTitle: matchResponse.data.vacancy_title || vacancy.title,
                matchPercentage: matchResponse.data.match_percentage,
                matchedSkills: (matchResponse.data.matched_skills || []).map((s: any) =>
                  typeof s === 'string' ? s : s.skill
                ),
                missingSkills: (matchResponse.data.missing_skills || []).map((s: any) =>
                  typeof s === 'string' ? s : s.skill
                ),
                location: vacancy.location,
              });
            }
          } catch (e) {
            // Skip errors
          }
        }

        // Sort by match percentage
        matches.sort((a, b) => b.matchPercentage - a.matchPercentage);
        setVacancies(matches.slice(0, 5));

        // Categorize skills
        const categories = categorizeSkills(skills);
        setSkillCategories(categories);
      } catch (error) {
        console.error('Error fetching matches:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [resumeId, skills]);

  // Simple skill categorization
  const categorizeSkills = (skillList: string[]): SkillCategory[] => {
    const categories: SkillCategory[] = [
      { category: 'Programming Languages', skills: [], color: '#1976d2' },
      { category: 'Frameworks & Libraries', skills: [], color: '#7b1fa2' },
      { category: 'Databases & Storage', skills: [], color: '#388e3c' },
      { category: 'Tools & DevOps', skills: [], color: '#f57c00' },
      { category: 'Soft Skills', skills: [], color: '#d32f2f' },
      { category: 'Other', skills: [], color: '#616161' },
    ];

    const programmingLangs = [
      'Java', 'Python', 'JavaScript', 'TypeScript', 'C#', 'C++', 'Go', 'Golang', 'Rust',
      'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'Perl', 'HTML', 'CSS',
      'SQL', 'Bash', 'Shell', 'PowerShell', 'Lua', 'Dart', 'Haskell', 'Clojure', 'Elixir',
      'Groovy', 'F#', 'Julia', 'SAS', 'Stata', 'Objective-C', 'Assembly'
    ];

    const frameworks = [
      'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'Spring', 'Spring Boot',
      'Express', 'Express.js', 'Rails', 'Ruby on Rails', 'Laravel', 'Symfony', 'jQuery',
      'Bootstrap', 'Tailwind', 'Next.js', 'Nuxt.js', 'Nuxt', 'Svelte', 'Ember', 'Backbone',
      'Hibernate', 'Entity Framework', 'ASP.NET', 'ASP.NET MVC', 'Webpack', 'Vite', 'Babel',
      'Redux', 'MobX', 'RxJS', 'jQuery', 'MUI', 'Material-UI', 'Chakra', 'Ant Design',
      'REST', 'REST API', 'RESTful', 'GraphQL', 'gRPC', 'WebSocket', 'Socket.io'
    ];

    const databases = [
      'PostgreSQL', 'MySQL', 'MongoDB', 'Oracle', 'SQLite', 'Redis',
      'Elasticsearch', 'DynamoDB', 'Cassandra', 'MariaDB', 'CouchDB', 'Neo4j',
      'InfluxDB', 'Prometheus', 'Cassandra', 'Couchbase', 'Firebase'
    ];

    const devOps = [
      'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'CI/CD', 'Git', 'Jenkins',
      'Terraform', 'Ansible', 'Linux', 'Unix', 'Nginx', 'Apache', 'Heroku',
      'Kafka', 'RabbitMQ', 'GitLab', 'GitHub', 'Bitbucket', 'Jira', 'Confluence',
      'Swagger', 'OpenAPI', 'Postman', 'GitOps', 'Vagrant', 'Puppet', 'Chef',
      'Maven', 'Gradle', 'npm', 'yarn', 'pnpm', 'pip', 'Composer', 'NuGet'
    ];

    const softSkills = [
      'Leadership', 'Communication', 'Agile', 'Scrum', 'Teamwork', 'Problem-solving',
      'Analytical', 'Management', 'Presentation', 'English', 'Negotiation', 'Mentoring',
      'Collaboration', 'Critical thinking', 'Time management', 'Adaptability'
    ];

    for (const skill of skillList) {
      const normalizedSkill = skill.trim();
      let categorized = false;

      if (programmingLangs.some((lang) => normalizedSkill.toLowerCase().includes(lang.toLowerCase()))) {
        const cat = categories.find((c) => c.category === 'Programming Languages');
        if (cat) cat.skills.push(normalizedSkill);
        categorized = true;
      }
      if (frameworks.some((fw) => normalizedSkill.toLowerCase().includes(fw.toLowerCase()))) {
        const cat = categories.find((c) => c.category === 'Frameworks & Libraries');
        if (cat) cat.skills.push(normalizedSkill);
        categorized = true;
      }
      if (databases.some((db) => normalizedSkill.toLowerCase().includes(db.toLowerCase()))) {
        const cat = categories.find((c) => c.category === 'Databases & Storage');
        if (cat) cat.skills.push(normalizedSkill);
        categorized = true;
      }
      if (devOps.some((tool) => normalizedSkill.toLowerCase().includes(tool.toLowerCase()))) {
        const cat = categories.find((c) => c.category === 'Tools & DevOps');
        if (cat) cat.skills.push(normalizedSkill);
        categorized = true;
      }
      if (softSkills.some((ss) => normalizedSkill.toLowerCase().includes(ss.toLowerCase()))) {
        const cat = categories.find((c) => c.category === 'Soft Skills');
        if (cat) cat.skills.push(normalizedSkill);
        categorized = true;
      }

      if (!categorized && normalizedSkill.length > 0) {
        const cat = categories.find((c) => c.category === 'Other');
        if (cat) cat.skills.push(normalizedSkill);
      }
    }

    return categories.filter((c) => c.skills.length > 0);
  };

  if (loading) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress size={40} />
        <Typography variant="body2" sx={{ mt: 2 }}>Analyzing matches...</Typography>
      </Paper>
    );
  }

  const getMatchColor = (percentage: number) => {
    if (percentage >= 70) return '#4caf50';
    if (percentage >= 50) return '#ff9800';
    return '#f44336';
  };

  return (
    <Box>
      {/* Recommended Positions */}
      {vacancies.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <WorkIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" fontWeight={600}>
              Recommended Positions
            </Typography>
          </Box>

          <Grid container spacing={2}>
            {vacancies.map((match, index) => (
              <Grid item xs={12} md={6} key={match.vacancyId}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    borderLeft: 4,
                    borderColor: getMatchColor(match.matchPercentage),
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    '&:hover': { boxShadow: 2, transform: 'translateY(-2px)' },
                  }}
                  onClick={() => navigate(`/compare/${resumeId}/${match.vacancyId}`)}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          {index === 0 && <StarIcon sx={{ fontSize: 16, color: '#ffc107', mr: 0.5 }} />}
                          <Typography variant="subtitle1" fontWeight={600}>
                            {match.vacancyTitle}
                          </Typography>
                        </Box>
                        {match.location && (
                          <Typography variant="caption" color="text.secondary">
                            📍 {match.location}
                          </Typography>
                        )}
                      </Box>
                      <Box
                        sx={{
                          bgcolor: `${getMatchColor(match.matchPercentage)}20`,
                          px: 2,
                          py: 1,
                          borderRadius: 1,
                          textAlign: 'center',
                          minWidth: 60,
                        }}
                      >
                        <Typography
                          variant="h6"
                          fontWeight={700}
                          sx={{ color: getMatchColor(match.matchPercentage) }}
                        >
                          {match.matchPercentage}%
                        </Typography>
                      </Box>
                    </Box>

                    {/* Match Progress Bar */}
                    <Box sx={{ mt: 2, mb: 1 }}>
                      <Box
                        sx={{
                          height: 6,
                          bgcolor: 'grey.200',
                          borderRadius: 3,
                          overflow: 'hidden',
                        }}
                      >
                        <Box
                          sx={{
                            height: '100%',
                            width: `${match.matchPercentage}%`,
                            bgcolor: getMatchColor(match.matchPercentage),
                            transition: 'width 0.5s ease',
                          }}
                        />
                      </Box>
                    </Box>

                    {/* Matched Skills Preview */}
                    {match.matchedSkills.length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" color="success.main" fontWeight={600}>
                          ✓ {match.matchedSkills.length} matched skills
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                          {match.matchedSkills.slice(0, 4).map((skill) => (
                            <Chip key={skill} label={skill} size="small" variant="outlined" sx={{ fontSize: '0.7rem', height: 20 }} />
                          ))}
                          {match.matchedSkills.length > 4 && (
                            <Chip
                              label={`+${match.matchedSkills.length - 4}`}
                              size="small"
                              variant="outlined"
                              sx={{ fontSize: '0.7rem', height: 20 }}
                            />
                          )}
                        </Box>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Skills Profile */}
      {skillCategories.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <SchoolIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" fontWeight={600}>
              Skills Profile
            </Typography>
          </Box>

          <Grid container spacing={2}>
            {skillCategories.map((cat) => (
              <Grid item xs={12} sm={6} md={4} key={cat.category}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    borderTop: 3,
                    borderColor: cat.color,
                  }}
                >
                  <CardContent>
                    <Typography variant="subtitle2" fontWeight={600} sx={{ color: cat.color, mb: 1 }}>
                      {cat.category}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {cat.skills.map((skill) => (
                        <Chip
                          key={skill}
                          label={skill}
                          size="small"
                          sx={{
                            bgcolor: `${cat.color}20`,
                            color: cat.color,
                            fontSize: '0.7rem',
                          }}
                        />
                      ))}
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      {cat.skills.length} {cat.skills.length === 1 ? 'skill' : 'skills'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Match Potential Summary */}
      {vacancies.length > 0 && vacancies[0] && (
        <Paper
          sx={{
            p: 3,
            mt: 3,
            background: (theme) =>
              `linear-gradient(135deg, ${theme.palette.primary.main}15 0%, ${theme.palette.secondary.main}15 100%)`,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            <Box>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Your Match Potential
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Based on your skills profile, you match best with {vacancies[0]?.vacancyTitle}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 3, alignItems: 'center' }}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" fontWeight={700} color="primary.main">
                  {skills?.length || 0}
                </Typography>
                <Typography variant="caption" color="text.secondary">Total Skills</Typography>
              </Box>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" fontWeight={700} color="success.main">
                  {vacancies[0]?.matchPercentage || 0}%
                </Typography>
                <Typography variant="caption" color="text.secondary">Best Match</Typography>
              </Box>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" fontWeight={700} color="info.main">
                  {vacancies.filter((v) => v.matchPercentage >= 50).length}
                </Typography>
                <Typography variant="caption" color="text.secondary">Good Matches</Typography>
              </Box>
            </Box>
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default CandidateMatchVisualization;
