import React from 'react';
import {
  Container,
  Paper,
  Typography,
  Stack,
  Box,
} from '@mui/material';
import SkillTextExplorer, {
  SkillMatchDetail,
} from '@components/SkillTextExplorer';

const SkillTextExplorerTest: React.FC = () => {
  // Sample resume text with embedded skills
  const sampleResume = `John Smith
Senior Full Stack Developer

PROFESSIONAL SUMMARY
Experienced software engineer with 7+ years of expertise in developing scalable web applications. Proficient in modern JavaScript frameworks and cloud technologies.

TECHNICAL SKILLS
• Programming Languages: JavaScript, TypeScript, Python, Java
• Frontend: React, Vue.js, Angular, HTML5, CSS3, Tailwind CSS
• Backend: Node.js, Express, Django, Spring Boot
• Databases: PostgreSQL, MongoDB, Redis, MySQL
• Cloud & DevOps: AWS, Docker, Kubernetes, Jenkins, Git
• Other: GraphQL, REST APIs, Apache Kafka, Microservices

EXPERIENCE

Senior Full Stack Developer | Tech Corp Inc.
Jan 2020 - Present
• Developed and maintained enterprise applications using React and Node.js
• Led migration from monolithic architecture to microservices
• Implemented CI/CD pipelines using Jenkins and Docker
• Optimized database queries in PostgreSQL reducing response time by 40%

Full Stack Developer | StartupXYZ
Jun 2018 - Dec 2019
• Built responsive web applications with React and TypeScript
• Developed RESTful APIs using Express and MongoDB
• Collaborated with cross-functional teams using Agile methodology
• Integrated AWS services including S3, Lambda, and RDS

Software Engineer | Digital Solutions Ltd
Aug 2016 - May 2018
• Created web applications using Angular and Java Spring Boot
• Worked with MySQL databases and wrote complex SQL queries
• Participated in code reviews and mentored junior developers

EDUCATION
Bachelor of Science in Computer Science
State University | 2016
• Dean's List, GPA: 3.8/4.0

CERTIFICATIONS
• AWS Certified Solutions Architect (2023)
• MongoDB Certified Developer (2022)
• Google Cloud Professional (2021)`;

  // Test data - various match types
  const testSkillMatches: SkillMatchDetail[] = [
    {
      skill: 'React',
      confidence: 1.0,
      match_type: 'direct',
      locations: [
        {
          text: 'React',
          start: 265,
          end: 270,
          context: '• Developed and maintained enterprise applications using React and Node.js',
        },
        {
          text: 'React',
          start: 454,
          end: 459,
          context: '• Built responsive web applications with React and TypeScript',
        },
      ],
    },
    {
      skill: 'TypeScript',
      confidence: 0.98,
      match_type: 'direct',
      locations: [
        {
          text: 'TypeScript',
          start: 130,
          end: 140,
          context: '• Programming Languages: JavaScript, TypeScript, Python, Java',
        },
        {
          text: 'TypeScript',
          start: 459,
          end: 469,
          context: '• Built responsive web applications with React and TypeScript',
        },
      ],
    },
    {
      skill: 'JavaScript',
      confidence: 0.95,
      match_type: 'direct',
      locations: [
        {
          text: 'JavaScript',
          start: 118,
          end: 128,
          context: '• Programming Languages: JavaScript, TypeScript, Python, Java',
        },
      ],
    },
    {
      skill: 'Node.js',
      confidence: 0.92,
      match_type: 'synonym',
      matched_as: 'NodeJS',
      locations: [
        {
          text: 'Node.js',
          start: 174,
          end: 180,
          context: '• Backend: Node.js, Express, Django, Spring Boot',
        },
        {
          text: 'Node.js',
          start: 282,
          end: 288,
          context: '• Developed and maintained enterprise applications using React and Node.js',
        },
      ],
    },
    {
      skill: 'PostgreSQL',
      confidence: 0.9,
      match_type: 'direct',
      locations: [
        {
          text: 'PostgreSQL',
          start: 197,
          end: 207,
          context: '• Databases: PostgreSQL, MongoDB, Redis, MySQL',
        },
        {
          text: 'PostgreSQL',
          start: 373,
          end: 383,
          context: '• Optimized database queries in PostgreSQL reducing response time by 40%',
        },
      ],
    },
    {
      skill: 'MongoDB',
      confidence: 0.88,
      match_type: 'direct',
      locations: [
        {
          text: 'MongoDB',
          start: 210,
          end: 217,
          context: '• Databases: PostgreSQL, MongoDB, Redis, MySQL',
        },
        {
          text: 'MongoDB',
          start: 517,
          end: 522,
          context: '• Developed RESTful APIs using Express and MongoDB',
        },
      ],
    },
    {
      skill: 'AWS',
      confidence: 0.85,
      match_type: 'direct',
      locations: [
        {
          text: 'AWS',
          start: 229,
          end: 232,
          context: '• Cloud & DevOps: AWS, Docker, Kubernetes, Jenkins, Git',
        },
        {
          text: 'AWS',
          start: 628,
          end: 631,
          context: '• Integrated AWS services including S3, Lambda, and RDS',
        },
      ],
    },
    {
      skill: 'Docker',
      confidence: 0.82,
      match_type: 'fuzzy',
      matched_as: 'Docker containerization',
      locations: [
        {
          text: 'Docker',
          start: 234,
          end: 240,
          context: '• Cloud & DevOps: AWS, Docker, Kubernetes, Jenkins, Git',
        },
        {
          text: 'Docker',
          start: 353,
          end: 359,
          context: '• Implemented CI/CD pipelines using Jenkins and Docker',
        },
      ],
    },
    {
      skill: 'Python',
      confidence: 0.78,
      match_type: 'context',
      matched_as: 'Python programming',
      locations: [
        {
          text: 'Python',
          start: 142,
          end: 148,
          context: '• Programming Languages: JavaScript, TypeScript, Python, Java',
        },
        {
          text: 'Python',
          start: 182,
          end: 188,
          context: '• Backend: Node.js, Express, Django, Spring Boot',
        },
      ],
    },
    {
      skill: 'GraphQL',
      confidence: 0.75,
      match_type: 'compound',
      matched_as: 'GraphQL API',
      locations: [
        {
          text: 'GraphQL',
          start: 247,
          end: 255,
          context: '• Other: GraphQL, REST APIs, Apache Kafka, Microservices',
        },
      ],
    },
  ];

  // Test case 2: High confidence matches only
  const highConfidenceMatches: SkillMatchDetail[] = testSkillMatches.filter(
    (skill) => skill.confidence >= 0.9
  );

  // Test case 3: Empty matches
  const emptyMatches: SkillMatchDetail[] = [];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={4}>
        {/* Page Header */}
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Skill Text Explorer - Component Test
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Testing the SkillTextExplorer component with various skill matches and
            scenarios
          </Typography>
        </Box>

        {/* Test Case 1: Full Resume with Mixed Matches */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 1: Full Resume with Mixed Match Types
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Complete resume with various match types (direct, synonym, fuzzy, context,
            compound) and different confidence levels. Click on highlighted skills to see
            details.
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillTextExplorer
              resumeText={sampleResume}
              skillMatches={testSkillMatches}
            />
          </Box>
        </Paper>

        {/* Test Case 2: High Confidence Matches Only */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 2: High Confidence Matches (90%+)
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Only showing skills with 90%+ confidence score
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillTextExplorer
              resumeText={sampleResume}
              skillMatches={highConfidenceMatches}
            />
          </Box>
        </Paper>

        {/* Test Case 3: No Skill Matches */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 3: No Skill Matches
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Resume text without any skill highlights
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillTextExplorer
              resumeText={sampleResume}
              skillMatches={emptyMatches}
            />
          </Box>
        </Paper>

        {/* Test Case 4: Loading State */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 4: Loading State
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Component in loading state
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillTextExplorer
              resumeText={sampleResume}
              skillMatches={[]}
              loading={true}
            />
          </Box>
        </Paper>

        {/* Test Case 5: Error State */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 5: Error State
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Component displaying an error message
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillTextExplorer
              resumeText={sampleResume}
              skillMatches={[]}
              error="Failed to load resume text"
            />
          </Box>
        </Paper>

        {/* Test Case 6: Empty Resume Text */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 6: Empty Resume Text
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Component with no resume text available
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillTextExplorer resumeText="" skillMatches={testSkillMatches} />
          </Box>
        </Paper>

        {/* Verification Checklist */}
        <Paper elevation={1} sx={{ p: 2, bgcolor: 'info.50' }}>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            Verification Checklist:
          </Typography>
          <Typography variant="body2" component="div">
            ✓ Displays resume text with highlighted skills<br />
            ✓ Skills are highlighted with different colors based on match type<br />
            ✓ Hovering over highlights displays tooltip with confidence score<br />
            ✓ Clicking a skill shows its match details in a panel<br />
            ✓ Legend shows all match types<br />
            ✓ Collapsible details panel works correctly<br />
            ✓ Loading state works correctly<br />
            ✓ Error state works correctly<br />
            ✓ Empty states work correctly<br />
            ✓ Scrollable text container for long resumes<br />
            ✓ No console errors
          </Typography>
        </Paper>
      </Stack>
    </Container>
  );
};

export default SkillTextExplorerTest;
