# Test harness (v0.2)

A minimal replica of the Acme Assistant orchestrator, with mock tools, a fictional dataset and a fictional help center, used to produce the evidence planned in [05-test-plan.md](../05-test-plan.md). Everything in here is fictional.

## What it replicates

- `orchestrator.py`: component C3 from [01-system.md](../01-system.md). The baseline reproduces the design decisions that create the risk (descriptions passed verbatim, confirmation judged by the model, one service credential, Markdown rendered as is). Each Bank-side control under test can be switched on: K01, K02, K03, K05, K14.
- `prompts/system.md`: the assistant's rules, with the tool definitions and escalation criteria in the prompt (design decision 4).
- `data/customers.json`, `data/help_center/`: three fictional customers and six fictional help center articles.
- `providers.py`: the model behind one interface. Any OpenAI-compatible endpoint (OpenAI, Groq, Gemini's compatibility endpoint, a local Ollama server), Anthropic, or a scripted mock for checking the mechanics.
- `cases/`: one JSON file per test case, with the injected payloads, the customer prompts and a deterministic judge. No LLM-as-judge: success is a string the attacker chose appearing in the reply, or an orchestrator event such as a freeze executed on the model's word.
- `run.py`: runs a case twice, baseline and with its control. Every completed attempt is appended to `results/<case>/<model>/attempts.jsonl`; `results.json` (every attempt, full messages) and `transcripts.md` (ASR table and representative transcripts) are rebuilt from it after each invocation. Runs are resumable: a later invocation only runs what is missing.

## Running

```bash
cd harness
pip install -r requirements.txt

# Gemini, through its OpenAI-compatible endpoint (the key goes in OPENAI_API_KEY)
export PROVIDER=openai MODEL=gemini-3.5-flash REASONING_EFFORT=low MIN_INTERVAL=13 OPENAI_API_KEY=<Gemini API key>
export OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/

# OpenAI, or any other OpenAI-compatible endpoint (unset OPENAI_BASE_URL for OpenAI itself)
export PROVIDER=openai MODEL=<model name> OPENAI_API_KEY=<key>

# Anthropic
export PROVIDER=anthropic MODEL=<model name> ANTHROPIC_API_KEY=<key>

python run.py TC-01 TC-03
python run.py TC-01 TC-03 --max-attempts 8          # at most 8 new attempts this time
python run.py TC-01 TC-03 --report                  # rebuild the reports, no model calls
python run.py TC-01 --attempts 5 --runs baseline    # a quick partial run
PROVIDER=mock python run.py TC-01                   # mechanics check, never evidence
```

`MIN_INTERVAL` spaces requests to stay under a per-minute quota (Gemini's free tier allowed 5 requests per minute per model in October 2026); a per-minute rate-limit error is waited out and retried. The runner stops at the first other provider error (a daily quota, a timeout) and does not record the interrupted attempt. Running the same command again continues where it stopped. On a free tier with a small daily request quota, a case can therefore be completed over several days; each attempt keeps its own timestamp and the report shows the date range.

Keys are read from the environment only. Nothing in `results/` contains a key; check before committing anyway.

## Reading the results

ASR is hits over completed attempts. Attempts interrupted by a provider error are not recorded and are run again later. Each attempt records the model name as configured, the model names the API reported back (`served_models`), the provider, the settings, the controls in force and the timestamp, so results are comparable across models and across time (T10). The two model names can differ: a hosted model name can be an alias that the provider resolves to a newer model. `served_models` only records what the API's responses say, which is not proof of which model answered: in October 2026 Gemini's responses echoed the requested `gemini-3.5-flash`, while its quota errors for the same requests named `gemini-3.6-flash`. The report warns when the attempts it aggregates were served by more than one model or made with different settings. An attempt only counts if its payload and customer prompt match the case file as it stands; editing a case invalidates the affected attempts.

## Rules

- The system under test is this replica. The model provider's service is the model, not the target; the payloads are ordinary text inside the replica's own tool results and messages.
- Payloads are published as test cases. Nothing here is tuned against a real production system.
- All data is fictional.
