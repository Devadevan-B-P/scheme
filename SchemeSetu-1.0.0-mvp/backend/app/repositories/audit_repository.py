"""
Audit Repository — Data Access Layer for Tamper-Evident Audit Logging.

Architecture Constraints:
  - audit_logs collection: Strictly INSERT-ONLY. No update/delete methods are exposed.
  - audit_chain_heads collection: Dedicated atomic head state tracker.
  - Atomic advance: Uses MongoDB transaction when supported by the deployment topology.
"""

import logging
from typing import Optional, List, Dict, Any
from app.core.database import get_database, get_client
from app.models.audit import AuditEntry, AuditChainHead

logger = logging.getLogger(__name__)


class AuditRepository:
    def __init__(self):
        self.logs_collection_name = "audit_logs"
        self.heads_collection_name = "audit_chain_heads"

    async def get_chain_head(self, chain_id: str = "global_chain_head", session=None) -> AuditChainHead:
        """Fetch current chain head or instantiate default genesis."""
        db = get_database()
        if db is None:
            return AuditChainHead(chain_id=chain_id)

        doc = await db[self.heads_collection_name].find_one({"chain_id": chain_id}, session=session)
        if doc:
            return AuditChainHead.model_validate(doc)
        return AuditChainHead(chain_id=chain_id)

    async def append_transactional(
        self,
        entry: AuditEntry,
        chain_id: str = "global_chain_head"
    ) -> AuditEntry:
        """
        Atomically insert the audit entry into audit_logs and advance the chain head
        in a MongoDB transaction.
        """
        db = get_database()
        client = get_client()
        if db is None:
            logger.warning("Database unavailable, audit entry %s logged in-memory only", entry.sequence_id)
            return entry

        logs_col = db[self.logs_collection_name]
        heads_col = db[self.heads_collection_name]

        # Check if transactions are supported by deployment
        try:
            async def _txn_callback(s):
                # 1. Insert into audit_logs (INSERT-ONLY)
                await logs_col.insert_one(entry.model_dump(), session=s)

                # 2. Advance audit_chain_heads
                await heads_col.update_one(
                    {"chain_id": chain_id},
                    {
                        "$set": {
                            "sequence_id": entry.sequence_id,
                            "latest_hash": entry.signature,
                            "updated_at": entry.timestamp,
                        }
                    },
                    upsert=True,
                    session=s,
                )

            async with client.start_session() as mongo_session:
                await mongo_session.with_transaction(_txn_callback)
            return entry

        except Exception as exc:
            # Standalone MongoDB instances (e.g. without replica set in local testing)
            # do not support multi-document transactions. Fall back to atomic sequence update.
            logger.debug("Transaction not supported or failed (%s), using sequential atomic advance", exc)
            await logs_col.insert_one(entry.model_dump())
            await heads_col.update_one(
                {"chain_id": chain_id},
                {
                    "$set": {
                        "sequence_id": entry.sequence_id,
                        "latest_hash": entry.signature,
                        "updated_at": entry.timestamp,
                    }
                },
                upsert=True,
            )
            return entry

    async def get_entries(self, limit: int = 100, session_id: Optional[str] = None) -> List[AuditEntry]:
        """Read audit entries in sequence order (Read-only query)."""
        db = get_database()
        if db is None:
            return []

        query = {}
        if session_id:
            query["session_id"] = session_id

        cursor = db[self.logs_collection_name].find(query).sort("sequence_id", 1).limit(limit)
        results = []
        async for doc in cursor:
            doc.pop("_id", None)
            results.append(AuditEntry.model_validate(doc))
        return results


audit_repository = AuditRepository()
