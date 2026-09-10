"""
Tests for MongoDB Transactional Audit Logging.
Verifies that append_transactional correctly records to audit_logs and updates audit_chain_heads.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.audit import AuditEntry, AuditChainHead
from app.repositories.audit_repository import AuditRepository


@pytest.mark.asyncio
async def test_append_transactional_mock_transaction():
    """Verify append_transactional executes insert on audit_logs and update on audit_chain_heads within a session."""
    repo = AuditRepository()
    
    mock_db = MagicMock()
    mock_logs = AsyncMock()
    mock_heads = AsyncMock()
    mock_db.__getitem__.side_effect = lambda name: mock_logs if name == "audit_logs" else mock_heads

    mock_session = AsyncMock()
    async def fake_with_transaction(callback):
        return await callback(mock_session)
    mock_session.with_transaction.side_effect = fake_with_transaction

    # Mock async context manager returned by client.start_session()
    mock_client = MagicMock()
    session_ctx = AsyncMock()
    session_ctx.__aenter__.return_value = mock_session
    session_ctx.__aexit__.return_value = None
    mock_client.start_session.return_value = session_ctx


    entry = AuditEntry(
        sequence_id=42,
        timestamp="2026-09-10T12:00:00Z",
        event_type="SCHEME_MATCH_GENERATED",
        session_id="session_xyz",
        payload_hash="payload_hash_42",
        previous_hash="prev_hash_41",
        signature="sig_42",
        payload={"action": "match", "score": 95},
    )

    with patch("app.repositories.audit_repository.get_database", return_value=mock_db), \
         patch("app.repositories.audit_repository.get_client", return_value=mock_client):
        result = await repo.append_transactional(entry, chain_id="global_chain_head")
        
        assert result.sequence_id == 42
        mock_logs.insert_one.assert_called_once()
        mock_heads.update_one.assert_called_once_with(
            {"chain_id": "global_chain_head"},
            {
                "$set": {
                    "sequence_id": 42,
                    "latest_hash": "sig_42",
                    "updated_at": "2026-09-10T12:00:00Z",
                }
            },
            upsert=True,
            session=mock_session,
        )


@pytest.mark.asyncio
async def test_append_transactional_fallback_when_transactions_unsupported():
    """Verify fallback to standalone insert and head update if multi-doc transaction throws an exception."""
    repo = AuditRepository()
    
    mock_db = MagicMock()
    mock_logs = AsyncMock()
    mock_heads = AsyncMock()
    mock_db.__getitem__.side_effect = lambda name: mock_logs if name == "audit_logs" else mock_heads

    # Simulate standalone mongo raising an error on start_session or start_transaction
    mock_client = MagicMock()
    mock_client.start_session.side_effect = RuntimeError("Transactions are not supported on standalone servers")

    entry = AuditEntry(
        sequence_id=43,
        timestamp="2026-09-10T12:05:00Z",
        event_type="CONSENT_RECORDED",
        session_id="session_xyz",
        payload_hash="payload_hash_43",
        previous_hash="sig_42",
        signature="sig_43",
        payload={"consent": True},
    )

    with patch("app.repositories.audit_repository.get_database", return_value=mock_db), \
         patch("app.repositories.audit_repository.get_client", return_value=mock_client):
        result = await repo.append_transactional(entry, chain_id="global_chain_head")
        
        assert result.sequence_id == 43
        # Should execute standalone insert and update
        mock_logs.insert_one.assert_called_once_with(entry.model_dump())
        mock_heads.update_one.assert_called_once_with(
            {"chain_id": "global_chain_head"},
            {
                "$set": {
                    "sequence_id": 43,
                    "latest_hash": "sig_43",
                    "updated_at": "2026-09-10T12:05:00Z",
                }
            },
            upsert=True,
        )
