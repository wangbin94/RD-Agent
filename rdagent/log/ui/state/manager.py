"""Centralized state management for RD-Agent UI."""

import streamlit as st
from streamlit import session_state as st_state

from .models import SessionManager, UIState


class StreamlitStateManager:
    """Bridge between Streamlit session state and our state management."""

    def __init__(self):
        self._key = "_rdagent_session_manager"

    def get_session_manager(self) -> SessionManager:
        """Get or create session manager in Streamlit session state."""
        if self._key not in st_state:
            st_state[self._key] = SessionManager()
        return st_state[self._key]

    def reset_session(self):
        """Reset the entire session state."""
        if self._key in st_state:
            del st_state[self._key]

    def get_state(self) -> UIState:
        """Get current UI state."""
        return self.get_session_manager().get_state()

    # Convenience methods that delegate to SessionManager
    def update_log_path(self, log_path):
        """Update log path."""
        return self.get_session_manager().update_log_path(log_path)

    def update_scenario(self, scenario):
        """Update scenario."""
        return self.get_session_manager().update_scenario(scenario)

    def update_file_storage(self, fs):
        """Update file storage."""
        return self.get_session_manager().update_file_storage(fs)

    def add_message(self, round_num, msg_type, message):
        """Add a message."""
        return self.get_session_manager().add_message(round_num, msg_type, message)

    def get_messages(self, round_num, msg_type):
        """Get messages."""
        return self.get_session_manager().get_messages(round_num, msg_type)

    def set_hypotheses(self, round_num, hypotheses):
        """Set hypotheses."""
        return self.get_session_manager().set_hypotheses(round_num, hypotheses)

    def get_hypotheses(self, round_num):
        """Get hypotheses."""
        return self.get_session_manager().get_hypotheses(round_num)

    def set_hypothesis_decisions(self, round_num, decisions):
        """Set hypothesis decisions."""
        return self.get_session_manager().set_hypothesis_decisions(round_num, decisions)

    def get_hypothesis_decisions(self, round_num):
        """Get hypothesis decisions."""
        return self.get_session_manager().get_hypothesis_decisions(round_num)

    def set_current_round(self, round_num):
        """Set current round."""
        return self.get_session_manager().set_current_round(round_num)

    def get_current_round(self):
        """Get current round."""
        return self.get_session_manager().get_current_round()

    def get_available_rounds(self):
        """Get available rounds."""
        return self.get_session_manager().get_available_rounds()

    def is_message_excluded(self, message):
        """Check if message is excluded."""
        return self.get_session_manager().is_message_excluded(message)


# Global state manager instance
state_manager = StreamlitStateManager()


def init_session_state():
    """Initialize session state with default values."""
    manager = state_manager.get_session_manager()

    # Initialize excluded tags if not already set
    state = manager.get_state()
    if not state.excluded_tags:
        state.excluded_tags = ["debug_tpl", "debug_llm"]

    return manager


def get_state() -> UIState:
    """Get current UI state."""
    return state_manager.get_state()


def get_session_manager() -> SessionManager:
    """Get session manager."""
    return state_manager.get_session_manager()


# Backward compatibility with original session state pattern
class StateProxy:
    """Proxy to maintain backward compatibility with direct state access."""

    def __init__(self, state_manager: StreamlitStateManager):
        self._manager = state_manager

    @property
    def log_path(self):
        return self._manager.get_state().log_path

    @log_path.setter
    def log_path(self, value):
        self._manager.update_log_path(value)

    @property
    def scenario(self):
        return self._manager.get_state().scenario

    @scenario.setter
    def scenario(self, value):
        self._manager.update_scenario(value)

    @property
    def fs(self):
        return self._manager.get_state().fs

    @fs.setter
    def fs(self, value):
        self._manager.update_file_storage(value)

    @property
    def msgs(self):
        return self._manager.get_state().msgs

    @property
    def last_msg(self):
        return self._manager.get_state().last_msg

    @property
    def current_tags(self):
        return self._manager.get_state().current_tags

    @property
    def lround(self):
        return self._manager.get_current_round()

    @lround.setter
    def lround(self, value):
        self._manager.set_current_round(value)

    @property
    def erounds(self):
        return self._manager.get_state().erounds

    @property
    def e_decisions(self):
        return self._manager.get_state().e_decisions

    @property
    def hypotheses(self):
        return self._manager.get_state().hypotheses

    @property
    def h_decisions(self):
        return self._manager.get_state().h_decisions

    @property
    def metric_series(self):
        return self._manager.get_state().metric_series

    @property
    def all_metric_series(self):
        return self._manager.get_state().all_metric_series

    @property
    def alpha_baseline_metrics(self):
        return self._manager.get_state().alpha_baseline_metrics

    @property
    def excluded_tags(self):
        return self._manager.get_state().excluded_tags

    @property
    def excluded_types(self):
        return self._manager.get_state().excluded_types


# Create backward-compatible state proxy
state = StateProxy(state_manager)