# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# set an environment variable for shapely.decorators.requires_geos to see if we
# are in a doc build
import os
os.environ["SPHINX_DOC_BUILD"] = "1"

# -- Project information -----------------------------------------------------

project = 'Shapely'
copyright = '2011-2022, Sean Gillies and Shapely contributors'

# The full version, including alpha/beta/rc tags.
import shapely
release = shapely.__version__.split("+")[0]

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'matplotlib.sphinxext.plot_directive',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'numpydoc',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_book_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_css_files = [
    'custom.css',
]

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = False

# -- Options for LaTeX output --------------------------------------------------

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'Shapely.tex', 'Shapely Documentation',
   'Sean Gillies', 'manual'),
]

#  --Options for sphinx extensions -----------------------------------------------

# connect docs in other projects
intersphinx_mapping = {
    'numpy': ('https://numpy.org/doc/stable/', None),
}
