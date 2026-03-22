import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from ...core import Instrument


class PuritySimulator(Instrument):
    """
    Simulates analytical purity results (e.g., from LCMS/HPLC).

    Uses a Beta(50, 2) distribution to model a realistic purity profile
    skewed toward high purity (~95–99.9%), as expected for synthesised
    drug-like compounds after purification.

    Args:
        name: Instrument name.
        seed: Optional random seed for reproducibility.
    """

    def __init__(self, name: str = "Agilent HPLC", seed: Optional[int] = None):
        super().__init__(name)
        self._rng = np.random.default_rng(seed)

    def run_simulation(self, instructions: Dict[str, Any]) -> pd.DataFrame:
        """
        Generate purity results for a list of samples.

        Args:
            instructions: Dict with key 'samples' (list of sample ID strings).

        Returns:
            DataFrame with columns: Sample ID, Retention Time, Area Percent,
            Method.
        """
        samples = instructions.get('samples', [])
        results = []

        for s in samples:
            # Beta(a=50, b=2) is skewed toward high purity (~95%+)
            purity = self._rng.beta(a=50, b=2) * 100
            purity = min(purity, 100.0)

            results.append({
                'Sample ID':      s,
                'Retention Time': self._rng.normal(2.5, 0.1),
                'Area Percent':   round(purity, 2),
                'Method':         'Method A',
            })

        return pd.DataFrame(results)
