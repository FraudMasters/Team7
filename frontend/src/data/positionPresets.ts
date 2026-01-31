/**
 * Position presets with predefined skills and requirements
 */

export interface PositionPreset {
  id: string;
  title: string;
  category: string;
  requiredSkills: string[];
  optionalSkills: string[];
  minExperience: number; // months
  suggestedSalary?: { min: number; max: number };
  description: string;
  keywords: string[];
}

export const POSITION_PRESETS: PositionPreset[] = [
  // Backend Developers
  {
    id: 'java-senior',
    title: 'Senior Java Developer',
    category: 'backend',
    requiredSkills: ['Java', 'Spring', 'PostgreSQL', 'Docker', 'Git'],
    optionalSkills: ['Kubernetes', 'Redis', 'Kafka', 'Maven', 'JUnit', 'Microservices'],
    minExperience: 48,
    suggestedSalary: { min: 150000, max: 220000 },
    description: 'Разработка backend-систем на Java, участие в архитектурных решениях',
    keywords: ['java', 'spring', 'backend', 'jdk', 'jvm'],
  },
  {
    id: 'java-middle',
    title: 'Middle Java Developer',
    category: 'backend',
    requiredSkills: ['Java', 'Spring Boot', 'SQL', 'Git', 'Maven'],
    optionalSkills: ['PostgreSQL', 'Redis', 'Docker', 'JUnit', 'REST'],
    minExperience: 24,
    suggestedSalary: { min: 100000, max: 150000 },
    description: 'Разработка серверных приложений на Java',
    keywords: ['java', 'spring', 'backend'],
  },
  {
    id: 'python-senior',
    title: 'Senior Python Developer',
    category: 'backend',
    requiredSkills: ['Python', 'Django', 'PostgreSQL', 'Docker', 'Git'],
    optionalSkills: ['FastAPI', 'Celery', 'Redis', 'Kubernetes', 'AWS'],
    minExperience: 48,
    suggestedSalary: { min: 140000, max: 200000 },
    description: 'Backend-разработка на Python, архитектура высоконагруженных систем',
    keywords: ['python', 'django', 'flask', 'backend'],
  },
  {
    id: 'python-middle',
    title: 'Middle Python Developer',
    category: 'backend',
    requiredSkills: ['Python', 'Django', 'SQL', 'Git'],
    optionalSkills: ['Flask', 'PostgreSQL', 'Docker', 'REST API'],
    minExperience: 24,
    suggestedSalary: { min: 90000, max: 140000 },
    description: 'Разработка backend на Python/Django',
    keywords: ['python', 'django'],
  },
  {
    id: 'nodejs-senior',
    title: 'Senior Node.js Developer',
    category: 'backend',
    requiredSkills: ['JavaScript', 'Node.js', 'TypeScript', 'Express', 'MongoDB'],
    optionalSkills: ['React', 'PostgreSQL', 'Redis', 'Docker', 'GraphQL'],
    minExperience: 48,
    suggestedSalary: { min: 140000, max: 200000 },
    description: 'Full-stack разработка на Node.js',
    keywords: ['nodejs', 'javascript', 'backend'],
  },
  {
    id: 'dotnet-senior',
    title: 'Senior .NET Developer',
    category: 'backend',
    requiredSkills: ['C#', '.NET', 'ASP.NET', 'SQL Server', 'Git'],
    optionalSkills: ['Entity Framework', 'Azure', 'Docker', 'Redis', 'WCF'],
    minExperience: 48,
    suggestedSalary: { min: 140000, max: 200000 },
    description: 'Enterprise разработка на Microsoft .NET',
    keywords: ['csharp', 'dotnet', 'aspnet'],
  },
  {
    id: 'go-senior',
    title: 'Senior Go Developer',
    category: 'backend',
    requiredSkills: ['Go', 'PostgreSQL', 'Docker', 'Kubernetes', 'Git'],
    optionalSkills: ['Redis', 'Kafka', 'gRPC', 'Microservices', 'CI/CD'],
    minExperience: 36,
    suggestedSalary: { min: 150000, max: 220000 },
    description: 'Разработка высокопроизводительных сервисов на Go',
    keywords: ['go', 'golang', 'backend'],
  },

  // Frontend Developers
  {
    id: 'react-senior',
    title: 'Senior React Developer',
    category: 'frontend',
    requiredSkills: ['JavaScript', 'React', 'TypeScript', 'HTML', 'CSS'],
    optionalSkills: ['Redux', 'Next.js', 'Webpack', 'Jest', 'GraphQL'],
    minExperience: 36,
    suggestedSalary: { min: 120000, max: 180000 },
    description: 'Разработка SPA на React/Redux',
    keywords: ['react', 'javascript', 'frontend', 'redux'],
  },
  {
    id: 'vue-senior',
    title: 'Senior Vue.js Developer',
    category: 'frontend',
    requiredSkills: ['JavaScript', 'Vue.js', 'TypeScript', 'HTML', 'CSS'],
    optionalSkills: ['Vuex', 'Vue Router', 'Webpack', 'Nuxt.js'],
    minExperience: 36,
    suggestedSalary: { min: 120000, max: 170000 },
    description: 'Фронтенд-разработка на Vue.js',
    keywords: ['vue', 'javascript', 'frontend'],
  },
  {
    id: 'angular-senior',
    title: 'Senior Angular Developer',
    category: 'frontend',
    requiredSkills: ['JavaScript', 'Angular', 'TypeScript', 'RxJS', 'HTML'],
    optionalSkills: ['NgRx', 'Angular Material', 'RxJS', 'SASS'],
    minExperience: 36,
    suggestedSalary: { min: 120000, max: 180000 },
    description: 'Enterprise приложения на Angular',
    keywords: ['angular', 'javascript', 'typescript'],
  },

  // Full Stack
  {
    id: 'fullstack-senior',
    title: 'Senior Full Stack Developer',
    category: 'fullstack',
    requiredSkills: ['JavaScript', 'React', 'Node.js', 'TypeScript', 'PostgreSQL'],
    optionalSkills: ['Docker', 'AWS', 'Redis', 'GraphQL', 'Next.js'],
    minExperience: 48,
    suggestedSalary: { min: 150000, max: 220000 },
    description: 'Full-stack разработка (React + Node.js)',
    keywords: ['fullstack', 'javascript', 'react', 'nodejs'],
  },
  {
    id: 'fullstack-java',
    title: 'Java Full Stack Developer',
    category: 'fullstack',
    requiredSkills: ['Java', 'Spring', 'React', 'PostgreSQL', 'JavaScript'],
    optionalSkills: ['TypeScript', 'Docker', 'Kubernetes', 'Maven'],
    minExperience: 48,
    suggestedSalary: { min: 150000, max: 210000 },
    description: 'Full-stack на Java + React',
    keywords: ['java', 'react', 'fullstack'],
  },

  // DevOps / SRE
  {
    id: 'devops-senior',
    title: 'Senior DevOps Engineer',
    category: 'devops',
    requiredSkills: ['Docker', 'Kubernetes', 'Linux', 'AWS', 'CI/CD'],
    optionalSkills: ['Terraform', 'Ansible', 'Jenkins', 'Git', 'Python'],
    minExperience: 36,
    suggestedSalary: { min: 140000, max: 200000 },
    description: 'Инфраструктура как код, автоматизация',
    keywords: ['devops', 'docker', 'kubernetes', 'aws'],
  },
  {
    id: 'sre-senior',
    title: 'Senior SRE',
    category: 'devops',
    requiredSkills: ['Linux', 'Kubernetes', 'Go', 'Python', 'Monitoring'],
    optionalSkills: ['Prometheus', 'Grafana', 'ELK', 'Ansible'],
    minExperience: 48,
    suggestedSalary: { min: 150000, max: 220000 },
    description: 'Site Reliability Engineering',
    keywords: ['sre', 'devops', 'reliability'],
  },

  // Data Science / ML
  {
    id: 'data-scientist',
    title: 'Data Scientist',
    category: 'data',
    requiredSkills: ['Python', 'Machine Learning', 'SQL', 'Statistics'],
    optionalSkills: ['TensorFlow', 'PyTorch', 'Pandas', 'Scikit-learn', 'Jupyter'],
    minExperience: 36,
    suggestedSalary: { min: 140000, max: 200000 },
    description: 'Машинное обучение и анализ данных',
    keywords: ['python', 'ml', 'data science'],
  },
  {
    id: 'ml-engineer',
    title: 'ML Engineer',
    category: 'data',
    requiredSkills: ['Python', 'TensorFlow', 'Deep Learning', 'SQL'],
    optionalSkills: ['PyTorch', 'Keras', 'NLP', 'Computer Vision'],
    minExperience: 36,
    suggestedSalary: { min: 150000, max: 220000 },
    description: 'Production ML systems',
    keywords: ['ml', 'python', 'tensorflow'],
  },

  // Mobile
  {
    id: 'ios-senior',
    title: 'Senior iOS Developer',
    category: 'mobile',
    requiredSkills: ['Swift', 'iOS', 'SwiftUI', 'Xcode'],
    optionalSkills: ['Objective-C', 'CocoaPods', 'Combine', 'Core Data'],
    minExperience: 36,
    suggestedSalary: { min: 130000, max: 180000 },
    description: 'Разработка iOS приложений',
    keywords: ['ios', 'swift', 'mobile'],
  },
  {
    id: 'android-senior',
    title: 'Senior Android Developer',
    category: 'mobile',
    requiredSkills: ['Kotlin', 'Android', 'Android Studio', 'Java'],
    optionalSkills: ['Jetpack Compose', 'RxJava', 'Retrofit', 'Dagger'],
    minExperience: 36,
    suggestedSalary: { min: 130000, max: 180000 },
    description: 'Разработка Android приложений',
    keywords: ['android', 'kotlin', 'mobile'],
  },

  // QA
  {
    id: 'qa-automation',
    title: 'QA Automation Engineer',
    category: 'qa',
    requiredSkills: ['Java', 'Selenium', 'Test Automation', 'Git'],
    optionalSkills: ['JUnit', 'Maven', 'REST Assured', 'Jenkins', 'CI/CD'],
    minExperience: 24,
    suggestedSalary: { min: 90000, max: 140000 },
    description: 'Автоматизация тестирования',
    keywords: ['qa', 'automation', 'selenium'],
  },
  {
    id: 'qa-manual',
    title: 'QA Manual Engineer',
    category: 'qa',
    requiredSkills: ['QA', 'Manual Testing', 'Test Cases', 'Bug Tracking'],
    optionalSkills: ['SQL', 'Postman', 'JIRA', 'Git'],
    minExperience: 12,
    suggestedSalary: { min: 50000, max: 80000 },
    description: 'Ручное тестирование ПО',
    keywords: ['qa', 'testing'],
  },
];

/**
 * Get preset by position title or keyword
 */
export function findPresetByKeyword(keyword: string): PositionPreset | null {
  const normalized = keyword.toLowerCase().trim();

  return (
    POSITION_PRESETS.find((preset) => {
      return (
        preset.title.toLowerCase().includes(normalized) ||
        preset.keywords.some((kw) => kw.toLowerCase().includes(normalized))
      );
    }) || null
  );
}

/**
 * Get presets by category
 */
export function getPresetsByCategory(category: string): PositionPreset[] {
  return POSITION_PRESETS.filter((preset) => preset.category === category);
}

/**
 * Get all categories
 */
export function getCategories(): string[] {
  return Array.from(new Set(POSITION_PRESETS.map((p) => p.category)));
}

/**
 * Get suggested presets based on input
 */
export function getSuggestedPresets(input: string): PositionPreset[] {
  const normalized = input.toLowerCase().trim();

  if (!normalized) return [];

  return POSITION_PRESETS.filter((preset) => {
    return (
      preset.title.toLowerCase().includes(normalized) ||
      preset.keywords.some((kw) => kw.toLowerCase().includes(normalized))
    );
  }).slice(0, 5);
}
