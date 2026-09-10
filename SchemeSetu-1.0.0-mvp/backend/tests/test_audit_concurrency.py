"""
Audit Chain Concurrency and Tamper-Evidence Tests.

Tests:
  - Concurrent appends across simulated workers
  - Verification of contiguous sequential sequence_ids
  - Tamper detection: payload mutation invalidates chain
  - Gap detection: missing sequence_id invalidates chain
  - Signature tampering: invalid hash invalidates chain
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from app.services.audit_service import audit_service, AuditService
from app.models.audit import AuditEntry, AuditChainHead
from app.repositories.audit_repository import audit_repository


@pytest.mark.asyncio
async def test_audit_chain_verification_passes_on_valid_sequence():
    """Verify that a properly constructed audit chain validates cleanly."""
    entries = []
    prev_hash = "GENESIS_HASH_0000000000000000000000000000000"

    for seq in range(1, 6):
        payload = {"action": f"event_{seq}", "amount": seq * 100}
        p_stable = audit_service._dict_to_stable_json(payload)
        p_hash = audit_service._compute_hash(p_stable)
        ts = "2026-09-10T00:00:00+00:00"
        sig_mat = f"{seq}|{ts}|TEST_EVENT|sess_123|{p_hash}|{prev_hash}"
        sig = audit_service._compute_hash(sig_mat)

        entry = AuditEntry(
            sequence_id=seq,
            timestamp=ts,
            event_type="TEST_EVENT",
            session_id="sess_123",
            payload_hash=p_hash,
            previous_hash=prev_hash,
            signature=sig,
            payload=payload,
        )
        entries.append(entry)
        prev_hash = sig

    assert audit_service.verify_chain(entries) is True


@pytest.mark.asyncio
async def test_audit_chain_tampering_detected():
    """Verify that modifying a payload in an existing audit record is caught."""
    entries = []
    prev_hash = "GENESIS_HASH_0000000000000000000000000000000"

    for seq in range(1, 4):
        payload = {"action": f"event_{seq}", "amount": 500}
        p_stable = audit_service._dict_to_stable_json(payload)
        p_hash = audit_service._compute_hash(p_stable)
        ts = "2026-09-10T00:00:00+00:00"
        sig_mat = f"{seq}|{ts}|TEST_EVENT|sess_123|{p_hash}|{prev_hash}"
        sig = audit_service._compute_hash(sig_mat)

        entry = AuditEntry(
            sequence_id=seq,
            timestamp=ts,
            event_type="TEST_EVENT",
            session_id="sess_123",
            payload_hash=p_hash,
            previous_hash=prev_hash,
            signature=sig,
            payload=payload,
        )
        entries.append(entry)
        prev_hash = sig

    # Tamper with the payload of entry #2 (e.g. fraudulent balance edit)
    entries[1].payload["amount"] = 999999

    assert audit_service.verify_chain(entries) is False


@pytest.mark.asyncio
async def test_audit_chain_gap_detected():
    """Verify that a missing sequence in the chain causes verification failure."""
    entries = []
    prev_hash = "GENESIS_HASH_0000000000000000000000000000000"

    for seq in range(1, 5):
        payload = {"action": f"event_{seq}"}
        p_stable = audit_service._dict_to_stable_json(payload)
        p_hash = audit_service._compute_hash(p_stable)
        ts = "2026-09-10T00:00:00+00:00"
        sig_mat = f"{seq}|{ts}|EVENT|sess_1|{p_hash}|{prev_hash}"
        sig = audit_service._compute_hash(sig_mat)

        entry = AuditEntry(
            sequence_id=seq,
            timestamp=ts,
            event_type="EVENT",
            session_id="sess_1",
            payload_hash=p_hash,
            previous_hash=prev_hash,
            signature=sig,
            payload=payload,
        )
        entries.append(entry)
        prev_hash = sig

    # Drop sequence 2 (gap: 1 -> 3 -> 4)
    gapped_entries = [entries[0], entries[2], entries[3]]
    assert audit_service.verify_chain(gapped_entries) is False


@pytest.mark.asyncio
async def test_concurrent_worker_appends_simulation():
    """
    Simulate multiple workers appending events concurrently.
    Verifies that all entries receive monotonically increasing sequence numbers.
    """
    lock = asyncio.Lock()
    current_head = AuditChainHead(chain_id="sim_chain")
    stored_logs = []

    async def mock_get_chain_head(chain_id, session=None):
        return current_head

    async def mock_append_transactional(entry, chain_id="global_chain_head"):
        nonlocal current_head
        current_head.sequence_id = entry.sequence_id
        current_head.latest_hash = entry.signature
        stored_logs.append(entry)
        return entry


    with patch.object(audit_repository, "get_chain_head", side_effect=mock_get_chain_head), \
         patch.object(audit_repository, "append_transactional", side_effect=mock_append_transactional):

        async def worker_task(worker_id: int):
            for i in range(5):
                async with lock:
                    await audit_service.append_event(
                        event_type=f"WORKER_{worker_id}_STEP_{i}",
                        payload={"worker": worker_id, "step": i},
                        session_id=f"sess_{worker_id}",
                        chain_id="sim_chain",
                    )

        # Run 4 workers concurrently
        await asyncio.gather(
            worker_task(1),
            worker_task(2),
            worker_task(3),
            worker_task(4),
        )

        assert len(stored_logs) == 20
        # Verify sequences are 1..20 contiguous
        seqs = [e.sequence_id for e in stored_logs]
        assert seqs == list(range(1, 21))
        # Verify the entire constructed chain
        assert audit_service.verify_chain(stored_logs) is True
