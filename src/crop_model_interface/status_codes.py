##############################################################################
### File: src/crop_model_interface/status_codes.py
##############################################################################
"""
Defines the Status enumeration used to track the state of simulations throughout
the pipeline, from setup to completion.
"""

from enum import Enum
from typing import Set

class Status(Enum):
    """
    Enumeration of possible simulation states.
    Used for tracking progress and handling errors in the simulation pipeline.
    """
    # Initial States
    PENDING = "Simulation task created but not yet processed"
    CONFIG_ERROR = "Configuration error (e.g., missing paths, invalid parameters)"
    
    # Setup States
    SETUP_ERROR = "Error during input file generation"
    READY_TO_RUN = "Input files generated successfully, ready for execution"
    
    # Run States
    RUNNING = "Simulation is currently executing"
    SUCCESS = "Simulation completed successfully"
    RUN_ERROR = "Error during simulation execution"
    TIMEOUT = "Simulation exceeded time limit"
    MISSING_FILES = "Required input/output files not found"
    
    # Output Processing States
    OUTPUT_PARSED = "Model outputs successfully parsed and standardized"
    OUTPUT_ERROR = "Error during output parsing"
    
    # Other States
    SKIPPED = "Simulation skipped (e.g., due to dependencies or filters)"
    UNKNOWN_ERROR = "Unspecified error occurred"

    def is_error(self) -> bool:
        """Returns True if this status represents an error condition."""
        return any(err in self.name for err in ['ERROR', 'TIMEOUT'])

    def is_final(self) -> bool:
        """Returns True if this status represents a final state (success or failure)."""
        return self in {
            Status.SUCCESS,
            Status.CONFIG_ERROR,
            Status.SETUP_ERROR,
            Status.RUN_ERROR,
            Status.TIMEOUT,
            Status.MISSING_FILES,
            Status.OUTPUT_PARSED,
            Status.OUTPUT_ERROR,
            Status.SKIPPED,
            Status.UNKNOWN_ERROR
        }

    def is_success(self) -> bool:
        """Returns True if this status represents successful completion."""
        return self in {Status.SUCCESS, Status.OUTPUT_PARSED}

    def is_runnable(self) -> bool:
        """Returns True if the simulation can be run from this state."""
        return self in {Status.READY_TO_RUN}

    @classmethod
    def error_states(cls) -> Set['Status']:
        """Returns the set of all error states."""
        return {status for status in cls if status.is_error()}

    @classmethod
    def final_states(cls) -> Set['Status']:
        """Returns the set of all final states."""
        return {status for status in cls if status.is_final()}

    @classmethod
    def runnable_states(cls) -> Set['Status']:
        """Returns the set of all states from which simulation can be run."""
        return {status for status in cls if status.is_runnable()}
