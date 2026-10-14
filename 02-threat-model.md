# 02 · Threat model

> **Draft.** The catalogue comes from the design review of [01-system.md](01-system.md). Detailed analysis and MITRE ATLAS mapping are pending.

## Method

Threats are identified per component (C1–C10), data flow (F1–F11) and trust boundary (TB1–TB4), and classified against the OWASP Top 10 for LLM Applications 2026. MITRE ATLAS techniques are added only where a matching technique exists, checked against atlas.mitre.org at the time of mapping.

### Attacker profiles

| ID | Profile | Capability |
|---|---|---|
| A1 | Malicious customer | Holds a valid account and fully controls their own chat. |
| A2 | External sender | Can send a low-value transfer to any customer and choose its description. |
| A3 | Content insider | Can publish or edit a help center article in the CMS, or controls an account that can. |
| A4 | Automated abuser | Drives scripted traffic through one or many accounts to exhaust capacity or run up cost. |
| N/A | No attacker | Failures of the system itself, such as wrong answers or unannounced provider changes. |

## Threat catalogue

| ID | Threat | Where | OWASP LLM 2026 | Source |
|---|---|---|---|---|
| T01 | Instructions hidden in a transfer description steer the assistant when the victim asks about their transactions | D2, F8 → F5 | LLM01 Prompt Injection | A2 |
| T02 | The assistant freezes a card the customer never asked to freeze, because confirmation is decided by the model | F6–F8, decision 2 | LLM03 Excessive Agency | A2, A1 |
| T03 | A customer extracts the system prompt, tool definitions and escalation criteria | D6, F5–F6 | LLM08 Hidden Context Exposure | A1 |
| T04 | A customer talks the assistant into commitments outside policy, such as promising a refund or waiving a fee | F1–F9 | LLM01 Prompt Injection, LLM07 Misinformation | A1 |
| T05 | A flaw in orchestrator scoping exposes another customer's data or lets a call act on another customer's card | F7–F8, decision 3 | LLM02 Sensitive Information Disclosure, LLM03 Excessive Agency | A1 |
| T06 | Full transcripts with tool results are kept for 12 months and readable by two teams, and handoff summaries copy personal data into ticketing | C8, C9, F10–F11 | LLM02 Sensitive Information Disclosure | Insider misuse, breach |
| T07 | Personal data under financial secrecy is processed by a provider outside Argentina under terms not yet verified | TB2, F5 | LLM02 Sensitive Information Disclosure, LLM04 Supply Chain | Third party |
| T08 | A poisoned help center article changes answers or carries instructions for the model | C10 → C5, F4, decision 5 | LLM05 Data and Model Poisoning, LLM09 Vector and Embedding Weaknesses, LLM01 Prompt Injection | A3 |
| T09 | Replies rendered as Markdown carry phishing links or misleading formatting | C1, F9 | LLM10 Improper Output Handling | A2, A3 |
| T10 | The provider changes the model or its filter and the assistant's behavior shifts without the Bank noticing | C4, decision 6 | LLM04 Supply Chain | N/A |
| T11 | Unlimited messages and tokens allow capacity exhaustion and cost abuse | C3, C4, decision 7 | LLM06 Unbounded Consumption | A4 |
| T12 | Wrong answers about fees, rights or procedures are taken as the Bank's word | C5, F3–F9 | LLM07 Misinformation | N/A |

## Detailed analysis

Each threat will be written up with this structure.

```text
Scenario:        step-by-step attack or failure path
Preconditions:   what must be true for it to work
Assets affected: D1–D7, customer funds or access, Bank obligations
Impact:          customer harm, financial, regulatory, reputational
OWASP LLM 2026:  category
MITRE ATLAS:     technique ID, if one matches
Notes:           assumptions and open questions
```

T01 to T12: pending.
