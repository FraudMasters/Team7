"""
Email synchronization tasks for IMAP polling and email storage.

This module provides Celery tasks for synchronizing emails from IMAP servers,
parsing email content, tracking email threads, and storing them in the database.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
from email.utils import parsedate_to_datetime
from email.header import decode_header

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models import Communication, EmailMessage, Resume
from models.communication import CommunicationType, CommunicationDirection, CommunicationStatus

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.email_sync.sync_emails_imap",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def sync_emails_imap(
    self,
    imap_server: Optional[str] = None,
    imap_port: Optional[int] = None,
    imap_username: Optional[str] = None,
    imap_password: Optional[str] = None,
    folder: str = "INBOX",
    mark_as_read: bool = False,
    batch_size: int = 50,
) -> Dict[str, Any]:
    """
    Synchronize emails from IMAP server and store in database.

    This Celery task connects to an IMAP server, fetches emails from the specified
    folder, and stores them in the database as Communication and EmailMessage records.
    It tracks email threads using message-id, in-reply-to, and references headers.

    Task Workflow:
    1. Connect to IMAP server with provided credentials
    2. Select the specified folder (default: INBOX)
    3. Search for unread or all emails (based on mark_as_read)
    4. Fetch email batch (limited by batch_size)
    5. Parse email headers and body
    6. Match emails to candidates based on sender/recipient addresses
    7. Create Communication and EmailMessage records with thread tracking
    8. Mark emails as read on server (optional)

    Args:
        self: Celery task instance (bind=True)
        imap_server: IMAP server hostname (optional, uses config default)
        imap_port: IMAP server port (optional, uses 993 for SSL)
        imap_username: Email username/login (optional, uses config default)
        imap_password: Email password/app password (optional, uses config default)
        folder: IMAP folder to sync from (default: "INBOX")
        mark_as_read: Whether to mark fetched emails as read on server (default: False)
        batch_size: Maximum number of emails to fetch in one batch (default: 50)

    Returns:
        Dictionary containing synchronization results:
        - status: Task status (completed/failed/pending)
        - emails_processed: Number of emails processed
        - emails_stored: Number of emails stored in database
        - emails_skipped: Number of emails skipped (no candidate match)
        - threads_updated: Number of email threads updated
        - sync_start_time: Timestamp when sync started (ISO format)
        - sync_end_time: Timestamp when sync ended (ISO format)
        - processing_time_ms: Total processing time
        - errors: List of error messages (if any)

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For IMAP connection or database errors

    Example:
        >>> result = sync_emails_imap.delay(
        ...     imap_server="imap.gmail.com",
        ...     imap_username="user@example.com",
        ...     imap_password="app_password",
        ...     folder="INBOX",
        ...     batch_size=100
        ... )
        >>> print(result.get())
        {'status': 'completed', 'emails_stored': 15, 'threads_updated': 5}
    """
    import time
    import asyncio
    start_time = time.time()

    logger.info(f"Starting email sync from {folder} folder (batch_size={batch_size})")

    # Use config defaults if not provided
    if not imap_server:
        imap_server = getattr(settings, 'imap_server', None)
    if not imap_port:
        imap_port = getattr(settings, 'imap_port', 993)
    if not imap_username:
        imap_username = getattr(settings, 'imap_username', None)
    if not imap_password:
        imap_password = getattr(settings, 'imap_password', None)

    if not all([imap_server, imap_username, imap_password]):
        error_msg = "IMAP credentials not configured. Set imap_server, imap_username, and imap_password in config."
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg,
            "emails_processed": 0,
            "emails_stored": 0,
        }

    try:
        # Run async database operations in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                _sync_emails_from_imap(
                    imap_server=imap_server,
                    imap_port=imap_port,
                    imap_username=imap_username,
                    imap_password=imap_password,
                    folder=folder,
                    mark_as_read=mark_as_read,
                    batch_size=batch_size,
                )
            )
        finally:
            loop.close()

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Email sync completed: {result['emails_stored']} emails stored, "
            f"{result['emails_skipped']} skipped, {result['threads_updated']} threads updated "
            f"in {processing_time}ms"
        )

        result["processing_time_ms"] = processing_time
        result["sync_start_time"] = time.time() - (processing_time / 1000)
        result["sync_end_time"] = time.time()
        result["status"] = "completed"

        return result

    except SoftTimeLimitExceeded:
        logger.error("Email sync task timed out")
        return {
            "status": "failed",
            "error": "Task timed out",
            "emails_processed": 0,
            "emails_stored": 0,
        }

    except Exception as e:
        logger.error(
            f"Failed to sync emails from IMAP: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "status": "failed",
            "error": str(e),
            "emails_processed": 0,
            "emails_stored": 0,
        }


@shared_task(
    name="tasks.email_sync.process_email_queue",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def process_email_queue(
    self,
    batch_size: int = 50,
) -> Dict[str, Any]:
    """
    Process pending email synchronization queue.

    This Celery task runs periodically to process any pending email synchronizations
    that may have failed or been delayed. It ensures all emails are eventually synced
    and stored in the database.

    Args:
        self: Celery task instance (bind=True)
        batch_size: Maximum number of queued emails to process (default: 50)

    Returns:
        Dictionary containing processing results:
        - status: Task status (completed/failed/pending)
        - emails_processed: Number of emails processed
        - successful_stores: Number of emails successfully stored
        - failed_stores: Number of emails that failed to store
        - processing_time_ms: Total processing time
        - errors: List of error messages (if any)

    Example:
        >>> result = process_email_queue.delay(batch_size=100)
        >>> print(result.get())
        {'status': 'completed', 'emails_processed': 50, 'successful_stores': 48}
    """
    import time
    start_time = time.time()

    logger.info(f"Processing email sync queue (batch_size={batch_size})")

    try:
        # Placeholder for queue processing logic
        # In production, this would query a queue table or message broker
        # for pending email sync operations and process them

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Email queue processing completed in {processing_time}ms "
            f"(placeholder implementation)"
        )

        return {
            "status": "completed",
            "emails_processed": 0,
            "successful_stores": 0,
            "failed_stores": 0,
            "processing_time_ms": processing_time,
            "note": "Placeholder implementation - queue processing not yet implemented",
        }

    except SoftTimeLimitExceeded:
        logger.error("Email queue processing task timed out")
        return {
            "status": "failed",
            "error": "Task timed out",
            "emails_processed": 0,
        }

    except Exception as e:
        logger.error(
            f"Failed to process email queue: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=120 * (2 ** self.request.retries))

        return {
            "status": "failed",
            "error": str(e),
            "emails_processed": 0,
        }


async def _sync_emails_from_imap(
    imap_server: str,
    imap_port: int,
    imap_username: str,
    imap_password: str,
    folder: str,
    mark_as_read: bool,
    batch_size: int,
) -> Dict[str, Any]:
    """
    Synchronize emails from IMAP server (async wrapper for database operations).

    This helper function handles the IMAP connection and email fetching,
    then delegates database operations to async functions.

    Args:
        imap_server: IMAP server hostname
        imap_port: IMAP server port
        imap_username: Email username/login
        imap_password: Email password/app password
        folder: IMAP folder to sync from
        mark_as_read: Whether to mark emails as read on server
        batch_size: Maximum emails to fetch

    Returns:
        Dictionary with sync results
    """
    from imaplib import IMAP4_SSL
    from email import message_from_bytes

    emails_processed = 0
    emails_stored = 0
    emails_skipped = 0
    threads_updated = 0
    errors = []

    try:
        # Connect to IMAP server
        logger.info(f"Connecting to IMAP server: {imap_server}:{imap_port}")
        mail = IMAP4_SSL(imap_server, imap_port)
        mail.login(imap_username, imap_password)
        mail.select(folder)

        # Search for all emails (or only unread emails)
        search_criteria = 'UNSEEN' if not mark_as_read else 'ALL'
        typ, data = mail.search(None, search_criteria)

        email_ids = data[0].split()
        logger.info(f"Found {len(email_ids)} emails in {folder}")

        # Limit to batch_size
        email_ids = email_ids[-batch_size:] if len(email_ids) > batch_size else email_ids

        async with async_session_maker() as db:
            for email_id in email_ids:
                try:
                    # Fetch email
                    typ, data = mail.fetch(email_id, '(RFC822)')
                    raw_email = data[0][1]
                    email_message = message_from_bytes(raw_email)

                    # Parse email headers
                    email_data = _parse_email_headers(email_message)

                    # Extract email body
                    email_data["body"] = _extract_email_body(email_message)

                    # Determine if inbound or outbound
                    from_address = email_data.get("from_address", "")
                    to_addresses = email_data.get("to_address", "")

                    # Check if sender is a known candidate
                    candidate = await _find_candidate_by_email(db, from_address)

                    if not candidate:
                        # Check if any recipient is a known candidate
                        for addr in to_addresses.split(","):
                            candidate = await _find_candidate_by_email(db, addr.strip())
                            if candidate:
                                email_data["direction"] = CommunicationDirection.OUTBOUND
                                break

                        if not candidate:
                            emails_skipped += 1
                            logger.debug(f"Skipping email from {from_address} - no matching candidate")
                            continue
                    else:
                        email_data["direction"] = CommunicationDirection.INBOUND

                    # Store email in database
                    communication = await _store_email_in_database(
                        db=db,
                        candidate_id=candidate.id,
                        email_data=email_data,
                    )

                    if communication:
                        emails_stored += 1
                        emails_processed += 1

                        # Track thread updates
                        if email_data.get("thread_id") or email_data.get("in_reply_to"):
                            threads_updated += 1

                        logger.info(
                            f"Stored email '{email_data.get('subject', '(no subject)')}' "
                            f"from {from_address}"
                        )

                except Exception as e:
                    error_msg = f"Failed to process email {email_id.decode()}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)
                    emails_processed += 1

            # Commit all database changes
            await db.commit()

        # Close IMAP connection
        mail.close()
        mail.logout()

        return {
            "emails_processed": emails_processed,
            "emails_stored": emails_stored,
            "emails_skipped": emails_skipped,
            "threads_updated": threads_updated,
            "errors": errors,
        }

    except Exception as e:
        logger.error(f"IMAP sync failed: {e}", exc_info=True)
        raise


def _parse_email_headers(email_message) -> Dict[str, Any]:
    """
    Parse email headers to extract metadata.

    Args:
        email_message: Email message object from email.message_from_bytes

    Returns:
        Dictionary containing parsed email headers:
        - from_address: Sender email address
        - to_address: Recipient email addresses (comma-separated)
        - cc_address: CC recipients (comma-separated)
        - subject: Email subject
        - message_id: Message-ID header
        - in_reply_to: In-Reply-To header (for threading)
        - references: References header (for threading)
        - sent_at: Timestamp when email was sent
    """
    def decode_header_value(header_value):
        """Decode header value if it's encoded."""
        if not header_value:
            return ""

        decoded_parts = decode_header(header_value)
        decoded_string = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    try:
                        decoded_string += part.decode(encoding)
                    except (UnicodeDecodeError, LookupError):
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part

        return decoded_string

    # Extract basic headers
    from_address = email_message.get("From", "")
    to_address = email_message.get("To", "")
    cc_address = email_message.get("Cc", "")
    subject = decode_header_value(email_message.get("Subject", ""))
    message_id = email_message.get("Message-ID", "")
    in_reply_to = email_message.get("In-Reply-To", "")
    references = email_message.get("References", "")

    # Parse sent date
    sent_at = None
    date_header = email_message.get("Date")
    if date_header:
        try:
            sent_at = parsedate_to_datetime(date_header)
        except Exception:
            sent_at = datetime.utcnow()

    # Generate thread_id from references or in_reply_to
    thread_id = None
    if references:
        # Use the first reference (root of thread)
        ref_list = references.split()
        if ref_list:
            thread_id = ref_list[0].strip("<>")
    elif in_reply_to:
        # Use the message being replied to as thread_id
        thread_id = in_reply_to.strip("<>")

    return {
        "from_address": from_address,
        "to_address": to_address,
        "cc_address": cc_address,
        "subject": subject,
        "message_id": message_id.strip("<>"),
        "in_reply_to": in_reply_to.strip("<>"),
        "thread_id": thread_id,
        "sent_at": sent_at,
    }


def _extract_email_body(email_message) -> str:
    """
    Extract email body from email message.

    Args:
        email_message: Email message object

    Returns:
        Email body as string (prefers plain text, falls back to HTML)
    """
    body = ""

    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            # Skip attachments
            if "attachment" in content_disposition:
                continue

            # Prefer plain text
            if content_type == "text/plain" and not body:
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='ignore')
                except Exception:
                    pass

            # Fall back to HTML if no plain text found
            elif content_type == "text/html" and not body:
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    html_body = payload.decode(charset, errors='ignore')
                    # Simple HTML tag stripping (could be enhanced)
                    import re
                    body = re.sub(r'<[^>]+>', ' ', html_body)
                    body = ' '.join(body.split())
                except Exception:
                    pass
    else:
        # Not multipart, get payload directly
        try:
            payload = email_message.get_payload(decode=True)
            charset = email_message.get_content_charset() or 'utf-8'
            body = payload.decode(charset, errors='ignore')
        except Exception:
            body = str(email_message.get_payload())

    return body.strip()


async def _find_candidate_by_email(
    db: AsyncSession,
    email_address: str,
) -> Optional[Resume]:
    """
    Find a candidate (Resume) by email address.

    This function searches for candidates with matching email addresses
    in their metadata or contact information.

    Args:
        db: Database session
        email_address: Email address to search for

    Returns:
        Resume object if found, None otherwise
    """
    from sqlalchemy import or_

    # Extract email from "Name <email>" format if present
    clean_email = email_address.strip()
    if "<" in clean_email and ">" in clean_email:
        start = clean_email.rfind("<") + 1
        end = clean_email.rfind(">")
        clean_email = clean_email[start:end]

    # Search for candidate with matching email in metadata
    stmt = select(Resume).where(
        or_(
            Resume.metadata['email'].astext == clean_email,
            Resume.metadata['contact_email'].astext == clean_email,
        )
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@shared_task(
    name="tasks.email_sync.send_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_email_task(
    self,
    candidate_id: str,
    recipient_email: str,
    subject: str,
    body: str,
    cc_addresses: Optional[List[str]] = None,
    bcc_addresses: Optional[List[str]] = None,
    reply_to_message_id: Optional[str] = None,
    template_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send email via SMTP with delivery tracking and bounce detection.

    This Celery task handles sending outbound emails via SMTP, tracking delivery
    status, detecting bounces, and storing the sent email in the database for
    communication history.

    Task Workflow:
    1. Validate recipient email address and candidate exists
    2. Compose email with proper headers (Message-ID, References, In-Reply-To)
    3. Connect to SMTP server and send email
    4. Store sent email in database as Communication and EmailMessage records
    5. Track delivery status and detect bounces
    6. Update communication status based on delivery result

    Args:
        self: Celery task instance (bind=True)
        candidate_id: UUID of the candidate this email is for
        recipient_email: Primary recipient email address
        subject: Email subject line
        body: Email body content (plain text or HTML)
        cc_addresses: Optional list of CC recipient addresses
        bcc_addresses: Optional list of BCC recipient addresses
        reply_to_message_id: Optional Message-ID being replied to (for threading)
        template_id: Optional template ID used for this email
        metadata: Optional additional metadata to store with communication

    Returns:
        Dictionary containing sending results:
        - communication_id: UUID of created communication record
        - email_message_id: UUID of created email_message record
        - status: Task status (sent/bounced/failed/pending)
        - recipient: Email address of primary recipient
        - message_id: Message-ID header of sent email
        - sent_at: Timestamp when sent (ISO format)
        - delivery_status: Delivery status (delivered/bounced/pending)
        - bounce_reason: Reason for bounce (if bounced)
        - processing_time_ms: Total processing time
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For SMTP or database errors

    Example:
        >>> result = send_email_task.delay(
        ...     candidate_id="123-456",
        ...     recipient_email="candidate@example.com",
        ...     subject="Interview Invitation",
        ...     body="We would like to invite you..."
        ... )
        >>> print(result.get())
        {'communication_id': '...', 'status': 'sent', 'recipient': 'candidate@example.com'}
    """
    import time
    import smtplib
    import asyncio
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.utils import formataddr, make_msgid

    start_time = time.time()

    logger.info(
        f"Preparing to send email to {recipient_email} for candidate {candidate_id}"
    )

    try:
        # Get SMTP settings from config
        smtp_server = getattr(settings, 'smtp_server', 'localhost')
        smtp_port = getattr(settings, 'smtp_port', 587)
        smtp_username = getattr(settings, 'smtp_username', None)
        smtp_password = getattr(settings, 'smtp_password', None)
        smtp_use_tls = getattr(settings, 'smtp_use_tls', True)
        from_email = getattr(settings, 'smtp_from_email', smtp_username or 'noreply@example.com')
        from_name = getattr(settings, 'smtp_from_name', 'AgentHR')

        if not all([smtp_server, from_email]):
            error_msg = "SMTP server and from_email must be configured"
            logger.error(error_msg)
            return {
                "status": "failed",
                "error": error_msg,
                "recipient": recipient_email,
                "candidate_id": candidate_id,
            }

        # Generate Message-ID for tracking
        message_id = make_msgid(domain=smtp_server)

        # Compose email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr((from_name, from_email))
        msg['To'] = recipient_email
        msg['Message-ID'] = message_id

        # Add CC recipients
        if cc_addresses:
            msg['Cc'] = ', '.join(cc_addresses)

        # Add threading headers if replying
        if reply_to_message_id:
            msg['In-Reply-To'] = reply_to_message_id
            # Try to get thread_id from database
            # For now, just use the reply_to_message_id as reference
            msg['References'] = reply_to_message_id

        # Attach email body
        # Detect if body is HTML
        if '<html>' in body.lower() or '<body>' in body.lower():
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
        else:
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)

        # Prepare recipient list
        all_recipients = [recipient_email]
        if cc_addresses:
            all_recipients.extend(cc_addresses)
        if bcc_addresses:
            all_recipients.extend(bcc_addresses)

        # Send email via SMTP
        logger.info(f"Connecting to SMTP server: {smtp_server}:{smtp_port}")

        if smtp_use_tls:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)

        if smtp_username and smtp_password:
            server.login(smtp_username, smtp_password)

        # Send email
        server.sendmail(from_email, all_recipients, msg.as_string())
        server.quit()

        logger.info(f"Email sent successfully to {recipient_email}")

        # Store sent email in database
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            communication_data = loop.run_until_complete(
                _store_sent_email_in_database(
                    candidate_id=candidate_id,
                    recipient_email=recipient_email,
                    cc_addresses=cc_addresses or [],
                    bcc_addresses=bcc_addresses or [],
                    subject=subject,
                    body=body,
                    message_id=message_id,
                    reply_to_message_id=reply_to_message_id,
                    template_id=template_id,
                    metadata=metadata,
                )
            )
        finally:
            loop.close()

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Email send task completed for {recipient_email} "
            f"in {processing_time}ms"
        )

        return {
            "communication_id": str(communication_data.get("communication_id", "")),
            "email_message_id": str(communication_data.get("email_message_id", "")),
            "status": "sent",
            "recipient": recipient_email,
            "message_id": message_id,
            "sent_at": time.time(),
            "delivery_status": "delivered",
            "processing_time_ms": processing_time,
        }

    except smtplib.SMTPRecipientsRefused as e:
        # Bounce detection: recipient refused
        logger.error(f"Email bounced for {recipient_email}: {e}")
        return {
            "status": "bounced",
            "recipient": recipient_email,
            "delivery_status": "bounced",
            "bounce_reason": "recipient_refused",
            "bounce_details": str(e),
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }

    except smtplib.SMTPException as e:
        # Other SMTP errors
        logger.error(f"SMTP error sending to {recipient_email}: {e}", exc_info=True)

        # Check if it's a permanent bounce (5xx error)
        error_str = str(e)
        if any(code in error_str for code in ['500', '501', '502', '503', '504', '550', '551', '552', '553', '554']):
            return {
                "status": "bounced",
                "recipient": recipient_email,
                "delivery_status": "bounced",
                "bounce_reason": "permanent_bounce",
                "bounce_details": error_str,
                "processing_time_ms": int((time.time() - start_time) * 1000),
            }

        # Retry with exponential backoff for transient errors
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "status": "failed",
            "recipient": recipient_email,
            "error": str(e),
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Email send task timed out for {recipient_email}")
        return {
            "status": "failed",
            "recipient": recipient_email,
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to send email to {recipient_email}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "status": "failed",
            "recipient": recipient_email,
            "error": str(e),
        }


async def _store_sent_email_in_database(
    candidate_id: str,
    recipient_email: str,
    cc_addresses: List[str],
    bcc_addresses: List[str],
    subject: str,
    body: str,
    message_id: str,
    reply_to_message_id: Optional[str],
    template_id: Optional[str],
    metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Store sent email in database as Communication and EmailMessage records.

    Args:
        candidate_id: UUID of the candidate
        recipient_email: Primary recipient email address
        cc_addresses: List of CC recipient addresses
        bcc_addresses: List of BCC recipient addresses
        subject: Email subject line
        body: Email body content
        message_id: Message-ID header of sent email
        reply_to_message_id: Message-ID being replied to (for threading)
        template_id: Template ID used for this email
        metadata: Additional metadata to store

    Returns:
        Dictionary containing communication_id and email_message_id
    """
    try:
        # Generate thread_id from reply_to_message_id or message_id
        thread_id = reply_to_message_id or message_id

        # Prepare communication metadata
        comm_metadata = {
            "send_source": "smtp",
            "sent_message_id": message_id,
            "template_id": template_id,
        }
        if metadata:
            comm_metadata.update(metadata)

        # Create Communication record for OUTBOUND email
        communication = Communication(
            candidate_id=candidate_id,
            type=CommunicationType.EMAIL,
            direction=CommunicationDirection.OUTBOUND,
            status=CommunicationStatus.SENT,
            subject=subject,
            body=body,
            sent_at=datetime.utcnow(),
            metadata=comm_metadata,
        )

        async with async_session_maker() as db:
            db.add(communication)
            await db.flush()

            # Create EmailMessage record
            email_message = EmailMessage(
                communication_id=communication.id,
                from_address=None,  # Will be set from config
                to_address=recipient_email,
                cc_address=', '.join(cc_addresses) if cc_addresses else None,
                bcc_address=', '.join(bcc_addresses) if bcc_addresses else None,
                message_id=message_id,
                thread_id=thread_id,
                in_reply_to=reply_to_message_id,
                synced_at=datetime.utcnow(),
            )

            db.add(email_message)
            await db.flush()

            # Commit transaction
            await db.commit()

            return {
                "communication_id": communication.id,
                "email_message_id": email_message.id,
            }

    except Exception as e:
        logger.error(f"Failed to store sent email in database: {e}", exc_info=True)
        raise


async def _store_email_in_database(
    db: AsyncSession,
    candidate_id: UUID,
    email_data: Dict[str, Any],
) -> Optional[Communication]:
    """
    Store email in database as Communication and EmailMessage records.

    Args:
        db: Database session
        candidate_id: UUID of the candidate
        email_data: Dictionary containing parsed email data

    Returns:
        Created Communication object if successful, None otherwise
    """
    try:
        # Create Communication record
        communication = Communication(
            candidate_id=candidate_id,
            type=CommunicationType.EMAIL,
            direction=email_data.get("direction", CommunicationDirection.INBOUND),
            status=CommunicationStatus.DELIVERED,
            subject=email_data.get("subject"),
            body=email_data.get("body", ""),
            sent_at=email_data.get("sent_at"),
            received_at=email_data.get("sent_at"),  # Use same time for inbound
            metadata={
                "sync_source": "imap",
                "raw_message_id": email_data.get("message_id"),
            },
        )

        db.add(communication)
        await db.flush()

        # Create EmailMessage record
        email_message = EmailMessage(
            communication_id=communication.id,
            from_address=email_data.get("from_address"),
            to_address=email_data.get("to_address"),
            cc_address=email_data.get("cc_address"),
            bcc_address=None,  # IMAP doesn't show BCC
            message_id=email_data.get("message_id"),
            thread_id=email_data.get("thread_id"),
            in_reply_to=email_data.get("in_reply_to"),
            synced_at=datetime.utcnow(),
        )

        db.add(email_message)
        await db.flush()

        return communication

    except Exception as e:
        logger.error(f"Failed to store email in database: {e}", exc_info=True)
        return None
