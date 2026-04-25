# Claude Token Guard — lab-data-simulator

## 🚫 NEVER READ OR INDEX
- `.venv/` — Python virtual environment with many large compiled binaries (RDKit, scipy, numpy, etc.)
- `output/` — generated simulation output files
- `poetry.lock` — dependency lock file, rarely useful in context

## ✅ SAFE TO READ
- `src/` — all simulation source code
- `tests/` — test files
- `examples/` — usage examples
- `pyproject.toml`, `poetry.toml` — project configuration
- `README.md`, `setup_env.sh`

## 🛠 CONTEXT RULES
- This is a lab data simulator with RDKit/cheminformatics dependencies
- For dependency questions, read `pyproject.toml` — not `poetry.lock`
- Never index `.so` or `.dylib` files
