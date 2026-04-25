"""Integration test: full Echo -> PheraSTAR -> 4PL fit pipeline."""
import numpy as np
from lab_data_simulator.simulators.liquid_handler import Echo
from lab_data_simulator.simulators.plate_reader import PheraSTAR
from lab_data_simulator.simulators.calculations import fit_4pl_curve


def test_echo_to_pherastar_pipeline():
    """Full Echo -> PheraSTAR -> 4PL fit pipeline runs without errors."""
    echo = Echo(seed=42)
    compounds = [
        {
            "compound_id": "CMP-001",
            "compound_name": "TestCpd",
            "source_well": "A1",
            "concentration": 10000,
        },
    ]
    picklist = echo.make_dose_response_picklist(
        compounds=compounds,
        n_points=8,
        n_replicates=2,
        seed=42,
    )
    assert not picklist.empty
    assert "Transfer Status" in picklist.columns

    ground_truth = {
        "CMP-001": {"a": 100, "b": 1.2, "c": 0.5, "d": 50000, "noise": 500},
    }
    reader = PheraSTAR(seed=42)
    result_df = reader.run_simulation(
        {
            "mode": "picklist_driven",
            "params": {
                "picklist": picklist,
                "ground_truth": ground_truth,
                "assay_volume_nl": 50000.0,
                "baseline": 100,
                "baseline_noise": 10,
            },
        }
    )
    assert len(result_df) == 384
    assert "Signal" in result_df.columns
    assert (result_df["Signal"] >= 0).all()

    success = picklist[picklist["Transfer Status"] == "Success"]
    well_signal = result_df.set_index("Well")["Signal"]
    matched = success[success["Destination Well"].isin(well_signal.index)].copy()
    concentrations = (
        matched["Source Concentration (µM)"].astype(float)
        * matched["Actual Volume (nL)"].astype(float)
        / 50000.0
    ).tolist()
    signals = well_signal.loc[matched["Destination Well"]].tolist()

    fit = fit_4pl_curve(concentrations, signals)
    assert "ic50" in fit
    assert "r_squared" in fit
