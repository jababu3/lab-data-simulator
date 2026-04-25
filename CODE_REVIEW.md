# Code Review — lab-data-simulator

**Reviewer:** Claude  
**Date:** 2026-04-08  
**Scope:** Pre-publication review of all source files, tests, examples, and packaging config  
**Verdict:** Good foundation — fix the 6 high-priority items before going public

---

## Overall Assessment

The project is well-structured and clearly the work of someone who knows the domain. The ABC hierarchy (`Instrument` / `DataGenerator`), numpy `default_rng` seeding pattern, realistic simulation parameters (Echo droplet quantisation, 4PL model, Beta-distributed purity), and test coverage are all solid. The README is excellent. The issues below are fixable in a focused session; none require a redesign.

---

## 🔴 High Priority — Fix Before Publishing

### 1. Broken RDKit dependency in `pyproject.toml`

Both `rdkit` and `rdkit-pypi` are listed as dependencies. `rdkit-pypi` was the old unofficial PyPI package; the official package is now just `rdkit` (since 2022.09.5). Having both will cause dependency resolution conflicts. Additionally, `platform = "linux"` on the `rdkit` entry is incorrect — RDKit installs fine on macOS and Windows via PyPI.

**Fix:** Remove `rdkit-pypi` entirely and drop the `platform` constraint.

```toml
# Before
rdkit = { version = ">=2022.9.1", source = "pypi", platform = "linux" }
rdkit-pypi = ">=2022.9.1"

# After
rdkit = ">=2022.9.1"
```

---

### 2. `SDFGenerator` is non-reproducible and inconsistent with the rest of the API

Every other simulator accepts a `seed` parameter and uses `numpy.default_rng`. `SDFGenerator` uses stdlib `random` with no seeding, making it non-reproducible. Beyond that, the QSAR properties (MW, LogP, TPSA, etc.) are random floats assigned to a hardcoded benzene scaffold — they are not computed from real molecular structures.

**Fix (reproducibility):** Replace `import random` with numpy RNG:

```python
# compound_reg.py
def __init__(self, name: str = "SDFGenerator", seed: Optional[int] = None):
    super().__init__(name)
    self._rng = np.random.default_rng(seed)

# In run_simulation, replace random.uniform / random.randint calls:
mw = round(self._rng.uniform(150.0, 500.0), 2)
hbd = int(self._rng.integers(0, 6))  # etc.
```

**Fix (documentation):** Add a note to the class docstring and README clarifying that QSAR properties are synthetic values, not computed from molecular structure.

---

### 3. `four_parameter_logistic` is unsafe when `c=0`

`np.power(x / c, b)` will produce a division-by-zero when the inflection point `c=0`. This is physically meaningless but easily passed in by accident.

**Fix:** Add a guard at the top of the function:

```python
def four_parameter_logistic(x, a, b, c, d):
    x = np.asarray(x)
    if np.any(np.asarray(c) == 0):
        raise ValueError("Inflection point 'c' (EC50/IC50) must be nonzero.")
    return d + (a - d) / (1 + np.power((x / c), b))
```

---

### 4. Unknown simulation mode silently returns zeros

In `PlateReader.run_simulation`, an unrecognised mode falls through to:

```python
else:
    signals = np.zeros(len(well_ids))
```

A user who typos `"4pl_dilution"` instead of `"4PL_dilution"` gets a silent all-zero plate with no error. A public API should be explicit.

**Fix:**

```python
else:
    valid_modes = ("4PL_dilution", "flat", "picklist_driven")
    raise ValueError(
        f"Unknown simulation mode '{mode}'. Valid modes: {valid_modes}"
    )
```

---

### 5. `FlowCytometrySimulator` and `HCISimulator` store numeric columns as strings

In `flow.py`, `% Parent` and `MFI` are formatted as f-strings before being stored in the DataFrame. In `hci.py`, `Mean Intensity_Nuclei` and `Mean Area_Nuclei` are stored the same way. Users calling `.mean()` or doing numeric operations on these columns will get a `TypeError`.

Additionally, `% Parent` as a column name causes problems in pandas `.query()`, SQL imports, and many downstream tools.

**Fix:** Store as `float`, rename the problematic column:

```python
# flow.py
results.append({
    "Sample ID": s,
    "Population": "Lymphocytes/CD3+/CD4+",
    "Count": count,
    "Percent_Parent": round(percent_pos, 1),   # float, not string
    "MFI": round(mfi, 0),                      # float, not string
})

# hci.py
results.append({
    "Sample ID": s,
    "Well Region": "Center",
    "Cell Count": cell_count,
    "Mean Intensity_Nuclei": round(intensity, 2),  # float
    "Mean Area_Nuclei": round(area, 2),             # float
})
```

---

### 6. Well cursor overflow in `make_dose_response_picklist`

The `_well()` helper maps a linear index to a 384-well position. If `len(compounds) × n_points × n_replicates > 384`, it silently generates well labels like `Q1`, `R1`, etc., which do not exist in a 384-well plate. No bounds check is performed.

**Fix:** Add validation before the transfer loop:

```python
total_transfers = len(compounds) * n_points * n_replicates
plate_capacity = 384  # or derive from self.rows * self.cols if known
if total_transfers > plate_capacity:
    raise ValueError(
        f"Transfer count ({total_transfers}) exceeds 384-well plate capacity. "
        f"Reduce compounds, n_points, or n_replicates."
    )
```

---

## 🟡 Medium Priority — Should Address

### 7. `Hamilton` and `Tecan` are empty stubs exported in `__all__`

Both classes contain only `pass`. They appear in `__all__` and in the README, implying they work. External contributors or users will be confused.

**Fix:** Either implement them minimally or make the stub explicit:

```python
class Hamilton(LiquidHandler):
    """Tip-based Liquid Handler (Hamilton STAR/Vantage). Not yet implemented."""

    def run_simulation(self, instructions):
        raise NotImplementedError("Hamilton simulator is not yet implemented.")
```

Consider removing them from `__all__` until implemented.

---

### 8. `fit_4pl_curve` docstring has a wrong return key

The docstring says `Returns: Dict with keys: 'bottom', 'hill_slope', 'ic50', 'top', 'r2'` but the function returns `r_squared`, not `r2`. Any user reading the docstring and using `result['r2']` will get a `KeyError`.

**Fix:** Update the docstring to say `r_squared`.

---

### 9. `picklist_driven` mode uses `iterrows()`

The `picklist_driven` branch iterates the picklist with `iterrows()`. For large plates with many compounds this is unnecessarily slow. For a public library used in data pipelines, vectorised operations are expected.

**Fix:** Filter and compute with vectorised pandas:

```python
valid = picklist[picklist["Transfer Status"] == "Success"].copy()
valid["final_conc_um"] = (
    valid["Source Concentration (µM)"].astype(float)
    * valid["Actual Volume (nL)"].astype(float)
    / assay_volume_nl
)
# Then build well_to_signal from valid.groupby("Destination Well")
```

---

### 10. `poetry.toml` is in `.gitignore` but also committed

`poetry.toml` exists in the repository but is listed in `.gitignore`. This is contradictory. Committing it (to share the `virtualenvs.in-project = true` setting) is reasonable — but then it should not be in `.gitignore`.

**Fix:** Remove `poetry.toml` from `.gitignore`.

---

### 11. `sys.path.insert` hack in `demo_simulation.py`

```python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
```

This is unnecessary when running via `poetry run`, since the package is installed into the virtual environment. It also masks import errors that should surface during development.

**Fix:** Remove the `sys.path.insert` block. The demo already works correctly with `poetry run python examples/demo_simulation.py`.

---

### 12. Integration tests directory is empty

`tests/integration/` exists but contains no files. This looks like unfinished work to an outside contributor.

**Fix:** Add at least one integration test covering the full pipeline (Echo → PheraSTAR → `fit_4pl_curve`), or remove the directory. A minimal test:

```python
# tests/integration/test_pipeline.py
def test_echo_to_pherastar_pipeline():
    """Full Echo → PheraSTAR → 4PL fit pipeline runs without errors."""
    from lab_data_simulator.simulators.liquid_handler import Echo
    from lab_data_simulator.simulators.plate_reader import PheraSTAR
    from lab_data_simulator.simulators.calculations import fit_4pl_curve
    # ... exercise the full workflow
```

---

## 🔵 Low Priority / Polish

### 13. `percent_inhibition` is untested and has no coverage

`percent_inhibition` is exported in `__all__` but has zero test coverage, including the `denominator == 0` edge case. Add tests.

---

### 14. `FlowCytometrySimulator` and `HCISimulator` hardcode labels

`Population` is always `"Lymphocytes/CD3+/CD4+"` and `Well Region` is always `"Center"`. These should be configurable:

```python
population = instructions.get("population", "Lymphocytes/CD3+/CD4+")
```

---

### 15. `SPRSimulator` uses uniform distributions for `ka` and `kd`

`rng.uniform(1e4, 1e6)` gives a flat distribution, so most simulated values cluster around 500,000 M⁻¹s⁻¹. Real SPR kinetic data follows a log-normal distribution. A one-liner fix:

```python
# Sample log-uniformly between 10^4 and 10^6
ka = 10 ** self._rng.uniform(4, 6)
kd = 10 ** self._rng.uniform(-4, -2)
```

---

### 16. No `py.typed` marker file

Since the library has type annotations throughout, add a `py.typed` marker file so mypy and type-aware editors recognise the package as typed (PEP 561).

```bash
touch src/lab_data_simulator/py.typed
```

And in `pyproject.toml`:
```toml
[tool.poetry]
packages = [
  { include = "lab_data_simulator", from = "src" },
]
# py.typed is included automatically as part of the package
```

---

### 17. No `CONTRIBUTING.md`

For a public repo, a minimal contributing guide is expected. Cover: dev setup (`./setup_env.sh`), running tests (`poetry run pytest`), code style (`black`, `flake8`), and PR guidelines.

---

### 18. `GEMINI.md` and `CLAUDE.md` are AI-assistant scaffolding files

These are internal token-guard files for AI coding assistants. External contributors will find them confusing. Consider adding them to `.gitignore` or moving them to a `.ai-context/` folder with a brief README note explaining their purpose.

---

## Summary

| Priority | Count | Items |
|---|---|---|
| 🔴 High — block on these | 6 | RDKit deps, SDFGenerator seed, 4PL c=0, silent mode fallback, string-typed numeric columns, well overflow |
| 🟡 Medium — address soon | 6 | Hamilton/Tecan stubs, docstring key mismatch, iterrows, poetry.toml gitignore, sys.path hack, empty integration tests |
| 🔵 Low / polish | 6 | percent_inhibition tests, hardcoded labels, SPR distribution, py.typed, CONTRIBUTING.md, AI scaffolding files |

The most impactful single fix is the **RDKit dependency** (will break installs on non-Linux), followed by the **`SDFGenerator` reproducibility gap** (breaks the consistency contract every other simulator establishes).
