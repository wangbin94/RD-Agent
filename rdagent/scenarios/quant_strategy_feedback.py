from rdagent.core.experiment import Experiment
from rdagent.core.feedback import Feedback
from typing import Dict, Any, Optional

class CustomStrategyExperiment2Feedback:
    def __init__(self):
        pass
        
    def generate_feedback(self, exp: Experiment) -> Feedback:
        """
        Generate feedback from a strategy experiment.
        
        Parameters:
        - exp: StrategyExperiment object
        
        Returns:
        - Feedback object
        """
        # Extract results from experiment
        results = exp.result if exp.result else {}
        
        # Create feedback based on results
        if "error" in results:
            feedback = Feedback(
                content=f"Error occurred during experiment execution: {results['error']}",
                priority=1
            )
        elif "metrics" in results:
            # If we have metrics, provide more detailed feedback
            metrics = results["metrics"]
            feedback_content = "Experiment completed with the following results:\n"
            for key, value in metrics.items():
                feedback_content += f"- {key}: {value}\n"
                
            # Determine priority based on performance
            priority = 3  # Default priority
            if "sharpe_ratio" in metrics and metrics["sharpe_ratio"] > 1.0:
                priority = 5  # High priority for good strategies
            elif "sharpe_ratio" in metrics and metrics["sharpe_ratio"] < 0.5:
                priority = 1  # Low priority for poor strategies
                
            feedback = Feedback(
                content=feedback_content,
                priority=priority
            )
        else:
            # Generic feedback if no specific results
            feedback = Feedback(
                content=f"Experiment completed. Results: {results}",
                priority=3
            )
            
        return feedback