from rdagent.core.scenario import Scenario
from rdagent.scenarios.general_model.scenario import GeneralModelScenario
from rdagent.core.evolving_framework import EvolvingStrategy, EvolvableSubjects
from rdagent.core.evaluation import Evaluator
from rdagent.core.developer import Developer
from rdagent.core.experiment import ASpecificExp
import os
import subprocess
from dataclasses import dataclass
import json
import random
import pickle
from datetime import datetime
from pathlib import Path

# Define a local Feedback dataclass to match expected usage
@dataclass
class Feedback:
    is_finished: bool
    is_acceptable: bool
    feedback_info: dict

# Helper classes for UI compatibility
class TargetTask:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        
class EvolutionWorkspace:
    def __init__(self, round_num, strategy_info, metrics, status):
        self.round = round_num
        self.strategy_name = strategy_info.name
        self.strategy_type = strategy_info.strategy_type
        self.parameters = strategy_info.params
        self.metrics = metrics
        self.status = status
        self.timestamp = datetime.now().isoformat()
        
        self.target_task = TargetTask(
            name=f"Strategy Evolution Round {round_num}",
            description=f"Evolving {strategy_info.strategy_type} strategy with parameters {strategy_info.params}"
        )

class FeedbackObject:
    def __init__(self, round_num, strategy_info, final_decision, metrics, feedback_text):
        self.final_decision = final_decision
        self.metrics = metrics
        self.feedback_text = feedback_text
        self.round = round_num
        self.strategy_name = strategy_info.name

# Simple RD-Agent compatible logging
class SimpleRDAgentLogger:
    def __init__(self):
        self.log_dir = Path(f"/workspace/RD-Agent/log/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')}")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.round_count = 0
        
    def log_evolution_round(self, round_num, strategy_info, metrics, status):
        """Log evolution round information using expected UI tags"""
        
        # Log as "evolving code" (what the UI expects)
        evolving_dir = self.log_dir / "evolving code" / "1"
        evolving_dir.mkdir(parents=True, exist_ok=True)
        
        # Create workspace object that UI expects using SimpleNamespace
        from types import SimpleNamespace
        
        target_task = SimpleNamespace(
            name=f"Strategy Evolution Round {round_num}",
            description=f"Evolving {strategy_info.strategy_type} strategy with parameters {strategy_info.params}"
        )
        
        evolution_workspace = SimpleNamespace(
            round=round_num,
            strategy_name=strategy_info.name,
            strategy_type=strategy_info.strategy_type,
            parameters=strategy_info.params,
            metrics=metrics,
            status=status,
            timestamp=datetime.now().isoformat(),
            target_task=target_task
        )
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
        pkl_file = evolving_dir / f"{timestamp}.pkl"
        
        with open(pkl_file, 'wb') as f:
            pickle.dump([evolution_workspace], f)  # Wrap in list as UI expects array
            
        # Also log as feedback
        self.log_evolution_feedback(round_num, strategy_info, metrics, status)
        
        print(f"Logged evolution round {round_num} to {pkl_file}")
        
    def log_evolution_feedback(self, round_num, strategy_info, metrics, status):
        """Log feedback for this evolution round"""
        feedback_dir = self.log_dir / "evolving feedback" / "1"
        feedback_dir.mkdir(parents=True, exist_ok=True)
        
        # Use a simple namespace object that can be pickled
        from types import SimpleNamespace
        
        is_acceptable = status == "success" and metrics.get("sharpe_ratio", -float('inf')) > 1.0
        feedback_obj = SimpleNamespace(
            final_decision=is_acceptable,
            metrics=metrics,
            feedback_text=f"Strategy {strategy_info.name} achieved Sharpe ratio of {metrics.get('sharpe_ratio', 'N/A'):.2f}",
            round=round_num,
            strategy_name=strategy_info.name
        )
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
        pkl_file = feedback_dir / f"{timestamp}.pkl"
        
        with open(pkl_file, 'wb') as f:
            pickle.dump([feedback_obj], f)  # Wrap in list as UI expects array
        
    def log_scenario_info(self, scenario_instance):
        """Log scenario background information"""
        scenario_dir = self.log_dir / "scenario" / "1" 
        scenario_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a simple GeneralModelScenario instance that can be unpickled
        from rdagent.scenarios.general_model.scenario import GeneralModelScenario
        
        # Create a basic GeneralModelScenario object
        simple_scenario = GeneralModelScenario()
        
        # Override the background property with our custom text
        simple_scenario._background = "Discovering an optimal day trading strategy for QQQ data by evolving strategy types and parameters."
        simple_scenario._rich_style_description = """
# Optimal Day Trading Strategy Discovery

This scenario aims to discover an optimal day trading strategy for the QQQ dataset.
It employs an evolutionary approach to explore different strategy types (e.g., Moving Average, RSI)
and their parameters, optimizing for the Sharpe Ratio.

## Framework: VectorBT
## Data: QQQ 5-minute data
## Optimization Metric: Sharpe Ratio
## Acceptance Threshold: > 1.0
"""
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
        pkl_file = scenario_dir / f"{timestamp}.pkl"
        
        with open(pkl_file, 'wb') as f:
            pickle.dump(simple_scenario, f)
            
    def log_final_summary(self, best_strategy, total_rounds):
        """Log final summary"""
        summary_dir = self.log_dir / "summary" / "1"
        summary_dir.mkdir(parents=True, exist_ok=True)
        
        summary_data = {
            "total_rounds": total_rounds,
            "best_strategy": best_strategy.name if best_strategy else None,
            "best_params": best_strategy.params if best_strategy else None,
            "completed": True,
            "timestamp": datetime.now().isoformat()
        }
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
        pkl_file = summary_dir / f"{timestamp}.pkl"
        
        with open(pkl_file, 'wb') as f:
            pickle.dump(summary_data, f)

# Define the location of the quant-strategy-lab
QUANT_LAB_PATH = "/workspace/quant-strategy-lab"
STRATEGY_DIR = os.path.join(QUANT_LAB_PATH, "strategies", "rd_agent_generated")
DATA_PATH = os.path.join(QUANT_LAB_PATH, "data/2025-05-09/5m/QQQ.csv")

# Ensure the strategy directory exists
os.makedirs(STRATEGY_DIR, exist_ok=True)
# Ensure rd_agent_generated is a Python package
with open(os.path.join(STRATEGY_DIR, "__init__.py"), "a"):
    pass

# --- Strategy Templates (Simplified for demonstration) ---

def generate_ma_crossover_strategy_code(strategy_name, short_window, long_window):
    return f"""
from strategies.base_strategy import BaseStrategy
from strategies import register_strategy
import pandas as pd
import numpy as np
from typing import Dict, Any, Union

@register_strategy(name="{strategy_name}", category="Moving Average")
class {strategy_name}(BaseStrategy):
    def get_default_params(self) -> Dict[str, Any]:
        return {{'short_window': {short_window}, 'long_window': {long_window}}}

    def generate_signals(self, data: pd.DataFrame) -> Union[pd.Series, np.ndarray]:
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column.")
        short_window = self.get_param('short_window')
        long_window = self.get_param('long_window')
        data['short_mavg'] = data['close'].rolling(window=short_window, min_periods=1).mean()
        data['long_mavg'] = data['close'].rolling(window=long_window, min_periods=1).mean()
        signals = pd.Series(np.zeros(len(data)), index=data.index)
        signals[data['short_mavg'] > data['long_mavg']] = 1.0 # Buy signal
        signals[data['short_mavg'] < data['long_mavg']] = -1.0 # Sell signal
        return signals
"""

def generate_rsi_strategy_code(strategy_name, rsi_period, rsi_buy_threshold, rsi_sell_threshold):
    return f"""
from strategies.base_strategy import BaseStrategy
from strategies import register_strategy
import pandas as pd
import numpy as np
from typing import Dict, Any, Union

@register_strategy(name="{strategy_name}", category="RSI")
class {strategy_name}(BaseStrategy):
    def get_default_params(self) -> Dict[str, Any]:
        return {{'rsi_period': {rsi_period}, 'rsi_buy_threshold': {rsi_buy_threshold}, 'rsi_sell_threshold': {rsi_sell_threshold}}}

    def generate_signals(self, data: pd.DataFrame) -> Union[pd.Series, np.ndarray]:
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column.")
        
        rsi_period = self.get_param('rsi_period')
        rsi_buy_threshold = self.get_param('rsi_buy_threshold')
        rsi_sell_threshold = self.get_param('rsi_sell_threshold')

        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        signals = pd.Series(np.zeros(len(data)), index=data.index)
        signals[rsi < rsi_buy_threshold] = 1.0 # Buy signal
        signals[rsi > rsi_sell_threshold] = -1.0 # Sell signal
        return signals
"""

class OptimalTradingStrategy(EvolvableSubjects):
    def __init__(self, name: str, code: str, strategy_type: str, params: dict = None):
        super().__init__()
        self.name = name
        self.code = code
        self.strategy_type = strategy_type
        self.params = params if params is not None else {}

    def __str__(self):
        return f"Strategy(name='{self.name}', type='{self.strategy_type}', params='{self.params}')"


class OptimalStrategyEvolver(EvolvingStrategy):
    def evolve(self, evolvable_subjects: OptimalTradingStrategy, evolving_trace):
        strategy_name = f"DynamicStrategy_{random.randint(1000, 9999)}"
        
        # Randomly choose a strategy type to generate
        strategy_choices = ["ma_crossover", "rsi"]
        chosen_strategy_type = random.choice(strategy_choices)

        new_params = {}
        strategy_code = ""

        if chosen_strategy_type == "ma_crossover":
            # Evolve MA parameters
            short_window = random.randint(5, 20)
            long_window = random.randint(21, 50)
            if evolvable_subjects.strategy_type == "ma_crossover" and evolvable_subjects.params:
                # If previous was MA, try to perturb existing params
                prev_short = evolvable_subjects.params.get('short_window', 10)
                prev_long = evolvable_subjects.params.get('long_window', 30)
                short_window = max(5, prev_short + random.randint(-5, 5))
                long_window = max(short_window + 1, prev_long + random.randint(-10, 10))
            
            new_params = {'short_window': short_window, 'long_window': long_window}
            strategy_code = generate_ma_crossover_strategy_code(strategy_name, short_window, long_window)
        
        elif chosen_strategy_type == "rsi":
            # Evolve RSI parameters
            rsi_period = random.randint(10, 20)
            rsi_buy_threshold = random.randint(20, 40)
            rsi_sell_threshold = random.randint(60, 80)
            if evolvable_subjects.strategy_type == "rsi" and evolvable_subjects.params:
                # If previous was RSI, try to perturb existing params
                prev_period = evolvable_subjects.params.get('rsi_period', 14)
                prev_buy = evolvable_subjects.params.get('rsi_buy_threshold', 30)
                prev_sell = evolvable_subjects.params.get('rsi_sell_threshold', 70)
                rsi_period = max(5, prev_period + random.randint(-3, 3))
                rsi_buy_threshold = max(10, min(50, prev_buy + random.randint(-5, 5)))
                rsi_sell_threshold = max(50, min(90, prev_sell + random.randint(-5, 5)))

            new_params = {'rsi_period': rsi_period, 'rsi_buy_threshold': rsi_buy_threshold, 'rsi_sell_threshold': rsi_sell_threshold}
            strategy_code = generate_rsi_strategy_code(strategy_name, rsi_period, rsi_buy_threshold, rsi_sell_threshold)

        # Write the strategy file to the quant-strategy-lab project
        strategy_file_path = os.path.join(STRATEGY_DIR, f"{strategy_name.lower()}.py")
        with open(strategy_file_path, "w") as f:
            f.write(strategy_code)

        print(f"Generated strategy file: {strategy_file_path}")
        subprocess.run(f"ls -l {STRATEGY_DIR}", shell=True, check=True)

        return OptimalTradingStrategy(name=strategy_name, code=strategy_code, strategy_type=chosen_strategy_type, params=new_params)


class OptimalDayTradingEvaluator(Evaluator):
    def evaluate(self, evaluable_obj: OptimalTradingStrategy):
        command = (
            f"python {QUANT_LAB_PATH}/run_experiment.py "
            f"--strategy {evaluable_obj.name} "
            f"--framework vectorbt "
            f"--data {DATA_PATH} "
            f"--start-date 2024-01-01 --end-date 2024-12-31"
        )

        process = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if process.returncode == 0:
            metrics = {}
            metrics_start_tag = "###METRICS_START###"
            metrics_end_tag = "###METRICS_END###"
            
            stdout_lines = process.stdout.splitlines()
            for line in stdout_lines:
                if metrics_start_tag in line and metrics_end_tag in line:
                    json_str = line.split(metrics_start_tag)[1].split(metrics_end_tag)[0]
                    try:
                        metrics = json.loads(json_str)
                        break
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON metrics: {json_str}")

            # Optimization Goal: Maximize Sharpe Ratio
            sharpe_ratio = metrics.get('sharpe_ratio', -float('inf')) # Default to negative infinity for minimization
            
            # Define acceptance criteria based on Sharpe Ratio
            is_acceptable = sharpe_ratio > 1.0 # Example threshold for a good Sharpe Ratio

            print(f"Backtest successful for {evaluable_obj.name}. Metrics: {metrics}")
            return Feedback(is_finished=True, is_acceptable=is_acceptable, feedback_info={"status": "success", "details": process.stdout, "metrics": metrics, "sharpe_ratio": sharpe_ratio})
        else:
            print(f"Backtest failed for {evaluable_obj.name}.")
            error_details = f"Return Code: {process.returncode}\nStdout: {process.stdout}\nStderr: {process.stderr}"
            return Feedback(is_finished=True, is_acceptable=False, feedback_info={"status": "failure", "details": error_details})


class CustomDeveloper(Developer):
    def __init__(self, scen: Scenario, evolving_strategy: EvolvingStrategy, evaluator: Evaluator, evolvable_subjects: EvolvableSubjects):
        super().__init__(scen)
        self.evolving_strategy = evolving_strategy
        self.evaluator = evaluator
        self.evolvable_subjects = evolvable_subjects
        self.best_sharpe_ratio = -float('inf')
        self.best_strategy = None
        self.logger = SimpleRDAgentLogger()
        
        # Log scenario initialization
        self.logger.log_scenario_info(scen)

    def develop(self, exp: ASpecificExp) -> ASpecificExp:
        print("CustomDeveloper.develop called (placeholder).")
        return exp

    def multistep_evolve(self, max_round: int):
        current_subjects = self.evolvable_subjects
        for i in range(max_round):
            print(f"\nEvolution round {i+1}/{max_round}")
            evolved_subjects = self.evolving_strategy.evolve(current_subjects, evolving_trace=[])
            print(f"Evolved to: {evolved_subjects}")

            feedback = self.evaluator.evaluate(evolved_subjects)
            
            # Log this evolution round
            if feedback.feedback_info['status'] == 'success':
                metrics = feedback.feedback_info.get('metrics', {})
                current_sharpe = feedback.feedback_info.get('sharpe_ratio', -float('inf'))
                
                self.logger.log_evolution_round(
                    round_num=i,
                    strategy_info=evolved_subjects,
                    metrics=metrics,
                    status="success"
                )
                
                if current_sharpe > self.best_sharpe_ratio:
                    self.best_sharpe_ratio = current_sharpe
                    self.best_strategy = evolved_subjects
                    print(f"New best strategy found with Sharpe Ratio: {self.best_sharpe_ratio}")
                
                if feedback.is_acceptable:
                    print("Evolution successful and acceptable.")
                    self.evolvable_subjects = evolved_subjects
                    break # Stop if an acceptable strategy is found
                else:
                    print("Evolution not acceptable. Continuing evolution.")
                    current_subjects = evolved_subjects # Continue evolving from the current subjects
            else:
                print("Backtest failed. Continuing evolution with previous subjects.")
                self.logger.log_evolution_round(
                    round_num=i,
                    strategy_info=evolved_subjects,
                    metrics={},
                    status="failed"
                )
                current_subjects = evolved_subjects

        print("\nMultistep evolution completed.")
        
        # Log final summary
        self.logger.log_final_summary(self.best_strategy, max_round)
        
        if self.best_strategy:
            print(f"Overall Best Strategy Found:\nName: {self.best_strategy.name}\nType: {self.best_strategy.strategy_type}\nParams: {self.best_strategy.params}\nSharpe Ratio: {self.best_sharpe_ratio}")
        else:
            print("No successful strategy found during evolution.")


class OptimalDayTradingStrategyScenario(GeneralModelScenario):
    @property
    def background(self) -> str:
        return "Discovering an optimal day trading strategy for QQQ data by evolving strategy types and parameters."

    @property
    def rich_style_description(self) -> str:
        return "# Optimal Day Trading Strategy Discovery\n\nThis scenario aims to discover an optimal day trading strategy for the QQQ dataset.\nIt employs an evolutionary approach to explore different strategy types (e.g., Moving Average, RSI)\nand their parameters, optimizing for the Sortino Ratio.\n"

    def get_scenario_all_desc(self, task=None, filtered_tag=None, simple_background=None) -> str:
        return self.background

    def get_runtime_environment(self) -> str:
        return "This scenario runs in a Python environment with pandas, numpy, and the rdagent core libraries, interacting with the quant-strategy-lab for backtesting."

    def _init_scenario(self):
        # Initial dummy subject to kick off the evolution
        self.evolvable_subjects = OptimalTradingStrategy(name="Initial", code="", strategy_type="None", params={})
        self.evolving_strategy = OptimalStrategyEvolver(scen=self)
        self.evaluator = OptimalDayTradingEvaluator()
        self.developer = CustomDeveloper(
            scen=self,
            evolving_strategy=self.evolving_strategy,
            evaluator=self.evaluator,
            evolvable_subjects=self.evolvable_subjects
        )

    def _run(self):
        self.developer.multistep_evolve(max_round=10) # Run for more rounds to allow for discovery

if __name__ == '__main__':
    scenario = OptimalDayTradingStrategyScenario()
    scenario._init_scenario()
    scenario._run()
