# Lab Data Simulator

A Python library for simulating laboratory data to verify Lab Informatics systems.

## Installation

```bash
./setup_env.sh
```

## Usage

```bash
poetry run python examples/demo_simulation.py
```

## Features

- **Plate Readers**: Simulate 96/384/1536 well plates with 4PL usage.
- **Liquid Handlers**: Generate transfer logs for Echo/Hamilton.
- **Compound Registration**: Generate SDF files with QSAR properties (MW, LogP, etc.).
- **Analytics**: Simulate SPR, Flow Cytometry, Purity results.
