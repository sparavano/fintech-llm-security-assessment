# 02 · Threat model

> **Draft.** The catalogue comes from the design review of [01-system.md](01-system.md). T01, T02 and T07 are analyzed; the rest are pending.

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
| T02 | The assistant freezes a card the customer never asked to freeze, because confirmation is decided by the model | F6–F8, decision 2 | LLM03 Excessive Agency | A2, A3, N/A |
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

Each threat follows the structure used for T01: scenario, outcomes, preconditions, assets affected, impact, detection, classification, treatment direction and open questions.

### T01 · Instructions hidden in a transfer description

**Scenario**

1. The attacker sends a low-value transfer to the victim and writes instructions for the assistant in the description field. Knowing the victim's account alias is enough, and people share their aliases routinely.
2. Within the next 30 days the victim asks the assistant about that transfer, or about anything that makes it call `get_recent_transactions`, such as a summary of the month's spending.
3. The orchestrator passes the transaction list to the model as the core API returns it, description included (decision 1). Nothing in the prompt tells the model that this text was written by a third party.
4. The model reads the description as an instruction and acts on it, in its reply or in its next tool call.

**What the attacker can obtain**

| Outcome | How it happens | Related |
|---|---|---|
| Phishing in the Bank's voice | The assistant warns the victim about a fake problem and points to a phone number or link the attacker controls. The app renders the link as clickable. | T09 |
| Card frozen without a request | The assistant calls `freeze_card` and reports that the customer confirmed. | T02 |
| Manipulated handoff | The summary written for the support agent includes requests the customer never made, such as unfreezing a card or updating contact details. | T06 |
| Exfiltration with no click | Only if the app also renders Markdown images: the reply makes the app load an attacker URL that carries account data in its parameters. | T09 |
| False information | The assistant misstates fees, charges or procedures. | T12 |

**Preconditions**

- The attacker can make a transfer, which requires an account somewhere. That leaves a trail, but the account may belong to a mule.
- The description field holds enough free text for an instruction. In this case it accepts up to 100 characters (assumption). Real limits vary by bank and payment rail. A short field makes the attack harder without ruling it out, because a harmful instruction can be brief and the attacker can send several transfers.
- The victim uses the assistant in a way that pulls their transactions while the transfer is still within the 30-day window.
- The model follows the injected text at least some of the time. Success depends on the model, the system prompt and the wording, and an attacker who targets many customers only needs it to work occasionally.

Other outsider-influenced fields reach the prompt by the same path: the sender's name on business accounts and the merchant name on card purchases, which the merchant sets up.

**Assets affected**

D2 carries the payload. D1 to D3 are exposed if exfiltration works. Also affected: the customer's access to their card, their funds through social engineering, the integrity of support handoffs (D7) and the Bank's credibility as a channel.

**Impact**

- *Customers:* fraud losses that start with a message delivered by the Bank's own assistant, and loss of access to their card.
- *Financial and legal:* reimbursement claims and consumer protection complaints (Ley 24.240). It is hard to argue that the customer was careless when the misleading message came from the Bank's own assistant.
- *Regulatory:* the cybersecurity section of the BCRA guide expects entities to consider the manipulation of data and models, input data in particular. This threat is a direct case of it.
- *Reputational:* a bank assistant that sends customers to a fraudster is the kind of incident that spreads.

**Detection**

Weak under the current design. The payload looks like ordinary transaction data, the Bank has no filter of its own (decision 6), and the provider's filter, as configured, screens for harmful content in general rather than for instructions inside tool results (assumption). The evidence would sit in the conversation store (C8), but only a review would surface it.

**Classification**

- OWASP LLM 2026: LLM01 Prompt Injection, indirect form. Its effects reach LLM03 Excessive Agency (T02), LLM10 Improper Output Handling (T09) and LLM02 Sensitive Information Disclosure.
- MITRE ATLAS: AML.T0051.001, LLM Prompt Injection: Indirect.

**Treatment direction** (see [04-controls.md](04-controls.md))

The strongest fix is architectural. The free-text description does not need to reach the model: the app can show it to the customer directly, and the model can explain a transaction from its amount, date and counterparty (K01). Filters and adversarial tests (K06, K12) help, but they are a second line of defense against an attacker who can retry as often as they like. Removing clickable links and images from replies (K05), confirming the freeze outside the model (K02) and flagging handoff summaries as model-generated (K14) close the specific outcomes listed above.

**Open questions**

- Does the app render Markdown images? If it does, exfiltration needs no click.
- What are the real length and character limits of the description field?
- Can the core API return transactions without the description?

Proposed rating: likelihood 4, impact 4, inherent risk 16 (High). See [03-risk-register.md](03-risk-register.md).

### T02 · A card is frozen without the customer asking

T01 is about what gets into the prompt. T02 is about what the model is allowed to do once something is there: `freeze_card` is the one action in the system that changes the state of an account, and the design puts the decision to execute it entirely in the model's hands.

**Why the confirmation step does not protect anything**

Decision 2 in [01-system.md](01-system.md) says the assistant asks the customer to confirm before freezing, and that a "yes" in the chat counts. Three things make that step weaker than it looks.

1. The rule lives in the system prompt. The orchestrator does not check that a confirmation happened; it executes whatever tool call the model emits, after verifying only that the card belongs to the customer (F7).
2. The model both asks the question and judges the answer. Whatever is in its context can play the part of the answer, including text that came from a transfer description (T01) or from a help center article (T08).
3. The Bank already treats the inverse action as sensitive: unfreezing requires biometric confirmation in the card settings screen. Freezing a card through a chat reply is held to a lower standard than unfreezing it, with no stated reason.

**Scenario**

Three paths lead to the same outcome.

*Through injected content (A2, via T01).* The attacker's transfer description claims that the customer has already confirmed a security freeze and asks the assistant to proceed. When the victim asks about their transactions, the model either calls `freeze_card` directly or asks for confirmation and takes the injected text, or a vague reply, as the yes. The orchestrator checks the card's owner, which is the victim, and executes the freeze. The victim finds out when a payment fails. Sent to many account aliases at once, the same description produces unrequested freezes across the customer base over the following days.

*Through retrieved content (A3, via T08).* A help center article instructs the assistant to freeze a card whenever a customer mentions a charge they do not recognize, "to protect the customer". The model, grounded on that passage, acts without being asked.

*Without an attacker.* The model mistakes an ordinary reply for a confirmation. Short Spanish affirmatives are ambiguous ("dale", "ok", "sí, pero antes explicame ese cargo"), and a freeze proposed two turns earlier can be matched to a "sí" that answered something else. At the Bank's volume this will happen occasionally.

**What can happen**

| Outcome | How | Related |
|---|---|---|
| Card unusable at the worst moment | The customer learns of the freeze when a payment is declined, at a shop, abroad or at night. | |
| Credible phishing pretext | Combined with T01, the declined payment confirms the fraud message: "your card was frozen for security, call this number to reactivate it". The freeze is what makes the lie work. | T01 |
| Mass freeze incident | One description sent to many aliases; support is flooded and the story spreads. | |
| No usable record of consent | The Bank's evidence that the customer agreed is the model's own reading of a chat. In a dispute it has nothing stronger. | T06 |

**Preconditions**

- Something puts an instruction or an ambiguous confirmation in front of the model: injected content, poisoned content or ordinary conversation.
- The orchestrator executes `freeze_card` on the model's call alone (decision 2).
- The card belongs to the customer. If scoping fails, that is T05, not this threat.
- The customer gets no immediate signal. [01-system.md](01-system.md) does not mention any notification when the assistant freezes a card, so this analysis assumes there is none.

**Assets affected**

The customer's access to their card and, through the pretext, their funds. Card status (D3). The integrity of the consent record in the conversation store (C8). The Bank's obligations toward users of financial services.

**Impact**

- *Customers:* declined payments and a card out of service until they notice and unfreeze it in the app; in the T01 combination, a fraud that the Bank's own system helped make believable.
- *Financial and legal:* support load, claims for failed payments and their consequences, and consumer complaints (Ley 24.240). In a dispute the Bank must produce the evidence it holds (art. 53), and here that evidence is a model's interpretation of a chat.
- *Regulatory:* the BCRA guide expects human-in-the-loop or human-on-the-loop oversight and audit logs for AI, and expects customers to be able to challenge automated decisions. A freeze executed on the model's judgment alone sits poorly with both.
- *Reputational:* "the bank's AI blocked my card" is an easy headline, and a mass event makes it a certain one.

Scored on the worst reasonable scenario, the attacker-driven one. The no-attacker path is more frequent but minor per case; the same controls cover it.

**Detection**

Partial. The freeze is logged in core banking and the conversation is stored, but nothing records whether the customer actually asked, and the catalogue assumes core banking does not record which channel changed the card's status (open question). Spikes in freezes through the assistant, or freezes shortly after a transfer from the same sender, could be detected if someone looked. Individual cases surface through complaints.

**Classification**

- OWASP LLM 2026: LLM03 Excessive Agency, in its autonomy form: a state-changing action executed without a check outside the model. The entry paths are LLM01 (T01) and LLM05/LLM09 (T08).
- MITRE ATLAS: AML.T0053, AI Agent Tool Invocation, reached through AML.T0051.001 in the injected-content path.

**Treatment direction** (see [04-controls.md](04-controls.md))

The fix is to take the decision out of the model. The model may propose a freeze; the app confirms it with a native dialog that names the action and the card; the orchestrator executes only when it receives the app's confirmation, never on the model's word (K02). This is the pattern the Bank already uses for unfreezing, so it removes an inconsistency rather than adding a new mechanism. A push notification with a one-tap undo (K15) turns a silent freeze into a visible one and defuses the phishing pretext, because the Bank's own message tells the customer how to unfreeze in the app. Limits on state-changing actions per customer (K07) and monitoring of freeze patterns (K12) bound the mass scenario. K01 shrinks the injected-content path at its source.

**Open questions**

- Is the customer notified, by any channel, when the assistant freezes a card?
- Does core banking record which channel changed a card's status?
- If the customer has more than one card, how does the model choose, and can it freeze all of them in one call?
- What does the system prompt say about confirmation, and has it been tested against short Spanish affirmatives and negations?

Proposed rating: likelihood 4, impact 4, inherent risk 16 (High). See [03-risk-register.md](03-risk-register.md).

### T07 · Data under financial secrecy is processed by a provider abroad under unverified terms

Nothing is attacked in this threat. With every request (F5) the Bank sends a third party outside Argentina the customer's identity (D1), thirty days of account movements with counterparties and free-text descriptions (D2), card references (D3), everything the customer typed (D4) and its own internal instructions (D6). The exposure is structural: it exists as long as the arrangement does, and it depends on what the provider does with the data and on which law reaches it.

The legal reading below is the author's, for the purposes of this case study. It is not legal advice (see the README).

**What the arrangement looks like**

[01-system.md](01-system.md) records three facts and one assumption: the model runs in the provider's cloud region outside Argentina (C4); the Bank adds no filtering or minimization of its own before sending (decisions 1 and 6); the Bank has not verified the provider's terms, and only assumes the provider does not train on API data (section 8). This analysis takes the most common case, a provider headquartered in the United States and processing in a United States region, and notes where a different region would change the answer.

Typical API terms of large providers, to be checked against the actual contract: inputs and outputs retained for a limited period, often around thirty days, for abuse monitoring; flagged content reviewed by the provider's staff; no training on API data by default; subprocessors; zero-retention options for some customers on request.

**Scenario**

Four paths lead to exposure, and a fifth to dependency.

*Routine review.* A conversation is flagged by the provider's abuse monitoring, which is plausible when customers discuss fraud, blocked cards or disputed charges, and an employee of the provider, outside Argentina and outside the Bank's control, reads a customer's name, movements and messages.

*Legal process abroad.* Under the United States CLOUD Act, United States authorities can compel a provider established there to produce data in its possession wherever it is stored. The Bank may learn of it afterwards or not at all.

*Provider incident.* A bug or breach on the provider's side exposes retained prompts: every assistant conversation of the retention window, with account movements, for every customer who used the assistant in that period.

*Use beyond the purpose.* If training on API data is not excluded in writing, customer data can end up in a model and, through memorization, in answers to other users.

*Dependency.* The provider changes its model, terms, prices or availability (see T10). Without a tested exit, the Bank either accepts the change or loses the assistant.

**Preconditions**

- Data crosses TB2 unminimized: names, identifiers and free text go to the provider although the model does not need them to explain a transaction.
- The provider's region is in a country the AAIP does not list as providing adequate protection. The list covers the EU and EEA, the United Kingdom, Switzerland, Guernsey, Jersey, the Isle of Man, the Faroe Islands, Canada (private sector), Andorra, New Zealand, Uruguay and Israel (automated data). The United States is not on it.
- The contract has not been reviewed for retention, human review, training, subprocessors, audit rights, law-enforcement requests, breach notification and exit assistance.
- The compliance steps described under *Impact* have not been taken, which is the state [01-system.md](01-system.md) describes.

**Assets affected**

D1, D2, D3, D4 and D6 on every request; D7 is generated at the provider. The Bank's duty of financial secrecy and its obligations as data controller. The assistant's availability, in the dependency path.

**Impact**

- *Financial secrecy.* Ley 21.526, art. 39, bars the Bank from revealing the passive operations it carries out; movements on a savings or checking account are passive operations, and the article's closing paragraph binds the Bank's staff to absolute reserve. Outsourcing is not prohibited: the BCRA's minimum requirements on technology and information security risk allow outsourcing in the country or abroad, under conditions. The duty is stretched where the provider's staff can read the data and where a foreign authority can compel it, so the contract must bind the provider and its people to the same reserve, and the data sent must be the minimum.
- *Personal data.* Ley 25.326, art. 12, prohibits transfers to countries without adequate protection unless an exception applies. The exception for banking transfers concerns the data needed to carry out the transactions themselves; in the author's reading it is not a basis for sending customer conversations to a service provider. The available bases are the data subject's express consent or contractual clauses: the model clauses of Disposición DNPDP 60-E/2016 (Annex II, service provision), which require purpose limitation, confidentiality, security, no subprocessing without written consent, audit access, notice of law-enforcement requests and return or destruction of the data, or the model clauses adopted by Resolución AAIP 198/2023. A contract that departs from the models must be submitted to the AAIP within thirty calendar days of signing. Arts. 4, 6, 9, 10 and 25 of the law also apply: data must be pertinent and not excessive, customers must be told the purpose and the recipients, the processor must apply security measures, keep confidentiality and use the data only for the contracted service.
- *BCRA requirements.* Section 10 of the minimum requirements (texto ordenado al 13/02/2026, Comunicación "A" 8401) governs relationships with third parties: prior notice to the SEFYC at least sixty calendar days before outsourcing critical services, with locations and subcontractors; a change of location or subcontractor counts as a new outsourcing; contracts with minimum terms including audit rights, service levels and data deletion; monitoring, internal audits and exit plans that cover the retrieval of data; the entity bears the cost of SEFYC inspections abroad, and a foreign provider must be constituted in a country with AML/CFT standards. Section 4.6 requires AI software used by third parties to be documented and risk-assessed. The BCRA AI guide adds, under outsourcing, pre-contract risk assessment, sufficient information about the models, assessment of criticality and concentration, portability and exit strategies, and continuous monitoring, with the entity keeping responsibility; under transparency, customers must be told when they interact with AI.
- *Sanctions and liability.* The AAIP can sanction under Ley 25.326, art. 31, and the BCRA under Ley 21.526, art. 41, from a warning to fines and disqualifications. A breach of financial secrecy exposes the Bank to civil claims by the customers affected.
- *Customers.* Exposed account movements enable targeted fraud and extortion and reveal patterns of life; the harm does not depend on whether the Bank was at fault.
- *Reputational.* "Bank sent customers' movements to a foreign AI company" is a story that needs no breach to run.

**Detection**

Weak. The Bank cannot observe what happens inside the provider. It relies on the contract, on the provider's certifications (which attest to the provider's controls, not to compliance with Argentine law), on breach notifications and on audit rights that large providers rarely grant beyond reports.

**Classification**

- OWASP LLM 2026: LLM02 Sensitive Information Disclosure, because customer data leaves the Bank's control and can resurface through retention, review or training; LLM04 Supply Chain, because the assistant depends on a third-party model and its terms.
- MITRE ATLAS: no matching technique. This is a supplier and compliance exposure, not an adversary technique.

**Treatment direction** (see [04-controls.md](04-controls.md))

Two things shrink the exposure at its source. First, send less (K16): the model needs amounts, dates and counterparties to explain a transaction, not the customer's name or identifier, and not the free text that T01 shows to be dangerous anyway. Second, put the arrangement in order before it runs (K09): a transfer basis under art. 12, a contract that meets Section 10.3 and mirrors the art. 39 duty of reserve, zero or shortest retention, no human review or review only under confidentiality by named staff, no training, subprocessor consent, notice of law-enforcement requests, breach notification, audit rights and exit assistance; the SEFYC notice if the service is critical; documentation under 4.6. A region in an adequate territory, such as the EU, would settle the art. 12 question but not foreign legal process, which follows the provider's home jurisdiction. An exit strategy with a tested alternative (K17) addresses the dependency path, and telling customers what happens to their conversation (K13) addresses art. 6 and the BCRA's transparency expectation. Hosting an open-weight model in the country would remove TB2 altogether; it trades the exposure for capability, cost and operational burden, and deserves its own evaluation.

**Open questions**

- Which country hosts the processing region, and does the provider offer one in a territory the AAIP lists as adequate?
- What do the contract and the provider's policies say about retention, human review, training, subprocessors, law-enforcement requests, breach notification, audit rights and exit assistance?
- Which transfer basis is in place, and if a non-model contract was used, was it submitted to the AAIP in time?
- Is the assistant a critical service under the Bank's own criteria, and was the SEFYC notified sixty days in advance?
- Does the privacy notice tell customers that a third-party provider abroad processes their conversations?

Proposed rating: likelihood 3, impact 5, inherent risk 15 (High). The compliance gap is recorded separately as finding F01 in [06-findings.md](06-findings.md). See [03-risk-register.md](03-risk-register.md).

T03 to T06 and T08 to T12: pending.
