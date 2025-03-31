"""Tests for utility functions."""

import os
import tempfile
from pathlib import Path

import pytest

from src.utils import setup_logging, ensure_dir_exists, Timer


def test_ensure_dir_exists():
    """Test directory creation functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_dir" / "subdir"
        
        # Test creating new directory
        assert not test_dir.exists()
        ensure_dir_exists(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()
        
        # Test with existing directory (should not raise)
        ensure_dir_exists(test_dir)
        assert test_dir.exists()


def test_setup_logging(tmp_path):
    """Test logging setup functionality."""
    log_file = tmp_path / "test.log"
    
    # Test with file logging
    logger = setup_logging(log_file=str(log_file), level="INFO")
    assert logger is not None
    assert log_file.exists()
    
    # Test log writing
    logger.info("Test message")
    with open(log_file) as f:
        content = f.read()
        assert "Test message" in content
    
    # Test without file (should not raise)
    logger = setup_logging(level="DEBUG")
    assert logger is not None


def test_timer():
    """Test timer context manager."""
    with Timer("test_operation") as timer:
        # Simulate some work
        for _ in range(1000000):
            pass
    
    assert timer.duration > 0
    assert isinstance(timer.duration, float)
    
    # Test string representation
    timer_str = str(timer)
    assert "test_operation" in timer_str
    assert "completed in" in timer_str


def test_timer_with_exception():
    """Test timer handles exceptions correctly."""
    with pytest.raises(ValueError):
        with Timer("failing_operation"):
            raise ValueError("Test error")


def test_timer_nested():
    """Test nested timer usage."""
    with Timer("outer") as t1:
        with Timer("inner") as t2:
            # Simulate some work
            for _ in range(100000):
                pass
    
    assert t1.duration >= t2.duration
    assert t2.duration > 0


@pytest.mark.parametrize("name,sleep_time", [
    ("quick", 0.001),
    ("medium", 0.005),
    ("slow", 0.01),
])
def test_timer_different_durations(name, sleep_time):
    """Test timer with different operation durations."""
    import time
    
    with Timer(name) as timer:
        time.sleep(sleep_time)
    
    assert timer.duration >= sleep_time
