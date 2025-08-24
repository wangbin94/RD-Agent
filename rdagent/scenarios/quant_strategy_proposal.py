from rdagent.core.scenario import Scenario
from rdagent.core.proposal import Hypothesis
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
        # Call parent constructor with required parameters
        super().__init__(
            hypothesis=name,
            reason=description,
            concise_reason=description[:100] if len(description) > 100 else description,
            concise_observation="",
            concise_justification=rationale[:100] if len(rationale) > 100 else rationale,
            concise_knowledge=""
        )
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
        self._generated_hypotheses = []
        self._current_index = 0
        
    def gen(self, trace, num_hypotheses: int = 5):
        """
        Generate hypotheses for custom strategies.
        
        Parameters:
        - trace: Trace object
        - num_hypotheses: Number of hypotheses to generate (only used when generating new hypotheses)
        
        Returns:
        - CustomStrategyHypothesis object
        """
        # If we haven't generated hypotheses yet, or we've used all of them, generate new ones
        if not self._generated_hypotheses or self._current_index >= len(self._generated_hypotheses):
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
                # Try to parse as JSON object first
                response_data = json.loads(response)
                # If it's a dict with a "strategies" key, use that
                if isinstance(response_data, dict) and "strategies" in response_data:
                    hypotheses_data = response_data["strategies"]
                else:
                    # Otherwise assume it's the array directly
                    hypotheses_data = response_data
                    
                self._generated_hypotheses = []
                for h in hypotheses_data:
                    self._generated_hypotheses.append(CustomStrategyHypothesis(
                        name=h["name"],
                        description=h["description"],
                        formulation=h["formulation"],
                        factors=h["factors"],
                        rationale=h.get("rationale", "")
                    ))
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                # Fallback if JSON parsing fails
                print(f"Error parsing JSON response: {e}")
                self._generated_hypotheses = []
            
            self._current_index = 0
        
        # Return the next hypothesis, or the first one if we've run out
        if self._generated_hypotheses:
            hypothesis = self._generated_hypotheses[self._current_index]
            self._current_index += 1
            return hypothesis
        else:
            # Fallback hypothesis if generation failed
            return CustomStrategyHypothesis(
                name="Fallback Strategy",
                description="A simple moving average crossover strategy",
                formulation="If fast MA > slow MA, go long; else go short",
                factors=["Fast MA", "Slow MA"],
                rationale="Simple trend following strategy"
            )