# 04 · Controls

> **Draft.** Candidate controls identified. Framework mapping pending.

## Candidate controls

| ID | Control | Mitigates |
|---|---|---|
| K01 | Keep third-party text out of the prompt where possible, for example by showing transfer descriptions in the app instead of passing them to the model; where such text must be included, mark it as untrusted data and neutralize instructions in it | T01, T08 |
| K02 | Confirm state-changing actions outside the model, with a native in-app confirmation instead of a chat reply | T02 |
| K03 | Enforce least privilege at the API layer: delegated per-customer tokens for tool calls, with ownership checked by the core APIs | T05 |
| K04 | Keep nothing in the system prompt that would cause harm if disclosed, and move escalation criteria into code | T03 |
| K05 | Render replies as plain text, or allow links only to an allowlist of Bank domains | T09 |
| K06 | Add Bank-side input and output filtering on top of the provider's filter, including detection of personal data | T01, T04, T06 |
| K07 | Set rate limits and token budgets per customer and per session, with alerts on anomalies | T11 |
| K08 | Minimize stored data: redact tool results and personal data in transcripts, shorten retention, restrict access by role | T06 |
| K09 | Run outsourcing due diligence on the provider: data use, retention, location, notice of model changes, and the transfer basis under Ley 25.326 | T07, T10 |
| K10 | Govern retrieval content: review articles before indexing and monitor the integrity of the index | T08 |
| K11 | Ground answers on fees and rights in retrieved passages with citations, and refuse or escalate when no passage supports the answer | T04, T12 |
| K12 | Test before release and on every provider change with an adversarial suite, and monitor tool-call patterns in production | T01, T02, T10 |
| K13 | Tell customers they are talking to an AI and keep a clear path to a human | T12 |
| K14 | Mark handoff summaries as model-generated, and require agents to confirm any request directly with the customer before acting on it | T01, T06 |

## Framework mapping

| ID | NIST AI RMF 1.0 | NIST AI 600-1 | ISO/IEC 42001 Annex A | BCRA AI guide section |
|---|---|---|---|---|
| K01–K14 | pending | pending | pending | pending |

ISO/IEC 42001 references will be given by control number only, checked against the licensed text of the standard.

The BCRA guide sections used for mapping are: Gobierno y gestión del riesgo de IA · Gestión y calidad de datos · Desarrollo, validación y monitoreo de modelos · Gestión de sesgos, equidad y explicabilidad · Ciberseguridad · Continuidad operativa y resiliencia · Tercerización · Transparencia.
