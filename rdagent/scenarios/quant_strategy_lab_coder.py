import os
import tempfile
from pathlib import Path
from rdagent.core.developer import Developer
from rdagent.scenarios.quant_strategy_lab_experiment import StrategyExperiment
from rdagent.scenarios.quant_strategy_lab_scenario import CustomStrategyScenario
from rdagent.oai.llm_utils import APIBackend
import json

class CustomStrategyCoder(Developer):
    def __init__(self, scen: CustomStrategyScenario) -> None:
        """
        Initialize the Custom Strategy Coder.
        
        Parameters:
        - scen: CustomStrategyScenario instance
        """
        super().__init__(scen)
        
    def develop(self, exp: StrategyExperiment) -> StrategyExperiment:
        """
        Develop strategy code based on tasks in the experiment.
        
        Parameters:
        - exp: StrategyExperiment containing tasks
        
        Returns:
        - StrategyExperiment with generated code in workspace
        """
        for task in exp.sub_tasks:
            # Generate code using LLM
            code = self._generate_strategy_code(task)
            
            # Save code to workspace
            exp.experiment_workspace.save_strategy_code(task.name, code)
            
        return exp
        
    def _generate_strategy_code(self, task) -> str:
        """
        Generate Python code for a strategy task using LLM.
        
        Parameters:
        - task: StrategyTask object
        
        Returns:
        - Generated Python code as string
        """
        # System prompt for code generation
        system_prompt = """
        You are an expert Python developer specializing in quantitative trading strategies.
        Your task is to generate a complete Python class that implements a trading strategy.
        The strategy should inherit from BaseStrategy and implement the generate_signals method.
        The generated code should be complete, syntactically correct, and executable.
        """
        
        # User prompt with task details
        user_prompt = f"""
        Generate a Python class for the following trading strategy:
        
        Strategy Name: {task.name}
        Description: {task.description}
        Parameters: {task.parameters}
        
        Requirements:
        1. The class must inherit from BaseStrategy
        2. Implement the generate_signals method that takes a pandas DataFrame and returns a pandas Series of signals
        3. Use the parameters provided in the strategy logic
        4. The code should be self-contained and import all necessary libraries
        5. Include comments explaining the strategy logic
        
        Example template:
        ```python
        import pandas as pd
        import numpy as np
        from strategies.base_strategy import BaseStrategy
        
        class {task.name}(BaseStrategy):
            def __init__(self, params):
                super().__init__(params)
                
            def generate_signals(self, data):
                # Strategy logic here
                signals = pd.Series(0, index=data.index)
                # ... implementation ...
                return signals
        ```
        """
        
        # Get code from LLM
        response = APIBackend().build_messages_and_create_chat_completion(
            user_prompt=user_prompt,
            system_prompt=system_prompt
        )
        
        # Extract code from markdown code blocks if present
        if "```python" in response:
            code = response.split("```python")[1].split("```")[0]
        elif "```" in response:
            code = response.split("```")[1].split("```")[0]
        else:
            code = response
            
        return code