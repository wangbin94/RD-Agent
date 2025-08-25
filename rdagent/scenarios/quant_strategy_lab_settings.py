from rdagent.components.coder.CoSTEER.config import CoSTEERSettings


class StrategyCoSTEERSettings(CoSTEERSettings):
    """
    CoSTEER settings specifically for trading strategy evolution.
    """
    
    class Config:
        env_prefix = "Strategy_CoSTEER_"
        
    # Strategy-specific evolution settings
    max_loop: int = 3  # Number of evolution iterations per loop
    knowledge_base_path: str | None = "knowledge_base/strategy"
    new_knowledge_base_path: str | None = "knowledge_base/strategy_new" 
    
    # Strategy evaluation settings
    enable_parallel_eval: bool = True
    evaluation_timeout_seconds: int = 300  # 5 minutes per strategy evaluation
    
    # Strategy-specific evolution parameters
    enable_risk_management_evolution: bool = True
    enable_parameter_tuning: bool = True
    enable_signal_improvement: bool = True