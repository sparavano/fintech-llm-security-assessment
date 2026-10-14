# 03 · Risk register

> **Draft.** Scoring method defined. Scores pending.

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
| T01 | Injection via transfer description | | | | | | | | |
| T02 | Unrequested card freeze | | | | | | | | |
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
