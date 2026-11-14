# Semester Week 11 Progress Report

## Completed Work

Fork created and the development environment set up in a GitHub Codespace. The API key is stored as a Codespaces secret, so no credential is present in any repository file.

Implemented `src/config.py`, `src/llm.py`, `src/schemas.py`, `src/agent.py` and `src/cli.py`, together with five tests in `tests/test_agent.py`. The proposal owed from week 10 was also written and submitted.

## Important Commits

47f892f — chore: project setup, env template and gitignore
d8f4572 — feat: LLM client, schemas, agent loop and 5 tests
eca98f6 — fix: switch to openai/gpt-oss-120b after Groq deprecated llama-3.3-70b
729d4a — docs: project proposal (week 10 deliverable, submitted late)

## Current Functionality

The application accepts a free-text request from the command line, sends it to the model, validates the response against a pydantic schema, and prints assessment directions followed by a disclaimer stating that the output is not a diagnosis.

The agent loop and its state object are already in place, bounded by a configurable step limit, although no tools are registered yet. All five tests pass without a live API key, since they exercise parsing and validation rather than the network.

## Problems Encountered

The first live request failed with HTTP 404: the model named in the proposal, `llama-3.3-70b-versatile`, had been shut down by Groq on 16 August 2026.

A second issue is substantive rather than technical. Asked about a 4-year-2-month-old boy who does not produce /r/ and /l/, the model recommended GFTA-2, PPVT-4 and the MacArthur-Bates CDI — English-language standardized instruments that are not used in Kazakhstani speech therapy practice and whose norms are derived from a different population.

## Solutions

The model was replaced with `openai/gpt-oss-120b`, the replacement Groq recommends on its deprecations page. Because the model name is read from an environment variable rather than hard-coded, recovery required changing one configuration line and no source code.

The second issue is not fixable by prompting, and it confirms the design chosen in the proposal: from week 13 the agent will only be able to name methods returned by `search_methods`, which queries a curated local database. A method absent from that database will not be producible at all.

## What I Learned

Writing the agent loop and the state object before any tool exists costs almost nothing and avoids restructuring later: week 13 extends an existing branch instead of rewriting the agent.

Keeping the model name in configuration rather than in code turned a broken deployment into a one-line fix. The failure also showed that provider documentation can be out of date relative to what an account can actually call.

Most importantly, the live run demonstrated concretely why tool grounding matters for this domain, rather than as an abstract requirement of the assignment.

## Next Week

Extract `ChildProfile` from free text as structured output, populate `src/data/methods.json` with at least eight real assessment methods, and extend the suite to seven tests.