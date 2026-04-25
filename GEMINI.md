# Anti-Gravity Rules & Token Guard — lab-data-simulator

## 🚫 EXCLUSIONS (Stop the Bleeding)
- **IGNORE:** `.venv/` — Python virtual environment with large compiled binaries (RDKit, scipy, numpy, etc.)
- **IGNORE:** `output/` — generated simulation output files
- **IGNORE:** `poetry.lock` — dependency lock file

## 🛠️ CONTEXT LIMITS
- Cheminformatics simulator using RDKit; dependencies in `.venv/` are compiled binaries
- For dependency questions, read `pyproject.toml` — not `poetry.lock`
- Never index `.so` or `.dylib` files
