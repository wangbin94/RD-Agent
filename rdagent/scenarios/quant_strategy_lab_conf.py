from pydantic_settings import SettingsConfigDict
from rdagent.components.workflow.conf import BasePropSetting

class CustomStrategyPropSetting(BasePropSetting):
    model_config = SettingsConfigDict(env_prefix="CUSTOM_STRATEGY_", protected_namespaces=())

    # Override base settings for custom strategy research
    scen: str = "rdagent.scenarios.quant_strategy_lab_scenario.CustomStrategyScenario"
    """Scenario class for Custom Strategy Research"""

    hypothesis_gen: str = "rdagent.scenarios.quant_strategy_proposal.CustomStrategyHypothesisGen"
    """Hypothesis generation class"""

    hypothesis2experiment: str = "rdagent.scenarios.quant_strategy_proposal.CustomStrategyHypothesis2Experiment"
    """Hypothesis to experiment class"""

    coder: str = "rdagent.scenarios.quant_strategy_lab_coder.CustomStrategyCoder"
    """Coder class"""

    runner: str = "rdagent.scenarios.quant_strategy_lab_runner.CustomStrategyRunner"
    """Runner class"""

    summarizer: str = "rdagent.scenarios.quant_strategy_feedback.CustomStrategyExperiment2Feedback"
    """Summarizer class"""

    evolving_n: int = 10
    """Number of evolutions"""

    # Custom strategy specific settings
    data_path: str = "data"
    """Path to the directory containing CSV data files"""
    
    framework: str = "vectorbt"
    """Backtesting framework to use (vectorbt, backtrader, qlib)"""

# Create an instance of the configuration
CUSTOM_STRATEGY_PROP_SETTING = CustomStrategyPropSetting()