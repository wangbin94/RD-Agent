"""Feedback components for RD-Agent UI."""

from pathlib import Path
from typing import Union

import streamlit as st

from rdagent.components.coder.factor_coder.evaluators import FactorSingleFeedback
from rdagent.components.coder.model_coder.evaluators import ModelSingleFeedback
from rdagent.components.coder.CoSTEER.evaluators import CoSTEERMultiFeedback, CoSTEERSingleFeedback
from rdagent.core.proposal import HypothesisFeedback
from rdagent.log.ui.qlib_report_figure import report_figure
from rdagent.log.ui.state import get_state
from rdagent.scenarios.general_model.scenario import GeneralModelScenario
from rdagent.scenarios.kaggle.experiment.scenario import KGScenario
from rdagent.scenarios.qlib.experiment.factor_experiment import QlibFactorScenario
from rdagent.scenarios.qlib.experiment.factor_from_report_experiment import QlibFactorFromReportScenario
from rdagent.scenarios.qlib.experiment.model_experiment import QlibModelScenario
from rdagent.scenarios.qlib.experiment.quant_experiment import QlibQuantScenario
from rdagent.scenarios.quant_strategy_lab_scenario import CustomStrategyScenario

# Define similar scenarios for type checking
SIMILAR_SCENARIOS = (
    QlibModelScenario,
    QlibFactorScenario,
    QlibFactorFromReportScenario,
    QlibQuantScenario,
    KGScenario,
    CustomStrategyScenario,
)


def evolving_feedback_window(wsf: Union[FactorSingleFeedback, ModelSingleFeedback]):
    """Display feedback tabs for evolving components.

    Args:
        wsf: Workspace feedback object (Factor or Model)
    """
    if isinstance(wsf, FactorSingleFeedback):
        ffc, efc, cfc, vfc = st.tabs(
            ["**Final Feedback🏁**", "Execution Feedback🖥️", "Code Feedback📄", "Value Feedback🔢"]
        )
        with ffc:
            st.markdown(wsf.final_feedback)
        with efc:
            st.code(wsf.execution_feedback, language="log")
        with cfc:
            st.markdown(wsf.code_feedback)
        with vfc:
            st.markdown(wsf.value_feedback)

    elif isinstance(wsf, ModelSingleFeedback):
        ffc, efc, cfc, msfc, vfc = st.tabs(
            [
                "**Final Feedback🏁**",
                "Execution Feedback🖥️",
                "Code Feedback📄",
                "Model Shape Feedback📐",
                "Value Feedback🔢",
            ]
        )
        with ffc:
            st.markdown(wsf.final_feedback)
        with efc:
            st.code(wsf.execution_feedback, language="log")
        with cfc:
            st.markdown(wsf.code_feedback)
        with msfc:
            st.markdown(wsf.shape_feedback)
        with vfc:
            st.markdown(wsf.value_feedback)

    else:
        # Fallback for any feedback object that has the standard UI properties
        if all(hasattr(wsf, attr) for attr in ['final_feedback', 'execution_feedback', 'code_feedback', 'value_feedback']):
            ffc, efc, cfc, vfc = st.tabs(
                ["**Final Feedback🏁**", "Execution Feedback🖥️", "Code Feedback📄", "Value Feedback🔢"]
            )
            with ffc:
                st.markdown(wsf.final_feedback)
            with efc:
                st.code(wsf.execution_feedback, language="log")
            with cfc:
                st.markdown(wsf.code_feedback)
            with vfc:
                st.markdown(wsf.value_feedback)
        else:
            st.warning(f"Unsupported feedback type: {type(wsf).__name__}. Expected FactorSingleFeedback or ModelSingleFeedback.")


def display_hypothesis_feedback(feedback: HypothesisFeedback):
    """Display hypothesis feedback information.

    Args:
        feedback: Hypothesis feedback object
    """
    st.markdown("**Hypothesis Feedback🔍**")
    st.markdown(
        f"""
- **Observations**: {feedback.observations}
- **Hypothesis Evaluation**: {feedback.hypothesis_evaluation}
- **New Hypothesis**: {feedback.new_hypothesis}
- **Decision**: {feedback.decision}
- **Reason**: {feedback.reason}"""
    )


def display_costeer_feedback(feedback: CoSTEERMultiFeedback):
    """Display CoSTEER multi-feedback information.

    Args:
        feedback: CoSTEER multi-feedback object
    """
    st.markdown("**CoSTEER Feedback🔧**")

    # Display overall status
    st.markdown(f"**Overall Status**: {'✅ Acceptable' if feedback.is_acceptable() else '❌ Not Acceptable'}")
    st.markdown(f"**Finished**: {'✅ Complete' if feedback.finished() else '⏳ In Progress'}")
    st.markdown(f"**Number of Tasks**: {len(feedback)} tasks")

    # Display individual feedback for each task
    for i, single_feedback in enumerate(feedback):
        if single_feedback is not None:
            with st.expander(f"Task {i+1} Feedback", expanded=i == 0):
                st.markdown("**Execution Feedback**")
                st.code(single_feedback.execution, language="text")

                if single_feedback.return_checking:
                    st.markdown("**Return Checking**")
                    st.markdown(single_feedback.return_checking)

                st.markdown("**Code Feedback**")
                st.markdown(single_feedback.code)

                if single_feedback.final_decision is not None:
                    decision_text = "✅ Accepted" if single_feedback.final_decision else "❌ Rejected"
                    st.markdown(f"**Final Decision**: {decision_text}")
        else:
            st.warning(f"Task {i+1}: No feedback available (task may have been skipped)")


def display_generic_feedback(feedback):
    """Display generic feedback for unknown feedback types.

    Args:
        feedback: Any feedback object
    """
    st.markdown("**Generic Feedback📋**")

    # Try to display common attributes
    feedback_type = type(feedback).__name__
    st.markdown(f"**Feedback Type**: {feedback_type}")

    # Check for common feedback attributes and display them
    common_attrs = ['decision', 'reason', 'message', 'status', 'result', 'summary']

    displayed_attrs = []
    for attr in common_attrs:
        if hasattr(feedback, attr):
            value = getattr(feedback, attr)
            if value is not None:
                st.markdown(f"**{attr.title()}**: {value}")
                displayed_attrs.append(attr)

    # If no common attributes found, show the string representation
    if not displayed_attrs:
        st.markdown("**Content**:")
        st.text(str(feedback))


def display_workspace_info(round_num: int):
    """Display workspace information for the given round.

    Args:
        round_num: Round number to display workspace for
    """
    current_state = get_state()
    if fbr := current_state.msgs[round_num]["runner result"]:
        try:
            st.write("workspace")
            st.write(fbr[0].content.experiment_workspace.workspace_path)
            st.write(fbr[0].content.stdout)
        except Exception as e:
            st.error(f"Error displaying workspace path: {str(e)}")


def display_experiment_config():
    """Display experiment configuration."""
    current_state = get_state()
    with st.expander("**Config⚙️**", expanded=True):
        st.markdown(current_state.scenario.experiment_setting, unsafe_allow_html=True)


def display_quantitative_chart(round_num: int):
    """Display quantitative backtesting chart.

    Args:
        round_num: Round number to display chart for
    """
    current_state = get_state()
    if fbr := current_state.msgs[round_num]["Quantitative Backtesting Chart"]:
        st.markdown("**Returns📈**")
        fig = report_figure(fbr[0].content)
        st.plotly_chart(fig)


def display_kaggle_submission(round_num: int):
    """Display Kaggle submission download for KGScenario.

    Args:
        round_num: Round number to display submission for
    """
    current_state = get_state()
    if isinstance(current_state.scenario, KGScenario):
        if fbe := current_state.msgs[round_num]["runner result"]:
            submission_path = fbe[0].content.experiment_workspace.workspace_path / "submission.csv"
            st.markdown(
                f":green[**Exp Workspace**]: {str(fbe[0].content.experiment_workspace.workspace_path.absolute())}"
            )
            try:
                data = submission_path.read_bytes()
                st.download_button(
                    label="**Download** submission.csv",
                    data=data,
                    file_name="submission.csv",
                    mime="text/csv",
                )
            except Exception as e:
                st.markdown(f":red[**Download Button Error**]: {e}")


def feedback_window(round_num: int = None):
    """Display feedback window for the current or specified round.

    Args:
        round_num: Round number to display feedback for. Uses global round if None.
    """
    current_state = get_state()
    if round_num is None:
        round_num = current_state.lround

    if isinstance(current_state.scenario, SIMILAR_SCENARIOS):
        with st.container(border=True):
            st.subheader("Feedback📝", divider="orange", anchor="_feedback")

            if current_state.lround > 0 and isinstance(current_state.scenario, SIMILAR_SCENARIOS):
                display_workspace_info(round_num)
                display_experiment_config()

            if fb := current_state.msgs[round_num]["feedback"]:
                display_quantitative_chart(round_num)
                feedback_content = fb[0].content

                # Display appropriate feedback based on type
                if isinstance(feedback_content, HypothesisFeedback):
                    display_hypothesis_feedback(feedback_content)
                elif isinstance(feedback_content, CoSTEERMultiFeedback):
                    display_costeer_feedback(feedback_content)
                else:
                    display_generic_feedback(feedback_content)

            display_kaggle_submission(round_num)


def feedback_summary_panel(round_num: int):
    """Display a compact feedback summary panel.

    Args:
        round_num: Round number to display summary for
    """
    current_state = get_state()
    with st.expander(f"Round {round_num} Feedback Summary", expanded=False):
        if fb := current_state.msgs[round_num]["feedback"]:
            feedback_content = fb[0].content

            if isinstance(feedback_content, HypothesisFeedback):
                st.markdown(f"**Decision**: {feedback_content.decision}")
                st.markdown(f"**Reason**: {feedback_content.reason}")
                if feedback_content.new_hypothesis:
                    st.markdown(f"**New Hypothesis**: {feedback_content.new_hypothesis}")
            elif isinstance(feedback_content, CoSTEERMultiFeedback):
                st.markdown(f"**Type**: CoSTEER Feedback")
                st.markdown(f"**Status**: {'✅ Acceptable' if feedback_content.is_acceptable() else '❌ Not Acceptable'}")
                st.markdown(f"**Tasks**: {len(feedback_content)}")
            else:
                st.markdown(f"**Type**: {type(feedback_content).__name__}")
                if hasattr(feedback_content, 'decision'):
                    st.markdown(f"**Decision**: {feedback_content.decision}")
        else:
            st.info("No feedback available for this round")