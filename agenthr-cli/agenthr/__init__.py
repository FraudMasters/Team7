"""
AgentHR CLI - Command-line interface for AgentHR.

This package provides a command-line interface for interacting with
the AgentHR backend API for resume analysis, candidate ranking,
and vacancy management.
"""

__version__ = "0.1.0"
__author__ = "AgentHR Team"
__email__ = "team@agenthr.dev"

from agenthr.cli import main

__all__ = ["main", "__version__"]
