from rdagent.core.experiment import Experiment, FBWorkspace
from rdagent.scenarios.quant_strategy_lab_task import StrategyTask
from typing import List, Dict, Any, Optional
from pathlib import Path

class StrategyExperiment(Experiment):
    def __init__(self, tasks: List[StrategyTask], *args, **kwargs) -> None:
        """
        Initialize a Strategy Experiment.
        
        Parameters:
        - tasks: List of StrategyTask objects
        """
        super().__init__(sub_tasks=tasks, *args, **kwargs)
        self.experiment_workspace = StrategyWorkspace()
        self.result: Optional[Dict[str, Any]] = None
        self.stdout: str = ""
        
    def to_json(self) -> Dict[str, Any]:
        """Convert experiment to JSON-serializable format."""
        return {
            "tasks": [task.get_task_information() for task in self.sub_tasks],
            "result": self.result,
            "stdout": self.stdout
        }

class StrategyWorkspace(FBWorkspace):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize a Strategy Workspace."""
        super().__init__(*args, **kwargs)
        # Create directories for strategy code
        (self.workspace_path / "strategies").mkdir(exist_ok=True)
        
    def save_strategy_code(self, strategy_name: str, code: str) -> None:
        """
        Save generated strategy code to workspace.
        
        Parameters:
        - strategy_name: Name of the strategy
        - code: Generated Python code for the strategy
        """
        strategy_file = self.workspace_path / "strategies" / f"{strategy_name}.py"
        strategy_file.write_text(code)
        
    def get_strategy_file_path(self, strategy_name: str) -> Path:
        """
        Get path to strategy file.
        
        Parameters:
        - strategy_name: Name of the strategy
        
        Returns:
        - Path to the strategy file
        """
        return self.workspace_path / "strategies" / f"{strategy_name}.py"