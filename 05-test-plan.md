# 05 · Test plan

> **Planned for v0.2.** Nothing has been tested yet.

## Objective

Produce evidence for the threats that can be tested without a real bank: T01, T02, T03, T04, T09 and T11.

## Environment

- An open-weight model running locally.
- A minimal replica of the orchestrator with two mock tools, `get_recent_transactions` and `freeze_card`, backed by a fictional dataset.
- Open-source LLM testing tools, such as garak or promptfoo.

## Test case format

| Field | Content |
|---|---|
| ID | Test identifier |
| Threat | T-number from [02-threat-model.md](02-threat-model.md) |
| Technique | What the test tries |
| Input | Prompt, transfer description or document used |
| Expected safe behavior | What the assistant should do |
| Result | Pass or fail, with the number of attempts |
| Evidence | Log excerpt or report reference |

## Rules

- Only the local replica is tested. No third-party AI service is attacked.
- All data is fictional.
- Test cases and result summaries are published. Payloads tuned against real production systems are not.
