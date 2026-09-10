# AI Boundaries

## Core Principle
**AI understands the user; the deterministic engine makes the financial decision.**

## Decision Boundary Audit

### What the AI (Gemini) IS allowed to do:
- ✅ **Extraction**: Extract entities (age, income, category, business type, location) from conversational text.
- ✅ **Intent Detection**: Understand what the user wants to do (e.g., "I want a loan", "I need help finding a scheme").
- ✅ **Translation & Language**: Communicate in multiple languages and translate user input.
- ✅ **Question Generation**: Generate the "Next-Best-Question" to ask the user when profile data is missing.

### What the AI (Gemini) is strictly FORBIDDEN from doing:
- ❌ **Eligibility**: Gemini NEVER decides if a user is eligible for a scheme.
- ❌ **Financial Calculations**: Gemini NEVER calculates subsidy percentages, margin money, or EMI.
- ❌ **Approval**: Gemini NEVER approves a loan or partner match.

## Verification
- All generative requests run through `backend/app/agent/gemini_client.py`.
- The outputs of the AI are forced into strict `Pydantic` schemas (Structured Outputs).
- These structured outputs are passed into `backend/app/engine/eligibility.py` and `backend/app/engine/financial.py` which contain hardcoded, mathematical, and deterministic Python logic to make the final decisions.
