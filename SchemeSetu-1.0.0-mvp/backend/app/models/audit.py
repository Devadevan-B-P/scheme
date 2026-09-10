from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class AuditEntry(BaseModel):
    """
    Single record in the tamper-evident audit log.
    INSERT-ONLY — never updated or deleted.
    """
    sequence_id: int = Field(..., description="Atomic incrementing integer for the global chain")
    timestamp: str = Field(..., description="UTC ISO 8601 timestamp")
    event_type: str = Field(..., description="Type of event, e.g., CONSENT_GRANTED, ELIGIBILITY_EVALUATED")
    session_id: str = Field(..., description="Associated session ID")
    payload_hash: str = Field(..., description="SHA-256 hash of the redacted event payload")
    previous_hash: str = Field(..., description="SHA-256 hash of the preceding AuditEntry")
    signature: str = Field(..., description="Hash of this current entry for chain integrity")
    payload: Dict[str, Any] = Field(default_factory=dict)


class AuditChainHead(BaseModel):
    """
    State tracking document for the tamper-evident chain head.
    Updated atomically alongside audit_logs insertion in a transaction.
    """
    chain_id: str = Field(default="global_chain_head")
    sequence_id: int = Field(default=0)
    latest_hash: str = Field(default="GENESIS_HASH_0000000000000000000000000000000")
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
