import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from ...core import Instrument


class HCISimulator(Instrument):
    """
    Simulates High Content Imaging (HCI) results (e.g., PerkinElmer Operetta).

    Generates per-well image analysis features including cell count, nuclear
    intensity, and nuclear area.

    Args:
        name: Instrument name.
        seed: Optional random seed for reproducibility.
    """

    def __init__(self, name: str = "Operetta CLS", seed: Optional[int] = None):
        super().__init__(name)
        self._rng = np.random.default_rng(seed)

    def run_simulation(self, instructions: Dict[str, Any]) -> pd.DataFrame:
        """
        Generate image analysis features for a list of samples.

        Args:
            instructions: Dict with key 'samples' (list of sample ID strings).

        Returns:
            DataFrame with columns: Sample ID, Well Region, Cell Count,
            Mean Intensity_Nuclei, Mean Area_Nuclei.
        """
        samples = instructions.get('samples', [])
        results = []

        for s in samples:
            # Clamp to zero — normal distribution can produce negatives
            cell_count = max(0, int(self._rng.normal(1000, 200)))
            intensity  = self._rng.normal(500, 100)   # mean nuclear intensity
            area       = self._rng.normal(200, 20)     # mean nuclear area (µm²)

            results.append({
                'Sample ID':             s,
                'Well Region':           'Center',
                'Cell Count':            cell_count,
                'Mean Intensity_Nuclei': f"{intensity:.2f}",
                'Mean Area_Nuclei':      f"{area:.2f}",
            })

        return pd.DataFrame(results)
