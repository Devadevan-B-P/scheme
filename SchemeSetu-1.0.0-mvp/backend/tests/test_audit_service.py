import pytest
from app.services.audit_service import audit_service
import asyncio

# Usually we would mock the DB, but since the tests might use a mock mongo fixture,
# let's just test the hashing logic for now if we can't spin up mongo easily in pytest.

def test_compute_hash():
    # Simple hash test
    data = "test_data"
    expected_hash = audit_service._compute_hash(data)
    assert len(expected_hash) == 64  # SHA-256 hex length

def test_dict_to_stable_json():
    # Ensure stable ordering
    d1 = {"b": 2, "a": 1}
    d2 = {"a": 1, "b": 2}
    assert audit_service._dict_to_stable_json(d1) == audit_service._dict_to_stable_json(d2)

