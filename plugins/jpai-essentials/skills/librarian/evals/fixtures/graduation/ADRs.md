# Decisions

## ADR-1: money is Decimal

- **Status:** Accepted (2026-03-01)
- **Decision:** Every amount is `decimal.Decimal`.
- **Because:** Floats lose cents on summation.

## ADR-2: one ledger per account

- **Status:** Accepted (2026-04-12)
- **Decision:** Each bank account reconciles against its own Ledger.
- **Because:** Shared ledgers made mismatches unattributable.
