import pytest
from lab_data_simulator.simulators.compound_reg import SDFGenerator
from lab_data_simulator.simulators.analytics.purity import PuritySimulator
from lab_data_simulator.simulators.analytics.spr import SPRSimulator
from lab_data_simulator.simulators.analytics.flow import FlowCytometrySimulator
from lab_data_simulator.simulators.analytics.hci import HCISimulator

def test_sdf_generation():
    gen = SDFGenerator()
    instructions = {
        'num_compounds': 5,
        'prefix': 'TEST',
        'start_id': 1
    }
    content = gen.run_simulation(instructions)
    
    assert isinstance(content, str)
    assert content.count('V2000') == 5
    assert content.count('$$$$') == 5
    assert '<ID>' in content
    assert 'TEST1' in content

def test_purity_simulator():
    sim = PuritySimulator()
    instructions = {'samples': ['S1', 'S2']}
    df = sim.run_simulation(instructions)
    assert len(df) == 2
    assert 'Area Percent' in df.columns
    assert df.iloc[0]['Sample ID'] == 'S1'

def test_spr_simulator():
    sim = SPRSimulator()
    instructions = {'samples': ['S1']}
    df = sim.run_simulation(instructions)
    assert len(df) == 1
    assert 'KD (M)' in df.columns

def test_flow_simulator():
    sim = FlowCytometrySimulator()
    instructions = {'samples': ['S1']}
    df = sim.run_simulation(instructions)
    assert len(df) == 1
    assert 'MFI' in df.columns

def test_hci_simulator():
    sim = HCISimulator()
    instructions = {'samples': ['S1']}
    df = sim.run_simulation(instructions)
    assert len(df) == 1
    assert 'Cell Count' in df.columns
