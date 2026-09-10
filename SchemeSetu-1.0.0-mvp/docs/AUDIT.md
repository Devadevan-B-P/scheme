# Audit Trail Architecture

The platform uses a tamper-evident global insertion-ordered hash chain to track consequential system actions without leaking PII.

## 1. The Hash Chain
Every audit entry is cryptographically linked to the previous entry:
```
chain_hash = SHA256(previous_hash + sequence_id + timestamp + payload_hash)
```

## 2. Transactional Appends
Appending an audit record is an atomic MongoDB transaction:
1. Lock and read the `audit_chain_heads` for the current sequence.
2. Insert the new log into `audit_logs` containing the linked hashes.
3. Advance `next_sequence_id` in `audit_chain_heads`.
4. Commit.

## 3. Payload Canonicalization
Before hashing, the payload is normalized using canonical JSON (sorted keys, no spaces):
```python
canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
payload_hash = sha256(canonical.encode()).hexdigest()
```

## 4. Retained Events
Events recorded in the chain include:
- `CONSENT_GRANTED`
- `OCR_COMPLETED`
- `PROFILE_CONFIRMED`
- `ELIGIBILITY_DECIDED`
- `PARTNER_MATCHED`

*Note: Raw text, uploaded bytes, and specific unneeded PII are excluded from the hashed payloads.*
