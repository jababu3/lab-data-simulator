import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from ...core import Instrument


class SPRSimulator(Instrument):
    """
    Simulates Surface Plasmon Resonance (SPR) results (e.g., Biacore).

    Generates realistic kinetic binding parameters (ka, kd, KD) for a list of
    sample IDs. Parameter ranges reflect typical small-molecule binding assays.

    Args:
        name: Instrument name.
        seed: Optional random seed for reproducibility.
    """

    def __init__(self, name: str = "Biacore 8k", seed: Optional[int] = None):
        super().__init__(name)
        self._rng = np.random.default_rng(seed)

    def run_simulation(self, instructions: Dict[str, Any]) -> pd.DataFrame:
        """
        Generate kinetic binding data (ka, kd, KD, Rmax, Chi²).

        Kinetic parameter ranges:
          ka  : 1e4 – 1e6 M⁻¹s⁻¹  (association rate)
          kd  : 1e-4 – 1e-2 s⁻¹   (dissociation rate)
          KD  : derived as kd / ka (equilibrium dissociation constant)
          Rmax: 30 – 100 RU        (maximum response units)
          Chi²: 0.1 – 2.0          (fit quality; <2 indicates good fit)

        Args:
            instructions: Dict with key 'samples' (list of sample ID strings).

        Returns:
            DataFrame with columns: Sample ID, ka (1/Ms), kd (1/s), KD (M),
            Rmax, Chi2.
        """
        samples = instructions.get('samples', [])
        results = []

        for s in samples:
            ka = self._rng.uniform(1e4, 1e6)   # association rate 1/Ms
            kd = self._rng.uniform(1e-4, 1e-2)  # dissociation rate 1/s
            KD = kd / ka                          # equilibrium constant M

            results.append({
                'Sample ID': s,
                'ka (1/Ms)': ka,
                'kd (1/s)':  kd,
                'KD (M)':    KD,
                'Rmax':      self._rng.uniform(30, 100),
                'Chi2':      self._rng.uniform(0.1, 2.0),
            })

        return pd.DataFrame(results)
