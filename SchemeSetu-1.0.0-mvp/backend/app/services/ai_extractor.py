"""
AI entity extraction service using Gemini via LangChain.

Converts a raw user message into a structured :class:`PartialProfileExtraction`
object using LangChain's `with_structured_output` binding.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.models.ai_schemas import PartialProfileExtraction

_SYSTEM_PROMPT = (
    "You are an entity extraction engine for a government schemes portal. "
    "Extract relevant beneficiary details from the user's message. "
    "If a piece of information is not provided, leave that field null. "
    "Do not guess or infer values."
)


async def extract_entities_from_message(
    user_message: str,
    current_state: dict | None = None,
) -> PartialProfileExtraction:
    """
    Extract structured beneficiary profile fields from a single user message.

    Parameters
    ----------
    user_message:
        The raw text received from the beneficiary.
    current_state:
        (Optional) A snapshot of the beneficiary's current profile state.
        Reserved for future use — e.g. few-shot context or slot-filling hints.
        Not used in the LLM call yet but accepted to keep the API stable.

    Returns
    -------
    :class:`PartialProfileExtraction`
        A Pydantic object where every field that was NOT mentioned in the
        message is ``None``.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=settings.GEMINI_API_KEY,
    )

    # method="function_calling" with include_raw=False bypasses the AFC
    # retry loop that caused the AsyncModels.generate_content warning and
    # the 20-25s overhead. The schema is still enforced by Pydantic on return.
    structured_llm = llm.with_structured_output(
        PartialProfileExtraction,
        method="function_calling",
        include_raw=False,
    )

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    result: PartialProfileExtraction = await structured_llm.ainvoke(messages)
    return result
