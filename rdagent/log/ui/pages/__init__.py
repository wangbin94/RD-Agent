"""Pages module for RD-Agent UI."""

from .dashboard import render_dashboard
from .evolving import render_evolving_window
from .research import render_research_window

__all__ = [
    "render_dashboard",
    "render_research_window",
    "render_evolving_window",
]