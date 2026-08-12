# Backend

This directory is the complete server-side boundary of MPVRP-CC.

- `app/` translates HTTP requests into domain operations.
- `core/generation/` creates and validates synthetic instances.
- `core/model/` owns canonical parsers and solution feasibility.
- `core/scoring/` evaluates submitted archives against official instances.
- `core/experiments/` creates and reprices paired cost scenarios.
- `database/` is the Notion persistence adapter.

Domain code does not depend on the static frontend. The frontend communicates
with it only through the routes declared in `app/main.py`.
