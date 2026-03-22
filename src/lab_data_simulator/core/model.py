from abc import ABC, abstractmethod
from typing import Any, Optional
import pandas as pd


class Instrument(ABC):
    """
    Abstract base class for all laboratory instruments.

    This class defines the common interface that all specific instruments
    (PlateReader, LiquidHandler, etc.) must implement.
    """

    def __init__(self, name: str, config: Optional[dict[str, Any]] = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    def run_simulation(self, instructions: Any) -> Any:
        """
        Run a simulation based on the provided instructions.

        Args:
            instructions: Input parameters defining the experiment (e.g. plate layout, settings)

        Returns:
            The simulated result (e.g., a DataFrame, a file path, or a result object).
        """
        pass


class DataGenerator(ABC):
    """
    Abstract base class for math/signal generators.

    Generators are responsible for creating the raw values (e.g., fluorescence units)
    based on underlying biological or physical models (e.g., 4-parameter logistic curve).
    """

    @abstractmethod
    def generate(self, input_values: Any, params: dict[str, Any]) -> Any:
        """
        Generate simulated data values.

        Args:
            input_values: The independent variable (e.g., concentration).
            params: Parameters for the model (e.g., Hill slope, Top, Bottom).

        Returns:
            Simulated signal/readout.
        """
        pass
