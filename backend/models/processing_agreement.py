"""
ProcessingAgreement model for Data Processing Agreement (DPA) templates and signatures
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ProcessingAgreement(Base, UUIDMixin, TimestampMixin):
    """
    ProcessingAgreement model for storing Data Processing Agreement (DPA) templates and signatures

    Attributes:
        id: UUID primary key
        organization_id: Foreign key or reference to organization
        agreement_type: Type of DPA (template, custom, amended)
        status: Current status of the agreement (draft, pending_signature, active, expired, terminated)
        version: Version number for tracking amendments and updates
        template_version: Template version if based on a standard template
        processor_name: Name of the data processor (third-party service)
        processor_contact: Contact information for the processor (email, phone, address)
        controller_representative: Name of the organization's representative signing the DPA
        terms: JSON object containing the DPA terms, conditions, and clauses
        data_categories: JSON array of data categories covered by this agreement (personal_data, sensitive_data, etc.)
        processing_purposes: JSON array of purposes for data processing
        security_measures: JSON object describing technical and organizational security measures
        subprocessing: JSON object containing subprocessor information and restrictions
        data_subject_rights: JSON object outlining data subject rights fulfillment procedures
        breach_notification: JSON object with breach notification procedures and timelines
        transfer_mechanisms: JSON array of data transfer mechanisms (SCCs, BCRs, etc.)
        effective_date: Date when the agreement becomes effective
        expiry_date: Optional date when the agreement expires
        termination_notice_days: Number of days notice required for termination
        auto_renewal: Whether the agreement auto-renews after expiry
        renewal_terms: JSON object containing auto-renewal terms and conditions
        signatures: JSON array with signature information (signatory, timestamp, method, ip_address)
        signed_by: User ID who signed on behalf of the organization
        signed_at: Timestamp when the agreement was signed
        signature_method: Method used for signing (digital, physical, electronic, clickwrap)
        documents: JSON array of attached document references and URLs
        notes: Additional notes or comments about the agreement
        created_by: User ID who created this DPA
        is_active: Whether this DPA is currently active and enforceable
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "processing_agreements"

    organization_id: Mapped[str] = mapped_column(nullable=False, index=True)
    agreement_type: Mapped[str] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(nullable=False, index=True)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    template_version: Mapped[Optional[str]] = mapped_column(nullable=True)
    processor_name: Mapped[str] = mapped_column(nullable=False)
    processor_contact: Mapped[dict] = mapped_column(JSON, nullable=False)
    controller_representative: Mapped[Optional[str]] = mapped_column(nullable=True)
    terms: Mapped[dict] = mapped_column(JSON, nullable=False)
    data_categories: Mapped[list] = mapped_column(JSON, nullable=False)
    processing_purposes: Mapped[list] = mapped_column(JSON, nullable=False)
    security_measures: Mapped[dict] = mapped_column(JSON, nullable=False)
    subprocessing: Mapped[dict] = mapped_column(JSON, nullable=False)
    data_subject_rights: Mapped[dict] = mapped_column(JSON, nullable=False)
    breach_notification: Mapped[dict] = mapped_column(JSON, nullable=False)
    transfer_mechanisms: Mapped[list] = mapped_column(JSON, nullable=False)
    effective_date: Mapped[datetime] = mapped_column(nullable=False)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    termination_notice_days: Mapped[int] = mapped_column(nullable=False, default=30)
    auto_renewal: Mapped[bool] = mapped_column(nullable=False, default=False)
    renewal_terms: Mapped[dict] = mapped_column(JSON, nullable=False)
    signatures: Mapped[list] = mapped_column(JSON, nullable=False)
    signed_by: Mapped[Optional[str]] = mapped_column(nullable=True)
    signed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    signature_method: Mapped[Optional[str]] = mapped_column(nullable=True)
    documents: Mapped[list] = mapped_column(JSON, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<ProcessingAgreement(id={self.id}, org={self.organization_id}, processor={self.processor_name}, status={self.status}, version={self.version})>"
