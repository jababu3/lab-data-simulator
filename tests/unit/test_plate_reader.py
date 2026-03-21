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

def test_four_parameter_logistic():
    # Test known values
    # y = d + (a - d) / (1 + (x / c)^b)
    # Let a=0, d=100, c=10, b=1
    # At x=10 (inflection), y should be (0+100)/2 = 50
    res = four_parameter_logistic(10, 0, 1, 10, 100)
    assert np.isclose(res, 50.0)
    
    # At x=0, y should be ~d (100) if b>0?? No, at x=0, (x/c)^b is 0, so 1+0=1, denom=1, y = d + a - d = a.
    # Wait, limit x->0: (x/c)^b -> 0 if b>0.
    # 1 + 0 = 1.
    # Res = d + (a - d) = a.
    # So at 0 concentration, we expect 'a' (Bottom/Min).
    res_zero = four_parameter_logistic(0, 0, 1, 10, 100)
    assert np.isclose(res_zero, 0.0)

def test_plate_simulation_structure():
    reader = PheraSTAR() # defaults to 1536
    instructions = {'mode': 'flat', 'params': {'baseline': 500}}
    df = reader.run_simulation(instructions)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 32 * 48
    assert 'Well' in df.columns
    assert 'Signal' in df.columns
    
def test_4pl_fit():
    x = np.array([0.1, 1, 10, 100, 1000])
    # Generate perfect data: a=0, b=1, c=10, d=100
    y = four_parameter_logistic(x, 0, 1, 10, 100)
    
    result = fit_4pl_curve(x, y)
    
    assert np.isclose(result['bottom'], 0, atol=1e-5)
    assert np.isclose(result['top'], 100, atol=1e-5)
    assert np.isclose(result['ic50'], 10, atol=1e-5)
    assert result['r_squared'] > 0.99
