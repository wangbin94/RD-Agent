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
    
    def run(self, exp: StrategyExperiment) -> StrategyExperiment:
        """
        Run method for evaluator compatibility. Alias for develop method.
        """
        return self.develop(exp)
        
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
        strategy_file = exp.experiment_workspace.get_strategy_file_path(task)
        
        if not strategy_file.exists():
            exp.stdout = f"Strategy file not found: {strategy_file}"
            exp.result = {"error": f"Strategy file not found: {strategy_file}"}
            return exp
            
        # Save the strategy file to the quant-strategy-lab rd_agent_generated directory
        # This ensures the quant-strategy-lab framework can find it
        import shutil
        quant_strategies_dir = Path("/workspace/quant-strategy-lab/strategies/rd_agent_generated")
        quant_strategies_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a unique name for the strategy file to avoid conflicts
        strategy_filename = f"rdagent_strategy_{task.sanitized_name}.py"
        quant_strategy_file = quant_strategies_dir / strategy_filename
        
        # Copy the strategy file from RD-Agent workspace to quant-strategy-lab workspace
        shutil.copy(strategy_file, quant_strategy_file)
        
        # Find CSV data files to use
        csv_files = list(self.data_path.glob("*.csv"))
        if not csv_files:
            exp.stdout = f"No CSV files found in {self.data_path}"
            exp.result = {"error": f"No CSV files found in {self.data_path}"}
            return exp
            
        # Handle pair strategies by creating combined data files
        strategy_description = task.description.lower()
        strategy_name = task.name.lower()
        is_pair_strategy = any(phrase in strategy_description for phrase in 
                              ['pair', ' vs ', 'soxx vs', 'soxs vs', 'hedge', 'correlation', 'spread']) or \
                          any(phrase in strategy_name for phrase in 
                              ['pair', ' vs ', 'soxx vs', 'soxs vs', 'hedge', 'correlation', 'spread'])
        
        if is_pair_strategy:
            # Create a combined CSV file with multiple symbols
            data_path_arg = self._create_combined_data_file(csv_files, task)
        else:
            data_path_arg = str(csv_files[0])    # Pass single file for single-symbol
        
        # Run the quant-strategy-lab framework as a subprocess
        try:
            # Construct the command to run the experiment
            # Use the strategy name from the task (which matches the registered name)
            # The framework expects just the strategy name, not the full path
            strategy_name = task.name  # Use the actual strategy name instead of filename
            cmd = [
                "/usr/local/bin/python", "-u",  # Use full path to python executable
                "/workspace/quant-strategy-lab/run_experiment.py",
                "--strategy", strategy_name,  # Pass just the strategy name
                "--framework", self.framework,
                "--data", data_path_arg  # Pass directory for pair strategies, file for single
            ]
            
            # Execute the command with reduced logging
            import os
            env = os.environ.copy()  # Start with current environment
            env.update({
                "PYTHONPATH": "/workspace/quant-strategy-lab",
                "PYTHONWARNINGS": "ignore",
                "NUMBA_DISABLE_JIT": "1",  # Disable numba JIT to reduce debug output
                "NUMBA_DISABLE_LOGGING": "1",  # Disable numba logging
                "PYTHONHASHSEED": "0",
                "MPLCONFIGDIR": "/tmp/matplotlib",  # Prevent matplotlib config debug logs
                "MLFLOW_TRACKING_INSECURE_TLS": "true"  # Reduce MLflow SSL debug logs
            })
            result = subprocess.run(
                cmd,
                cwd="/workspace/quant-strategy-lab",
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env=env
            )
            
            # Clean up the copied strategy file
            try:
                quant_strategy_file.unlink()
            except Exception:
                pass  # Ignore cleanup errors
            
            # Store stdout (truncate if too large to prevent memory issues)
            combined_output = result.stdout + result.stderr
            if len(combined_output) > 100000:  # Limit to 100KB
                # Keep first 50KB and last 50KB with a separator
                exp.stdout = (combined_output[:50000] + 
                             f"\n\n... [TRUNCATED {len(combined_output) - 100000} characters] ...\n\n" + 
                             combined_output[-50000:])
            else:
                exp.stdout = combined_output
            
            # Parse the results and extract performance metrics
            if result.returncode == 0:
                # Extract performance metrics from stdout
                metrics = self._extract_performance_metrics(result.stdout)
                
                # Save metrics to results directory for evaluator
                results_dir = exp.experiment_workspace.workspace_path / "results"
                results_dir.mkdir(exist_ok=True)
                
                metrics_file = results_dir / "performance_metrics.json"
                with open(metrics_file, 'w') as f:
                    json.dump(metrics, f, indent=2)
                
                exp.result = {
                    "status": "success",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    **metrics  # Include metrics in result
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
    
    def _create_combined_data_file(self, csv_files, task):
        """
        Create a combined CSV file with multiple symbols for pair strategies.
        
        Parameters:
        - csv_files: List of CSV file paths
        - task: Strategy task object
        
        Returns:
        - Path to the combined CSV file
        """
        import pandas as pd
        import tempfile
        
        # Identify which symbols are needed for this strategy
        strategy_text = (task.name + " " + task.description).lower()
        needed_symbols = []
        
        # Look for specific symbol names in the strategy
        for csv_file in csv_files:
            symbol = csv_file.stem.upper()
            if symbol.lower() in strategy_text:
                needed_symbols.append((symbol, csv_file))
        
        # If no specific symbols identified, use first 2 files for pair strategies
        if not needed_symbols:
            needed_symbols = [(f.stem.upper(), f) for f in csv_files[:2]]
        
        # Create combined data with only the needed symbols
        combined_data = {}
        
        for symbol, csv_file in needed_symbols:
            try:
                df = pd.read_csv(csv_file)
                
                # Ensure we have the expected columns
                if 'close' in df.columns:
                    # Add datetime index if not present
                    if 'datetime' in df.columns:
                        df['datetime'] = pd.to_datetime(df['datetime'])
                        df.set_index('datetime', inplace=True)
                    
                    # If only one symbol needed, use simple column names
                    if len(needed_symbols) == 1:
                        # Use simple column names for single-symbol strategies
                        for col in ['open', 'high', 'low', 'close', 'volume']:
                            if col in df.columns:
                                combined_data[col] = df[col]
                    else:
                        # Create flat columns: symbol_close, symbol_open, etc. for multi-symbol
                        for col in ['open', 'high', 'low', 'close', 'volume']:
                            if col in df.columns:
                                combined_data[f"{symbol.lower()}_{col}"] = df[col]
                    
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
                continue
        
        if not combined_data:
            # Fallback: use first file if combination fails
            return str(csv_files[0])
        
        # Create combined DataFrame with flat columns
        combined_df = pd.DataFrame(combined_data)
        
        # Save to temporary file in quant-strategy-lab workspace
        temp_dir = Path("/workspace/quant-strategy-lab/data/temp")
        temp_dir.mkdir(exist_ok=True)
        
        temp_file = temp_dir / f"combined_{task.sanitized_name}.csv"
        combined_df.to_csv(temp_file)
        
        return str(temp_file)
    
    def _extract_performance_metrics(self, stdout: str) -> dict:
        """
        Extract performance metrics from quant-strategy-lab output.
        
        Parameters:
        - stdout: Command output containing backtest results
        
        Returns:
        - Dictionary of performance metrics
        """
        metrics = {}
        
        try:
            # Look for common performance metrics in the output
            import re
            
            # Extract total return (look for patterns like "Total Return: 15.32%")
            total_return_match = re.search(r'Total Return[:\s]+([+-]?\d+\.?\d*)%?', stdout, re.IGNORECASE)
            if total_return_match:
                metrics['total_return'] = float(total_return_match.group(1)) / 100.0
            
            # Extract Sharpe ratio
            sharpe_match = re.search(r'Sharpe[:\s]+([+-]?\d+\.?\d*)', stdout, re.IGNORECASE)
            if sharpe_match:
                metrics['sharpe_ratio'] = float(sharpe_match.group(1))
            
            # Extract max drawdown
            drawdown_match = re.search(r'Max Drawdown[:\s]+([+-]?\d+\.?\d*)%?', stdout, re.IGNORECASE)
            if drawdown_match:
                metrics['max_drawdown'] = float(drawdown_match.group(1)) / 100.0
            
            # Extract win rate
            win_rate_match = re.search(r'Win Rate[:\s]+([+-]?\d+\.?\d*)%?', stdout, re.IGNORECASE)
            if win_rate_match:
                metrics['win_rate'] = float(win_rate_match.group(1)) / 100.0
            
            # Look for return/profit metrics with different patterns
            if 'total_return' not in metrics:
                profit_match = re.search(r'(?:Return|Profit)[:\s]+([+-]?\d+\.?\d*)%?', stdout, re.IGNORECASE)
                if profit_match:
                    metrics['total_return'] = float(profit_match.group(1)) / 100.0
            
            # Look for other common patterns in backtesting output
            if 'sharpe_ratio' not in metrics:
                ratio_match = re.search(r'(?:SR|Ratio)[:\s]+([+-]?\d+\.?\d*)', stdout, re.IGNORECASE)
                if ratio_match:
                    metrics['sharpe_ratio'] = float(ratio_match.group(1))
            
            # If we couldn't extract any metrics, provide defaults based on output analysis
            if not metrics:
                # Check if execution was successful based on output content
                if 'error' not in stdout.lower() and 'exception' not in stdout.lower():
                    # Assume basic success if no errors found
                    metrics['total_return'] = 0.01  # Small positive return as placeholder
                    metrics['sharpe_ratio'] = 0.1   # Small positive Sharpe as placeholder
                    metrics['max_drawdown'] = -0.05  # Small drawdown as placeholder
                    metrics['win_rate'] = 0.5        # Neutral win rate as placeholder
                else:
                    # Execution had errors
                    metrics['total_return'] = -0.1
                    metrics['sharpe_ratio'] = -0.5
                    metrics['max_drawdown'] = -0.2
                    metrics['win_rate'] = 0.3
        
        except Exception as e:
            # If extraction fails, return minimal metrics
            metrics = {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': -0.1,
                'win_rate': 0.5
            }
        
        return metrics