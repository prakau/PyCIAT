##############################################################################
### File: src/analysis.py
##############################################################################
"""
Analysis functions for processing simulation outputs, calculating impacts,
and evaluating adaptation effectiveness.
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from scipy import stats

from .utils import Timer, ensure_dir_exists

logger = logging.getLogger(__name__)

def calculate_baseline_statistics(data: pd.DataFrame,
                               groupby_cols: List[str],
                               value_cols: List[str],
                               percentiles: Optional[List[float]] = None) -> pd.DataFrame:
    """
    Calculate baseline statistics for specified variables.

    Args:
        data: DataFrame containing simulation results
        groupby_cols: Columns to group by (e.g., location, soil)
        value_cols: Variables to calculate statistics for
        percentiles: Optional list of percentiles to calculate

    Returns:
        DataFrame with baseline statistics
    """
    if percentiles is None:
        percentiles = [10, 25, 50, 75, 90]

    try:
        # Calculate basic statistics
        stats_dict = {
            f"{col}_mean": ('mean', col) for col in value_cols
        }
        stats_dict.update({
            f"{col}_std": ('std', col) for col in value_cols
        })
        stats_dict.update({
            f"{col}_cv": (lambda x: x.std() / x.mean(), col) for col in value_cols
        })
        
        # Add percentiles
        for p in percentiles:
            stats_dict.update({
                f"{col}_p{p}": (lambda x, p=p: np.percentile(x, p), col)
                for col in value_cols
            })
        
        # Calculate statistics
        baseline_stats = data.groupby(groupby_cols).agg(**stats_dict).reset_index()
        
        return baseline_stats

    except Exception as e:
        logger.error(f"Error calculating baseline statistics: {e}")
        return pd.DataFrame()

def calculate_climate_impacts(future_data: pd.DataFrame,
                            baseline_data: pd.DataFrame,
                            impact_vars: List[str],
                            groupby_cols: List[str]) -> pd.DataFrame:
    """
    Calculate climate change impacts relative to baseline.

    Args:
        future_data: DataFrame with future scenario results
        baseline_data: DataFrame with baseline period results
        impact_vars: Variables to calculate impacts for
        groupby_cols: Columns to group by for impact calculation

    Returns:
        DataFrame with absolute and relative changes
    """
    try:
        # Calculate baseline means for reference
        baseline_means = baseline_data.groupby(groupby_cols)[impact_vars].mean().reset_index()
        
        # Calculate future means
        future_means = future_data.groupby(groupby_cols)[impact_vars].mean().reset_index()
        
        # Calculate absolute and relative changes
        impacts = pd.merge(future_means, baseline_means, on=groupby_cols, suffixes=('_future', '_baseline'))
        
        for var in impact_vars:
            # Absolute change
            impacts[f"{var}_abs_change"] = (
                impacts[f"{var}_future"] - impacts[f"{var}_baseline"]
            )
            
            # Relative change (%)
            impacts[f"{var}_rel_change"] = (
                (impacts[f"{var}_future"] - impacts[f"{var}_baseline"]) /
                impacts[f"{var}_baseline"] * 100
            )
        
        return impacts

    except Exception as e:
        logger.error(f"Error calculating climate impacts: {e}")
        return pd.DataFrame()

def evaluate_adaptation_effectiveness(adaptation_data: pd.DataFrame,
                                   baseline_impacts: pd.DataFrame,
                                   target_vars: List[str],
                                   adaptation_id_col: str = 'adaptation',
                                   groupby_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Evaluate effectiveness of adaptation strategies.

    Args:
        adaptation_data: DataFrame with adaptation scenario results
        baseline_impacts: DataFrame with baseline impact calculations
        target_vars: Variables to evaluate adaptation effectiveness for
        adaptation_id_col: Column identifying adaptation strategies
        groupby_cols: Additional columns to group by

    Returns:
        DataFrame with adaptation effectiveness metrics
    """
    try:
        if groupby_cols is None:
            groupby_cols = ['location_id', 'climate_source', 'scenario', 'period']
        
        # Merge adaptation results with baseline impacts
        analysis_cols = groupby_cols + [adaptation_id_col] + target_vars
        merged = pd.merge(
            adaptation_data[analysis_cols],
            baseline_impacts,
            on=groupby_cols,
            suffixes=('_adapt', '')
        )
        
        results = []
        for adaptation in adaptation_data[adaptation_id_col].unique():
            adapt_subset = merged[merged[adaptation_id_col] == adaptation]
            
            for var in target_vars:
                # Calculate effectiveness metrics
                effectiveness = {
                    'adaptation': adaptation,
                    'variable': var,
                    'mean_impact_reduction': (
                        adapt_subset[f"{var}_abs_change"].mean() -
                        adapt_subset[f"{var}_adapt"].mean()
                    ),
                    'impact_reduction_std': (
                        adapt_subset[f"{var}_abs_change"].std()
                    ),
                    'relative_effectiveness': (
                        (adapt_subset[f"{var}_adapt"].mean() -
                         adapt_subset[f"{var}_abs_change"].mean()) /
                        abs(adapt_subset[f"{var}_abs_change"].mean()) * 100
                    )
                }
                
                # Add statistical significance
                t_stat, p_value = stats.ttest_ind(
                    adapt_subset[f"{var}_adapt"],
                    adapt_subset[f"{var}_abs_change"]
                )
                effectiveness['significant'] = p_value < 0.05
                effectiveness['p_value'] = p_value
                
                results.append(effectiveness)
        
        return pd.DataFrame(results)

    except Exception as e:
        logger.error(f"Error evaluating adaptation effectiveness: {e}")
        return pd.DataFrame()

def calculate_ensemble_statistics(data: pd.DataFrame,
                                groupby_cols: List[str],
                                value_cols: List[str],
                                model_col: str = 'crop_model',
                                agreement_threshold: float = 0.75) -> pd.DataFrame:
    """
    Calculate ensemble statistics and model agreement.

    Args:
        data: DataFrame with results from multiple models
        groupby_cols: Columns to group by
        value_cols: Variables to calculate ensemble statistics for
        model_col: Column identifying different models
        agreement_threshold: Threshold for model agreement (fraction)

    Returns:
        DataFrame with ensemble statistics and agreement metrics
    """
    try:
        ensemble_stats = []
        
        for var in value_cols:
            # Calculate basic ensemble statistics
            stats = data.groupby(groupby_cols).agg({
                var: ['mean', 'std', 'min', 'max']
            }).reset_index()
            
            # Calculate model agreement metrics
            agreement = data.groupby(groupby_cols).agg({
                var: lambda x: np.mean(x > x.mean()),  # Fraction above mean
                model_col: 'count'  # Number of models
            }).reset_index()
            
            # Merge statistics
            combined = pd.merge(stats, agreement, on=groupby_cols)
            
            # Flag high agreement
            combined[f"{var}_high_agreement"] = (
                combined[f"{var}_agreement"] > agreement_threshold
            )
            
            ensemble_stats.append(combined)
        
        # Combine results for all variables
        return pd.concat(ensemble_stats, axis=1)

    except Exception as e:
        logger.error(f"Error calculating ensemble statistics: {e}")
        return pd.DataFrame()

def aggregate_to_regions(data: pd.DataFrame,
                        region_mapping: pd.DataFrame,
                        value_cols: List[str],
                        location_col: str = 'location_id',
                        region_col: str = 'region_id',
                        weights: Optional[Dict[str, float]] = None) -> pd.DataFrame:
    """
    Aggregate point-based results to regions.

    Args:
        data: DataFrame with point-based results
        region_mapping: DataFrame mapping points to regions
        value_cols: Variables to aggregate
        location_col: Column identifying locations
        region_col: Column identifying regions
        weights: Optional dictionary of location weights

    Returns:
        DataFrame with results aggregated to regions
    """
    try:
        # Merge with region mapping
        merged = pd.merge(data, region_mapping[[location_col, region_col]], on=location_col)
        
        if weights is not None:
            # Apply weights to values
            for var in value_cols:
                merged[f"{var}_weighted"] = (
                    merged[var] * merged[location_col].map(weights)
                )
            
            # Calculate weighted means
            regional = merged.groupby(region_col).agg({
                f"{var}_weighted": 'sum' for var in value_cols
            }).reset_index()
            
            # Remove _weighted suffix
            regional.columns = [col.replace('_weighted', '') for col in regional.columns]
        
        else:
            # Simple unweighted means
            regional = merged.groupby(region_col)[value_cols].mean().reset_index()
        
        return regional

    except Exception as e:
        logger.error(f"Error aggregating to regions: {e}")
        return pd.DataFrame()

# Add more analysis functions as needed...
