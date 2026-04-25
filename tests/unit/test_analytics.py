import pytest
import numpy as np
import pandas as pd
from lab_data_simulator.simulators.compound_reg import SDFGenerator
from lab_data_simulator.simulators.analytics.purity import PuritySimulator
from lab_data_simulator.simulators.analytics.spr import SPRSimulator
from lab_data_simulator.simulators.analytics.flow import FlowCytometrySimulator
from lab_data_simulator.simulators.analytics.hci import HCISimulator
from lab_data_simulator.simulators.calculations import percent_inhibition


def test_sdf_generation():
    gen = SDFGenerator()
    instructions = {
        'num_compounds': 5,
        'prefix': 'TEST',
        'start_id': 1,
    }
    content = gen.run_simulation(instructions)

    assert isinstance(content, str)
    assert content.count('V2000') == 5
    assert content.count('$$$$') == 5
    assert '<ID>' in content
    assert 'TEST1' in content
    # Valid molblock ends with M  END
    assert 'M  END' in content


def test_purity_simulator():
    sim = PuritySimulator(seed=42)
    instructions = {'samples': ['S1', 'S2']}
    df = sim.run_simulation(instructions)

    assert len(df) == 2
    assert 'Area Percent' in df.columns
    assert df.iloc[0]['Sample ID'] == 'S1'
    # Purity must be in valid range
    assert (df['Area Percent'] >= 0).all()
    assert (df['Area Percent'] <= 100).all()


def test_purity_reproducibility():
    df_a = PuritySimulator(seed=1).run_simulation({'samples': ['A', 'B', 'C']})
    df_b = PuritySimulator(seed=1).run_simulation({'samples': ['A', 'B', 'C']})
    pd.testing.assert_frame_equal(df_a, df_b)


def test_spr_simulator():
    sim = SPRSimulator(seed=42)
    instructions = {'samples': ['S1', 'S2']}
    df = sim.run_simulation(instructions)

    assert len(df) == 2
    assert 'KD (M)' in df.columns
    # KD must be positive (kd/ka with both positive)
    assert (df['KD (M)'] > 0).all()
    # Rmax and Chi2 in expected ranges
    assert (df['Rmax'] >= 30).all() and (df['Rmax'] <= 100).all()
    assert (df['Chi2'] >= 0.1).all() and (df['Chi2'] <= 2.0).all()


def test_spr_reproducibility():
    df_a = SPRSimulator(seed=5).run_simulation({'samples': ['A', 'B']})
    df_b = SPRSimulator(seed=5).run_simulation({'samples': ['A', 'B']})
    pd.testing.assert_frame_equal(df_a, df_b)


def test_flow_simulator():
    sim = FlowCytometrySimulator(seed=42)
    instructions = {'samples': ['S1', 'S2']}
    df = sim.run_simulation(instructions)

    assert len(df) == 2
    assert 'MFI' in df.columns
    assert 'Count' in df.columns
    assert 'Percent_Parent' in df.columns
    # Numeric columns must support arithmetic
    assert (df['Count'] >= 0).all()
    assert df['MFI'].mean() > 0
    assert (df['Percent_Parent'] >= 0).all() and (df['Percent_Parent'] <= 100).all()


def test_flow_reproducibility():
    df_a = FlowCytometrySimulator(seed=3).run_simulation({'samples': ['A', 'B']})
    df_b = FlowCytometrySimulator(seed=3).run_simulation({'samples': ['A', 'B']})
    pd.testing.assert_frame_equal(df_a, df_b)


def test_hci_simulator():
    sim = HCISimulator(seed=42)
    instructions = {'samples': ['S1', 'S2']}
    df = sim.run_simulation(instructions)

    assert len(df) == 2
    assert 'Cell Count' in df.columns
    # Cell counts must be non-negative
    assert (df['Cell Count'] >= 0).all()


def test_hci_reproducibility():
    df_a = HCISimulator(seed=8).run_simulation({'samples': ['A', 'B']})
    df_b = HCISimulator(seed=8).run_simulation({'samples': ['A', 'B']})
    pd.testing.assert_frame_equal(df_a, df_b)


def test_percent_inhibition_basic():
    high = [10000, 10000, 10000]
    low = [100, 100, 100]
    result = percent_inhibition(high, low, [5050])
    assert abs(result[0] - 50.0) < 1.0


def test_percent_inhibition_full_inhibition():
    result = percent_inhibition([10000], [100], [100])
    assert abs(result[0] - 100.0) < 0.01


def test_percent_inhibition_no_inhibition():
    result = percent_inhibition([10000], [100], [10000])
    assert abs(result[0] - 0.0) < 0.01


def test_percent_inhibition_zero_denominator():
    result = percent_inhibition([5000.0], [5000.0], [5000.0])
    assert np.isnan(result[0])


def test_sdf_reproducibility():
    gen_a = SDFGenerator(seed=99)
    gen_b = SDFGenerator(seed=99)
    content_a = gen_a.run_simulation({'num_compounds': 3, 'prefix': 'X'})
    content_b = gen_b.run_simulation({'num_compounds': 3, 'prefix': 'X'})
    assert content_a == content_b
