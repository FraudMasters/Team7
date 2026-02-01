# Data Models Reference

This document provides a comprehensive reference for all database models in the Resume Analysis System.

## Overview

The system uses:
- **Database**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0+ with declarative base
- **Primary Keys**: UUID (universally unique identifiers) for all models
- **Timestamps**: Automatic `created_at` and `updated_at` tracking via `TimestampMixin`

## Model Organization

Models are organized into the following categories:

1. **Core Resume & Matching** - Resume processing, analysis, and job matching
2. **Candidate Management** - Ranking, tagging, notes, and activity tracking
3. **ML & Analytics** - Machine learning models, performance metrics, and analytics
4. **Taxonomy & Skills** - Skill definitions, synonyms, and development plans
5. **Search & Alerts** - Saved searches, search history, and alerts
6. **System & Configuration** - Users, preferences, reports, and workflow
7. **Backup & Audit** - System backups and audit logging
8. **Special Features** - Interview prep, ATS results, demographic analysis

---

## Base Classes and Mixins

### `Base`
All models inherit from `Base`, which extends SQLAlchemy's `DeclarativeBase`.

### `TimestampMixin`
Provides automatic timestamp tracking:
- `created_at` (DateTime): Auto-set on record creation
- `updated_at` (DateTime): Auto-updated on record modification

### `UUIDMixin`
Provides UUID primary key:
- `id` (UUID, PK): Auto-generated UUID using `uuid4()`

---

## Core Resume & Matching Models

### `Resume`
Stores uploaded resume files and processing metadata.

**Table**: `resumes`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `filename` (VARCHAR 255): Original filename
- `file_path` (VARCHAR 512): Storage path
- `content_type` (VARCHAR 100): MIME type (application/pdf, etc.)
- `status` (ENUM): Processing status - pending, processing, completed, failed
- `raw_text` (TEXT): Extracted text content from PDF/DOCX
- `language` (VARCHAR 10): Detected language (en, ru, etc.)
- `error_message` (TEXT): Error details if processing failed
- `created_at` (TIMESTAMPTZ): Upload timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Indexes**:
- `status` - For querying by processing state

**Enums**:
- `ResumeStatus`: PENDING, PROCESSING, COMPLETED, FAILED

**Relationships**: Referenced by AnalysisResult, MatchResult, CandidateRank, etc.

---

### `ResumeAnalysis`
Stores structured resume analysis with parsed work experience and education.

**Table**: `resume_analyses`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to Resume (CASCADE delete)
- `parsed_data` (JSON): Structured resume data (contact, education, experience)
- `work_experience` (JSON): Array of work experience entries
- `education` (JSON): Array of education entries
- `skills` (JSON): Extracted and classified skills
- `languages` (JSON): Detected languages with proficiency
- `certifications` (JSON): Professional certifications
- `projects` (JSON): Notable projects
- `publications` (JSON): Research publications
- `created_at` (TIMESTAMPTZ): Analysis timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Relationships**:
- `resume` → Resume (many-to-one)

---

### `AnalysisResult`
Stores NLP/ML analysis results for resumes including errors, skills, and recommendations.

**Table**: `analysis_results`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to resumes (CASCADE delete, unique)
- `errors` (JSON): Detected errors (grammar, spelling, missing elements)
- `skills` (JSON): Extracted skills with metadata and confidence scores
- `experience_summary` (JSON): Total experience and per-skill breakdown
- `recommendations` (JSON): Improvement suggestions
- `keywords` (JSON): KeyBERT extracted keywords with scores
- `entities` (JSON): Named entities (organizations, dates, education)
- `created_at` (TIMESTAMPTZ): Analysis timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Constraints**:
- One analysis per resume (`resume_id` is unique)

---

### `JobVacancy`
Stores job descriptions for matching against resumes.

**Table**: `job_vacancies`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `title` (VARCHAR 255): Job title
- `description` (TEXT): Full job description
- `required_skills` (JSON): Mandatory skills array
- `min_experience_months` (INTEGER): Minimum required experience
- `additional_requirements` (JSON): Preferred skills array
- `industry` (VARCHAR 100): Industry sector
- `work_format` (VARCHAR 50): remote, office, hybrid
- `location` (VARCHAR 255): Location requirements
- `salary_min` (INTEGER): Minimum salary
- `salary_max` (INTEGER): Maximum salary
- `english_level` (VARCHAR 50): Required English proficiency
- `employment_type` (VARCHAR 50): full-time, part-time, contract
- `external_id` (VARCHAR 255): External system ID (job board API)
- `source` (VARCHAR 50): Source (manual, api, scrape)
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Indexes**:
- `external_id` - For deduplication

**Relationships**:
- `weight_profiles` → MatchingWeightProfile (one-to-many)

---

### `MatchResult`
Stores resume-to-vacancy matching results with unified scoring.

**Table**: `match_results`

**Fields**:

*Legacy Fields*:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to Resume (CASCADE delete)
- `vacancy_id` (UUID, FK): Link to JobVacancy (CASCADE delete)
- `match_percentage` (NUMERIC 5,2): Overall match score 0-100
- `matched_skills` (JSON): Skills found with highlighting info
- `missing_skills` (JSON): Required skills not found
- `additional_skills_matched` (JSON): Additional skills matched
- `experience_verified` (BOOLEAN): Whether experience requirements met
- `experience_details` (JSON): Per-skill experience breakdown

*Unified Matching Metrics*:
- `overall_score` (NUMERIC 5,4): Combined score from all methods (0-1)
- `keyword_score` (NUMERIC 5,4): Enhanced keyword matching (0-1)
- `tfidf_score` (NUMERIC 5,4): TF-IDF weighted score (0-1)
- `vector_score` (NUMERIC 5,4): Semantic similarity score (0-1)
- `vector_similarity` (NUMERIC 5,4): Raw cosine similarity (-1 to 1)
- `recommendation` (VARCHAR 20): excellent, good, maybe, poor
- `keyword_passed` (BOOLEAN): Keyword threshold met
- `tfidf_passed` (BOOLEAN): TF-IDF threshold met
- `vector_passed` (BOOLEAN): Vector threshold met
- `tfidf_matched` (JSON): Matched keywords from TF-IDF
- `tfidf_missing` (JSON): Missing keywords from TF-IDF
- `matcher_version` (VARCHAR 50): Matcher version used
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Indexes**:
- `resume_id` - For querying by resume
- `vacancy_id` - For querying by vacancy

---

### `ResumeComparison`
Stores saved multi-resume comparison views for recruiters.

**Table**: `resume_comparisons`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `vacancy_id` (UUID, FK): Link to JobVacancy (CASCADE delete)
- `name` (VARCHAR 500): Optional comparison name
- `resume_ids` (JSON): Array of resume IDs being compared
- `filters` (JSON): Filter settings (match range, sort field, etc.)
- `comparison_notes` (JSON): Recruiter notes about the comparison
- `created_by` (VARCHAR 255): User who created the comparison
- `shared_with` (JSON): Array of user IDs/emails comparison is shared with
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `ParsedResume`
Stores structured resume data extracted by parsing models.

**Table**: `parsed_resumes`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to Resume (CASCADE delete)
- `contact_info` (JSON): Email, phone, location, links
- `work_history` (JSON): Structured work experience
- `education_history` (JSON): Structured education
- `skills` (JSON): Categorized skills
- `languages` (JSON): Language proficiency
- `certifications` (JSON): Professional certifications
- `projects` (JSON): Project portfolio
- `publications` (JSON): Research publications
- `awards` (JSON): Professional awards
- `patents` (JSON): Patents held
- `created_at` (TIMESTAMPTZ): Parsing timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

## Candidate Management Models

### `CandidateRank`
Stores AI-powered candidate ranking scores with explainability.

**Table**: `candidate_ranks`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to Resume (CASCADE delete)
- `vacancy_id` (UUID, FK): Link to JobVacancy (CASCADE delete)
- `rank_score` (NUMERIC 5,4): Overall ranking score (0-1)
- `rank_position` (NUMERIC 10,0): Position in ranked list (1=best)
- `model_version` (VARCHAR 50): Ranking model version
- `model_type` (VARCHAR 50): Model type (random_forest, gradient_boosting, etc.)
- `is_experiment` (BOOLEAN): Whether in A/B test experiment
- `experiment_group` (VARCHAR 20): A/B test group (control/treatment)
- `feature_contributions` (JSON): SHAP values for explainability
- `ranking_factors` (JSON): Detailed factor scores
- `prediction_confidence` (NUMERIC 5,4): Model confidence (0-1)
- `recommendation` (VARCHAR 20): excellent, good, maybe, poor
- `extra_metadata` (JSON): Additional metadata
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Indexes**:
- `resume_id` - For querying by resume
- `vacancy_id` - For querying by vacancy

---

### `RankingFeedback`
Stores recruiter feedback on AI rankings for continuous learning.

**Table**: `ranking_feedback`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `rank_id` (UUID, FK): Link to CandidateRank (CASCADE delete)
- `recruiter_id` (UUID, FK): Optional link to Recruiter (SET NULL)
- `feedback_type` (VARCHAR 50): thumbs, rating, outcome
- `was_helpful` (BOOLEAN): Whether AI ranking was helpful
- `actual_outcome` (VARCHAR 50): hired, rejected, interviewing, pending
- `adjusted_score` (NUMERIC 5,4): Recruiter's adjusted score
- `rating` (NUMERIC 3,0): 1-5 star rating
- `comments` (TEXT): Optional text comments
- `feedback_source` (VARCHAR 50): web_ui, api, bulk_import
- `created_at` (TIMESTAMPTZ): Feedback timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Indexes**:
- `rank_id` - For querying by rank

---

### `CandidateTag`
Stores tags/labels for categorizing candidates.

**Table**: `candidate_tags`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to Resume (CASCADE delete)
- `tag_name` (VARCHAR 100): Tag name
- `tag_color` (VARCHAR 7): Hex color code for UI
- `created_by` (VARCHAR 255): User who created the tag
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `CandidateNote`
Stores recruiter notes about candidates.

**Table**: `candidate_notes`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to Resume (CASCADE delete)
- `recruiter_id` (UUID, FK): Optional link to Recruiter (SET NULL)
- `note_content` (TEXT): Note content
- `is_private` (BOOLEAN): Whether note is private to creator
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `CandidateActivity`
Stores activity history for candidates.

**Table**: `candidate_activities`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to Resume (CASCADE delete)
- `activity_type` (VARCHAR 50): Type of activity
- `activity_data` (JSON): Activity-specific data
- `performed_by` (VARCHAR 255): User who performed activity
- `created_at` (TIMESTAMPTZ): Activity timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `CandidateFeedback`
Collects structured feedback on candidates from interviews.

**Table**: `candidate_feedback`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to Resume (CASCADE delete)
- `vacancy_id` (UUID, FK): Link to JobVacancy (CASCADE delete)
- `feedback_data` (JSON): Structured feedback responses
- `overall_rating` (INTEGER): 1-5 overall rating
- `interviewer_id` (VARCHAR 255): Interviewer identifier
- `interview_date` (DATE): Date of interview
- `created_at` (TIMESTAMPTZ): Submission timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

## ML & Analytics Models

### `MLModelVersion`
Stores machine learning model versioning and A/B testing information.

**Table**: `ml_model_versions`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `model_name` (VARCHAR 100): Model name (skill_matching, resume_parser, etc.)
- `version` (VARCHAR 50): Version identifier (v1.0.0, v2.1.3)
- `is_active` (BOOLEAN): Whether currently active
- `is_experiment` (BOOLEAN): Whether experimental model for A/B testing
- `experiment_config` (JSON): A/B test configuration (traffic_percentage, etc.)
- `model_metadata` (JSON): Training metadata (algorithm, training_date, etc.)
- `accuracy_metrics` (JSON): Performance metrics (precision, recall, f1_score, etc.)
- `file_path` (VARCHAR 500): Path to model file in storage
- `performance_score` (NUMERIC 5,2): Overall performance score (0-100)
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Indexes**:
- `model_name` - For querying by model name

---

### `ModelPerformanceHistory`
Tracks ML model performance over time.

**Table**: `model_performance_history`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `model_version_id` (UUID, FK): Link to MLModelVersion
- `metric_name` (VARCHAR 100): Name of metric
- `metric_value` (NUMERIC 10,4): Metric value
- `evaluated_at` (TIMESTAMPTZ): Evaluation timestamp
- `test_data_size` (INTEGER): Size of test dataset
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `ModelTrainingEvent`
Logs ML model training events for reproducibility.

**Table**: `model_training_events`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `model_name` (VARCHAR 100): Name of trained model
- `model_version` (VARCHAR 50): Resulting version
- `training_params` (JSON): Training hyperparameters
- `training_data_info` (JSON): Dataset information
- `training_duration_seconds` (INTEGER): Training time
- `training_status` (VARCHAR 50): success, failed, cancelled
- `error_message` (TEXT): Error details if failed
- `started_at` (TIMESTAMPTZ): Training start time
- `completed_at` (TIMESTAMPTZ): Training completion time
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `AnalyticsEvent`
Stores analytics events for tracking system usage.

**Table**: `analytics_events`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `event_type` (VARCHAR 100): Type of event
- `event_data` (JSON): Event-specific data
- `user_id` (VARCHAR 255): User who triggered event
- `session_id` (VARCHAR 255): Session identifier
- `created_at` (TIMESTAMPTZ): Event timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `SkillFeedback`
Collects user feedback on extracted skills for continuous improvement.

**Table**: `skill_feedback`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to Resume (CASCADE delete)
- `skill_name` (VARCHAR 255): Skill being feedback on
- `is_correct` (BOOLEAN): Whether skill extraction was correct
- `suggested_correction` (VARCHAR 255): Suggested skill name
- `feedback_source` (VARCHAR 50): Source of feedback
- `created_at` (TIMESTAMPTZ): Feedback timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `FairnessMetrics`
Tracks fairness metrics for ML models to detect bias.

**Table**: `fairness_metrics`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `model_name` (VARCHAR 100): Model being evaluated
- `model_version` (VARCHAR 50): Model version
- `demographic_group` (VARCHAR 100): Demographic group
- `metric_name` (VARCHAR 100): Fairness metric (disparate_impact, etc.)
- `metric_value` (NUMERIC 10,4): Metric value
- `threshold_breach` (BOOLEAN): Whether fairness threshold breached
- `evaluated_at` (TIMESTAMPTZ): Evaluation timestamp
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `DemographicInference`
Stores inferred demographic information (for bias analysis only).

**Table**: `demographic_inferences`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to Resume (CASCADE delete)
- `inference_type` (VARCHAR 50): Type of inference
- `inferred_value` (VARCHAR 100): Inferred value
- `confidence_score` (NUMERIC 5,4): Confidence in inference
- `model_version` (VARCHAR 50): Model used for inference
- `created_at` (TIMESTAMPTZ): Inference timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

## Taxonomy & Skills Models

### `SkillTaxonomy`
Stores industry-specific skill taxonomies with versioning.

**Table**: `skill_taxonomies`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `industry` (VARCHAR 100): Industry sector (tech, healthcare, finance)
- `skill_name` (VARCHAR 255): Canonical skill name
- `context` (VARCHAR 100): Context category (web_framework, language, database)
- `variants` (JSON): Alternative names/spellings for this skill
- `extra_metadata` (JSON): Additional skill metadata (description, category)
- `is_active` (BOOLEAN): Whether taxonomy entry is active
- `version` (INTEGER): Version number
- `previous_version_id` (UUID, FK): Previous version (self-reference)
- `is_latest` (BOOLEAN): Whether this is latest version
- `is_public` (BOOLEAN): Whether publicly shareable
- `organization_id` (VARCHAR 255): Organization owner
- `source_organization` (VARCHAR 255): Original organization if shared
- `view_count` (INTEGER): Number of times viewed
- `use_count` (INTEGER): Number of times used in matching
- `last_used_at` (TIMESTAMPTZ): Last usage timestamp
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Indexes**:
- `industry` - For querying by industry
- `skill_name` - For querying by skill

---

### `CustomSynonym`
Stores custom skill synonyms for organizations.

**Table**: `custom_synonyms`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `organization_id` (VARCHAR 255): Organization that owns this synonym
- `canonical_skill` (VARCHAR 255): Canonical skill name
- `synonym` (VARCHAR 255): Custom synonym
- `industry` (VARCHAR 100): Industry context
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `SkillGapReport`
Stores skill gap analysis reports for candidates.

**Table**: `skill_gap_reports`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to Resume (CASCADE delete)
- `vacancy_id` (UUID, FK): Link to JobVacancy (CASCADE delete)
- `skill_gaps` (JSON): Missing skills and proficiency gaps
- `recommended_training` (JSON): Recommended training resources
- `priority_level` (VARCHAR 20): critical, high, medium, low
- `estimated_closure_time_weeks` (INTEGER): Weeks to close gaps
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `LearningResource`
Stores learning resources for skill development.

**Table**: `learning_resources`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `skill_name` (VARCHAR 255): Associated skill
- `resource_type` (VARCHAR 50): course, book, video, tutorial
- `title` (VARCHAR 500): Resource title
- `description` (TEXT): Resource description
- `url` (VARCHAR 1000): Resource URL
- `difficulty_level` (VARCHAR 20): beginner, intermediate, advanced
- `duration_hours` (NUMERIC 6,2): Estimated completion time
- `rating` (NUMERIC 3,2): Average user rating
- `cost` (VARCHAR 50): free, paid, subscription
- `provider` (VARCHAR 255): Content provider
- `tags` (JSON): Resource tags
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `SkillDevelopmentPlan`
Stores personalized skill development plans.

**Table**: `skill_development_plans`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to Resume (CASCADE delete)
- `vacancy_id` (UUID, FK): Optional link to JobVacancy (CASCADE delete)
- `plan_name` (VARCHAR 255): Plan name
- `target_skills` (JSON): Skills to develop with priorities
- `learning_resources` (JSON): Associated learning resources
- `timeline_weeks` (INTEGER): Plan duration in weeks
- `milestones` (JSON): Learning milestones
- `progress_percentage` (INTEGER): Overall progress (0-100)
- `status` (VARCHAR 50): not_started, in_progress, completed, paused
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

## Search & Alerts Models

### `SavedSearch`
Stores user search queries and filter configurations.

**Table**: `saved_searches`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `name` (VARCHAR 255): User-provided search name
- `query` (TEXT): Search query with boolean operators
- `filters` (JSON): Filter settings (skills, experience_years, location, language)
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Indexes**:
- `name` - For querying by name

---

### `SearchAlert`
Stores alerts for new matching resumes.

**Table**: `search_alerts`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `saved_search_id` (UUID, FK): Link to SavedSearch (CASCADE delete)
- `alert_frequency` (VARCHAR 50): immediate, daily, weekly
- `last_sent_at` (TIMESTAMPTZ): Last alert sent timestamp
- `is_active` (BOOLEAN): Whether alert is active
- `notification_method` (VARCHAR 50): email, webhook, in_app
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `SearchHistory`
Stores search history for analytics.

**Table**: `search_history`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `user_id` (VARCHAR 255): User who performed search
- `search_query` (TEXT): Search query
- `filters` (JSON): Applied filters
- `results_count` (INTEGER): Number of results
- `created_at` (TIMESTAMPTZ): Search timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

## System & Configuration Models

### `Recruiter`
Tracks recruiter attribution and performance.

**Table**: `recruiters`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `name` (VARCHAR 255): Recruiter's full name
- `email` (VARCHAR 255): Contact email (unique)
- `department` (VARCHAR 100): Department or team name
- `is_active` (BOOLEAN): Whether recruiter is active
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Indexes**:
- `name` - For querying by name
- `email` - Unique, for authentication
- `department` - For departmental analytics
- `is_active` - For filtering active recruiters

---

### `UserPreferences`
Stores user-specific preferences and settings.

**Table**: `user_preferences`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `user_id` (VARCHAR 255): User identifier
- `preferences` (JSON): User preference settings
- `notifications_enabled` (BOOLEAN): Whether notifications enabled
- `theme` (VARCHAR 20): UI theme preference
- `language` (VARCHAR 10): UI language preference
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `HiringStage`
Defines hiring pipeline stages for vacancies.

**Table**: `hiring_stages`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `vacancy_id` (UUID, FK): Link to JobVacancy (CASCADE delete)
- `stage_name` (VARCHAR 100): Stage name (applied, screening, interview, etc.)
- `stage_order` (INTEGER): Order in pipeline
- `is_active` (BOOLEAN): Whether stage is active
- `auto_advance_rules` (JSON): Rules for auto-advancing candidates
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `Report`
Stores generated reports.

**Table**: `reports`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `report_type` (VARCHAR 50): Type of report
- `title` (VARCHAR 255): Report title
- `parameters` (JSON): Report generation parameters
- `file_path` (VARCHAR 512): Path to generated report file
- `status` (VARCHAR 50): generating, completed, failed
- `generated_by` (VARCHAR 255): User who requested report
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `ScheduledReport`
Stores scheduled report configurations.

**Table**: `scheduled_reports`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `report_id` (UUID, FK): Link to Report (CASCADE delete)
- `schedule` (VARCHAR 100): Cron expression for schedule
- `recipients` (JSON): List of recipient emails
- `next_run_at` (TIMESTAMPTZ): Next scheduled run
- `last_run_at` (TIMESTAMPTZ): Last run timestamp
- `is_active` (BOOLEAN): Whether schedule is active
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `FeedbackTemplate`
Stores reusable feedback form templates.

**Table**: `feedback_templates`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `template_name` (VARCHAR 255): Template name
- `template_type` (VARCHAR 50): interview, ranking, general
- `questions` (JSON): Feedback questions structure
- `is_active` (BOOLEAN): Whether template is active
- `created_by` (VARCHAR 255): User who created template
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `WorkflowStageConfig`
Configures workflow stages for different processes.

**Table**: `workflow_stage_configs`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `workflow_type` (VARCHAR 50): Type of workflow
- `stage_name` (VARCHAR 100): Stage name
- `stage_config` (JSON): Stage configuration
- `order_index` (INTEGER): Stage order
- `is_required` (BOOLEAN): Whether stage is required
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `BatchJob`
Tracks batch processing jobs.

**Table**: `batch_jobs`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `job_type` (VARCHAR 50): Type of batch job
- `status` (VARCHAR 50): pending, running, completed, failed
- `total_items` (INTEGER): Total items to process
- `processed_items` (INTEGER): Items processed
- `failed_items` (INTEGER): Items failed
- `error_details` (JSON): Error details for failures
- `started_at` (TIMESTAMPTZ): Job start time
- `completed_at` (TIMESTAMPTZ): Job completion time
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

## Backup & Audit Models

### `Backup`
Tracks backup and restore operations.

**Table**: `backups`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `name` (VARCHAR 255): Backup name
- `type` (ENUM): database, files, models, full
- `status` (ENUM): pending, in_progress, completed, failed, expired, restoring
- `size_bytes` (BIGINT): Backup size in bytes
- `backup_path` (VARCHAR 512): Path to backup archive
- `completed_at` (VARCHAR 50): Completion timestamp
- `retention_days` (INTEGER): Retention period in days
- `checksum` (VARCHAR 128): SHA256 checksum
- `is_incremental` (BOOLEAN): Whether incremental backup
- `parent_backup_id` (VARCHAR 50): Parent backup for incremental
- `s3_uploaded` (BOOLEAN): Whether uploaded to S3
- `s3_key` (VARCHAR 512): S3 object key
- `error_message` (TEXT): Error message if failed
- `files_count` (INTEGER): Number of files in backup
- `tables_count` (INTEGER): Number of database tables
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Enums**:
- `BackupType`: DATABASE, FILES, MODELS, FULL
- `BackupStatus`: PENDING, IN_PROGRESS, COMPLETED, FAILED, EXPIRED, RESTORING

**Indexes**:
- `type` - For querying by backup type
- `status` - For querying by status
- `checksum` - For integrity verification

---

### `BackupConfig`
System-wide backup configuration settings.

**Table**: `backup_configs`

**Fields**:
- `id` (INTEGER, PK): Auto-increment primary key
- `retention_days` (INTEGER): Default retention period (default: 30)
- `backup_schedule` (VARCHAR 100): Cron expression (default: "0 2 * * *")
- `s3_enabled` (BOOLEAN): Whether S3 backup enabled
- `s3_bucket` (VARCHAR 255): S3 bucket name
- `s3_endpoint` (VARCHAR 512): S3-compatible endpoint URL
- `s3_access_key` (VARCHAR 255): S3 access key ID
- `s3_secret_key` (VARCHAR 255): S3 secret key (encrypted)
- `s3_region` (VARCHAR 50): S3 region (default: us-east-1)
- `notification_email` (VARCHAR 255): Email for failure notifications
- `enabled` (BOOLEAN): Whether automated backups enabled
- `incremental_enabled` (BOOLEAN): Whether incremental backups enabled
- `compression_enabled` (BOOLEAN): Whether to compress backups
- `last_backup_at` (VARCHAR 50): Last successful backup timestamp
- `last_backup_status` (VARCHAR 50): Last backup status
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `AuditLog`
Tracks system-wide user actions and changes for compliance.

**Table**: `audit_logs`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `action_type` (VARCHAR 50): Type of action (see AuditActionType enum)
- `entity_type` (VARCHAR 100): Type of entity affected
- `entity_id` (UUID): ID of affected entity
- `user_id` (UUID): User who performed action
- `organization_id` (UUID): Organization where action occurred
- `ip_address` (VARCHAR 45): IP address of action
- `user_agent` (TEXT): Client user agent string
- `action_data` (JSON): Action-specific data
- `before_value` (JSON): Entity state before action
- `after_value` (JSON): Entity state after action
- `reason` (TEXT): Optional explanation for action
- `created_at` (TIMESTAMPTZ): Action timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Enums** (AuditActionType):
- Resume operations: RESUME_CREATED, RESUME_UPDATED, RESUME_DELETED, RESUME_VIEWED, RESUME_UPLOADED
- Vacancy operations: VACANCY_CREATED, VACANCY_UPDATED, VACANCY_DELETED, VACANCY_VIEWED
- User operations: USER_CREATED, USER_UPDATED, USER_DELETED, USER_INVITED, USER_ROLE_CHANGED
- Candidate operations: CANDIDATE_RANKED, CANDIDATE_TAGGED, CANDIDATE_NOTE_ADDED, CANDIDATE_STAGE_CHANGED
- Matching operations: MATCH_CREATED, MATCH_UPDATED, MATCH_DELETED
- Export operations: DATA_EXPORTED, REPORT_GENERATED
- System operations: SETTINGS_UPDATED, BACKUP_CREATED, BACKUP_RESTORED
- Auth operations: LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT, PASSWORD_CHANGED

**Indexes**:
- `action_type` - For querying by action type
- `entity_type` - For querying by entity type
- `entity_id` - For querying by entity
- `user_id` - For querying by user
- `organization_id` - For querying by organization

---

## Matching Configuration Models

### `MatchingWeightProfile`
Stores custom matching weight profiles for vacancies.

**Table**: `matching_weight_profiles`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `vacancy_id` (UUID, FK): Link to JobVacancy (CASCADE delete)
- `profile_name` (VARCHAR 255): Profile name
- `weights` (JSON): Weight configuration for different match factors
- `thresholds` (JSON): Minimum thresholds for passing
- `is_active` (BOOLEAN): Whether profile is active
- `created_by` (VARCHAR 255): User who created profile
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Relationships**:
- `vacancy` → JobVacancy (many-to-one)

---

### `MatchingWeightVersion`
Version history for matching weight profiles.

**Table**: `matching_weight_versions`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `profile_id` (UUID, FK): Link to MatchingWeightProfile
- `version` (INTEGER): Version number
- `weights` (JSON): Weight configuration snapshot
- `thresholds` (JSON): Threshold configuration snapshot
- `change_reason` (TEXT): Reason for change
- `changed_by` (VARCHAR 255): User who made change
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

### `MatchingWeightsHistory`
Historical tracking of matching weight changes.

**Table**: `matching_weights_history`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `vacancy_id` (UUID, FK): Link to JobVacancy
- `old_weights` (JSON): Previous weight configuration
- `new_weights` (JSON): New weight configuration
- `change_reason` (TEXT): Reason for change
- `changed_by` (VARCHAR 255): User who made change
- `created_at` (TIMESTAMPTZ): Change timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

## Special Features Models

### `InterviewPrep`
Stores generated interview questions for candidates.

**Table**: `interview_preps`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to Resume (CASCADE delete)
- `vacancy_id` (UUID, FK): Link to JobVacancy (CASCADE delete)
- `technical_questions` (JSON): Technical interview questions
- `behavioral_questions` (JSON): Behavioral interview questions
- `situational_questions` (JSON): Situational interview questions
- `skill_verification_topics` (JSON): Skills/experience to verify
- `areas_to_probe` (JSON): Areas requiring deeper investigation
- `custom_questions` (JSON): Recruiter-added custom questions
- `question_feedback` (JSON): Feedback on question usefulness
- `provider` (TEXT): LLM provider used
- `model` (TEXT): Model name used
- `raw_response` (TEXT): Raw LLM response for debugging
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

**Indexes**:
- `resume_id` - For querying by resume
- `vacancy_id` - For querying by vacancy

---

### `ATSResult`
Stores ATS (Applicant Tracking System) compatibility scores.

**Table**: `ats_results`

**Fields**:
- `id` (UUID, PK): Unique identifier
- `resume_id` (UUID, FK): Link to Resume (CASCADE delete)
- `vacancy_id` (UUID, FK): Link to JobVacancy (CASCADE delete)
- `ats_score` (NUMERIC 5,2): ATS compatibility score (0-100)
- `parse_issues` (JSON): Parsing issues detected
- `format_recommendations` (JSON): Formatting recommendations
- `keyword_matches` (JSON): Keyword matching results
- `missing_keywords` (JSON): Required keywords not found
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp

---

## Using Models in Python

### Import Models

```python
from models import (
    Resume,
    AnalysisResult,
    JobVacancy,
    MatchResult,
    CandidateRank,
    SkillTaxonomy,
    MLModelVersion,
    Recruiter,
    AuditLog,
    Backup,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
```

### Create Database Session

```python
# Create engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
```

### Create Records

```python
# Create a new resume
resume = Resume(
    filename="resume.pdf",
    file_path="/uploads/resume.pdf",
    content_type="application/pdf",
    status=ResumeStatus.PENDING
)
session.add(resume)
session.commit()

# Create analysis result
analysis = AnalysisResult(
    resume_id=resume.id,
    errors={"grammar": [], "spelling": []},
    skills=["Python", "SQL", "FastAPI"],
    experience_summary={"total_months": 60}
)
session.add(analysis)
session.commit()
```

### Query Records

```python
# Query pending resumes
pending_resumes = session.query(Resume).filter(
    Resume.status == ResumeStatus.PENDING
).all()

# Query match results for a vacancy
matches = session.query(MatchResult).filter(
    MatchResult.vacancy_id == vacancy_id,
    MatchResult.overall_score >= 0.7
).order_by(MatchResult.overall_score.desc()).all()

# Query with joins
results = session.query(MatchResult, Resume).join(
    Resume, MatchResult.resume_id == Resume.id
).filter(
    MatchResult.vacancy_id == vacancy_id
).all()
```

### Update Records

```python
# Update resume status
resume.status = ResumeStatus.COMPLETED
session.commit()

# Update analysis results
analysis.skills.append("New Skill")
session.commit()
```

### Delete Records

```python
# Delete a resume (CASCADE will delete related records)
session.delete(resume)
session.commit()
```

## Model Relationships

### Key Foreign Key Relationships

1. **Resume** → AnalysisResult (one-to-one)
2. **Resume** → MatchResult (one-to-many)
3. **Resume** → CandidateRank (one-to-many)
4. **JobVacancy** → MatchResult (one-to-many)
5. **JobVacancy** → CandidateRank (one-to-many)
6. **JobVacancy** → MatchingWeightProfile (one-to-many)
7. **CandidateRank** → RankingFeedback (one-to-many)
8. **Recruiter** → RankingFeedback (one-to-many)
9. **MLModelVersion** → ModelPerformanceHistory (one-to-many)

### Cascade Behaviors

- **CASCADE**: Deleting parent deletes all children
  - Resume → AnalysisResult, MatchResult, CandidateRank, etc.
  - JobVacancy → MatchResult, CandidateRank, InterviewPrep, etc.

- **SET NULL**: Deleting parent sets foreign key to NULL
  - Recruiter → RankingFeedback (recruiter_id)

## Database Schema

### ER Diagram (Text Representation)

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Resume    │────<│ AnalysisResult   │     │ JobVacancy   │
└─────────────┘     └──────────────────┘     └──────────────┘
       │                    │                      │
       │                    │                      │
       v                    v                      v
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│MatchResult  │     │CandidateRank     │<────│MatchingWeight│
└─────────────┘     └──────────────────┘     └──────────────┘
       │                    │
       v                    v
┌─────────────┐     ┌──────────────────┐
│InterviewPrep│     │RankingFeedback   │
└─────────────┘     └──────────────────┘
                            ^
                            │
                     ┌──────────────┐
                     │  Recruiter   │
                     └──────────────┘
```

## Best Practices

1. **Always use UUIDs** for foreign key references
2. **Leverage mixins** (TimestampMixin, UUIDMixin) for consistent fields
3. **Use JSON fields** for flexible, schema-less data
4. **Add indexes** on frequently queried columns
5. **Use CASCADE deletes** for related data cleanup
6. **Document enums** in model docstrings
7. **Use relationship()** for ORM-level relationships
8. **Implement __repr__()** for debugging

## Migration Notes

When modifying models:
1. Update the model class
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration file
4. Apply migration: `alembic upgrade head`
5. Test migration on staging database first

See `DATABASE_SETUP.md` for detailed migration procedures.

## Further Reading

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Alembic Migration Guide](../DATABASE_SETUP.md)
- [API Reference](./API_REFERENCE.md)
- [Architecture Overview](./ARCHITECTURE.md)
