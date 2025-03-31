"""Tests for impact analysis functionality."""

import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from typing import Dict, Any

from src.analysis import (
    calculate_impact_metrics,
    compute_ensemble_statistics,
    evaluate_adaptation_effectiveness,
    aggregate_regional_impacts
)

@pytest.fixture
def sample_simulation_results() -> pd.DataFrame:
    """Create sample simulation results for testing."""
    np.random.seed(42)
    
    # Create base results
    results = pd.DataFrame({
        'simulation_id': [f'sim_{i:03d}' for i in range(100)],
        'location_id': [f'loc_{i:02d}' for i in range(10)] * 10,
        'climate_model': ['model_A', 'model_B'] * 50,
        'scenario': ['historical', 'ssp245', 'ssp585'] * 34,
        'period': ['baseline', 'near_future', 'far_future'] * 34,
        'adaptation': ['baseline', 'early_sowing'] * 50,
        'yield': np.random.normal(4000, 800, 100),
        'biomass': np.random.normal(10000, 2000, 100),
        'anthesis_date': np.random.randint(50, 80, 100),
        'maturity_date': np.random.randint(90, 120, 100)
    })
    
    # Add location metadata
    results['latitude'] = [12.0 + i * 0.5 for i in range(10)] * 10
    results['longitude'] = [75.0 + i * 0.5 for i in range(10)] * 10
    results['elevation'] = np.random.uniform(500, 1000, 100)
    
    return results

def test_calculate_impact_metrics(sample_simulation_results: pd.DataFrame):
    """Test calculation of climate change impact metrics."""
    impacts = calculate_impact_metrics(
        results=sample_simulation_results,
        baseline_period='baseline',
        future_period='near_future',
        variables=['yield', 'biomass']
    )
    
    assert isinstance(impacts, pd.DataFrame)
    assert 'yield_abs_change' in impacts.columns
    assert 'yield_rel_change' in impacts.columns
    assert 'biomass_abs_change' in impacts.columns
    assert 'biomass_rel_change' in impacts.columns
    
    # Verify calculation correctness
    assert all(impacts['yield_rel_change'].between(-100, 100))
    assert all(impacts['biomass_rel_change'].between(-100, 100))

def test_compute_ensemble_statistics(sample_simulation_results: pd.DataFrame):
    """Test computation of ensemble statistics."""
    stats = compute_ensemble_statistics(
        results=sample_simulation_results,
        group_cols=['location_id', 'period'],
        value_cols=['yield', 'biomass']
    )
    
    assert isinstance(stats, pd.DataFrame)
    assert 'yield_mean' in stats.columns
    assert 'yield_std' in stats.columns
    assert 'biomass_mean' in stats.columns
    assert 'biomass_std' in stats.columns
    
    # Verify statistical properties
    assert all(stats['yield_std'] >= 0)
    assert all(stats['biomass_std'] >= 0)

def test_evaluate_adaptation_effectiveness(sample_simulation_results: pd.DataFrame):
    """Test evaluation of adaptation strategies."""
    effectiveness = evaluate_adaptation_effectiveness(
        results=sample_simulation_results,
        baseline_adaptation='baseline',
        target_variable='yield',
        group_cols=['location_id', 'climate_model', 'scenario']
    )
    
    assert isinstance(effectiveness, pd.DataFrame)
    assert 'adaptation' in effectiveness.columns
    assert 'relative_effectiveness' in effectiveness.columns
    assert 'absolute_effectiveness' in effectiveness.columns
    
    # Verify calculation correctness
    early_sowing = effectiveness[effectiveness['adaptation'] == 'early_sowing']
    assert all(early_sowing['relative_effectiveness'].notna())

def test_aggregate_regional_impacts(sample_simulation_results: pd.DataFrame):
    """Test regional impact aggregation."""
    # Create regional mapping
    region_mapping = pd.DataFrame({
        'location_id': [f'loc_{i:02d}' for i in range(10)],
        'region': ['Region_A', 'Region_B'] * 5
    })
    
    aggregated = aggregate_regional_impacts(
        results=sample_simulation_results,
        region_mapping=region_mapping,
        variables=['yield', 'biomass'],
        weights='area'  # Using equal weights for test
    )
    
    assert isinstance(aggregated, pd.DataFrame)
    assert 'region' in aggregated.columns
    assert 'yield_mean' in aggregated.columns
    assert 'biomass_mean' in aggregated.columns

def test_impact_uncertainty_ranges(sample_simulation_results: pd.DataFrame):
    """Test calculation of impact uncertainty ranges."""
    impacts = calculate_impact_metrics(
        results=sample_simulation_results,
        baseline_period='baseline',
        future_period='near_future',
        variables=['yield'],
        uncertainty_ranges=True
    )
    
    assert 'yield_change_q10' in impacts.columns
    assert 'yield_change_q90' in impacts.columns
    assert all(impacts['yield_change_q90'] >= impacts['yield_change_q10'])

def test_ensemble_agreement(sample_simulation_results: pd.DataFrame):
    """Test calculation of ensemble agreement metrics."""
    agreement = compute_ensemble_statistics(
        results=sample_simulation_results,
        group_cols=['location_id', 'period'],
        value_cols=['yield'],
        include_agreement=True
    )
    
    assert 'yield_agreement_direction' in agreement.columns
    assert all(agreement['yield_agreement_direction'].between(0, 100))

def test_adaptation_ranking(sample_simulation_results: pd.DataFrame):
    """Test ranking of adaptation strategies."""
    effectiveness = evaluate_adaptation_effectiveness(
        results=sample_simulation_results,
        baseline_adaptation='baseline',
        target_variable='yield',
        include_ranking=True
    )
    
    assert 'rank' in effectiveness.columns
    assert effectiveness['rank'].nunique() == (
        effectiveness['adaptation'].nunique() - 1  # Excluding baseline
    )

def test_spatial_patterns(sample_simulation_results: pd.DataFrame):
    """Test analysis of spatial impact patterns."""
    impacts = calculate_impact_metrics(
        results=sample_simulation_results,
        baseline_period='baseline',
        future_period='near_future',
        variables=['yield'],
        spatial_analysis=True
    )
    
    assert 'latitude' in impacts.columns
    assert 'longitude' in impacts.columns
    assert 'yield_change_spatial_cluster' in impacts.columns

def test_error_handling():
    """Test error handling in analysis functions."""
    # Create invalid results
    invalid_results = pd.DataFrame({
        'simulation_id': ['sim_001'],
        'yield': ['invalid']  # Invalid data type
    })
    
    with pytest.raises(ValueError):
        calculate_impact_metrics(
            results=invalid_results,
            baseline_period='baseline',
            future_period='future',
            variables=['yield']
        )
    
    # Test missing required columns
    missing_cols = pd.DataFrame({
        'simulation_id': ['sim_001'],
        'yield': [1000]
        # Missing period column
    })
    
    with pytest.raises(ValueError):
        calculate_impact_metrics(
            results=missing_cols,
            baseline_period='baseline',
            future_period='future',
            variables=['yield']
        )
