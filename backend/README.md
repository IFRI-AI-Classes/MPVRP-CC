# Backend

This directory is the complete server-side boundary of MPVRP-CC.

- `app/` translates HTTP requests into domain operations.
- `core/generation/` creates and validates synthetic instances.
- `core/model/` owns canonical parsers and solution feasibility.
- `core/scoring/` evaluates submitted archives against official instances.
- `core/experiments/` creates and reprices paired cost scenarios.
- `database/` stores participant and scoreboard information.

The server and the static website remain independent. They communicate through
the public HTTP API.
