"""Refactored RD-Agent Streamlit App with modular architecture."""

import argparse
import pickle
from pathlib import Path

import streamlit as st

from rdagent.log.ui.pages import render_dashboard
from rdagent.log.ui.services import FileStorageManager, LogFolderProcessor, ScenarioLoader
from rdagent.log.ui.state import get_session_manager, init_session_state
from rdagent.log.ui.utils import apply_ui_styles

# Configure Streamlit page
st.set_page_config(
    layout="wide",
    page_title="RD-Agent",
    page_icon="🎓",
    initial_sidebar_state="expanded"
)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="RD-Agent Streamlit App")
    parser.add_argument("--log_dir", type=str, help="Path to the log directory")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser.parse_args()


def initialize_app():
    """Initialize the application with command line arguments and setup."""
    args = parse_arguments()

    # Store command line arguments in session state
    if 'args_initialized' not in st.session_state:
        st.session_state.main_log_path = Path(args.log_dir) if args.log_dir else None
        st.session_state.debug_mode = args.debug
        st.session_state.args_initialized = True

    # Initialize session state management
    init_session_state()

    # Apply global styles
    apply_ui_styles()


def setup_log_path():
    """Setup log path and validate directory."""
    state_manager = get_session_manager()

    if st.session_state.main_log_path:
        # Check if the main log path exists
        if not st.session_state.main_log_path.exists():
            st.error(f"Log directory does not exist: {st.session_state.main_log_path}")
            return False

        # Get latest log folder if none is selected
        current_state = state_manager.get_state()
        if not current_state.log_path:
            latest_folder = LogFolderProcessor.get_latest_log_folder(st.session_state.main_log_path)
            if latest_folder:
                state_manager.update_log_path(latest_folder)
            else:
                st.warning("No log folders found in the specified directory")
                return False

        return True
    else:
        st.toast(":red[**Please Set Log Path!**]", icon="⚠️")
        return False


def load_scenario():
    """Load scenario from the current log path."""
    state_manager = get_session_manager()
    current_state = state_manager.get_state()

    if not current_state.log_path:
        return False

    # Construct full log path
    if st.session_state.main_log_path:
        full_log_path = st.session_state.main_log_path / current_state.log_path
    else:
        full_log_path = current_state.log_path

    # Validate log path
    if not FileStorageManager.validate_log_path(full_log_path):
        st.warning(f"Invalid log directory: {full_log_path}")
        return False

    # Load scenario if not already loaded
    if not current_state.scenario:
        scenario = ScenarioLoader.load_scenario_from_path(full_log_path)
        if scenario:
            state_manager.update_scenario(scenario)

            # Create message iterator (this is what the original code stored in state.fs)
            fs_iterator = FileStorageManager.create_message_iterator(full_log_path)
            if fs_iterator:
                state_manager.update_file_storage(fs_iterator)
            else:
                st.error("Failed to create message iterator")
                return False
        else:
            st.error(f"Failed to load scenario from {full_log_path}")
            return False

    return True


def handle_error_boundary():
    """Handle application errors gracefully."""
    try:
        # Initialize application
        initialize_app()

        # Setup log path
        if not setup_log_path():
            st.stop()

        # Load scenario
        if not load_scenario():
            st.stop()

        # Render main dashboard
        render_dashboard()

    except Exception as e:
        st.error(f"Application Error: {str(e)}")

        if st.session_state.get('debug_mode', False):
            st.exception(e)

        # Provide recovery options
        st.markdown("### Recovery Options")
        if st.button("Reset Application State"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        if st.button("Reload Scenario"):
            state_manager = get_session_manager()
            state_manager.get_state().scenario = None
            state_manager.get_state().fs = None
            st.rerun()


def main():
    """Main application entry point."""
    handle_error_boundary()


if __name__ == "__main__":
    main()