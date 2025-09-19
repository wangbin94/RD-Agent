"""State models for RD-Agent UI."""

from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from rdagent.core.proposal import Hypothesis
from rdagent.core.scenario import Scenario
from rdagent.log.base import Message
from rdagent.log.storage import FileStorage


class UIState(BaseModel):
    """Central state model for RD-Agent UI."""

    # File system and logging
    log_path: Optional[Path] = None
    fs: Optional[FileStorage] = None
    scenario: Optional[Scenario] = None

    # Message handling
    msgs: Dict[int, Dict[str, List[Message]]] = Field(default_factory=lambda: defaultdict(lambda: defaultdict(list)))
    last_msg: Optional[Message] = None
    current_tags: List[str] = Field(default_factory=list)

    # Filtering and display settings
    excluded_tags: List[str] = Field(default_factory=lambda: ["debug_tpl", "debug_llm"])
    excluded_types: List[str] = Field(default_factory=list)

    # Round and loop tracking
    lround: int = 0  # RD Loop Round
    erounds: Dict[int, int] = Field(default_factory=lambda: defaultdict(int))  # Evolving Rounds in each RD Loop

    # Decisions and hypotheses
    e_decisions: Dict[int, Dict[int, tuple]] = Field(default_factory=lambda: defaultdict(lambda: defaultdict(tuple)))
    hypotheses: Dict[int, Union[Hypothesis, List[Hypothesis], None]] = Field(default_factory=lambda: defaultdict(lambda: None))
    h_decisions: Dict[int, Union[bool, List[bool]]] = Field(default_factory=lambda: defaultdict(bool))

    # Metrics and performance data
    metric_series: List[Any] = Field(default_factory=list)
    all_metric_series: List[Any] = Field(default_factory=list)
    alpha_baseline_metrics: Optional[Any] = None

    class Config:
        arbitrary_types_allowed = True


class SessionManager:
    """Manages UI session state with persistence and validation."""

    def __init__(self):
        self._state: Optional[UIState] = None

    def get_state(self) -> UIState:
        """Get current state, creating if necessary."""
        if self._state is None:
            self._state = UIState()
        return self._state

    def reset_state(self):
        """Reset state to initial values."""
        self._state = UIState()

    def update_log_path(self, log_path: Optional[Path]):
        """Update log path and reset related state."""
        state = self.get_state()
        state.log_path = log_path
        state.fs = None
        if log_path:
            state.scenario = None

    def update_scenario(self, scenario: Optional[Scenario]):
        """Update scenario and reset related state."""
        state = self.get_state()
        state.scenario = scenario
        if scenario:
            # Reset round-related state when scenario changes
            state.lround = 0
            state.erounds.clear()
            state.e_decisions.clear()
            state.hypotheses.clear()
            state.h_decisions.clear()
            state.msgs.clear()

    def update_file_storage(self, fs: Optional[FileStorage]):
        """Update file storage."""
        state = self.get_state()
        state.fs = fs

    def add_message(self, round_num: int, msg_type: str, message: Message):
        """Add a message to the specified round and type."""
        state = self.get_state()
        state.msgs[round_num][msg_type].append(message)
        state.last_msg = message

    def get_messages(self, round_num: int, msg_type: str) -> List[Message]:
        """Get messages for a specific round and type."""
        state = self.get_state()
        return state.msgs[round_num][msg_type]

    def set_hypotheses(self, round_num: int, hypotheses: Union[Hypothesis, List[Hypothesis], None]):
        """Set hypotheses for a specific round."""
        state = self.get_state()
        state.hypotheses[round_num] = hypotheses

    def get_hypotheses(self, round_num: int) -> Union[Hypothesis, List[Hypothesis], None]:
        """Get hypotheses for a specific round."""
        state = self.get_state()
        return state.hypotheses[round_num]

    def set_hypothesis_decisions(self, round_num: int, decisions: Union[bool, List[bool]]):
        """Set hypothesis decisions for a specific round."""
        state = self.get_state()
        state.h_decisions[round_num] = decisions

    def get_hypothesis_decisions(self, round_num: int) -> Union[bool, List[bool]]:
        """Get hypothesis decisions for a specific round."""
        state = self.get_state()
        return state.h_decisions[round_num]

    def set_evolving_rounds(self, round_num: int, e_round: int):
        """Set evolving rounds for a specific round."""
        state = self.get_state()
        state.erounds[round_num] = e_round

    def get_evolving_rounds(self, round_num: int) -> int:
        """Get evolving rounds for a specific round."""
        state = self.get_state()
        return state.erounds[round_num]

    def set_evolving_decisions(self, round_num: int, e_round: int, decision: tuple):
        """Set evolving decisions for a specific round and evolving round."""
        state = self.get_state()
        state.e_decisions[round_num][e_round] = decision

    def get_evolving_decisions(self, round_num: int) -> Dict[int, tuple]:
        """Get all evolving decisions for a specific round."""
        state = self.get_state()
        return state.e_decisions[round_num]

    def update_metrics(self, metric_series: List[Any], all_metric_series: List[Any]):
        """Update metrics data."""
        state = self.get_state()
        state.metric_series = metric_series
        state.all_metric_series = all_metric_series

    def set_alpha_baseline_metrics(self, metrics: Any):
        """Set alpha baseline metrics."""
        state = self.get_state()
        state.alpha_baseline_metrics = metrics

    def get_current_round(self) -> int:
        """Get current round number."""
        return self.get_state().lround

    def set_current_round(self, round_num: int):
        """Set current round number."""
        state = self.get_state()
        state.lround = round_num

    def get_available_rounds(self) -> List[int]:
        """Get list of available rounds."""
        state = self.get_state()
        rounds = list(state.msgs.keys())
        if 0 in rounds:
            rounds.remove(0)
        return sorted(rounds)

    def is_message_excluded(self, message: Message) -> bool:
        """Check if a message should be excluded from display."""
        state = self.get_state()

        # Check excluded tags
        for tag in state.excluded_tags:
            if hasattr(message, 'tags') and tag in message.tags:
                return True

        # Check excluded types
        if type(message.content).__name__ in state.excluded_types:
            return True

        return False


# Global session manager instance
session_manager = SessionManager()