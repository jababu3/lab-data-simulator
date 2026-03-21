import pytest
import pandas as pd
from lab_data_simulator.simulators.liquid_handler import LiquidHandler, Echo, Hamilton

def test_liquid_handler_basic_transfer():
    handler = LiquidHandler("TestHandler")
    instructions = {
        'source_plate': 'Src1',
        'dest_plate': 'Dst1',
        'transfers': [
            {'source_well': 'A01', 'dest_well': 'A01', 'volume': 10},
            {'source_well': 'A02', 'dest_well': 'A02', 'volume': 20}
        ]
    }
    
    log = handler.run_simulation(instructions)
    
    assert len(log) == 2
    assert log.iloc[0]['Volume'] == 10
    assert log.iloc[1]['Volume'] == 20
    assert 'Source Plate' in log.columns
    assert 'Destination Plate' in log.columns

def test_echo_simulation():
    echo = Echo()
    instructions = {
        'transfers': [{'source_well': 'A1', 'dest_well': 'B1', 'volume': 2.5}]
    }
    log = echo.run_simulation(instructions)
    
    assert 'Transfer Status' in log.columns
    assert log.iloc[0]['Transfer Status'] == 'Success'
