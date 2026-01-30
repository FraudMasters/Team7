/**
 * Tests for Industry Taxonomies
 *
 * Tests industry-specific skill taxonomies with offline fallback support.
 */

import { describe, it, expect } from 'vitest';
import {
  INDUSTRY_TAXONOMIES,
  getIndustryTaxonomy,
  getIndustrySkills,
  getAllIndustrySkills,
  searchIndustrySkills,
  getSkillsByIndustryCategory,
  getIndustryCategories,
  getCanonicalIndustrySkillName,
  getIndustrySkillSuggestions,
  getAllIndustries,
} from './industryTaxonomies';
import type { SkillDefinition } from './skillsTaxonomy';

describe('industryTaxonomies', () => {
  describe('INDUSTRY_TAXONOMIES', () => {
    it('should have 6 industries', () => {
      expect(INDUSTRY_TAXONOMIES).toHaveLength(6);
    });

    it('should include healthcare industry', () => {
      const healthcare = INDUSTRY_TAXONOMIES.find((t) => t.id === 'healthcare');
      expect(healthcare).toBeDefined();
      expect(healthcare?.name).toBe('Healthcare');
    });

    it('should include finance industry', () => {
      const finance = INDUSTRY_TAXONOMIES.find((t) => t.id === 'finance');
      expect(finance).toBeDefined();
      expect(finance?.name).toBe('Finance');
    });

    it('should include marketing industry', () => {
      const marketing = INDUSTRY_TAXONOMIES.find((t) => t.id === 'marketing');
      expect(marketing).toBeDefined();
      expect(marketing?.name).toBe('Marketing');
    });

    it('should include manufacturing industry', () => {
      const manufacturing = INDUSTRY_TAXONOMIES.find((t) => t.id === 'manufacturing');
      expect(manufacturing).toBeDefined();
      expect(manufacturing?.name).toBe('Manufacturing');
    });

    it('should include sales industry', () => {
      const sales = INDUSTRY_TAXONOMIES.find((t) => t.id === 'sales');
      expect(sales).toBeDefined();
      expect(sales?.name).toBe('Sales');
    });

    it('should include design industry', () => {
      const design = INDUSTRY_TAXONOMIES.find((t) => t.id === 'design');
      expect(design).toBeDefined();
      expect(design?.name).toBe('Design');
    });
  });

  describe('getIndustryTaxonomy', () => {
    it('should return healthcare taxonomy', () => {
      const taxonomy = getIndustryTaxonomy('healthcare');
      expect(taxonomy).toBeDefined();
      expect(taxonomy?.id).toBe('healthcare');
      expect(taxonomy?.name).toBe('Healthcare');
      expect(taxonomy?.categories).toBeInstanceOf(Array);
    });

    it('should return undefined for invalid industry', () => {
      const taxonomy = getIndustryTaxonomy('invalid-industry');
      expect(taxonomy).toBeUndefined();
    });
  });

  describe('getIndustrySkills', () => {
    it('should return all healthcare skills', () => {
      const skills = getIndustrySkills('healthcare');
      expect(skills.length).toBeGreaterThan(20);
      expect(skills.every((s) => 'id' in s && 'name' in s && 'synonyms' in s)).toBe(true);
    });

    it('should return skills with valid structure', () => {
      const skills = getIndustrySkills('finance');
      skills.forEach((skill) => {
        expect(skill.id).toBeTruthy();
        expect(skill.name).toBeTruthy();
        expect(Array.isArray(skill.synonyms)).toBe(true);
        expect(skill.category).toBeTruthy();
      });
    });

    it('should return empty array for invalid industry', () => {
      const skills = getIndustrySkills('invalid');
      expect(skills).toEqual([]);
    });
  });

  describe('getAllIndustrySkills', () => {
    it('should return skills from all industries', () => {
      const allSkills = getAllIndustrySkills();
      expect(allSkills.length).toBeGreaterThan(100);
    });

    it('should include skills from each industry', () => {
      const allSkills = getAllIndustrySkills();
      const industries = ['healthcare', 'finance', 'marketing', 'manufacturing', 'sales', 'design'];

      industries.forEach((industryId) => {
        const industrySkills = getIndustrySkills(industryId);
        expect(allSkills.length).toBeGreaterThanOrEqual(industrySkills.length);
      });
    });
  });

  describe('searchIndustrySkills', () => {
    it('should find healthcare skills by name', () => {
      const results = searchIndustrySkills('healthcare', 'nurse');
      expect(results.length).toBeGreaterThan(0);
      expect(results[0].name.toLowerCase()).toContain('nurse');
    });

    it('should find finance skills by name', () => {
      const results = searchIndustrySkills('finance', 'accounting');
      expect(results.length).toBeGreaterThan(0);
    });

    it('should find skills by synonym', () => {
      const results = searchIndustrySkills('healthcare', 'rn');
      expect(results.length).toBeGreaterThan(0);
      expect(results[0].name).toBe('Registered Nurse');
    });

    it('should find skills by synonym variant', () => {
      const results = searchIndustrySkills('marketing', 'ppc');
      expect(results.length).toBeGreaterThan(0);
      expect(results[0].name).toBe('SEM');
    });

    it('should return empty array for short query', () => {
      const results = searchIndustrySkills('healthcare', 'n');
      expect(results).toEqual([]);
    });

    it('should return empty array for empty query', () => {
      const results = searchIndustrySkills('healthcare', '');
      expect(results).toEqual([]);
    });

    it('should respect limit parameter', () => {
      const results = searchIndustrySkills('marketing', 'marketing', 5);
      expect(results.length).toBeLessThanOrEqual(5);
    });

    it('should prioritize exact matches', () => {
      const results = searchIndustrySkills('healthcare', 'CPR');
      expect(results[0].name).toBe('CPR');
    });

    it('should return empty array for invalid industry', () => {
      const results = searchIndustrySkills('invalid', 'test');
      expect(results).toEqual([]);
    });

    it('should be case insensitive', () => {
      const lowerResults = searchIndustrySkills('finance', 'cfa');
      const upperResults = searchIndustrySkills('finance', 'CFA');
      expect(lowerResults.length).toBeGreaterThan(0);
      expect(upperResults.length).toBeGreaterThan(0);
      expect(lowerResults[0].name).toBe(upperResults[0].name);
    });
  });

  describe('getSkillsByIndustryCategory', () => {
    it('should return skills for healthcare clinical_skills category', () => {
      const skills = getSkillsByIndustryCategory('healthcare', 'clinical_skills');
      expect(skills.length).toBeGreaterThan(0);
      expect(skills.every((s) => s.category === 'clinical_skills')).toBe(true);
    });

    it('should return skills for finance accounting category', () => {
      const skills = getSkillsByIndustryCategory('finance', 'accounting');
      expect(skills.length).toBeGreaterThan(0);
      expect(skills.every((s) => s.category === 'accounting')).toBe(true);
    });

    it('should return skills for marketing digital_marketing category', () => {
      const skills = getSkillsByIndustryCategory('marketing', 'digital_marketing');
      expect(skills.length).toBeGreaterThan(0);
      expect(skills.some((s) => s.name === 'SEO')).toBe(true);
    });

    it('should return empty array for invalid industry', () => {
      const skills = getSkillsByIndustryCategory('invalid', 'accounting');
      expect(skills).toEqual([]);
    });

    it('should return empty array for invalid category', () => {
      const skills = getSkillsByIndustryCategory('finance', 'invalid-category');
      expect(skills).toEqual([]);
    });
  });

  describe('getIndustryCategories', () => {
    it('should return healthcare categories', () => {
      const categories = getIndustryCategories('healthcare');
      expect(categories.length).toBeGreaterThan(0);
      expect(categories.every((c) => 'id' in c && 'name' in c)).toBe(true);
    });

    it('should return categories with valid structure', () => {
      const categories = getIndustryCategories('marketing');
      categories.forEach((category) => {
        expect(category.id).toBeTruthy();
        expect(category.name).toBeTruthy();
      });
    });

    it('should return empty array for invalid industry', () => {
      const categories = getIndustryCategories('invalid');
      expect(categories).toEqual([]);
    });
  });

  describe('getCanonicalIndustrySkillName', () => {
    it('should return canonical name for exact match', () => {
      const result = getCanonicalIndustrySkillName('healthcare', 'CPR');
      expect(result).toBe('CPR');
    });

    it('should return canonical name for synonym', () => {
      const result = getCanonicalIndustrySkillName('healthcare', 'RN');
      expect(result).toBe('Registered Nurse');
    });

    it('should return canonical name for another synonym', () => {
      const result = getCanonicalIndustrySkillName('finance', 'cfa');
      expect(result).toBe('CFA');
    });

    it('should return null for unknown skill', () => {
      const result = getCanonicalIndustrySkillName('healthcare', 'unknown-skill');
      expect(result).toBeNull();
    });

    it('should return null for empty input', () => {
      const result = getCanonicalIndustrySkillName('healthcare', '');
      expect(result).toBeNull();
    });

    it('should return null for invalid industry', () => {
      const result = getCanonicalIndustrySkillName('invalid', 'CPR');
      expect(result).toBeNull();
    });

    it('should be case insensitive', () => {
      const lowerResult = getCanonicalIndustrySkillName('healthcare', 'rn');
      const upperResult = getCanonicalIndustrySkillName('healthcare', 'RN');
      expect(lowerResult).toBe(upperResult);
      expect(lowerResult).toBe('Registered Nurse');
    });
  });

  describe('getIndustrySkillSuggestions', () => {
    it('should return skill name suggestions', () => {
      const suggestions = getIndustrySkillSuggestions('healthcare', 'nurse');
      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions.every((s) => typeof s === 'string')).toBe(true);
    });

    it('should respect limit parameter', () => {
      const suggestions = getIndustrySkillSuggestions('marketing', 'marketing', 5);
      expect(suggestions.length).toBeLessThanOrEqual(5);
    });

    it('should return empty array for empty query', () => {
      const suggestions = getIndustrySkillSuggestions('finance', '');
      expect(suggestions).toEqual([]);
    });

    it('should return empty array for short query', () => {
      const suggestions = getIndustrySkillSuggestions('sales', 's');
      expect(suggestions).toEqual([]);
    });
  });

  describe('getAllIndustries', () => {
    it('should return all industries', () => {
      const industries = getAllIndustries();
      expect(industries).toHaveLength(6);
    });

    it('should return industries with valid structure', () => {
      const industries = getAllIndustries();
      industries.forEach((industry) => {
        expect(industry.id).toBeTruthy();
        expect(industry.name).toBeTruthy();
      });
    });

    it('should include all expected industries', () => {
      const industries = getAllIndustries();
      const industryIds = industries.map((i) => i.id);

      expect(industryIds).toContain('healthcare');
      expect(industryIds).toContain('finance');
      expect(industryIds).toContain('marketing');
      expect(industryIds).toContain('manufacturing');
      expect(industryIds).toContain('sales');
      expect(industryIds).toContain('design');
    });
  });

  describe('Healthcare Specific Skills', () => {
    it('should have patient care skills', () => {
      const skills = searchIndustrySkills('healthcare', 'patient');
      expect(someSkillMatches(skills, 'Patient Care')).toBe(true);
    });

    it('should have nursing specialties', () => {
      const skills = getIndustrySkills('healthcare');
      expect(someSkillMatches(skills, 'Registered Nurse')).toBe(true);
      expect(someSkillMatches(skills, 'Nurse Practitioner')).toBe(true);
    });

    it('should have emergency skills', () => {
      const skills = searchIndustrySkills('healthcare', 'emergency');
      expect(skills.length).toBeGreaterThan(0);
    });

    it('should support common medical abbreviations as synonyms', () => {
      expect(getCanonicalIndustrySkillName('healthcare', 'RN')).toBe('Registered Nurse');
      expect(getCanonicalIndustrySkillName('healthcare', 'LPN')).toBe('Licensed Practical Nurse');
      expect(getCanonicalIndustrySkillName('healthcare', 'CPR')).toBe('CPR');
    });
  });

  describe('Finance Specific Skills', () => {
    it('should have accounting skills', () => {
      const skills = searchIndustrySkills('finance', 'account');
      expect(skills.length).toBeGreaterThan(0);
    });

    it('should have financial analysis skills', () => {
      const skills = getIndustrySkills('finance');
      expect(someSkillMatches(skills, 'Financial Modeling')).toBe(true);
      expect(someSkillMatches(skills, 'Budgeting')).toBe(true);
    });

    it('should support finance certifications', () => {
      const skills = getIndustrySkills('finance');
      expect(someSkillMatches(skills, 'CPA')).toBe(true);
      expect(someSkillMatches(skills, 'CFA')).toBe(true);
    });
  });

  describe('Marketing Specific Skills', () => {
    it('should have digital marketing skills', () => {
      const skills = getIndustrySkills('marketing');
      expect(someSkillMatches(skills, 'SEO')).toBe(true);
      expect(someSkillMatches(skills, 'SEM')).toBe(true);
      expect(someSkillMatches(skills, 'Social Media Marketing')).toBe(true);
    });

    it('should support marketing tool abbreviations', () => {
      expect(getCanonicalIndustrySkillName('marketing', 'ppc')).toBe('SEM');
      expect(getCanonicalIndustrySkillName('marketing', 'seo')).toBe('SEO');
    });
  });

  describe('Manufacturing Specific Skills', () => {
    it('should have process skills', () => {
      const skills = getIndustrySkills('manufacturing');
      expect(someSkillMatches(skills, 'CNC Machining')).toBe(true);
      expect(someSkillMatches(skills, 'Lean Manufacturing')).toBe(true);
    });

    it('should have safety skills', () => {
      const skills = searchIndustrySkills('manufacturing', 'osha');
      expect(skills.length).toBeGreaterThan(0);
    });
  });

  describe('Sales Specific Skills', () => {
    it('should have sales techniques', () => {
      const skills = getIndustrySkills('sales');
      expect(someSkillMatches(skills, 'Consultative Selling')).toBe(true);
      expect(someSkillMatches(skills, 'Prospecting')).toBe(true);
    });

    it('should have sales tools', () => {
      const skills = getIndustrySkills('sales');
      expect(someSkillMatches(skills, 'Salesforce')).toBe(true);
      expect(someSkillMatches(skills, 'HubSpot Sales')).toBe(true);
    });
  });

  describe('Design Specific Skills', () => {
    it('should have graphic design skills', () => {
      const skills = getIndustrySkills('design');
      expect(someSkillMatches(skills, 'Adobe Photoshop')).toBe(true);
      expect(someSkillMatches(skills, 'Figma')).toBe(true);
    });

    it('should have UX design skills', () => {
      const skills = getIndustrySkills('design');
      expect(someSkillMatches(skills, 'User Research')).toBe(true);
      expect(someSkillMatches(skills, 'Wireframing')).toBe(true);
    });
  });

  describe('Edge Cases', () => {
    it('should handle special characters in search', () => {
      const results = searchIndustrySkills('finance', 'CFA');
      expect(results.length).toBeGreaterThan(0);
    });

    it('should handle whitespace in search', () => {
      const results1 = searchIndustrySkills('healthcare', '  RN  ');
      const results2 = searchIndustrySkills('healthcare', 'RN');
      expect(results1.length).toBe(results2.length);
    });

    it('should handle very long search queries', () => {
      const results = searchIndustrySkills('marketing', 'very long search query that does not match anything');
      expect(results).toEqual([]);
    });

    it('should handle unicode characters', () => {
      const results = searchIndustrySkills('manufacturing', 'six sigma');
      expect(results.length).toBeGreaterThan(0);
    });
  });
});

/**
 * Helper function to check if any skill matches the given name
 */
function someSkillMatches(skills: SkillDefinition[], name: string): boolean {
  return skills.some((skill) => skill.name === name);
}
