# Configuration file for the Sphinx documentation builder.

project = "jgo"
copyright = "Apposed"
author = "SciJava developers"

extensions = [
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_depth": 3,
    "collapse_navigation": False,
}
html_static_path = ["_static"]
html_logo = "../jgo.png"
html_favicon = "../jgo.png"
html_title = "jgo documentation"

# -- MyST options ------------------------------------------------------------

myst_heading_anchors = 4

# -- Source suffix ------------------------------------------------------------

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
