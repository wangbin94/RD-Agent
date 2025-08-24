import subprocess
import json
import tempfile
from pathlib import Path
from rdagent.core.developer import Developer
from rdagent.scenarios.quant_strategy_lab_experiment import StrategyExperiment
from rdagent.scenarios.quant_strategy_lab_scenario import CustomStrategyScenario

class CustomStrategyRunner(Developer):
    def __init__(self, scen: CustomStrategyScenario) -> None:
        """
        Initialize the Custom Strategy Runner.
        
        Parameters:
        - scen: CustomStrategyScenario instance
        """
        super().__init__(scen)
        self.data_path = scen.data_path
        self.framework = scen.framework
        
    def develop(self, exp: StrategyExperiment) -> StrategyExperiment:
        """
        Run the generated strategy using quant-strategy-lab framework.
        
        Parameters:
        - exp: StrategyExperiment containing generated code
        
        Returns:
        - StrategyExperiment with results from backtesting
        """
        # For now, we'll run the first strategy in the experiment
        # In a more complex implementation, we might run all strategies
        if not exp.sub_tasks:
            exp.stdout = "No strategies to run"
            exp.result = {"error": "No strategies to run"}
            return exp
            
        task = exp.sub_tasks[0]
        strategy_file = exp.experiment_workspace.get_strategy_file_path(task.name)
        
        if not strategy_file.exists():
            exp.stdout = f"Strategy file not found: {strategy_file}"
            exp.result = {"error": f"Strategy file not found: {strategy_file}"}
            return exp
            
        # Find a CSV data file to use
        csv_files = list(self.data_path.glob("*.csv"))
        if not csv_files:
            exp.stdout = f"No CSV files found in {self.data_path}"
            exp.result = {"error": f"No CSV files found in {self.data_path}"}
            return exp
            
        data_file = csv_files[0]  # Use the first CSV file
        
        # Run the quant-strategy-lab framework as a subprocess
        try:
            # Construct the command to run the experiment
            cmd = [
                "python",
                "/home/wang/dl/quant-strategy-lab/run_experiment.py",
                "--strategy", str(strategy_file),
                "--framework", self.framework,
                "--data", str(data_file),
                "--output", "json"  # Request JSON output for easier parsing
            ]
            
            # Execute the command
            result = subprocess.run(
                cmd,
                cwd="/home/wang/dl/quant-strategy-lab",
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Store stdout
            exp.stdout = result.stdout + result.stderr
            
            # Parse the results
            if result.returncode == 0:
                # Try to parse JSON output if possible
                try:
                    # If the output is JSON, parse it
                    exp.result = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # If not JSON, create a simple result object
                    exp.result = {
                        "status": "success",
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
            else:
                exp.result = {
                    "status": "error",
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            exp.stdout = "Strategy execution timed out"
            exp.result = {"error": "Strategy execution timed out"}
        except Exception as e:
            exp.stdout = f"Error running strategy: {str(e)}"
            exp.result = {"error": f"Error running strategy: {str(e)}"}
            
        return exp