# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'WattAdvisor'
copyright = '2023, Fraunhofer IOSB-AST'
author = 'Fraunhofer IOSB-AST'
release = '1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinx_math_dollar', 'sphinx.ext.mathjax',
              'sphinx.ext.intersphinx', 'autoapi.extension', 'myst_nb']  #, 'sphinx.ext.autosectionlabel'

# MathJax options to render display equations
mathjax_path = "https://cdn.jsdelivr.net/npm/mathjax@2/MathJax.js?config=TeX-AMS-MML_HTMLorMML"

templates_path = ['_templates']
source_suffix = ['.rst', '.md', '.ipynb']
master_doc = 'index'
pygments_style = 'sphinx'
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
autoapi_dirs = ['../../wattadvisor']
autoapi_options = ['members', 'undoc-members', 'show-inheritance', 'show-module-summary', 'imported-members']
autoapi_python_class_content = "both"
# jupyter_execute_notebooks = "off"
nb_execution_mode = 'off'
# nbsphinx_execute = 'never'
nb_execution_excludepatterns = []
#execution_excludepatterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

mathjax_config = {
    'tex2jax': {
        'inlineMath': [['$', '$'], ['\\(', '\\)']],
        'displayMath': [['$$', '$$'], ['\\[', '\\]']]
    }
}

mathjax3_config = {
    'tex': {
        'inlineMath': [['$', '$'], ['\\(', '\\)']],
        'displayMath': [['$$', '$$'], ['\\[', '\\]']]
    }
}

