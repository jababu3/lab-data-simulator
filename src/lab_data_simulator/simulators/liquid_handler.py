import pandas as pd
import numpy as np
from typing import Any, Optional
from ..core import Instrument

# ---------------------------------------------------------------------------
# Echo acoustic dispensing constants
# ---------------------------------------------------------------------------
ECHO_MIN_VOL_NL = 25  # Minimum dispense volume (nL)
ECHO_MAX_VOL_NL = 10_000  # Maximum dispense volume (nL)
ECHO_DROPLET_NL = 2.5  # Droplet size – all volumes must be multiples of 2.5 nL


def _round_to_droplet(volume_nl: float) -> float:
    """Round a volume to the nearest 2.5 nL droplet."""
    return round(round(volume_nl / ECHO_DROPLET_NL) * ECHO_DROPLET_NL, 4)


# ---------------------------------------------------------------------------
# Base LiquidHandler
# ---------------------------------------------------------------------------


class LiquidHandler(Instrument):
    """
    Simulates a Liquid Handler (e.g., Echo, Hamilton, Tecan).
    Generates transfer logs (picklists) based on instructions.
    """

    def __init__(self, name: str, config: Optional[dict[str, Any]] = None):
        super().__init__(name, config)

    def run_simulation(self, instructions: dict[str, Any]) -> pd.DataFrame:
        """
        Simulate a liquid transfer process.

        Args:
            instructions: Dictionary containing:
                - 'source_plate': ID of source plate
                - 'dest_plate': ID of destination plate
                - 'transfers': List of dicts with keys:
                    'source_well', 'dest_well', 'volume'
                    (optional) 'liquid_class', 'compound_id', 'compound_name'

        Returns:
            DataFrame representing the Transfer Log / Picklist
        """
        transfers = instructions.get("transfers", [])
        source_plate = instructions.get("source_plate", "Source1")
        dest_plate = instructions.get("dest_plate", "Dest1")

        log_data = []
        for t in transfers:
            log_data.append(
                {
                    "Source Plate Name": source_plate,
                    "Source Well": t.get("source_well", ""),
                    "Destination Plate Name": dest_plate,
                    "Destination Well": t.get("dest_well", ""),
                    "Transfer Volume": t.get("volume", 0),
                    "Liquid Class": t.get("liquid_class", "Default"),
                }
            )

        return pd.DataFrame(log_data)


# ---------------------------------------------------------------------------
# Echo Acoustic Liquid Handler
# ---------------------------------------------------------------------------

# Probability weights for each failure type (success is handled separately)
_FAILURE_TYPES = [
    "Insufficient Fluid",
    "Fluid Thickness Error",
    "Well Geometry Error",
    "No Fluid",
]

_FAILURE_WEIGHTS = [0.50, 0.25, 0.15, 0.10]  # relative weights among failures


class Echo(LiquidHandler):
    """
    Simulates a Labcyte/Beckman Coulter Echo Acoustic Liquid Handler.

    Generates a realistic Echo transfer (survey) file with:
    - Multi-compound picklist columns (Compound ID, Compound Name, Concentration)
    - Actual vs. requested volume columns
    - Per-transfer status ('Success', 'Insufficient Fluid', etc.)
    - Droplet-quantised volumes (multiples of 2.5 nL)
    - Optional simulated well-level failures

    Instructions dict keys
    ----------------------
    source_plate : str
        Source plate barcode / name.
    dest_plate : str
        Destination plate barcode / name.
    transfers : list[dict]
        Each entry may contain:
            source_well     – e.g. 'A1'  (required)
            dest_well       – e.g. 'B3'  (required)
            volume          – requested volume in nL (required)
            compound_id     – e.g. 'CMP-00042'
            compound_name   – e.g. 'Staurosporine'
            concentration   – source concentration in µM
            liquid_class    – overrides default liquid class
    failure_rate : float
        Fraction of transfers that result in a failure (0.0–1.0). Default 0.05.
    volume_cv : float
        Coefficient of variation for actual vs. requested volume noise. Default 0.03.
    seed : int | None
        Random seed for reproducibility.
    """

    DEFAULT_LIQUID_CLASS = (
        "AQ_BP"  # Standard Echo liquid class for aqueous, backpressure
    )

    def __init__(self, name: str = "Echo 655", seed: Optional[int] = None):
        super().__init__(name)
        self._rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_simulation(self, instructions: dict[str, Any]) -> pd.DataFrame:
        """Return a DataFrame that mirrors a real Echo survey/transfer log."""
        source_plate = instructions.get("source_plate", "Source[1]")
        dest_plate = instructions.get("dest_plate", "Destination[1]")
        transfers = instructions.get("transfers", [])
        failure_rate = float(instructions.get("failure_rate", 0.05))
        volume_cv = float(instructions.get("volume_cv", 0.03))
        seed_override = instructions.get("seed")

        if not 0.0 <= failure_rate <= 1.0:
            raise ValueError(
                f"failure_rate must be between 0.0 and 1.0, got {failure_rate}"
            )
        if volume_cv < 0.0:
            raise ValueError(f"volume_cv must be non-negative, got {volume_cv}")

        rng = (
            np.random.default_rng(seed_override)
            if seed_override is not None
            else self._rng
        )

        rows = []
        for t in transfers:
            req_vol = float(t.get("volume", 100))
            clamped = float(np.clip(req_vol, ECHO_MIN_VOL_NL, ECHO_MAX_VOL_NL))
            requested_vol = _round_to_droplet(clamped)

            # Determine transfer outcome
            failed = rng.random() < failure_rate
            if failed:
                status = rng.choice(_FAILURE_TYPES, p=_FAILURE_WEIGHTS)
                # Partial or zero actual transfer depending on error type
                actual_vol = (
                    0.0
                    if status in ("No Fluid", "Well Geometry Error")
                    else _round_to_droplet(requested_vol * rng.uniform(0, 0.6))
                )
            else:
                status = "Success"
                # Add small Gaussian noise to simulate acoustic variability
                noise = rng.normal(1.0, volume_cv)
                actual_vol = _round_to_droplet(
                    float(
                        np.clip(requested_vol * noise, ECHO_MIN_VOL_NL, ECHO_MAX_VOL_NL)
                    )
                )

            rows.append(
                {
                    "Source Plate Name": source_plate,
                    "Source Well": t.get("source_well", ""),
                    "Destination Plate Name": dest_plate,
                    "Destination Well": t.get("dest_well", ""),
                    "Compound ID": t.get("compound_id", ""),
                    "Compound Name": t.get("compound_name", ""),
                    "Source Concentration (µM)": t.get("concentration", ""),
                    "Liquid Class": t.get("liquid_class", self.DEFAULT_LIQUID_CLASS),
                    "Requested Volume (nL)": requested_vol,
                    "Actual Volume (nL)": actual_vol,
                    "Transfer Status": status,
                }
            )

        df = pd.DataFrame(rows)
        return df

    # ------------------------------------------------------------------
    # Convenience factory: build a dose-response picklist automatically
    # ------------------------------------------------------------------

    def make_dose_response_picklist(
        self,
        compounds: list[dict[str, Any]],
        source_plate: str = "CPD_SRC[1]",
        dest_plate: str = "ASSAY_DEST[1]",
        top_vol_nl: float = 250.0,
        dilution_factor: float = 3.0,
        n_points: int = 8,
        n_replicates: int = 2,
        failure_rate: float = 0.05,
        volume_cv: float = 0.03,
        seed: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Build a realistic dose-response picklist for one or more compounds.

        Each compound is dispensed across `n_points` dilution steps starting
        at `top_vol_nl` nL, with `n_replicates` replicates per point.

        Parameters
        ----------
        compounds : list[dict]
            Each dict should have: 'compound_id', 'compound_name',
            'source_well', 'concentration' (µM).
        source_plate : str
        dest_plate : str
        top_vol_nl : float
            Volume at the top concentration step (nL).
        dilution_factor : float
            Serial dilution fold (e.g. 3 → 3-fold dilution).
        n_points : int
            Number of concentration points.
        n_replicates : int
            Replicates per concentration point.
        failure_rate : float
        volume_cv : float
        seed : int | None

        Returns
        -------
        pd.DataFrame
        """
        # Seed is now passed safely through instructions without changing the instance state.

        # Pre-compute destination wells (row-major across a 384-well plate)
        def _well(idx: int) -> str:
            row = chr(ord("A") + (idx // 24))
            col = (idx % 24) + 1
            return f"{row}{col}"

        transfers = []
        well_cursor = 0

        for cpd in compounds:
            for pt in range(n_points):
                vol = _round_to_droplet(top_vol_nl / (dilution_factor**pt))
                vol = float(np.clip(vol, ECHO_MIN_VOL_NL, ECHO_MAX_VOL_NL))
                for _ in range(n_replicates):
                    transfers.append(
                        {
                            "source_well": cpd.get("source_well", "A1"),
                            "dest_well": _well(well_cursor),
                            "volume": vol,
                            "compound_id": cpd.get("compound_id", ""),
                            "compound_name": cpd.get("compound_name", ""),
                            "concentration": cpd.get("concentration", ""),
                        }
                    )
                    well_cursor += 1

        instructions = {
            "source_plate": source_plate,
            "dest_plate": dest_plate,
            "transfers": transfers,
            "failure_rate": failure_rate,
            "volume_cv": volume_cv,
            "seed": seed,
        }
        return self.run_simulation(instructions)


# ---------------------------------------------------------------------------
# Hamilton & Tecan stubs
# ---------------------------------------------------------------------------


class Hamilton(LiquidHandler):
    """Tip-based Liquid Handler (Hamilton STAR/Vantage)."""

    pass


class Tecan(LiquidHandler):
    """Tip-based Liquid Handler (Tecan Evo/Fluent)."""

    pass
