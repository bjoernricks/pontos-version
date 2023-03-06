# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#

# pylint: disable=invalid-name,redefined-builtin,wrong-import-position

import sys
from pathlib import Path

sys.path.insert(0, Path(__file__).parent.absolute())

from pontos.version import __version__

# -- Project information -----------------------------------------------------

project = "pontos"
copyright = "2022-2023, Greenbone Networks GmbH <info@greenbone.net>"
author = "Greenbone Networks GmbH <info@greenbone.net>"

# The full version, including alpha/beta/rc tags
release = __version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# The master toctree document.
master_doc = "index"

language = "en"

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_title = project

html_favicon = "favicon.png"

html_css_files = ["custom.css"]
html_logo = "_static/logo.svg"

html_static_path = ["_static"]

repo_url = "https://github.com/greenbone/pontos/"
html_theme_options = {
    "source_repository": repo_url,
    "source_branch": "main",
    "source_directory": "src/",
    "light_css_variables": {
        "color-content-foreground": "#4C4C4C",
        "color-foreground-primary": "4C4C4C",
        "color-foreground-secondary": "#7F7F7F",
        "color-code-background": "#333333",
        "color-code-foreground": "#E5E5E5",
        "color-admonition-title--note": "#11AB51",
        "admonition-font-size": "0.9rem",
        "color-background-primary": "#FFFFFF",
        "color-background-secondary": "#F3F3F3",
        "color-sidebar-background": "#F3F3F3",
    },
    "dark_css_variables": {
        "color-content-foreground": "#F3F3F3",
        "color-foreground-primary": "F3F3F3",
        "color-foreground-secondary": "#E5E5E5",
        "color-code-background": "#333333",
        "color-code-foreground": "#E5E5E5",
        "color-admonition-title--note": "#11AB51",
        "admonition-font-size": "0.9rem",
        "color-background-primary": "#171717",
        "color-background-secondary": "#4C4C4C",
        "color-sidebar-background": "#333333",
    },
    "footer_icons": [
        {
            "name": "GitHub",
            "url": repo_url,
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
}

autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

autodoc_class_signature = "separated"

pygments_style = "zenburn"


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = project + "-doc"

# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        project + ".tex",
        project + " Documentation",
        "Greenbone Networks GmbH",
        "manual",
    )
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(master_doc, project, project + " Documentation", [author], 1)]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        project,
        project + " Documentation",
        author,
        project,
        "One line description of project.",
        "Miscellaneous",
    )
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ["search.html"]


# -- Extension configuration -------------------------------------------------
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

myst_enable_extensions = ["colon_fence"]
