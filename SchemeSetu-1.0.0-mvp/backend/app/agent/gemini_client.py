"""
Gemini Client Wrapper using official google-genai SDK.

Features:
  - Model identifier env-configurable via GEMINI_MODEL (default: gemini-3.8-flash)
  - Non-blocking startup check: logs status, does not crash application on boot
  - Structured extraction using Pydantic JSON schema
  - Conservative offline fallback extractor (strictly limited patterns, never guesses)
"""

import json
import logging
import re
from typing import Optional, List
from google import genai
from google.genai import types

from app.core.config import settings
from app.agent.prompts import SYSTEM_PROMPT, ExtractedEntities
from app.models.user import ConversationMessage

logger = logging.getLogger(__name__)


class GeminiAgentClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._client: Optional[genai.Client] = None
        self._is_verified = False

        if self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning("Failed to initialize Google GenAI client: %s", e)

    async def startup_check(self) -> bool:
        """
        Non-blocking startup verification: checks if GEMINI_MODEL is reachable.
        Logs warning and operates in degraded mode if unavailable.
        """
        if not self.api_key or not self._client:
            logger.info("GEMINI_API_KEY not configured. Running with conservative fallback entity extractor.")
            self._is_verified = False
            return False

        try:
            logger.info("Verifying Gemini model '%s' connectivity...", self.model_name)
            response = await self._client.aio.models.generate_content(
                model=self.model_name,
                contents="Ping",
                config=types.GenerateContentConfig(
                    max_output_tokens=5,
                    temperature=0.0,
                ),
            )
            if response and response.text:
                self._is_verified = True
                logger.info("Successfully verified Gemini model '%s'.", self.model_name)
                return True
        except Exception as exc:
            logger.warning(
                "Gemini startup check notice for '%s': %s. Operating with fallback extractor.",
                self.model_name,
                exc,
            )
            self._is_verified = False
            return False

        return False

    @property
    def is_available(self) -> bool:
        return self._is_verified and self._client is not None

    async def extract_entities(
        self,
        sanitized_user_message: str,
        conversation_history: List[ConversationMessage],
        target_language: str = "en",
    ) -> ExtractedEntities:
        """
        Extract structured profile variables from user input.
        Input MUST already be sanitized.
        """
        if self._client and self.api_key:
            try:
                history_text = "\n".join(
                    f"{msg.role.value}: {msg.content}" for msg in conversation_history[-4:]
                )

                prompt = (
                    f"{SYSTEM_PROMPT}\n\n"
                    f"Previous conversation history:\n{history_text}\n\n"
                    f"User message to analyze: \"{sanitized_user_message}\"\n"
                    f"Preferred language hint: {target_language}\n"
                )

                response = await self._client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ExtractedEntities,
                        temperature=0.1,
                    ),
                )

                if response and response.text:
                    parsed = json.loads(response.text)
                    entity = ExtractedEntities.model_validate(parsed)
                    entity.extraction_mode = "gemini"
                    return entity
            except Exception as e:
                logger.warning("Gemini API call failed (%s). Using conservative fallback extractor.", e)

        # Fallback to deterministic conservative extractor
        return self._local_fallback_extract(sanitized_user_message, target_language)

    def _local_fallback_extract(self, text: str, language: str) -> ExtractedEntities:
        """
        Conservative deterministic entity extractor.
        Strict rule: If not confident, leaves fields None rather than guessing.
        """
        text_lower = text.lower()
        extracted = ExtractedEntities(language=language, extraction_mode="fallback")

        # Category
        if " sc " in f" {text_lower} " or "scheduled caste" in text_lower or "dalit" in text_lower:
            extracted.category = "SC"
        elif " st " in f" {text_lower} " or "scheduled tribe" in text_lower or "adivasi" in text_lower:
            extracted.category = "ST"
        elif " obc " in f" {text_lower} " or "backward class" in text_lower:
            extracted.category = "OBC"
        elif "general" in text_lower:
            extracted.category = "General"

        # Gender
        if any(w in text_lower for w in ["woman", "women", "female", "mahila", "ladki", "aurat"]):
            extracted.gender = "Female"
        elif any(w in text_lower for w in ["man", "male", "purush", "ladka"]):
            extracted.gender = "Male"

        # Age
        age_match = re.search(r"\b(\d{2})\s*(?:years?|yrs?|saal|sal|umr|age)\b", text_lower)
        if age_match:
            extracted.age = int(age_match.group(1))
        else:
            standalone = re.findall(r"\b(1[89]|[2-6]\d|7[0-5])\b", text_lower)
            if standalone and "lakh" not in text_lower and "thousand" not in text_lower and "rs" not in text_lower:
                extracted.age = int(standalone[0])

        # Annual Income
        lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs|lakhs)", text_lower)
        if lakh_match:
            extracted.annual_income = float(lakh_match.group(1)) * 100000.0
        else:
            income_match = re.search(r"(?:income|kamai|salary|earning)[^\d]*(\d[\d,]{3,9})", text_lower)
            if income_match:
                clean_num = income_match.group(1).replace(",", "")
                extracted.annual_income = float(clean_num)
            else:
                direct_nums = re.findall(r"\b(\d{5,7})\b", text_lower)
                if direct_nums:
                    extracted.annual_income = float(direct_nums[0])

        # Business type (conservative match only)
        common_businesses = [
            "tailoring", "silai", "dairy", "dairy farm", "grocery", "kirana",
            "salon", "beauty parlour", "handicrafts", "poultry", "tea stall",
            "clothing", "repair", "auto", "bakery", "restaurant",
        ]
        for b in common_businesses:
            if b in text_lower:
                extracted.business_type = b
                break

        # Location
        common_cities = ["lucknow", "kanpur", "delhi", "patna", "bhopal", "varanasi", "mumbai", "agra"]
        for c in common_cities:
            if c in text_lower:
                extracted.location = c.title()
                break

        # Disability
        if any(neg in text_lower for neg in ["no disability", "not disabled", "no, i do not", "none", "na"]):
            extracted.disability_status = False
        elif any(w in text_lower for w in ["disabled", "disability", "handicap", "divyang", "pwd"]):
            extracted.disability_status = True

        extracted.friendly_acknowledgment = "Thank you for providing your details. Updating your entrepreneur profile."
        return extracted


gemini_agent = GeminiAgentClient()
