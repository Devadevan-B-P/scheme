import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import settings

async def generate_conversational_reply(user_message: str, profile_state: dict, eligibility_results: list) -> str:
    """
    Translates raw extraction and eligibility results into a natural language response
    for the user.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=settings.GEMINI_API_KEY,
    )

    system_prompt = """You are SchemeSetu, a helpful assistant guiding marginalized entrepreneurs to government schemes.
Read the provided Profile State and Eligibility Results.
If the user is missing information (like age or category) needed to pass the rules, politely ask them for it.
If they are Not Eligible, explain exactly which rule failed in simple terms based ONLY on the provided results. NEVER invent rules.
Keep it concise, conversational, and empathetic. Do not use markdown headers."""

    # Serialize context to JSON so the LLM can read it clearly
    context = f"""
Profile State:
{json.dumps(profile_state, indent=2, default=str)}

Eligibility Results:
{json.dumps(eligibility_results, indent=2, default=str)}

User Message: {user_message}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=context)
    ]

    response = await llm.ainvoke(messages)
    content = response.content
    
    if isinstance(content, list):
        # Extract text blocks if returned as a list
        return " ".join(block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text")
        
    return str(content)
