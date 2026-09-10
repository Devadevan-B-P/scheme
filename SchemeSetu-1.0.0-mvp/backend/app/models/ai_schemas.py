"""
Pydantic schema for partial LLM-based extraction of beneficiary profile fields.

Every field mirrors BeneficiaryProfile but is Optional[...] with a None default
so the LLM only populates what it actually finds in the user's message.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PartialProfileExtraction(BaseModel):
    """
    Partial snapshot of a beneficiary profile extracted from a single user message.

    All fields are optional — the LLM must leave a field ``null`` when the
    corresponding information was not mentioned.  No inferring, no guessing.
    """

    beneficiary_id: Optional[UUID] = Field(
        default=None,
        description="UUID of the beneficiary if already known; otherwise leave null.",
    )
    channel: Optional[str] = Field(
        default=None,
        description=(
            "Communication channel the user is on. "
            "One of: 'whatsapp', 'web', 'ivr', 'sms'."
        ),
    )
    language: Optional[str] = Field(
        default=None,
        description="ISO 639-1 language code inferred from the message (e.g. 'en', 'hi', 'mr').",
    )
    category: Optional[str] = Field(
        default=None,
        description=(
            "Social category of the beneficiary. "
            "One of: 'sc' (Scheduled Caste), 'st' (Scheduled Tribe), "
            "'obc' (Other Backward Class), 'general', 'ews' (Economically Weaker Section)."
        ),
    )
    gender: Optional[str] = Field(
        default=None,
        description="Gender of the beneficiary. One of: 'male', 'female', 'other'.",
    )
    age: Optional[int] = Field(
        default=None,
        description="Age of the beneficiary in whole years.",
    )
    location: Optional[dict] = Field(
        default=None,
        description=(
            "Geographical location as a dict with keys: "
            "'state' (str), 'district' (str), 'pincode' (str). "
            "Include only the keys that are mentioned."
        ),
    )
    annual_income: Optional[float] = Field(
        default=None,
        description=(
            "Annual household income in Indian Rupees (₹). "
            "Convert lakhs/crores to absolute rupee values if stated "
            "(e.g. '2 lakh' → 200000.0)."
        ),
    )
    education_level: Optional[str] = Field(
        default=None,
        description=(
            "Highest education level attained. "
            "One of: 'illiterate', 'primary', 'secondary', 'higher_secondary', "
            "'graduate', 'post_graduate'."
        ),
    )
    disability_status: Optional[bool] = Field(
        default=None,
        description="True if the beneficiary has a disability, False if explicitly stated they do not.",
    )
    business_type: Optional[str] = Field(
        default=None,
        description=(
            "Type of business the beneficiary intends to start or expand. "
            "One of: 'manufacturing', 'service', 'trading', 'agro_processing', 'other'."
        ),
    )
    project_cost: Optional[float] = Field(
        default=None,
        description=(
            "Total estimated project cost in Indian Rupees (₹). "
            "Convert lakhs/crores to absolute values (e.g. '5 lakh' → 500000.0)."
        ),
    )
    loan_required: Optional[float] = Field(
        default=None,
        description=(
            "Loan amount the beneficiary is seeking in Indian Rupees (₹). "
            "Convert lakhs/crores to absolute values."
        ),
    )
