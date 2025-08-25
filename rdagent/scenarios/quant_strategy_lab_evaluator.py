import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from rdagent.components.coder.CoSTEER.evaluators import (
    CoSTEEREvaluator,
    CoSTEERSingleFeedback,
)
from rdagent.core.experiment import FBWorkspace
from rdagent.log import rdagent_logger as logger
from rdagent.scenarios.quant_strategy_lab_runner import CustomStrategyRunner
from rdagent.utils.agent.tpl import T


@dataclass
class StrategyFeedback(CoSTEERSingleFeedback):
    """
    Feedback for Strategy CoSTEER evaluation.
    This feedback is used to evaluate strategy backtest performance and code quality.
    """
    
    # Strategy performance metrics
    total_return: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown: float | None = None
    win_rate: float | None = None
    
    # Code quality assessment
    code_executable: bool | None = None
    code_has_errors: bool | None = None
    
    # Overall evaluation
    acceptable: bool | None = None
    performance_score: float | None = None
    
    # Improvement suggestions
    improvement_suggestion: str | None = None
    
    def is_acceptable(self) -> bool:
        """
        Determine if the strategy is acceptable based on multiple criteria:
        1. Code must be executable without errors
        2. Performance metrics must meet minimum thresholds
        """
        if self.acceptable is not None:
            return self.acceptable
            
        # Code must be executable
        if self.code_executable is False or self.code_has_errors is True:
            return False
            
        # Basic performance check - at least positive returns or reasonable Sharpe
        if self.total_return is not None and self.sharpe_ratio is not None:
            return self.total_return > 0 or self.sharpe_ratio > 0.5
            
        # Fallback to parent class logic
        return super().is_acceptable()
    
    def __str__(self) -> str:
        parts = []
        
        if self.total_return is not None:
            parts.append(f"Total Return: {self.total_return:.2%}")
        if self.sharpe_ratio is not None:
            parts.append(f"Sharpe Ratio: {self.sharpe_ratio:.2f}")
        if self.max_drawdown is not None:
            parts.append(f"Max Drawdown: {self.max_drawdown:.2%}")
        if self.win_rate is not None:
            parts.append(f"Win Rate: {self.win_rate:.2%}")
            
        if self.code_executable is not None:
            parts.append(f"Executable: {'Yes' if self.code_executable else 'No'}")
        if self.code_has_errors:
            parts.append("Has Errors: Yes")
            
        if self.improvement_suggestion:
            parts.append(f"Suggestion: {self.improvement_suggestion}")
            
        return " | ".join(parts) if parts else "No feedback available"


class StrategyEvaluator(CoSTEEREvaluator):
    """
    Evaluator for trading strategy performance using backtest results.
    """
    
    def __init__(self, scen, runner: CustomStrategyRunner):
        super().__init__(scen)
        self.runner = runner
    
    def evaluate(self, target_task, implementation: FBWorkspace, gt_implementation: FBWorkspace = None, queried_knowledge=None, **kwargs) -> StrategyFeedback:
        """
        Evaluate a strategy implementation by running backtest and analyzing results.
        
        Parameters:
        - target_task: StrategyTask containing strategy specification
        - implementation: FBWorkspace containing strategy code
        - gt_implementation: Ground truth implementation (optional)
        - queried_knowledge: Optional knowledge context
        
        Returns:
        - StrategyFeedback with performance metrics and evaluation
        """
        try:
            # Create a temporary experiment to run the strategy
            from rdagent.scenarios.quant_strategy_lab_experiment import StrategyExperiment, StrategyWorkspace
            
            # Create workspace and experiment for evaluation
            temp_workspace = StrategyWorkspace()
            temp_experiment = StrategyExperiment(
                tasks=[target_task],
                experiment_workspace=temp_workspace
            )
            
            # Copy implementation code to workspace
            for file_name, content in implementation.file_dict.items():
                temp_workspace.save_code_file(file_name, content)
            
            # Run the strategy backtest
            logger.info(f"Evaluating strategy: {target_task.name}")
            result_exp = self.runner.run(temp_experiment)
            
            # Parse results and create feedback
            feedback = self._parse_results_to_feedback(target_task, result_exp, implementation)
            
            # Generate improvement suggestions using LLM
            if not feedback.is_acceptable():
                feedback.improvement_suggestion = self._generate_improvement_suggestion(
                    target_task, implementation, feedback
                )
            
            logger.info(f"Strategy evaluation complete: {feedback}")
            return feedback
            
        except Exception as e:
            logger.error(f"Strategy evaluation failed: {e}")
            return StrategyFeedback(
                execution=f"Execution failed with error: {str(e)}",
                return_checking=None,
                code=f"Code evaluation failed with error: {str(e)}",
                code_executable=False,
                code_has_errors=True,
                acceptable=False,
                improvement_suggestion=f"Execution failed with error: {str(e)}"
            )
    
    def _parse_results_to_feedback(self, task, result_exp, implementation) -> StrategyFeedback:
        """
        Parse backtest results into structured feedback.
        """
        try:
            # Try to extract performance metrics from results
            metrics = {}
            
            # Check if results exist
            if hasattr(result_exp, 'experiment_workspace') and result_exp.experiment_workspace:
                results_path = result_exp.experiment_workspace.workspace_path / "results"
                if results_path.exists():
                    # Look for performance metrics files
                    for results_file in results_path.glob("*.json"):
                        try:
                            with open(results_file, 'r') as f:
                                data = json.load(f)
                                if isinstance(data, dict):
                                    metrics.update(data)
                        except Exception:
                            continue
            
            # Extract key performance metrics
            total_return = metrics.get('total_return', metrics.get('return', None))
            sharpe_ratio = metrics.get('sharpe_ratio', metrics.get('sharpe', None))
            max_drawdown = metrics.get('max_drawdown', metrics.get('drawdown', None))
            win_rate = metrics.get('win_rate', None)
            
            # Determine code quality
            code_executable = True  # If we got here, code ran
            code_has_errors = False
            
            # Check for any error indicators in results
            if 'error' in metrics or 'exception' in str(metrics).lower():
                code_has_errors = True
                code_executable = False
            
            return StrategyFeedback(
                execution="Strategy executed successfully",
                return_checking=f"Performance metrics - Total Return: {total_return}, Sharpe Ratio: {sharpe_ratio}",
                code="Code executed without errors",
                total_return=total_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                code_executable=code_executable,
                code_has_errors=code_has_errors,
                performance_score=sharpe_ratio if sharpe_ratio is not None else total_return
            )
            
        except Exception as e:
            logger.error(f"Failed to parse results: {e}")
            return StrategyFeedback(
                execution=f"Failed to parse results: {str(e)}",
                return_checking=None,
                code=f"Code evaluation failed with error: {str(e)}",
                code_executable=False,
                code_has_errors=True,
                acceptable=False
            )
    
    def _generate_improvement_suggestion(self, task, implementation, feedback) -> str:
        """
        Generate LLM-based improvement suggestions for underperforming strategies.
        """
        try:
            # Create prompt for improvement suggestions
            system_prompt = """
            You are an expert quantitative trading strategy analyst. 
            Analyze the strategy code and performance results, then provide specific suggestions for improvement.
            Focus on concrete, actionable improvements to the strategy logic, parameters, or risk management.
            """
            
            code_content = ""
            for file_name, content in implementation.file_dict.items():
                code_content += f"\n### {file_name}\n```python\n{content}\n```\n"
            
            user_prompt = f"""
            Strategy: {task.name}
            Description: {task.description}
            
            Current Code:
            {code_content}
            
            Performance Results:
            - Total Return: {feedback.total_return}
            - Sharpe Ratio: {feedback.sharpe_ratio}
            - Max Drawdown: {feedback.max_drawdown}
            - Win Rate: {feedback.win_rate}
            - Code Executable: {feedback.code_executable}
            - Has Errors: {feedback.code_has_errors}
            
            Please provide 2-3 specific, actionable suggestions to improve this strategy's performance.
            Focus on strategy logic, parameter tuning, risk management, or signal generation improvements.
            """
            
            # Use the same LLM backend as the coder
            from rdagent.oai.llm_utils import APIBackend
            response = APIBackend().build_messages_and_create_chat_completion(
                user_prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate improvement suggestion: {e}")
            return "Unable to generate specific suggestions. Consider reviewing strategy logic and parameters."