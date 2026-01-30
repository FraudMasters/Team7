/**
 * Skills taxonomy with synonyms and autocomplete support
 */

export interface SkillCategory {
  id: string;
  name: string;
  skills: SkillDefinition[];
}

export interface SkillDefinition {
  id: string;
  name: string;
  synonyms: string[];
  category: string;
}

export const SKILLS_TAXONOMY: SkillCategory[] = [
  {
    id: 'programming_languages',
    name: 'Языки программирования',
    skills: [
      { id: 'python', name: 'Python', synonyms: ['py', 'python3'], category: 'programming_languages' },
      { id: 'java', name: 'Java', synonyms: ['JAVA', 'jdk', 'jvm'], category: 'programming_languages' },
      { id: 'javascript', name: 'JavaScript', synonyms: ['JS', 'ECMAScript', 'js'], category: 'programming_languages' },
      { id: 'csharp', name: 'C#', synonyms: ['CSharp', 'dotnet', '.net'], category: 'programming_languages' },
      { id: 'cpp', name: 'C++', synonyms: ['C plus plus', 'Cpp'], category: 'programming_languages' },
      { id: 'php', name: 'PHP', synonyms: ['Hypertext Preprocessor'], category: 'programming_languages' },
      { id: 'go', name: 'Go', synonyms: ['Golang'], category: 'programming_languages' },
      { id: 'ruby', name: 'Ruby', synonyms: [], category: 'programming_languages' },
      { id: 'typescript', name: 'TypeScript', synonyms: ['TS'], category: 'programming_languages' },
      { id: 'kotlin', name: 'Kotlin', synonyms: [], category: 'programming_languages' },
      { id: 'swift', name: 'Swift', synonyms: [], category: 'programming_languages' },
      { id: 'rust', name: 'Rust', synonyms: [], category: 'programming_languages' },
      { id: 'scala', name: 'Scala', synonyms: [], category: 'programming_languages' },
      { id: 'r', name: 'R', synonyms: ['R language'], category: 'programming_languages' },
    ],
  },
  {
    id: 'frameworks',
    name: 'Фреймворки и библиотеки',
    skills: [
      { id: 'angular', name: 'Angular', synonyms: ['AngularJS', 'Angular 2+'], category: 'frameworks' },
      { id: 'react', name: 'React', synonyms: ['ReactJS', 'React.js', 'reactjs'], category: 'frameworks' },
      { id: 'vue', name: 'Vue.js', synonyms: ['Vue', 'VueJS', 'View.js'], category: 'frameworks' },
      { id: 'aspnet', name: 'ASP.NET', synonyms: ['Asp.Net'], category: 'frameworks' },
      { id: 'mvc', name: 'MVC', synonyms: ['Model-View-Controller'], category: 'frameworks' },
      { id: 'jquery', name: 'jQuery', synonyms: ['JQuery'], category: 'frameworks' },
      { id: 'entity_framework', name: 'Entity Framework', synonyms: ['EF', 'EntityFramework'], category: 'frameworks' },
      { id: 'web_api', name: 'ASP.NET Web API', synonyms: ['Web API'], category: 'frameworks' },
      { id: 'wcf', name: 'WCF', synonyms: ['Windows Communication Foundation'], category: 'frameworks' },
      { id: 'spring', name: 'Spring', synonyms: ['Spring Boot', 'Spring Framework'], category: 'frameworks' },
      { id: 'django', name: 'Django', synonyms: [], category: 'frameworks' },
      { id: 'flask', name: 'Flask', synonyms: [], category: 'frameworks' },
      { id: 'express', name: 'Express.js', synonyms: ['Express'], category: 'frameworks' },
      { id: 'laravel', name: 'Laravel', synonyms: [], category: 'frameworks' },
      { id: 'symfony', name: 'Symfony', synonyms: [], category: 'frameworks' },
      { id: 'rails', name: 'Ruby on Rails', synonyms: ['Rails'], category: 'frameworks' },
      { id: 'nextjs', name: 'Next.js', synonyms: ['Nextjs'], category: 'frameworks' },
      { id: 'nuxtjs', name: 'Nuxt.js', synonyms: ['Nuxtjs'], category: 'frameworks' },
    ],
  },
  {
    id: 'databases',
    name: 'Базы данных',
    skills: [
      { id: 'sql', name: 'SQL', synonyms: ['MySQL', 'MySql', 'PostgreSQL', 'Postgres', 'PG', 'SQLite', 'SQLite3'], category: 'databases' },
      { id: 'mysql', name: 'MySQL', synonyms: ['MySql'], category: 'databases' },
      { id: 'postgresql', name: 'PostgreSQL', synonyms: ['Postgres', 'PG'], category: 'databases' },
      { id: 'mariadb', name: 'MariaDB', synonyms: [], category: 'databases' },
      { id: 'mssql', name: 'MS SQL Server', synonyms: ['MSSQL', 'Microsoft SQL Server', 'SQL Server'], category: 'databases' },
      { id: 'oracle', name: 'Oracle', synonyms: ['Oracle Database'], category: 'databases' },
      { id: 'mongodb', name: 'MongoDB', synonyms: ['Mongo'], category: 'databases' },
      { id: 'redis', name: 'Redis', synonyms: [], category: 'databases' },
      { id: 'elasticsearch', name: 'Elasticsearch', synonyms: ['Elastic Search', 'ES'], category: 'databases' },
      { id: 'cassandra', name: 'Cassandra', synonyms: [], category: 'databases' },
      { id: 'dynamodb', name: 'DynamoDB', synonyms: [], category: 'databases' },
    ],
  },
  {
    id: 'devops',
    name: 'DevOps и инструменты',
    skills: [
      { id: 'docker', name: 'Docker', synonyms: [], category: 'devops' },
      { id: 'kubernetes', name: 'Kubernetes', synonyms: ['K8s', 'k8s'], category: 'devops' },
      { id: 'jenkins', name: 'Jenkins', synonyms: [], category: 'devops' },
      { id: 'git', name: 'Git', synonyms: [], category: 'devops' },
      { id: 'aws', name: 'AWS', synonyms: ['Amazon Web Services'], category: 'devops' },
      { id: 'azure', name: 'Azure', synonyms: ['Microsoft Azure'], category: 'devops' },
      { id: 'gcp', name: 'GCP', synonyms: ['Google Cloud Platform', 'Google Cloud'], category: 'devops' },
      { id: 'terraform', name: 'Terraform', synonyms: [], category: 'devops' },
      { id: 'ansible', name: 'Ansible', synonyms: [], category: 'devops' },
      { id: 'ci_cd', name: 'CI/CD', synonyms: ['Continuous Integration', 'Continuous Deployment', 'continuous integration', 'continuous deployment'], category: 'devops' },
      { id: 'linux', name: 'Linux', synonyms: ['Unix', 'UNIX'], category: 'devops' },
      { id: 'ubuntu', name: 'Ubuntu', synonyms: [], category: 'devops' },
      { id: 'centos', name: 'CentOS', synonyms: [], category: 'devops' },
      { id: 'redhat', name: 'Red Hat', synonyms: ['RHEL'], category: 'devops' },
      { id: 'helm', name: 'Helm', synonyms: [], category: 'devops' },
      { id: 'prometheus', name: 'Prometheus', synonyms: [], category: 'devops' },
      { id: 'grafana', name: 'Grafana', synonyms: [], category: 'devops' },
      { id: 'elk', name: 'ELK Stack', synonyms: ['Elasticsearch', 'Logstash', 'Kibana'], category: 'devops' },
    ],
  },
  {
    id: 'testing',
    name: 'Тестирование',
    skills: [
      { id: 'junit', name: 'JUnit', synonyms: [], category: 'testing' },
      { id: 'selenium', name: 'Selenium', synonyms: [], category: 'testing' },
      { id: 'testng', name: 'TestNG', synonyms: [], category: 'testing' },
      { id: 'jest', name: 'Jest', synonyms: [], category: 'testing' },
      { id: 'mocha', name: 'Mocha', synonyms: [], category: 'testing' },
      { id: 'cypress', name: 'Cypress', synonyms: [], category: 'testing' },
      { id: 'pytest', name: 'Pytest', synonyms: [], category: 'testing' },
      { id: 'tdd', name: 'TDD', synonyms: ['Test Driven Development'], category: 'testing' },
      { id: 'bdd', name: 'BDD', synonyms: ['Behavior Driven Development'], category: 'testing' },
    ],
  },
  {
    id: 'methodologies',
    name: 'Методологии',
    skills: [
      { id: 'agile', name: 'Agile', synonyms: ['Agile/Scrum'], category: 'methodologies' },
      { id: 'scrum', name: 'Scrum', synonyms: [], category: 'methodologies' },
      { id: 'kanban', name: 'Kanban', synonyms: [], category: 'methodologies' },
      { id: 'devops', name: 'DevOps', synonyms: [], category: 'methodologies' },
      { id: 'microservices', name: 'Microservices', synonyms: ['Micro-service Architectures'], category: 'methodologies' },
      { id: 'oop', name: 'OOP', synonyms: ['Object Oriented Programming'], category: 'methodologies' },
      { id: 'solid', name: 'SOLID', synonyms: [], category: 'methodologies' },
      { id: 'rest', name: 'REST', synonyms: ['RESTful', 'REST APIs', 'RESTful APIs', 'rest api'], category: 'methodologies' },
      { id: 'soap', name: 'SOAP', synonyms: [], category: 'methodologies' },
      { id: 'graphql', name: 'GraphQL', synonyms: [], category: 'methodologies' },
    ],
  },
  {
    id: 'web',
    name: 'Web технологии',
    skills: [
      { id: 'html', name: 'HTML', synonyms: ['HTML5'], category: 'web' },
      { id: 'css', name: 'CSS', synonyms: ['CSS3'], category: 'web' },
      { id: 'http', name: 'HTTP', synonyms: ['HTTPS'], category: 'web' },
      { id: 'web_sockets', name: 'WebSockets', synonyms: ['Web Sockets'], category: 'web' },
      { id: 'oauth', name: 'OAuth', synonyms: ['OAuth2'], category: 'web' },
      { id: 'jwt', name: 'JWT', synonyms: ['JSON Web Tokens'], category: 'web' },
      { id: 'sass', name: 'SASS', synonyms: ['SCSS'], category: 'web' },
      { id: 'webpack', name: 'Webpack', synonyms: [], category: 'web' },
      { id: 'vite', name: 'Vite', synonyms: [], category: 'web' },
      { id: 'babel', name: 'Babel', synonyms: [], category: 'web' },
    ],
  },
  {
    id: 'messaging',
    name: 'Месседжинг и очереди',
    skills: [
      { id: 'rabbitmq', name: 'RabbitMQ', synonyms: [], category: 'messaging' },
      { id: 'kafka', name: 'Kafka', synonyms: ['Apache Kafka'], category: 'messaging' },
      { id: 'activemq', name: 'ActiveMQ', synonyms: [], category: 'messaging' },
      { id: 'zeromq', name: 'ZeroMQ', synonyms: [], category: 'messaging' },
      { id: 'redis_pubsub', name: 'Redis Pub/Sub', synonyms: [], category: 'messaging' },
      { id: 'aws_sqs', name: 'AWS SQS', synonyms: [], category: 'messaging' },
      { id: 'aws_sns', name: 'AWS SNS', synonyms: [], category: 'messaging' },
    ],
  },
  {
    id: 'data_science',
    name: 'Data Science',
    skills: [
      { id: 'pandas', name: 'Pandas', synonyms: [], category: 'data_science' },
      { id: 'numpy', name: 'NumPy', synonyms: [], category: 'data_science' },
      { id: 'tensorflow', name: 'TensorFlow', synonyms: [], category: 'data_science' },
      { id: 'pytorch', name: 'PyTorch', synonyms: [], category: 'data_science' },
      { id: 'scikit_learn', name: 'Scikit-learn', synonyms: ['sklearn'], category: 'data_science' },
      { id: 'jupyter', name: 'Jupyter', synonyms: ['Jupyter Notebook'], category: 'data_science' },
      { id: 'matplotlib', name: 'Matplotlib', synonyms: [], category: 'data_science' },
      { id: 'nlp', name: 'NLP', synonyms: ['Natural Language Processing'], category: 'data_science' },
    ],
  },
];

/**
 * Flatten all skills with synonyms for autocomplete
 */
export function getAllSkills(): SkillDefinition[] {
  const allSkills: SkillDefinition[] = [];

  SKILLS_TAXONOMY.forEach((category) => {
    category.skills.forEach((skill) => {
      allSkills.push(skill);
    });
  });

  return allSkills;
}

/**
 * Search skills by input (supports synonyms)
 */
export function searchSkills(query: string, limit = 20): SkillDefinition[] {
  if (!query || query.length < 2) return [];

  const normalized = query.toLowerCase().trim();
  const allSkills = getAllSkills();

  const matches = allSkills.filter((skill) => {
    // Check exact name match
    if (skill.name.toLowerCase().includes(normalized)) {
      return true;
    }

    // Check synonyms
    return skill.synonyms.some((synonym) =>
      synonym.toLowerCase().includes(normalized)
    );
  });

  // Sort by relevance (exact name match first)
  matches.sort((a, b) => {
    const aExact = a.name.toLowerCase() === normalized;
    const bExact = b.name.toLowerCase() === normalized;

    if (aExact && !bExact) return -1;
    if (!aExact && bExact) return 1;

    return 0;
  });

  return matches.slice(0, limit);
}

/**
 * Get canonical skill name (handles synonyms)
 */
export function getCanonicalSkillName(input: string): string | null {
  if (!input) return null;

  const normalized = input.toLowerCase().trim();
  const allSkills = getAllSkills();

  for (const skill of allSkills) {
    // Exact name match
    if (skill.name.toLowerCase() === normalized) {
      return skill.name;
    }

    // Synonym match
    if (skill.synonyms.some((s) => s.toLowerCase() === normalized)) {
      return skill.name;
    }
  }

  return null; // Not found, return as-is
}

/**
 * Get skill suggestions based on partial input
 */
export function getSkillSuggestions(input: string): string[] {
  const matches = searchSkills(input, 10);
  return matches.map((m) => m.name);
}

/**
 * Get skills by category
 */
export function getSkillsByCategory(categoryId: string): SkillDefinition[] {
  const category = SKILLS_TAXONOMY.find((c) => c.id === categoryId);
  return category?.skills || [];
}

/**
 * Get all categories
 */
export function getAllCategories(): { id: string; name: string }[] {
  return SKILLS_TAXONOMY.map((c) => ({
    id: c.id,
    name: c.name,
  }));
}

/**
 * Merged taxonomy search options
 */
export interface MergedSearchOptions {
  industry?: string;
  organizationId?: string;
  limit?: number;
}

/**
 * Search skills across all taxonomy sources (static + industry + custom)
 *
 * This function uses the taxonomies API client to fetch merged taxonomies
 * including static skills, industry-specific skills, and custom organization
 * synonyms. Falls back to static-only search if API is unavailable.
 *
 * @param query - Search query string
 * @param options - Search options including industry and organization ID
 * @returns Matching skills sorted by relevance
 */
export async function searchSkillsMerged(
  query: string,
  options: MergedSearchOptions = {}
): Promise<SkillDefinition[]> {
  // Dynamic import to avoid circular dependencies
  const { taxonomiesClient } = await import('@/api/taxonomies');

  try {
    return await taxonomiesClient.searchSkills(query, options);
  } catch (error) {
    // Fallback to static-only search if API fails
    return searchSkills(query, options.limit);
  }
}

/**
 * Get canonical skill name from merged taxonomies
 *
 * This function checks all taxonomy sources (static, industry, custom)
 * to find the canonical name for a given skill or synonym.
 *
 * @param input - User input skill name
 * @param options - Search options including industry and organization ID
 * @returns Canonical skill name or null if not found
 */
export async function getCanonicalSkillNameMerged(
  input: string,
  options: MergedSearchOptions = {}
): Promise<string | null> {
  if (!input) return null;

  // Dynamic import to avoid circular dependencies
  const { taxonomiesClient } = await import('@/api/taxonomies');

  try {
    return await taxonomiesClient.getCanonicalSkillName(input, options);
  } catch (error) {
    // Fallback to static-only canonical lookup
    return getCanonicalSkillName(input);
  }
}

/**
 * Get skill suggestions from merged taxonomies
 *
 * @param input - Partial skill input
 * @param options - Search options
 * @returns Array of suggested skill names
 */
export async function getSkillSuggestionsMerged(
  input: string,
  options: MergedSearchOptions = {}
): Promise<string[]> {
  const matches = await searchSkillsMerged(input, options);
  return matches.map((m) => m.name);
}
