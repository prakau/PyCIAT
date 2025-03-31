##############################################################################
### File: src/crop_model_interface/__init__.py
##############################################################################
"""
Contains the factory function for getting the appropriate crop model interface
and shared enumerations/utilities for model interfaces.
"""

import logging
from typing import Dict, Any, Optional

# Import all potential interfaces
# Using try-except to handle missing implementations gracefully
try:
    from .dssat_interface import DSSATInterface
except ImportError:
    DSSATInterface = None
    logging.getLogger(__name__).debug("Could not import DSSATInterface.")

try:
    from .apsim_interface import APSIMInterface
except ImportError:
    APSIMInterface = None
    logging.getLogger(__name__).debug("Could not import APSIMInterface.")

try:
    from .stics_interface import STICSInterface
except ImportError:
    STICSInterface = None
    logging.getLogger(__name__).debug("Could not import STICSInterface.")

# Import status codes for simulations
try:
    from .status_codes import Status
except ImportError:
    logging.getLogger(__name__).error("Could not import Status enumeration. Simulations may fail.")
    # Create a minimal Status enum as fallback?
    from enum import Enum, auto
    class Status(Enum):
        UNKNOWN_ERROR = auto()
        CONFIG_ERROR = auto()
        SETUP_ERROR = auto()

def get_model_interface(model_name: str) -> Optional[Any]:
    """
    Factory function to return the appropriate model interface class.
    
    Args:
        model_name: String identifier for the model (e.g., 'DSSAT', 'APSIM', 'STICS')
    
    Returns:
        Model interface object or None if interface not found/implemented
    """
    model_interfaces: Dict[str, Any] = {
        'DSSAT': DSSATInterface,
        'APSIM': APSIMInterface,
        'STICS': STICSInterface
    }
    
    interface_class = model_interfaces.get(model_name.upper())
    if interface_class is None:
        logging.getLogger(__name__).error(
            f"No interface implementation found for model '{model_name}'. "
            "Available interfaces: {list(model_interfaces.keys())}"
        )
        return None
    
    try:
        # Initialize the interface
        # Note: Interfaces should handle their own initialization requirements
        interface = interface_class()
        return interface
    except Exception as e:
        logging.getLogger(__name__).error(
            f"Failed to initialize interface for model '{model_name}': {e}"
        )
        return None

# Optionally expose the Status enum at package level
__all__ = ['get_model_interface', 'Status']
