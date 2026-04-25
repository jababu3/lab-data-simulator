# Lab Data Simulator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![CI](https://github.com/jababu3/lab-data-simulator/actions/workflows/python-app.yml/badge.svg)](https://github.com/jababu3/lab-data-simulator/actions/workflows/python-app.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python library for generating realistic laboratory instrument data. Use it to explore, test, and learn about lab informatics systems without needing access to physical instruments.

Designed as a companion to hands-on lab informatics work — if you're building or evaluating a LIMS, ELN, or data pipeline, this library gives you realistic data to work with from day one.

## What It Simulates

| Instrument | Class | Output |
|---|---|---|
| Echo Acoustic Liquid Handler | `Echo` | Dose-response picklists with realistic failure rates and volume CV |
| PHERAstar Plate Reader | `PheraSTAR` | 4PL dose-response reads in block format with instrument report headers |
| Compound Registration | `SDFGenerator` | SDF files with computed QSAR properties (MW, LogP, etc.) |
| SPR (Surface Plasmon Resonance) | `SPRSimulator` | Binding kinetics results (KD, kon, koff) |
| Flow Cytometry | `FlowSimulator` | Cell population data |
| Purity Analysis | `PuritySimulator` | Compound purity results |

All simulators produce realistic noise, failure modes, and instrument-specific formatting — not just clean random numbers.

## Installation

Requires Python ≥ 3.9. Uses [Poetry](https://python-poetry.org/) for dependency management.

```bash
git clone https://github.com/jababu3/lab-data-simulator.git
cd lab-data-simulator
./setup_env.sh
```

Or install with Poetry directly:

```bash
poetry install
```

## Quick Start

Run the full demo to generate example outputs for all instruments:

```bash
poetry run python examples/demo_simulation.py
```

This creates an `output/` directory with:
- `echo_transfer_log.csv` — acoustic dispense picklist with transfer statuses
- `pherastar_readout.txt` — plate reader report with instrument headers
- `pherastar_raw_data.txt` — raw block-format data
- `ground_truth.csv` — known 4PL parameters for validating curve fits
- `demo_compounds.sdf` — compound registration file
- `spr_results.csv` — SPR binding results

## Usage Examples

### Echo Liquid Handler — Dose-Response Picklist

```python
from lab_data_simulator.simulators.liquid_handler import Echo

echo = Echo(seed=42)

compounds = [
    {'compound_id': 'CMP-001', 'compound_name': 'Staurosporine', 'source_well': 'A1', 'concentration': 10000},
    {'compound_id': 'CMP-002', 'compound_name': 'Gefitinib',     'source_well': 'A2', 'concentration': 10000},
    {'compound_id': 'DMSO',    'compound_name': 'DMSO Control',  'source_well': 'P1', 'concentration': 0},
]

picklist = echo.make_dose_response_picklist(
    compounds=compounds,
    source_plate='CPD_SRC_P001',
    dest_plate='ASSAY_PLATE_001',
    top_vol_nl=250.0,
    dilution_factor=3.0,
    n_points=8,
    n_replicates=2,
    failure_rate=0.08,   # 8% failure rate — realistic for acoustic dispensing
    volume_cv=0.03,      # 3% CV on dispense volume
)
```

### PHERAstar Plate Reader — Picklist-Driven Simulation

```python
from lab_data_simulator.simulators.plate_reader import PheraSTAR

reader = PheraSTAR()  # defaults to 384-well

ground_truth = {
    'CMP-001': {'a': 100, 'b': 1.2, 'c': 0.5,  'd': 50000, 'noise': 1500},
    'CMP-002': {'a': 100, 'b': 0.8, 'c': 5.0,  'd': 50000, 'noise': 1000},
    'DMSO':    {'a': 50000, 'b': 1.0, 'c': 1.0, 'd': 50000, 'noise': 800},
}

result_df = reader.run_simulation({
    'mode': 'picklist_driven',
    'params': {
        'picklist': picklist,
        'ground_truth': ground_truth,
        'assay_volume_nl': 50000.0,
        'baseline': 100,
        'baseline_noise': 20,
    }
})

# Export in PHERAstar report format
reader.to_report(result_df, protocol_name='Kinase Dose Response', output_path='output/readout.txt')
```

### Compound Registration — SDF Generation

```python
from lab_data_simulator.simulators.compound_reg import SDFGenerator

sdf_gen = SDFGenerator()
sdf_data = sdf_gen.run_simulation({'num_compounds': 10, 'prefix': 'CMP'})

with open('compounds.sdf', 'w') as f:
    f.write(sdf_data)
```

### SPR Binding Kinetics

```python
from lab_data_simulator.simulators.analytics.spr import SPRSimulator

spr = SPRSimulator()
results = spr.run_simulation({'samples': ['CMP-001', 'CMP-002', 'CMP-003']})
print(results)  # DataFrame with KD, kon, koff per compound
```

## Project Structure

```
lab-data-simulator/
├── src/
│   └── lab_data_simulator/
│       ├── core/
│       │   └── model.py              # Base simulation model
│       └── simulators/
│           ├── liquid_handler.py     # Echo acoustic dispenser
│           ├── plate_reader.py       # PHERAstar plate reader
│           ├── compound_reg.py       # Compound registration / SDF
│           └── analytics/
│               ├── spr.py            # Surface Plasmon Resonance
│               ├── purity.py         # Compound purity
│               ├── flow.py           # Flow cytometry
│               └── hci.py            # High-content imaging
├── examples/
│   └── demo_simulation.py
├── tests/
│   ├── unit/
│   └── integration/
├── output/                           # Generated by demo (gitignored)
└── pyproject.toml
```

## Running Tests

```bash
poetry run pytest
poetry run pytest --cov=lab_data_simulator  # with coverage
```

## Who This Is For

- **Lab informatics engineers** building or validating LIMS, ELN, or data pipeline integrations who need realistic test data
- **Scientists** learning how informatics systems process instrument output
- **Educators and students** getting hands-on with drug discovery data workflows without instrument access

## Related

This library pairs with [lab-informatics](https://github.com/jababu3/lab-informatics) — a simulated lab informatics environment (LIMS + data infrastructure) you can run locally. Together they give you a complete end-to-end lab data workflow to explore.

## Disclaimer

This project is not affiliated with, endorsed by, or connected to BMG Labtech, Revvity, Cytiva, Beckman Coulter, Molecular Devices, BD Biosciences, PerkinElmer, or any other instrument manufacturer. Instrument and software names are used solely to identify the output formats being simulated and to provide realistic context for educational purposes.

## License

MIT — see [LICENSE](LICENSE) for details.
