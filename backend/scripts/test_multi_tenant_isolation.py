#!/usr/bin/env python3
"""
Manual verification script for multi-tenant organization isolation.

This script allows manual testing of organization isolation without pytest.
Run this script to verify that:
1. Organizations can be created and isolated
2. Candidates are properly scoped to organizations
3. No cross-organization data leakage occurs

Usage:
    cd backend
    python scripts/test_multi_tenant_isolation.py
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from httpx import AsyncClient, ASGITransport
from main import app


async def create_organization(client: AsyncClient, name: str, slug: str) -> dict:
    """Helper to create an organization."""
    response = await client.post(
        "/api/organizations/",
        json={"name": name, "slug": slug}
    )
    if response.status_code != 201:
        print(f"❌ Failed to create {name}: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)
    return response.json()


async def upload_candidate(client: AsyncClient, org_id: str, filename: str) -> dict:
    """Helper to upload a test candidate (resume)."""
    # Create a minimal PDF content
    pdf_content = b"%PDF-1.4\nTest content"

    files = {"file": (filename, pdf_content, "application/pdf")}
    headers = {"X-Organization-ID": org_id}

    response = await client.post(
        "/api/resumes/upload",
        headers=headers,
        files=files
    )
    if response.status_code != 201:
        print(f"❌ Failed to upload candidate: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)
    return response.json()


async def get_candidates(client: AsyncClient, org_id: str) -> list:
    """Helper to get candidates for an organization."""
    response = await client.get(
        "/api/candidates/",
        headers={"X-Organization-ID": org_id}
    )
    if response.status_code != 200:
        print(f"❌ Failed to get candidates: {response.status_code}")
        print(f"   Response: {response.text}")
        return []
    data = response.json()
    return data.get("candidates", data.get("items", []))


async def main():
    """Main verification workflow."""
    print("=" * 70)
    print("MULTI-TENANT ORGANIZATION ISOLATION VERIFICATION")
    print("=" * 70)
    print()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Step 1: Create organizations
        print("📋 Step 1: Creating organizations...")
        org_a = await create_organization(client, "Test Organization A", "test-org-a")
        org_b = await create_organization(client, "Test Organization B", "test-org-b")
        print(f"✓ Created Organization A: {org_a['id']} ({org_a['name']})")
        print(f"✓ Created Organization B: {org_b['id']} ({org_b['name']})")
        print()

        # Step 2: Upload candidates to Organization A
        print("📋 Step 2: Uploading candidates to Organization A...")
        org_a_candidates = []
        for i in range(3):
            candidate = await upload_candidate(client, org_a['id'], f"org_a_candidate_{i}.pdf")
            org_a_candidates.append(candidate['id'])
            print(f"✓ Uploaded candidate {i+1}/3 to Organization A: {candidate['id']}")
        print()

        # Step 3: Upload candidates to Organization B
        print("📋 Step 3: Uploading candidates to Organization B...")
        org_b_candidates = []
        for i in range(2):
            candidate = await upload_candidate(client, org_b['id'], f"org_b_candidate_{i}.pdf")
            org_b_candidates.append(candidate['id'])
            print(f"✓ Uploaded candidate {i+1}/2 to Organization B: {candidate['id']}")
        print()

        # Step 4: Verify Organization A sees only its candidates
        print("📋 Step 4: Verifying Organization A isolation...")
        org_a_result = await get_candidates(client, org_a['id'])
        org_a_candidate_ids = [c['id'] for c in org_a_result]

        print(f"Organization A can see {len(org_a_candidate_ids)} candidates:")
        for cid in org_a_candidate_ids:
            print(f"  - {cid}")

        # Check that all Org A candidates are visible
        missing_in_a = [c for c in org_a_candidates if c not in org_a_candidate_ids]
        if missing_in_a:
            print(f"❌ ERROR: Organization A cannot see its own candidates: {missing_in_a}")
            sys.exit(1)

        # Check that no Org B candidates are visible to Org A
        leakage_to_a = [c for c in org_b_candidates if c in org_a_candidate_ids]
        if leakage_to_a:
            print(f"❌ ERROR: Organization A can see Organization B's candidates: {leakage_to_a}")
            print("❌ CROSS-ORGANIZATION DATA LEAKAGE DETECTED!")
            sys.exit(1)
        else:
            print("✓ Organization A sees only its own candidates (no leakage from Org B)")
        print()

        # Step 5: Verify Organization B sees only its candidates
        print("📋 Step 5: Verifying Organization B isolation...")
        org_b_result = await get_candidates(client, org_b['id'])
        org_b_candidate_ids = [c['id'] for c in org_b_result]

        print(f"Organization B can see {len(org_b_candidate_ids)} candidates:")
        for cid in org_b_candidate_ids:
            print(f"  - {cid}")

        # Check that all Org B candidates are visible
        missing_in_b = [c for c in org_b_candidates if c not in org_b_candidate_ids]
        if missing_in_b:
            print(f"❌ ERROR: Organization B cannot see its own candidates: {missing_in_b}")
            sys.exit(1)

        # Check that no Org A candidates are visible to Org B
        leakage_to_b = [c for c in org_a_candidates if c in org_b_candidate_ids]
        if leakage_to_b:
            print(f"❌ ERROR: Organization B can see Organization A's candidates: {leakage_to_b}")
            print("❌ CROSS-ORGANIZATION DATA LEAKAGE DETECTED!")
            sys.exit(1)
        else:
            print("✓ Organization B sees only its own candidates (no leakage from Org A)")
        print()

        # Final summary
        print("=" * 70)
        print("✅ ALL VERIFICATION STEPS PASSED!")
        print("=" * 70)
        print()
        print("Summary:")
        print(f"  • Organization A: {len(org_a_candidates)} candidates uploaded, {len(org_a_candidate_ids)} visible")
        print(f"  • Organization B: {len(org_b_candidates)} candidates uploaded, {len(org_b_candidate_ids)} visible")
        print(f"  • Cross-organization leakage: NONE ✓")
        print()
        print("✅ Multi-tenant organization isolation is working correctly!")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
