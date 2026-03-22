import pytest
import pandas as pd
from lab_data_simulator.simulators.liquid_handler import LiquidHandler, Echo, Hamilton

_VALID_STATUSES = {'Success', 'Insufficient Fluid', 'Fluid Thickness Error',
                   'Well Geometry Error', 'No Fluid'}


def test_liquid_handler_basic_transfer():
    handler = LiquidHandler("TestHandler")
    instructions = {
        'source_plate': 'Src1',
        'dest_plate': 'Dst1',
        'transfers': [
            {'source_well': 'A01', 'dest_well': 'A01', 'volume': 10},
            {'source_well': 'A02', 'dest_well': 'A02', 'volume': 20},
        ]
    }

    log = handler.run_simulation(instructions)

    assert len(log) == 2
    assert log.iloc[0]['Transfer Volume'] == 10
    assert log.iloc[1]['Transfer Volume'] == 20
    assert 'Source Plate Name' in log.columns
    assert 'Destination Plate Name' in log.columns


def test_echo_simulation_structure():
    """Echo run_simulation returns correct columns and valid transfer statuses."""
    echo = Echo(seed=42)
    instructions = {
        'transfers': [{'source_well': 'A1', 'dest_well': 'B1', 'volume': 25.0}],
        'failure_rate': 0.0,   # force success so test is deterministic
    }
    log = echo.run_simulation(instructions)

    assert 'Transfer Status' in log.columns
    assert log.iloc[0]['Transfer Status'] == 'Success'
    assert 'Requested Volume (nL)' in log.columns
    assert 'Actual Volume (nL)' in log.columns


def test_echo_simulation_failure_statuses():
    """Transfer statuses are always one of the known values."""
    echo = Echo(seed=0)
    instructions = {
        'transfers': [{'source_well': 'A1', 'dest_well': f'B{i}', 'volume': 25.0}
                      for i in range(1, 51)],
        'failure_rate': 0.5,
    }
    log = echo.run_simulation(instructions)
    assert set(log['Transfer Status'].unique()).issubset(_VALID_STATUSES)


def test_echo_failure_rate_validation():
    """failure_rate outside [0, 1] raises ValueError."""
    echo = Echo()
    with pytest.raises(ValueError):
        echo.run_simulation({'transfers': [], 'failure_rate': 1.5})
    with pytest.raises(ValueError):
        echo.run_simulation({'transfers': [], 'failure_rate': -0.1})


def test_echo_volume_cv_validation():
    """Negative volume_cv raises ValueError."""
    echo = Echo()
    with pytest.raises(ValueError):
        echo.run_simulation({'transfers': [], 'volume_cv': -0.01})


def test_echo_dose_response_picklist():
    """make_dose_response_picklist returns correct row count and columns."""
    echo = Echo(seed=42)
    compounds = [
        {'compound_id': 'CMP-001', 'compound_name': 'CompA', 'source_well': 'A1', 'concentration': 10000},
        {'compound_id': 'CMP-002', 'compound_name': 'CompB', 'source_well': 'A2', 'concentration': 10000},
    ]
    picklist = echo.make_dose_response_picklist(
        compounds=compounds,
        n_points=8,
        n_replicates=2,
        failure_rate=0.0,
    )

    # 2 compounds × 8 points × 2 replicates = 32 rows
    assert len(picklist) == 32
    assert 'Compound ID' in picklist.columns
    assert 'Destination Well' in picklist.columns


def test_echo_reproducibility():
    """Same seed produces identical results."""
    echo_a = Echo(seed=99)
    echo_b = Echo(seed=99)
    instructions = {
        'transfers': [{'source_well': 'A1', 'dest_well': f'B{i}', 'volume': 100.0}
                      for i in range(1, 11)],
        'failure_rate': 0.3,
    }
    log_a = echo_a.run_simulation(instructions)
    log_b = echo_b.run_simulation(instructions)
    pd.testing.assert_frame_equal(log_a, log_b)
