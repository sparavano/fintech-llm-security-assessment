# 03 · Risk register

> **v0.1.** All twelve threats scored on the system as designed. Residual scores follow in v0.3, after the controls in [04-controls.md](04-controls.md) are detailed and, where possible, tested.

## Scoring method

**Likelihood (1–5)** reflects how easily the threat can be realized against the system as designed in [01-system.md](01-system.md): the capability the attacker needs, how exposed the entry point is and which controls already exist.

| Score | Label | Guide |
|---|---|---|
| 1 | Rare | Needs insider access and specialist skill, and existing controls would likely stop it. |
| 2 | Unlikely | Needs specialist skill or a rare combination of conditions. |
| 3 | Possible | Feasible for a motivated attacker with public techniques. |
| 4 | Likely | Feasible for any customer or sender with moderate effort. |
| 5 | Almost certain | Trivial to attempt at scale, or will happen without any attacker. |

**Impact (1–5)** is the highest score across four dimensions: harm to customers, financial loss, regulatory or legal exposure, and reputation.

| Score | Label | Guide |
|---|---|---|
| 1 | Minimal | Inconvenience to one customer, no data exposed. |
| 2 | Minor | Limited harm to few customers, quickly reversible. |
| 3 | Moderate | Personal data of a customer exposed, or service disrupted for many. |
| 4 | Major | Personal data under financial secrecy exposed for many customers, or actions taken on accounts without consent. |
| 5 | Severe | Large-scale exposure or harm, likely regulatory action. |

**Rating** = Likelihood × Impact: 1–4 Low, 5–9 Medium, 10–16 High, 20–25 Critical.

*Inherent* risk is scored on the system as designed. *Residual* risk is scored after the controls proposed in [04-controls.md](04-controls.md).

## Register

| ID | Threat (short) | L | I | Inherent | Treatment | Controls | L | I | Residual |
|---|---|---|---|---|---|---|---|---|---|
| T01 | Injection via transfer description | 4 | 4 | 16 High | Mitigate | K01, K02, K05, K06, K12, K14 | | | |
| T02 | Unrequested card freeze | 4 | 4 | 16 High | Mitigate | K01, K02, K07, K12, K15 | | | |
| T03 | Hidden context extraction | 4 | 2 | 8 Medium | Mitigate | K04, K06, K12 | | | |
| T04 | Out-of-policy commitments | 4 | 3 | 12 High | Mitigate | K06, K11, K12, K13 | | | |
| T05 | Cross-customer scoping failure | 2 | 4 | 8 Medium | Mitigate | K03, K12 | | | |
| T06 | Transcript and handoff over-retention | 3 | 4 | 12 High | Mitigate | K08, K14, K16 | | | |
| T07 | Cross-border processing by provider | 3 | 5 | 15 High | Mitigate | K09, K13, K16, K17 | | | |
| T08 | Poisoned help center content | 2 | 4 | 8 Medium | Mitigate | K01, K05, K06, K10 | | | |
| T09 | Malicious links in rendered replies | 3 | 4 | 12 High | Mitigate | K05 | | | |
| T10 | Unannounced provider changes | 4 | 3 | 12 High | Mitigate | K09, K12, K17 | | | |
| T11 | Unbounded consumption | 4 | 3 | 12 High | Mitigate | K07 | | | |
| T12 | Misinformation taken as the Bank's word | 4 | 3 | 12 High | Mitigate | K11, K12, K13 | | | |

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

Three observations fall out of the ranking. The top two share a root cause, untrusted text reaching a model that can act, and share their main control (K02 plus K01). T07 is the only High that is not an attack: it is a compliance and supplier exposure that exists from day one. The six threats tied at 12 are all cheap to reduce: K05 (plain-text rendering) alone removes most of T09, K07 removes most of T11, and K11 with K12 addresses T04, T10 and T12 together.

## Rationale

### T01

- **Likelihood 4 (Likely).** Anyone who can send a transfer can attempt it, the techniques are public and nothing in the design separates third-party text from instructions. It is not a 5 because success depends on how the model behaves and on the victim asking about their transactions within 30 days.
- **Impact 4 (Major).** Social engineering in the Bank's own voice, card lockouts and manipulated handoffs, repeatable across many customers. It is not a 5 because the assistant cannot move money by itself, so losses require the victim to act on the message.

### T02

Scored on the worst reasonable scenario, the attacker-driven path through T01. The no-attacker path (a misread confirmation) is more frequent but minor per case, and the same controls cover it.

- **Likelihood 4 (Likely).** Any sender can attempt it through T01, and nothing in the design stands between the model's decision and the freeze: the confirmation rule exists only in the system prompt. It is slightly less likely than T01 because the model must act, not just reply, but that does not change the level. It is not a 5 because the attacker-driven path still depends on the model following the injected text.
- **Impact 4 (Major).** An action on the account without the customer's consent, repeatable at scale, and the piece that makes the T01 fraud believable. It is not a 5 because the freeze is reversible by the customer in the app and cannot move funds. It is not a 3 because the impact scale places actions taken on accounts without consent at level 4, and a mass event disrupts service for many customers at once.

### T07

Scored on the worst reasonable scenario, a provider-side incident that exposes the retained conversations. The likelihood scale is read as frequency here, since no attacker is involved.

- **Likelihood 3 (Possible).** An exposure event needs something to happen on the provider's side: an incident, a legal demand or use of the data beyond the contract. Routine review of flagged conversations by the provider's staff is more likely than that, and the compliance gap exists from day one, but a probability score is the wrong tool for a non-compliance that is present by design. The gap is recorded as finding F01 in [06-findings.md](06-findings.md).
- **Impact 5 (Severe).** Every assistant conversation of the retention window, with account movements, for every customer who used it, exposed at once; sanctions from the AAIP and the BCRA would follow. The scale defines level 5 as large-scale exposure with likely regulatory action, and this is that case.

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

- **Likelihood 3 (Possible).** It needs a path into the prompt (T01, T08) or a cooperative model (T04); given T01's rating, the path exists.
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
