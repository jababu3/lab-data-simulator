from typing import Any, Optional
import numpy as np
from ..core import Instrument


class SDFGenerator(Instrument):
    """
    Generates SDfiles for compound registration.

    Note: QSAR properties (MW, LogP, TPSA, etc.) are synthetic random values,
    not computed from molecular structure. All compounds share a benzene scaffold.
    """

    # Simple benzene template for fallback
    # Starts with header, then counts line, then atom block, bond block...
    # This is a very minimal valid molblock.
    BENZENE_MOLBLOCK = (
        "\n"
        "  Simulated\n"
        "\n"
        "  6  6  0  0  0  0  0  0  0  0999 V2000\n"
        "    0.0000    1.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\n"
        "    0.8660    0.5000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\n"
        "    0.8660   -0.5000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\n"
        "    0.0000   -1.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\n"
        "   -0.8660   -0.5000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\n"
        "   -0.8660    0.5000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\n"
        "  1  2  2  0\n"
        "  2  3  1  0\n"
        "  3  4  2  0\n"
        "  4  5  1  0\n"
        "  5  6  2  0\n"
        "  6  1  1  0\n"
        "M  END"
    )

    def __init__(self, name: str = "SDFGenerator", seed: Optional[int] = None):
        super().__init__(name)
        self._rng = np.random.default_rng(seed)

    def run_simulation(self, instructions: dict[str, Any]) -> str:
        """
        Generate an SDFile content string.

        Args:
            instructions:
                - 'num_compounds': int
                - 'prefix': str (e.g. 'CHEM')
                - 'start_id': int (e.g. 1000)

        Returns:
            str: Content of the .sdf file
        """
        num_compounds = instructions.get("num_compounds", 10)
        prefix = instructions.get("prefix", "CHEM")
        start_id = instructions.get("start_id", 1000)

        sdf_content = []

        for i in range(num_compounds):
            cid = f"{prefix}{start_id + i}"
            molblock = self.BENZENE_MOLBLOCK

            # Generate synthetic QSAR properties (not computed from structure)
            mw = round(self._rng.uniform(150.0, 500.0), 2)
            logp = round(self._rng.uniform(-1.0, 5.0), 2)
            tpsa = round(self._rng.uniform(20.0, 140.0), 1)
            hbd = int(self._rng.integers(0, 6))
            hba = int(self._rng.integers(1, 11))
            rotatable = int(self._rng.integers(1, 9))
            purity = round(self._rng.uniform(95.0, 99.9), 1)

            record = [
                molblock,
                ">  <ID>",
                f"{cid}",
                "",
                ">  <MolecularWeight>",
                f"{mw}",
                "",
                ">  <LogP>",
                f"{logp}",
                "",
                ">  <TPSA>",
                f"{tpsa}",
                "",
                ">  <HBD>",
                f"{hbd}",
                "",
                ">  <HBA>",
                f"{hba}",
                "",
                ">  <RotatableBonds>",
                f"{rotatable}",
                "",
                ">  <Purity>",
                f"{purity}",
                "",
                "$$$$",
            ]
            sdf_content.append("\n".join(record))

        return "\n".join(sdf_content)
