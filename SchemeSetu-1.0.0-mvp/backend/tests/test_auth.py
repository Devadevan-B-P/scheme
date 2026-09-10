"""
Unit & Integration Tests for Auth, User Profile & Schemes MongoDB endpoints.
"""

import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db
from app.models.user import User
from app.models.beneficiary import BeneficiaryProfile


@pytest_asyncio.fixture(autouse=True)
async def initialize_database():
    """Ensure database connection and Beanie models are initialized."""
    from app.core.database import close_mongo_connection
    await init_db()
    yield
    await close_mongo_connection()


@pytest.mark.asyncio
async def test_signup_and_login_flow():
    """Test full registration and login flow storing details in MongoDB."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.gov.in"
        password = "SecurePassword123!"

        # 1. Signup
        signup_res = await client.post("/api/v1/auth/signup", json={
            "full_name": "Test Beneficiary",
            "email": unique_email,
            "password": password,
            "phone_number": "9876543210",
            "category": "SC",
            "state": "Kerala",
            "district": "Thiruvananthapuram",
        })

        assert signup_res.status_code == 200, signup_res.text
        data = signup_res.json()
        assert data["message"] == "Registration successful"
        user_info = data["user"]
        assert user_info["email"] == unique_email
        assert user_info["full_name"] == "Test Beneficiary"
        user_id = user_info["user_id"]

        # Verify record exists in MongoDB users & beneficiary_profiles collection
        u_uuid = uuid.UUID(user_id)
        user_in_db = await User.find_one(User.user_id == u_uuid)
        assert user_in_db is not None
        assert user_in_db.email == unique_email

        profile_in_db = await BeneficiaryProfile.find_one(BeneficiaryProfile.beneficiary_id == u_uuid)
        assert profile_in_db is not None

        # 2. Login
        login_res = await client.post("/api/v1/auth/login", json={
            "email": unique_email,
            "password": password,
        })

        assert login_res.status_code == 200, login_res.text
        login_data = login_res.json()
        assert login_data["message"] == "Login successful"
        assert login_data["user"]["user_id"] == user_id


@pytest.mark.asyncio
async def test_profile_update_and_schemes_list():
    """Test updating user profile in MongoDB and retrieving schemes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        # Signup
        signup_res = await client.post("/api/v1/auth/signup", json={
            "full_name": "Initial Name",
            "email": unique_email,
            "password": "Password123",
            "category": "SC",
            "state": "Kerala",
            "district": "Ernakulam",
        })
        user_id = signup_res.json()["user"]["user_id"]

        # Update profile
        update_res = await client.put(f"/api/v1/auth/profile/{user_id}", json={
            "full_name": "Updated Beneficiary Name",
            "annual_income": 250000.0,
            "age": 30,
            "gender": "Male",
            "business_type": "Manufacturing",
            "project_cost": 400000.0,
            "loan_required": 350000.0,
        })

        assert update_res.status_code == 200
        updated_data = update_res.json()["user"]
        assert updated_data["full_name"] == "Updated Beneficiary Name"
        assert updated_data["annual_income"] == 250000.0
        assert updated_data["age"] == 30

        # Fetch profile
        get_res = await client.get(f"/api/v1/auth/profile/{user_id}")
        assert get_res.status_code == 200
        assert get_res.json()["full_name"] == "Updated Beneficiary Name"

        # Fetch schemes list
        schemes_res = await client.get("/api/v1/schemes")
        assert schemes_res.status_code == 200
        schemes = schemes_res.json()
        assert len(schemes) >= 1
