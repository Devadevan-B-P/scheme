"""
Authentication and Profile management routes for SchemeSetu.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.user import User
from app.models.beneficiary import BeneficiaryProfile
from app.core.security import hash_password, verify_password

router = APIRouter(tags=["Authentication"])


# ── Request / Response schemas ────────────────────────────────────────────────


class SignupRequest(BaseModel):
    full_name: str
    email: str
    password: str
    phone_number: str | None = None
    category: str = "SC"
    state: str = "Kerala"
    district: str = "Thiruvananthapuram"
    role: str = "beneficiary"  # "beneficiary" | "admin"


class LoginRequest(BaseModel):
    email: str
    password: str


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    phone_number: str | None = None
    category: str | None = None
    state: str | None = None
    district: str | None = None
    pin_code: str | None = None
    age: int | None = None
    gender: str | None = None
    annual_income: float | None = None
    occupation: str | None = None
    business_type: str | None = None
    project_cost: float | None = None
    loan_required: float | None = None


# ── Auth Endpoints ─────────────────────────────────────────────────────────────


@router.post("/auth/signup")
async def signup(request: SignupRequest) -> dict:
    """
    Register a new beneficiary or admin user. Stores details in MongoDB.
    """
    email_clean = request.email.lower().strip()
    existing_user = await User.find_one(User.email == email_clean)
    if existing_user:
        raise HTTPException(status_code=400, detail="User email already registered")

    user_role = request.role if request.role in ("admin", "beneficiary") else "beneficiary"

    user = User(
        user_id=uuid4(),
        email=email_clean,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        phone_number=request.phone_number,
        category=request.category,
        state=request.state,
        district=request.district,
        role=user_role,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await user.insert()

    # Ensure corresponding BeneficiaryProfile document exists in MongoDB
    profile = await BeneficiaryProfile.find_one(BeneficiaryProfile.beneficiary_id == user.user_id)
    if not profile:
        profile = BeneficiaryProfile(
            beneficiary_id=user.user_id,
            category=user.category.lower(),
            location={"state": user.state, "district": user.district},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await profile.insert()

    loc = profile.location or {}

    return {
        "message": "Registration successful",
        "user": {
            "user_id": str(user.user_id),
            "email": user.email,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "category": user.category,
            "state": user.state,
            "district": user.district,
            "pin_code": loc.get("pincode", ""),
            "role": user.role,
            "age": profile.age,
            "gender": profile.gender,
            "annual_income": profile.annual_income,
            "business_type": profile.business_type,
            "project_cost": profile.project_cost,
            "loan_required": profile.loan_required,
        }
    }


@router.post("/auth/login")
async def login(request: LoginRequest) -> dict:
    """
    Authenticate beneficiary or admin user from MongoDB.
    """
    email_clean = request.email.lower().strip()
    user = await User.find_one(User.email == email_clean)
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email address or password")

    user_role = user.role if user.role in ("admin", "beneficiary") else "beneficiary"

    profile = await BeneficiaryProfile.find_one(BeneficiaryProfile.beneficiary_id == user.user_id)
    if not profile:
        profile = BeneficiaryProfile(
            beneficiary_id=user.user_id,
            category=user.category.lower() if user.category else "sc",
            location={"state": user.state, "district": user.district},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await profile.insert()

    loc = profile.location or {}

    return {
        "message": "Login successful",
        "user": {
            "user_id": str(user.user_id),
            "email": user.email,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "category": user.category,
            "state": user.state,
            "district": user.district,
            "pin_code": loc.get("pincode", ""),
            "role": user_role,
            "age": profile.age,
            "gender": profile.gender,
            "annual_income": profile.annual_income,
            "business_type": profile.business_type,
            "project_cost": profile.project_cost,
            "loan_required": profile.loan_required,
        }
    }


@router.get("/auth/profile/{user_id}")
async def get_profile(user_id: str) -> dict:
    """
    Get combined User and BeneficiaryProfile from MongoDB.
    """
    try:
        u_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user = await User.find_one(User.user_id == u_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = await BeneficiaryProfile.find_one(BeneficiaryProfile.beneficiary_id == u_uuid)
    if not profile:
        profile = BeneficiaryProfile(beneficiary_id=u_uuid)
        await profile.insert()

    loc = profile.location or {}

    return {
        "user_id": str(user.user_id),
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "category": user.category,
        "state": user.state or loc.get("state", ""),
        "district": user.district or loc.get("district", ""),
        "pin_code": loc.get("pincode", ""),
        "role": user.role,
        "age": profile.age,
        "gender": profile.gender,
        "annual_income": profile.annual_income,
        "occupation": getattr(profile, "occupation", None),
        "business_type": profile.business_type,
        "project_cost": profile.project_cost,
        "loan_required": profile.loan_required,
        "profile_completeness_pct": profile.profile_completeness_pct,
    }


@router.put("/auth/profile/{user_id}")
async def update_profile(user_id: str, request: ProfileUpdateRequest) -> dict:
    """
    Update User and BeneficiaryProfile in MongoDB.
    """
    try:
        u_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user = await User.find_one(User.user_id == u_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = await BeneficiaryProfile.find_one(BeneficiaryProfile.beneficiary_id == u_uuid)
    if not profile:
        profile = BeneficiaryProfile(beneficiary_id=u_uuid)
        await profile.insert()

    # Update User document
    if request.full_name is not None:
        user.full_name = request.full_name
    if request.phone_number is not None:
        user.phone_number = request.phone_number
    if request.category is not None:
        user.category = request.category
    if request.state is not None:
        user.state = request.state
    if request.district is not None:
        user.district = request.district
    user.updated_at = datetime.now(timezone.utc)
    await user.save()

    # Update BeneficiaryProfile document
    if request.category is not None:
        profile.category = request.category.lower()
    if request.age is not None:
        profile.age = request.age
    if request.gender is not None:
        profile.gender = request.gender.lower()
    if request.annual_income is not None:
        profile.annual_income = request.annual_income
    if request.business_type is not None:
        profile.business_type = request.business_type
    if request.project_cost is not None:
        profile.project_cost = request.project_cost
    if request.loan_required is not None:
        profile.loan_required = request.loan_required

    loc = profile.location or {}
    if request.state is not None:
        loc["state"] = request.state
    if request.district is not None:
        loc["district"] = request.district
    if request.pin_code is not None:
        loc["pincode"] = request.pin_code
    profile.location = loc
    profile.updated_at = datetime.now(timezone.utc)

    # Track completeness
    tracked = [
        "channel", "language", "category", "gender", "age",
        "location", "annual_income", "education_level",
        "business_type", "project_cost", "loan_required",
    ]
    filled = sum(1 for f in tracked if getattr(profile, f) is not None)
    profile.profile_completeness_pct = round((filled / len(tracked)) * 100)

    await profile.save()

    return {
        "message": "Profile updated successfully",
        "user": {
            "user_id": str(user.user_id),
            "email": user.email,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "category": user.category,
            "state": user.state,
            "district": user.district,
            "pin_code": loc.get("pincode", ""),
            "role": user.role,
            "age": profile.age,
            "gender": profile.gender,
            "annual_income": profile.annual_income,
            "occupation": getattr(profile, "occupation", None),
            "business_type": profile.business_type,
            "project_cost": profile.project_cost,
            "loan_required": profile.loan_required,
            "profile_completeness_pct": profile.profile_completeness_pct,
        }
    }
