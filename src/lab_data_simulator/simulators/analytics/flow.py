import pandas as pd
import numpy as np
from typing import Any, Optional
from ...core import Instrument


class FlowCytometrySimulator(Instrument):
    """
    Simulates Flow Cytometry results (e.g., BD FACSymphony).

    Generates population-level statistics including cell count, percent
    positive, and mean fluorescence intensity (MFI) for a list of samples.

    Args:
        name: Instrument name.
        seed: Optional random seed for reproducibility.
    """

    def __init__(self, name: str = "BD FACSymphony", seed: Optional[int] = None):
        super().__init__(name)
        self._rng = np.random.default_rng(seed)

    def run_simulation(self, instructions: dict[str, Any]) -> pd.DataFrame:
        """
        Generate population statistics (% Positive, MFI, Count).

        Args:
            instructions: Dict with key 'samples' (list of sample ID strings).

        Returns:
            DataFrame with columns: Sample ID, Population, Count, % Parent,
            MFI.
        """
        samples = instructions.get("samples", [])
        results = []

        for s in samples:
            percent_pos = self._rng.uniform(0, 100)
            # Lognormal distribution is realistic for fluorescence intensity
            mfi = self._rng.lognormal(mean=8, sigma=1)
            # Clamp to zero — normal distribution can produce negatives
            count = max(0, int(self._rng.normal(10000, 500)))

            results.append(
                {
                    "Sample ID": s,
                    "Population": "Lymphocytes/CD3+/CD4+",
                    "Count": count,
                    "% Parent": f"{percent_pos:.1f}",
                    "MFI": f"{mfi:.0f}",
                }
            )

        return pd.DataFrame(results)
