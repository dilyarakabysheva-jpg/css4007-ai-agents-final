# Semester Week 12 Progress Report

## Completed Work

All three week 12 milestones from the proposal are done.

- **Method database.** `src/data/methods.json` now holds 11 Russian-language assessment methods used in Kazakhstani speech therapy practice (Filicheva–Chirkina, Nishcheva, Inshakova, Smirnova, Fotekova, Volkova, Strebeleva, Trubnikova, Gribova, Agranovich, Sadovnikova). The proposal asked for at least 8. Each record has an id, authors, an age range in months, the assessment areas it covers and a short description of what it checks.
- **Search over the database.** `src/methods.py` adds `MethodDatabase`, which loads and validates the file, and `search_methods(age_months, area)`. This week it is a plain Python function. In week 13 it becomes the first model-callable tool.
- **Structured extraction of `ChildProfile`.** `Agent.extract_profile` sends the specialist's free-text description to the model with a JSON-only extraction prompt and validates the result with pydantic. It returns a `ChildProfile` with age in months, concerns and assessment areas.
- **Validation of inputs and outputs.** New pydantic models are `Method`, `MethodQuery` and `ProfileExtraction`. Areas are a fixed `Literal` set of seven codes, so an area the model makes up is rejected or dropped. Age is limited to 12–96 months, and a method whose age range is reversed fails at load time.
- **Deterministic age check.** `src/age.py` reads the age from the Russian text ("4 года 2 месяца", "3 г. 6 мес.", "4,5 года"). If the model's `age_months` disagrees with it, the parser wins and a warning is logged.
- **Tests.** `tests/test_week12.py` adds 11 test functions, 16 cases with parametrisation. The suite now has 16 test functions and 21 cases, all passing without an API key. The proposal target was 7.
- **Housekeeping.** I added `requirements.txt`. The fallback model in `src/config.py` still pointed to the shut-down `llama-3.3-70b-versatile`, so I changed it to `openai/gpt-oss-120b`.

AI assistance:I wrote the code myself and just used Claude to review it and catch any potential errors. I can walk through how every part works. All 21 tests are passing. My Codespaces limit ran out this week, so I uploaded the files directly on GitHub. I'll re-run the live check against the model once it resets..

## Important Commits

- Commit hash: 9a09a8f
- Description: feat: method database (11 methods) and validated search_methods
- Link: https://github.com/dilyarakabysheva-jpg/css4007-ai-agents-final/commit/9a09a8f

- Commit hash: b546f66
- Description: feat: structured ChildProfile extraction with deterministic age check
- Link: https://github.com/dilyarakabysheva-jpg/css4007-ai-agents-final/commit/b546f66

- Commit hash: 59ce9ed
- Description: test: week 12 tests for extraction, search and database failures
- Link: https://github.com/dilyarakabysheva-jpg/css4007-ai-agents-final/commit/59ce9ed

## Current Functionality

`python -m src.cli --profile "<description>"` turns a free-text description into a validated profile and lists the matching methods from the local database for each detected area:

```
Возраст: 4 г. 2 мес. (50 мес.)
Жалобы: не произносит Р и Л; словарь бедный

Звукопроизношение:
  - Т.Б. Филичева, Г.В. Чиркина. «Обследование детей с общим недоразвитием речи» — ...
  - Н.В. Нищева. «Речевая карта ребёнка с общим недоразвитием речи (от 4 до 7 лет)» — ...
  ...
Письмо и чтение:
  В базе нет методики для этого возраста и направления.
```

When the description has no age, the application does not guess. It says which data is missing. When the database file is missing or corrupted, it reports that instead of producing methods. The original advice mode, `python -m src.cli "<description>"`, still works.

In this mode the call order (extract the profile, then search each area) is still fixed in code. That is acceptable for week 12, but it does not meet the C-level criterion yet. In week 13 the model will decide when to call `search_methods`.

## Problems Encountered

1. The extraction step asks the model to convert "4 года 2 месяца" into months. The proposal already noted that language models are unreliable at this kind of arithmetic, and one wrong month shifts which methods match the child's age.
2. The model can return area labels outside the agreed list, such as a free-form "stuttering". These would break a strict schema or flow into the search as unknown values.
3. Age ranges for the methods are not given in a uniform way across the sources. Some authors give an exact range ("from 4 to 7 years"), others only "preschool age".

## Solutions

1. Age is cross-checked against a regex parser. The model still extracts it, so descriptions in unusual wording are covered, but the deterministic value takes priority whenever the text contains one.
2. Unknown areas are dropped before validation, with a logged warning, and the remaining fields still go through pydantic. `search_methods` itself rejects an unknown area with a `ValidationError`, so it can never quietly return an empty result for a made-up area.
3. Where the source gives no exact range, the range follows the author's stated target group. The database `note` marks these ranges as approximate. I will check them against the printed editions before the defense.

## What I Learned

An empty result and an error are different answers and need different types. `search_methods` returns `[]` when the database truly has no method for that age, and raises `MethodDatabaseError` when the database cannot be read. If both were an empty list, the agent could not tell "no such method" from "I could not look", and in week 13 it would have no basis for telling the specialist which one happened.

Validating at the boundary of the language model, rather than trusting its JSON, applies to values as well as structure. The JSON can be well-formed and still be wrong, as the age example shows.

Faking the model client in tests (`FakeClient` returns a response object shaped like the OpenAI SDK's) lets the whole extraction path be tested without a key or network access.

## Next Week

Register `search_methods` (and `check_age_norm` with a small `norms.json`) as tools with JSON schemas built from the existing pydantic models. Add the `tool_calls` branch to `Agent.run` so the model decides whether to call a tool, validate tool arguments before execution, and return tool results to the model. Test that a request like "Что такое ТНР?" is answered without any tool call.
