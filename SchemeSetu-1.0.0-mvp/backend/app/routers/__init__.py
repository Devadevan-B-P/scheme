"""Routers package - shim mapping to app.api."""
from app.api import chat, documents, eligibility, financial, partners, schemes, consent

__all__ = ["chat", "documents", "eligibility", "financial", "partners", "schemes", "consent"]
