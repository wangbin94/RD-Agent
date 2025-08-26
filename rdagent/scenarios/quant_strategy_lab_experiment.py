import re
from rdagent.core.experiment import Experiment, FBWorkspace
from rdagent.scenarios.quant_strategy_lab_task import StrategyTask
from typing import List, Dict, Any, Optional
from pathlib import Path

class TaskWorkspace(FBWorkspace):
    """Workspace object for displaying task results in UI"""
    def __init__(self, task, workspace_path):
        super().__init__()
        self.target_task = task
        self.workspace_path = workspace_path
        self.file_dict = {}  # Will be populated with filename -> code mappings

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
        
    def save_strategy(self, strategy_name: str, code: str) -> None:
        """
        Save a strategy to a Python file.
        
        Parameters:
        - strategy_name: Name of the strategy
        - code: Generated Python code for the strategy
        """
        # Import StrategyTask to check if strategy_name is a StrategyTask
        from rdagent.scenarios.quant_strategy_lab_task import StrategyTask
        
        # If strategy_name is a StrategyTask, use its sanitized_name
        if isinstance(strategy_name, StrategyTask):
            sanitized_name = strategy_name.sanitized_name
        else:
            # Sanitize the strategy name to create a valid file name
            sanitized_name = re.sub(r'[^a-zA-Z0-9_]', '_', strategy_name)
            # Remove multiple consecutive underscores
            sanitized_name = re.sub(r'_+', '_', sanitized_name)
            # Remove leading/trailing underscores
            sanitized_name = sanitized_name.strip('_')
            
        strategy_file = self.workspace_path / "strategies" / f"{sanitized_name}.py"
        # Create the strategies directory if it doesn't exist
        strategy_file.parent.mkdir(parents=True, exist_ok=True)
        strategy_file.write_text(code)
        
    def get_strategy_file_path(self, strategy_name: str) -> Path:
        """
        Get path to strategy file.
        
        Parameters:
        - strategy_name: Name of the strategy
        
        Returns:
        - Path to the strategy file
        """
        # Import StrategyTask to check if strategy_name is a StrategyTask
        from rdagent.scenarios.quant_strategy_lab_task import StrategyTask
        
        # If strategy_name is a StrategyTask, use its sanitized_name
        if isinstance(strategy_name, StrategyTask):
            sanitized_name = strategy_name.sanitized_name
        else:
            # Sanitize the strategy name to create a valid file name
            sanitized_name = re.sub(r'[^a-zA-Z0-9_]', '_', strategy_name)
            # Remove multiple consecutive underscores
            sanitized_name = re.sub(r'_+', '_', sanitized_name)
            # Remove leading/trailing underscores
            sanitized_name = sanitized_name.strip('_')
            
        return self.workspace_path / "strategies" / f"{sanitized_name}.py"