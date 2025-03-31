"""
PyCIAT: Python Crop Impact Assessment Tool
========================================

A framework for simulating and analyzing climate change impacts on crop production
using multiple crop models, with advanced features for adaptation assessment,
soil processes, and machine learning integration.

Copyright (c) 2025, PyCIAT Contributors
MIT License
"""

__version__ = "0.1.0"
__author__ = "PyCIAT Contributors"

# Core components
from . import config_loader
from . import utils
from . import climate_processing
from . import analysis
from . import visualization
from . import soil_processing

# Crop model interfaces
from .crop_model_interface import (
    base_interface,
    dssat_interface,
    apsim_interface,
    stics_interface,
    status_codes,
)

# Surrogate model components
from .surrogate_model import (
    feature_engineering,
    model_selection,
    evaluation,
    predict,
)

# Advanced modules for specialized simulations
from . import advanced_modules

# Version information
VERSION_INFO = {
    'major': 0,
    'minor': 1,
    'patch': 0,
    'release': 'final',
}

# Expose key classes/functions at package level
from .config_loader import load_config
from .utils import setup_logging, Timer
from .crop_model_interface.base_interface import CropModelInterface
from .crop_model_interface.status_codes import SimulationStatus

__all__ = [
    # Version info
    '__version__',
    '__author__',
    'VERSION_INFO',
    
    # Core functionality
    'load_config',
    'setup_logging',
    'Timer',
    'CropModelInterface',
    'SimulationStatus',
    
    # Main modules
    'config_loader',
    'utils',
    'climate_processing',
    'analysis',
    'visualization',
    'soil_processing',
    
    # Subpackages
    'crop_model_interface',
    'surrogate_model',
    'advanced_modules',
]
