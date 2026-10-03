"""Process supervisor. Start a command, stop it on a sensor limit or an operator halt."""

from process_supervisor.supervisor import HALT, Limits, Supervisor

__all__ = ["HALT", "Limits", "Supervisor"]
__version__ = "0.1.0"
