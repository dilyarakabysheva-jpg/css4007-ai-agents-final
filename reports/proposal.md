# Project Proposal — Semester Week 10

## Project Title

Speech Therapy Assessment Assistant — a tool-using agent that helps a speech therapist select assessment methods for a child.

## Problem Description

Initial speech-language assessment requires selecting methods that match the child's age and the suspected disorder. These methods are scattered across textbooks and clinical manuals, and a novice specialist spends considerable time locating them for each child.

A general-purpose chatbot is unsafe for this task. In a live test run on 15 November 2026, asked about a 4-year-2-month-old boy who does not produce /r/ and /l/, the model recommended GFTA-2, PPVT-4 and the MacArthur-Bates CDI. These are English-language standardized instruments that are not part of Kazakhstani speech therapy practice, and their norms are derived from a different population. The model produced them because it draws method names from its training data, which is predominantly English-language literature.

This project addresses exactly that failure. The agent may only name methods returned by a tool that queries a curated local database, so a recommendation the database does not contain cannot be produced at all.

## Target Users

Practicing speech therapists and speech therapy students during clinical placement. Secondary users: instructors of the psychological-pedagogical diagnostics course, who can use the generated protocols as teaching material.

## Selected Difficulty

C — tool-using agent. The LLM selects which tool to call; no hard-coded call sequence is used.

## Expected Functionality

The specialist describes a child in free text. The model decides on its own whether to search the method database, check a reported result against age norms, build an assessment protocol, or answer directly without any tool. The agent returns assessment directions with references to specific methods from the database, explains what each direction checks, and states what information is missing when the description is incomplete.

The agent never issues a diagnosis. It supports the specialist's decision and says so explicitly in every answer.

## Proposed Functions

| Function | Purpose | Inputs | Outputs | Dependencies |
| --- | --- | --- | --- | --- |
| `Config.validate` | fail early when credentials are absent | none | raises on missing key | python-dotenv |
| `LLMClient.chat` | call the model, translate API failures into user-facing errors | messages, tools | API response object | openai |
| `Agent.run` | agent loop bounded by a step limit | request string | `AssessmentAdvice` | llm, schemas, config |
| `Agent.parse` | extract and validate JSON from model output | raw text | `AssessmentAdvice` | pydantic |
| `ChildProfile` | validate child data before any tool call | age in months, concerns | validated model | pydantic |
| `search_methods` | find assessment methods in the local database | age_months, area | list of methods | methods.json |
| `check_age_norm` | compare a reported result against age norms | age_months, area, score | deviation and level | norms.json |
| `build_protocol` | assemble an assessment protocol form | child profile, method ids | protocol text | methods.json |

## Proposed Agent Tools

Three tools, where the C level requires two; the third provides margin if one proves too thin in practice.

`search_methods` cannot be replaced by prompting. Method names, authors and age ranges must be exact, and the live run described above demonstrates what the model produces without this constraint.

`check_age_norm` performs arithmetic against norm tables. Language models are unreliable at numeric comparison, and a wrong answer here would mislead a specialist about whether a child's vocabulary falls within norm.

`build_protocol` assembles a document strictly from data already confirmed by the other two tools, so the output form cannot contain invented methods.

All tool arguments are validated with pydantic before the function executes, so malformed arguments from the model are rejected rather than passed through.

## Model Selection

`openai/gpt-oss-120b` served through Groq's OpenAI-compatible API, with `temperature` 0.2 for reproducible answers. The model supports function calling, which the C level requires.

The model name and base URL are read from environment variables rather than hard-coded. This decision was validated during week 11: the originally selected `llama-3.3-70b-versatile` returned HTTP 404 because Groq had shut it down on 16 August 2026, and recovery required changing one line of configuration rather than editing source code.

The API key is supplied through a Codespaces secret and never written to any file in the repository.

## Architecture

The loop and the state object are in place from week 11, before tools exist, so adding tool handling in week 13 extends the existing branch rather than restructuring the agent.

## Example Requests

1. "Мальчик 4 года 2 месяца, не произносит Р и Л, словарь бедный" — expected: the model calls `search_methods` with the child's age in months and the articulation area, and reports only methods returned by that call.

2. "Девочка 5 лет, активный словарь 1200 слов, это норма?" — expected: the model calls `check_age_norm` and reports the deviation computed by the tool, not estimated by itself.

3. "Что такое ТНР?" — expected: a direct answer with no tool call. The C level explicitly requires handling requests that need no tools.

## Evaluation Plan

Eight pytest cases, none of which require a live API key, so the suite runs deterministically:

- two on input validation: implausible age, empty list of concerns
- two on parsing model output: JSON embedded in surrounding prose, malformed JSON
- two on tool selection: a request that must trigger a tool, a request that must not
- one on tool failure: the database file is unavailable and the agent reports this instead of inventing data
- one on missing data: no method exists for the requested age, and the agent says so

Beyond the automated suite, the three example requests above are run manually against the live model each week, and the results are recorded in `reports/week-16.md`.

Reliability scenarios are tested in week 15: a request for a diagnosis, a prompt injection attempting to override the system role, an out-of-range age, and a failed tool call.

## Weekly Milestones

| Week | Dates | Milestone |
| --- | --- | --- |
| 10 | Nov 2–8 | Proposal and planning. Submitted late on 13 November. |
| 11 | Nov 9–15 | LLM integration, structured output, validation, 5 tests, working prototype. |
| 12 | Nov 16–22 | Structured extraction of `ChildProfile` from free text; `methods.json` populated with at least 8 methods; 7 tests. |
| 13 | Nov 23–29 | `search_methods` and `check_age_norm` registered as model-callable tools; argument validation; handling of requests needing no tools. |
| 14 | Nov 30–Dec 6 | `build_protocol` added; tool execution logging to `logs/tool_calls.log`. |
| 15 | Dec 7–13 | Reliability: diagnosis refusal, prompt injection resistance, tool failure handling, step limit. |
| 16 | Dec 14–20 | Full test run, results recorded, setup and run instructions in README, AI assistant usage statement. |
| 17 | Dec 21–22 | Final commit hash, fork URL, live demonstration. |