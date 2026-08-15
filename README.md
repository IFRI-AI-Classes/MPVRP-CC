# MPVRP-CC platform

Research and competition platform for the **Multi-Product Vehicle Routing
Problem with Split Deliveries and Changeover Costs**.

In this benchmark, a changeover cost represents the operational preparation
associated with loading a product. It may apply before the first trip as well
as between successive trips; it is not limited to the act of switching from
one product to another.

The repository deliberately separates two deployable surfaces:

- the static GitHub Pages frontend at the repository root and in `pages/`;
- the FastAPI service and domain logic in `backend/`.

The interactive route visualizer remains a standalone canvas application in
`pages/visualisation.html`.

## Benchmark scenarios

`data/instances/` contains 150 one-to-one pairs:

- `with_changeover_costs/` is the official dataset used for scoring;
- `without_changeover_costs/` keeps the same UUID, fleet, locations, stocks and
  demands, but replaces every transition cost by zero.

The official score is the sum of `distance_total + total_switch_cost` across the
150 original-cost instances. A missing or infeasible solution receives a penalty
of `100000`.

See [`docs/problem.md`](docs/problem.md),
[`docs/instance_format.md`](docs/instance_format.md), and
[`docs/solution_format.md`](docs/solution_format.md) for the canonical contract.

## Structure

```text
backend/
  app/                 FastAPI application and HTTP routes
  core/generation/     structured random instance generation
  core/model/          instance/solution parsing and strict feasibility checks
  core/scoring/        secure ZIP ingestion and official evaluation
  core/experiments/    paired scenarios and ex-post changeover repricing
  database/            participant and scoreboard persistence
data/instances/        paired benchmark datasets
docs/                  Markdown sources used by the static documentation pages
pages/                 GitHub Pages UI and JavaScript clients
tests/                 unit and integration tests
```

## Backend setup

Python 3.12 and `uv` are recommended.

```bash
uv sync
uv run uvicorn backend.app.main:app --reload
```

The API is available on `http://127.0.0.1:8000`; OpenAPI documentation is at
`/docs`.

Configure deployments with:

```dotenv
FRONTEND_DEV_URL=http://127.0.0.1:5500
FRONTEND_PROD_URL=https://your-org.github.io
FRONTEND_PROD_URL_2=https://your-custom-domain.example
```

## Static frontend

The frontend has no build requirement. Serve the repository root with any static
server, for example:

```bash
python -m http.server 5500
```

Create the runtime API configuration before publishing:

```bash
API_URL=https://api.example.org ./generate_config.sh
```

The UI loads Tailwind CSS and the Inter/Bricolage Grotesque web fonts from their
CDNs. Documentation pages fetch their Markdown source at runtime. The
specification page provides an A4 print view; its “Download as PDF” action opens
the browser print dialog, where it can be saved as PDF.

## Tests

```bash
uv run pytest
```

The suite validates the API, strict solution checks, generator, ZIP safety,
scoreboard persistence and all 150 paired benchmark files.

## Docker

```bash
docker build -t mpvrp-cc .
docker run --rm -p 8000:8000 --env-file .env mpvrp-cc
```

## License

See [`LICENSE`](LICENSE).
