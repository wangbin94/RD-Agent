"""Evolving/Development window page for RD-Agent UI."""

import streamlit as st

from rdagent.log.ui.components.feedback import evolving_feedback_window
from rdagent.log.ui.state import get_state
from rdagent.log.ui.utils import IconManager
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


def render_evolving_status(round_num):
    """Render evolving status section.

    Args:
        round_num: Round number to display status for
    """
    current_state = get_state()

    if current_state.erounds[round_num] > 0:
        st.markdown("**☑️ Evolving Status**")

        es = current_state.e_decisions[round_num]
        e_status_mks = "".join(f"| {ei} " for ei in range(1, current_state.erounds[round_num] + 1)) + "|\n"
        e_status_mks += "|--" * current_state.erounds[round_num] + "|\n"

        for ei, estatus in es.items():
            if not estatus:
                estatus = (0, 0, 0)
            e_status_mks += f"| {estatus[0]} / {estatus[1]} / {estatus[2]} "

        e_status_mks += "|\n"
        st.markdown(e_status_mks)

        # Legend
        st.markdown("**Legend**: Success / Failure / Total")


def render_code_development(round_num):
    """Render code development section.

    Args:
        round_num: Round number to display development for
    """
    current_state = get_state()

    # Look for code-related messages
    code_types = ["coding", "code generation", "implementation", "evolving code"]

    for code_type in code_types:
        if code_msgs := current_state.msgs[round_num].get(code_type):
            st.subheader(f"💻 {code_type.title()}")

            for i, code_msg in enumerate(code_msgs):
                with st.expander(f"{code_type.title()} {i+1}", expanded=i == 0):
                    try:
                        # Display code content
                        if hasattr(code_msg.content, 'code'):
                            st.code(code_msg.content.code, language='python')

                        elif hasattr(code_msg.content, 'implementation'):
                            st.code(code_msg.content.implementation, language='python')

                        elif hasattr(code_msg.content, 'source_code'):
                            st.code(code_msg.content.source_code, language='python')

                        else:
                            # Try to display as code if it looks like code
                            content_str = str(code_msg.content)
                            if any(keyword in content_str for keyword in ['def ', 'class ', 'import ', 'from ']):
                                st.code(content_str, language='python')
                            else:
                                st.markdown(content_str)

                    except Exception as e:
                        st.error(f"Error displaying code: {e}")
                        st.text(str(code_msg.content))


def render_execution_results(round_num):
    """Render execution results section.

    Args:
        round_num: Round number to display execution results for
    """
    current_state = get_state()

    # Look for execution-related messages
    execution_types = ["execution", "runner result", "test results", "evaluation"]

    for exec_type in execution_types:
        if exec_msgs := current_state.msgs[round_num].get(exec_type):
            st.subheader(f"🔧 {exec_type.title()}")

            for i, exec_msg in enumerate(exec_msgs):
                with st.expander(f"{exec_type.title()} {i+1}", expanded=i == 0):
                    try:
                        # Display execution results
                        if hasattr(exec_msg.content, 'stdout'):
                            st.markdown("**Output:**")
                            st.code(exec_msg.content.stdout, language='bash')

                        if hasattr(exec_msg.content, 'stderr'):
                            st.markdown("**Errors:**")
                            st.code(exec_msg.content.stderr, language='bash')

                        if hasattr(exec_msg.content, 'return_code'):
                            st.markdown(f"**Return Code:** {exec_msg.content.return_code}")

                        if hasattr(exec_msg.content, 'execution_time'):
                            st.markdown(f"**Execution Time:** {exec_msg.content.execution_time}s")

                        # Display workspace path if available
                        if hasattr(exec_msg.content, 'experiment_workspace'):
                            workspace_path = exec_msg.content.experiment_workspace.workspace_path
                            st.markdown(f"**Workspace:** `{workspace_path}`")

                        # Fallback display
                        if not any(hasattr(exec_msg.content, attr) for attr in
                                 ['stdout', 'stderr', 'return_code', 'execution_time']):
                            st.write(exec_msg.content)

                    except Exception as e:
                        st.error(f"Error displaying execution result: {e}")
                        st.text(str(exec_msg.content))


def render_evolving_feedback(round_num):
    """Render evolving feedback section.

    Args:
        round_num: Round number to display feedback for
    """
    current_state = get_state()

    # Look for evolving feedback messages
    feedback_types = ["evolving feedback", "feedback", "evaluation feedback"]

    for feedback_type in feedback_types:
        if feedback_msgs := current_state.msgs[round_num].get(feedback_type):
            st.subheader(f"📝 {feedback_type.title()}")

            for i, feedback_msg in enumerate(feedback_msgs):
                with st.expander(f"{feedback_type.title()} {i+1}", expanded=i == 0):
                    try:
                        from rdagent.components.coder.factor_coder.evaluators import FactorSingleFeedback
                        from rdagent.components.coder.model_coder.evaluators import ModelSingleFeedback

                        # Use the feedback component if it's a supported feedback type
                        if isinstance(feedback_msg.content, (FactorSingleFeedback, ModelSingleFeedback)):
                            evolving_feedback_window(feedback_msg.content)
                        else:
                            # Generic feedback display
                            if hasattr(feedback_msg.content, 'feedback'):
                                st.markdown(feedback_msg.content.feedback)
                            elif hasattr(feedback_msg.content, 'message'):
                                st.markdown(feedback_msg.content.message)
                            else:
                                st.write(feedback_msg.content)

                    except Exception as e:
                        st.error(f"Error displaying feedback: {e}")
                        st.text(str(feedback_msg.content))


def render_model_artifacts(round_num):
    """Render model artifacts and outputs.

    Args:
        round_num: Round number to display artifacts for
    """
    current_state = get_state()

    # Look for model-related artifacts
    artifact_types = ["model output", "model artifacts", "saved models", "checkpoints"]

    for artifact_type in artifact_types:
        if artifact_msgs := current_state.msgs[round_num].get(artifact_type):
            st.subheader(f"🤖 {artifact_type.title()}")

            for i, artifact_msg in enumerate(artifact_msgs):
                with st.expander(f"{artifact_type.title()} {i+1}", expanded=i == 0):
                    try:
                        # Display artifact information
                        if hasattr(artifact_msg.content, 'model_path'):
                            st.markdown(f"**Model Path:** `{artifact_msg.content.model_path}`")

                        if hasattr(artifact_msg.content, 'metrics'):
                            st.markdown("**Metrics:**")
                            st.json(artifact_msg.content.metrics)

                        if hasattr(artifact_msg.content, 'parameters'):
                            st.markdown("**Parameters:**")
                            st.json(artifact_msg.content.parameters)

                        # Fallback display
                        if not any(hasattr(artifact_msg.content, attr) for attr in
                                 ['model_path', 'metrics', 'parameters']):
                            st.write(artifact_msg.content)

                    except Exception as e:
                        st.error(f"Error displaying artifact: {e}")
                        st.text(str(artifact_msg.content))


def render_debug_information(round_num):
    """Render debug information if available.

    Args:
        round_num: Round number to display debug info for
    """
    current_state = get_state()

    # Show available message types for debugging
    available_types = list(current_state.msgs[round_num].keys())
    if available_types:
        with st.expander("🐛 Debug Info", expanded=False):
            st.markdown("**Available message types in this round:**")
            for msg_type in available_types:
                msg_count = len(current_state.msgs[round_num][msg_type])
                st.markdown(f"- {msg_type}: {msg_count} messages")


def render_evolving_window(round_num):
    """Render the complete evolving/development window.

    Args:
        round_num: Round number to display development for
    """
    current_state = get_state()

    # Set title based on scenario type
    if isinstance(current_state.scenario, SIMILAR_SCENARIOS):
        title = IconManager.format_with_icon("Development", "development")
    else:
        title = IconManager.format_with_icon("Development (evolving coder)", "development")

    st.subheader(title, divider="green", anchor="_development")

    # Render evolving status
    render_evolving_status(round_num)

    # Render main content sections
    render_code_development(round_num)
    render_execution_results(round_num)
    render_evolving_feedback(round_num)

    # Render additional sections based on scenario type
    if isinstance(current_state.scenario, (QlibModelScenario, QlibFactorScenario)):
        render_model_artifacts(round_num)

    # Show debug info if enabled
    if st.session_state.get('debug_mode', False):
        render_debug_information(round_num)

    # Show message if no development data is available
    if not any(current_state.msgs[round_num].values()):
        st.info(f"No development data available for round {round_num}")


def render_evolving_navigation():
    """Render navigation controls for evolving data."""
    current_state = get_state()

    col1, col2 = st.columns([3, 1])

    with col1:
        if len(current_state.msgs) > 1:
            available_rounds = [r for r in current_state.msgs.keys() if r != 0]

            if available_rounds:
                st.selectbox(
                    "Select Development Round",
                    options=available_rounds,
                    index=available_rounds.index(current_state.lround) if current_state.lround in available_rounds else 0,
                    key="evolving_round_selector"
                )

    with col2:
        st.checkbox("Debug Mode", key="debug_mode", help="Show additional debug information")