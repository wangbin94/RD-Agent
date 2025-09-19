"""Task and hypothesis display components for RD-Agent UI."""

from typing import Dict, List, Union

import pandas as pd
import streamlit as st

from rdagent.components.coder.factor_coder.factor import FactorTask
from rdagent.components.coder.model_coder.model import ModelTask
from rdagent.core.proposal import Hypothesis


def tabs_hint():
    """Display hint for tab navigation."""
    st.info(
        "💡 **Tips**: You can use the left ⬅️ and right ➡️ arrow keys to switch between tabs. "
        "Or click on the tab headers to navigate directly."
    )


def display_factor_task(task: FactorTask):
    """Display a single factor task.

    Args:
        task: Factor task to display
    """
    st.markdown(f"**Description**: {task.factor_description}")

    st.latex("Formulation")
    st.latex(task.factor_formulation)

    if isinstance(task.variables, dict) and task.variables:
        mks = "| Variable | Description |\n| --- | --- |\n"
        for variable, description in task.variables.items():
            mks += f"| ${variable}$ | {description} |\n"
        st.markdown(mks)


def display_model_task(task: ModelTask):
    """Display a single model task.

    Args:
        task: Model task to display
    """
    st.markdown(f"**Model Type**: {task.model_type}")
    st.markdown(f"**Description**: {task.description}")

    st.latex("Formulation")
    st.latex(task.formulation)

    if task.variables:
        mks = "| Variable | Description |\n| --- | --- |\n"
        for variable, description in task.variables.items():
            mks += f"| ${variable}$ | {description} |\n"
        st.markdown(mks)

    st.markdown(f"**Train Para**: {task.training_hyperparameters}")


def tasks_window(tasks: List[Union[FactorTask, ModelTask]]):
    """Display tasks window with tabs for each task.

    Args:
        tasks: List of tasks to display (either FactorTask or ModelTask)
    """
    if not tasks:
        st.info("No tasks available")
        return

    if isinstance(tasks[0], FactorTask):
        st.markdown("**Factor Tasks🚩**")
        tab_names = [f.factor_name for f in tasks]

        # Show hint if tab names are too long
        if sum(len(name) for name in tab_names) > 100:
            tabs_hint()

        tabs = st.tabs(tab_names)
        for i, task in enumerate(tasks):
            with tabs[i]:
                display_factor_task(task)

    elif isinstance(tasks[0], ModelTask):
        st.markdown("**Model Tasks🚩**")
        tab_names = [m.name for m in tasks]

        # Show hint if tab names are too long
        if sum(len(name) for name in tab_names) > 100:
            tabs_hint()

        tabs = st.tabs(tab_names)
        for i, task in enumerate(tasks):
            with tabs[i]:
                display_model_task(task)

    else:
        st.error(f"Unsupported task type: {type(tasks[0])}")


def display_hypotheses(
    hypotheses: Dict[int, Hypothesis],
    decisions: Dict[int, bool],
    success_only: bool = False
):
    """Display hypotheses in a styled dataframe.

    Args:
        hypotheses: Dictionary mapping hypothesis ID to Hypothesis object
        decisions: Dictionary mapping hypothesis ID to decision (True/False)
        success_only: If True, only show successful hypotheses
    """
    name_mapping = {
        "hypothesis": "RD-Agent proposes the hypothesis⬇️",
        "concise_justification": "because the reason⬇️",
        "concise_observation": "based on the observation⬇️",
        "concise_knowledge": "Knowledge⬇️ gained after practice",
    }

    # Filter hypotheses based on success_only flag
    if success_only:
        filtered_hypotheses = {k: v.__dict__ for k, v in hypotheses.items() if decisions.get(k, False)}
    else:
        filtered_hypotheses = {k: v.__dict__ for k, v in hypotheses.items()}

    if not filtered_hypotheses:
        st.info("No hypotheses to display")
        return

    df = pd.DataFrame(filtered_hypotheses).T

    # Swap columns if both exist (correcting the order)
    if "concise_observation" in df.columns and "concise_justification" in df.columns:
        df["concise_observation"], df["concise_justification"] = (
            df["concise_justification"],
            df["concise_observation"]
        )
        df.rename(
            columns={
                "concise_observation": "concise_justification",
                "concise_justification": "concise_observation"
            },
            inplace=True,
        )

    # Remove unnecessary columns
    columns_to_remove = ["reason", "concise_reason"]
    for col in columns_to_remove:
        if col in df.columns:
            df.drop([col], axis=1, inplace=True)

    # Apply name mapping
    df.columns = df.columns.map(lambda x: name_mapping.get(x, x))

    # Remove columns with all None values
    for col in list(df.columns):
        if all(value is None for value in df[col]):
            df.drop([col], axis=1, inplace=True)

    # Styling functions
    def style_rows(row):
        """Style rows based on decision (green for accepted hypotheses)."""
        if decisions.get(row.name, False):
            return ["color: green;"] * len(row)
        return [""] * len(row)

    def style_columns(col):
        """Style columns (italic for non-hypothesis columns, bold for hypothesis)."""
        hypothesis_col = name_mapping.get("hypothesis", "hypothesis")
        if col.name != hypothesis_col:
            return ["font-style: italic;"] * len(col)
        return ["font-weight: bold;"] * len(col)

    # Display styled dataframe
    styled_df = df.style.apply(style_rows, axis=1).apply(style_columns, axis=0)
    st.dataframe(styled_df, use_container_width=True)


def hypothesis_summary_cards(hypotheses: Dict[int, Hypothesis], decisions: Dict[int, bool]):
    """Display hypotheses as summary cards.

    Args:
        hypotheses: Dictionary mapping hypothesis ID to Hypothesis object
        decisions: Dictionary mapping hypothesis ID to decision (True/False)
    """
    for hyp_id, hypothesis in hypotheses.items():
        decision = decisions.get(hyp_id, False)
        card_color = "green" if decision else "red"
        status = "✅ Accepted" if decision else "❌ Rejected"

        with st.container():
            st.markdown(
                f"""
                <div style="border: 2px solid {card_color}; border-radius: 10px; padding: 15px; margin: 10px 0;">
                    <h4 style="color: {card_color};">Hypothesis #{hyp_id} - {status}</h4>
                    <p><strong>Hypothesis:</strong> {hypothesis.hypothesis}</p>
                    {f'<p><strong>Justification:</strong> {hypothesis.concise_justification}</p>' if hasattr(hypothesis, 'concise_justification') and hypothesis.concise_justification else ''}
                    {f'<p><strong>Observation:</strong> {hypothesis.concise_observation}</p>' if hasattr(hypothesis, 'concise_observation') and hypothesis.concise_observation else ''}
                </div>
                """,
                unsafe_allow_html=True
            )


def task_progress_indicator(completed_tasks: int, total_tasks: int):
    """Display task progress indicator.

    Args:
        completed_tasks: Number of completed tasks
        total_tasks: Total number of tasks
    """
    if total_tasks == 0:
        progress = 0
    else:
        progress = completed_tasks / total_tasks

    st.progress(progress)
    st.metric(
        label="Task Progress",
        value=f"{completed_tasks}/{total_tasks}",
        delta=f"{progress:.1%} Complete"
    )