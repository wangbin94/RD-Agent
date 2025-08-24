from rdagent.core.scenario import Scenario
from rdagent.core.hypothesis import Hypothesis
from rdagent.core.prompts import Prompts
from rdagent.oai.llm_utils import APIBackend
from typing import List

class CustomStrategyHypothesis(Hypothesis):
    def __init__(self, 
                 name: str, 
                 description: str, 
                 formulation: str, 
                 factors: List[str],
                 rationale: str = ""):
        self.name = name
        self.description = description
        self.formulation = formulation
        self.factors = factors
        self.rationale = rationale

    def __str__(self):
        return f"""Strategy: {self.name}
Description: {self.description}
Formulation: {self.formulation}
Factors: {', '.join(self.factors)}
Rationale: {self.rationale}"""

class CustomStrategyHypothesisGen:
    def __init__(self, scen: Scenario):
        self.scen = scen
        
    def gen(self, num_hypotheses: int = 5) -> List[CustomStrategyHypothesis]:
        """
        Generate hypotheses for custom strategies.
        
        Parameters:
        - num_hypotheses: Number of hypotheses to generate
        
        Returns:
        - List of CustomStrategyHypothesis objects
        """
        # System prompt for hypothesis generation
        system_prompt = """
        You are an expert quantitative researcher specializing in financial strategy development.
        Your task is to generate innovative trading strategy hypotheses based on the provided scenario.
        Each hypothesis should include a clear name, description, mathematical formulation, and list of factors.
        """
        
        # User prompt with scenario details
        user_prompt = f"""
        Generate {num_hypotheses} trading strategy hypotheses for the following scenario:
        
        {self.scen.get_scenario_all_desc()}
        
        For each hypothesis, provide:
        1. A concise name
        2. A detailed description of the strategy logic
        3. A mathematical formulation of the strategy
        4. A list of factors or indicators used
        
        Format your response as JSON array with each element having:
        - name: Strategy name
        - description: Strategy description
        - formulation: Mathematical formulation
        - factors: List of factors/indicators
        - rationale: Brief rationale for why this strategy might work
        """
        
        # Get hypotheses from LLM
        response = APIBackend().build_messages_and_create_chat_completion(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            json_mode=True
        )
        
        # Parse the JSON response
        import json
        try:
            hypotheses_data = json.loads(response)
            hypotheses = []
            for h in hypotheses_data:
                hypotheses.append(CustomStrategyHypothesis(
                    name=h["name"],
                    description=h["description"],
                    formulation=h["formulation"],
                    factors=h["factors"],
                    rationale=h["rationale"]
                ))
            return hypotheses
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return []