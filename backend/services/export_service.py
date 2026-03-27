"""
Data export service for GDPR right to portability.

This module provides functionality to export candidate data in machine-readable formats
(JSON/CSV/XML) to support GDPR Article 15 - Right of Access (Data Portability).

The export service supports:
- Exporting all personal data for a candidate (resume, parsed data, activities, notes, tags)
- Multiple export formats (JSON for structured data, CSV for tabular data, XML for hierarchical data)
- Comprehensive data collection including consent records, activities, and analytics
- GDPR-compliant data portability

GDPR Requirements Met:
- Right to access: Candidates can receive all their personal data
- Data portability: Data provided in structured, commonly used format
- Comprehensive export: Includes all PII across all related tables
"""
import csv
import io
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.resume import Resume
from models.parsed_resume import ParsedResume
from models.hiring_stage import HiringStage
from models.candidate_activity import CandidateActivity
from models.candidate_note import CandidateNote
from models.candidate_tag import CandidateTag
from models.consent_record import ConsentRecord
from models.candidate_feedback import CandidateFeedback
from models.work_experience import WorkExperience
from models.resume_analysis import ResumeAnalysis

logger = logging.getLogger(__name__)


class ExportService:
    """
    Service for exporting candidate data for GDPR data portability.

    This service provides methods to export all personal data associated with a candidate
    in JSON, CSV, or XML format, supporting GDPR Article 15 - Right of Access.

    Attributes:
        db: Database session for executing queries

    Example:
        >>> export_service = ExportService(db)
        >>> json_data = await export_service.export_candidate_data(resume_id, format="json")
        >>> csv_data = await export_service.export_candidate_data(resume_id, format="csv")
        >>> xml_data = await export_service.export_candidate_data(resume_id, format="xml")
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the export service.

        Args:
            db: Database session for executing queries
        """
        self.db = db
        logger.info("ExportService initialized")

    async def export_candidate_data(
        self,
        resume_id: UUID,
        export_format: str = "json",
        include_analytics: bool = False,
    ) -> Dict[str, Any]:
        """
        Export all personal data for a candidate.

        Collects all PII across multiple tables:
        - Resume metadata and raw text
        - Parsed resume data (contact info, skills, experience, education)
        - Hiring stages and pipeline history
        - Activities and notes
        - Tags and feedback
        - Consent records
        - Work experience (if available)
        - Resume analysis (if available)

        Args:
            resume_id: UUID of the resume to export
            export_format: Format for export - "json", "csv", or "xml" (default: "json")
            include_analytics: Whether to include analytics data (default: False)

        Returns:
            Dictionary containing:
                - format: Export format ("json", "csv", or "xml")
                - data: Export data (dict for JSON, string for CSV/XML)
                - metadata: Export metadata (timestamp, resume_id, record counts)

        Raises:
            ValueError: If resume_id not found or invalid format
            Exception: If database query fails

        Example:
            >>> result = await export_service.export_candidate_data(
            ...     resume_id=uuid.uuid4(),
            ...     export_format="json"
            ... )
            >>> print(result["format"])  # "json"
            >>> print(result["metadata"]["total_records"])
        """
        logger.info(f"Exporting data for resume_id={resume_id}, format={export_format}")

        # Validate export format
        valid_formats = ["json", "csv", "xml"]
        if export_format not in valid_formats:
            raise ValueError(
                f"Invalid export format: {export_format}. Must be one of: {', '.join(valid_formats)}"
            )

        # Fetch all candidate data
        candidate_data = await self._collect_candidate_data(resume_id)

        if not candidate_data:
            raise ValueError(f"Resume not found: {resume_id}")

        # Format the data based on requested format
        if export_format == "csv":
            formatted_data = self._format_as_csv(candidate_data)
        elif export_format == "xml":
            formatted_data = self._format_as_xml(candidate_data)
        else:  # json
            formatted_data = self._format_as_json(candidate_data)

        # Prepare metadata
        metadata = {
            "export_timestamp": datetime.utcnow().isoformat() + "Z",
            "resume_id": str(resume_id),
            "filename": candidate_data.get("resume", {}).get("filename"),
            "format": export_format,
            "total_records": self._count_records(candidate_data),
            "includes_analytics": include_analytics,
        }

        logger.info(
            f"Export completed: {metadata['total_records']} records, "
            f"format={export_format}"
        )

        return {
            "format": export_format,
            "data": formatted_data,
            "metadata": metadata,
        }

    async def _collect_candidate_data(self, resume_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Collect all candidate data from database tables.

        Queries all related tables for a candidate's personal data.

        Args:
            resume_id: UUID of the resume

        Returns:
            Dictionary with all candidate data, or None if resume not found
        """
        try:
            # Fetch resume
            resume_result = await self.db.execute(
                select(Resume).where(Resume.id == resume_id)
            )
            resume = resume_result.scalar_one_or_none()

            if not resume:
                logger.warning(f"Resume not found: {resume_id}")
                return None

            candidate_data: Dict[str, Any] = {
                "resume": {
                    "id": str(resume.id),
                    "filename": resume.filename,
                    "content_type": resume.content_type,
                    "status": resume.status.value if resume.status else None,
                    "raw_text": resume.raw_text,
                    "language": resume.language,
                    "created_at": resume.created_at.isoformat() if resume.created_at else None,
                    "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
                }
            }

            # Fetch parsed resume data
            parsed_result = await self.db.execute(
                select(ParsedResume).where(ParsedResume.resume_id == resume_id)
            )
            parsed = parsed_result.scalar_one_or_none()
            if parsed:
                candidate_data["parsed_resume"] = {
                    "id": str(parsed.id),
                    "email": parsed.email,
                    "phone": parsed.phone,
                    "name": parsed.name,
                    "location": parsed.location,
                    "links": parsed.links,
                    "skills": parsed.skills,
                    "experience": parsed.experience,
                    "education": parsed.education,
                    "languages": parsed.languages,
                    "created_at": parsed.created_at.isoformat() if parsed.created_at else None,
                }

            # Fetch hiring stages (pipeline history)
            stages_result = await self.db.execute(
                select(HiringStage)
                .where(HiringStage.resume_id == resume_id)
                .order_by(HiringStage.created_at)
            )
            stages = stages_result.scalars().all()
            candidate_data["hiring_stages"] = [
                {
                    "id": str(stage.id),
                    "stage_name": stage.stage_name,
                    "vacancy_id": str(stage.vacancy_id) if stage.vacancy_id else None,
                    "notes": stage.notes,
                    "created_at": stage.created_at.isoformat() if stage.created_at else None,
                    "updated_at": stage.updated_at.isoformat() if stage.updated_at else None,
                }
                for stage in stages
            ]

            # Fetch candidate activities
            activities_result = await self.db.execute(
                select(CandidateActivity)
                .where(CandidateActivity.resume_id == resume_id)
                .order_by(CandidateActivity.created_at.desc())
            )
            activities = activities_result.scalars().all()
            candidate_data["activities"] = [
                {
                    "id": str(activity.id),
                    "activity_type": activity.activity_type.value,
                    "description": activity.description,
                    "created_at": activity.created_at.isoformat() if activity.created_at else None,
                }
                for activity in activities
            ]

            # Fetch candidate notes
            notes_result = await self.db.execute(
                select(CandidateNote)
                .where(CandidateNote.resume_id == resume_id)
                .order_by(CandidateNote.created_at.desc())
            )
            notes = notes_result.scalars().all()
            candidate_data["notes"] = [
                {
                    "id": str(note.id),
                    "content": note.content,
                    "created_at": note.created_at.isoformat() if note.created_at else None,
                    "updated_at": note.updated_at.isoformat() if note.updated_at else None,
                }
                for note in notes
            ]

            # Fetch candidate tags
            tags_result = await self.db.execute(
                select(CandidateTag)
                .where(CandidateTag.resume_id == resume_id)
                .order_by(CandidateTag.created_at)
            )
            tags = tags_result.scalars().all()
            candidate_data["tags"] = [
                {
                    "id": str(tag.id),
                    "tag_name": tag.tag_name,
                    "color": tag.color,
                    "created_at": tag.created_at.isoformat() if tag.created_at else None,
                }
                for tag in tags
            ]

            # Fetch consent records
            consents_result = await self.db.execute(
                select(ConsentRecord)
                .where(ConsentRecord.user_id.is_(None))  # Organization-level consents
                .order_by(ConsentRecord.created_at.desc())
            )
            consents = consents_result.scalars().all()
            candidate_data["consent_records"] = [
                {
                    "id": str(consent.id),
                    "consent_type": consent.consent_type.value,
                    "granted": consent.granted,
                    "withdrawn_at": consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
                    "withdrawal_reason": consent.withdrawal_reason,
                    "consent_text": consent.consent_text,
                    "consent_version": consent.consent_version,
                    "created_at": consent.created_at.isoformat() if consent.created_at else None,
                }
                for consent in consents
            ]

            # Fetch candidate feedback
            feedback_result = await self.db.execute(
                select(CandidateFeedback)
                .where(CandidateFeedback.resume_id == resume_id)
                .order_by(CandidateFeedback.created_at.desc())
            )
            feedbacks = feedback_result.scalars().all()
            candidate_data["feedback"] = [
                {
                    "id": str(feedback.id),
                    "language": feedback.language,
                    "tone": feedback.tone,
                    "feedback_source": feedback.feedback_source,
                    "match_score": feedback.match_score,
                    "grammar_feedback": feedback.grammar_feedback,
                    "skills_feedback": feedback.skills_feedback,
                    "experience_feedback": feedback.experience_feedback,
                    "recommendations": feedback.recommendations,
                    "viewed_by_candidate": feedback.viewed_by_candidate,
                    "downloaded": feedback.downloaded,
                    "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
                }
                for feedback in feedbacks
            ]

            # Fetch work experience
            work_exp_result = await self.db.execute(
                select(WorkExperience).where(WorkExperience.resume_id == resume_id)
            )
            work_experiences = work_exp_result.scalars().all()
            candidate_data["work_experience"] = [
                {
                    "id": str(exp.id),
                    "company": exp.company,
                    "title": exp.title,
                    "start_date": exp.start_date.isoformat() if exp.start_date else None,
                    "end_date": exp.end_date.isoformat() if exp.end_date else None,
                    "description": exp.description,
                }
                for exp in work_experiences
            ]

            # Fetch resume analysis
            analysis_result = await self.db.execute(
                select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id)
            )
            analyses = analysis_result.scalars().all()
            candidate_data["resume_analyses"] = [
                {
                    "id": str(analysis.id),
                    "language": analysis.language,
                    "raw_text": analysis.raw_text,
                    "skills": analysis.skills,
                    "keywords": analysis.keywords,
                    "entities": analysis.entities,
                    "total_experience_months": analysis.total_experience_months,
                    "education": analysis.education,
                    "contact_info": analysis.contact_info,
                    "grammar_issues": analysis.grammar_issues,
                    "warnings": analysis.warnings,
                    "quality_score": analysis.quality_score,
                    "processing_time_seconds": analysis.processing_time_seconds,
                    "analyzer_version": analysis.analyzer_version,
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                }
                for analysis in analyses
            ]

            logger.info(f"Collected data for resume {resume_id}: {self._count_records(candidate_data)} records")
            return candidate_data

        except Exception as e:
            logger.error(f"Error collecting candidate data for {resume_id}: {e}", exc_info=True)
            raise

    def _format_as_json(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format candidate data as JSON.

        Args:
            candidate_data: Collected candidate data

        Returns:
            JSON-formatted data structure
        """
        return candidate_data

    def _format_as_csv(self, candidate_data: Dict[str, Any]) -> str:
        """
        Format candidate data as CSV.

        Creates a flattened CSV representation of all candidate data.
        Nested structures are serialized as JSON strings.

        Args:
            candidate_data: Collected candidate data

        Returns:
            CSV-formatted string
        """
        output = io.StringIO()

        # Create flattened records for CSV
        records = []

        # Main record with resume info
        resume = candidate_data.get("resume", {})
        parsed = candidate_data.get("parsed_resume", {})

        main_record = {
            "record_type": "main",
            "id": resume.get("id"),
            "filename": resume.get("filename"),
            "email": parsed.get("email"),
            "phone": parsed.get("phone"),
            "name": parsed.get("name"),
            "location": parsed.get("location"),
            "status": resume.get("status"),
            "created_at": resume.get("created_at"),
        }
        records.append(main_record)

        # Add hiring stages
        for stage in candidate_data.get("hiring_stages", []):
            records.append({
                "record_type": "hiring_stage",
                "id": stage["id"],
                "stage_name": stage["stage_name"],
                "vacancy_id": stage["vacancy_id"],
                "notes": stage["notes"],
                "created_at": stage["created_at"],
            })

        # Add activities
        for activity in candidate_data.get("activities", []):
            records.append({
                "record_type": "activity",
                "id": activity["id"],
                "activity_type": activity["activity_type"],
                "description": activity["description"],
                "created_at": activity["created_at"],
            })

        # Add notes
        for note in candidate_data.get("notes", []):
            records.append({
                "record_type": "note",
                "id": note["id"],
                "content": note["content"],
                "created_at": note["created_at"],
            })

        # Add tags
        for tag in candidate_data.get("tags", []):
            records.append({
                "record_type": "tag",
                "id": tag["id"],
                "tag_name": tag["tag_name"],
                "color": tag["color"],
                "created_at": tag["created_at"],
            })

        # Add consent records
        for consent in candidate_data.get("consent_records", []):
            records.append({
                "record_type": "consent",
                "id": consent["id"],
                "consent_type": consent["consent_type"],
                "granted": consent["granted"],
                "withdrawn_at": consent["withdrawn_at"],
                "created_at": consent["created_at"],
            })

        # Add work experience
        for exp in candidate_data.get("work_experience", []):
            records.append({
                "record_type": "work_experience",
                "id": exp["id"],
                "company": exp["company"],
                "title": exp["title"],
                "start_date": exp["start_date"],
                "end_date": exp["end_date"],
                "description": exp["description"],
            })

        # Write CSV
        if records:
            # Get all unique field names
            fieldnames = set()
            for record in records:
                fieldnames.update(record.keys())
            fieldnames = sorted(fieldnames)

            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)

        return output.getvalue()

    def _format_as_xml(self, candidate_data: Dict[str, Any]) -> str:
        """
        Format candidate data as XML.

        Creates a hierarchical XML representation of all candidate data.
        Nested structures are preserved in XML element hierarchy.

        Args:
            candidate_data: Collected candidate data

        Returns:
            XML-formatted string
        """
        # Create root element
        root = ET.Element("candidate_export")

        # Add resume data
        resume = candidate_data.get("resume", {})
        if resume:
            resume_elem = ET.SubElement(root, "resume")
            for key, value in resume.items():
                if value is not None:
                    child = ET.SubElement(resume_elem, key)
                    child.text = str(value)

        # Add parsed resume data
        parsed = candidate_data.get("parsed_resume", {})
        if parsed:
            parsed_elem = ET.SubElement(root, "parsed_resume")
            for key, value in parsed.items():
                if value is not None:
                    if isinstance(value, (list, dict)):
                        child = ET.SubElement(parsed_elem, key)
                        child.text = str(value)
                    else:
                        child = ET.SubElement(parsed_elem, key)
                        child.text = str(value)

        # Add hiring stages
        hiring_stages = candidate_data.get("hiring_stages", [])
        if hiring_stages:
            stages_elem = ET.SubElement(root, "hiring_stages")
            for stage in hiring_stages:
                stage_elem = ET.SubElement(stages_elem, "hiring_stage")
                for key, value in stage.items():
                    if value is not None:
                        child = ET.SubElement(stage_elem, key)
                        child.text = str(value)

        # Add activities
        activities = candidate_data.get("activities", [])
        if activities:
            activities_elem = ET.SubElement(root, "activities")
            for activity in activities:
                activity_elem = ET.SubElement(activities_elem, "activity")
                for key, value in activity.items():
                    if value is not None:
                        child = ET.SubElement(activity_elem, key)
                        child.text = str(value)

        # Add notes
        notes = candidate_data.get("notes", [])
        if notes:
            notes_elem = ET.SubElement(root, "notes")
            for note in notes:
                note_elem = ET.SubElement(notes_elem, "note")
                for key, value in note.items():
                    if value is not None:
                        child = ET.SubElement(note_elem, key)
                        child.text = str(value)

        # Add tags
        tags = candidate_data.get("tags", [])
        if tags:
            tags_elem = ET.SubElement(root, "tags")
            for tag in tags:
                tag_elem = ET.SubElement(tags_elem, "tag")
                for key, value in tag.items():
                    if value is not None:
                        child = ET.SubElement(tag_elem, key)
                        child.text = str(value)

        # Add consent records
        consents = candidate_data.get("consent_records", [])
        if consents:
            consents_elem = ET.SubElement(root, "consent_records")
            for consent in consents:
                consent_elem = ET.SubElement(consents_elem, "consent_record")
                for key, value in consent.items():
                    if value is not None:
                        child = ET.SubElement(consent_elem, key)
                        child.text = str(value)

        # Add feedback
        feedbacks = candidate_data.get("feedback", [])
        if feedbacks:
            feedbacks_elem = ET.SubElement(root, "feedback")
            for feedback in feedbacks:
                feedback_elem = ET.SubElement(feedbacks_elem, "feedback_record")
                for key, value in feedback.items():
                    if value is not None:
                        child = ET.SubElement(feedback_elem, key)
                        child.text = str(value)

        # Add work experience
        work_exp = candidate_data.get("work_experience", [])
        if work_exp:
            work_exp_elem = ET.SubElement(root, "work_experience")
            for exp in work_exp:
                exp_elem = ET.SubElement(work_exp_elem, "experience")
                for key, value in exp.items():
                    if value is not None:
                        child = ET.SubElement(exp_elem, key)
                        child.text = str(value)

        # Add resume analyses
        analyses = candidate_data.get("resume_analyses", [])
        if analyses:
            analyses_elem = ET.SubElement(root, "resume_analyses")
            for analysis in analyses:
                analysis_elem = ET.SubElement(analyses_elem, "resume_analysis")
                for key, value in analysis.items():
                    if value is not None:
                        child = ET.SubElement(analysis_elem, key)
                        child.text = str(value)

        # Convert to string with pretty formatting
        ET.indent(root, space="  ", level=0)
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def _count_records(self, candidate_data: Dict[str, Any]) -> int:
        """
        Count total records in candidate data.

        Args:
            candidate_data: Collected candidate data

        Returns:
            Total number of records across all categories
        """
        count = 1  # Resume
        count += len(candidate_data.get("hiring_stages", []))
        count += len(candidate_data.get("activities", []))
        count += len(candidate_data.get("notes", []))
        count += len(candidate_data.get("tags", []))
        count += len(candidate_data.get("consent_records", []))
        count += len(candidate_data.get("feedback", []))
        count += len(candidate_data.get("work_experience", []))
        count += len(candidate_data.get("resume_analyses", []))
        return count


# Global service instance
_export_service: Optional[ExportService] = None


def get_export_service(db: AsyncSession) -> ExportService:
    """
    Get or create the export service instance.

    Args:
        db: Database session

    Returns:
        ExportService instance
    """
    return ExportService(db)
