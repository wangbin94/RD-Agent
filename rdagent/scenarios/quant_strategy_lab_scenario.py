import subprocess
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from rdagent.core.scenario import Scenario
from rdagent.core.experiment import Task
from rdagent.utils.agent.tpl import T
from rdagent.oai.llm_utils import APIBackend

class CustomStrategyScenario(Scenario):
    def __init__(self, data_path: str = "data", framework: str = "vectorbt") -> None:
        """
        Initialize the Custom Strategy Scenario for quant-strategy-lab.
        
        Parameters:
        - data_path: Path to the directory containing CSV data files.
        - framework: The backtesting framework to use (vectorbt, backtrader, qlib).
        """
        self.data_path = Path(data_path)
        self.framework = framework
        self._background = self._generate_background()
        self._source_data = self._get_data_folder_intro()
        self._rich_style_description = self._generate_rich_description()
        
    def _generate_background(self) -> str:
        """Generate background information for the scenario."""
        return f"""
        This scenario is designed for automated strategy research using the quant-strategy-lab framework.
        The framework supports multiple backtesting engines including VectorBT, Backtrader, and Qlib.
        Strategies are defined by inheriting from a BaseStrategy class and implementing generate_signals method.
        Data is provided in CSV format with OHLCV columns.
        Framework selected for this research: {self.framework}
        """
        
    def _get_data_folder_intro(self) -> str:
        """Get description of available data files."""
        if not self.data_path.exists():
            return "Data directory not found."
            
        csv_files = list(self.data_path.glob("*.csv"))
        if not csv_files:
            return "No CSV files found in data directory."
            
        file_descriptions = []
        for csv_file in csv_files[:3]:  # Limit to first 3 files for brevity
            file_descriptions.append(f"- {csv_file.name} ({csv_file.stat().st_size} bytes)")
            
        description = f"Available data files in '{self.data_path}':\n" + "\n".join(file_descriptions)
        if len(csv_files) > 3:
            description += f"\n... and {len(csv_files) - 3} more files."
            
        return description
        
    def _generate_rich_description(self) -> str:
        """Generate rich style description for UI presentation."""
        return f"## Custom Strategy Research Scenario\n\nFramework: **{self.framework}**\nData Path: **{self.data_path}**"
        
    @property
    def background(self) -> str:
        return self._background
        
    def get_source_data_desc(self, task: Optional[Task] = None) -> str:
        return self._source_data
        
    @property
    def rich_style_description(self) -> str:
        return self._rich_style_description
        
    def get_scenario_all_desc(
        self, 
        task: Optional[Task] = None, 
        filtered_tag: Optional[str] = None, 
        simple_background: Optional[bool] = None
    ) -> str:
        """Combine all scenario descriptions."""
        if simple_background:
            return f"Background of the scenario:\n{self.background}"
        return f"""Background of the scenario:
{self.background}
The source data you can use:
{self.get_source_data_desc(task)}
The interface you should follow to write the runnable code:
- Strategies must inherit from BaseStrategy class
- Implement generate_signals method that returns a pandas Series of signals
- Use available data files in the specified data directory
The simulator user can use to test your strategy:
- The quant-strategy-lab framework with {self.framework} backend
"""
        
    def get_runtime_environment(self) -> str:
        """Get information about the runtime environment."""
        try:
            # Get Python version
            python_version = subprocess.check_output(["python", "--version"], stderr=subprocess.STDOUT).decode().strip()
            
            # Get installed packages related to our framework
            installed_packages = subprocess.check_output(["pip", "list"], stderr=subprocess.STDOUT).decode().strip()
            relevant_packages = []
            for line in installed_packages.split('\n'):
                if any(pkg in line.lower() for pkg in ['vectorbt', 'backtrader', 'qlib', 'pandas', 'numpy']):
                    relevant_packages.append(line)
                    
            return f"Python Version: {python_version}\nRelevant Packages:\n" + "\n".join(relevant_packages)
        except Exception as e:
            return f"Error getting runtime environment: {str(e)}"