"""Research window page for RD-Agent UI."""

import streamlit as st

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


def render_pdf_screenshots(round_num):
    """Render PDF screenshots for the given round.

    Args:
        round_num: Round number to display screenshots for
    """
    current_state = get_state()

    if pim := current_state.msgs[round_num].get("load_pdf_screenshot"):
        st.subheader("📄 Research Papers")

        # Display up to 2 PDF screenshots
        for i in range(min(2, len(pim))):
            with st.expander(f"Paper {i+1}", expanded=i == 0):
                try:
                    # Display the PDF screenshot image
                    st.image(pim[i].content, caption=f"Paper {i+1} Screenshot")
                except Exception as e:
                    st.error(f"Error displaying PDF screenshot: {e}")


def render_hypothesis_generation(round_num):
    """Render hypothesis generation for the given round.

    Args:
        round_num: Round number to display hypothesis generation for
    """
    current_state = get_state()

    if hg := current_state.msgs[round_num].get("hypothesis generation"):
        st.subheader("💡 Hypothesis Generation")

        for i, hypothesis_msg in enumerate(hg):
            with st.expander(f"Hypothesis {i+1}", expanded=i == 0):
                try:
                    # Display hypothesis content
                    if hasattr(hypothesis_msg.content, 'hypothesis'):
                        st.markdown(f"**Hypothesis**: {hypothesis_msg.content.hypothesis}")

                    if hasattr(hypothesis_msg.content, 'reason'):
                        st.markdown(f"**Reasoning**: {hypothesis_msg.content.reason}")

                    if hasattr(hypothesis_msg.content, 'concise_justification'):
                        st.markdown(f"**Justification**: {hypothesis_msg.content.concise_justification}")

                    if hasattr(hypothesis_msg.content, 'concise_observation'):
                        st.markdown(f"**Observation**: {hypothesis_msg.content.concise_observation}")

                except Exception as e:
                    st.error(f"Error displaying hypothesis: {e}")
                    # Fallback: display raw content
                    st.text(str(hypothesis_msg.content))


def render_task_information(round_num):
    """Render task information for the given round.

    Args:
        round_num: Round number to display task information for
    """
    current_state = get_state()

    # Look for task-related messages
    task_types = ["factor task", "model task", "task generation", "tasks"]

    for task_type in task_types:
        if task_msgs := current_state.msgs[round_num].get(task_type):
            st.subheader(f"🚩 {task_type.title()}")

            for i, task_msg in enumerate(task_msgs):
                with st.expander(f"Task {i+1}", expanded=i == 0):
                    try:
                        from rdagent.log.ui.components.tasks import display_factor_task, display_model_task
                        from rdagent.components.coder.factor_coder.factor import FactorTask
                        from rdagent.components.coder.model_coder.model import ModelTask

                        if isinstance(task_msg.content, FactorTask):
                            display_factor_task(task_msg.content)
                        elif isinstance(task_msg.content, ModelTask):
                            display_model_task(task_msg.content)
                        else:
                            # Generic task display
                            st.write(task_msg.content)

                    except Exception as e:
                        st.error(f"Error displaying task: {e}")
                        st.text(str(task_msg.content))


def render_research_summaries(round_num):
    """Render research summaries and insights for the given round.

    Args:
        round_num: Round number to display research summaries for
    """
    current_state = get_state()

    # Look for research-related messages
    research_types = ["research summary", "insights", "literature review", "background research"]

    for research_type in research_types:
        if research_msgs := current_state.msgs[round_num].get(research_type):
            st.subheader(f"📚 {research_type.title()}")

            for i, research_msg in enumerate(research_msgs):
                with st.expander(f"{research_type.title()} {i+1}", expanded=i == 0):
                    try:
                        # Display research content
                        if hasattr(research_msg.content, 'summary'):
                            st.markdown("**Summary**")
                            st.markdown(research_msg.content.summary)

                        if hasattr(research_msg.content, 'key_insights'):
                            st.markdown("**Key Insights**")
                            if isinstance(research_msg.content.key_insights, list):
                                for insight in research_msg.content.key_insights:
                                    st.markdown(f"- {insight}")
                            else:
                                st.markdown(research_msg.content.key_insights)

                        if hasattr(research_msg.content, 'methodology'):
                            st.markdown("**Methodology**")
                            st.markdown(research_msg.content.methodology)

                        # Fallback: display as markdown
                        if not any(hasattr(research_msg.content, attr) for attr in ['summary', 'key_insights', 'methodology']):
                            st.markdown(str(research_msg.content))

                    except Exception as e:
                        st.error(f"Error displaying research summary: {e}")
                        st.text(str(research_msg.content))


def render_data_exploration(round_num):
    """Render data exploration results for the given round.

    Args:
        round_num: Round number to display data exploration for
    """
    current_state = get_state()

    if data_msgs := current_state.msgs[round_num].get("data exploration"):
        st.subheader("📊 Data Exploration")

        for i, data_msg in enumerate(data_msgs):
            with st.expander(f"Data Analysis {i+1}", expanded=i == 0):
                try:
                    # Display data exploration content
                    if hasattr(data_msg.content, 'dataset_info'):
                        st.markdown("**Dataset Information**")
                        st.json(data_msg.content.dataset_info)

                    if hasattr(data_msg.content, 'statistics'):
                        st.markdown("**Statistics**")
                        st.json(data_msg.content.statistics)

                    if hasattr(data_msg.content, 'visualizations'):
                        st.markdown("**Visualizations**")
                        # Handle visualization content appropriately
                        st.write(data_msg.content.visualizations)

                    # Fallback display
                    if not any(hasattr(data_msg.content, attr) for attr in ['dataset_info', 'statistics', 'visualizations']):
                        st.write(data_msg.content)

                except Exception as e:
                    st.error(f"Error displaying data exploration: {e}")
                    st.text(str(data_msg.content))


def render_research_window(round_num):
    """Render the complete research window.

    Args:
        round_num: Round number to display research for
    """
    current_state = get_state()

    with st.container(border=True):
        # Set title based on scenario type
        if isinstance(current_state.scenario, SIMILAR_SCENARIOS):
            title = IconManager.format_with_icon("Research", "research")
        else:
            title = IconManager.format_with_icon("Research (reader)", "research")

        st.subheader(title, divider="blue", anchor="_research")

        if isinstance(current_state.scenario, SIMILAR_SCENARIOS):
            # Render PDF screenshots
            render_pdf_screenshots(round_num)

            # Render hypothesis generation
            render_hypothesis_generation(round_num)

            # Render task information
            render_task_information(round_num)

            # Render research summaries
            render_research_summaries(round_num)

        elif isinstance(current_state.scenario, GeneralModelScenario):
            # Different content for GeneralModelScenario
            st.info("General Model Scenario Research")

            # Render data exploration
            render_data_exploration(round_num)

            # Show any available research content
            if current_state.msgs[round_num]:
                available_types = list(current_state.msgs[round_num].keys())
                if available_types:
                    st.markdown("**Available Research Data:**")
                    for msg_type in available_types:
                        st.markdown(f"- {msg_type}")

        else:
            st.warning("Unknown scenario type for research window")

        # Show debug information if no content is available
        if not any(current_state.msgs[round_num].values()):
            st.info(f"No research data available for round {round_num}")


def render_research_navigation():
    """Render navigation controls for research data."""
    current_state = get_state()

    if len(current_state.msgs) > 1:
        available_rounds = [r for r in current_state.msgs.keys() if r != 0]

        if available_rounds:
            st.selectbox(
                "Select Research Round",
                options=available_rounds,
                index=available_rounds.index(current_state.lround) if current_state.lround in available_rounds else 0,
                key="research_round_selector"
            )