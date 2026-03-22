import pytest
import numpy as np
import pandas as pd
from lab_data_simulator.simulators.plate_reader import PlateReader, PheraSTAR
from lab_data_simulator.simulators.calculations import four_parameter_logistic, fit_4pl_curve


def test_plate_reader_initialization():
    reader = PlateReader("TestReader", plate_format=384)
    assert reader.rows == 16
    assert reader.cols == 24

    reader_96 = PlateReader("96Well", plate_format=96)
    assert reader_96.rows == 8
    assert reader_96.cols == 12

    reader_1536 = PlateReader("1536Well", plate_format=1536)
    assert reader_1536.rows == 32
    assert reader_1536.cols == 48


def test_plate_reader_invalid_format():
    with pytest.raises(ValueError):
        PlateReader("BadReader", plate_format=192)


def test_four_parameter_logistic():
    # At x == c (inflection point), y == (a + d) / 2
    # With a=0, b=1, c=10, d=100 → y at x=10 should be 50
    res = four_parameter_logistic(10, 0, 1, 10, 100)
    assert np.isclose(res, 50.0)

    # As x → 0, y → a (Bottom)
    res_zero = four_parameter_logistic(0, 0, 1, 10, 100)
    assert np.isclose(res_zero, 0.0)


def test_plate_simulation_structure_384():
    """PheraSTAR defaults to 384-well (16 × 24 = 384 wells)."""
    reader = PheraSTAR(seed=42)
    instructions = {'mode': 'flat', 'params': {'baseline': 500}}
    df = reader.run_simulation(instructions)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 16 * 24   # 384 wells
    assert 'Well' in df.columns
    assert 'Signal' in df.columns


def test_plate_simulation_structure_1536():
    reader = PlateReader("1536Reader", plate_format=1536, seed=0)
    instructions = {'mode': 'flat', 'params': {'baseline': 500}}
    df = reader.run_simulation(instructions)
    assert len(df) == 32 * 48   # 1536 wells


def test_plate_reader_reproducibility():
    """Same seed produces identical signals."""
    reader_a = PheraSTAR(seed=7)
    reader_b = PheraSTAR(seed=7)
    instructions = {'mode': 'flat', 'params': {'baseline': 1000, 'noise_std': 50}}
    df_a = reader_a.run_simulation(instructions)
    df_b = reader_b.run_simulation(instructions)
    pd.testing.assert_frame_equal(df_a, df_b)


def test_4pl_fit():
    x = np.array([0.1, 1, 10, 100, 1000])
    # Generate perfect data: a=0, b=1, c=10, d=100
    y = four_parameter_logistic(x, 0, 1, 10, 100)

    result = fit_4pl_curve(x, y)

    assert np.isclose(result['bottom'], 0, atol=1e-5)
    assert np.isclose(result['top'], 100, atol=1e-5)
    assert np.isclose(result['ic50'], 10, atol=1e-5)
    assert result['r_squared'] > 0.99


def test_4pl_fit_empty_arrays():
    """fit_4pl_curve handles empty input gracefully."""
    result = fit_4pl_curve([], [])
    assert np.isnan(result['ic50'])
    assert result['r_squared'] == 0.0
