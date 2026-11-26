"""
Main PlateDesigner class for generating microplate layouts.
"""
from typing import Optional

# Support both package and direct imports
try:
    from .config import PlateConfig
    from .solver import MiniZincSolver
    from .output import Layout
    from .validators import validate_plate_config, validate_minizinc_available
    from .exceptions import SolverError, ValidationError
except ImportError:
    from config import PlateConfig
    from solver import MiniZincSolver
    from output import Layout
    from validators import validate_plate_config, validate_minizinc_available
    from exceptions import SolverError, ValidationError


class PlateDesigner:
    """
    Main interface for designing microplate layouts.
    
    Example:
        ```python
        from plaid_core import PlateDesigner, PlateConfig, Compound, Control
        
        config = PlateConfig(
            plate_rows=8, plate_cols=12, empty_edge=1,
            compounds=[
                Compound(name="CompA", concentrations=3, replicates=3),
            ],
            controls=[
                Control(name="PosCtrl", concentration_levels=1, replicates=3)
            ]
        )
        
        designer = PlateDesigner()
        layout = designer.design(config)
        layout.save_csv("output.csv")
        print(layout.summary())
        ```
    """
    
    def __init__(self, minizinc_path: Optional[str] = None):
        """
        Initialize PlateDesigner.
        
        Args:
            minizinc_path: Optional path to minizinc executable.
                          If not provided, searches PATH.
                          
        Raises:
            MiniZincNotFoundError: If minizinc not found
        """
        # Check MiniZinc availability
        if not validate_minizinc_available():
            raise SolverError(
                "MiniZinc not found. Install from https://www.minizinc.org/"
            )
        
        self.solver = MiniZincSolver(minizinc_path)
    
    def design(self, config: PlateConfig) -> Layout:
        """
        Generate microplate layout.
        
        Args:
            config: PlateConfig instance
            
        Returns:
            Layout object with design results
            
        Raises:
            ValidationError: If configuration is invalid
            SolverError: If solver fails
            NoSolutionFoundError: If no valid layout exists
            TimeoutError: If solver exceeds timeout
        """
        # Validate configuration
        validate_plate_config(config)
        
        # Run solver
        csv_output = self.solver.solve(config)
        
        # Parse and return layout
        layout = Layout(csv_output)
        return layout
