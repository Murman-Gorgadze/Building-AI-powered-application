# AGENTS.md · FanReserve

## What this project is
A loyalty app that lets fans of recurring events (e.g. weekly football) buy tickets from my reserve when an event is sold out. This repo slice decides which events deserve a reserve and which fans get priority.

## Stack
- Language: Python 3.11
- Framework: none yet (plain module, pytest)
- Model access: OpenRouter · default model: google/gemini-3.8-flash, cloude, github copilot
- Data: CSV samples now, database later


## Conventions
- Secrets come from environment variables. Never write a key into a file.
- Every model call reads and logs `usage`.
- New features ship with at least one golden question in `/evals`.
- Scoring weights live as constants at the top of `src/reserve.py`; do not bury numbers in logic.

## You may
- Create and edit files in `src/`, `tests/`, `docs/`
- Propose dependency changes (ask before adding)

## You may not
- Touch `.env`, CI config, or anything in `secrets/`
- Delete tests to make them pass
- Call paid APIs in loops without a cap
