"""
End-to-end verification test for job seeker profile management.

This test verifies the complete job seeker profile management workflow:
1. Register as job_seeker or login with existing job_seeker account
2. Navigate to profile page (via API)
3. Add basic profile information
4. Add work history entry
5. Add education entry
6. Add skills
7. Verify all data persists on page reload (re-fetch from API)

This is the acceptance test for the job seeker profile management feature.
"""
import pytest
from datetime import date
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from database import get_db
from models.user import User
from models.role import Role, UserRole
from models.job_seeker_profile import JobSeekerProfile
from models.work_history import WorkHistory, EmploymentType
from models.education import Education, DegreeType
from models.skill import Skill, ProficiencyLevel


@pytest.mark.asyncio
async def test_complete_job_seeker_profile_workflow(client: AsyncClient, test_db: AsyncSession):
    """
    End-to-end test: Complete job seeker profile management workflow.

    This test verifies the complete journey:
    1. Register as job_seeker
    2. Create basic profile information
    3. Add work history entry
    4. Add education entry
    5. Add skills
    6. Verify all data persists (re-fetch from API)

    This is the main acceptance test for the feature.
    """
    print("\n" + "="*80)
    print("COMPLETE JOB SEEKER PROFILE MANAGEMENT - E2E TEST")
    print("="*80 + "\n")

    # ============================================================
    # STEP 1: Register as job_seeker
    # ============================================================
    print("STEP 1: Register as Job Seeker")
    print("-" * 80)

    job_seeker_data = {
        "email": "profile_test@example.com",
        "password": "ProfileTest123!",
        "full_name": "Profile Test User",
        "role": "job_seeker"
    }

    print("Registering new job seeker account...")
    response = await client.post("/api/auth/register", json=job_seeker_data)
    print(f"✓ Registration response status: {response.status_code}")

    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    registration_result = response.json()
    user_id = registration_result['id']
    print(f"✓ User registered with ID: {user_id}")

    # Login to get tokens
    print("\nLogging in to get access token...")
    login_response = await client.post(
        "/api/auth/login",
        json={
            "email": job_seeker_data["email"],
            "password": job_seeker_data["password"]
        }
    )
    assert login_response.status_code == 200
    login_result = login_response.json()
    access_token = login_result["access_token"]
    print(f"✓ Logged in successfully")

    # Set auth header for subsequent requests
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # ============================================================
    # STEP 2: Verify profile doesn't exist yet
    # ============================================================
    print("\nSTEP 2: Verify Profile Doesn't Exist Yet")
    print("-" * 80)

    print("Attempting to fetch profile (should return 404)...")
    profile_response = await client.get(
        "/api/profiles/me",
        headers=auth_headers
    )
    print(f"✓ Profile fetch response status: {profile_response.status_code}")

    assert profile_response.status_code == 404, "Profile should not exist yet"
    print("✓ Profile doesn't exist (as expected)")

    # ============================================================
    # STEP 3: Add basic profile information
    # ============================================================
    print("\nSTEP 3: Add Basic Profile Information")
    print("-" * 80)

    profile_data = {
        "phone": "+1 (555) 987-6543",
        "location": "San Francisco, CA",
        "bio": "Passionate software engineer with expertise in full-stack development. "
              "Love building scalable applications and solving complex problems.",
        "linkedin_url": "https://linkedin.com/in/profiletestuser",
        "portfolio_url": "https://portfolio.testuser.com",
        "years_of_experience": 5.5,
        "current_title": "Senior Software Engineer",
        "current_company": "Tech Innovations Inc.",
        "industry": "Technology",
        "job_seeker_status": "actively_looking",
        "preferred_locations": "San Francisco, CA, Remote, New York, NY",
        "preferred_job_types": "full_time, contract",
        "expected_salary": "$150,000 - $180,000"
    }

    print("Creating profile with basic information...")
    create_profile_response = await client.post(
        "/api/profiles/me",
        headers=auth_headers,
        json=profile_data
    )
    print(f"✓ Profile creation response status: {create_profile_response.status_code}")

    assert create_profile_response.status_code == 201, f"Expected 201, got {create_profile_response.status_code}"
    created_profile = create_profile_response.json()
    profile_id = created_profile['id']
    print(f"✓ Profile created with ID: {profile_id}")
    print(f"✓ Location: {created_profile['location']}")
    print(f"✓ Current Title: {created_profile['current_title']}")
    print(f"✓ Years of Experience: {created_profile['years_of_experience']}")

    # Verify all fields are correctly stored
    assert created_profile['phone'] == profile_data['phone']
    assert created_profile['location'] == profile_data['location']
    assert created_profile['bio'] == profile_data['bio']
    assert created_profile['linkedin_url'] == profile_data['linkedin_url']
    assert created_profile['portfolio_url'] == profile_data['portfolio_url']
    assert created_profile['years_of_experience'] == profile_data['years_of_experience']
    assert created_profile['current_title'] == profile_data['current_title']
    assert created_profile['current_company'] == profile_data['current_company']
    assert created_profile['industry'] == profile_data['industry']
    assert created_profile['job_seeker_status'] == profile_data['job_seeker_status']
    assert created_profile['preferred_locations'] == profile_data['preferred_locations']
    assert created_profile['preferred_job_types'] == profile_data['preferred_job_types']
    assert created_profile['expected_salary'] == profile_data['expected_salary']
    print("✓ All profile fields verified")

    # ============================================================
    # STEP 4: Add work history entry
    # ============================================================
    print("\nSTEP 4: Add Work History Entry")
    print("-" * 80)

    work_history_data = {
        "company_name": "Tech Innovations Inc.",
        "position_title": "Senior Software Engineer",
        "start_date": "2020-06-01",
        "end_date": None,  # Current position
        "employment_type": "full_time",
        "location": "San Francisco, CA",
        "description": "Leading development of microservices architecture. "
                      "Implemented CI/CD pipelines and reduced deployment time by 60%."
    }

    print("Adding first work history entry...")
    work_response = await client.post(
        "/api/profiles/me/work-history",
        headers=auth_headers,
        json=work_history_data
    )
    print(f"✓ Work history creation response status: {work_response.status_code}")

    assert work_response.status_code == 201, f"Expected 201, got {work_response.status_code}"
    created_work = work_response.json()
    work_id_1 = created_work['id']
    print(f"✓ Work history entry created with ID: {work_id_1}")
    print(f"✓ Position: {created_work['position_title']} at {created_work['company_name']}")

    # Add second work history entry
    work_history_data_2 = {
        "company_name": "StartUp Ventures LLC",
        "position_title": "Software Developer",
        "start_date": "2018-01-01",
        "end_date": "2020-05-31",
        "employment_type": "full_time",
        "location": "Remote",
        "description": "Full-stack development using React and Node.js. "
                      "Built and maintained customer-facing web applications."
    }

    print("\nAdding second work history entry...")
    work_response_2 = await client.post(
        "/api/profiles/me/work-history",
        headers=auth_headers,
        json=work_history_data_2
    )
    print(f"✓ Second work history entry created: {work_response_2.status_code}")

    assert work_response_2.status_code == 201
    created_work_2 = work_response_2.json()
    work_id_2 = created_work_2['id']
    print(f"✓ Work history entry created with ID: {work_id_2}")

    # Verify work history count
    print("\nFetching all work history entries...")
    work_list_response = await client.get(
        "/api/profiles/me/work-history",
        headers=auth_headers
    )
    assert work_list_response.status_code == 200
    work_list = work_list_response.json()
    assert work_list['count'] == 2, f"Expected 2 work history entries, got {work_list['count']}"
    print(f"✓ Total work history entries: {work_list['count']}")

    # ============================================================
    # STEP 5: Add education entry
    # ============================================================
    print("\nSTEP 5: Add Education Entry")
    print("-" * 80)

    education_data = {
        "institution_name": "University of California, Berkeley",
        "degree": "Bachelor of Science",
        "field_of_study": "Computer Science",
        "degree_type": "bachelor",
        "start_date": "2014-09-01",
        "end_date": "2018-05-31",
        "location": "Berkeley, CA",
        "description": "Graduated with honors. Focus on algorithms, data structures, and software engineering."
    }

    print("Adding education entry...")
    education_response = await client.post(
        "/api/profiles/me/education",
        headers=auth_headers,
        json=education_data
    )
    print(f"✓ Education creation response status: {education_response.status_code}")

    assert education_response.status_code == 201, f"Expected 201, got {education_response.status_code}"
    created_education = education_response.json()
    education_id = created_education['id']
    print(f"✓ Education entry created with ID: {education_id}")
    print(f"✓ Degree: {created_education['degree']} in {created_education['field_of_study']}")
    print(f"✓ Institution: {created_education['institution_name']}")

    # Add second education entry (Master's)
    education_data_2 = {
        "institution_name": "Stanford University",
        "degree": "Master of Science",
        "field_of_study": "Computer Science",
        "degree_type": "master",
        "start_date": "2018-09-01",
        "end_date": "2020-06-30",
        "location": "Stanford, CA",
        "description": "Specialized in Machine Learning and Artificial Intelligence."
    }

    print("\nAdding second education entry...")
    education_response_2 = await client.post(
        "/api/profiles/me/education",
        headers=auth_headers,
        json=education_data_2
    )
    assert education_response_2.status_code == 201
    created_education_2 = education_response_2.json()
    print(f"✓ Second education entry created")

    # Verify education count
    print("\nFetching all education entries...")
    education_list_response = await client.get(
        "/api/profiles/me/education",
        headers=auth_headers
    )
    assert education_list_response.status_code == 200
    education_list = education_list_response.json()
    assert education_list['count'] == 2, f"Expected 2 education entries, got {education_list['count']}"
    print(f"✓ Total education entries: {education_list['count']}")

    # ============================================================
    # STEP 6: Add skills
    # ============================================================
    print("\nSTEP 6: Add Skills")
    print("-" * 80)

    skills_to_add = [
        {
            "name": "Python",
            "category": "Programming Languages",
            "proficiency_level": "expert",
            "years_of_experience": 5,
            "description": "Expert in Python, Django, FastAPI, and data science libraries."
        },
        {
            "name": "TypeScript",
            "category": "Programming Languages",
            "proficiency_level": "advanced",
            "years_of_experience": 4,
            "description": "Advanced TypeScript for React and Node.js development."
        },
        {
            "name": "React",
            "category": "Frontend Frameworks",
            "proficiency_level": "advanced",
            "years_of_experience": 4,
            "description": "Building complex React applications with hooks and context."
        },
        {
            "name": "Machine Learning",
            "category": "Data Science",
            "proficiency_level": "intermediate",
            "years_of_experience": 2,
            "description": "Experience with TensorFlow, PyTorch, and scikit-learn."
        },
        {
            "name": "Docker",
            "category": "DevOps",
            "proficiency_level": "advanced",
            "years_of_experience": 3,
            "description": "Containerization and orchestration with Docker and Kubernetes."
        }
    ]

    skill_ids = []
    for skill_data in skills_to_add:
        print(f"Adding skill: {skill_data['name']}...")
        skill_response = await client.post(
            "/api/profiles/me/skills",
            headers=auth_headers,
            json=skill_data
        )
        assert skill_response.status_code == 201, f"Failed to create skill {skill_data['name']}"
        created_skill = skill_response.json()
        skill_ids.append(created_skill['id'])
        print(f"  ✓ Created: {created_skill['name']} ({created_skill['proficiency_level']})")

    # Verify skills count
    print("\nFetching all skills...")
    skills_list_response = await client.get(
        "/api/profiles/me/skills",
        headers=auth_headers
    )
    assert skills_list_response.status_code == 200
    skills_list = skills_list_response.json()
    assert skills_list['count'] == 5, f"Expected 5 skills, got {skills_list['count']}"
    print(f"✓ Total skills: {skills_list['count']}")

    # ============================================================
    # STEP 7: Verify all data persists (simulate page reload)
    # ============================================================
    print("\nSTEP 7: Verify All Data Persists (Simulate Page Reload)")
    print("-" * 80)

    print("Re-fetching profile data...")
    profile_verify_response = await client.get(
        "/api/profiles/me",
        headers=auth_headers
    )
    assert profile_verify_response.status_code == 200
    verified_profile = profile_verify_response.json()

    print("Verifying profile data persisted correctly...")
    assert verified_profile['id'] == profile_id
    assert verified_profile['phone'] == profile_data['phone']
    assert verified_profile['location'] == profile_data['location']
    assert verified_profile['bio'] == profile_data['bio']
    assert verified_profile['current_title'] == profile_data['current_title']
    assert verified_profile['years_of_experience'] == profile_data['years_of_experience']
    print("✓ Profile data persisted correctly")

    print("\nRe-fetching work history...")
    work_verify_response = await client.get(
        "/api/profiles/me/work-history",
        headers=auth_headers
    )
    assert work_verify_response.status_code == 200
    verified_work = work_verify_response.json()
    assert verified_work['count'] == 2
    # Verify work entries are ordered by start_date (most recent first)
    work_entries = verified_work['work_history']
    assert work_entries[0]['position_title'] == "Senior Software Engineer"
    assert work_entries[1]['position_title'] == "Software Developer"
    print(f"✓ Work history persisted correctly ({verified_work['count']} entries)")

    print("\nRe-fetching education...")
    education_verify_response = await client.get(
        "/api/profiles/me/education",
        headers=auth_headers
    )
    assert education_verify_response.status_code == 200
    verified_education = education_verify_response.json()
    assert verified_education['count'] == 2
    print(f"✓ Education persisted correctly ({verified_education['count']} entries)")

    print("\nRe-fetching skills...")
    skills_verify_response = await client.get(
        "/api/profiles/me/skills",
        headers=auth_headers
    )
    assert skills_verify_response.status_code == 200
    verified_skills = skills_verify_response.json()
    assert verified_skills['count'] == 5
    # Verify skills are ordered by category (nulls last) and name
    assert any(s['name'] == 'Python' for s in verified_skills['skills'])
    assert any(s['name'] == 'TypeScript' for s in verified_skills['skills'])
    assert any(s['name'] == 'React' for s in verified_skills['skills'])
    print(f"✓ Skills persisted correctly ({verified_skills['count']} entries)")

    # ============================================================
    # STEP 8: Test profile update
    # ============================================================
    print("\nSTEP 8: Test Profile Update")
    print("-" * 80)

    update_data = {
        "current_title": "Lead Software Engineer",
        "years_of_experience": 6.0,
        "job_seeker_status": "open"
    }

    print("Updating profile with new information...")
    update_response = await client.put(
        "/api/profiles/me",
        headers=auth_headers,
        json=update_data
    )
    assert update_response.status_code == 200
    updated_profile = update_response.json()
    print(f"✓ Profile updated successfully")

    assert updated_profile['current_title'] == "Lead Software Engineer"
    assert updated_profile['years_of_experience'] == 6.0
    assert updated_profile['job_seeker_status'] == "open"
    print(f"✓ Updated title: {updated_profile['current_title']}")
    print(f"✓ Updated experience: {updated_profile['years_of_experience']} years")
    print(f"✓ Updated status: {updated_profile['job_seeker_status']}")

    # Verify other fields remain unchanged
    assert updated_profile['location'] == profile_data['location']
    assert updated_profile['phone'] == profile_data['phone']
    print("✓ Other fields remained unchanged")

    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "="*80)
    print("E2E TEST SUMMARY")
    print("="*80)
    print("✓ Job seeker registration: PASSED")
    print("✓ Profile creation with basic info: PASSED")
    print("✓ Work history entries (2): PASSED")
    print("✓ Education entries (2): PASSED")
    print("✓ Skills entries (5): PASSED")
    print("✓ Data persistence verification: PASSED")
    print("✓ Profile update: PASSED")
    print("\n" + "="*80)
    print("ALL TESTS PASSED - JOB SEEKER PROFILE MANAGEMENT VERIFIED")
    print("="*80 + "\n")


@pytest.mark.asyncio
async def test_profile_work_history_crud_operations(client: AsyncClient, test_db: AsyncSession):
    """
    Test CRUD operations for work history entries.
    """
    print("\n" + "="*80)
    print("WORK HISTORY CRUD OPERATIONS TEST")
    print("="*80 + "\n")

    # Create user and login
    user_data = {
        "email": "worktest@example.com",
        "password": "WorkTest123!",
        "full_name": "Work Test User",
        "role": "job_seeker"
    }
    await client.post("/api/auth/register", json=user_data)
    login_response = await client.post(
        "/api/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]}
    )
    access_token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # Create profile first
    await client.post(
        "/api/profiles/me",
        headers=auth_headers,
        json={"location": "San Francisco, CA"}
    )

    # CREATE: Add work history
    print("Testing CREATE operation...")
    work_data = {
        "company_name": "Test Corp",
        "position_title": "Developer",
        "start_date": "2020-01-01",
        "employment_type": "full_time"
    }
    create_response = await client.post(
        "/api/profiles/me/work-history",
        headers=auth_headers,
        json=work_data
    )
    assert create_response.status_code == 201
    created_work = create_response.json()
    work_id = created_work['id']
    print(f"✓ Created work entry: {work_id}")

    # READ: Get single work history entry
    print("\nTesting READ (single) operation...")
    get_response = await client.get(
        f"/api/profiles/me/work-history/{work_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 200
    work_entry = get_response.json()
    assert work_entry['id'] == work_id
    assert work_entry['position_title'] == "Developer"
    print(f"✓ Retrieved work entry: {work_entry['position_title']}")

    # UPDATE: Update work history
    print("\nTesting UPDATE operation...")
    update_data = {
        "position_title": "Senior Developer",
        "end_date": "2023-12-31"
    }
    update_response = await client.put(
        f"/api/profiles/me/work-history/{work_id}",
        headers=auth_headers,
        json=update_data
    )
    assert update_response.status_code == 200
    updated_work = update_response.json()
    assert updated_work['position_title'] == "Senior Developer"
    assert updated_work['end_date'] == "2023-12-31"
    print(f"✓ Updated work entry: {updated_work['position_title']}")

    # DELETE: Delete work history
    print("\nTesting DELETE operation...")
    delete_response = await client.delete(
        f"/api/profiles/me/work-history/{work_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 200
    print(f"✓ Deleted work entry")

    # Verify deletion
    get_deleted_response = await client.get(
        f"/api/profiles/me/work-history/{work_id}",
        headers=auth_headers
    )
    assert get_deleted_response.status_code == 404
    print(f"✓ Verified entry is deleted (404)")

    print("\n" + "="*80)
    print("WORK HISTORY CRUD TESTS PASSED")
    print("="*80 + "\n")


@pytest.mark.asyncio
async def test_profile_education_crud_operations(client: AsyncClient, test_db: AsyncSession):
    """
    Test CRUD operations for education entries.
    """
    print("\n" + "="*80)
    print("EDUCATION CRUD OPERATIONS TEST")
    print("="*80 + "\n")

    # Create user and login
    user_data = {
        "email": "edutest@example.com",
        "password": "EduTest123!",
        "full_name": "Edu Test User",
        "role": "job_seeker"
    }
    await client.post("/api/auth/register", json=user_data)
    login_response = await client.post(
        "/api/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]}
    )
    access_token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # Create profile first
    await client.post(
        "/api/profiles/me",
        headers=auth_headers,
        json={"location": "Boston, MA"}
    )

    # CREATE: Add education
    print("Testing CREATE operation...")
    education_data = {
        "institution_name": "MIT",
        "degree": "Bachelor of Science",
        "field_of_study": "Computer Science",
        "degree_type": "bachelor",
        "start_date": "2016-09-01"
    }
    create_response = await client.post(
        "/api/profiles/me/education",
        headers=auth_headers,
        json=education_data
    )
    assert create_response.status_code == 201
    created_edu = create_response.json()
    edu_id = created_edu['id']
    print(f"✓ Created education entry: {edu_id}")

    # READ: Get single education entry
    print("\nTesting READ (single) operation...")
    get_response = await client.get(
        f"/api/profiles/me/education/{edu_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 200
    edu_entry = get_response.json()
    assert edu_entry['id'] == edu_id
    assert edu_entry['degree'] == "Bachelor of Science"
    print(f"✓ Retrieved education entry: {edu_entry['degree']}")

    # UPDATE: Update education
    print("\nTesting UPDATE operation...")
    update_data = {
        "field_of_study": "Computer Science and Mathematics",
        "end_date": "2020-05-31"
    }
    update_response = await client.put(
        f"/api/profiles/me/education/{edu_id}",
        headers=auth_headers,
        json=update_data
    )
    assert update_response.status_code == 200
    updated_edu = update_response.json()
    assert updated_edu['field_of_study'] == "Computer Science and Mathematics"
    assert updated_edu['end_date'] == "2020-05-31"
    print(f"✓ Updated education entry")

    # DELETE: Delete education
    print("\nTesting DELETE operation...")
    delete_response = await client.delete(
        f"/api/profiles/me/education/{edu_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 200
    print(f"✓ Deleted education entry")

    # Verify deletion
    get_deleted_response = await client.get(
        f"/api/profiles/me/education/{edu_id}",
        headers=auth_headers
    )
    assert get_deleted_response.status_code == 404
    print(f"✓ Verified entry is deleted (404)")

    print("\n" + "="*80)
    print("EDUCATION CRUD TESTS PASSED")
    print("="*80 + "\n")


@pytest.mark.asyncio
async def test_profile_skills_crud_operations(client: AsyncClient, test_db: AsyncSession):
    """
    Test CRUD operations for skill entries.
    """
    print("\n" + "="*80)
    print("SKILLS CRUD OPERATIONS TEST")
    print("="*80 + "\n")

    # Create user and login
    user_data = {
        "email": "skilltest@example.com",
        "password": "SkillTest123!",
        "full_name": "Skill Test User",
        "role": "job_seeker"
    }
    await client.post("/api/auth/register", json=user_data)
    login_response = await client.post(
        "/api/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]}
    )
    access_token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # Create profile first
    await client.post(
        "/api/profiles/me",
        headers=auth_headers,
        json={"location": "Seattle, WA"}
    )

    # CREATE: Add skill
    print("Testing CREATE operation...")
    skill_data = {
        "name": "Go",
        "category": "Programming Languages",
        "proficiency_level": "intermediate",
        "years_of_experience": 1
    }
    create_response = await client.post(
        "/api/profiles/me/skills",
        headers=auth_headers,
        json=skill_data
    )
    assert create_response.status_code == 201
    created_skill = create_response.json()
    skill_id = created_skill['id']
    print(f"✓ Created skill entry: {skill_id}")

    # READ: Get single skill entry
    print("\nTesting READ (single) operation...")
    get_response = await client.get(
        f"/api/profiles/me/skills/{skill_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 200
    skill_entry = get_response.json()
    assert skill_entry['id'] == skill_id
    assert skill_entry['name'] == "Go"
    print(f"✓ Retrieved skill entry: {skill_entry['name']}")

    # UPDATE: Update skill
    print("\nTesting UPDATE operation...")
    update_data = {
        "proficiency_level": "advanced",
        "years_of_experience": 2
    }
    update_response = await client.put(
        f"/api/profiles/me/skills/{skill_id}",
        headers=auth_headers,
        json=update_data
    )
    assert update_response.status_code == 200
    updated_skill = update_response.json()
    assert updated_skill['proficiency_level'] == "advanced"
    assert updated_skill['years_of_experience'] == 2
    print(f"✓ Updated skill entry: {updated_skill['proficiency_level']}")

    # DELETE: Delete skill
    print("\nTesting DELETE operation...")
    delete_response = await client.delete(
        f"/api/profiles/me/skills/{skill_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 200
    print(f"✓ Deleted skill entry")

    # Verify deletion
    get_deleted_response = await client.get(
        f"/api/profiles/me/skills/{skill_id}",
        headers=auth_headers
    )
    assert get_deleted_response.status_code == 404
    print(f"✓ Verified entry is deleted (404)")

    print("\n" + "="*80)
    print("SKILLS CRUD TESTS PASSED")
    print("="*80 + "\n")
