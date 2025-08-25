from rdagent.components.coder.CoSTEER.evolvable_subjects import EvolvingItem
from rdagent.core.evolving_framework import EvolvingStrategy, QueriedKnowledge
from rdagent.core.experiment import FBWorkspace
from rdagent.scenarios.quant_strategy_lab_task import StrategyTask
from rdagent.scenarios.quant_strategy_lab_evaluator import StrategyFeedback
from rdagent.utils.agent.tpl import T
from rdagent.oai.llm_utils import APIBackend
from rdagent.log import rdagent_logger as logger


class StrategyEvolvingStrategy(EvolvingStrategy):
    """
    Evolving strategy for improving trading strategies based on backtest feedback.
    """
    
    def __init__(self, scen):
        super().__init__(scen)
    
    def evolve(
        self,
        target_task: StrategyTask,
        implementation: FBWorkspace,
        feedback: StrategyFeedback,
        queried_knowledge: QueriedKnowledge | None = None,
    ) -> FBWorkspace:
        """
        Evolve a strategy implementation based on performance feedback.
        
        Parameters:
        - target_task: The strategy task specification
        - implementation: Current strategy code implementation  
        - feedback: Performance feedback from backtesting
        - queried_knowledge: Optional knowledge context
        
        Returns:
        - Improved strategy implementation
        """
        try:
            logger.info(f"Evolving strategy: {target_task.name}")
            logger.info(f"Current performance: {feedback}")
            
            # Generate improved strategy code using LLM
            improved_code = self._generate_improved_strategy(
                target_task, implementation, feedback, queried_knowledge
            )
            
            # Create new workspace with improved code
            new_workspace = FBWorkspace()
            new_workspace.workspace_path = implementation.workspace_path
            
            # Copy existing files and update strategy code
            for file_name, content in implementation.file_dict.items():
                if file_name.endswith('.py') and 'strategy' in file_name.lower():
                    # This is the main strategy file - replace with improved version
                    new_workspace.file_dict[file_name] = improved_code
                else:
                    # Keep other files unchanged
                    new_workspace.file_dict[file_name] = content
            
            logger.info(f"Strategy evolution complete for: {target_task.name}")
            return new_workspace
            
        except Exception as e:
            logger.error(f"Strategy evolution failed: {e}")
            # Return original implementation if evolution fails
            return implementation
    
    def _generate_improved_strategy(
        self, 
        task: StrategyTask, 
        current_impl: FBWorkspace, 
        feedback: StrategyFeedback,
        knowledge: QueriedKnowledge | None
    ) -> str:
        """
        Generate improved strategy code using LLM based on feedback.
        """
        # Get current strategy code
        current_code = ""
        strategy_filename = ""
        for filename, content in current_impl.file_dict.items():
            if filename.endswith('.py'):
                current_code = content
                strategy_filename = filename
                break
        
        # Build knowledge context
        knowledge_context = ""
        if knowledge and hasattr(knowledge, 'content'):
            knowledge_context = f"\nRelevant Knowledge:\n{knowledge.content}\n"
        
        # Create system prompt for strategy improvement
        system_prompt = """
        You are an expert quantitative trading strategy developer specializing in strategy optimization.
        Your task is to improve an existing trading strategy based on backtest performance feedback.
        
        Guidelines for improvement:
        1. Maintain the original strategy concept but enhance the implementation
        2. Address specific performance issues identified in the feedback
        3. Consider risk management, signal quality, and parameter optimization
        4. Preserve the required BaseStrategy interface (get_default_params, generate_signals)
        5. Ensure the code is syntactically correct and executable
        6. Use lowercase column names: 'open', 'high', 'low', 'close', 'volume'
        """
        
        # Create user prompt with current code and feedback
        user_prompt = f"""
        Original Strategy Task:
        Name: {task.name}
        Description: {task.description}
        Parameters: {task.parameters}
        
        Current Strategy Code:
        ```python
        {current_code}
        ```
        
        Performance Feedback:
        - Total Return: {feedback.total_return}
        - Sharpe Ratio: {feedback.sharpe_ratio}  
        - Max Drawdown: {feedback.max_drawdown}
        - Win Rate: {feedback.win_rate}
        - Code Executable: {feedback.code_executable}
        - Has Errors: {feedback.code_has_errors}
        
        Improvement Suggestions:
        {feedback.improvement_suggestion or "Focus on improving risk-adjusted returns."}
        
        {knowledge_context}
        
        Please provide an improved version of the strategy that addresses the performance issues.
        Focus on:
        1. Improving signal quality and timing
        2. Better risk management and position sizing  
        3. Parameter optimization
        4. Reducing drawdowns while maintaining returns
        
        Return only the complete improved Python code, maintaining the same class structure and interface.
        """
        
        try:
            # Generate improved code using LLM
            response = APIBackend().build_messages_and_create_chat_completion(
                user_prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            # Extract code from response
            if "```python" in response:
                improved_code = response.split("```python")[1].split("```")[0].strip()
            elif "```" in response:
                improved_code = response.split("```")[1].split("```")[0].strip()  
            else:
                improved_code = response.strip()
            
            # Fallback if extraction failed
            if not improved_code or len(improved_code) < 100:
                if response.strip().startswith(('import ', 'from ', 'class ', '@')):
                    improved_code = response.strip()
                else:
                    logger.warning("Failed to extract improved code, returning original")
                    return current_code
            
            return improved_code
            
        except Exception as e:
            logger.error(f"Failed to generate improved strategy: {e}")
            return current_code