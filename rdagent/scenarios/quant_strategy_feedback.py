from rdagent.core.experiment import Experiment
from rdagent.core.proposal import HypothesisFeedback
from rdagent.core.scenario import Scenario
from typing import Dict, Any, Optional

class CustomStrategyExperiment2Feedback:
    def __init__(self, scen: Scenario):
        self.scen = scen
        
    def generate_feedback(self, exp: Experiment, trace=None) -> HypothesisFeedback:
        """
        Generate feedback from a strategy experiment.
        
        Parameters:
        - exp: StrategyExperiment object
        - trace: Optional trace information
        
        Returns:
        - HypothesisFeedback object
        """
        # Extract results from experiment
        results = exp.result if exp.result else {}
        
        # Create feedback based on results
        if "error" in results:
            feedback = HypothesisFeedback(
                observations="",
                hypothesis_evaluation="",
                new_hypothesis="",
                reason=f"Error occurred during experiment execution: {results['error']}",
                decision=False,
                code_change_summary="",
                eda_improvement=""
            )
        elif "metrics" in results:
            # If we have metrics, provide more detailed feedback
            metrics = results["metrics"]
            feedback_content = "Experiment completed with the following results:\n"
            for key, value in metrics.items():
                feedback_content += f"- {key}: {value}\n"
                
            # Determine decision based on performance
            decision = False
            if "sharpe_ratio" in metrics and metrics["sharpe_ratio"] > 1.0:
                decision = True  # Good strategy
                
            feedback = HypothesisFeedback(
                observations="",
                hypothesis_evaluation="",
                new_hypothesis="",
                decision=decision,
                reason=feedback_content,
                code_change_summary="",
                eda_improvement=""
            )
        else:
            # Generic feedback if no specific results
            feedback = HypothesisFeedback(
                observations="",
                hypothesis_evaluation="",
                new_hypothesis="",
                decision=True,
                reason=f"Experiment completed. Results: {results}",
                code_change_summary="",
                eda_improvement=""
            )
            
        return feedback