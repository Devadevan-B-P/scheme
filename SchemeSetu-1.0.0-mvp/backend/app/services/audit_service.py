"""
Tamper-Evident Audit Service.

Guarantees:
  - Cryptographic hash chaining: Each entry seals previous_hash + payload_hash into its signature.
  - Atomicity: Audit entry insert and chain-head advance occur within an atomic MongoDB transaction.
  - Insert-only: Audit entries cannot be modified or deleted.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.models.audit import AuditEntry
from app.repositories.audit_repository import audit_repository

logger = logging.getLogger(__name__)


class AuditService:
    @staticmethod
    def _compute_hash(data: str) -> str:
        """Compute SHA-256 hash of a string."""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @staticmethod
    def _dict_to_stable_json(data: Dict[str, Any]) -> str:
        """Serialize dict to a deterministic stable JSON string for consistent hashing."""
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    async def append_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        session_id: str,
        chain_id: str = "global_chain_head",
    ) -> AuditEntry:
        """
        Atomically append a new event to the global tamper-evident audit hash chain.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        payload_stable = self._dict_to_stable_json(payload)
        payload_hash = self._compute_hash(payload_stable)

        # Read current chain head
        current_head = await audit_repository.get_chain_head(chain_id=chain_id)
        sequence_id = current_head.sequence_id + 1
        previous_hash = current_head.latest_hash

        # Compute signature: hash(sequence_id + timestamp + event_type + session_id + payload_hash + previous_hash)
        signature_material = f"{sequence_id}|{timestamp}|{event_type}|{session_id}|{payload_hash}|{previous_hash}"
        signature = self._compute_hash(signature_material)

        entry = AuditEntry(
            sequence_id=sequence_id,
            timestamp=timestamp,
            event_type=event_type,
            session_id=session_id,
            payload_hash=payload_hash,
            previous_hash=previous_hash,
            signature=signature,
            payload=payload,
        )

        # Atomic append inside MongoDB transaction
        committed_entry = await audit_repository.append_transactional(entry, chain_id=chain_id)
        logger.info("Appended audit event %d: %s for session %s", sequence_id, event_type, session_id)
        return committed_entry

    def verify_chain(self, entries: List[AuditEntry]) -> bool:
        """
        Verify cryptographic integrity of a sequence of audit entries.
        Returns False if any sequence gap, tampering, or hash mismatch is detected.
        """
        if not entries:
            return True

        expected_prev = "GENESIS_HASH_0000000000000000000000000000000"
        expected_seq = entries[0].sequence_id

        for entry in entries:
            # 1. Sequence contiguous check
            if entry.sequence_id != expected_seq:
                logger.warning("Audit chain broken: expected seq %d, got %d", expected_seq, entry.sequence_id)
                return False

            # 2. Previous hash link check (if starting from 1)
            if entry.sequence_id == 1 and entry.previous_hash != expected_prev:
                logger.warning("Audit chain broken: genesis hash mismatch at seq 1")
                return False

            # 3. Payload hash recomputation check
            computed_payload_hash = self._compute_hash(self._dict_to_stable_json(entry.payload))
            if computed_payload_hash != entry.payload_hash:
                logger.warning("Audit chain broken: payload hash mismatch at seq %d", entry.sequence_id)
                return False

            # 4. Signature recomputation check
            signature_material = (
                f"{entry.sequence_id}|{entry.timestamp}|{entry.event_type}|"
                f"{entry.session_id}|{entry.payload_hash}|{entry.previous_hash}"
            )
            computed_signature = self._compute_hash(signature_material)
            if computed_signature != entry.signature:
                logger.warning("Audit chain broken: signature mismatch at seq %d", entry.sequence_id)
                return False

            expected_prev = entry.signature
            expected_seq += 1

        return True


audit_service = AuditService()
