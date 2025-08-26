from rdagent.components.coder.CoSTEER.evolving_strategy import MultiProcessEvolvingStrategy
from rdagent.components.coder.CoSTEER.evaluators import CoSTEERSingleFeedback
from rdagent.components.coder.CoSTEER.knowledge_management import CoSTEERQueriedKnowledge
from rdagent.core.experiment import FBWorkspace
from rdagent.scenarios.quant_strategy_lab_task import StrategyTask
from rdagent.scenarios.quant_strategy_lab_experiment import StrategyWorkspace
from rdagent.scenarios.quant_strategy_lab_experiment import TaskWorkspace
from rdagent.oai.llm_utils import APIBackend
from rdagent.log import rdagent_logger as logger


class StrategyEvolvingStrategy(MultiProcessEvolvingStrategy):
    """
    Evolving strategy for improving trading strategies based on backtest feedback.
    """
    
    def __init__(self, scen):
        # Get settings from scenario or use default None
        settings = getattr(scen, 'settings', None)
        super().__init__(scen, settings)
    
    def implement_one_task(
        self,
        target_task: StrategyTask,
        queried_knowledge: CoSTEERQueriedKnowledge | None = None,
        workspace: FBWorkspace | None = None,
        prev_task_feedback: CoSTEERSingleFeedback | None = None,
    ) -> str:
        """
        Implement one strategy task by evolving the strategy code based on feedback.
        
        Parameters:
        - target_task: The strategy task specification
        - queried_knowledge: Optional knowledge context
        - workspace: Current strategy code implementation  
        - prev_task_feedback: Performance feedback from previous evaluation
        
        Returns:
        - Improved strategy code as string
        """
        try:
            logger.info(f"Implementing strategy: {target_task.name}")
            
            # Get current strategy code from workspace
            current_code = ""
            if workspace and workspace.file_dict:
                for filename, content in workspace.file_dict.items():
                    if filename.endswith('.py'):
                        current_code = content
                        break
            
            # Convert CoSTEER feedback to strategy feedback format
            strategy_feedback = self._convert_feedback(prev_task_feedback)
            
            # Generate improved strategy code using LLM
            improved_code = self._generate_improved_strategy(
                target_task, current_code, strategy_feedback, queried_knowledge
            )
            
            logger.info(f"Strategy implementation complete for: {target_task.name}")
            return improved_code
            
        except Exception as e:
            logger.error(f"Strategy implementation failed: {e}")
            # Return original implementation if evolution fails
            return current_code
    
    def assign_code_list_to_evo(self, code_list, evo):
        """
        Assign evolved code list to the evolving item.
        
        Parameters:
        - code_list: List of evolved code strings
        - evo: Evolving item to assign code to
        
        Returns:
        - Updated evolving item
        """
        for index in range(len(evo.sub_tasks)):
            if code_list[index] is None:
                continue
            if evo.sub_workspace_list[index] is None:
                evo.sub_workspace_list[index] = TaskWorkspace(evo.sub_tasks[index], evo.experiment_workspace.workspace_path)
            # Use the sanitized name for the file
            filename = f"{evo.sub_tasks[index].sanitized_name}.py"
            evo.sub_workspace_list[index].inject_files(**{filename: code_list[index]})
        return evo
    
    def _convert_feedback(self, feedback: CoSTEERSingleFeedback) -> dict:
        """
        Convert CoSTEER feedback to strategy feedback format.
        
        Parameters:
        - feedback: CoSTEER feedback from evaluation
        
        Returns:
        - Dictionary with strategy feedback information
        """
        if feedback is None:
            return {
                'total_return': None,
                'sharpe_ratio': None,
                'max_drawdown': None,
                'win_rate': None,
                'code_executable': True,
                'code_has_errors': False,
                'improvement_suggestion': "No feedback available. Focus on implementing a robust strategy."
            }
        
        # Parse feedback information from CoSTEER feedback
        # This is a simplified conversion - in practice, you might want to extract
        # more detailed information from the feedback strings
        return {
            'total_return': None,  # Would need to parse from feedback.execution or feedback.return_checking
            'sharpe_ratio': None,
            'max_drawdown': None,
            'win_rate': None,
            'code_executable': feedback.execution is not None and "error" not in feedback.execution.lower(),
            'code_has_errors': feedback.execution is not None and "error" in feedback.execution.lower(),
            'improvement_suggestion': feedback.code or "Improve strategy logic and performance."
        }
    
    def _generate_improved_strategy(
        self, 
        task: StrategyTask, 
        current_code: str,
        feedback: dict,
        knowledge: CoSTEERQueriedKnowledge | None
    ) -> str:
        """
        Generate improved strategy code using LLM based on feedback.
        """
        # Build knowledge context
        knowledge_context = ""
        if knowledge:
            # Try to extract useful knowledge from the queried knowledge
            if hasattr(knowledge, 'task_to_similar_task_successful_knowledge'):
                similar_knowledge = knowledge.task_to_similar_task_successful_knowledge.get(
                    task.get_task_information(), []
                )
                if similar_knowledge:
                    knowledge_context = f"\nRelevant Knowledge:\n{similar_knowledge[0] if similar_knowledge else ''}\n"
        
        # Create system prompt for strategy improvement
        system_prompt = """
        You are an expert quantitative trading strategy developer specializing in strategy optimization.
        Your task is to improve an existing trading strategy based on feedback.
        
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
        - Total Return: {feedback['total_return']}
        - Sharpe Ratio: {feedback['sharpe_ratio']}  
        - Max Drawdown: {feedback['max_drawdown']}
        - Win Rate: {feedback['win_rate']}
        - Code Executable: {feedback['code_executable']}
        - Has Errors: {feedback['code_has_errors']}
        
        Improvement Suggestions:
        {feedback['improvement_suggestion']}
        
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