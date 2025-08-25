import re
from rdagent.components.coder.CoSTEER.task import CoSTEERTask
from typing import Dict, Any, Optional

class StrategyTask(CoSTEERTask):
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        logic_formulation: Optional[str] = None,
        *args,
        **kwargs
    ) -> None:
        """
        Initialize a Strategy Task.
        
        Parameters:
        - name: Name of the strategy
        - description: Natural language description of the strategy logic
        - parameters: Dictionary of strategy parameters
        - logic_formulation: Optional pseudo-code or mathematical formulation of the strategy
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.logic_formulation = logic_formulation
        super().__init__(name=name, description=description, *args, **kwargs)
        
    @property
    def sanitized_name(self) -> str:
        """
        Get the sanitized name for use in file names.
        """
        # Sanitize the strategy name to create a valid file name
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', self.name)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        return sanitized
        
    def get_task_information(self) -> str:
        """Return a string representation for LLM prompts."""
        info = f"""Strategy Name: {self.name}
Description: {self.description}
Parameters: {self.parameters}"""
        if self.logic_formulation:
            info += f"\nLogic Formulation:\n{self.logic_formulation}"
        return info
        
    def get_task_brief_information(self) -> str:
        """Return a concise string representation."""
        return f"Strategy '{self.name}': {self.description} with parameters {self.parameters}"