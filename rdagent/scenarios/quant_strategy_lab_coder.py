import os
import tempfile
from pathlib import Path
from rdagent.components.coder.CoSTEER import CoSTEER
from rdagent.components.coder.CoSTEER.evaluators import CoSTEERMultiEvaluator
from rdagent.scenarios.quant_strategy_lab_experiment import StrategyExperiment, TaskWorkspace
from rdagent.scenarios.quant_strategy_lab_scenario import CustomStrategyScenario
from rdagent.scenarios.quant_strategy_lab_evaluator import StrategyEvaluator, StrategyFeedback
from rdagent.scenarios.quant_strategy_lab_evolving_strategy import StrategyEvolvingStrategy
from rdagent.scenarios.quant_strategy_lab_settings import StrategyCoSTEERSettings
from rdagent.scenarios.quant_strategy_lab_runner import CustomStrategyRunner
from rdagent.oai.llm_utils import APIBackend
from rdagent.core.experiment import FBWorkspace
from rdagent.log import rdagent_logger as logger
import json

class CustomStrategyCoder(CoSTEER):
    def __init__(self, scen: CustomStrategyScenario) -> None:
        """
        Initialize the Custom Strategy Coder with CoSTEER evolution system.
        
        Parameters:
        - scen: CustomStrategyScenario instance
        """
        # Initialize CoSTEER settings
        settings = StrategyCoSTEERSettings()
        
        # Create strategy runner for evaluation
        runner = CustomStrategyRunner(scen)
        
        # Create evaluator
        evaluator = CoSTEERMultiEvaluator([StrategyEvaluator(scen, runner)], scen)
        
        # Create evolving strategy
        evolving_strategy = StrategyEvolvingStrategy(scen)
        
        # Initialize CoSTEER with strategy-specific components
        super().__init__(
            settings=settings,
            eva=evaluator,
            es=evolving_strategy,
            scen=scen
        )
        
    def develop(self, exp: StrategyExperiment) -> StrategyExperiment:
        """
        Develop strategy code using CoSTEER evolution system.
        This will create initial implementations and then iteratively improve them.
        """
        # Generate initial strategy implementations for all tasks
        workspaces = []
        
        for task in exp.sub_tasks:
            try:
                # Generate initial strategy code
                code = self._generate_strategy_code(task)
                
                if code and code.strip():
                    # Create TaskWorkspace for CoSTEER evolution
                    workspace = TaskWorkspace(task, exp.experiment_workspace.workspace_path)
                    workspace.file_dict = {f"{task.sanitized_name}.py": code}
                    
                    # Save code to experiment workspace
                    exp.experiment_workspace.save_strategy(task, code)
                    workspaces.append(workspace)
                    logger.info(f"Initial strategy generated for task: {task.name}")
                else:
                    workspaces.append(None)
                    logger.warning(f"Failed to generate initial strategy for task: {task.name}")
                    
            except Exception as e:
                logger.error(f"Exception generating initial strategy for task {task.name}: {e}")
                workspaces.append(None)
        
        # Set initial workspaces
        exp.sub_workspace_list = workspaces
        
        # Now let CoSTEER handle the iterative evolution
        logger.info("Starting CoSTEER evolution for strategy improvement...")
        evolved_exp = super().develop(exp)
        
        return evolved_exp
        
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
        2. Implement BOTH required abstract methods:
           - get_default_params(): Return dict of default parameter values
           - generate_signals(): Takes DataFrame, returns Series of signals
        3. Use the parameters provided in the strategy logic
        4. The code should be self-contained and import all necessary libraries
        5. Include comments explaining the strategy logic
        6. Signal values: 1 (buy), -1 (sell), 0 (hold)
        7. IMPORTANT: Use lowercase column names: 'open', 'high', 'low', 'close', 'volume'
        8. NOTE: For pair strategies needing multiple symbols, ensure the strategy can handle single-symbol data gracefully
        
        Example template:
        ```python
        import pandas as pd
        import numpy as np
        from strategies.base_strategy import BaseStrategy
        from strategies import register_strategy
        
        @register_strategy(name="{task.name}", category="RD-Agent Generated")
        class {task.name}(BaseStrategy):
            def __init__(self, params=None):
                if params is None:
                    params = {{}}
                super().__init__(params)
            
            def get_default_params(self):
                \"\"\"Return default parameters for this strategy.\"\"\"
                return {{
                    'param1': 10,
                    'param2': 0.5,
                    # Add more parameters based on the strategy requirements
                }}
                
            def generate_signals(self, data):
                \"\"\"Generate trading signals from market data.\"\"\"
                # Data columns: 'open', 'high', 'low', 'close', 'volume' (lowercase)
                # Strategy logic here
                signals = pd.Series(0, index=data.index)
                # ... implementation using data['close'], data['high'], etc. ...
                return signals
        ```
        
        CRITICAL: You MUST implement get_default_params() method that returns a dictionary of parameter names and their default values based on the strategy requirements.
        """
        
        # Get code from LLM
        response = APIBackend().build_messages_and_create_chat_completion(
            user_prompt=user_prompt,
            system_prompt=system_prompt
        )
        
        # Extract code from markdown code blocks if present
        if "```python" in response:
            code = response.split("```python")[1].split("```")[0].strip()
        elif "```" in response:
            code = response.split("```")[1].split("```")[0].strip()
        else:
            code = response.strip()
            
        # Additional cleaning - if the response looks like it's just code, return it
        if not code and response.strip().startswith(('import ', 'from ', 'class ', '@')):
            code = response.strip()
            
        return code