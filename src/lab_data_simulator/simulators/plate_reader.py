import io
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..core import Instrument
from .calculations import four_parameter_logistic


class PlateReader(Instrument):
    """
    Simulates a Plate Reader (e.g., PheraSTAR, Envision).
    Supports 96, 384, and 1536 well formats.
    """

    PLATE_FORMATS = {
        96:   (8,  12),
        384:  (16, 24),
        1536: (32, 48),
    }

    # Subclasses may override these to carry instrument-specific defaults
    INSTRUMENT_MODEL    = 'PlateReader'
    FIRMWARE_VERSION    = '1.0'
    SOFTWARE_VERSION    = 'Reader Control 3.0'
    SERIAL_NUMBER       = 'SIM-000000'
    DETECTION_MODE      = 'Fluorescence Intensity'
    EXCITATION_NM       = 'N/A'
    EMISSION_NM         = 'N/A'
    FOCAL_HEIGHT_MM     = 'N/A'
    GAIN                = 'N/A'
    NUMBER_OF_FLASHES   = 'N/A'
    SHAKING_DURATION_S  = 0
    SHAKING_MODE        = 'None'

    def __init__(self, name: str, plate_format: int = 384,
                 config: Optional[Dict[str, Any]] = None,
                 seed: Optional[int] = None):
        super().__init__(name, config)
        if plate_format not in self.PLATE_FORMATS:
            raise ValueError(
                f"Unsupported plate format: {plate_format}. "
                f"Must be one of {list(self.PLATE_FORMATS.keys())}"
            )
        self.plate_format = plate_format
        self.rows, self.cols = self.PLATE_FORMATS[plate_format]
        self._rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_well_ids(self) -> List[str]:
        """Generate well IDs (A01, A02, ... B01 ...)."""
        well_ids = []
        for r in range(self.rows):
            row_char = chr(65 + r) if r < 26 else 'A' + chr(65 + r - 26)
            for c in range(1, self.cols + 1):
                well_ids.append(f"{row_char}{c:02d}")
        return well_ids

    # ------------------------------------------------------------------
    # Core simulation
    # ------------------------------------------------------------------

    def run_simulation(self, instructions: Dict[str, Any]) -> pd.DataFrame:
        """
        Simulate a plate read.

        Args:
            instructions: Dictionary containing:
                - 'mode'   : '4PL_dilution' | 'flat'
                - 'params' : mode-specific parameters (see below)
                - 'plate_id' : optional plate barcode string

        4PL_dilution params:
            start_conc      – starting concentration (µM)
            dilution_factor – serial dilution fold
            curve_params    – dict with keys a, b, c, d  (4PL parameters)
            noise_std       – optional, defaults to 5 % of max signal

        flat params:
            baseline   – mean signal
            noise_std  – standard deviation of noise

        Returns:
            DataFrame with columns ['Well', 'Signal']
        """
        well_ids = self._generate_well_ids()
        mode   = instructions.get('mode', 'flat')
        params = instructions.get('params', {})

        if mode == '4PL_dilution':
            start_conc     = params.get('start_conc', 10.0)
            dilution_factor = params.get('dilution_factor', 3.0)
            curve_params   = params.get('curve_params',
                                        {'a': 0, 'b': 1, 'c': 0.5, 'd': 10000})
            concentrations = []
            for _ in range(self.rows):
                conc = start_conc
                for _ in range(self.cols):
                    concentrations.append(conc)
                    conc /= dilution_factor

            signals = four_parameter_logistic(
                concentrations,
                curve_params['a'], curve_params['b'],
                curve_params['c'], curve_params['d'],
            )
            noise_std = params.get('noise_std', 0.05 * float(np.max(signals)))
            signals   = signals + self._rng.normal(0, noise_std, size=len(signals))

        elif mode == 'flat':
            baseline  = params.get('baseline', 1000)
            noise_std = params.get('noise_std', 50)
            signals   = self._rng.normal(baseline, noise_std, size=len(well_ids))

        elif mode == 'picklist_driven':
            picklist = params.get('picklist')  # pd.DataFrame from Echo
            ground_truth = params.get('ground_truth', {}) # dict: cpd_id -> {'a':X, 'b':X, 'c':X, 'd':X, 'noise':X}
            assay_volume_nl = params.get('assay_volume_nl', 50000.0) # default 50 uL total well volume
            baseline = params.get('baseline', 100)

            # Map wells to concentration and compound
            # Note: handle cases where a well might have multiple transfers (we'll just take the aggregate or first but usually dose-response is 1 transfer per well)
            well_to_signal = {}
            if picklist is not None and not picklist.empty:
                required_cols = {'Destination Well', 'Compound ID',
                                 'Source Concentration (µM)', 'Actual Volume (nL)', 'Transfer Status'}
                missing = required_cols - set(picklist.columns)
                if missing:
                    raise ValueError(f"Picklist is missing required columns: {missing}")
                # Group by destination well just in case there are multiple drops
                # But typically our dose response generator makes 1 row per dest well.
                for _, row in picklist.iterrows():
                    dest_well = row.get('Destination Well')
                    if not dest_well or row.get('Transfer Status', 'Success') != 'Success':
                        continue
                    
                    cpd_id = row.get('Compound ID')
                    src_conc_um = float(row.get('Source Concentration (µM)', 0))
                    actual_vol_nl = float(row.get('Actual Volume (nL)', 0))
                    
                    # Final concentration in well
                    final_conc_um = (src_conc_um * actual_vol_nl) / assay_volume_nl
                    
                    gt = ground_truth.get(cpd_id)
                    if gt:
                        # calculate theoretical signal
                        signal = four_parameter_logistic(
                            final_conc_um, gt['a'], gt['b'], gt['c'], gt['d']
                        )
                        noise = self._rng.normal(0, gt.get('noise', 100))
                        well_to_signal[dest_well] = float(signal + noise)

            signals = []
            for wid in well_ids:
                if wid in well_to_signal:
                    signals.append(max(0, well_to_signal[wid]))
                else:
                    # Empty well or no successful transfer -> baseline
                    noise = self._rng.normal(0, params.get('baseline_noise', 10))
                    signals.append(max(0, baseline + noise))
                    
            signals = np.array(signals)

        else:
            signals = np.zeros(len(well_ids))

        return pd.DataFrame({'Well': well_ids, 'Signal': signals})

    # ------------------------------------------------------------------
    # Output formats
    # ------------------------------------------------------------------

    def to_block_format(self, df: pd.DataFrame,
                        value_col: str = 'Signal') -> pd.DataFrame:
        """
        Pivot a flat Well/Signal DataFrame into a plate block layout.

        Returns a DataFrame where:
          - Index   = row letters (A, B, C, ...)
          - Columns = column numbers (1, 2, 3, ...)
          - Values  = the signal (or other value_col)
        """
        df = df.copy()
        df['_row'] = df['Well'].str.extract(r'^([A-Z]{1,2})')
        df['_col'] = df['Well'].str.extract(r'(\d+)$').astype(int)
        block = df.pivot(index='_row', columns='_col', values=value_col)
        block.index.name   = 'Row'
        block.columns.name = 'Column'
        return block

    def to_report(
        self,
        df: pd.DataFrame,
        *,
        include_header: bool = True,
        protocol_name: str   = 'Unnamed Protocol',
        assay_name: str      = 'Unnamed Assay',
        plate_id: str        = 'PLATE_001',
        operator: str        = 'Operator',
        target_temp_c: float = 25.0,
        measurement_mode: Optional[str] = None,
        excitation_nm: Optional[str]    = None,
        emission_nm: Optional[str]      = None,
        gain: Optional[str]             = None,
        n_flashes: Optional[str]        = None,
        output_path: Optional[str]      = None,
    ) -> str:
        """
        Generate a realistic BMG LABTECH / PheraSTAR-style full-header report.

        The report contains:
          1. Instrument & run metadata header (key: value lines)
          2. Blank separator line
          3. Data block (plate grid layout)

        Parameters
        ----------
        df              : DataFrame from run_simulation()
        protocol_name   : Name of the BMG protocol used
        assay_name      : Assay / experiment label
        plate_id        : Plate barcode / ID
        operator        : Operator name
        target_temp_c   : Target incubation temperature (°C)
        measurement_mode: Overrides class default detection mode
        excitation_nm   : Overrides class default excitation wavelength
        emission_nm     : Overrides class default emission wavelength
        gain            : Overrides class default gain
        n_flashes       : Overrides class default number of flashes
        output_path     : If given, write the report to this file path

        Returns
        -------
        str : The full report as a string
        """
        now = datetime.now()
        rows, cols = self.PLATE_FORMATS[self.plate_format]

        # Override instrument defaults with any per-call values
        det_mode = measurement_mode or self.DETECTION_MODE
        exc_nm   = excitation_nm    or self.EXCITATION_NM
        emi_nm   = emission_nm      or self.EMISSION_NM
        gain_val = gain             or self.GAIN
        flashes  = n_flashes        or self.NUMBER_OF_FLASHES

        block = self.to_block_format(df)

        lines: List[str] = []

        if include_header:
            # ── Section 1: Instrument information ──────────────────────────
            lines += [
                'BMG LABTECH - Reader Data File',
                '',
                'Instrument Information',
                f'Reader Model:              {self.INSTRUMENT_MODEL}',
                f'Serial Number:             {self.SERIAL_NUMBER}',
                f'Firmware Version:          {self.FIRMWARE_VERSION}',
                f'Software Version:          {self.SOFTWARE_VERSION}',
                '',
            ]

            # ── Section 2: Run / assay information ─────────────────────────
            lines += [
                'Run Information',
                f'Protocol Name:             {protocol_name}',
                f'Assay Name:                {assay_name}',
                f'Plate ID:                  {plate_id}',
                f'Plate Type:                {self.plate_format}-well',
                f'Operator:                  {operator}',
                f'Date:                      {now.strftime("%Y-%m-%d")}',
                f'Time:                      {now.strftime("%H:%M:%S")}',
                f'Target Temperature (°C):   {target_temp_c:.1f}',
                f'No. of Wells:              {rows * cols}',
                '',
            ]

            # ── Section 3: Measurement settings ────────────────────────────
            lines += [
                'Measurement Settings',
                f'Detection Mode:            {det_mode}',
                f'Excitation (nm):           {exc_nm}',
                f'Emission (nm):             {emi_nm}',
                f'Focal Height (mm):         {self.FOCAL_HEIGHT_MM}',
                f'Gain:                      {gain_val}',
                f'Number of Flashes:         {flashes}',
                f'Shaking Duration (s):      {self.SHAKING_DURATION_S}',
                f'Shaking Mode:              {self.SHAKING_MODE}',
                '',
            ]

            # ── Section 4: Data block ───────────────────────────────────────
            lines += ['Data']

        # Build column header row: blank label cell + column numbers
        col_nums   = [str(c) for c in block.columns]
        header_row = '\t'.join([''] + col_nums)
        lines.append(header_row)

        for row_label, row_data in block.iterrows():
            vals = '\t'.join(f'{v:.2f}' for v in row_data)
            lines.append(f'{row_label}\t{vals}')

        lines.append('')   # trailing newline

        report = '\n'.join(lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as fh:
                fh.write(report)

        return report


# ---------------------------------------------------------------------------
# PheraSTAR FSX
# ---------------------------------------------------------------------------

class PheraSTAR(PlateReader):
    """
    Simulates a BMG LABTECH PHERAstar FSX multimode plate reader.
    Defaults to 384-well format with HTRF-compatible instrument settings.
    """
    INSTRUMENT_MODEL   = 'PHERAstar FSX'
    FIRMWARE_VERSION   = '5.11 R4'
    SOFTWARE_VERSION   = 'MARS 3.32 R2'
    SERIAL_NUMBER      = 'FSX0000001'
    DETECTION_MODE     = 'Fluorescence Intensity'
    EXCITATION_NM      = '485'
    EMISSION_NM        = '520'
    FOCAL_HEIGHT_MM    = '7.3'
    GAIN               = '1200'
    NUMBER_OF_FLASHES  = '100'
    SHAKING_DURATION_S = 5
    SHAKING_MODE       = 'Double orbital'

    def __init__(self, name: str = 'PHERAstar FSX', plate_format: int = 384,
                 seed: Optional[int] = None):
        super().__init__(name, plate_format, seed=seed)


# ---------------------------------------------------------------------------
# Envision
# ---------------------------------------------------------------------------

class Envision(PlateReader):
    """Simulates a PerkinElmer Envision multimode plate reader."""
    INSTRUMENT_MODEL  = 'EnVision'
    FIRMWARE_VERSION  = '1.14'
    SOFTWARE_VERSION  = 'EnVision Manager 1.14'
    SERIAL_NUMBER     = 'ENV0000001'
    DETECTION_MODE    = 'Fluorescence Intensity'
    EXCITATION_NM     = '490'
    EMISSION_NM       = '535'
    FOCAL_HEIGHT_MM   = '8.0'
    GAIN              = '100'
    NUMBER_OF_FLASHES = '50'

    def __init__(self, name: str = 'Envision', plate_format: int = 384,
                 seed: Optional[int] = None):
        super().__init__(name, plate_format, seed=seed)

    def to_report(
        self,
        df: pd.DataFrame,
        *,
        include_header: bool = True,
        protocol_name: str   = 'Unnamed Protocol',
        assay_name: str      = 'Unnamed Assay',
        plate_id: str        = 'PLATE_001',
        operator: str        = 'Operator',
        target_temp_c: float = 25.0,
        measurement_mode: Optional[str] = None,
        excitation_nm: Optional[str]    = None,
        emission_nm: Optional[str]      = None,
        gain: Optional[str]             = None,
        n_flashes: Optional[str]        = None,
        output_path: Optional[str]      = None,
    ) -> str:
        """
        Generate a PerkinElmer Envision style format.
        
        The report contains:
          1. Plate information header
          2. Results data block (plate grid layout) mapped as comma-separated values.
        """
        now = datetime.now()
        block = self.to_block_format(df)
        lines: List[str] = []

        if include_header:
            lines += [
                "Plate information",
                f"Barcode,{plate_id}",
                f"Measurement date,{now.strftime('%m/%d/%Y %I:%M:%S %p')}",
                f"User,{operator}",
                f"Protocol,{protocol_name}",
                f"Assay,{assay_name}",
                f"Measurement Mode,{measurement_mode or self.DETECTION_MODE}",
                f"Excitation,{excitation_nm or self.EXCITATION_NM}",
                f"Emission,{emission_nm or self.EMISSION_NM}",
                f"Gain,{gain or self.GAIN}",
                f"Flashes,{n_flashes or self.NUMBER_OF_FLASHES}",
                f"Target Temp,{target_temp_c:.1f}",
                ""
            ]

        lines.append("Results")
        
        # Build column header row: blank label cell + column numbers
        col_nums = [str(c) for c in block.columns]
        header_row = ',' + ','.join(col_nums)
        lines.append(header_row)

        for row_label, row_data in block.iterrows():
            vals = ','.join(f'{v:.2f}' for v in row_data)
            lines.append(f'{row_label},{vals}')

        lines.append('')   # trailing newline

        report = '\n'.join(lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as fh:
                fh.write(report)

        return report
