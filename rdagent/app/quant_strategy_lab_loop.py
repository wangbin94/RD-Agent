import asyncio
import json
from typing import Optional
import fire
from rdagent.components.workflow.rd_loop import RDLoop
from rdagent.core.exception import RunnerError
from rdagent.core.utils import import_class
from rdagent.log import rdagent_logger as logger
from rdagent.scenarios.quant_strategy_lab_conf import CUSTOM_STRATEGY_PROP_SETTING

class CustomStrategyRDLoop(RDLoop):
    """Custom RD Loop for strategy research using quant-strategy-lab"""
    
    def __init__(self, PROP_SETTING=None):
        if PROP_SETTING is None:
            PROP_SETTING = CUSTOM_STRATEGY_PROP_SETTING
        super().__init__(PROP_SETTING)

def main(
    path: Optional[str] = None,
    step_n: Optional[int] = None,
    loop_n: Optional[int] = None,
    data_path: str = "data",
    framework: str = "vectorbt",
    strategy_name: Optional[str] = None,
):
    """
    Run the custom strategy research loop.
    
    Parameters:
    - path: Path to continue from a previous session
    - step_n: Number of steps to run
    - loop_n: Number of loops to run
    - data_path: Path to the directory containing CSV data files
    - framework: Backtesting framework to use (vectorbt, backtrader, qlib)
    - strategy_name: Name of a specific strategy to research (optional)
    """
    
    # Update configuration with command line arguments
    CUSTOM_STRATEGY_PROP_SETTING.data_path = data_path
    CUSTOM_STRATEGY_PROP_SETTING.framework = framework
    
    if path is None:
        strategy_loop = CustomStrategyRDLoop(CUSTOM_STRATEGY_PROP_SETTING)
    else:
        strategy_loop = CustomStrategyRDLoop.load(path)
        
    asyncio.run(strategy_loop.run(step_n=step_n, loop_n=loop_n))

if __name__ == "__main__":
    fire.Fire(main)