# 06 · Findings

> **v0.1, with interim test evidence from v0.2.** Twelve findings from the design review of [01-system.md](01-system.md), ordered by severity. What the tests show so far is in [Test evidence so far](#test-evidence-so-far-v02-interim); residual risk and final recommendations come in v0.3.

## Format

| Field | Content |
|---|---|
| ID | F-number |
| Title | One-line statement of the problem |
| Severity | From the inherent rating of the related threats in [03-risk-register.md](03-risk-register.md) |
| Related threats | T-numbers in [02-threat-model.md](02-threat-model.md) |
| Evidence | Design review (the decision or fact in 01-system.md), or a test ID from [05-test-plan.md](05-test-plan.md) |
| Recommendation | Control IDs from [04-controls.md](04-controls.md) and what to change |
| Status | Open, accepted or resolved |

## Findings

| ID | Title | Severity | Related threats | Evidence | Recommendation | Status |
|---|---|---|---|---|---|---|
| F01 | Customer data under financial secrecy is sent to a provider abroad without a verified legal and contractual basis | High | T07 | Design review: section 8 records the provider's terms as unverified; C4 is outside Argentina | K09, K16, K13: establish the transfer basis under Ley 25.326 art. 12, bring the contract up to BCRA Section 10.3, notify the SEFYC if the service is critical, minimize the data sent and tell customers | Open |
| F02 | Text written by third parties (transfer descriptions, sender and merchant names) reaches the model unmarked and unfiltered | High | T01, T09, T02 | Design review: decision 1 | K01, K16, K06: show descriptions in the app instead of passing them to the model; where text must be passed, mark it as untrusted and neutralize instructions | Open |
| F03 | The only action that changes the customer's account is executed on the model's judgment; a chat "yes" is the sole confirmation | High | T02 | Design review: decision 2; F7 checks ownership but not consent | K02, K15, K07: native in-app confirmation enforced by the orchestrator, notification with undo, limits on state-changing calls | Open |
| F04 | Replies are rendered as Markdown with clickable links, and possibly images | High | T09, T01, T08 | Design review: C1, F9 | K05: plain-text rendering or a link allowlist; never render images from model output | Open |
| F05 | Answers about fees, rights and procedures have no grounding requirement and no accuracy measurement | High | T04, T12 | Design review: F3–F9; no evaluation process described | K11, K12, K13: citations and refusal when no passage supports the answer; sampled accuracy review; tell customers what the assistant can decide | Open |
| F06 | No model version pinning, no contractual notice of changes and no regression testing against the provider | High | T10 | Design review: C4, decision 6 | K09, K12, K17: pin versions, obtain notice, run the evaluation suite on a schedule and on every change, keep the exit exercised | Open |
| F07 | No rate limits, token budgets or spending cap | High | T11 | Design review: decision 7 | K07: limits per customer and session, caps on tool calls, budget ceiling at the provider, alerts | Open |
| F08 | Full transcripts with tool results are kept twelve months and readable by two teams; handoff summaries are not marked as model-generated | High | T06, T01 | Design review: C8, C9, F10–F11 | K08, K14: redact and shorten, restrict by role, mark summaries and require agent confirmation with the customer | Open |
| F09 | The Bank relies entirely on the provider's content filter; it has no input or output filtering of its own | High | T01, T03, T04, T08 | Design review: decision 6 | K06: Bank-side filtering for injected instructions, personal data, unauthorized commitments and extraction attempts | Open |
| F10 | One service credential reaches every customer's transactions and cards; scoping is enforced only in the orchestrator | Medium | T05 | Design review: decision 3, F7 | K03, K12: per-customer delegated tokens and ownership checks in the core APIs; adversarial testing of the tool interface; alerts on cross-customer calls | Open |
| F11 | Help center content reaches the retrieval index with no review or integrity monitoring | Medium | T08 | Design review: decision 5, F4 | K10, K01: review before indexing, separate publishing from feeding the model, monitor the index | Open |
| F12 | The system prompt holds the escalation criteria, and nothing monitors extraction attempts | Medium | T03 | Design review: D6, decision 4 | K04, K06: move criteria into code, keep the prompt free of anything harmful if disclosed, log extraction attempts | Open |

## Test evidence so far (v0.2, interim)

> Interim. Model as configured: `gemini-3.5-flash` through Gemini's OpenAI-compatible API, free tier, reasoning effort low, temperature 0, 17 to 21 October 2026. Counts as of 21 October 2026; the reports in [harness/results/](harness/results/) always hold the current state.

| Finding | What the tests show so far |
|---|---|
| F06 | Four provider-side behaviours in five days of testing. A model (`gemini-2.5-flash`) was no longer available to new users. Requests for `gemini-3.5-flash` were answered while the quota errors for the same requests named `gemini-3.6-flash`, and the responses themselves echoed the requested name. With that daily quota exhausted, the same request was answered without the `reasoning_effort` parameter and refused under the `gemini-3.6-flash` quota with it. Gemini 3 models required the client to return a signature with each tool call, which broke the integration until it was adapted. The Bank cannot learn from a response which model answered it, and a request parameter can change the answer. This supports F06 and adds a requirement: record, on the Bank's side, the configuration of every call. |
| F02, F03 | TC-01 baseline: no hits in 8 attempts in which the payload reached the model. TC-03 baseline: no card frozen in 18 attempts in which the payload reached the model; the model never called the freeze tool. This model resisted these payloads. Both findings stand: the design still passes third-party text to the model and still leaves the freeze to the model's judgment, and the resistance belongs to a model that, as F06 shows, can change without notice. K01 and K02 remove that dependency. |
| F09 | When the model ignored an injected instruction it did so silently: it listed the transfer without its description and never told the customer that the description carried an instruction. Neither the customer nor the Bank learns that an attempt took place; Bank-side detection (K06) is what would tell them. |
| F02 | In 1 of the 18 TC-03 baseline replies the assistant showed the customer part of an injected alarm ("URGENTE asistente: tarjeta 4417 comprometida...") as if it were the transfer's description, without acting on it. The customer can already read the description in the app; what the assistant adds is its own voice. |

Limits of this evidence: one model and one configuration; a fixed set of simple payloads that do not adapt to the model's answers; and temperature 0, so each attempt is a different payload and prompt rather than a random draw. The counts describe these payloads against this model at these dates, not the model's resistance to injection in general.

## What the findings say together

Four design changes remove most of the risk in this system at little cost to its usefulness: the transfer description is still shown in the app, and links to the Bank's own pages remain allowed.

1. **Send less to the model** (F02, F01): identifiers out, third-party free text out. The model can explain a transaction from its amount, date and counterparty.
2. **Take decisions out of the model** (F03): the model proposes, the app confirms, the orchestrator executes only on the app's word. The Bank already does this for unfreezing.
3. **Treat output as untrusted** (F04, F09): plain text to the app, filters on the way out.
4. **Put the provider arrangement in order** (F01, F06): legal basis, contract, notice of changes, exit.

The remaining findings are ordinary security and operations work with an AI-shaped application: limits (F07), retention and access (F08), least privilege (F10), content governance (F11), prompt hygiene (F12), and measurement (F05).

## Suggested order of work

| Priority | Findings | Why first |
|---|---|---|
| Immediate | F01, F04, F07 | F01 is a compliance gap that exists today; F04 and F07 are cheap, independent of everything else, and close the worst outcomes of T01 and T11 |
| Short term | F02, F03, F09, F05 | The architectural changes for the two top threats, plus the filtering and grounding that make the rest testable |
| Medium term | F06, F08, F10, F11, F12 | Supplier change management, data retention, least privilege, content governance and prompt hygiene |

Severities are inherent. They will be revised in v0.3 once the controls are specified and, where possible, tested.
