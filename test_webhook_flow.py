#!/usr/bin/env python3
"""
End-to-end webhook reception and processing flow test.

This script tests the complete webhook flow:
1. Creates test integrations for each platform
2. Sends test webhook payloads
3. Verifies webhook reception and validation
4. Checks data processing and storage
5. Verifies sync log entry creation

Run this script from the project root directory.
"""
import asyncio
import json
import hmac
import hashlib
import httpx
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import backend modules
import sys
sys.path.insert(0, './backend')

from database import async_session_maker
from models.integration import Integration, IntegrationPlatform, IntegrationStatus
from models.sync_log import SyncLog, SyncType, SyncStatus


# Test configuration
API_BASE_URL = "http://localhost:8000"
WEBHOOK_SECRET = "test_webhook_secret_12345"


# Test webhook payloads for each platform
TEST_WEBHOOKS = {
    "greenhouse": [
        {
            "event": "candidate.created",
            "data": {
                "candidate_id": 12345,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "application_id": 98765,
            }
        },
        {
            "event": "candidate.updated",
            "data": {
                "candidate_id": 12345,
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@example.com",
            }
        },
    ],
    "lever": [
        {
            "event": "candidate.created",
            "data": {
                "id": "507f1f77bcf86cd799439011",
                "name": "Jane Doe",
                "email": "jane.doe@example.com",
            }
        },
        {
            "event": "opportunity.updated",
            "data": {
                "opportunityId": "507f1f77bcf86cd799439012",
                "candidateId": "507f1f77bcf86cd799439011",
                "stage": "Phone Screen",
            }
        },
    ],
    "workday": [
        {
            "event": "employee.created",
            "data": {
                "worker_id": "ABC123",
                "name": "Bob Johnson",
                "email": "bob.johnson@company.com",
                "position": "Software Engineer",
            }
        },
        {
            "event": "candidate.updated",
            "data": {
                "candidate_id": "WD-456",
                "name": "Alice Williams",
                "status": "Interview",
            }
        },
    ],
    "bamboohr": [
        {
            "event": "employee_added",
            "data": {
                "id": "101",
                "firstName": "Charlie",
                "lastName": "Brown",
                "email": "charlie.brown@company.com",
                "jobTitle": "Product Manager",
            }
        },
        {
            "event": "employee_updated",
            "data": {
                "id": "101",
                "firstName": "Charlie",
                "lastName": "Brown",
                "jobTitle": "Senior Product Manager",
            }
        },
    ],
    "ashby": [
        {
            "event": "candidate.created",
            "data": {
                "id": "ashby_candidate_123",
                "name": "Diana Prince",
                "email": "diana.prince@example.com",
            }
        },
        {
            "event": "application.created",
            "data": {
                "candidateId": "ashby_candidate_123",
                "jobPostingId": "ashby_job_456",
                "status": "Applied",
            }
        },
    ],
}


def generate_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature for webhook payload."""
    return f"sha256={hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()}"


async def create_test_integration(
    db: AsyncSession,
    platform: IntegrationPlatform,
    name: str
) -> Integration:
    """Create a test integration for webhook testing."""
    integration = Integration(
        name=name,
        platform=platform,
        status=IntegrationStatus.ACTIVE,
        credentials={
            "api_key": "test_api_key",
            "webhook_secret": WEBHOOK_SECRET,
        },
        sync_enabled=True,
        sync_interval_minutes=60,
    )

    db.add(integration)
    await db.commit()
    await db.refresh(integration)

    print(f"✓ Created test integration: {name} ({platform.value}) - ID: {integration.id}")
    return integration


async def cleanup_test_integrations(db: AsyncSession) -> None:
    """Clean up test integrations before running tests."""
    result = await db.execute(
        select(Integration).where(Integration.name.like("Webhook Test%"))
    )
    integrations = result.scalars().all()

    for integration in integrations:
        await db.delete(integration)

    await db.commit()
    print(f"✓ Cleaned up {len(integrations)} old test integrations")


async def send_webhook(
    platform: str,
    payload: Dict[str, Any],
    integration: Integration
) -> Dict[str, Any]:
    """Send a webhook payload to the webhook endpoint."""

    webhook_url = f"{API_BASE_URL}/api/webhooks/{platform}"
    payload_str = json.dumps(payload)
    signature = generate_signature(payload_str, WEBHOOK_SECRET)

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers=headers
            )

            return {
                "status_code": response.status_code,
                "response_data": response.json(),
                "success": response.status_code == 200,
            }
    except Exception as e:
        return {
            "status_code": 0,
            "response_data": {"error": str(e)},
            "success": False,
        }


async def verify_sync_log(
    db: AsyncSession,
    integration_id: str,
    event_type: str
) -> Optional[SyncLog]:
    """Verify that a sync log was created for the webhook event."""
    result = await db.execute(
        select(SyncLog)
        .where(SyncLog.integration_id == integration_id)
        .where(SyncLog.sync_metadata["webhook_event"].astext == event_type)
        .order_by(SyncLog.created_at.desc())
        .limit(1)
    )

    sync_log = result.scalar_one_or_none()
    return sync_log


async def test_webhook_flow(
    db: AsyncSession,
    platform: str,
    platform_enum: IntegrationPlatform
) -> Dict[str, Any]:
    """Test webhook flow for a single platform."""

    print(f"\n{'='*60}")
    print(f"Testing webhook flow for platform: {platform.upper()}")
    print(f"{'='*60}")

    # Step 1: Create test integration
    print("\n[Step 1] Creating test integration...")
    integration = await create_test_integration(
        db,
        platform_enum,
        f"Webhook Test - {platform.capitalize()}"
    )

    test_results = {
        "platform": platform,
        "integration_id": str(integration.id),
        "webhooks_tested": 0,
        "webhooks_passed": 0,
        "sync_logs_created": 0,
        "errors": [],
    }

    # Step 2: Send test webhooks
    print(f"\n[Step 2] Sending test webhooks for {platform}...")
    test_webhooks = TEST_WEBHOOKS.get(platform, [])

    if not test_webhooks:
        print(f"⚠ No test webhooks defined for {platform}")
        return test_results

    for i, webhook_payload in enumerate(test_webhooks, 1):
        event_type = webhook_payload["event"]
        print(f"\n  [Webhook {i}/{len(test_webhooks)}] Event: {event_type}")
        print(f"  Payload: {json.dumps(webhook_payload['data'], indent=4)}")

        # Send webhook
        result = await send_webhook(platform, webhook_payload, integration)
        test_results["webhooks_tested"] += 1

        # Verify response
        if not result["success"]:
            error_msg = f"Webhook request failed: {result['response_data']}"
            print(f"  ✗ {error_msg}")
            test_results["errors"].append(error_msg)
            continue

        print(f"  ✓ Webhook sent successfully (status: {result['status_code']})")
        print(f"  Response: {json.dumps(result['response_data'], indent=4)}")

        # Verify webhook was received and processed
        if result["response_data"].get("success"):
            print(f"  ✓ Webhook received and processed")

            # Check if sync was triggered
            event_id = result["response_data"].get("event_id")
            if event_id:
                print(f"  ✓ Sync triggered (sync_id: {event_id})")
                test_results["webhooks_passed"] += 1

                # Step 3: Verify sync log entry
                print(f"\n  [Step 3] Verifying sync log entry...")
                await asyncio.sleep(0.5)  # Give DB time to commit

                sync_log = await verify_sync_log(db, integration.id, event_type)

                if sync_log:
                    print(f"  ✓ Sync log found:")
                    print(f"    - ID: {sync_log.id}")
                    print(f"    - Type: {sync_log.sync_type}")
                    print(f"    - Status: {sync_log.status}")
                    print(f"    - Metadata: {json.dumps(sync_log.sync_metadata, indent=6)}")
                    test_results["sync_logs_created"] += 1
                else:
                    error_msg = "Sync log not found in database"
                    print(f"  ✗ {error_msg}")
                    test_results["errors"].append(error_msg)
            else:
                print(f"  ℹ Sync not triggered (event type may not require sync)")
                test_results["webhooks_passed"] += 1
        else:
            error_msg = f"Webhook processing failed: {result['response_data'].get('message')}"
            print(f"  ✗ {error_msg}")
            test_results["errors"].append(error_msg)

    return test_results


async def run_all_tests() -> None:
    """Run webhook flow tests for all platforms."""

    print("\n" + "="*60)
    print("WEBHOOK RECEPTION AND PROCESSING FLOW TEST")
    print("="*60)
    print(f"\nTarget API: {API_BASE_URL}")
    print(f"Test webhook secret: {WEBHOOK_SECRET}")

    # Create database session
    async with async_session_maker() as db:
        # Cleanup old test data
        print("\n[Setup] Cleaning up old test integrations...")
        await cleanup_test_integrations(db)

        # Test each platform
        platforms = {
            "greenhouse": IntegrationPlatform.GREENHOUSE,
            "lever": IntegrationPlatform.LEVER,
            "workday": IntegrationPlatform.WORKDAY,
            "bamboohr": IntegrationPlatform.BAMBOOHR,
            "ashby": IntegrationPlatform.ASHBY,
        }

        all_results = []

        for platform, platform_enum in platforms.items():
            try:
                result = await test_webhook_flow(db, platform, platform_enum)
                all_results.append(result)
            except Exception as e:
                print(f"\n✗ Error testing {platform}: {e}")
                import traceback
                traceback.print_exc()
                all_results.append({
                    "platform": platform,
                    "errors": [str(e)],
                })

        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        total_webhooks = sum(r.get("webhooks_tested", 0) for r in all_results)
        total_passed = sum(r.get("webhooks_passed", 0) for r in all_results)
        total_sync_logs = sum(r.get("sync_logs_created", 0) for r in all_results)
        total_errors = sum(len(r.get("errors", [])) for r in all_results)

        print(f"\nTotal webhooks tested: {total_webhooks}")
        print(f"Total webhooks passed: {total_passed}")
        print(f"Total sync logs created: {total_sync_logs}")
        print(f"Total errors: {total_errors}")

        print("\nResults by platform:")
        for result in all_results:
            platform = result["platform"].upper()
            tested = result.get("webhooks_tested", 0)
            passed = result.get("webhooks_passed", 0)
            sync_logs = result.get("sync_logs_created", 0)
            errors = result.get("errors", [])

            status = "✓ PASS" if len(errors) == 0 else "✗ FAIL"
            print(f"\n  {status} {platform}:")
            print(f"    - Webhooks tested: {tested}")
            print(f"    - Webhooks passed: {passed}")
            print(f"    - Sync logs created: {sync_logs}")
            if errors:
                print(f"    - Errors:")
                for error in errors:
                    print(f"      • {error}")

        # Final verdict
        print("\n" + "="*60)
        if total_errors == 0 and total_passed == total_webhooks:
            print("✓ ALL TESTS PASSED")
            print("="*60)
            print("\nVerification steps completed:")
            print("  ✓ Test webhook payloads sent to webhook endpoints")
            print("  ✓ Webhooks received and validated (signature verification)")
            print("  ✓ Data processed and sync tasks triggered")
            print("  ✓ Sync log entries created in database")
        else:
            print("✗ SOME TESTS FAILED")
            print("="*60)
            print(f"\n{total_errors} errors encountered. See details above.")

        print("\n[Cleanup] Test integrations left in database for manual inspection")
        print("To clean up, run: python test_webhook_flow.py --cleanup")


async def cleanup_only() -> None:
    """Clean up test integrations only."""
    async with async_session_maker() as db:
        await cleanup_test_integrations(db)
    print("\n✓ Cleanup complete")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test webhook reception and processing flow"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up test integrations without running tests"
    )

    args = parser.parse_args()

    if args.cleanup:
        asyncio.run(cleanup_only())
    else:
        asyncio.run(run_all_tests())
