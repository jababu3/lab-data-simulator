import pandas as pd
import numpy as np
from typing import Dict, Any, List
from ...core import Instrument

class PuritySimulator(Instrument):
    """
    Simulates analytical purity results (e.g. from LCMS/HPLC).
    """
    def __init__(self, name: str = "Agilent HPLC"):
        super().__init__(name)
        
    def run_simulation(self, instructions: Dict[str, Any]) -> pd.DataFrame:
        """
        Generate a list of samples with purity values.
        """
        samples = instructions.get('samples', [])
        results = []
        
        for s in samples:
            # Simulate high purity usually
            purity = np.random.beta(a=50, b=2) * 100 
            purity = min(purity, 100.0)
            
            results.append({
                'Sample ID': s,
                'Retention Time': np.random.normal(2.5, 0.1),
                'Area Percent': round(purity, 2),
                'Method': 'Method A'
            })
            
        return pd.DataFrame(results)
