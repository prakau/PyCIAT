##############################################################################
### File: src/config_loader.py
##############################################################################
"""
Configuration loader and validator for the modeling framework.
Handles loading the YAML config file and validating its contents.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import yaml

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass

def resolve_path(base_dir: str, path: str) -> str:
    """
    Resolves a path that might be relative to base_dir.
    
    Args:
        base_dir: Base directory for resolving relative paths
        path: Path to resolve (absolute or relative to base_dir)
    
    Returns:
        str: Absolute path
    """
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(base_dir, path))

def validate_paths(config: Dict[str, Any]) -> None:
    """
    Validates that critical paths exist or can be created.
    
    Args:
        config: Configuration dictionary
    
    Raises:
        ConfigurationError: If paths are invalid or inaccessible
    """
    base_dir = config.get('base_dir')
    if not base_dir:
        raise ConfigurationError("base_dir must be specified in config")
    
    if not os.path.isabs(base_dir):
        raise ConfigurationError("base_dir must be an absolute path")
    
    if not os.path.exists(base_dir):
        raise ConfigurationError(f"base_dir does not exist: {base_dir}")
    
    # Check executable paths for active crop models
    for model in config.get('crop_models_to_run', []):
        exe_path = config.get('crop_model_configs', {}).get(model, {}).get('executable_path')
        if not exe_path:
            raise ConfigurationError(f"executable_path not specified for model {model}")
        
        full_exe_path = resolve_path(base_dir, exe_path)
        if not os.path.exists(full_exe_path):
            raise ConfigurationError(f"Executable not found for {model}: {full_exe_path}")
        if not os.access(full_exe_path, os.X_OK):
            raise ConfigurationError(f"Executable not executable for {model}: {full_exe_path}")

def validate_climate_config(config: Dict[str, Any]) -> None:
    """
    Validates climate configuration settings.
    
    Args:
        config: Configuration dictionary
    
    Raises:
        ConfigurationError: If climate settings are invalid
    """
    climate = config.get('climate', {})
    if not climate:
        raise ConfigurationError("climate section missing from config")
    
    # Check that at least one source is active
    if not climate.get('active_sources'):
        raise ConfigurationError("No active climate sources specified")
    
    # Validate that specified sources exist in paths
    sources = config.get('paths', {}).get('climate_sources', {})
    for source in climate['active_sources']:
        if source not in sources:
            raise ConfigurationError(f"Climate source '{source}' not defined in paths.climate_sources")

    # Validate time periods
    if not climate.get('historical_period'):
        raise ConfigurationError("historical_period not specified in climate config")
    
    if len(climate['historical_period']) != 2:
        raise ConfigurationError("historical_period must be a list of [start_date, end_date]")

def validate_simulation_config(config: Dict[str, Any]) -> None:
    """
    Validates simulation settings.
    
    Args:
        config: Configuration dictionary
    
    Raises:
        ConfigurationError: If simulation settings are invalid
    """
    sim = config.get('simulation', {})
    if not sim:
        raise ConfigurationError("simulation section missing from config")
    
    # Check required simulation parameters
    if not sim.get('sowing_dates'):
        raise ConfigurationError("No sowing dates specified in simulation config")

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Loads and validates the configuration file.
    
    Args:
        config_path: Path to the YAML configuration file
    
    Returns:
        Dict[str, Any]: Validated configuration dictionary
    
    Raises:
        ConfigurationError: If config is invalid or missing required elements
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if not config:
            raise ConfigurationError("Empty configuration file")
        
        # Validate critical sections
        validate_paths(config)
        validate_climate_config(config)
        validate_simulation_config(config)
        
        # Resolve relative paths to absolute paths
        config = _resolve_all_paths(config)
        
        return config
    
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Error parsing YAML file: {e}")
    except FileNotFoundError:
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    except Exception as e:
        raise ConfigurationError(f"Unexpected error loading config: {e}")

def _resolve_all_paths(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively resolves all paths in the config relative to base_dir.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Dict[str, Any]: Configuration with resolved paths
    """
    base_dir = config['base_dir']
    
    def _resolve_recursive(data: Union[Dict, List, str, Any]) -> Union[Dict, List, str, Any]:
        if isinstance(data, dict):
            return {k: _resolve_recursive(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [_resolve_recursive(item) for item in data]
        elif isinstance(data, str) and any(
            data.endswith(ext) for ext in ['.txt', '.csv', '.shp', '.exe', '.json', '.nc']
        ):
            return resolve_path(base_dir, data)
        return data
    
    return _resolve_recursive(config)

# Optional: Add config schema validation if using JSON Schema
# def validate_config_schema(config: Dict[str, Any]) -> None:
#     """Validates config against JSON schema."""
#     pass
