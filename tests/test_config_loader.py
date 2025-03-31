"""Tests for configuration loading and validation."""

import os
from pathlib import Path
from typing import Dict, Any

import pytest
import yaml

from src.config_loader import load_config, validate_config, ConfigurationError

def test_load_config_valid(temp_config_file: str):
    """Test loading a valid configuration file."""
    config = load_config(temp_config_file)
    
    assert isinstance(config, dict)
    assert 'base_dir' in config
    assert 'paths' in config
    assert 'climate' in config
    assert 'simulation' in config

def test_load_config_missing_file():
    """Test error handling for missing config file."""
    with pytest.raises(ConfigurationError) as exc_info:
        load_config("nonexistent_config.yaml")
    
    assert "Could not find configuration file" in str(exc_info.value)

def test_load_config_invalid_yaml(tmp_path: Path):
    """Test error handling for invalid YAML."""
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text("invalid: yaml: content: [")
    
    with pytest.raises(ConfigurationError) as exc_info:
        load_config(str(config_file))
    
    assert "Error parsing YAML" in str(exc_info.value)

def test_validate_config_complete(test_config: Dict[str, Any]):
    """Test validation of complete configuration."""
    # Should not raise any exceptions
    validate_config(test_config)

def test_validate_config_missing_required(test_config: Dict[str, Any]):
    """Test validation with missing required fields."""
    # Remove required field
    del test_config['paths']
    
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(test_config)
    
    assert "Missing required configuration" in str(exc_info.value)
    assert "paths" in str(exc_info.value)

def test_validate_config_invalid_type(test_config: Dict[str, Any]):
    """Test validation with incorrect type for field."""
    # Set invalid type
    test_config['climate']['lat_range'] = "invalid"
    
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(test_config)
    
    assert "Invalid type for" in str(exc_info.value)
    assert "lat_range" in str(exc_info.value)

def test_validate_config_invalid_range(test_config: Dict[str, Any]):
    """Test validation of numerical ranges."""
    # Set invalid latitude range
    test_config['climate']['lat_range'] = [-100, 100]
    
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(test_config)
    
    assert "Invalid value for" in str(exc_info.value)
    assert "lat_range" in str(exc_info.value)

def test_validate_config_paths(test_config: Dict[str, Any], temp_working_dir: Path):
    """Test validation of path configurations."""
    # Create required directories and files
    for path_key, rel_path in test_config['paths'].items():
        full_path = temp_working_dir / rel_path
        
        # Create parent directory
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create dummy file for files
        if not rel_path.endswith('/'):
            full_path.touch()
    
    # Update paths in config to use temp directory
    test_config['base_dir'] = str(temp_working_dir)
    
    # Should not raise any exceptions
    validate_config(test_config)

def test_validate_config_invalid_paths(test_config: Dict[str, Any]):
    """Test validation with nonexistent paths."""
    test_config['base_dir'] = "/nonexistent/path"
    
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(test_config)
    
    assert "Base directory does not exist" in str(exc_info.value)

def test_validate_config_models(test_config: Dict[str, Any]):
    """Test validation of crop model configurations."""
    # Add invalid model
    test_config['crop_models_to_run'].append('invalid_model')
    
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(test_config)
    
    assert "Invalid crop model" in str(exc_info.value)

def test_validate_config_climate_vars(test_config: Dict[str, Any]):
    """Test validation of climate variables."""
    # Add invalid variable
    test_config['climate']['variables'].append('invalid_var')
    
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(test_config)
    
    assert "Invalid climate variable" in str(exc_info.value)

def test_validate_config_dates(test_config: Dict[str, Any]):
    """Test validation of date configurations."""
    # Set invalid date format
    test_config['climate']['historical_period'][0] = "invalid-date"
    
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(test_config)
    
    assert "Invalid date format" in str(exc_info.value)

def test_validate_config_period_order(test_config: Dict[str, Any]):
    """Test validation of period ordering."""
    # Swap period dates
    test_config['climate']['historical_period'].reverse()
    
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(test_config)
    
    assert "End date must be after start date" in str(exc_info.value)

def test_load_and_validate_config(temp_working_dir: Path, test_config: Dict[str, Any]):
    """Test complete config loading and validation process."""
    # Create config file
    config_file = temp_working_dir / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.safe_dump(test_config, f)
    
    # Create required directories and files
    for path_key, rel_path in test_config['paths'].items():
        full_path = temp_working_dir / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if not rel_path.endswith('/'):
            full_path.touch()
    
    # Update base directory
    test_config['base_dir'] = str(temp_working_dir)
    
    # Write updated config
    with open(config_file, 'w') as f:
        yaml.safe_dump(test_config, f)
    
    # Load and validate
    config = load_config(str(config_file))
    assert config['base_dir'] == str(temp_working_dir)
    assert all(Path(config['paths'][k]).exists() for k in config['paths'])
