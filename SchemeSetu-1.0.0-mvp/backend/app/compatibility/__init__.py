"""Legacy compatibility adapter routers."""
from fastapi import APIRouter
from app.compatibility.legacy_chat import router as legacy_chat_router
from app.compatibility.legacy_docs import router as legacy_docs_router
from app.compatibility.legacy_partners import router as legacy_partners_router
from app.compatibility.legacy_admin import router as legacy_admin_router

compatibility_router = APIRouter()
compatibility_router.include_router(legacy_chat_router)
compatibility_router.include_router(legacy_docs_router)
compatibility_router.include_router(legacy_partners_router)
compatibility_router.include_router(legacy_admin_router)
