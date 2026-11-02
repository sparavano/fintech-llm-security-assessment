# 04 · Controls

> **v0.1, with one change from the v0.2 tests and two from v0.4.** K01 has two forms; the tests showed that only the first, keeping third-party text out of the prompt, can be relied on (see [06-findings.md](06-findings.md#recommendations-after-testing-v03)). From v0.4, K08 redacts by reference instead of by deletion, and K18 is added; both come from experiment FX-01 ([07-forensic-readiness.md](07-forensic-readiness.md#proposed-control-k18-and-an-amendment-to-k08)). Seventeen controls identified from the design review and one from FX-01, with the threats each one treats and a proposed mapping to four frameworks. The mapping is a working proposal: it should be checked against the licensed text of the ISO standards and against NIST AI 100-1 and 600-1 before it is relied on.

## Candidate controls

| ID | Control | Mitigates |
|---|---|---|
| K01 | Keep third-party text out of the prompt where possible, for example by showing transfer descriptions in the app instead of passing them to the model; where such text, or any retrieved content, must be included, mark it as data rather than instructions and neutralize instructions in it | T01, T02, T08 |
| K02 | Confirm state-changing actions outside the model: the model proposes, the app confirms with a native dialog that names the action and the card, and the orchestrator executes only on the app's confirmation, never on the model's word | T02, T01 |
| K03 | Enforce least privilege at the API layer: delegated per-customer tokens for tool calls, with ownership checked by the core APIs | T05 |
| K04 | Keep nothing in the system prompt that would cause harm if disclosed, and move escalation criteria into code | T03 |
| K05 | Treat model output as untrusted input to the app: render replies as plain text, or allow links only to an allowlist of Bank domains, and never render images from model output | T09, T01, T08 |
| K06 | Add Bank-side input and output filtering on top of the provider's filter, including detection of personal data, of commitments the assistant may not make, and of extraction attempts | T01, T03, T04, T08 |
| K07 | Set rate limits and token budgets per customer and per session, and limits on state-changing tool calls per customer and per period, with alerts on anomalies | T02, T11 |
| K08 | Minimize stored data: redact tool results and personal data in transcripts by reference, not by deletion (replace third-party text with its hash and a pointer to its system of record, so the record still proves what the model received), shorten retention, restrict access by role | T06 |
| K09 | Put the provider arrangement in order: a transfer basis under Ley 25.326 art. 12 (model clauses or an adequate territory), a contract that meets BCRA Section 10.3 and binds the provider and its staff to the art. 39 duty of reserve, with zero or shortest retention, no training, no human review or review only under confidentiality, subprocessor consent, notice of law-enforcement requests, breach notification, audit rights and exit assistance; the SEFYC notice under Section 10.1 if the service is critical; documentation under Section 4.6; pre-contract risk assessment per the BCRA AI guide | T07, T10 |
| K10 | Govern retrieval content as code: review before indexing, separate the right to publish for people from the right to feed the model, and monitor the integrity of the index | T08 |
| K11 | Ground answers on fees, rights and procedures in retrieved passages with citations, and refuse or hand off when no passage supports the answer | T04, T12 |
| K12 | Test before release, on a schedule and on every provider change with an adversarial and accuracy suite; monitor behavior, tool-call patterns and cross-customer calls in production | T01, T02, T03, T04, T05, T10, T12 |
| K13 | Tell customers they are talking to an AI, what it can and cannot decide, that a third-party provider processes the conversation and where, and keep a clear path to a human | T07, T12 |
| K14 | Mark handoff summaries as model-generated, and require agents to confirm any request directly with the customer before acting on it | T01, T06 |
| K15 | Notify the customer through a separate channel whenever the assistant changes the state of their account, and point to the app's own path to undo it, with the confirmation the app already requires | T02 |
| K16 | Minimize and pseudonymize what crosses TB2: replace the customer's name and identifier with a session token, pass only the transaction fields the model needs, and drop or truncate free text | T07, T01 |
| K17 | Keep an exit strategy: an abstraction layer so the provider can be replaced, a tested fallback (a second provider or a degraded mode without the assistant), and prompts, evaluations and configuration owned by the Bank | T07, T10 |
| K18 | Keep a forensic-grade, minimized record of every session: for every call to the model, the hash of its exact input with references to systems of record that keep versions (transactions, help center articles, system prompt, tool definitions), the model requested and the names the provider reports back, settings and controls in force; every tool call and core API call with the customer it ran for and the channel that triggered it; every reply before and after rendering. Hash-chain the record and write its head, at least once per session, to a store outside the control of whoever writes the log. Keep the versions the record points to for as long as the record. It acts on detection and response, not on prevention | T01, T02, T05, T06, T08, T10 |

## Framework mapping

Columns: NIST AI RMF 1.0 subcategories; NIST AI 600-1 risk categories (the Generative AI Profile is mapped at the level of its twelve risk categories, not of its individual suggested actions); ISO/IEC 42001:2023 Annex A control numbers; ISO/IEC 27001:2022 Annex A control numbers, because several controls are ordinary information security controls the Bank already owes under its baseline; and the BCRA AI guide section. ISO references are by number only; no text from the standards is reproduced.

| ID | NIST AI RMF 1.0 | NIST AI 600-1 | ISO/IEC 42001 Annex A | ISO/IEC 27001:2022 Annex A | BCRA AI guide |
|---|---|---|---|---|---|
| K01 | MAP 2.2, MEASURE 2.7, MANAGE 1.3 | Information Security; Information Integrity | A.6.2.2, A.6.2.4 | 8.26, 8.28 | Ciberseguridad; Gestión y calidad de datos |
| K02 | MAP 3.5, MANAGE 2.4 | Human-AI Configuration | A.6.2.2, A.9.2, A.9.4 | 8.26 | Gobierno y gestión del riesgo de IA; Ciberseguridad |
| K03 | MEASURE 2.7, MANAGE 1.3 | Information Security | A.6.2.2 | 5.15, 5.18, 8.2, 8.3 | Ciberseguridad |
| K04 | MAP 2.2, MEASURE 2.7 | Information Security | A.6.2.3, A.6.2.7 | 8.26 | Ciberseguridad |
| K05 | MEASURE 2.7, MANAGE 1.3 | Information Security; Information Integrity | A.6.2.2, A.6.2.5 | 8.26, 8.28 | Ciberseguridad |
| K06 | MEASURE 2.7, MEASURE 2.10, MANAGE 4.1 | Information Security; Data Privacy; Information Integrity | A.6.2.6, A.6.2.8 | 8.12, 8.16 | Ciberseguridad; Desarrollo, validación y monitoreo de modelos |
| K07 | MEASURE 2.7, MANAGE 4.1 | Information Security | A.4.5, A.6.2.6 | 8.6, 8.16 | Ciberseguridad; Continuidad operativa y resiliencia |
| K08 | GOVERN 1.1, MEASURE 2.10 | Data Privacy | A.4.3, A.6.2.8 | 5.33, 5.34, 8.3, 8.10, 8.11 | Gestión y calidad de datos; Ciberseguridad |
| K09 | GOVERN 1.1, GOVERN 6.1, GOVERN 6.2, MAP 4.1, MAP 4.2, MANAGE 3.1 | Value Chain and Component Integration; Data Privacy | A.8.5, A.10.2, A.10.3 | 5.19, 5.20, 5.21, 5.22, 5.23, 5.31, 5.34 | Tercerización; Gobierno y gestión del riesgo de IA |
| K10 | MEASURE 2.7, MANAGE 1.3 | Information Integrity; Information Security | A.7.3, A.7.4, A.7.5 | 5.15, 8.15, 8.32 | Gestión y calidad de datos; Ciberseguridad |
| K11 | MEASURE 2.5, MEASURE 2.8, MEASURE 2.9 | Confabulation; Information Integrity | A.6.2.2, A.6.2.4, A.8.2 | — | Desarrollo, validación y monitoreo de modelos; Transparencia |
| K12 | MEASURE 1.1, MEASURE 2.4, MEASURE 2.5, MEASURE 2.7, MANAGE 2.2, MANAGE 4.1 | Information Security; Confabulation | A.6.2.4, A.6.2.6, A.6.2.8 | 8.15, 8.16, 8.29, 8.32 | Desarrollo, validación y monitoreo de modelos; Ciberseguridad |
| K13 | MAP 2.2, MEASURE 2.8, MANAGE 4.1 | Human-AI Configuration | A.8.2, A.8.5 | 5.34 | Transparencia |
| K14 | MAP 3.5, MANAGE 4.1 | Human-AI Configuration; Information Integrity | A.8.2, A.9.2 | — | Gobierno y gestión del riesgo de IA; Transparencia |
| K15 | MAP 3.5, MANAGE 4.1 | Human-AI Configuration | A.8.2, A.9.2 | — | Transparencia; Gobierno y gestión del riesgo de IA |
| K16 | GOVERN 1.1, MEASURE 2.10 | Data Privacy; Information Security | A.4.3, A.6.2.2 | 5.34, 8.11, 8.12 | Gestión y calidad de datos; Ciberseguridad |
| K17 | GOVERN 1.7, GOVERN 6.2, MANAGE 3.1 | Value Chain and Component Integration | A.10.3 | 5.22, 5.23, 5.30 | Tercerización; Continuidad operativa y resiliencia |
| K18 | MANAGE 4.1 | Information Security; Information Integrity | A.6.2.8 | 5.28, 8.15, 8.17 | Ciberseguridad; Desarrollo, validación y monitoreo de modelos |

Reading the table by framework:

- *NIST AI RMF.* Eight of the eighteen controls land in MEASURE 2.7 (security and resilience) and seven in MANAGE 4.1 (post-deployment monitoring, which includes incident response), which says that this system's risks are operational more than conceptual. The GOVERN 6 and MAP 4 entries for K09 and K17 are the supply-chain outcomes, and GOVERN 1.1 marks the controls that exist mainly to meet a legal obligation (K08, K09, K16).
- *NIST AI 600-1.* Six of the twelve risk categories apply; the other six (such as CBRN information, obscene content and environmental impacts) do not for a banking assistant and are deliberately absent.
- *ISO/IEC 42001.* The controls cluster in A.6.2 (life cycle), A.8 (information for interested parties), A.9 (use) and A.10 (third parties); A.5 (impact assessment) is not mapped to a single control because this assessment as a whole is the A.5 activity.
- *ISO/IEC 27001.* K03, K05, K07, K08, K10, K12, K16 and K18 are largely classic controls with an AI-shaped application; their 27001 references show where the Bank's existing baseline already reaches. K18 is logging (8.15), clock synchronization (8.17) and collection of evidence (5.28) applied to what a model received and did; for the later handling of the record as evidence, ISO/IEC 27037 is the reference.
- *BCRA AI guide.* Ciberseguridad carries most of the technical controls; Tercerización, Transparencia and Gobierno carry the organizational ones. Gestión de sesgos, equidad y explicabilidad has no control in this assessment because the assistant takes no credit, pricing or fraud decisions; it would need one if that changed.
