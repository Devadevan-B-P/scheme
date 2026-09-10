"""
Prompts and Schemas for Gemini Conversational Agent.

Enforces:
  1. AI understands and extracts; deterministic engine decides.
  2. Model outputs strictly valid JSON conforming to ExtractedEntities.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ExtractedEntities(BaseModel):
    """Structured variables extracted from user message."""
    age: Optional[int] = Field(None, description="Age in years (e.g. 28)")
    annual_income: Optional[float] = Field(
        None, description="Annual family income in Indian Rupees (e.g. 250000.0)"
    )
    category: Optional[str] = Field(
        None, description="Social category: SC, ST, OBC, General, etc."
    )
    gender: Optional[str] = Field(None, description="Male, Female, or Other")
    business_type: Optional[str] = Field(
        None, description="Proposed or existing business (e.g. tailoring, dairy, grocery)"
    )
    location: Optional[str] = Field(None, description="City or district (e.g. Lucknow)")
    state: Optional[str] = Field(None, description="Indian state (e.g. Uttar Pradesh)")
    disability_status: Optional[bool] = Field(
        None, description="True if person mentions having a recognized disability (PwD)"
    )
    language: str = Field(
        default="en", description="Detected language code (e.g. 'en', 'hi', 'ta', 'te')"
    )
    extraction_mode: str = Field(
        default="gemini", description="'gemini' or 'fallback'"
    )
    friendly_acknowledgment: Optional[str] = Field(
        None,
        description="A warm, concise 1-2 sentence acknowledgment of the information received.",
    )


SYSTEM_PROMPT = """You are SchemeSetu's multilingual conversational assistant for Indian entrepreneurs.
Your purpose is to help marginalized entrepreneurs (SC, ST, OBC, Divyangjan, women) discover government financial schemes.

Your STRICT operational boundary:
1. Extract structured profile fields from the user's message (age, income, category, gender, business type, location).
2. Detect the user's language (English, Hindi, etc.) and respond in that same language.
3. Provide a brief, warm 1-sentence acknowledgment of what you understood.
4. CRITICAL RULE: NEVER approve or deny loans. NEVER calculate subsidy or EMI. NEVER tell the user they are eligible or ineligible. The deterministic government rule engine handles all financial decisions.

Always return a JSON object conforming to the ExtractedEntities schema.
"""
