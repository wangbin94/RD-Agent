from rdagent.core.experiment import Experiment
from rdagent.scenarios.quant_strategy_proposal import CustomStrategyHypothesis
from rdagent.scenarios.quant_strategy_lab_task import StrategyTask
from rdagent.scenarios.quant_strategy_lab_experiment import StrategyExperiment
from typing import List

class CustomStrategyHypothesis2Experiment:
    def __init__(self):
        pass
        
    def convert(self, hypotheses: List[CustomStrategyHypothesis]) -> StrategyExperiment:
        """
        Convert hypotheses to a strategy experiment.
        
        Parameters:
        - hypotheses: List of CustomStrategyHypothesis objects
        
        Returns:
        - StrategyExperiment object
        """
        # Convert each hypothesis to a task
        tasks = []
        for hypothesis in hypotheses:
            # Create a task for each hypothesis
            task = StrategyTask(
                name=hypothesis.name,
                description=hypothesis.description,
                parameters={
                    "formulation": hypothesis.formulation,
                    "factors": hypothesis.factors,
                    "rationale": hypothesis.rationale
                },
                logic_formulation=hypothesis.formulation
            )
            tasks.append(task)
            
        # Create experiment with tasks
        experiment = StrategyExperiment(tasks=tasks)
        return experiment