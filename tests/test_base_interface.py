"""Tests for the base crop model interface."""

import os
from pathlib import Path
from typing import Dict, Any

import pytest

from src.crop_model_interface.base_interface import BaseCropModelInterface
from src.crop_model_interface.status_codes import SimulationStatus

class TestModelInterface(BaseCropModelInterface):
    """Test implementation of base interface."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_name = "test_model"
    
    def prepare_simulation(self, sim_id: str, params: Dict[str, Any]) -> bool:
        """Test implementation of prepare_simulation."""
        self.write_status(sim_id, SimulationStatus.READY_TO_RUN)
        return True
    
    def run_simulation(self, sim_id: str) -> bool:
        """Test implementation of run_simulation."""
        self.write_status(sim_id, SimulationStatus.SUCCESS)
        return True
    
    def process_outputs(self, sim_id: str) -> Dict[str, Any]:
        """Test implementation of process_outputs."""
        return {"yield": 5000.0, "biomass": 12000.0}

def test_interface_initialization(test_config: Dict[str, Any]):
    """Test base interface initialization."""
    interface = TestModelInterface(test_config)
    
    assert interface.model_name == "test_model"
    assert interface.config == test_config
    assert isinstance(interface.get_status_file(), Path)

def test_status_file_operations(test_config: Dict[str, Any], temp_working_dir: Path):
    """Test status file operations."""
    interface = TestModelInterface(test_config)
    sim_id = "test_sim_001"
    
    # Test status writing
    interface.write_status(
        sim_id,
        SimulationStatus.READY_TO_RUN,
        message="Test status"
    )
    
    # Test status reading
    status = interface.get_simulation_status(sim_id)
    assert status['status'] == SimulationStatus.READY_TO_RUN
    assert status['message'] == "Test status"
    assert 'start_time' in status
    assert status['simulation_id'] == sim_id

def test_simulation_workflow(test_config: Dict[str, Any], temp_working_dir: Path):
    """Test complete simulation workflow."""
    interface = TestModelInterface(test_config)
    sim_id = "test_sim_002"
    params = {
        "weather_file": "weather.csv",
        "soil_file": "soil.sol",
        "crop": "maize",
        "planting_date": "2020-06-15"
    }
    
    # Test preparation
    assert interface.prepare_simulation(sim_id, params)
    status = interface.get_simulation_status(sim_id)
    assert status['status'] == SimulationStatus.READY_TO_RUN
    
    # Test running
    assert interface.run_simulation(sim_id)
    status = interface.get_simulation_status(sim_id)
    assert status['status'] == SimulationStatus.SUCCESS
    
    # Test output processing
    outputs = interface.process_outputs(sim_id)
    assert isinstance(outputs, dict)
    assert "yield" in outputs
    assert "biomass" in outputs

def test_error_handling(test_config: Dict[str, Any]):
    """Test error handling in base interface."""
    interface = TestModelInterface(test_config)
    
    # Test invalid simulation ID
    with pytest.raises(ValueError):
        interface.get_simulation_status("")
    
    # Test invalid status code
    with pytest.raises(ValueError):
        interface.write_status("test_sim", "INVALID_STATUS")

def test_status_tracking(test_config: Dict[str, Any], temp_working_dir: Path):
    """Test detailed status tracking functionality."""
    interface = TestModelInterface(test_config)
    sim_id = "test_sim_003"
    
    # Test initial status
    interface.write_status(sim_id, SimulationStatus.INITIALIZING)
    status = interface.get_simulation_status(sim_id)
    assert status['status'] == SimulationStatus.INITIALIZING
    assert status['end_time'] is None
    
    # Test status update
    interface.write_status(
        sim_id,
        SimulationStatus.RUNNING,
        message="Processing simulation"
    )
    status = interface.get_simulation_status(sim_id)
    assert status['status'] == SimulationStatus.RUNNING
    assert status['message'] == "Processing simulation"
    assert status['start_time'] is not None
    
    # Test final status
    interface.write_status(
        sim_id,
        SimulationStatus.SUCCESS,
        message="Completed successfully"
    )
    status = interface.get_simulation_status(sim_id)
    assert status['status'] == SimulationStatus.SUCCESS
    assert status['end_time'] is not None

def test_multiple_simulations(test_config: Dict[str, Any], temp_working_dir: Path):
    """Test handling multiple simultaneous simulations."""
    interface = TestModelInterface(test_config)
    sim_ids = [f"test_sim_{i:03d}" for i in range(5)]
    
    # Initialize all simulations
    for sim_id in sim_ids:
        interface.write_status(sim_id, SimulationStatus.INITIALIZING)
    
    # Check all simulations are tracked
    for sim_id in sim_ids:
        status = interface.get_simulation_status(sim_id)
        assert status['simulation_id'] == sim_id
        assert status['status'] == SimulationStatus.INITIALIZING
    
    # Update statuses
    for i, sim_id in enumerate(sim_ids):
        if i % 2 == 0:
            interface.write_status(sim_id, SimulationStatus.SUCCESS)
        else:
            interface.write_status(sim_id, SimulationStatus.FAILED)
    
    # Verify final statuses
    for i, sim_id in enumerate(sim_ids):
        status = interface.get_simulation_status(sim_id)
        expected_status = (
            SimulationStatus.SUCCESS if i % 2 == 0
            else SimulationStatus.FAILED
        )
        assert status['status'] == expected_status

def test_simulation_timing(test_config: Dict[str, Any], temp_working_dir: Path):
    """Test simulation timing tracking."""
    interface = TestModelInterface(test_config)
    sim_id = "test_sim_004"
    
    # Start simulation
    interface.write_status(sim_id, SimulationStatus.RUNNING)
    start_status = interface.get_simulation_status(sim_id)
    
    # Complete simulation
    interface.write_status(sim_id, SimulationStatus.SUCCESS)
    end_status = interface.get_simulation_status(sim_id)
    
    # Verify timing
    assert start_status['start_time'] is not None
    assert end_status['end_time'] is not None
    assert end_status['end_time'] >= start_status['start_time']
