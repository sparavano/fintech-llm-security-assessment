# 03 · Risk register

> **Draft.** Scoring method defined. T01 and T02 scored; T03 to T12 pending.

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
| T03 | Hidden context extraction | | | | | | | | |
| T04 | Out-of-policy commitments | | | | | | | | |
| T05 | Cross-customer scoping failure | | | | | | | | |
| T06 | Transcript and handoff over-retention | | | | | | | | |
| T07 | Cross-border processing by provider | | | | | | | | |
| T08 | Poisoned help center content | | | | | | | | |
| T09 | Malicious links in rendered replies | | | | | | | | |
| T10 | Unannounced provider changes | | | | | | | | |
| T11 | Unbounded consumption | | | | | | | | |
| T12 | Misinformation taken as the Bank's word | | | | | | | | |

Scores are qualitative judgments about a fictional system. Their value lies in the reasoning recorded for each one.

## Rationale

### T01

- **Likelihood 4 (Likely).** Anyone who can send a transfer can attempt it, the techniques are public and nothing in the design separates third-party text from instructions. It is not a 5 because success depends on how the model behaves and on the victim asking about their transactions within 30 days.
- **Impact 4 (Major).** Social engineering in the Bank's own voice, card lockouts and manipulated handoffs, repeatable across many customers. It is not a 5 because the assistant cannot move money by itself, so losses require the victim to act on the message.

### T02

Scored on the worst reasonable scenario, the attacker-driven path through T01. The no-attacker path (a misread confirmation) is more frequent but minor per case, and the same controls cover it.

- **Likelihood 4 (Likely).** Any sender can attempt it through T01, and nothing in the design stands between the model's decision and the freeze: the confirmation rule exists only in the system prompt. It is slightly less likely than T01 because the model must act, not just reply, but that does not change the level. It is not a 5 because the attacker-driven path still depends on the model following the injected text.
- **Impact 4 (Major).** An action on the account without the customer's consent, repeatable at scale, and the piece that makes the T01 fraud believable. It is not a 5 because the freeze is reversible by the customer in the app and cannot move funds. It is not a 3 because the impact scale places actions taken on accounts without consent at level 4, and a mass event disrupts service for many customers at once.
