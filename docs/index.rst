====================================
Crop Model Climate Impact Framework
====================================

A modular framework for running crop model simulations to assess climate change impacts and adaptation strategies.

.. image:: https://img.shields.io/badge/python-3.8+-blue.svg
   :target: https://www.python.org/downloads/

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT

Overview
--------
This framework provides a standardized interface for:

- Running multiple crop models (DSSAT, APSIM, STICS)
- Processing climate data from various sources (GCMs, RCMs)
- Analyzing climate change impacts on crop yields
- Evaluating adaptation strategies
- Training surrogate models for rapid scenario exploration

Features
--------
- **Multiple Model Support**: Common interface for different crop models
- **Climate Data Processing**: Standardized handling of climate model outputs
- **Parallel Execution**: Support for both local multiprocessing and HPC environments
- **Modular Design**: Easy to extend with new models and features
- **Surrogate Models**: Optional ML-based surrogate models for rapid assessment
- **Analysis Tools**: Standard impact metrics and visualization functions

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   guides/installation
   guides/configuration
   guides/quickstart
   guides/pipeline
   guides/hpc_usage
   guides/customization

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/basic_usage
   examples/climate_data
   examples/simulation_setup
   examples/impact_analysis
   examples/adaptation_evaluation
   examples/surrogate_models

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/crop_model_interface
   api/climate_processing
   api/analysis
   api/visualization
   api/surrogate_model
   api/utils

.. toctree::
   :maxdepth: 1
   :caption: Development

   development/contributing
   development/testing
   development/documentation
   development/roadmap
   development/changelog

Getting Started
--------------

Installation
^^^^^^^^^^^

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/username/crop-model-framework.git
   cd crop-model-framework

   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows

   # Install dependencies
   pip install -r requirements.txt

Basic Usage
^^^^^^^^^^

1. Configure the framework:

   .. code-block:: bash

      cp config/config_template.yaml config/config.yaml
      # Edit config.yaml with your settings

2. Run the complete pipeline:

   .. code-block:: bash

      python scripts/run_all.py --config config/config.yaml

3. Or run individual steps:

   .. code-block:: bash

      python scripts/00_setup_environment.py --config config/config.yaml
      python scripts/01_prepare_climate_data.py --config config/config.yaml
      # ... and so on

Contributing
-----------
Contributions are welcome! Please see our :doc:`development/contributing` guide for details.

Support
-------
For support, please:

1. Check the :doc:`guides/troubleshooting` guide
2. Search existing `GitHub Issues <https://github.com/username/crop-model-framework/issues>`_
3. Create a new issue if needed

License
-------
This project is licensed under the MIT License. See the :doc:`development/license` file for details.

Note that individual crop models (DSSAT, APSIM, STICS) are subject to their own licenses and terms of use.

Citation
--------
If you use this framework in your research, please cite:

.. code-block:: bibtex

   @misc{crop-model-framework,
     author = {Framework Contributors},
     title = {Crop Model Climate Impact Framework},
     year = {2025},
     publisher = {GitHub},
     url = {https://github.com/username/crop-model-framework}
   }

Indices and Tables
-----------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
