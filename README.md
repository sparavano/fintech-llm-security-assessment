# LLM Security Assessment: Digital Bank Assistant (case study)

Security and risk assessment of a **fictional** generative AI assistant run by a **fictional** Argentine digital bank. The case walks through the full cycle an AI risk or security team would follow for an LLM-based system: characterize it, model its threats, rate the risks and map them to controls under the frameworks a regulated financial entity in Argentina would be expected to consider.

> **Status:** v0.1 in progress. Design review only, no testing yet. See [Roadmap](#roadmap).

## Why this case

In June 2026 the Central Bank of Argentina (BCRA) published a supervision guide on the responsible and secure use of AI. It sets supervisory expectations on AI governance and risk management, data, model validation and monitoring, bias and explainability, cybersecurity, business continuity, outsourcing and transparency. A customer-facing assistant that reads account data and can act on the customer's behalf touches nearly every one of those areas, which makes it a good test bed.

## Scope

In scope: the assistant described in [01-system.md](01-system.md), its orchestration layer, retrieval index, tool integrations, conversation logging and the third-party LLM service it depends on.

Out of scope: the mobile app and the core banking platform beyond their interfaces with the assistant, model training, and any real organization.

## Method

| Step | Output | Main references |
|---|---|---|
| 1. System characterization | [01-system.md](01-system.md) | |
| 2. Threat modeling | [02-threat-model.md](02-threat-model.md) | OWASP Top 10 for LLM Applications 2026, MITRE ATLAS |
| 3. Risk analysis | [03-risk-register.md](03-risk-register.md) | NIST AI RMF 1.0 |
| 4. Control mapping | [04-controls.md](04-controls.md) | NIST AI RMF 1.0, NIST AI 600-1, ISO/IEC 42001:2023 Annex A, BCRA AI supervision guide |
| 5. Testing (v0.2) | [05-test-plan.md](05-test-plan.md) | Open-source LLM testing tools against a locally hosted open model |
| 6. Findings | [06-findings.md](06-findings.md) | |

## Roadmap

- [x] v0.1: system characterization
- [ ] v0.1: threat model, risk register, control mapping and design-review findings
- [ ] v0.2: test cases and evidence against a locally hosted open model
- [ ] v0.3: residual risk and final recommendations

## Ground rules

- The bank, its assistant and every detail about them are fictional. Any resemblance to a real institution or product is coincidental.
- No text from ISO/IEC standards is reproduced. They are referenced by clause or control number only.
- Tests run only against open models hosted locally. No third-party AI service is attacked.
- This is a methodological case study. It is not an audit opinion and it is not legal advice.

## References

- BCRA, *Guía de supervisión sobre el uso responsable y seguro de inteligencia artificial (IA)*, versión inicial junio de 2026. <https://www.bcra.gob.ar/guias-de-supervision-bcra/>
- BCRA, *Requisitos mínimos para la gestión y control de los riesgos de la tecnología y seguridad de la información* (texto ordenado). <https://www.bcra.gob.ar/archivos/Pdfs/Texord/t-rmgcti.pdf>
- OWASP GenAI Security Project, *OWASP Top 10 for LLM Applications 2026*. <https://genai.owasp.org/home/resources/owasp-genai-llm-top-10-2026/>
- MITRE ATLAS. <https://atlas.mitre.org/>
- NIST, *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*, NIST AI 100-1. <https://www.nist.gov/itl/ai-risk-management-framework>
- NIST, *Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile*, NIST AI 600-1. <https://doi.org/10.6028/NIST.AI.600-1>
- ISO/IEC 42001:2023, *Information technology — Artificial intelligence — Management system*.
- Ley 25.326 de Protección de los Datos Personales (Argentina).
- Ley 21.526 de Entidades Financieras, art. 39 (secreto financiero).

## Author

Santiago Paravano, researcher and university lecturer in AI ethics and data privacy, working on AI governance, risk and security.

Drafting was assisted by an AI model. The analysis and conclusions are the author's.

---

Personal academic work, published in my capacity as researcher and lecturer. It does not represent the position of any employer or institution.

*Reflexión personal, académica y de divulgación. No representa la posición de ningún organismo o institución en la que me desempeñe o haya desempeñado funciones (Ley 25.188).*
