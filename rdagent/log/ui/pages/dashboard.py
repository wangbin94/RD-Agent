"""Main dashboard page for RD-Agent UI."""

import streamlit as st

from rdagent.log.ui.components.charts import display_metrics_dataframe, metrics_window
from rdagent.log.ui.components.feedback import feedback_window
from rdagent.log.ui.components.tasks import display_hypotheses, task_progress_indicator
from rdagent.log.ui.services import LogFolderProcessor, MessageStreamProcessor, ScenarioLoader
from rdagent.log.ui.state import get_session_manager, get_state, init_session_state, state
from rdagent.log.ui.utils import IconManager, apply_ui_styles
from rdagent.scenarios.general_model.scenario import GeneralModelScenario
from rdagent.scenarios.kaggle.experiment.scenario import KGScenario
from rdagent.scenarios.qlib.experiment.factor_experiment import QlibFactorScenario
from rdagent.scenarios.qlib.experiment.factor_from_report_experiment import QlibFactorFromReportScenario
from rdagent.scenarios.qlib.experiment.model_experiment import QlibModelScenario
from rdagent.scenarios.qlib.experiment.quant_experiment import QlibQuantScenario
from rdagent.scenarios.quant_strategy_lab_scenario import CustomStrategyScenario

# Similar scenarios for type checking
SIMILAR_SCENARIOS = (
    QlibModelScenario,
    QlibFactorScenario,
    QlibFactorFromReportScenario,
    QlibQuantScenario,
    KGScenario,
    CustomStrategyScenario,
)


def load_all_messages():
    """Load all messages from the file storage."""
    current_state = get_state()
    if not current_state.fs:
        refresh_current_trace()
        return

    try:
        processor = MessageStreamProcessor()
        result = processor.process_messages_until(
            current_state.fs,
            current_state.excluded_tags,
            current_state.excluded_types,
            end_func=lambda _: False  # Load everything
        )

        # Update state with processed data
        state_manager = get_session_manager()
        current_state.msgs.update(result["msgs"])
        current_state.lround = result["lround"]
        current_state.erounds.update(result["erounds"])
        current_state.hypotheses.update(result["hypotheses"])
        current_state.h_decisions.update(result["h_decisions"])

        st.success("All messages loaded successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error loading messages: {e}")


def reset_current_trace():
    """Reset the current trace."""
    refresh_current_trace(same_trace=True)


def load_next_loop():
    """Load messages until the next feedback loop."""
    current_state = get_state()
    if not current_state.fs:
        refresh_current_trace()
        return

    try:
        processor = MessageStreamProcessor()
        result = processor.process_messages_until(
            current_state.fs,
            current_state.excluded_tags,
            current_state.excluded_types,
            end_func=lambda m: "feedback" in m.tag and "evolving feedback" not in m.tag
        )

        # Update state with processed data
        current_state.msgs.update(result["msgs"])
        current_state.lround = result["lround"]
        current_state.erounds.update(result["erounds"])
        current_state.hypotheses.update(result["hypotheses"])
        current_state.h_decisions.update(result["h_decisions"])

        st.success("Next loop loaded!")
        st.rerun()
    except Exception as e:
        st.error(f"Error loading next loop: {e}")


def load_next_step():
    """Load messages until the next evolving feedback."""
    current_state = get_state()
    if not current_state.fs:
        refresh_current_trace()
        return

    try:
        processor = MessageStreamProcessor()
        result = processor.process_messages_until(
            current_state.fs,
            current_state.excluded_tags,
            current_state.excluded_types,
            end_func=lambda m: "evolving feedback" in m.tag
        )

        # Update state with processed data
        current_state.msgs.update(result["msgs"])
        current_state.lround = result["lround"]
        current_state.erounds.update(result["erounds"])
        current_state.hypotheses.update(result["hypotheses"])
        current_state.h_decisions.update(result["h_decisions"])

        st.success("Next step loaded!")
        st.rerun()
    except Exception as e:
        st.error(f"Error loading next step: {e}")


def load_single_step():
    """Load a single step for debugging."""
    current_state = get_state()
    if not current_state.fs:
        refresh_current_trace()
        return

    try:
        processor = MessageStreamProcessor()
        result = processor.process_messages_until(
            current_state.fs,
            current_state.excluded_tags,
            current_state.excluded_types,
            end_func=lambda _: True  # Load just one message
        )

        # Update state with processed data
        current_state.msgs.update(result["msgs"])
        current_state.lround = result["lround"]
        current_state.erounds.update(result["erounds"])
        current_state.hypotheses.update(result["hypotheses"])
        current_state.h_decisions.update(result["h_decisions"])

        st.success("Single step loaded!")
        st.rerun()
    except Exception as e:
        st.error(f"Error loading single step: {e}")


def refresh_current_trace(same_trace: bool = False):
    """Refresh the current trace."""
    state_manager = get_session_manager()
    current_state = get_state()

    if not same_trace:
        # Reset everything
        state_manager.reset_state()

    # Reload scenario and file storage
    if current_state.log_path and st.session_state.main_log_path:
        full_log_path = st.session_state.main_log_path / current_state.log_path

        scenario = ScenarioLoader.load_scenario_from_path(full_log_path)
        if scenario:
            state_manager.update_scenario(scenario)

            from rdagent.log.ui.services import FileStorageManager
            fs_iterator = FileStorageManager.create_message_iterator(full_log_path)
            if fs_iterator:
                state_manager.update_file_storage(fs_iterator)

    st.rerun()


def render_sidebar():
    """Render the sidebar with log folder selection."""
    st.sidebar.header("📁 Log Selection")

    # Get current state
    current_state = get_state()

    # Log folder selection
    if hasattr(st.session_state, 'main_log_path') and st.session_state.main_log_path:
        folders = LogFolderProcessor.filter_log_folders(st.session_state.main_log_path)

        if folders:
            selected_folder = st.sidebar.selectbox(
                "Select Log Folder",
                options=folders,
                index=0 if current_state.log_path in folders else 0,
                key="log_folder_select"
            )

            # Update state if selection changed
            if current_state.log_path != selected_folder:
                state_manager = get_session_manager()
                state_manager.update_log_path(selected_folder)
                st.rerun()
        else:
            st.sidebar.error("No log folders found")
    else:
        st.sidebar.warning("Please set log path")

    # Navigation Controls
    st.sidebar.header("🎮 Navigation Controls")

    col1, col2 = st.sidebar.columns([1, 1])
    with col1:
        if st.button(":green[**All Loops**]", use_container_width=True):
            load_all_messages()
        if st.button("**Reset**", use_container_width=True):
            reset_current_trace()

    with col2:
        if st.button(":green[Next Loop]", use_container_width=True):
            load_next_loop()
        if st.button("Next Step", use_container_width=True):
            load_next_step()

    # Configuration Controls
    with st.sidebar.popover(":orange[**Config⚙️**]", use_container_width=True):
        excluded_tags = st.multiselect(
            "Excluded log tags",
            ["llm_messages", "debug_tpl", "debug_llm"],
            ["llm_messages"],
            key="excluded_tags"
        )
        excluded_types = st.multiselect(
            "Excluded log types",
            ["str", "dict", "list"],
            ["str"],
            key="excluded_types"
        )

        # Update state with new exclusions
        current_state.excluded_tags = excluded_tags
        current_state.excluded_types = excluded_types

    # Debug Controls
    if st.session_state.get('debug_mode', False):
        st.sidebar.header("🐛 Debug Controls")
        debug = st.sidebar.toggle("Debug Mode", value=False)

        if debug:
            if st.sidebar.button("Single Step Run", use_container_width=True):
                load_single_step()

    # Display current scenario info
    if current_state.scenario:
        scenario_type = type(current_state.scenario).__name__
        st.sidebar.info(f"**Scenario**: {scenario_type}")

        if hasattr(current_state.scenario, 'experiment_setting'):
            with st.sidebar.expander("Experiment Settings"):
                st.markdown(current_state.scenario.experiment_setting, unsafe_allow_html=True)


def render_summary_section():
    """Render the summary section."""
    st.header(IconManager.format_with_icon("Summary", "metrics"), divider="rainbow", anchor="_summary")

    current_state = get_state()

    if isinstance(current_state.scenario, CustomStrategyScenario):
        # Custom strategy scenario has different summary handling
        st.info("Custom Strategy Scenario Summary")
        # Add custom strategy specific summary logic here
        return

    # Standard summary for other scenarios
    if current_state.all_metric_series:
        # Create metrics DataFrame
        metrics_df = None  # This would be populated from metric series

        if metrics_df is not None:
            display_metrics_dataframe(metrics_df, "Performance Metrics")

            # Show metrics chart if data is available
            if len(metrics_df.columns) > 0:
                rows = min(2, (len(metrics_df.columns) + 1) // 2)
                cols = min(2, len(metrics_df.columns))
                metrics_window(metrics_df, rows, cols)

    # Show hypothesis summary if available
    current_round = current_state.lround
    if current_round > 0:
        hypotheses = current_state.hypotheses.get(current_round)
        decisions = current_state.h_decisions.get(current_round, {})

        if hypotheses and decisions:
            st.subheader("Hypothesis Summary")

            # Convert to proper format if needed
            if not isinstance(hypotheses, dict):
                hypotheses = {0: hypotheses} if hypotheses else {}
            if not isinstance(decisions, dict):
                decisions = {0: decisions} if isinstance(decisions, bool) else {}

            display_hypotheses(hypotheses, decisions)


def render_rd_loops_section():
    """Render the R&D loops section."""
    current_state = get_state()

    if isinstance(current_state.scenario, SIMILAR_SCENARIOS):
        st.header(IconManager.format_with_icon("R&D Loops", "loop"), divider="rainbow", anchor="_rdloops")

        if len(current_state.msgs) > 1:
            r_options = list(current_state.msgs.keys())
            if 0 in r_options:
                r_options.remove(0)

            if r_options:
                # Round selection
                initial_index = max(0, min(current_state.lround - 1, len(r_options) - 1))
                selected_round = st.radio(
                    "**Loops**",
                    horizontal=True,
                    options=r_options,
                    index=initial_index,
                    key="round_selector"
                )

                # Update current round in state
                if selected_round != current_state.lround:
                    state_manager = get_session_manager()
                    state_manager.set_current_round(selected_round)

                return selected_round
            else:
                return 1
        else:
            return 1
    elif isinstance(current_state.scenario, GeneralModelScenario):
        return 0
    else:
        st.error("Unknown Scenario!")
        st.stop()


def render_main_content(selected_round):
    """Render the main content area."""
    current_state = get_state()

    # Create columns for research/feedback and development
    if isinstance(current_state.scenario, SIMILAR_SCENARIOS):
        rf_col, dev_col = st.columns([2, 2])
    elif isinstance(current_state.scenario, GeneralModelScenario):
        rf_col = st.container()
        dev_col = st.container()
        selected_round = 0
    else:
        st.error("Unknown scenario type")
        return

    with rf_col:
        render_research_feedback_section(selected_round)

    with dev_col.container(border=True):
        render_development_section(selected_round)


def render_research_feedback_section(round_num):
    """Render research and feedback sections."""
    from rdagent.log.ui.pages.research import render_research_window

    render_research_window(round_num)
    feedback_window(round_num)


def render_development_section(round_num):
    """Render development/evolving section."""
    from rdagent.log.ui.pages.evolving import render_evolving_window

    render_evolving_window(round_num)


def render_dashboard():
    """Render the complete dashboard."""
    # Apply global styles
    apply_ui_styles()

    # Initialize session state
    init_session_state()

    # Render sidebar
    render_sidebar()

    # Check if scenario is loaded
    current_state = get_state()
    if current_state.scenario is None:
        st.warning("No scenario loaded. Please select a valid log folder.")
        return

    # Render main sections
    render_summary_section()

    # Task completion analysis (if available)
    if st.toggle("Show Task Completion Analysis"):
        render_task_analysis()

    selected_round = render_rd_loops_section()

    if selected_round is not None:
        render_main_content(selected_round)

    # Footer
    render_footer()


def render_task_analysis():
    """Render task completion analysis."""
    st.subheader("Task Completion Analysis")

    # This would contain the analyze_task_completion logic
    # For now, show a placeholder
    st.info("Task completion analysis would be displayed here")


def render_footer():
    """Render footer with disclaimer."""
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("#### Disclaimer")
    st.markdown(
        "*This content is AI-generated and may not be fully accurate or up-to-date; "
        "please verify with a professional for critical matters.*",
        unsafe_allow_html=True,
    )