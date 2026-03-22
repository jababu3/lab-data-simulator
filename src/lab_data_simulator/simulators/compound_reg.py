from typing import Any
import random
from ..core import Instrument


class SDFGenerator(Instrument):
    """
    Generates SDfiles for compound registration.
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

    def __init__(self, name: str = "SDFGenerator"):
        super().__init__(name)

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

            # Generate random QSAR properties
            mw = round(random.uniform(150.0, 500.0), 2)
            logp = round(random.uniform(-1.0, 5.0), 2)
            tpsa = round(random.uniform(20.0, 140.0), 1)
            hbd = random.randint(0, 5)
            hba = random.randint(1, 10)
            rotatable = random.randint(1, 8)
            purity = round(random.uniform(95.0, 99.9), 1)

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
