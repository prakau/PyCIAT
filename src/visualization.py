##############################################################################
### File: src/visualization.py
##############################################################################
"""
Functions for creating standardized visualizations of simulation results,
impacts, and adaptation effectiveness.
"""

import logging
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, Optional, List, Tuple, Union
import geopandas as gpd

from .utils import ensure_dir_exists

logger = logging.getLogger(__name__)

# Set style defaults
plt.style.use('seaborn')
FIGURE_DPI = 300
DEFAULT_COLORS = sns.color_palette("husl", 8)

def setup_figure_style() -> None:
    """Configure common matplotlib parameters for consistent styling."""
    plt.rcParams.update({
        'figure.dpi': FIGURE_DPI,
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.titlesize': 14
    })

def plot_spatial_impacts(results: pd.DataFrame,
                        shape_df: gpd.GeoDataFrame,
                        variable: str,
                        output_path: str,
                        title: Optional[str] = None,
                        id_column: str = 'location_id',
                        colormap: str = 'RdYlBu',
                        fig_size: Tuple[float, float] = (10, 8)) -> None:
    """
    Create spatial plot of impacts using location geometries.

    Args:
        results: DataFrame with results by location
        shape_df: GeoDataFrame with location geometries
        variable: Variable to plot
        output_path: Path to save figure
        title: Optional plot title
        id_column: Column linking results to geometries
        colormap: Matplotlib colormap name
        fig_size: Figure dimensions (width, height)
    """
    try:
        # Merge results with geometries
        plot_data = shape_df.merge(results, on=id_column, how='left')
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=fig_size)
        
        # Plot base map
        plot_data.plot(
            column=variable,
            cmap=colormap,
            legend=True,
            ax=ax,
            legend_kwds={'label': variable}
        )
        
        # Add title if provided
        if title:
            ax.set_title(title)
        
        # Remove axes
        ax.axis('off')
        
        # Save figure
        ensure_dir_exists(str(Path(output_path).parent))
        plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Spatial plot saved to {output_path}")
    
    except Exception as e:
        logger.error(f"Error creating spatial plot: {e}")

def plot_impact_boxplots(data: pd.DataFrame,
                        variable: str,
                        groupby: str,
                        output_path: str,
                        title: Optional[str] = None,
                        y_label: Optional[str] = None,
                        fig_size: Tuple[float, float] = (10, 6)) -> None:
    """
    Create boxplots of impacts across scenarios/periods.

    Args:
        data: DataFrame with results
        variable: Variable to plot
        groupby: Column to group boxes by
        output_path: Path to save figure
        title: Optional plot title
        y_label: Optional y-axis label
        fig_size: Figure dimensions
    """
    try:
        # Create figure
        plt.figure(figsize=fig_size)
        
        # Create boxplot
        sns.boxplot(
            data=data,
            x=groupby,
            y=variable,
            width=0.7
        )
        
        # Customize plot
        if title:
            plt.title(title)
        if y_label:
            plt.ylabel(y_label)
        
        # Rotate x-labels if needed
        plt.xticks(rotation=45)
        
        # Save figure
        ensure_dir_exists(str(Path(output_path).parent))
        plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Boxplot saved to {output_path}")
    
    except Exception as e:
        logger.error(f"Error creating boxplot: {e}")

def plot_adaptation_effectiveness(data: pd.DataFrame,
                               output_path: str,
                               title: Optional[str] = None,
                               error_bars: bool = True,
                               sort_by: str = 'mean_impact_reduction',
                               fig_size: Tuple[float, float] = (12, 6)) -> None:
    """
    Create bar plot showing adaptation effectiveness.

    Args:
        data: DataFrame with adaptation effectiveness metrics
        output_path: Path to save figure
        title: Optional plot title
        error_bars: Whether to show error bars
        sort_by: Column to sort adaptations by
        fig_size: Figure dimensions
    """
    try:
        # Sort data
        plot_data = data.sort_values(sort_by, ascending=True)
        
        # Create figure
        fig, ax = plt.subplots(figsize=fig_size)
        
        # Create bars
        bars = ax.barh(
            plot_data['adaptation'],
            plot_data['mean_impact_reduction'],
            xerr=plot_data['impact_reduction_std'] if error_bars else None,
            capsize=5
        )
        
        # Color bars by significance
        for i, bar in enumerate(bars):
            bar.set_color(DEFAULT_COLORS[0] if plot_data.iloc[i]['significant'] else 'lightgray')
        
        # Customize plot
        if title:
            ax.set_title(title)
        ax.set_xlabel('Impact Reduction')
        ax.set_ylabel('Adaptation Strategy')
        
        # Add significance markers
        for i, significant in enumerate(plot_data['significant']):
            if significant:
                ax.text(
                    ax.get_xlim()[1] * 0.02,
                    i,
                    '*',
                    verticalalignment='center'
                )
        
        # Save figure
        ensure_dir_exists(str(Path(output_path).parent))
        plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Adaptation effectiveness plot saved to {output_path}")
    
    except Exception as e:
        logger.error(f"Error creating adaptation effectiveness plot: {e}")

def plot_ensemble_agreement(data: pd.DataFrame,
                          variable: str,
                          shape_df: gpd.GeoDataFrame,
                          output_path: str,
                          id_column: str = 'location_id',
                          title: Optional[str] = None,
                          fig_size: Tuple[float, float] = (15, 5)) -> None:
    """
    Create multi-panel plot showing ensemble mean and agreement.

    Args:
        data: DataFrame with ensemble statistics
        variable: Variable to plot
        shape_df: GeoDataFrame with location geometries
        output_path: Path to save figure
        id_column: Column linking results to geometries
        title: Optional plot title
        fig_size: Figure dimensions
    """
    try:
        # Create figure with two panels
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=fig_size)
        
        # Merge data with geometries
        plot_data = shape_df.merge(data, on=id_column, how='left')
        
        # Plot ensemble mean
        mean_plot = plot_data.plot(
            column=f"{variable}_mean",
            cmap='RdYlBu',
            legend=True,
            ax=ax1,
            legend_kwds={'label': f'{variable} (Ensemble Mean)'}
        )
        ax1.set_title('Ensemble Mean')
        ax1.axis('off')
        
        # Plot agreement
        agreement_plot = plot_data.plot(
            column=f"{variable}_high_agreement",
            cmap='RdYlGn',
            legend=True,
            ax=ax2,
            legend_kwds={'label': 'Model Agreement'}
        )
        ax2.set_title('Model Agreement')
        ax2.axis('off')
        
        # Add main title if provided
        if title:
            fig.suptitle(title, y=1.05)
        
        # Save figure
        ensure_dir_exists(str(Path(output_path).parent))
        plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Ensemble agreement plot saved to {output_path}")
    
    except Exception as e:
        logger.error(f"Error creating ensemble agreement plot: {e}")

def plot_time_series(data: pd.DataFrame,
                    x_column: str,
                    y_column: str,
                    output_path: str,
                    groupby: Optional[str] = None,
                    title: Optional[str] = None,
                    y_label: Optional[str] = None,
                    rolling_window: Optional[int] = None,
                    fig_size: Tuple[float, float] = (12, 6)) -> None:
    """
    Create time series plot with optional grouping and smoothing.

    Args:
        data: DataFrame with time series data
        x_column: Column for x-axis (typically time)
        y_column: Column to plot on y-axis
        output_path: Path to save figure
        groupby: Optional column for grouping lines
        title: Optional plot title
        y_label: Optional y-axis label
        rolling_window: Optional window size for moving average
        fig_size: Figure dimensions
    """
    try:
        # Create figure
        plt.figure(figsize=fig_size)
        
        if groupby:
            # Plot lines for each group
            for name, group in data.groupby(groupby):
                plot_data = group.copy()
                if rolling_window:
                    plot_data[y_column] = (
                        plot_data[y_column].rolling(rolling_window, center=True).mean()
                    )
                plt.plot(plot_data[x_column], plot_data[y_column], label=name)
            plt.legend()
        else:
            # Plot single line
            plot_data = data.copy()
            if rolling_window:
                plot_data[y_column] = (
                    plot_data[y_column].rolling(rolling_window, center=True).mean()
                )
            plt.plot(plot_data[x_column], plot_data[y_column])
        
        # Customize plot
        if title:
            plt.title(title)
        if y_label:
            plt.ylabel(y_label)
        
        plt.grid(True, alpha=0.3)
        
        # Save figure
        ensure_dir_exists(str(Path(output_path).parent))
        plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Time series plot saved to {output_path}")
    
    except Exception as e:
        logger.error(f"Error creating time series plot: {e}")

# Add more visualization functions as needed...
