"""
Integration tests for comment editing and deletion with time restrictions.

This test suite verifies:
1. Comments can be edited within 5 minutes of creation
2. Comments cannot be edited after 5 minutes have passed
3. Soft delete functionality works correctly
4. Edit window only applies to content changes, not resolved status
5. edits_count is properly incremented on each edit
"""
import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from uuid import uuid4
from unittest.mock import Mock, patch

from main import app
from database import get_db
from models.resume import Resume
from models.recruiter import Recruiter
from models.team_comment import TeamComment


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_edit_delete_restrictions.db"


@pytest.fixture
async def test_db():
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Create test client with database override."""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_data(test_db: AsyncSession):
    """Create test data: resume and recruiter."""
    # Create test resume
    resume = Resume(
        id=uuid4(),
        filename="test_candidate.pdf",
        file_path="/test/test_candidate.pdf",
        status="processed",
    )
    test_db.add(resume)

    # Create test recruiter
    author_recruiter = Recruiter(
        id=uuid4(),
        email="author@example.com",
        name="Author User",
    )
    test_db.add(author_recruiter)

    await test_db.commit()

    return {
        "resume": resume,
        "author": author_recruiter,
    }


@pytest.mark.asyncio
async def test_create_comment(test_data, client: AsyncClient):
    """Test creating a new comment."""
    response = await client.post(
        "/api/team-comments/",
        json={
            "resume_id": str(test_data["resume"].id),
            "author_id": str(test_data["author"].id),
            "content": "This is a test comment for editing restrictions",
            "parent_comment_id": None,
            "is_resolved": False
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "This is a test comment for editing restrictions"
    assert data["edits_count"] == 0
    assert data["is_deleted"] is False
    return data


@pytest.mark.asyncio
async def test_edit_comment_within_window(test_data, client: AsyncClient, test_db: AsyncSession):
    """Test editing a comment within the 5-minute window (should succeed)."""
    # Create a comment
    comment_response = await client.post(
        "/api/team-comments/",
        json={
            "resume_id": str(test_data["resume"].id),
            "author_id": str(test_data["author"].id),
            "content": "Original content",
            "parent_comment_id": None,
            "is_resolved": False
        }
    )
    assert comment_response.status_code == 201
    comment = comment_response.json()
    comment_id = comment["id"]

    # Edit immediately (within window)
    edit_response = await client.put(
        f"/api/team-comments/{comment_id}",
        json={
            "content": "Updated content"
        }
    )

    assert edit_response.status_code == 200
    updated_comment = edit_response.json()
    assert updated_comment["content"] == "Updated content"
    assert updated_comment["edits_count"] == 1


@pytest.mark.asyncio
async def test_edit_comment_after_window(test_data, client: AsyncClient, test_db: AsyncSession):
    """Test editing a comment after the 5-minute window (should fail)."""
    # Create a comment
    comment = TeamComment(
        id=uuid4(),
        resume_id=test_data["resume"].id,
        author_id=test_data["author"].id,
        content="Old content",
        parent_comment_id=None,
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=6),  # 6 minutes ago
        updated_at=datetime.now(timezone.utc) - timedelta(minutes=6),
    )
    test_db.add(comment)
    await test_db.commit()

    # Try to edit (should fail due to time window)
    edit_response = await client.put(
        f"/api/team-comments/{comment.id}",
        json={
            "content": "New content"
        }
    )

    assert edit_response.status_code == 403
    error_detail = edit_response.json()
    assert "can only be edited within 5 minutes" in error_detail["detail"].lower()


@pytest.mark.asyncio
async def test_edit_comment_at_boundary(test_data, client: AsyncClient, test_db: AsyncSession):
    """Test editing a comment exactly at the 5-minute boundary (should succeed)."""
    # Create a comment exactly 5 minutes ago
    comment = TeamComment(
        id=uuid4(),
        resume_id=test_data["resume"].id,
        author_id=test_data["author"].id,
        content="Boundary content",
        parent_comment_id=None,
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=5),  # Exactly 5 minutes
        updated_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    test_db.add(comment)
    await test_db.commit()

    # Try to edit (should succeed as we're at the boundary)
    edit_response = await client.put(
        f"/api/team-comments/{comment.id}",
        json={
            "content": "Boundary edited content"
        }
    )

    # This should succeed - at exactly 5 minutes it's still editable
    assert edit_response.status_code == 200
    updated_comment = edit_response.json()
    assert updated_comment["content"] == "Boundary edited content"
    assert updated_comment["edits_count"] == 1


@pytest.mark.asyncio
async def test_edit_comment_just_after_boundary(test_data, client: AsyncClient, test_db: AsyncSession):
    """Test editing a comment just after the 5-minute boundary (should fail)."""
    # Create a comment 5 minutes and 1 second ago
    comment = TeamComment(
        id=uuid4(),
        resume_id=test_data["resume"].id,
        author_id=test_data["author"].id,
        content="Just after boundary content",
        parent_comment_id=None,
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=5, seconds=1),  # 5:01 ago
        updated_at=datetime.now(timezone.utc) - timedelta(minutes=5, seconds=1),
    )
    test_db.add(comment)
    await test_db.commit()

    # Try to edit (should fail)
    edit_response = await client.put(
        f"/api/team-comments/{comment.id}",
        json={
            "content": "Should not work"
        }
    )

    assert edit_response.status_code == 403
    error_detail = edit_response.json()
    assert "can only be edited within 5 minutes" in error_detail["detail"].lower()


@pytest.mark.asyncio
async def test_resolve_status_no_time_restriction(test_data, client: AsyncClient, test_db: AsyncSession):
    """Test that resolved status can be changed regardless of time window."""
    # Create an old comment (10 minutes ago)
    comment = TeamComment(
        id=uuid4(),
        resume_id=test_data["resume"].id,
        author_id=test_data["author"].id,
        content="Old comment to resolve",
        parent_comment_id=None,
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        updated_at=datetime.now(timezone.utc) - timedelta(minutes=10),
    )
    test_db.add(comment)
    await test_db.commit()

    # Change resolved status (should succeed even though content edit would fail)
    resolve_response = await client.put(
        f"/api/team-comments/{comment.id}",
        json={
            "is_resolved": True
        }
    )

    assert resolve_response.status_code == 200
    updated_comment = resolve_response.json()
    assert updated_comment["is_resolved"] is True
    assert updated_comment["edits_count"] == 0  # No edit count increment


@pytest.mark.asyncio
async def test_delete_comment_soft_delete(test_data, client: AsyncClient, test_db: AsyncSession):
    """Test soft delete functionality."""
    # Create a comment
    comment_response = await client.post(
        "/api/team-comments/",
        json={
            "resume_id": str(test_data["resume"].id),
            "author_id": str(test_data["author"].id),
            "content": "Comment to be deleted",
            "parent_comment_id": None,
            "is_resolved": False
        }
    )
    assert comment_response.status_code == 201
    comment = comment_response.json()
    comment_id = comment["id"]

    # Delete the comment
    delete_response = await client.delete(f"/api/team-comments/{comment_id}")

    assert delete_response.status_code == 200
    delete_data = delete_response.json()
    assert delete_data["message"] == "Team comment deleted successfully"
    assert delete_data["id"] == comment_id

    # Verify soft delete in database
    result = await test_db.execute(
        select(TeamComment).where(TeamComment.id == uuid4(comment_id))
    )
    deleted_comment = result.scalar_one_or_none()

    assert deleted_comment is not None
    assert deleted_comment.is_deleted is True
    assert deleted_comment.content == "Comment to be deleted"  # Content preserved


@pytest.mark.asyncio
async def test_deleted_comment_not_in_list(test_data, client: AsyncClient, test_db: AsyncSession):
    """Test that deleted comments don't appear in default list views."""
    # Create a comment
    comment_response = await client.post(
        "/api/team-comments/",
        json={
            "resume_id": str(test_data["resume"].id),
            "author_id": str(test_data["author"].id),
            "content": "Visible comment",
            "parent_comment_id": None,
            "is_resolved": False
        }
    )
    comment = comment_response.json()
    comment_id = comment["id"]

    # Verify it's in the list
    list_response = await client.get(
        "/api/team-comments/",
        params={"resume_id": str(test_data["resume"].id)}
    )
    assert list_response.status_code == 200
    comments = list_response.json()["comments"]
    assert any(c["id"] == comment_id for c in comments)

    # Delete the comment
    delete_response = await client.delete(f"/api/team-comments/{comment_id}")
    assert delete_response.status_code == 200

    # Verify it's no longer in the list
    list_response_after = await client.get(
        "/api/team-comments/",
        params={"resume_id": str(test_data["resume"].id)}
    )
    assert list_response_after.status_code == 200
    comments_after = list_response_after.json()["comments"]
    assert not any(c["id"] == comment_id for c in comments_after)


@pytest.mark.asyncio
async def test_deleted_comment_visible_with_flag(test_data, client: AsyncClient, test_db: AsyncSession):
    """Test that deleted comments appear when include_deleted flag is set."""
    # Create a comment
    comment_response = await client.post(
        "/api/team-comments/",
        json={
            "resume_id": str(test_data["resume"].id),
            "author_id": str(test_data["author"].id),
            "content": "Comment with soft delete",
            "parent_comment_id": None,
            "is_resolved": False
        }
    )
    comment = comment_response.json()
    comment_id = comment["id"]

    # Delete the comment
    delete_response = await client.delete(f"/api/team-comments/{comment_id}")
    assert delete_response.status_code == 200

    # List with include_deleted flag
    list_response = await client.get(
        "/api/team-comments/",
        params={
            "resume_id": str(test_data["resume"].id),
            "include_deleted": True
        }
    )
    assert list_response.status_code == 200
    comments = list_response.json()["comments"]

    # Should find the deleted comment
    deleted_comment = next((c for c in comments if c["id"] == comment_id), None)
    assert deleted_comment is not None
    assert deleted_comment["is_deleted"] is True


@pytest.mark.asyncio
async def test_edit_multiple_times_within_window(test_data, client: AsyncClient):
    """Test editing a comment multiple times within the time window."""
    # Create a comment
    comment_response = await client.post(
        "/api/team-comments/",
        json={
            "resume_id": str(test_data["resume"].id),
            "author_id": str(test_data["author"].id),
            "content": "Version 1",
            "parent_comment_id": None,
            "is_resolved": False
        }
    )
    comment = comment_response.json()
    comment_id = comment["id"]

    # First edit
    response1 = await client.put(
        f"/api/team-comments/{comment_id}",
        json={"content": "Version 2"}
    )
    assert response1.status_code == 200
    assert response1.json()["edits_count"] == 1

    # Second edit
    response2 = await client.put(
        f"/api/team-comments/{comment_id}",
        json={"content": "Version 3"}
    )
    assert response2.status_code == 200
    assert response2.json()["edits_count"] == 2

    # Third edit
    response3 = await client.put(
        f"/api/team-comments/{comment_id}",
        json={"content": "Version 4"}
    )
    assert response3.status_code == 200
    assert response3.json()["edits_count"] == 3


@pytest.mark.asyncio
async def test_get_deleted_comment_by_id(test_data, client: AsyncClient, test_db: AsyncSession):
    """Test that deleted comments can still be retrieved by ID."""
    # Create a comment
    comment_response = await client.post(
        "/api/team-comments/",
        json={
            "resume_id": str(test_data["resume"].id),
            "author_id": str(test_data["author"].id),
            "content": "Delete me but keep my data",
            "parent_comment_id": None,
            "is_resolved": False
        }
    )
    comment = comment_response.json()
    comment_id = comment["id"]

    # Delete the comment
    delete_response = await client.delete(f"/api/team-comments/{comment_id}")
    assert delete_response.status_code == 200

    # Get the deleted comment by ID
    get_response = await client.get(f"/api/team-comments/{comment_id}")
    assert get_response.status_code == 200

    retrieved_comment = get_response.json()
    assert retrieved_comment["id"] == comment_id
    assert retrieved_comment["is_deleted"] is True
    assert retrieved_comment["content"] == "Delete me but keep my data"


@pytest.mark.asyncio
async def test_edit_deleted_comment_fails(test_data, client: AsyncClient, test_db: AsyncSession):
    """Test that editing a deleted comment is not possible."""
    # Create a comment
    comment_response = await client.post(
        "/api/team-comments/",
        json={
            "resume_id": str(test_data["resume"].id),
            "author_id": str(test_data["author"].id),
            "content": "Delete and try to edit",
            "parent_comment_id": None,
            "is_resolved": False
        }
    )
    comment = comment_response.json()
    comment_id = comment["id"]

    # Delete the comment
    delete_response = await client.delete(f"/api/team-comments/{comment_id}")
    assert delete_response.status_code == 200

    # Try to edit the deleted comment
    edit_response = await client.put(
        f"/api/team-comments/{comment_id}",
        json={"content": "Should not work"}
    )

    # Should fail - deleted comments can't be edited
    # The API will still return 403 because it's checking the time window
    # In a real implementation, we might want to check is_deleted first
    # For now, this test documents current behavior
    assert edit_response.status_code in [403, 404]


@pytest.mark.asyncio
async def test_delete_already_deleted_comment(test_data, client: AsyncClient, test_db: AsyncSession):
    """Test deleting an already deleted comment."""
    # Create a comment
    comment_response = await client.post(
        "/api/team-comments/",
        json={
            "resume_id": str(test_data["resume"].id),
            "author_id": str(test_data["author"].id),
            "content": "Delete me twice",
            "parent_comment_id": None,
            "is_resolved": False
        }
    )
    comment = comment_response.json()
    comment_id = comment["id"]

    # First delete
    delete1 = await client.delete(f"/api/team-comments/{comment_id}")
    assert delete1.status_code == 200

    # Second delete (should succeed - idempotent operation)
    delete2 = await client.delete(f"/api/team-comments/{comment_id}")
    assert delete2.status_code == 200
    assert delete2.json()["message"] == "Team comment deleted successfully"


@pytest.mark.asyncio
async def test_edit_and_resolve_together(test_data, client: AsyncClient, test_db: AsyncSession):
    """Test editing content and changing resolved status in same request."""
    # Create a comment
    comment_response = await client.post(
        "/api/team-comments/",
        json={
            "resume_id": str(test_data["resume"].id),
            "author_id": str(test_data["author"].id),
            "content": "Original",
            "parent_comment_id": None,
            "is_resolved": False
        }
    )
    comment = comment_response.json()
    comment_id = comment["id"]

    # Edit both content and resolved status
    response = await client.put(
        f"/api/team-comments/{comment_id}",
        json={
            "content": "Updated content",
            "is_resolved": True
        }
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["content"] == "Updated content"
    assert updated["is_resolved"] is True
    assert updated["edits_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
