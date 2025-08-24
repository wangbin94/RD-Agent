from rdagent.core.experiment import Experiment
from rdagent.scenarios.quant_strategy_proposal import CustomStrategyHypothesis
from rdagent.scenarios.quant_strategy_lab_task import StrategyTask
from rdagent.scenarios.quant_strategy_lab_experiment import StrategyExperiment
from rdagent.core.proposal import Hypothesis
from typing import List

class CustomStrategyHypothesis2Experiment:
    def __init__(self):
        pass
        
    def convert(self, hypothesis: Hypothesis, trace) -> StrategyExperiment:
        """
        Convert a hypothesis to a strategy experiment.
        
        Parameters:
        - hypothesis: CustomStrategyHypothesis object
        - trace: Trace object
        
        Returns:
        - StrategyExperiment object
        """
        # Convert hypothesis to a task
        # For now, we're assuming the hypothesis is a CustomStrategyHypothesis
        # In a more complex implementation, we might handle multiple hypotheses
        
        # Create a task from the hypothesis
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
        
        # Create experiment with tasks
        experiment = StrategyExperiment(tasks=[task])
        experiment.hypothesis = hypothesis
        return experiment