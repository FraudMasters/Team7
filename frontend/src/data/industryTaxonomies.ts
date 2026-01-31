/**
 * Industry-specific skill taxonomies with synonyms and autocomplete support
 * Provides offline fallback data for auto-suggest functionality
 */

import { SkillDefinition, SkillCategory } from './skillsTaxonomy';

export interface IndustryTaxonomy {
  id: string;
  name: string;
  categories: SkillCategory[];
}

/**
 * Healthcare Industry Taxonomy
 */
const HEALTHCARE_TAXONOMY: IndustryTaxonomy = {
  id: 'healthcare',
  name: 'Healthcare',
  categories: [
    {
      id: 'clinical_skills',
      name: 'Clinical Skills',
      skills: [
        { id: 'patient_care', name: 'Patient Care', synonyms: ['Clinical Care', 'Direct Patient Care'], category: 'clinical_skills' },
        { id: 'patient_assessment', name: 'Patient Assessment', synonyms: ['Clinical Assessment', 'Health Assessment', 'Physical Examination', 'Triage'], category: 'clinical_skills' },
        { id: 'vital_signs', name: 'Vital Signs Monitoring', synonyms: ['Vitals', 'Patient Vitals', 'Blood Pressure Monitoring'], category: 'clinical_skills' },
        { id: 'wound_care', name: 'Wound Care', synonyms: ['Wound Management', 'Dressing Changes', 'Incision Care'], category: 'clinical_skills' },
        { id: 'medication_admin', name: 'Medication Administration', synonyms: ['Medication Management', 'Drug Administration', 'Pharmacology'], category: 'clinical_skills' },
        { id: 'iv_therapy', name: 'IV Therapy', synonyms: ['Intravenous Therapy', 'IV Insertion', 'IV Maintenance'], category: 'clinical_skills' },
        { id: 'phlebotomy', name: 'Phlebotomy', synonyms: ['Blood Draw', 'Blood Collection', 'Venipuncture', 'Specimen Collection'], category: 'clinical_skills' },
        { id: 'cpr', name: 'CPR', synonyms: ['Cardiopulmonary Resuscitation', 'BLS', 'Basic Life Support'], category: 'clinical_skills' },
        { id: 'acls', name: 'ACLS', synonyms: ['Advanced Cardiac Life Support'], category: 'clinical_skills' },
        { id: 'bls', name: 'BLS', synonyms: ['Basic Life Support'], category: 'clinical_skills' },
        { id: 'emergencry_response', name: 'Emergency Response', synonyms: ['Emergency Care', 'Crisis Intervention'], category: 'clinical_skills' },
        { id: 'infection_control', name: 'Infection Control', synonyms: ['Infection Prevention', 'Sterile Techniques'], category: 'clinical_skills' },
      ],
    },
    {
      id: 'nursing_specialties',
      name: 'Nursing Specialties',
      skills: [
        { id: 'registered_nurse', name: 'Registered Nurse', synonyms: ['RN', 'R.N.', 'Staff Nurse'], category: 'nursing_specialties' },
        { id: 'licensed_practical_nurse', name: 'Licensed Practical Nurse', synonyms: ['LPN', 'L.V.N.', 'Licensed Vocational Nurse'], category: 'nursing_specialties' },
        { id: 'nurse_practitioner', name: 'Nurse Practitioner', synonyms: ['NP', 'A.P.R.N.', 'Advanced Practice RN'], category: 'nursing_specialties' },
        { id: 'critical_care_nursing', name: 'Critical Care Nursing', synonyms: ['ICU Nursing', 'Intensive Care Nursing'], category: 'nursing_specialties' },
        { id: 'er_nursing', name: 'Emergency Room Nursing', synonyms: ['ED Nursing', 'Emergency Department Nursing'], category: 'nursing_specialties' },
        { id: 'or_nursing', name: 'Operating Room Nursing', synonyms: ['OR Nursing', 'Perioperative Nursing', 'Surgical Nursing'], category: 'nursing_specialties' },
        { id: 'pediatric_nursing', name: 'Pediatric Nursing', synonyms: ['Peds Nursing', 'Child Health Nursing'], category: 'nursing_specialties' },
        { id: 'geriatric_nursing', name: 'Geriatric Nursing', synonyms: ['Elder Care Nursing', 'Senior Care'], category: 'nursing_specialties' },
        { id: 'oncology_nursing', name: 'Oncology Nursing', synonyms: ['Cancer Care Nursing'], category: 'nursing_specialties' },
        { id: 'labor_delivery', name: 'Labor and Delivery', synonyms: ['L&D Nursing', 'OB Nursing', 'Obstetrics'], category: 'nursing_specialties' },
      ],
    },
    {
      id: 'medical_terminology',
      name: 'Medical Terminology & Documentation',
      skills: [
        { id: 'medical_terminology', name: 'Medical Terminology', synonyms: ['Medical Terms', 'Clinical Terminology'], category: 'medical_terminology' },
        { id: 'electronic_health_records', name: 'Electronic Health Records', synonyms: ['EHR', 'EMR', 'Electronic Medical Records', 'Epic', 'Cerner'], category: 'medical_terminology' },
        { id: 'medical_charting', name: 'Medical Charting', synonyms: ['Patient Charting', 'Documentation', 'Nursing Notes'], category: 'medical_terminology' },
        { id: 'hipaa', name: 'HIPAA Compliance', synonyms: ['Patient Privacy', 'Healthcare Privacy', 'PHI Protection'], category: 'medical_terminology' },
        { id: 'icd_10', name: 'ICD-10 Coding', synonyms: ['Medical Coding', 'Diagnosis Coding'], category: 'medical_terminology' },
        { id: 'cpt_coding', name: 'CPT Coding', synonyms: ['Procedure Coding', 'Current Procedural Terminology'], category: 'medical_terminology' },
      ],
    },
  ],
};

/**
 * Finance Industry Taxonomy
 */
const FINANCE_TAXONOMY: IndustryTaxonomy = {
  id: 'finance',
  name: 'Finance',
  categories: [
    {
      id: 'accounting',
      name: 'Accounting',
      skills: [
        { id: 'financial_accounting', name: 'Financial Accounting', synonyms: ['GAAP', 'Financial Reporting', 'General Ledger'], category: 'accounting' },
        { id: 'managerial_accounting', name: 'Managerial Accounting', synonyms: ['Cost Accounting', 'Management Accounting'], category: 'accounting' },
        { id: 'accounts_payable', name: 'Accounts Payable', synonyms: ['AP', 'Vendor Payments', 'Payables'], category: 'accounting' },
        { id: 'accounts_receivable', name: 'Accounts Receivable', synonyms: ['AR', 'Billing', 'Receivables'], category: 'accounting' },
        { id: 'reconciliation', name: 'Reconciliation', synonyms: ['Bank Reconciliation', 'Account Reconciliation'], category: 'accounting' },
        { id: 'financial_statements', name: 'Financial Statements', synonyms: ['Balance Sheet', 'Income Statement', 'Cash Flow'], category: 'accounting' },
        { id: 'audit', name: 'Audit', synonyms: ['Auditing', 'Internal Audit', 'External Audit'], category: 'accounting' },
        { id: 'tax_accounting', name: 'Tax Accounting', synonyms: ['Tax Preparation', 'Tax Compliance'], category: 'accounting' },
      ],
    },
    {
      id: 'financial_analysis',
      name: 'Financial Analysis',
      skills: [
        { id: 'financial_modeling', name: 'Financial Modeling', synonyms: ['Financial Analysis', 'Excel Modeling'], category: 'financial_analysis' },
        { id: 'budgeting', name: 'Budgeting', synonyms: ['Budget Management', 'Financial Planning'], category: 'financial_analysis' },
        { id: 'forecasting', name: 'Forecasting', synonyms: ['Financial Forecasting', 'Revenue Forecasting'], category: 'financial_analysis' },
        { id: 'variance_analysis', name: 'Variance Analysis', synonyms: ['Budget Variance', 'Performance Analysis'], category: 'financial_analysis' },
        { id: 'ratio_analysis', name: 'Ratio Analysis', synonyms: ['Financial Ratios', 'KPI Analysis'], category: 'financial_analysis' },
        { id: 'valuation', name: 'Valuation', synonyms: ['Business Valuation', 'Asset Valuation', 'DCF'], category: 'financial_analysis' },
        { id: 'investment_analysis', name: 'Investment Analysis', synonyms: ['Portfolio Analysis', 'Securities Analysis'], category: 'financial_analysis' },
      ],
    },
    {
      id: 'finance_certifications',
      name: 'Certifications & Compliance',
      skills: [
        { id: 'cpa', name: 'CPA', synonyms: ['Certified Public Accountant'], category: 'finance_certifications' },
        { id: 'cfa', name: 'CFA', synonyms: ['Chartered Financial Analyst'], category: 'finance_certifications' },
        { id: 'cma', name: 'CMA', synonyms: ['Certified Management Accountant'], category: 'finance_certifications' },
        { id: 'series_7', name: 'Series 7', synonyms: ['General Securities Representative'], category: 'finance_certifications' },
        { id: 'series_63', name: 'Series 63', synonyms: ['Uniform Securities Agent'], category: 'finance_certifications' },
        { id: 'sec_compliance', name: 'SEC Compliance', synonyms: ['Regulatory Compliance', 'Securities Compliance'], category: 'finance_certifications' },
        { id: 'sox_compliance', name: 'Sarbanes-Oxley', synonyms: ['SOX', 'Sarbanes Oxley Compliance'], category: 'finance_certifications' },
        { id: 'anti_money_laundering', name: 'AML', synonyms: ['Anti-Money Laundering', 'KYC', 'Know Your Customer'], category: 'finance_certifications' },
      ],
    },
  ],
};

/**
 * Marketing Industry Taxonomy
 */
const MARKETING_TAXONOMY: IndustryTaxonomy = {
  id: 'marketing',
  name: 'Marketing',
  categories: [
    {
      id: 'digital_marketing',
      name: 'Digital Marketing',
      skills: [
        { id: 'seo', name: 'SEO', synonyms: ['Search Engine Optimization', 'Organic Search'], category: 'digital_marketing' },
        { id: 'sem', name: 'SEM', synonyms: ['PPC', 'Google Ads', 'Search Engine Marketing', 'Paid Search'], category: 'digital_marketing' },
        { id: 'social_media_marketing', name: 'Social Media Marketing', synonyms: ['SMM', 'Social Media Management'], category: 'digital_marketing' },
        { id: 'email_marketing', name: 'Email Marketing', synonyms: ['Email Campaigns', 'Newsletter Marketing'], category: 'digital_marketing' },
        { id: 'content_marketing', name: 'Content Marketing', synonyms: ['Content Strategy', 'Content Creation'], category: 'digital_marketing' },
        { id: 'affiliate_marketing', name: 'Affiliate Marketing', synonyms: ['Partner Marketing', 'Referral Marketing'], category: 'digital_marketing' },
        { id: 'inbound_marketing', name: 'Inbound Marketing', synonyms: ['Demand Generation', 'Lead Generation'], category: 'digital_marketing' },
        { id: 'marketing_automation', name: 'Marketing Automation', synonyms: ['HubSpot', 'Marketo', 'Pardot', 'Eloqua'], category: 'digital_marketing' },
        { id: 'web_analytics', name: 'Web Analytics', synonyms: ['Google Analytics', 'GA4', 'Adobe Analytics'], category: 'digital_marketing' },
        { id: 'conversion_optimization', name: 'CRO', synonyms: ['Conversion Rate Optimization', 'A/B Testing'], category: 'digital_marketing' },
      ],
    },
    {
      id: 'marketing_tools',
      name: 'Marketing Tools & Platforms',
      skills: [
        { id: 'google_ads', name: 'Google Ads', synonyms: ['AdWords', 'Google AdWords'], category: 'marketing_tools' },
        { id: 'facebook_ads', name: 'Facebook Ads', synonyms: ['Meta Ads', 'Instagram Ads', 'Social Advertising'], category: 'marketing_tools' },
        { id: 'linkedin_ads', name: 'LinkedIn Ads', synonyms: ['B2B Advertising', 'LinkedIn Marketing'], category: 'marketing_tools' },
        { id: 'mailchimp', name: 'Mailchimp', synonyms: ['Email Marketing Platforms', 'Constant Contact'], category: 'marketing_tools' },
        { id: 'hubspot', name: 'HubSpot', synonyms: ['Inbound Marketing Software', 'CRM Marketing'], category: 'marketing_tools' },
        { id: 'google_analytics', name: 'Google Analytics', synonyms: ['GA', 'GA4', 'Analytics'], category: 'marketing_tools' },
        { id: 'search_console', name: 'Google Search Console', synonyms: ['GSC', 'Webmaster Tools'], category: 'marketing_tools' },
        { id: 'semrush', name: 'SEMrush', synonyms: ['SEO Tools', 'Ahrefs', 'Moz'], category: 'marketing_tools' },
        { id: 'hootsuite', name: 'Hootsuite', synonyms: ['Social Media Management Tools', 'Buffer', 'Sprout Social'], category: 'marketing_tools' },
        { id: 'canva', name: 'Canva', synonyms: ['Graphic Design Tools', 'Design Software'], category: 'marketing_tools' },
      ],
    },
    {
      id: 'marketing_strategy',
      name: 'Marketing Strategy',
      skills: [
        { id: 'brand_management', name: 'Brand Management', synonyms: ['Branding', 'Brand Strategy'], category: 'marketing_strategy' },
        { id: 'market_research', name: 'Market Research', synonyms: ['Consumer Research', 'Market Analysis'], category: 'marketing_strategy' },
        { id: 'competitive_analysis', name: 'Competitive Analysis', synonyms: ['Competitor Research', 'Market Intelligence'], category: 'marketing_strategy' },
        { id: 'customer_segmentation', name: 'Customer Segmentation', synonyms: ['Audience Segmentation', 'Targeting'], category: 'marketing_strategy' },
        { id: 'marketing_attribution', name: 'Marketing Attribution', synonyms: ['Multi-touch Attribution', 'ROI Analysis'], category: 'marketing_strategy' },
        { id: 'product_marketing', name: 'Product Marketing', synonyms: ['Product Launch', 'Go-to-Market'], category: 'marketing_strategy' },
        { id: 'growth_hacking', name: 'Growth Hacking', synonyms: ['Growth Marketing', 'Experimentation'], category: 'marketing_strategy' },
      ],
    },
  ],
};

/**
 * Manufacturing Industry Taxonomy
 */
const MANUFACTURING_TAXONOMY: IndustryTaxonomy = {
  id: 'manufacturing',
  name: 'Manufacturing',
  categories: [
    {
      id: 'manufacturing_processes',
      name: 'Manufacturing Processes',
      skills: [
        { id: 'cnc_machining', name: 'CNC Machining', synonyms: ['CNC Programming', 'Computer Numerical Control'], category: 'manufacturing_processes' },
        { id: 'lean_manufacturing', name: 'Lean Manufacturing', synonyms: ['Lean Production', 'Kaizen', 'Continuous Improvement'], category: 'manufacturing_processes' },
        { id: 'six_sigma', name: 'Six Sigma', synonyms: ['6 Sigma', 'Quality Management', 'Process Improvement'], category: 'manufacturing_processes' },
        { id: 'quality_control', name: 'Quality Control', synonyms: ['QC', 'Quality Assurance', 'QA'], category: 'manufacturing_processes' },
        { id: 'assembly', name: 'Assembly Line', synonyms: ['Production Line', 'Assembly Operations'], category: 'manufacturing_processes' },
        { id: 'welding', name: 'Welding', synonyms: ['MIG Welding', 'TIG Welding', 'Arc Welding'], category: 'manufacturing_processes' },
        { id: 'fabrication', name: 'Fabrication', synonyms: ['Metal Fabrication', 'Sheet Metal'], category: 'manufacturing_processes' },
        { id: 'injection_molding', name: 'Injection Molding', synonyms: ['Plastic Molding', 'Mold Design'], category: 'manufacturing_processes' },
        { id: '3d_printing', name: '3D Printing', synonyms: ['Additive Manufacturing', 'Rapid Prototyping'], category: 'manufacturing_processes' },
        { id: 'cmm', name: 'CMM', synonyms: ['Coordinate Measuring Machine', 'Precision Measurement'], category: 'manufacturing_processes' },
      ],
    },
    {
      id: 'manufacturing_systems',
      name: 'Manufacturing Systems & Tools',
      skills: [
        { id: 'autocad', name: 'AutoCAD', synonyms: ['CAD', 'Computer Aided Design', 'SolidWorks'], category: 'manufacturing_systems' },
        { id: 'cam', name: 'CAM', synonyms: ['Computer Aided Manufacturing', 'Mastercam', 'GibbsCAM'], category: 'manufacturing_systems' },
        { id: 'plc', name: 'PLC Programming', synonyms: ['Programmable Logic Controller', 'Automation', 'Ladder Logic'], category: 'manufacturing_systems' },
        { id: 'erp', name: 'ERP', synonyms: ['Enterprise Resource Planning', 'SAP', 'Oracle'], category: 'manufacturing_systems' },
        { id: 'mes', name: 'MES', synonyms: ['Manufacturing Execution System', 'Production Tracking'], category: 'manufacturing_systems' },
        { id: 'scada', name: 'SCADA', synonyms: ['Supervisory Control', 'Industrial Control Systems'], category: 'manufacturing_systems' },
        { id: 'preventive_maintenance', name: 'Preventive Maintenance', synonyms: ['Equipment Maintenance', 'TPM', 'Total Productive Maintenance'], category: 'manufacturing_systems' },
        { id: 'inventory_management', name: 'Inventory Management', synonyms: ['Stock Control', 'Warehouse Management'], category: 'manufacturing_systems' },
      ],
    },
    {
      id: 'manufacturing_safety',
      name: 'Safety & Compliance',
      skills: [
        { id: 'osha', name: 'OSHA Compliance', synonyms: ['Occupational Safety', 'Workplace Safety'], category: 'manufacturing_safety' },
        { id: 'iso_9001', name: 'ISO 9001', synonyms: ['Quality Management System', 'ISO Certification'], category: 'manufacturing_safety' },
        { id: 'iso_14001', name: 'ISO 14001', synonyms: ['Environmental Management', 'Environmental Compliance'], category: 'manufacturing_safety' },
        { id: 'safety protocols', name: 'Safety Protocols', synonyms: ['Safety Procedures', 'PPE', 'Lockout Tagout'], category: 'manufacturing_safety' },
        { id: 'risk_assessment', name: 'Risk Assessment', synonyms: ['Hazard Analysis', 'Safety Analysis'], category: 'manufacturing_safety' },
      ],
    },
  ],
};

/**
 * Sales Industry Taxonomy
 */
const SALES_TAXONOMY: IndustryTaxonomy = {
  id: 'sales',
  name: 'Sales',
  categories: [
    {
      id: 'sales_techniques',
      name: 'Sales Techniques',
      skills: [
        { id: 'consultative_selling', name: 'Consultative Selling', synonyms: ['Solution Selling', 'Needs-Based Selling'], category: 'sales_techniques' },
        { id: 'spinning', name: 'SPIN Selling', synonyms: ['Questioning Techniques', 'Sales Methodology'], category: 'sales_techniques' },
        { id: 'prospecting', name: 'Prospecting', synonyms: ['Lead Generation', 'Cold Calling', 'Outreach'], category: 'sales_techniques' },
        { id: 'negotiation', name: 'Negotiation', synonyms: ['Sales Negotiation', 'Contract Negotiation'], category: 'sales_techniques' },
        { id: 'closing', name: 'Closing', synonyms: ['Closing Techniques', 'Deal Closing'], category: 'sales_techniques' },
        { id: 'upselling', name: 'Upselling', synonyms: ['Cross-selling', 'Revenue Expansion'], category: 'sales_techniques' },
        { id: 'relationship_selling', name: 'Relationship Selling', synonyms: ['Account Management', 'Client Relationships'], category: 'sales_techniques' },
        { id: 'value_selling', name: 'Value Selling', synonyms: ['Value-Based Selling', 'ROI Selling'], category: 'sales_techniques' },
      ],
    },
    {
      id: 'sales_tools',
      name: 'Sales Tools & CRM',
      skills: [
        { id: 'salesforce', name: 'Salesforce', synonyms: ['SFDC', 'Salesforce CRM', 'Lightning'], category: 'sales_tools' },
        { id: 'hubspot_sales', name: 'HubSpot Sales', synonyms: ['HubSpot CRM', 'Sales Hub'], category: 'sales_tools' },
        { id: 'zoho', name: 'Zoho CRM', synonyms: ['Zoho', 'Zoho One'], category: 'sales_tools' },
        { id: 'outreach', name: 'Outreach', synonyms: ['Sales Engagement', 'Outreach.io'], category: 'sales_tools' },
        { id: 'linkedin_sales', name: 'LinkedIn Sales Navigator', synonyms: ['Sales Navigator', 'LinkedIn Sales'], category: 'sales_tools' },
        { id: 'gong', name: 'Gong.io', synonyms: ['Revenue Intelligence', 'Conversation Intelligence'], category: 'sales_tools' },
        { id: 'challenger', name: 'Challenger Sale', synonyms: ['Challenger Methodology', 'Challenger Sales'], category: 'sales_tools' },
        { id: 'meddic', name: 'MEDDIC', synonyms: ['MEDDPICC', 'Sales Qualification'], category: 'sales_tools' },
      ],
    },
    {
      id: 'sales_operations',
      name: 'Sales Operations & Strategy',
      skills: [
        { id: 'sales_forecasting', name: 'Sales Forecasting', synonyms: ['Revenue Forecasting', 'Pipeline Management'], category: 'sales_operations' },
        { id: 'pipeline_management', name: 'Pipeline Management', synonyms: ['Opportunity Management', 'Deal Management'], category: 'sales_operations' },
        { id: 'sales_analytics', name: 'Sales Analytics', synonyms: ['Sales Metrics', 'KPI Tracking', 'Sales Reporting'], category: 'sales_operations' },
        { id: 'territory_management', name: 'Territory Management', synonyms: ['Territory Planning', 'Geographic Management'], category: 'sales_operations' },
        { id: 'quota_attainment', name: 'Quota Attainment', synonyms: ['Sales Quota', 'Target Achievement'], category: 'sales_operations' },
        { id: 'sales_strategy', name: 'Sales Strategy', synonyms: ['Go-to-Market Strategy', 'Sales Planning'], category: 'sales_operations' },
        { id: 'commission_structures', name: 'Commission Structures', synonyms: ['Compensation Plans', 'Sales Incentives'], category: 'sales_operations' },
      ],
    },
  ],
};

/**
 * Design Industry Taxonomy
 */
const DESIGN_TAXONOMY: IndustryTaxonomy = {
  id: 'design',
  name: 'Design',
  categories: [
    {
      id: 'graphic_design',
      name: 'Graphic Design',
      skills: [
        { id: 'adobe_photoshop', name: 'Adobe Photoshop', synonyms: ['Photoshop', 'PS', 'Image Editing'], category: 'graphic_design' },
        { id: 'adobe_illustrator', name: 'Adobe Illustrator', synonyms: ['Illustrator', 'AI', 'Vector Graphics'], category: 'graphic_design' },
        { id: 'adobe_indesign', name: 'Adobe InDesign', synonyms: ['InDesign', 'Layout Design', 'Page Layout'], category: 'graphic_design' },
        { id: 'figma', name: 'Figma', synonyms: ['UI Design', 'Collaborative Design'], category: 'graphic_design' },
        { id: 'sketch', name: 'Sketch', synonyms: ['UI Design Tool', 'Mac Design'], category: 'graphic_design' },
        { id: 'adobe_xd', name: 'Adobe XD', synonyms: ['Experience Design', 'UX/UI Tool'], category: 'graphic_design' },
        { id: 'typography', name: 'Typography', synonyms: ['Type Design', 'Font Selection', 'Lettering'], category: 'graphic_design' },
        { id: 'color_theory', name: 'Color Theory', synonyms: ['Color Palettes', 'Color Schemes'], category: 'graphic_design' },
        { id: 'layout_design', name: 'Layout Design', synonyms: ['Composition', 'Visual Hierarchy'], category: 'graphic_design' },
        { id: 'brand_identity', name: 'Brand Identity', synonyms: ['Branding', 'Logo Design', 'Visual Identity'], category: 'graphic_design' },
      ],
    },
    {
      id: 'ux_design',
      name: 'UX Design',
      skills: [
        { id: 'user_research', name: 'User Research', synonyms: ['UX Research', 'User Testing', 'User Interviews'], category: 'ux_design' },
        { id: 'wireframing', name: 'Wireframing', synonyms: ['Wireframes', 'Low-Fidelity Design'], category: 'ux_design' },
        { id: 'prototyping', name: 'Prototyping', synonyms: ['Interactive Prototypes', 'Mockups', 'High-Fidelity Prototypes'], category: 'ux_design' },
        { id: 'user_flows', name: 'User Flows', synonyms: ['Flowcharts', 'User Journey', 'Task Flows'], category: 'ux_design' },
        { id: 'information_architecture', name: 'Information Architecture', synonyms: ['IA', 'Content Organization', 'Site Mapping'], category: 'ux_design' },
        { id: 'usability_testing', name: 'Usability Testing', synonyms: ['UX Testing', 'User Testing', 'A/B Testing'], category: 'ux_design' },
        { id: 'interaction_design', name: 'Interaction Design', synonyms: ['IxD', 'Microinteractions', 'Animation'], category: 'ux_design' },
        { id: 'design_systems', name: 'Design Systems', synonyms: ['Component Libraries', 'Style Guides'], category: 'ux_design' },
      ],
    },
    {
      id: 'design_specializations',
      name: 'Design Specializations',
      skills: [
        { id: 'web_design', name: 'Web Design', synonyms: ['Website Design', 'Responsive Design'], category: 'design_specializations' },
        { id: 'mobile_design', name: 'Mobile Design', synonyms: ['App Design', 'iOS Design', 'Android Design'], category: 'design_specializations' },
        { id: 'motion_graphics', name: 'Motion Graphics', synonyms: ['Animation', 'After Effects', 'Motion Design'], category: 'design_specializations' },
        { id: 'video_editing', name: 'Video Editing', synonyms: ['Premiere Pro', 'Final Cut', 'Video Production'], category: 'design_specializations' },
        { id: 'print_design', name: 'Print Design', synonyms: ['Print Media', 'Packaging Design', 'Publication Design'], category: 'design_specializations' },
        { id: 'illustration', name: 'Illustration', synonyms: ['Digital Illustration', 'Vector Art'], category: 'design_specializations' },
      ],
    },
  ],
};

/**
 * All industry taxonomies
 */
export const INDUSTRY_TAXONOMIES: IndustryTaxonomy[] = [
  HEALTHCARE_TAXONOMY,
  FINANCE_TAXONOMY,
  MARKETING_TAXONOMY,
  MANUFACTURING_TAXONOMY,
  SALES_TAXONOMY,
  DESIGN_TAXONOMY,
];

/**
 * Get taxonomy by industry ID
 */
export function getIndustryTaxonomy(industryId: string): IndustryTaxonomy | undefined {
  return INDUSTRY_TAXONOMIES.find((taxonomy) => taxonomy.id === industryId);
}

/**
 * Get all skills from a specific industry
 */
export function getIndustrySkills(industryId: string): SkillDefinition[] {
  const taxonomy = getIndustryTaxonomy(industryId);
  if (!taxonomy) return [];

  const allSkills: SkillDefinition[] = [];
  taxonomy.categories.forEach((category) => {
    category.skills.forEach((skill) => {
      allSkills.push(skill);
    });
  });

  return allSkills;
}

/**
 * Get all skills from all industries
 */
export function getAllIndustrySkills(): SkillDefinition[] {
  const allSkills: SkillDefinition[] = [];

  INDUSTRY_TAXONOMIES.forEach((taxonomy) => {
    taxonomy.categories.forEach((category) => {
      category.skills.forEach((skill) => {
        allSkills.push(skill);
      });
    });
  });

  return allSkills;
}

/**
 * Search industry skills by query
 */
export function searchIndustrySkills(
  industryId: string,
  query: string,
  limit = 20
): SkillDefinition[] {
  if (!query || query.length < 2) return [];

  const skills = getIndustrySkills(industryId);
  const normalized = query.toLowerCase().trim();

  const matches = skills.filter((skill) => {
    if (skill.name.toLowerCase().includes(normalized)) {
      return true;
    }
    return skill.synonyms.some((synonym) =>
      synonym.toLowerCase().includes(normalized)
    );
  });

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
 * Get skills by category within an industry
 */
export function getSkillsByIndustryCategory(
  industryId: string,
  categoryId: string
): SkillDefinition[] {
  const taxonomy = getIndustryTaxonomy(industryId);
  if (!taxonomy) return [];

  const category = taxonomy.categories.find((c) => c.id === categoryId);
  return category?.skills || [];
}

/**
 * Get all categories for an industry
 */
export function getIndustryCategories(industryId: string): { id: string; name: string }[] {
  const taxonomy = getIndustryTaxonomy(industryId);
  if (!taxonomy) return [];

  return taxonomy.categories.map((c) => ({
    id: c.id,
    name: c.name,
  }));
}

/**
 * Get canonical skill name from industry taxonomies
 */
export function getCanonicalIndustrySkillName(
  industryId: string,
  input: string
): string | null {
  if (!input) return null;

  const normalized = input.toLowerCase().trim();
  const skills = getIndustrySkills(industryId);

  for (const skill of skills) {
    if (skill.name.toLowerCase() === normalized) {
      return skill.name;
    }
    if (skill.synonyms.some((s) => s.toLowerCase() === normalized)) {
      return skill.name;
    }
  }

  return null;
}

/**
 * Get skill suggestions for an industry
 */
export function getIndustrySkillSuggestions(
  industryId: string,
  input: string,
  limit = 10
): string[] {
  const matches = searchIndustrySkills(industryId, input, limit);
  return matches.map((m) => m.name);
}

/**
 * Get all available industries
 */
export function getAllIndustries(): { id: string; name: string }[] {
  return INDUSTRY_TAXONOMIES.map((taxonomy) => ({
    id: taxonomy.id,
    name: taxonomy.name,
  }));
}

/**
 * Search skills across all industries (alias for taxonomies API)
 * This provides a unified search interface that searches across all industry taxonomies
 *
 * @param query - Search query string
 * @param limit - Maximum number of results to return
 * @returns Matching skills from all industries
 */
export function searchSkills(query: string, limit = 20): SkillDefinition[] {
  if (!query || query.length < 2) return [];

  const normalized = query.toLowerCase().trim();
  const allSkills = getAllIndustrySkills();

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

  // Sort by relevance (exact name match first, then starts with)
  matches.sort((a, b) => {
    const aExact = a.name.toLowerCase() === normalized;
    const bExact = b.name.toLowerCase() === normalized;

    if (aExact && !bExact) return -1;
    if (!aExact && bExact) return 1;

    const aStartsWith = a.name.toLowerCase().startsWith(normalized);
    const bStartsWith = b.name.toLowerCase().startsWith(normalized);

    if (aStartsWith && !bStartsWith) return -1;
    if (!bStartsWith && bStartsWith) return 1;

    return 0;
  });

  return matches.slice(0, limit);
}
