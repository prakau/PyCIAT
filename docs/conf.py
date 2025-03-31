##############################################################################
### File: docs/conf.py
##############################################################################
"""
Sphinx documentation configuration file.
"""

import os
import sys
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath('..'))

# Project information
project = 'PyCIAT'
copyright = f'{datetime.now().year}, PyCIAT Contributors' # Or keep original if preferred
author = 'PyCIAT Contributors' # Or keep original if preferred
version = '0.1.0'  # Update with each release
release = version

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx_rtd_theme',
    'sphinx.ext.githubpages',
    'sphinx_autodoc_typehints',
    'nbsphinx',
    'sphinx_copybutton',
    'sphinx_design',
    'sphinxcontrib.mermaid',
    'sphinx_togglebutton',
    'sphinx.ext.graphviz',
    'numpydoc',
]

# Extension settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Napoleon settings
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Numpydoc settings
numpydoc_show_class_members = False
numpydoc_show_inherited_class_members = False
numpydoc_class_members_toctree = False

# Intersphinx mappings
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/pandas-docs/stable/', None),
    'xarray': ('https://xarray.pydata.org/en/stable/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
}

# Theme settings
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'style_nav_header_background': '#2980B9',
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# HTML settings
html_static_path = ['_static']
html_css_files = ['custom.css']
html_logo = None  # Add path to logo if available
html_favicon = None  # Add path to favicon if available
html_show_sourcelink = True
html_show_sphinx = True
html_show_copyright = True

# LaTeX settings
latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '11pt',
    'figure_align': 'htbp',
}

# Source settings
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}
master_doc = 'index'
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
templates_path = ['_templates']

# Misc settings
todo_include_todos = True
numfig = True
smartquotes = True
language = 'en'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# These folders are copied to the documentation's HTML output
html_static_path = ['_static']

# These paths are either relative to html_static_path or fully qualified paths
html_css_files = [
    'css/custom.css',
]

# Options for notebook building
nbsphinx_execute = 'never'  # Don't execute notebooks during build
nbsphinx_allow_errors = False
nbsphinx_timeout = 60  # Timeout in seconds for notebook execution

# Additional configurations
linkcheck_ignore = [r'http://localhost:\d+']
graphviz_output_format = 'svg'

# Configure autodoc to skip certain members
def skip_member(app, what, name, obj, skip, options):
    """Custom skip function for autodoc."""
    # Skip certain members
    if name in ['__dict__', '__doc__', '__module__', '__weakref__']:
        return True
    return skip

def setup(app):
    """Setup function for Sphinx extension."""
    app.connect('autodoc-skip-member', skip_member)
