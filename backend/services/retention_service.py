"""
Retention service for automated data cleanup and GDPR compliance

This module provides comprehensive data retention functionality including:
- Automated data cleanup based on retention policies
- Support for multiple entity types (resumes, candidate data, analytics)
- Multiple retention actions (delete, anonymize, archive, flag for review)
- Audit logging for all retention operations
- Organization-specific and global retention policies
- Batch processing for efficient cleanup
- Dry-run mode for testing policies
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session

from config import get_settings
from models.base import Base
from models.data_retention_policy import (
    DataRetentionPolicy,
    RetentionEntityType,
    RetentionActionType,
)
from models.resume import Resume
from models.audit_log import AuditLog, AuditActionType
from models.analytics_event import AnalyticsEvent
from models.match_result import MatchResult
from models.analysis_result import AnalysisResult
from models.search_history import SearchHistory
from models.report import Report
from models.backup import Backup

logger = logging.getLogger(__name__)
settings = get_settings()


# Default retention periods (in days) if no policy is set
DEFAULT_RETENTION_DAYS = {
    RetentionEntityType.RESUME: 365,  # 1 year for resumes
    RetentionEntityType.CANDIDATE_DATA: 730,  # 2 years for candidate data
    RetentionEntityType.CANDIDATE_NOTES: 730,  # 2 years for notes
    RetentionEntityType.CANDIDATE_TAGS: 730,  # 2 years for tags
    RetentionEntityType.ANALYTICS_EVENTS: 90,  # 3 months for analytics
    RetentionEntityType.MATCH_RESULTS: 180,  # 6 months for match results
    RetentionEntityType.ANALYSIS_RESULTS: 365,  # 1 year for analysis results
    RetentionEntityType.AUDIT_LOGS: 2555,  # 7 years for audit logs (legal requirement)
    RetentionEntityType.SEARCH_HISTORY: 90,  # 3 months for search history
    RetentionEntityType.REPORTS: 365,  # 1 year for reports
    RetentionEntityType.BACKUPS: 90,  # 3 months for backups
}


class RetentionService:
    """
    Service for managing data retention and cleanup operations.

    This service handles automated cleanup of data based on retention policies,
    ensuring GDPR compliance through storage limitation and data minimization.
    Supports multiple retention actions and organization-specific policies.
    """

    def __init__(self, db_session: Session):
        """
        Initialize the retention service.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session

    def get_active_policies(
        self,
        entity_type: Optional[RetentionEntityType] = None,
        organization_id: Optional[UUID] = None,
    ) -> List[DataRetentionPolicy]:
        """
        Get all active retention policies, optionally filtered.

        Args:
            entity_type: Filter by entity type
            organization_id: Filter by organization (None for global policies only)

        Returns:
            List of active retention policies
        """
        query = select(DataRetentionPolicy).where(
            DataRetentionPolicy.is_active == True
        )

        if entity_type:
            query = query.where(DataRetentionPolicy.entity_type == entity_type)

        if organization_id is None:
            # Get only global policies (organization_id is None)
            query = query.where(DataRetentionPolicy.organization_id.is_(None))
        else:
            # Get org-specific policies OR global policies
            query = query.where(
                or_(
                    DataRetentionPolicy.organization_id == organization_id,
                    DataRetentionPolicy.organization_id.is_(None),
                )
            )

        query = query.order_by(
            DataRetentionPolicy.organization_id.desc().nulls_last(),
            DataRetentionPolicy.retention_days.asc(),
        )

        result = self.db_session.execute(query)
        return list(result.scalars().all())

    def get_policy_for_entity(
        self,
        entity_type: RetentionEntityType,
        organization_id: Optional[UUID] = None,
    ) -> Optional[DataRetentionPolicy]:
        """
        Get the applicable retention policy for an entity.

        Organization-specific policies take precedence over global policies.
        Shorter retention periods take precedence over longer ones.

        Args:
            entity_type: Type of entity
            organization_id: Optional organization ID

        Returns:
            Most applicable retention policy or None
        """
        policies = self.get_active_policies(entity_type, organization_id)

        if not policies:
            return None

        # Prefer organization-specific policies
        org_policies = [p for p in policies if p.organization_id == organization_id]
        if org_policies:
            policies = org_policies

        # Return the policy with the shortest retention period (most strict)
        return policies[0]

    def get_retention_days(
        self,
        entity_type: RetentionEntityType,
        organization_id: Optional[UUID] = None,
    ) -> int:
        """
        Get the number of days to retain data for a given entity type.

        Args:
            entity_type: Type of entity
            organization_id: Optional organization ID

        Returns:
            Number of days to retain data
        """
        policy = self.get_policy_for_entity(entity_type, organization_id)

        if policy:
            return policy.retention_days

        # Return default retention period
        return DEFAULT_RETENTION_DAYS.get(entity_type, 365)

    def find_expired_entities(
        self,
        entity_type: RetentionEntityType,
        organization_id: Optional[UUID] = None,
        limit: Optional[int] = None,
    ) -> List[Tuple[Any, DataRetentionPolicy]]:
        """
        Find entities that have exceeded their retention period.

        Args:
            entity_type: Type of entity to search for
            organization_id: Optional organization ID
            limit: Maximum number of entities to return

        Returns:
            List of (entity, policy) tuples
        """
        policy = self.get_policy_for_entity(entity_type, organization_id)

        if not policy:
            # Create a default policy object for reference
            retention_days = DEFAULT_RETENTION_DAYS.get(entity_type, 365)
            policy = DataRetentionPolicy(
                policy_name=f"Default {entity_type.value}",
                entity_type=entity_type,
                retention_days=retention_days,
                action_type=RetentionActionType.DELETE,
            )

        cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)

        entities = []

        try:
            if entity_type == RetentionEntityType.RESUME:
                from models.resume import ResumeStatus

                query = select(Resume).where(
                    and_(
                        Resume.created_at < cutoff_date,
                        Resume.status.in_(
                            [ResumeStatus.NEW, ResumeStatus.REVIEWED, ResumeStatus.COMPLETED]
                        ),  # Not HIRED
                    )
                )
                if limit:
                    query = query.limit(limit)
                result = self.db_session.execute(query)
                entities = [(entity, policy) for entity in result.scalars().all()]

            elif entity_type == RetentionEntityType.ANALYTICS_EVENTS:
                query = select(AnalyticsEvent).where(
                    AnalyticsEvent.created_at < cutoff_date
                )
                if limit:
                    query = query.limit(limit)
                result = self.db_session.execute(query)
                entities = [(entity, policy) for entity in result.scalars().all()]

            elif entity_type == RetentionEntityType.MATCH_RESULTS:
                query = select(MatchResult).where(
                    MatchResult.created_at < cutoff_date
                )
                if limit:
                    query = query.limit(limit)
                result = self.db_session.execute(query)
                entities = [(entity, policy) for entity in result.scalars().all()]

            elif entity_type == RetentionEntityType.ANALYSIS_RESULTS:
                query = select(AnalysisResult).where(
                    AnalysisResult.created_at < cutoff_date
                )
                if limit:
                    query = query.limit(limit)
                result = self.db_session.execute(query)
                entities = [(entity, policy) for entity in result.scalars().all()]

            elif entity_type == RetentionEntityType.SEARCH_HISTORY:
                query = select(SearchHistory).where(
                    SearchHistory.created_at < cutoff_date
                )
                if limit:
                    query = query.limit(limit)
                result = self.db_session.execute(query)
                entities = [(entity, policy) for entity in result.scalars().all()]

            elif entity_type == RetentionEntityType.REPORTS:
                query = select(Report).where(Report.created_at < cutoff_date)
                if limit:
                    query = query.limit(limit)
                result = self.db_session.execute(query)
                entities = [(entity, policy) for entity in result.scalars().all()]

            elif entity_type == RetentionEntityType.BACKUPS:
                query = select(Backup).where(Backup.created_at < cutoff_date)
                if limit:
                    query = query.limit(limit)
                result = self.db_session.execute(query)
                entities = [(entity, policy) for entity in result.scalars().all()]

            # AUDIT_LOGS are handled separately (longer retention, legal requirement)
            # CANDIDATE_DATA, CANDIDATE_NOTES, CANDIDATE_TAGS require more complex queries
            # that join with Resume or other entities

            logger.debug(
                f"Found {len(entities)} expired entities of type {entity_type.value}"
            )

        except Exception as e:
            logger.error(f"Error finding expired entities for {entity_type.value}: {e}")

        return entities

    def anonymize_resume(self, resume: Resume) -> bool:
        """
        Anonymize a resume by removing PII but keeping aggregate data.

        Args:
            resume: Resume entity to anonymize

        Returns:
            True if anonymization successful
        """
        try:
            # Remove PII data
            resume.raw_text = "[ANONYMIZED]"
            resume.filename = f"anonymized_{resume.id}.pdf"
            resume.error_message = "Anonymized due to retention policy"

            self.db_session.flush()

            logger.debug(f"Anonymized resume {resume.id}")
            return True

        except Exception as e:
            logger.error(f"Error anonymizing resume {resume.id}: {e}")
            return False

    def delete_entity(
        self,
        entity: Base,
        entity_type: str,
        policy: DataRetentionPolicy,
        user_id: Optional[UUID] = None,
    ) -> bool:
        """
        Delete an entity and log to audit trail.

        Args:
            entity: Entity to delete
            entity_type: Type of entity (for audit log)
            policy: Retention policy that triggered deletion
            user_id: Optional user ID for audit log

        Returns:
            True if deletion successful
        """
        try:
            entity_id = entity.id

            # Create audit log BEFORE deleting (so we can access entity properties)
            action_type = AuditActionType.RESUME_DELETED
            if entity_type != "resume":
                # Use a generic action type for other entities
                action_type = "data_retention_deletion"

            audit_log = AuditLog(
                action_type=action_type,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                reason=(policy.deletion_reason or f"Retention policy: {policy.policy_name}"),
                action_data={
                    "policy_name": policy.policy_name,
                    "retention_days": policy.retention_days,
                    "legal_basis": policy.legal_basis,
                },
            )
            self.db_session.add(audit_log)

            # Delete the entity
            self.db_session.delete(entity)
            self.db_session.flush()

            logger.debug(f"Deleted {entity_type} {entity_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting {entity_type} {entity.id}: {e}")
            self.db_session.rollback()
            return False

    def process_retention_action(
        self,
        entity: Base,
        entity_type: str,
        policy: DataRetentionPolicy,
        user_id: Optional[UUID] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a retention action on an entity.

        Args:
            entity: Entity to process
            entity_type: Type of entity
            policy: Retention policy to apply
            user_id: Optional user ID for audit log
            dry_run: If True, don't actually modify data

        Returns:
            Dictionary with processing result
        """
        result = {
            "entity_id": str(entity.id),
            "entity_type": entity_type,
            "action": policy.action_type.value,
            "policy": policy.policy_name,
            "success": False,
            "dry_run": dry_run,
        }

        if dry_run:
            result["success"] = True
            result["message"] = "Dry run - would process action"
            return result

        try:
            if policy.action_type == RetentionActionType.DELETE:
                success = self.delete_entity(
                    entity, entity_type, policy, user_id=user_id
                )
                result["success"] = success

            elif policy.action_type == RetentionActionType.ANONYMIZE:
                if entity_type == "resume":
                    success = self.anonymize_resume(entity)
                    result["success"] = success
                else:
                    result["message"] = "Anonymize not supported for this entity type"

            elif policy.action_type == RetentionActionType.ARCHIVE:
                # For now, treat archive as a flag
                result["success"] = True
                result["message"] = "Entity flagged for archival"
                # TODO: Implement actual archival to cold storage

            elif policy.action_type == RetentionActionType.FLAG_REVIEW:
                result["success"] = True
                result["message"] = "Entity flagged for manual review"
                # TODO: Implement review queue

            if result["success"]:
                self.db_session.commit()

        except Exception as e:
            logger.error(f"Error processing retention action: {e}")
            result["error"] = str(e)
            self.db_session.rollback()

        return result

    def cleanup_entity_type(
        self,
        entity_type: RetentionEntityType,
        organization_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        dry_run: bool = False,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Cleanup all expired entities of a given type.

        Args:
            entity_type: Type of entity to cleanup
            organization_id: Optional organization ID
            user_id: Optional user ID for audit logging
            dry_run: If True, don't actually modify data
            limit: Maximum number of entities to process

        Returns:
            Dictionary with cleanup results
        """
        logger.info(
            f"Starting cleanup for {entity_type.value} "
            f"(org={organization_id}, dry_run={dry_run})"
        )

        start_time = datetime.utcnow()
        results = {
            "entity_type": entity_type.value,
            "organization_id": str(organization_id) if organization_id else None,
            "dry_run": dry_run,
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "actions": [],
        }

        try:
            # Find expired entities
            expired_entities = self.find_expired_entities(
                entity_type, organization_id, limit=limit
            )

            if not expired_entities:
                logger.info(f"No expired entities found for {entity_type.value}")
                results["message"] = "No expired entities found"
                return results

            # Process each expired entity
            for entity, policy in expired_entities:
                result = self.process_retention_action(
                    entity=entity,
                    entity_type=entity_type.value,
                    policy=policy,
                    user_id=user_id,
                    dry_run=dry_run,
                )

                results["processed"] += 1
                results["actions"].append(result)

                if result["success"]:
                    results["succeeded"] += 1
                else:
                    results["failed"] += 1

            elapsed = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                f"Cleanup completed for {entity_type.value}: "
                f"{results['succeeded']}/{results['processed']} succeeded "
                f"in {elapsed:.1f}s"
            )

            results["elapsed_seconds"] = elapsed

        except Exception as e:
            logger.error(f"Error during cleanup of {entity_type.value}: {e}")
            results["error"] = str(e)

        return results

    def cleanup_all_entities(
        self,
        organization_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Cleanup all expired entities across all types.

        Args:
            organization_id: Optional organization ID
            user_id: Optional user ID for audit logging
            dry_run: If True, don't actually modify data

        Returns:
            Dictionary with combined cleanup results
        """
        logger.info(
            f"Starting full cleanup (org={organization_id}, dry_run={dry_run})"
        )

        start_time = datetime.utcnow()
        all_results = {
            "organization_id": str(organization_id) if organization_id else None,
            "dry_run": dry_run,
            "entity_types": {},
            "total_processed": 0,
            "total_succeeded": 0,
            "total_failed": 0,
        }

        # Get all entity types
        entity_types = [
            RetentionEntityType.RESUME,
            RetentionEntityType.ANALYTICS_EVENTS,
            RetentionEntityType.MATCH_RESULTS,
            RetentionEntityType.ANALYSIS_RESULTS,
            RetentionEntityType.SEARCH_HISTORY,
            RetentionEntityType.REPORTS,
            RetentionEntityType.BACKUPS,
        ]

        # Process each entity type
        for entity_type in entity_types:
            result = self.cleanup_entity_type(
                entity_type=entity_type,
                organization_id=organization_id,
                user_id=user_id,
                dry_run=dry_run,
            )

            all_results["entity_types"][entity_type.value] = result
            all_results["total_processed"] += result.get("processed", 0)
            all_results["total_succeeded"] += result.get("succeeded", 0)
            all_results["total_failed"] += result.get("failed", 0)

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        all_results["elapsed_seconds"] = elapsed

        logger.info(
            f"Full cleanup completed: "
            f"{all_results['total_succeeded']}/{all_results['total_processed']} succeeded "
            f"in {elapsed:.1f}s"
        )

        return all_results

    def get_retention_summary(
        self, organization_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of retention policies and pending cleanup.

        Args:
            organization_id: Optional organization ID

        Returns:
            Dictionary with retention summary
        """
        summary = {
            "organization_id": str(organization_id) if organization_id else "global",
            "policies": [],
            "pending_cleanup": {},
        }

        # Get all active policies
        policies = self.get_active_policies(organization_id=organization_id)

        for policy in policies:
            policy_info = {
                "entity_type": policy.entity_type.value,
                "policy_name": policy.policy_name,
                "retention_days": policy.retention_days,
                "action_type": policy.action_type.value,
                "is_global": policy.organization_id is None,
            }
            summary["policies"].append(policy_info)

            # Count pending entities for this policy
            try:
                expired_entities = self.find_expired_entities(
                    RetentionEntityType(policy.entity_type),
                    organization_id,
                    limit=1000,  # Limit for performance
                )
                summary["pending_cleanup"][policy.entity_type.value] = len(
                    expired_entities
                )
            except Exception as e:
                logger.warning(f"Could not count pending cleanup for {policy.entity_type}: {e}")
                summary["pending_cleanup"][policy.entity_type.value] = "unknown"

        return summary

    def create_retention_policy(
        self,
        policy_name: str,
        entity_type: RetentionEntityType,
        retention_days: int,
        action_type: RetentionActionType = RetentionActionType.DELETE,
        organization_id: Optional[UUID] = None,
        description: Optional[str] = None,
        legal_basis: Optional[str] = None,
        deletion_reason: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> DataRetentionPolicy:
        """
        Create a new retention policy.

        Args:
            policy_name: Name for the policy
            entity_type: Type of entity this policy applies to
            retention_days: Number of days to retain data
            action_type: Action to take when retention expires
            organization_id: Optional organization ID (None for global)
            description: Optional description
            legal_basis: Legal basis for retention
            deletion_reason: Reason to record in audit logs
            user_id: Optional user ID for audit logging

        Returns:
            Created DataRetentionPolicy
        """
        policy = DataRetentionPolicy(
            policy_name=policy_name,
            entity_type=entity_type,
            retention_days=retention_days,
            action_type=action_type,
            organization_id=organization_id,
            is_active=True,
            description=description,
            legal_basis=legal_basis,
            deletion_reason=deletion_reason,
        )

        self.db_session.add(policy)
        self.db_session.flush()

        # Audit log for policy creation
        audit_log = AuditLog(
            action_type="retention_policy_created",
            entity_type="data_retention_policy",
            entity_id=policy.id,
            user_id=user_id,
            action_data={
                "policy_name": policy_name,
                "entity_type": entity_type.value,
                "retention_days": retention_days,
                "action_type": action_type.value,
            },
        )
        self.db_session.add(audit_log)

        self.db_session.commit()

        logger.info(f"Created retention policy: {policy_name}")
        return policy

    def update_retention_policy(
        self,
        policy_id: UUID,
        user_id: Optional[UUID] = None,
        **updates,
    ) -> Optional[DataRetentionPolicy]:
        """
        Update an existing retention policy.

        Args:
            policy_id: ID of policy to update
            user_id: Optional user ID for audit logging
            **updates: Fields to update

        Returns:
            Updated policy or None if not found
        """
        query = select(DataRetentionPolicy).where(DataRetentionPolicy.id == policy_id)
        result = self.db_session.execute(query)
        policy = result.scalar_one_or_none()

        if not policy:
            return None

        # Store old values for audit log
        old_values = {
            "retention_days": policy.retention_days,
            "action_type": policy.action_type.value,
            "is_active": policy.is_active,
        }

        # Update fields
        for key, value in updates.items():
            if hasattr(policy, key) and value is not None:
                setattr(policy, key, value)

        self.db_session.flush()

        # Audit log for policy update
        audit_log = AuditLog(
            action_type="retention_policy_updated",
            entity_type="data_retention_policy",
            entity_id=policy.id,
            user_id=user_id,
            before_value=old_values,
            after_value={
                "retention_days": policy.retention_days,
                "action_type": policy.action_type.value,
                "is_active": policy.is_active,
            },
        )
        self.db_session.add(audit_log)

        self.db_session.commit()

        logger.info(f"Updated retention policy: {policy.policy_name}")
        return policy

    def delete_retention_policy(
        self, policy_id: UUID, user_id: Optional[UUID] = None
    ) -> bool:
        """
        Delete a retention policy.

        Args:
            policy_id: ID of policy to delete
            user_id: Optional user ID for audit logging

        Returns:
            True if deleted successfully
        """
        query = select(DataRetentionPolicy).where(DataRetentionPolicy.id == policy_id)
        result = self.db_session.execute(query)
        policy = result.scalar_one_or_none()

        if not policy:
            return False

        policy_name = policy.policy_name

        self.db_session.delete(policy)
        self.db_session.flush()

        # Audit log for policy deletion
        audit_log = AuditLog(
            action_type="retention_policy_deleted",
            entity_type="data_retention_policy",
            entity_id=policy_id,
            user_id=user_id,
            action_data={"policy_name": policy_name},
        )
        self.db_session.add(audit_log)

        self.db_session.commit()

        logger.info(f"Deleted retention policy: {policy_name}")
        return True
