# 04 · Controls

> **Draft.** Candidate controls identified. Framework mapping pending.

## Candidate controls

| ID | Control | Mitigates |
|---|---|---|
| K01 | Keep third-party text out of the prompt where possible, for example by showing transfer descriptions in the app instead of passing them to the model; where such text must be included, mark it as untrusted data and neutralize instructions in it | T01, T08 |
| K02 | Confirm state-changing actions outside the model: the model proposes, the app confirms with a native dialog that names the action and the card, and the orchestrator executes only on the app's confirmation, never on the model's word | T02 |
| K03 | Enforce least privilege at the API layer: delegated per-customer tokens for tool calls, with ownership checked by the core APIs | T05 |
| K04 | Keep nothing in the system prompt that would cause harm if disclosed, and move escalation criteria into code | T03 |
| K05 | Render replies as plain text, or allow links only to an allowlist of Bank domains | T09 |
| K06 | Add Bank-side input and output filtering on top of the provider's filter, including detection of personal data | T01, T04, T06 |
| K07 | Set rate limits and token budgets per customer and per session, and limits on state-changing tool calls per customer and per period, with alerts on anomalies | T02, T11 |
| K08 | Minimize stored data: redact tool results and personal data in transcripts, shorten retention, restrict access by role | T06 |
| K09 | Put the provider arrangement in order before it runs: a transfer basis under Ley 25.326 art. 12 (model clauses or an adequate territory), a contract that meets BCRA Section 10.3 and binds the provider and its staff to the art. 39 duty of reserve, with zero or shortest retention, no training, no human review or review only under confidentiality, subprocessor consent, notice of law-enforcement requests, breach notification, audit rights and exit assistance; the SEFYC notice under Section 10.1 if the service is critical; documentation under Section 4.6; pre-contract risk assessment per the BCRA AI guide | T07, T10 |
| K10 | Govern retrieval content: review articles before indexing and monitor the integrity of the index | T08 |
| K11 | Ground answers on fees and rights in retrieved passages with citations, and refuse or escalate when no passage supports the answer | T04, T12 |
| K12 | Test before release and on every provider change with an adversarial suite, and monitor tool-call patterns in production | T01, T02, T10 |
| K13 | Tell customers they are talking to an AI, that a third-party provider processes the conversation and where, and keep a clear path to a human | T07, T12 |
| K14 | Mark handoff summaries as model-generated, and require agents to confirm any request directly with the customer before acting on it | T01, T06 |
| K15 | Notify the customer through a separate channel whenever the assistant changes the state of their account, with a one-tap path in the app to undo it | T02 |
| K16 | Minimize and pseudonymize what crosses TB2: replace the customer's name and identifier with a session token, pass only the transaction fields the model needs, and drop or truncate free text | T07, T01 |
| K17 | Keep an exit strategy: an abstraction layer so the provider can be replaced, a tested fallback (a second provider or a degraded mode without the assistant), and prompts, evaluations and configuration owned by the Bank | T07, T10 |

## Framework mapping

| ID | NIST AI RMF 1.0 | NIST AI 600-1 | ISO/IEC 42001 Annex A | BCRA AI guide section |
|---|---|---|---|---|
| K01–K17 | pending | pending | pending | pending |

ISO/IEC 42001 references will be given by control number only, checked against the licensed text of the standard.

The BCRA guide sections used for mapping are: Gobierno y gestión del riesgo de IA · Gestión y calidad de datos · Desarrollo, validación y monitoreo de modelos · Gestión de sesgos, equidad y explicabilidad · Ciberseguridad · Continuidad operativa y resiliencia · Tercerización · Transparencia.
