# 06 · Findings

> **Draft.** Findings in v0.1 come from design review only. Test evidence is added in v0.2. F01 recorded; more follow as the threat analysis advances.

## Format

| Field | Content |
|---|---|
| ID | F-number |
| Title | One-line statement of the problem |
| Severity | From the inherent rating in [03-risk-register.md](03-risk-register.md) |
| Related threats | T-numbers |
| Evidence | Design review, or test ID from [05-test-plan.md](05-test-plan.md) |
| Recommendation | Control IDs from [04-controls.md](04-controls.md) and what to change |
| Status | Open, accepted or resolved |

## Findings

| ID | Title | Severity | Related threats | Evidence | Recommendation | Status |
|---|---|---|---|---|---|---|
| F01 | Customer data under financial secrecy is sent to a provider abroad without a verified legal and contractual basis | High | T07 | Design review: [01-system.md](01-system.md) section 8 records the provider's terms as unverified; see T07 in [02-threat-model.md](02-threat-model.md) | K09, K16, K13: establish the transfer basis under Ley 25.326 art. 12, bring the contract up to BCRA Section 10.3, notify the SEFYC if the service is critical, minimize the data sent and tell customers | Open |
