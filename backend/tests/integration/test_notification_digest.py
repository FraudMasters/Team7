"""
Integration test for email digest functionality with notification aggregation.

This test verifies:
1. Multiple notifications can be created for the same recipient
2. Notification preferences control digest frequency
3. Notifications are properly grouped by recipient
4. Notifications are grouped by type within each digest
5. Digest emails are formatted correctly
6. Notifications are marked as delivered after digest is sent
7. Different digest frequencies (hourly, daily, weekly) work correctly
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db
from models.notification import Notification, NotificationType
from models.notification_preference import NotificationPreference, DigestFrequency
from models.recruiter import Recruiter
from tasks.notification_digest import (
    send_hourly_notification_digest,
    send_daily_notification_digest,
    send_weekly_notification_digest,
    format_notification_digest_email,
    _get_pending_notifications_for_digest,
    _mark_notifications_as_delivered,
)


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_digest.db"


@pytest.fixture
async def digest_test_db():
    """Create test database session for digest tests."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_recruiter(digest_test_db: AsyncSession):
    """Create a test recruiter with email for digest testing."""
    recruiter = Recruiter(
        email="test_recruiter@example.com",
        name="Test Recruiter",
        is_active=True,
    )
    digest_test_db.add(recruiter)
    await digest_test_db.commit()
    await digest_test_db.refresh(recruiter)

    return recruiter


@pytest.mark.asyncio
async def test_create_multiple_notifications_for_digest(digest_test_db: AsyncSession, test_recruiter: Recruiter):
    """
    Test: Create multiple notifications of same type for digest aggregation.

    Verification steps:
    1. Create a test recruiter
    2. Create 5 notifications of same type (candidate_applied)
    3. Create 3 notifications of different type (new_match)
    4. Verify all notifications are in database
    5. Verify notifications are not yet delivered
    """
    print("\n=== Test: Create Multiple Notifications for Digest ===\n")

    # Create multiple notifications of the same type
    print("Creating 5 candidate_applied notifications...")
    candidate_applied_notifications = []
    for i in range(5):
        notification = Notification(
            recipient_id=test_recruiter.id,
            notification_type=NotificationType.CANDIDATE_APPLIED,
            title=f"New Candidate Applied {i+1}",
            message=f"Candidate {i+1} has applied for the position",
            data={"candidate_id": str(uuid.uuid4()), "vacancy_id": str(uuid.uuid4())},
            is_read=False,
            delivered_at=None,
            delivery_failed=False,
        )
        digest_test_db.add(notification)
        candidate_applied_notifications.append(notification)

    print("Creating 3 new_match notifications...")
    new_match_notifications = []
    for i in range(3):
        notification = Notification(
            recipient_id=test_recruiter.id,
            notification_type=NotificationType.NEW_MATCH,
            title=f"New Match Found {i+1}",
            message=f"New candidate match {i+1} found for your search",
            data={"candidate_id": str(uuid.uuid4()), "vacancy_id": str(uuid.uuid4())},
            is_read=False,
            delivered_at=None,
            delivery_failed=False,
        )
        digest_test_db.add(notification)
        new_match_notifications.append(notification)

    await digest_test_db.commit()

    # Verify all notifications are in database
    print("\nVerifying notifications in database...")
    query = select(Notification).where(Notification.recipient_id == test_recruiter.id)
    result = await digest_test_db.execute(query)
    all_notifications = result.scalars().all()

    assert len(all_notifications) == 8, f"Expected 8 notifications, found {len(all_notifications)}"
    print(f"✓ Created {len(all_notifications)} notifications total")

    # Verify none are delivered yet
    undelivered_query = select(Notification).where(
        and_(
            Notification.recipient_id == test_recruiter.id,
            Notification.delivered_at.is_(None),
        )
    )
    undelivered_result = await digest_test_db.execute(undelivered_query)
    undelivered_notifications = undelivered_result.scalars().all()

    assert len(undelivered_notifications) == 8, "Expected all 8 notifications to be undelivered"
    print(f"✓ All {len(undelivered_notifications)} notifications are undelivered")

    print("\n✓ Test passed: Multiple notifications created successfully\n")


@pytest.mark.asyncio
async def test_notification_preferences_digest_frequency(digest_test_db: AsyncSession, test_recruiter: Recruiter):
    """
    Test: Create notification preferences with digest frequency.

    Verification steps:
    1. Create notification preference for hourly digest
    2. Create notification preference for daily digest
    3. Verify preferences are stored correctly
    4. Verify digest frequency is set correctly
    """
    print("\n=== Test: Notification Preferences Digest Frequency ===\n")

    # Create preference for hourly digest on candidate_applied
    print("Creating hourly digest preference for candidate_applied...")
    hourly_preference = NotificationPreference(
        user_id=test_recruiter.id,
        notification_type=NotificationType.CANDIDATE_APPLIED.value,
        email_enabled=True,
        in_app_enabled=True,
        push_enabled=False,
        sms_enabled=False,
        digest_frequency=DigestFrequency.HOURLY.value,
    )
    digest_test_db.add(hourly_preference)
    await digest_test_db.commit()
    await digest_test_db.refresh(hourly_preference)

    assert hourly_preference.digest_frequency == DigestFrequency.HOURLY.value
    print(f"✓ Hourly preference created: {hourly_preference.digest_frequency}")

    # Create preference for daily digest on new_match
    print("\nCreating daily digest preference for new_match...")
    daily_preference = NotificationPreference(
        user_id=test_recruiter.id,
        notification_type=NotificationType.NEW_MATCH.value,
        email_enabled=True,
        in_app_enabled=True,
        push_enabled=False,
        sms_enabled=False,
        digest_frequency=DigestFrequency.DAILY.value,
    )
    digest_test_db.add(daily_preference)
    await digest_test_db.commit()
    await digest_test_db.refresh(daily_preference)

    assert daily_preference.digest_frequency == DigestFrequency.DAILY.value
    print(f"✓ Daily preference created: {daily_preference.digest_frequency}")

    # Verify preferences are in database
    query = select(NotificationPreference).where(NotificationPreference.user_id == test_recruiter.id)
    result = await digest_test_db.execute(query)
    preferences = result.scalars().all()

    assert len(preferences) == 2, f"Expected 2 preferences, found {len(preferences)}"
    print(f"\n✓ Test passed: {len(preferences)} preferences stored correctly\n")


@pytest.mark.asyncio
async def test_query_pending_notifications_for_digest(digest_test_db: AsyncSession, test_recruiter: Recruiter):
    """
    Test: Query pending notifications for hourly digest.

    Verification steps:
    1. Create notifications with different timestamps
    2. Create notification preference for hourly digest
    3. Query for pending notifications within time window
    4. Verify only recent undelivered notifications are returned
    5. Verify notifications include recipient email and name
    """
    print("\n=== Test: Query Pending Notifications for Digest ===\n")

    # Create notification preference for hourly digest
    print("Setting up hourly digest preference...")
    preference = NotificationPreference(
        user_id=test_recruiter.id,
        notification_type=NotificationType.CANDIDATE_APPLIED.value,
        email_enabled=True,
        in_app_enabled=True,
        push_enabled=False,
        sms_enabled=False,
        digest_frequency=DigestFrequency.HOURLY.value,
    )
    digest_test_db.add(preference)
    await digest_test_db.commit()

    # Create recent notifications (within last hour)
    print("Creating 3 recent notifications (within last hour)...")
    time_cutoff = datetime.utcnow() - timedelta(minutes=30)
    recent_notifications = []
    for i in range(3):
        notification = Notification(
            recipient_id=test_recruiter.id,
            notification_type=NotificationType.CANDIDATE_APPLIED,
            title=f"Recent Applied {i+1}",
            message=f"Recent candidate {i+1} applied",
            is_read=False,
            delivered_at=None,
            delivery_failed=False,
            created_at=time_cutoff + timedelta(minutes=i),
        )
        digest_test_db.add(notification)
        recent_notifications.append(notification)

    # Create old notification (outside time window)
    print("Creating 1 old notification (outside time window)...")
    old_notification = Notification(
        recipient_id=test_recruiter.id,
        notification_type=NotificationType.CANDIDATE_APPLIED,
        title="Old Applied",
        message="Old candidate applied",
        is_read=False,
        delivered_at=None,
        delivery_failed=False,
        created_at=time_cutoff - timedelta(hours=2),
    )
    digest_test_db.add(old_notification)

    await digest_test_db.commit()

    # Query for pending notifications
    print("\nQuerying pending notifications for hourly digest...")
    cutoff_time = datetime.utcnow() - timedelta(hours=1)
    pending_notifications = await _get_pending_notifications_for_digest(
        digest_test_db,
        DigestFrequency.HOURLY.value,
        cutoff_time,
    )

    print(f"Found {len(pending_notifications)} pending notifications")

    # Should only return the 3 recent notifications
    assert len(pending_notifications) == 3, f"Expected 3 pending notifications, found {len(pending_notifications)}"
    print(f"✓ Correctly filtered to recent notifications: {len(pending_notifications)}")

    # Verify notifications include recipient information
    for notif in pending_notifications:
        assert "recipient_email" in notif, "Notification missing recipient_email"
        assert "recipient_name" in notif, "Notification missing recipient_name"
        assert notif["recipient_email"] == test_recruiter.email
        assert notif["recipient_name"] == test_recruiter.name

    print(f"✓ All notifications include recipient info (email: {test_recruiter.email})")

    # Verify old notification is not included
    notification_titles = [n["title"] for n in pending_notifications]
    assert "Old Applied" not in notification_titles, "Old notification should not be included"
    print("✓ Old notification correctly excluded")

    print("\n✓ Test passed: Pending notifications queried correctly\n")


@pytest.mark.asyncio
async def test_format_notification_digest_email(digest_test_db: AsyncSession, test_recruiter: Recruiter):
    """
    Test: Format notification digest email with grouped notifications.

    Verification steps:
    1. Create multiple notifications of different types
    2. Format digest email using the helper function
    3. Verify email subject is correct
    4. Verify notifications are grouped by type in email body
    5. Verify email includes proper footer and action URLs
    """
    print("\n=== Test: Format Notification Digest Email ===\n")

    # Create sample notifications
    notifications = [
        {
            "id": str(uuid.uuid4()),
            "notification_type": "candidate_applied",
            "title": "New Candidate Applied",
            "message": "John Doe has applied for Senior Developer position",
            "created_at": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
            "action_url": "https://example.com/candidates/123",
            "data": {"candidate_id": "123"},
        },
        {
            "id": str(uuid.uuid4()),
            "notification_type": "candidate_applied",
            "title": "Another Candidate Applied",
            "message": "Jane Smith has applied for Senior Developer position",
            "created_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
            "action_url": "https://example.com/candidates/456",
            "data": {"candidate_id": "456"},
        },
        {
            "id": str(uuid.uuid4()),
            "notification_type": "new_match",
            "title": "New Match Found",
            "message": "Found a new match for your search: Backend Developer",
            "created_at": (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
            "action_url": "https://example.com/matches/789",
            "data": {"match_id": "789"},
        },
    ]

    # Format digest email
    print("Formatting daily digest email...")
    email_details = format_notification_digest_email(
        recipient_email=test_recruiter.email,
        recipient_name=test_recruiter.name,
        notifications=notifications,
        digest_frequency="daily",
    )

    # Verify email structure
    assert "subject" in email_details, "Email missing subject"
    assert "body" in email_details, "Email missing body"
    assert "priority" in email_details, "Email missing priority"

    print(f"✓ Email formatted with subject: {email_details['subject']}")

    # Verify subject
    assert "Daily" in email_details["subject"], "Subject should mention 'Daily'"
    assert "Digest" in email_details["subject"], "Subject should mention 'Digest'"
    print(f"✓ Subject is correct: {email_details['subject']}")

    # Verify body contains key elements
    body = email_details["body"]
    assert test_recruiter.name in body, "Body should greet recipient by name"
    assert "3 notification" in body, "Body should mention total notification count"
    assert "candidate_applied" in body or "Candidate Applied" in body, "Body should include notification types"
    assert "new_match" in body or "New Match" in body, "Body should include notification types"
    assert "https://example.com/candidates/123" in body, "Body should include action URL"
    print("✓ Body contains greeting, notification count, types, and action URLs")

    # Verify footer
    assert "daily email notifications enabled" in body.lower(), "Body should mention digest frequency in footer"
    assert "notification preferences" in body.lower(), "Body should mention preferences in footer"
    print("✓ Footer includes preference management information")

    print("\n✓ Test passed: Digest email formatted correctly\n")


@pytest.mark.asyncio
async def test_mark_notifications_as_delivered(digest_test_db: AsyncSession, test_recruiter: Recruiter):
    """
    Test: Mark notifications as delivered after digest is sent.

    Verification steps:
    1. Create multiple undelivered notifications
    2. Call _mark_notifications_as_delivered with notification IDs
    3. Verify notifications have delivered_at timestamp
    4. Verify count of marked notifications is correct
    """
    print("\n=== Test: Mark Notifications as Delivered ===\n")

    # Create undelivered notifications
    print("Creating 5 undelivered notifications...")
    notification_ids = []
    for i in range(5):
        notification = Notification(
            recipient_id=test_recruiter.id,
            notification_type=NotificationType.CANDIDATE_APPLIED,
            title=f"Notification {i+1}",
            message=f"Test notification {i+1}",
            is_read=False,
            delivered_at=None,
            delivery_failed=False,
        )
        digest_test_db.add(notification)
        await digest_test_db.flush()  # Get IDs without committing
        notification_ids.append(str(notification.id))

    await digest_test_db.commit()

    # Verify notifications are undelivered
    print("\nVerifying notifications are initially undelivered...")
    query = select(Notification).where(Notification.id.in_([uuid.UUID(nid) for nid in notification_ids]))
    result = await digest_test_db.execute(query)
    notifications = result.scalars().all()

    for notif in notifications:
        assert notif.delivered_at is None, f"Notification {notif.id} should be undelivered initially"

    print(f"✓ All {len(notifications)} notifications are undelivered")

    # Mark notifications as delivered
    print("\nMarking notifications as delivered...")
    delivered_count = await _mark_notifications_as_delivered(digest_test_db, notification_ids)

    assert delivered_count == 5, f"Expected to mark 5 notifications as delivered, marked {delivered_count}"
    print(f"✓ Marked {delivered_count} notifications as delivered")

    # Verify notifications are now delivered
    print("\nVerifying notifications are now delivered...")
    await digest_test_db.refresh(notifications[0])
    await digest_test_db.refresh(notifications[1])

    query = select(Notification).where(Notification.id.in_([uuid.UUID(nid) for nid in notification_ids]))
    result = await digest_test_db.execute(query)
    delivered_notifications = result.scalars().all()

    for notif in delivered_notifications:
        assert notif.delivered_at is not None, f"Notification {notif.id} should be delivered"

    print(f"✓ All {len(delivered_notifications)} notifications now have delivered_at timestamp")

    print("\n✓ Test passed: Notifications marked as delivered correctly\n")


@pytest.mark.asyncio
async def test_hourly_notification_digest_task(digest_test_db: AsyncSession, test_recruiter: Recruiter):
    """
    Test: End-to-end hourly notification digest task.

    Verification steps:
    1. Create notification preference for hourly digest
    2. Create multiple notifications within last hour
    3. Run send_hourly_notification_digest task
    4. Verify task returns success
    5. Verify correct number of emails sent
    6. Verify notifications are marked as delivered
    7. Verify task processing time is recorded
    """
    print("\n=== Test: Hourly Notification Digest Task (End-to-End) ===\n")

    # Create notification preference for hourly digest
    print("Setting up hourly digest preference...")
    preference = NotificationPreference(
        user_id=test_recruiter.id,
        notification_type=NotificationType.CANDIDATE_APPLIED.value,
        email_enabled=True,
        in_app_enabled=True,
        push_enabled=False,
        sms_enabled=False,
        digest_frequency=DigestFrequency.HOURLY.value,
    )
    digest_test_db.add(preference)
    await digest_test_db.commit()

    # Create notifications within last hour
    print("Creating 4 notifications within last hour...")
    time_cutoff = datetime.utcnow() - timedelta(minutes=30)
    notification_ids = []
    for i in range(4):
        notification = Notification(
            recipient_id=test_recruiter.id,
            notification_type=NotificationType.CANDIDATE_APPLIED,
            title=f"Hourly Digest Notification {i+1}",
            message=f"Test notification {i+1} for hourly digest",
            is_read=False,
            delivered_at=None,
            delivery_failed=False,
            created_at=time_cutoff + timedelta(minutes=i),
        )
        digest_test_db.add(notification)
        await digest_test_db.flush()
        notification_ids.append(str(notification.id))

    await digest_test_db.commit()
    print(f"✓ Created {len(notification_ids)} notifications")

    # Run the hourly digest task
    print("\nRunning hourly notification digest task...")
    task = send_hourly_notification_digest()
    result = task.apply().get()

    print(f"Task result: {result}")

    # Verify task succeeded
    assert result["status"] == "completed", f"Task failed: {result.get('error')}"
    print(f"✓ Task completed successfully")

    # Verify emails sent
    assert result["emails_sent"] == 1, f"Expected 1 email sent, got {result['emails_sent']}"
    print(f"✓ Sent {result['emails_sent']} digest email")

    # Verify notifications processed
    assert result["notifications_processed"] == 4, f"Expected 4 notifications processed, got {result['notifications_processed']}"
    print(f"✓ Processed {result['notifications_processed']} notifications")

    # Verify processing time recorded
    assert "processing_time_ms" in result, "Result missing processing_time_ms"
    print(f"✓ Processing time: {result['processing_time_ms']}ms")

    # Verify notifications marked as delivered
    print("\nVerifying notifications marked as delivered...")
    query = select(Notification).where(Notification.id.in_([uuid.UUID(nid) for nid in notification_ids]))
    result = await digest_test_db.execute(query)
    notifications = result.scalars().all()

    delivered_count = sum(1 for n in notifications if n.delivered_at is not None)
    assert delivered_count == 4, f"Expected 4 notifications delivered, got {delivered_count}"
    print(f"✓ All {delivered_count} notifications marked as delivered")

    print("\n✓ Test passed: Hourly digest task completed successfully\n")


@pytest.mark.asyncio
async def test_daily_notification_digest_task(digest_test_db: AsyncSession, test_recruiter: Recruiter):
    """
    Test: End-to-end daily notification digest task.

    Verification steps:
    1. Create notification preference for daily digest
    2. Create multiple notifications within last 24 hours
    3. Run send_daily_notification_digest task
    4. Verify task returns success
    5. Verify correct number of emails sent
    6. Verify notifications are marked as delivered
    """
    print("\n=== Test: Daily Notification Digest Task (End-to-End) ===\n")

    # Create notification preference for daily digest
    print("Setting up daily digest preference...")
    preference = NotificationPreference(
        user_id=test_recruiter.id,
        notification_type=NotificationType.NEW_MATCH.value,
        email_enabled=True,
        in_app_enabled=True,
        push_enabled=False,
        sms_enabled=False,
        digest_frequency=DigestFrequency.DAILY.value,
    )
    digest_test_db.add(preference)
    await digest_test_db.commit()

    # Create notifications within last 24 hours
    print("Creating 6 notifications within last 24 hours...")
    time_cutoff = datetime.utcnow() - timedelta(hours=12)
    notification_ids = []
    for i in range(6):
        notification = Notification(
            recipient_id=test_recruiter.id,
            notification_type=NotificationType.NEW_MATCH,
            title=f"Daily Digest Notification {i+1}",
            message=f"Test notification {i+1} for daily digest",
            is_read=False,
            delivered_at=None,
            delivery_failed=False,
            created_at=time_cutoff + timedelta(hours=i),
        )
        digest_test_db.add(notification)
        await digest_test_db.flush()
        notification_ids.append(str(notification.id))

    await digest_test_db.commit()
    print(f"✓ Created {len(notification_ids)} notifications")

    # Run the daily digest task
    print("\nRunning daily notification digest task...")
    task = send_daily_notification_digest()
    result = task.apply().get()

    print(f"Task result: {result}")

    # Verify task succeeded
    assert result["status"] == "completed", f"Task failed: {result.get('error')}"
    print(f"✓ Task completed successfully")

    # Verify emails sent
    assert result["emails_sent"] == 1, f"Expected 1 email sent, got {result['emails_sent']}"
    print(f"✓ Sent {result['emails_sent']} digest email")

    # Verify notifications processed
    assert result["notifications_processed"] == 6, f"Expected 6 notifications processed, got {result['notifications_processed']}"
    print(f"✓ Processed {result['notifications_processed']} notifications")

    # Verify notifications marked as delivered
    print("\nVerifying notifications marked as delivered...")
    query = select(Notification).where(Notification.id.in_([uuid.UUID(nid) for nid in notification_ids]))
    result = await digest_test_db.execute(query)
    notifications = result.scalars().all()

    delivered_count = sum(1 for n in notifications if n.delivered_at is not None)
    assert delivered_count == 6, f"Expected 6 notifications delivered, got {delivered_count}"
    print(f"✓ All {delivered_count} notifications marked as delivered")

    print("\n✓ Test passed: Daily digest task completed successfully\n")


@pytest.mark.asyncio
async def test_weekly_notification_digest_task(digest_test_db: AsyncSession, test_recruiter: Recruiter):
    """
    Test: End-to-end weekly notification digest task.

    Verification steps:
    1. Create notification preference for weekly digest
    2. Create multiple notifications within last 7 days
    3. Run send_weekly_notification_digest task
    4. Verify task returns success
    5. Verify correct number of emails sent
    6. Verify notifications are marked as delivered
    """
    print("\n=== Test: Weekly Notification Digest Task (End-to-End) ===\n")

    # Create notification preference for weekly digest
    print("Setting up weekly digest preference...")
    preference = NotificationPreference(
        user_id=test_recruiter.id,
        notification_type=NotificationType.INTERVIEW_SCHEDULED.value,
        email_enabled=True,
        in_app_enabled=True,
        push_enabled=False,
        sms_enabled=False,
        digest_frequency=DigestFrequency.WEEKLY.value,
    )
    digest_test_db.add(preference)
    await digest_test_db.commit()

    # Create notifications within last 7 days
    print("Creating 8 notifications within last 7 days...")
    time_cutoff = datetime.utcnow() - timedelta(days=3)
    notification_ids = []
    for i in range(8):
        notification = Notification(
            recipient_id=test_recruiter.id,
            notification_type=NotificationType.INTERVIEW_SCHEDULED,
            title=f"Weekly Digest Notification {i+1}",
            message=f"Test notification {i+1} for weekly digest",
            is_read=False,
            delivered_at=None,
            delivery_failed=False,
            created_at=time_cutoff + timedelta(days=i/8),  # Spread over 3 days
        )
        digest_test_db.add(notification)
        await digest_test_db.flush()
        notification_ids.append(str(notification.id))

    await digest_test_db.commit()
    print(f"✓ Created {len(notification_ids)} notifications")

    # Run the weekly digest task
    print("\nRunning weekly notification digest task...")
    task = send_weekly_notification_digest()
    result = task.apply().get()

    print(f"Task result: {result}")

    # Verify task succeeded
    assert result["status"] == "completed", f"Task failed: {result.get('error')}"
    print(f"✓ Task completed successfully")

    # Verify emails sent
    assert result["emails_sent"] == 1, f"Expected 1 email sent, got {result['emails_sent']}"
    print(f"✓ Sent {result['emails_sent']} digest email")

    # Verify notifications processed
    assert result["notifications_processed"] == 8, f"Expected 8 notifications processed, got {result['notifications_processed']}"
    print(f"✓ Processed {result['notifications_processed']} notifications")

    # Verify notifications marked as delivered
    print("\nVerifying notifications marked as delivered...")
    query = select(Notification).where(Notification.id.in_([uuid.UUID(nid) for nid in notification_ids]))
    result = await digest_test_db.execute(query)
    notifications = result.scalars().all()

    delivered_count = sum(1 for n in notifications if n.delivered_at is not None)
    assert delivered_count == 8, f"Expected 8 notifications delivered, got {delivered_count}"
    print(f"✓ All {delivered_count} notifications marked as delivered")

    print("\n✓ Test passed: Weekly digest task completed successfully\n")


@pytest.mark.asyncio
async def test_notification_aggregation_in_digest(digest_test_db: AsyncSession, test_recruiter: Recruiter):
    """
    Test: Notifications are properly grouped by type in digest emails.

    Verification steps:
    1. Create notifications of multiple types (candidate_applied, new_match, interview_scheduled)
    2. Set digest preferences for all types
    3. Run digest task
    4. Verify email body groups notifications by type
    5. Verify group headers are correct
    """
    print("\n=== Test: Notification Aggregation in Digest ===\n")

    # Create preferences for multiple notification types
    print("Setting up digest preferences for multiple notification types...")
    for notif_type in [NotificationType.CANDIDATE_APPLIED, NotificationType.NEW_MATCH, NotificationType.INTERVIEW_SCHEDULED]:
        preference = NotificationPreference(
            user_id=test_recruiter.id,
            notification_type=notif_type.value,
            email_enabled=True,
            in_app_enabled=True,
            push_enabled=False,
            sms_enabled=False,
            digest_frequency=DigestFrequency.HOURLY.value,
        )
        digest_test_db.add(preference)
    await digest_test_db.commit()

    # Create notifications of different types
    print("\nCreating notifications of different types...")
    time_cutoff = datetime.utcnow() - timedelta(minutes=30)

    # 3 candidate_applied notifications
    for i in range(3):
        notification = Notification(
            recipient_id=test_recruiter.id,
            notification_type=NotificationType.CANDIDATE_APPLIED,
            title=f"Candidate Applied {i+1}",
            message=f"Candidate {i+1} applied",
            created_at=time_cutoff + timedelta(minutes=i),
            delivered_at=None,
            delivery_failed=False,
        )
        digest_test_db.add(notification)

    # 2 new_match notifications
    for i in range(2):
        notification = Notification(
            recipient_id=test_recruiter.id,
            notification_type=NotificationType.NEW_MATCH,
            title=f"New Match {i+1}",
            message=f"New match {i+1} found",
            created_at=time_cutoff + timedelta(minutes=10+i),
            delivered_at=None,
            delivery_failed=False,
        )
        digest_test_db.add(notification)

    # 1 interview_scheduled notification
    notification = Notification(
        recipient_id=test_recruiter.id,
        notification_type=NotificationType.INTERVIEW_SCHEDULED,
        title="Interview Scheduled",
        message="Interview scheduled with candidate",
        created_at=time_cutoff + timedelta(minutes=20),
        delivered_at=None,
        delivery_failed=False,
    )
    digest_test_db.add(notification)

    await digest_test_db.commit()
    print(f"✓ Created 6 notifications of 3 different types")

    # Query pending notifications
    print("\nQuerying pending notifications for digest...")
    cutoff_time = datetime.utcnow() - timedelta(hours=1)
    pending_notifications = await _get_pending_notifications_for_digest(
        digest_test_db,
        DigestFrequency.HOURLY.value,
        cutoff_time,
    )

    print(f"Found {len(pending_notifications)} pending notifications")

    # Group by type for digest
    from collections import defaultdict
    grouped_notifications = defaultdict(list)
    for notif in pending_notifications:
        notif_type = notif.get("notification_type")
        grouped_notifications[notif_type].append(notif)

    print(f"\n✓ Notifications grouped into {len(grouped_notifications)} types:")
    for notif_type, notifs in grouped_notifications.items():
        print(f"  - {notif_type}: {len(notifs)} notifications")

    # Verify grouping
    assert len(grouped_notifications) == 3, f"Expected 3 groups, got {len(grouped_notifications)}"
    assert "candidate_applied" in grouped_notifications, "Missing candidate_applied group"
    assert "new_match" in grouped_notifications, "Missing new_match group"
    assert "interview_scheduled" in grouped_notifications, "Missing interview_scheduled group"

    assert len(grouped_notifications["candidate_applied"]) == 3, f"Expected 3 candidate_applied, got {len(grouped_notifications['candidate_applied'])}"
    assert len(grouped_notifications["new_match"]) == 2, f"Expected 2 new_match, got {len(grouped_notifications['new_match'])}"
    assert len(grouped_notifications["interview_scheduled"]) == 1, f"Expected 1 interview_scheduled, got {len(grouped_notifications['interview_scheduled'])}"

    # Format digest email to verify grouping in output
    print("\nFormatting digest email with grouped notifications...")
    email_details = format_notification_digest_email(
        recipient_email=test_recruiter.email,
        recipient_name=test_recruiter.name,
        notifications=pending_notifications,
        digest_frequency="hourly",
    )

    email_body = email_details["body"]

    # Verify email contains group headers
    assert "Candidate_Applied" in email_body or "candidate_applied" in email_body, "Email should mention candidate_applied"
    assert "New_Match" in email_body or "new_match" in email_body, "Email should mention new_match"
    assert "Interview_Scheduled" in email_body or "interview_scheduled" in email_body, "Email should mention interview_scheduled"

    print("✓ Email body contains all notification type groups")

    print("\n✓ Test passed: Notifications properly aggregated by type\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
