# LLM Security Assessment: Digital Bank Assistant (case study)

Security and risk assessment of a **fictional** generative AI assistant run by a **fictional** Argentine digital bank. The case walks through the full cycle an AI risk or security team would follow for an LLM-based system: characterize it, model its threats, rate the risks, map them to controls under the frameworks a regulated financial entity in Argentina would be expected to consider, and record findings.

> **Status:** v0.1 complete, based on a review of the system's design: twelve threats analyzed and rated, seventeen controls mapped, twelve findings. v0.2 (testing) in progress: the harness is published, results are added as they are produced and summarized in [06-findings.md](06-findings.md#test-evidence-so-far-v02-interim); see [Roadmap](#roadmap).

## Results in brief

| Item | Summary |
|---|---|
| System | A customer-facing assistant that answers product questions, explains the customer's last 30 days of transactions and can freeze a debit card, built on a third-party hosted model ([01-system.md](01-system.md)) |
| Threats | 12, covering the ten categories of the OWASP Top 10 for LLM Applications 2026 ([02-threat-model.md](02-threat-model.md)) |
| Highest risks | T01, instructions hidden in a transfer description, and T02, a card frozen on the model's judgment alone (16 each); T07, financial-secrecy data processed by a provider abroad under unverified terms (15) ([03-risk-register.md](03-risk-register.md)) |
| Controls | 17, mapped to NIST AI RMF 1.0, NIST AI 600-1, ISO/IEC 42001, ISO/IEC 27001 and the BCRA AI guide ([04-controls.md](04-controls.md)) |
| Findings | 12 from design review, 9 High and 3 Medium, with a suggested order of work ([06-findings.md](06-findings.md)) |
| Tests so far (v0.2, interim) | Against a hosted model (Gemini, October 2026). The model obeyed none of the orders planted in transfer descriptions, but twice showed the customer the attacker's message, phone number included, as if it were the transfer's description, once with the description marked as untrusted data (K01). A follow-up case, with its hypotheses and reading published before it ran, tested whether that happened because those messages gave the model no order: it did not (0 hits in 20 attempts). What the 85 attempts show instead is a model that leaves injected descriptions out while showing legitimate ones, silently and not always: 3 leaks in the 63 replies that listed the transfer, with the marking and without, and the same request answered five times gave five different replies, one of them a leak. The freeze control (K02) held every freeze attempted by a scripted model that stands in for a fully compromised one (20 of 20). Provider: its quota errors named a different model from the one requested, and a request parameter changed which quota applied. The findings stand ([06-findings.md](06-findings.md#test-evidence-so-far-v02-interim), [harness/results/](harness/results/)) |
| Main conclusion | Four design changes remove most of the risk at little cost to usefulness: send less to the model, take decisions out of the model, treat output as untrusted, and put the provider arrangement in order |

## Why this case

In June 2026 the Central Bank of Argentina (BCRA) published a supervision guide on the responsible and secure use of AI. It sets supervisory expectations on AI governance and risk management, data, model validation and monitoring, bias and explainability, cybersecurity, business continuity, outsourcing and transparency. A customer-facing assistant that reads account data and can act on the customer's behalf touches nearly every one of those areas, which makes it a good test bed. The case also exercises the Argentine rules that bite hardest on such a system: financial secrecy (Ley 21.526, art. 39), personal data and international transfers (Ley 25.326), consumer information duties (Ley 24.240) and the BCRA's minimum requirements on technology and information security risk.

## Scope

In scope: the assistant described in [01-system.md](01-system.md), its orchestration layer, retrieval index, tool integrations, conversation logging and the third-party LLM service it depends on.

Out of scope: the mobile app and the core banking platform beyond their interfaces with the assistant, model training, and any real organization.

## Method

| Step | Output | Main references |
|---|---|---|
| 1. System characterization | [01-system.md](01-system.md) | |
| 2. Threat modeling | [02-threat-model.md](02-threat-model.md) | OWASP Top 10 for LLM Applications 2026, MITRE ATLAS, OWASP API Security Top 10 2023 |
| 3. Risk analysis | [03-risk-register.md](03-risk-register.md) | NIST AI RMF 1.0 |
| 4. Control mapping | [04-controls.md](04-controls.md) | NIST AI RMF 1.0, NIST AI 600-1, ISO/IEC 42001:2023 Annex A, ISO/IEC 27001:2022 Annex A, BCRA AI supervision guide |
| 5. Testing (v0.2) | [05-test-plan.md](05-test-plan.md), [harness/](harness/) | A replica of the orchestrator with mock tools, run against a hosted model through its API; deterministic judges, resumable runs and a fingerprint of the setup on every attempt |
| 6. Findings | [06-findings.md](06-findings.md) | |

How to read it: 01 describes the system and lists, on purpose, the design decisions that create the risk. 02 analyzes each threat; T01, T02 and T07 are written in full as reference cases and the rest in condensed form. 03 scores them and explains every score. 04 says what to do about them and where each control sits in the frameworks. 06 turns the review into findings with an order of work.

## Roadmap

- [x] v0.1: system characterization, threat model, risk register, control mapping and design-review findings
- [ ] v0.2: test cases and evidence against a hosted model through its API, per [05-test-plan.md](05-test-plan.md)
  - [x] harness: replica orchestrator, mock tools, fictional data, deterministic judges, runner
  - [x] cases TC-01 and TC-03 written; TC-01b added on 24 October 2026 to test a pattern found in TC-01, and TC-01r on 26 October to test whether the two leaks repeat, each with its reading fixed before the run ([05-test-plan.md](05-test-plan.md#changes-during-v02))
  - [ ] results: TC-01 complete; TC-03 complete (baseline against Gemini, K02 against the scripted model); TC-01b complete, hypothesis contradicted; TC-01r 5 of 20; the current state of each case is in [harness/results/](harness/results/)
  - [ ] remaining cases
- [ ] v0.3: residual risk and final recommendations

How the references were checked: the OWASP LLM Top 10 2026 categories against the official document; the MITRE ATLAS identifiers against MITRE's D3FEND listing of ATLAS 2026.07 (AML.T0034 and case study AML.CS0021 against a third-party mirror only); the NIST AI RMF subcategories and the NIST AI 600-1 risk categories against the published documents; the Argentine statutes and the BCRA texts against their official publications; the ISO/IEC 42001 and 27001 Annex A numbering against public control listings, pending a check against the licensed text.

## Ground rules

- The bank, its assistant and every detail about them are fictional. Any resemblance to a real institution or product is coincidental.
- No text from ISO/IEC standards is reproduced. They are referenced by clause or control number only.
- Tests run against a replica of the system. The model provider's service is used as the model under its terms of use; it is not the target.
- This is a methodological case study. It is not an audit opinion and it is not legal advice. The legal readings in it are the author's, for the purposes of the case.

## References

Frameworks and standards

- OWASP GenAI Security Project, *OWASP Top 10 for LLM Applications 2026*. <https://genai.owasp.org/home/resources/owasp-genai-llm-top-10-2026/>
- OWASP, *API Security Top 10 2023*. <https://owasp.org/API-Security/>
- MITRE ATLAS. <https://atlas.mitre.org/>
- NIST, *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*, NIST AI 100-1. <https://www.nist.gov/itl/ai-risk-management-framework>
- NIST, *Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile*, NIST AI 600-1. <https://doi.org/10.6028/NIST.AI.600-1>
- ISO/IEC 42001:2023, *Information technology — Artificial intelligence — Management system*.
- ISO/IEC 27001:2022, *Information security, cybersecurity and privacy protection — Information security management systems — Requirements*.

Argentine regulation

- BCRA, *Guía de supervisión sobre el uso responsable y seguro de inteligencia artificial (IA)*, versión inicial junio de 2026. <https://www.bcra.gob.ar/guias-de-supervision-bcra/>
- BCRA, *Requisitos mínimos para la gestión y control de los riesgos de la tecnología y seguridad de la información*, texto ordenado al 13/02/2026 (Comunicación "A" 8401). <https://www.bcra.gob.ar/archivos/Pdfs/Texord/t-rmgcti.pdf>
- BCRA, *Guía de supervisión de prevención de pérdida de información (DLP)*, versión inicial junio de 2020. <https://www.bcra.gob.ar/guias-de-supervision-bcra/>
- Ley 21.526 de Entidades Financieras, art. 39 (secreto financiero) and art. 41 (sanciones).
- Ley 25.326 de Protección de los Datos Personales, in particular arts. 4, 6, 9, 10, 12, 25 and 31; Decreto 1558/2001.
- AAIP, international transfers: Disposición DNPDP 60-E/2016 (model clauses and adequacy list) and Resolución AAIP 198/2023 (RIPD model clauses). <https://www.argentina.gob.ar/transferencias-internacionales>
- Ley 24.240 de Defensa del Consumidor, arts. 4, 8, 37 and 53.

Cases

- *Moffatt v. Air Canada*, 2024 BCCRT 149 (British Columbia Civil Resolution Tribunal): a company is liable for its chatbot's misinformation.
- MITRE ATLAS case study AML.CS0021, *ChatGPT Conversation Exfiltration*: indirect prompt injection with exfiltration through a rendered image.

## Author

Santiago Paravano, researcher and university lecturer in AI ethics and data privacy, working on AI governance, risk and security.

Drafting was assisted by an AI model. The analysis and conclusions are the author's.

---

Personal academic work, published in my capacity as researcher and lecturer. It does not represent the position of any employer or institution.

*Reflexión personal, académica y de divulgación. No representa la posición de ningún organismo o institución en la que me desempeñe o haya desempeñado funciones (Ley 25.188).*
