"""
Integration tests for comment resolution cascading functionality.

This test suite verifies that when a parent comment is marked as resolved or unresolved,
the resolution status cascades to all child comments (replies) recursively.
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.team_comment import TeamComment
from models.resume import Resume
from models.recruiter import Recruiter


@pytest.mark.asyncio
async def test_resolve_parent_cascades_to_direct_children(db_session: AsyncSession):
    """
    Test that marking a parent comment as resolved cascades to direct children.

    This test verifies that when a top-level comment is marked as resolved,
    all its direct replies (children) are also automatically marked as resolved.
    """
    # Create test data: resume, author, and parent comment with two direct replies
    resume = Resume(id=uuid4(), filename="test_resume.pdf", content=b"test content")
    author = Recruiter(id=uuid4(), email="author@example.com", name="Author")

    db_session.add(resume)
    db_session.add(author)
    await db_session.flush()

    # Create parent comment
    parent_comment = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=None,
        content="Parent comment",
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(parent_comment)
    await db_session.flush()

    # Create two direct reply comments
    reply1 = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=parent_comment.id,
        content="First reply",
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
    )
    reply2 = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=parent_comment.id,
        content="Second reply",
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(reply1)
    db_session.add(reply2)
    await db_session.commit()

    # Verify initial state (all unresolved)
    assert parent_comment.is_resolved is False
    assert reply1.is_resolved is False
    assert reply2.is_resolved is False

    # Mark parent as resolved
    parent_comment.is_resolved = True
    await _cascade_resolution_status(db_session, parent_comment.id, True)
    await db_session.commit()

    # Refresh from database
    await db_session.refresh(parent_comment)
    await db_session.refresh(reply1)
    await db_session.refresh(reply2)

    # Verify parent is resolved
    assert parent_comment.is_resolved is True, "Parent comment should be resolved"

    # Verify both direct children are also resolved (cascaded)
    assert reply1.is_resolved is True, "First reply should be resolved (cascaded)"
    assert reply2.is_resolved is True, "Second reply should be resolved (cascaded)"


@pytest.mark.asyncio
async def test_resolve_parent_cascades_to_nested_replies(db_session: AsyncSession):
    """
    Test that resolution cascades to nested replies (multi-level threading).

    This test verifies that resolution status cascades recursively through
    multiple levels of nested replies.
    """
    # Create test data
    resume = Resume(id=uuid4(), filename="test_resume.pdf", content=b"test content")
    author = Recruiter(id=uuid4(), email="author@example.com", name="Author")

    db_session.add(resume)
    db_session.add(author)
    await db_session.flush()

    # Create comment thread with 3 levels:
    # parent (level 0)
    #   ├── child1 (level 1)
    #   │   └── grandchild1 (level 2)
    #   └── child2 (level 1)
    parent = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=None,
        content="Parent comment",
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(parent)
    await db_session.flush()

    child1 = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=parent.id,
        content="Child 1",
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(child1)
    await db_session.flush()

    child2 = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=parent.id,
        content="Child 2",
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(child2)
    await db_session.flush()

    grandchild1 = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=child1.id,
        content="Grandchild 1",
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(grandchild1)
    await db_session.commit()

    # Mark parent as resolved
    parent.is_resolved = True
    await _cascade_resolution_status(db_session, parent.id, True)
    await db_session.commit()

    # Refresh all comments
    await db_session.refresh(parent)
    await db_session.refresh(child1)
    await db_session.refresh(child2)
    await db_session.refresh(grandchild1)

    # Verify all comments in thread are resolved
    assert parent.is_resolved is True, "Parent should be resolved"
    assert child1.is_resolved is True, "Child 1 should be resolved (cascaded)"
    assert child2.is_resolved is True, "Child 2 should be resolved (cascaded)"
    assert grandchild1.is_resolved is True, "Grandchild 1 should be resolved (cascaded)"


@pytest.mark.asyncio
async def test_unresolve_parent_cascades_to_children(db_session: AsyncSession):
    """
    Test that unresolving a parent comment cascades to children.

    This test verifies that when a resolved parent comment is marked as
    unresolved, all its children also become unresolved.
    """
    # Create test data with resolved thread
    resume = Resume(id=uuid4(), filename="test_resume.pdf", content=b"test content")
    author = Recruiter(id=uuid4(), email="author@example.com", name="Author")

    db_session.add(resume)
    db_session.add(author)
    await db_session.flush()

    # Create parent and children, all resolved
    parent = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=None,
        content="Parent comment",
        is_resolved=True,  # Initially resolved
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(parent)
    await db_session.flush()

    child1 = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=parent.id,
        content="Child 1",
        is_resolved=True,  # Initially resolved
        is_deleted=False,
        edits_count=0,
    )
    child2 = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=parent.id,
        content="Child 2",
        is_resolved=True,  # Initially resolved
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(child1)
    db_session.add(child2)
    await db_session.commit()

    # Verify initial state (all resolved)
    await db_session.refresh(parent)
    await db_session.refresh(child1)
    await db_session.refresh(child2)
    assert parent.is_resolved is True
    assert child1.is_resolved is True
    assert child2.is_resolved is True

    # Mark parent as unresolved
    parent.is_resolved = False
    await _cascade_resolution_status(db_session, parent.id, False)
    await db_session.commit()

    # Refresh from database
    await db_session.refresh(parent)
    await db_session.refresh(child1)
    await db_session.refresh(child2)

    # Verify parent is unresolved
    assert parent.is_resolved is False, "Parent should be unresolved"

    # Verify both children are also unresolved (cascaded)
    assert child1.is_resolved is False, "Child 1 should be unresolved (cascaded)"
    assert child2.is_resolved is False, "Child 2 should be unresolved (cascaded)"


@pytest.mark.asyncio
async def test_cascading_affects_only_descendants(db_session: AsyncSession):
    """
    Test that resolution cascading only affects descendants, not unrelated comments.

    This test verifies that when a parent is marked as resolved, only its
    descendants are affected. Comments in other threads remain unchanged.
    """
    # Create test data
    resume = Resume(id=uuid4(), filename="test_resume.pdf", content=b"test content")
    author = Recruiter(id=uuid4(), email="author@example.com", name="Author")

    db_session.add(resume)
    db_session.add(author)
    await db_session.flush()

    # Create two separate comment threads
    # Thread 1: parent1 -> child1
    parent1 = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=None,
        content="Parent 1",
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(parent1)
    await db_session.flush()

    child1 = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=parent1.id,
        content="Child 1",
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(child1)

    # Thread 2: parent2 -> child2 (unrelated thread)
    parent2 = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=None,
        content="Parent 2",
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(parent2)
    await db_session.flush()

    child2 = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=parent2.id,
        content="Child 2",
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(child2)
    await db_session.commit()

    # Mark parent1 as resolved (should only affect thread 1)
    parent1.is_resolved = True
    await _cascade_resolution_status(db_session, parent1.id, True)
    await db_session.commit()

    # Refresh all comments
    await db_session.refresh(parent1)
    await db_session.refresh(child1)
    await db_session.refresh(parent2)
    await db_session.refresh(child2)

    # Verify thread 1 is resolved
    assert parent1.is_resolved is True, "Parent 1 should be resolved"
    assert child1.is_resolved is True, "Child 1 should be resolved (cascaded)"

    # Verify thread 2 is NOT affected
    assert parent2.is_resolved is False, "Parent 2 should NOT be resolved (different thread)"
    assert child2.is_resolved is False, "Child 2 should NOT be resolved (different thread)"


@pytest.mark.asyncio
async def test_resolve_comment_with_no_children(db_session: AsyncSession):
    """
    Test that resolving a comment with no children works correctly.

    This test verifies edge case: resolving a comment that has no replies
    should work correctly (no-op on cascading).
    """
    # Create test data
    resume = Resume(id=uuid4(), filename="test_resume.pdf", content=b"test content")
    author = Recruiter(id=uuid4(), email="author@example.com", name="Author")

    db_session.add(resume)
    db_session.add(author)
    await db_session.flush()

    # Create comment with no children
    comment = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=None,
        content="Standalone comment",
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(comment)
    await db_session.commit()

    # Mark as resolved (should not error even though no children)
    comment.is_resolved = True
    await _cascade_resolution_status(db_session, comment.id, True)
    await db_session.commit()

    # Verify comment is resolved
    await db_session.refresh(comment)
    assert comment.is_resolved is True, "Comment should be resolved"


@pytest.mark.asyncio
async def test_api_endpoint_resolves_parent_and_children(
    db_session: AsyncSession, client
):
    """
    Test that the API endpoint correctly cascades resolution.

    This is an end-to-end test that verifies the PUT /api/team-comments/{id}
    endpoint correctly cascades resolution status to child comments.
    """
    # Create test data
    resume = Resume(id=uuid4(), filename="test_resume.pdf", content=b"test content")
    author = Recruiter(id=uuid4(), email="author@example.com", name="Author")

    db_session.add(resume)
    db_session.add(author)
    await db_session.commit()

    # Create parent and child comments
    parent = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=None,
        content="Parent comment",
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(parent)
    await db_session.flush()

    child = TeamComment(
        id=uuid4(),
        resume_id=resume.id,
        author_id=author.id,
        parent_comment_id=parent.id,
        content="Child reply",
        is_resolved=False,
        is_deleted=False,
        edits_count=0,
    )
    db_session.add(child)
    await db_session.commit()

    # Call API to mark parent as resolved
    response = client.put(
        f"/api/team-comments/{parent.id}",
        json={"is_resolved": True},
    )

    # Verify API response
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["is_resolved"] is True, "Parent should be resolved in response"

    # Verify database state
    await db_session.refresh(parent)
    await db_session.refresh(child)

    assert parent.is_resolved is True, "Parent should be resolved in database"
    assert child.is_resolved is True, "Child should be resolved (cascaded) in database"


# Helper function (duplicate of API implementation for testing)
async def _cascade_resolution_status(
    db: AsyncSession,
    parent_comment_id,
    is_resolved: bool,
) -> None:
    """
    Cascade resolution status to all child comments recursively.
    """
    from models.team_comment import TeamComment
    from uuid import UUID

    # Find all direct children
    children_result = await db.execute(
        select(TeamComment).where(
            TeamComment.parent_comment_id == UUID(parent_comment_id)
        )
    )
    children = children_result.scalars().all()

    for child in children:
        # Update child's resolution status
        child.is_resolved = is_resolved

        # Recursively cascade to nested replies
        await _cascade_resolution_status(db, child.id, is_resolved)
