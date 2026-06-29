"""
UI-level modules for GEO Streamlit app.

Each top-level Tab in `geo_tool.py` should have a corresponding
`tab_*.py` module here, exposing a `render_*` function that is
invoked from the main app.
"""

from . import (
    tab_keywords,
    tab_autowrite,
    tab_optimize,
    tab_validation,
    tab_history,
    tab_reports,
    tab_workflow,
    tab_resources,
    tab_platform_sync,
    tab_config_optimizer,
)

__all__ = [
    "tab_keywords",
    "tab_autowrite",
    "tab_optimize",
    "tab_validation",
    "tab_history",
    "tab_reports",
    "tab_workflow",
    "tab_resources",
    "tab_platform_sync",
    "tab_config_optimizer",
]