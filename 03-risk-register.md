# 03 · Risk register

> **v0.3.** All twelve threats scored on the system as designed (v0.1) and, from 29 October 2026, after the controls in [04-controls.md](04-controls.md). Residual scores assume each control is implemented as specified there; where the v0.2 tests bear on a score, the rationale says so. Three residual scores hold only under a condition, listed in [Residual ranking](#residual-ranking).

## Scoring method

**Likelihood (1–5)** reflects how easily the threat can be realized against the system as designed in [01-system.md](01-system.md): the capability the attacker needs, how exposed the entry point is and which controls already exist. For threats without an attacker, it reflects how often the event is expected over a one-year horizon.

| Score | Label | Guide |
|---|---|---|
| 1 | Rare | Needs insider access and specialist skill, and existing controls would likely stop it. Without an attacker: not expected within the horizon. |
| 2 | Unlikely | Needs specialist skill or a rare combination of conditions. Without an attacker: could occur, but is not expected. |
| 3 | Possible | Feasible for a motivated attacker with public techniques. Without an attacker: may well occur within the horizon. |
| 4 | Likely | Feasible for any customer or sender with moderate effort. Without an attacker: expected to occur within the horizon. |
| 5 | Almost certain | Trivial to attempt at scale and reliably successful. Without an attacker: occurs routinely. |

**Impact (1–5)** is the highest score across four dimensions: harm to customers, financial loss, regulatory or legal exposure, and reputation.

| Score | Label | Guide |
|---|---|---|
| 1 | Minimal | Inconvenience to one customer; no data exposed; no financial, legal or reputational effect. |
| 2 | Minor | Limited harm to few customers, quickly reversible; costs the Bank absorbs; no regulatory interest. |
| 3 | Moderate | Personal data of a customer exposed, or service disrupted for many; disputes and losses limited to individual cases; a regulatory finding without sanction; contained reputational damage. |
| 4 | Major | Personal data under financial secrecy exposed for many customers, or actions taken on accounts without consent; sanctions likely; sustained reputational damage. |
| 5 | Severe | Large-scale exposure or harm; regulatory action likely; lasting reputational damage. |

**Rating** = Likelihood × Impact: 1–4 Low, 5–9 Medium, 10–16 High, above 16 Critical.

*Inherent* risk is scored on the system as designed. *Residual* risk is scored after the controls proposed in [04-controls.md](04-controls.md).

## Register

| ID | Threat (short) | L | I | Inherent | Treatment | Controls | L | I | Residual |
|---|---|---|---|---|---|---|---|---|---|
| T01 | Injection via transfer description | 4 | 4 | 16 High | Mitigate | K01, K02, K05, K06, K12, K14, K16 | 2 | 3 | 6 Medium |
| T02 | Unrequested card freeze | 4 | 4 | 16 High | Mitigate | K01, K02, K07, K12, K15 | 2 | 2 | 4 Low |
| T03 | Hidden context extraction | 4 | 2 | 8 Medium | Mitigate | K04, K06, K12 | 4 | 1 | 4 Low |
| T04 | Out-of-policy commitments | 4 | 3 | 12 High | Mitigate | K06, K11, K12 | 3 | 3 | 9 Medium |
| T05 | Cross-customer scoping failure | 2 | 4 | 8 Medium | Mitigate | K03, K12 | 1 | 4 | 4 Low |
| T06 | Transcript and handoff over-retention | 3 | 4 | 12 High | Mitigate | K08, K14 | 2 | 3 | 6 Medium |
| T07 | Cross-border processing by provider | 3 | 5 | 15 High | Mitigate | K09, K13, K16, K17 | 2 | 4 | 8 Medium |
| T08 | Poisoned help center content | 2 | 4 | 8 Medium | Mitigate | K01, K05, K06, K10 | 1 | 3 | 3 Low |
| T09 | Malicious links in rendered replies | 3 | 4 | 12 High | Mitigate | K05 | 1 | 2 | 2 Low |
| T10 | Unannounced provider changes | 4 | 3 | 12 High | Mitigate | K09, K12, K17 | 3 | 2 | 6 Medium |
| T11 | Unbounded consumption | 4 | 3 | 12 High | Mitigate | K07 | 2 | 2 | 4 Low |
| T12 | Misinformation taken as the Bank's word | 4 | 3 | 12 High | Mitigate | K11, K12, K13 | 3 | 2 | 6 Medium |

Scores are qualitative judgments about a fictional system. Their value lies in the reasoning recorded for each one.

## Ranking

| Rank | ID | Threat (short) | Inherent | What drives it |
|---|---|---|---|---|
| 1 | T01 | Injection via transfer description | 16 High | Third-party text enters the prompt unmarked; any sender can try |
| 1 | T02 | Unrequested card freeze | 16 High | The only state-changing action is executed on the model's judgment |
| 3 | T07 | Cross-border processing by provider | 15 High | Financial-secrecy data leaves the country under unverified terms |
| 4 | T04 | Out-of-policy commitments | 12 High | No grounding requirement; the Bank owns what the assistant says |
| 4 | T06 | Transcript and handoff over-retention | 12 High | Twelve months of full transcripts, readable by two teams |
| 4 | T09 | Malicious links in rendered replies | 12 High | Model output rendered as Markdown with links |
| 4 | T10 | Unannounced provider changes | 12 High | No version pinning, no change notice, no regression tests |
| 4 | T11 | Unbounded consumption | 12 High | No rate limits or budgets |
| 4 | T12 | Misinformation taken as the Bank's word | 12 High | No grounding, no accuracy measurement |
| 10 | T03 | Hidden context extraction | 8 Medium | Easy to do, little to gain while the prompt holds no secrets |
| 10 | T05 | Cross-customer scoping failure | 8 Medium | Needs a flaw in one check; severe if found |
| 10 | T08 | Poisoned help center content | 8 Medium | Needs CMS access; wide reach once in |

The ranking says a few things on its own. The top two share a root cause, untrusted text reaching a model that can act, and share their main control (K02 plus K01). Three Highs need no attacker, T07, T10 and T12, and T07 is the only one that is a compliance exposure present from day one. Of the six threats tied at 12, five are cheap to reduce: K05 (plain-text rendering) alone removes most of T09, K07 most of T11, K11 with K12 addresses T04 and T12, and K12 with version pinning and change notice (K09) addresses T10. T06 is the exception: retention and access need process changes, not a switch.

## Rationale

### T01

- **Likelihood 4 (Likely).** Anyone who can send a transfer can attempt it, the techniques are public and nothing in the design separates third-party text from instructions. It is not a 5 because success depends on how the model behaves and on the victim asking about their transactions within 30 days.
- **Impact 4 (Major).** Social engineering in the Bank's own voice, card lockouts and manipulated handoffs, repeatable across many customers. It is not a 5 because the assistant cannot move money by itself, so losses require the victim to act on the message.

### T02

Scored on the worst reasonable scenario, the attacker-driven path through T01. The no-attacker path (a misread confirmation) is more frequent but minor per case, and the same controls cover it.

- **Likelihood 4 (Likely).** Any sender can attempt it through T01, and nothing in the design stands between the model's decision and the freeze: the confirmation rule exists only in the system prompt. It is slightly less likely than T01 because the model must act, not just reply, but that does not change the level. It is not a 5 because the attacker-driven path still depends on the model following the injected text.
- **Impact 4 (Major).** An action on the account without the customer's consent, repeatable at scale, and the piece that makes the T01 fraud believable. It is not a 5 because the freeze is reversible by the customer in the app and cannot move funds. It is not a 3 because the impact scale places actions taken on accounts without consent at level 4, and a mass event disrupts service for many customers at once.

### T07

Scored on the worst reasonable scenario, a provider-side incident that exposes the retained conversations. Likelihood is read on the no-attacker side of the scale.

- **Likelihood 3 (Possible).** An exposure event needs something to happen on the provider's side: an incident, a legal demand or use of the data beyond the contract. Routine review of flagged conversations by the provider's staff is more likely than that, and the compliance gap exists from day one, but a probability score is the wrong tool for a non-compliance that is present by design. The gap is recorded as finding F01 in [06-findings.md](06-findings.md).
- **Impact 5 (Severe).** Every assistant conversation of the retention window, with account movements, for every customer who used it, exposed at once; sanctions from the AAIP and the BCRA would be likely. The scale defines level 5 as large-scale exposure with likely regulatory action, and this is that case.

### T03

- **Likelihood 4 (Likely).** Any customer can try, the techniques are public and nothing filters the output.
- **Impact 2 (Minor).** The prompt is designed as rules, not secrets; the gain is indirect (tuning T01 and T04). It would rise to 3 or more if secrets were ever placed in the prompt, which is what K04 prevents.

### T04

- **Likelihood 4 (Likely).** Any customer can push, models yield under persistence, and there is no grounding requirement.
- **Impact 3 (Moderate).** Case-by-case disputes and reputational cost; no tool can act on the promise, so losses need the Bank to honor or litigate each case. Shared techniques could scale it, which K12 is meant to catch early.

### T05

- **Likelihood 2 (Unlikely).** It needs a flaw in the orchestrator's scoping; the overwrite of the customer ID from the session is the right design, and the check on card ownership is explicit. It is not a 1 because the single credential makes any flaw exploitable at once, and the model gives attackers a tireless way to search for one.
- **Impact 4 (Major).** Other customers' movements disclosed or their cards acted on, across the customer base, because one credential reaches everyone.

### T06

- **Likelihood 3 (Possible).** No attacker is needed for the accumulation; turning it into harm needs an insider, a compromised account or a breach, which are not everyday events but happen.
- **Impact 4 (Major).** A year of full transcripts with movements for every customer who used the assistant, readable by two teams. It is not a 5 because the store sits inside the Bank's own controls, unlike the provider copy in T07.

### T08

- **Likelihood 2 (Unlikely).** It needs write access to the CMS, which limits the attacker set to the content team, their contractors and whoever compromises one of their accounts.
- **Impact 4 (Major).** One article can reach every customer who asks a common question, with the Bank's citation lending authority; in the active variant it carries everything T01 carries.

### T09

- **Likelihood 3 (Possible).** It needs a path into the prompt (T01, T08) or a cooperative model (T04); given T01's rating, the path exists. It is rated below T01 because the injection must both succeed and aim at the reply format, a narrower outcome.
- **Impact 4 (Major).** Phishing inside the Bank's own app, or exfiltration of thirty days of movements with no click. Scored separately from T01 because K05 closes it independently of whether injection is solved.

### T10

- **Likelihood 4 (Likely).** Hosted models change on the provider's schedule; without pinning and notice, a behavior shift is a matter of time.
- **Impact 3 (Moderate).** Most changes are small; the loss of a safety property is the case that matters, and it is caught late without K12.

### T11

- **Likelihood 4 (Likely).** Any logged-in customer can script the endpoint, and there are no limits.
- **Impact 3 (Moderate).** Cost and an unavailable assistant; the Bank has other channels and the core platform is out of scope except at the interface.

### T12

- **Likelihood 4 (Likely).** Confabulation and stale content are ordinary failure modes, not edge cases, and nothing measures accuracy.
- **Impact 3 (Moderate).** Harm is per customer and per question, but the same wrong answer repeats until found; the conduct dimension (Ley 24.240, art. 4) keeps it from being minor.

## Residual ranking

| Rank | ID | Threat (short) | Inherent | Residual | Condition the residual depends on | Basis |
|---|---|---|---|---|---|---|
| 1 | T04 | Out-of-policy commitments | 12 High | 9 Medium | | Design judgment |
| 2 | T07 | Cross-border processing by provider | 15 High | 8 Medium | K09 in force: until the contract and the transfer basis exist, the inherent score stands and F01 is a present gap | Design judgment |
| 3 | T01 | Injection via transfer description | 16 High | 6 Medium | K01 in its first form, descriptions kept out of the prompt; with marking only, the residual stays at the inherent level | v0.2 tests (TC-01, TC-01b, TC-01r) |
| 3 | T06 | Transcript and handoff over-retention | 12 High | 6 Medium | | Design judgment |
| 3 | T10 | Unannounced provider changes | 12 High | 6 Medium | K12 samples each test several times and records the configuration of every call | v0.2 observations (F06) |
| 3 | T12 | Misinformation taken as the Bank's word | 12 High | 6 Medium | | Design judgment |
| 7 | T02 | Unrequested card freeze | 16 High | 4 Low | | v0.2 test of K02 against a scripted model (TC-03) |
| 7 | T03 | Hidden context extraction | 8 Medium | 4 Low | | Design judgment |
| 7 | T05 | Cross-customer scoping failure | 8 Medium | 4 Low | | Design judgment; TC-07 not run |
| 7 | T11 | Unbounded consumption | 12 High | 4 Low | | Design judgment |
| 11 | T08 | Poisoned help center content | 8 Medium | 3 Low | | Design judgment |
| 12 | T09 | Malicious links in rendered replies | 12 High | 2 Low | | Design judgment |

With the controls in place no threat stays High, and the two that led the inherent ranking fall furthest. Both falls rest on controls that take the decision away from the model rather than asking the model to behave: K02 executes the freeze only on the app's confirmation, and K01 in its first form keeps the attacker's text out of the prompt. The v0.2 tests are the reason for the condition on T01: marking the description as untrusted, the second form of K01, did not stop the model from passing the attacker's message to the customer (06-findings), so a Bank that implements only the marking keeps T01 at 16. What remains at the top is what no switch removes: commitments and misinformation, which need grounding and measurement that never reach zero, and the provider arrangement, whose residual depends on a contract.

## Residual rationale

### T01

- **Likelihood 2 (Unlikely).** With transfer descriptions shown by the app and not passed to the model (K01, first form) and the remaining third-party fields reduced to what the model needs (K16), the attacker's main channel into the prompt is closed. Counterparty names still reach the model; they are short and can be truncated, which is why the score is not 1. The v0.2 tests show why the first form is required: across 100 attempts, with the description marked as untrusted or not, the model passed the attacker's message, phone number included, to the customer four times, and repeating the same request gave a different reply each time (TC-01r). That behaviour is the model's, undocumented and unstable, and the Bank cannot rely on it.
- **Impact 3 (Moderate).** With K05 there is no link or image, with K02 the freeze needs the customer's confirmation in the app, and with K14 an injected request in a handoff is visible as model-generated. What is left is a short text in a counterparty name reaching an individual customer.

### T02

- **Likelihood 2 (Unlikely).** With K02 the orchestrator executes a freeze only when the app's native dialog, which names the card, is confirmed. Against a scripted model that attempts every freeze an injection asks for, the baseline froze the card in 20 of 20 attempts and the control in none (TC-03). The remaining path is a customer talked into confirming the dialog, which takes social engineering outside the model; it is not 1 because T01's residual can supply that pretext.
- **Impact 2 (Minor).** The action now has the customer's own confirmation, K15 notifies them through a separate channel with the way to undo it, and K07 limits repetition.

### T03

- **Likelihood 4 (Likely).** Extraction stays as easy as before; nothing here prevents it, and K06 only detects attempts.
- **Impact 1 (Minimal).** With K04 the prompt holds nothing harmful if disclosed and the escalation criteria live in code.

### T04

- **Likelihood 3 (Possible).** Grounding with citations and refusal when no passage applies (K11) and Bank-side detection of commitments (K06) make it harder; a persistent customer can still find phrasings that get through, and K12 measures how often.
- **Impact 3 (Moderate).** Unchanged: the Bank still owns what the assistant says, and each case is a dispute. Not tested in v0.2 (TC-06).

### T05

- **Likelihood 1 (Rare).** With per-customer delegated tokens and ownership checked by the core APIs (K03), a flaw in the orchestrator no longer reaches other customers on its own.
- **Impact 4 (Major).** Unchanged if it happens. Not tested in v0.2 (TC-07); the score rests on the design of K03.

### T06

- **Likelihood 2 (Unlikely).** Redacted transcripts, shorter retention and access by role (K08) reduce what an insider or a breach can reach.
- **Impact 3 (Moderate).** Less data, kept for less time, readable by fewer people; still personal data under financial secrecy for the retention window.

### T07

- **Likelihood 2 (Unlikely).** A contract that binds the provider to zero or shortest retention, no training and confidentiality (K09), with notice of legal demands and audit rights, makes an exposure event less likely; it remains an event outside the Bank's control.
- **Impact 4 (Major).** Pseudonymized and minimized data (K16) lowers what an exposure reveals, but transactions are still financial data of identifiable customers. The score assumes K09 is in force; until it is, the compliance gap of F01 exists regardless of probability.

### T08

- **Likelihood 1 (Rare).** Review before indexing and separating the right to publish from the right to feed the model (K10) turn a single compromised account into an insufficient condition.
- **Impact 3 (Moderate).** With K05 the active variant has no link or image to carry; misinformation in one article still reaches many customers until found.

### T09

- **Likelihood 1 (Rare).** With plain-text rendering or a link allowlist and no images from model output (K05), there is no rendered element left to abuse.
- **Impact 2 (Minor).** A link to an allowed Bank domain in the wrong context; phishing by text, such as a phone number, is T01's residual, not this one.

### T10

- **Likelihood 3 (Possible).** Pinning and notice (K09) cannot stop the provider from changing what serves a name: in v0.2 the provider's quota errors named a different model from the one requested, and a request parameter changed which quota applied (F06). Changes will keep happening.
- **Impact 2 (Minor).** With the evaluation suite run on a schedule and on every change (K12) and an exit path (K17), a lost safety property is caught before it reaches many customers. This requires two things the v0.2 tests showed are needed: each test is run several times, because the same request gave different replies, and the configuration of every call is recorded on the Bank's side, because the response does not say which model answered.

### T11

- **Likelihood 2 (Unlikely).** Rate limits, token budgets and alerts (K07) make sustained abuse visible and bounded.
- **Impact 2 (Minor).** Cost is capped and a single account cannot exhaust the service.

### T12

- **Likelihood 3 (Possible).** Grounding with citations (K11) and sampled accuracy measurement (K12) reduce wrong answers; confabulation does not go to zero.
- **Impact 2 (Minor).** Customers are told what the assistant can decide and have a path to a human (K13), errors are found by measurement instead of by complaints, and citations let customers check. Not tested in v0.2 (TC-10).
