"""Chart components for RD-Agent UI."""

import textwrap
from io import BytesIO
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from rdagent.core.proposal import Hypothesis
from rdagent.log.ui.state import get_state


def hypothesis_hover_text(hypothesis: Hypothesis, decision: bool = False) -> str:
    """Generate hover text for hypothesis data points.

    Args:
        hypothesis: The hypothesis object
        decision: Whether the hypothesis was accepted

    Returns:
        HTML formatted hover text
    """
    color = "green" if decision else "black"
    text = hypothesis.hypothesis
    lines = textwrap.wrap(text, width=60)
    return f"<span style='color: {color};'>{'<br>'.join(lines)}</span>"


def create_metrics_chart(
    df: pd.DataFrame,
    rows: int,
    cols: int,
    height: int = 300,
    colors: Optional[list[str]] = None
) -> go.Figure:
    """Create metrics subplot chart.

    Args:
        df: DataFrame with metrics data
        rows: Number of subplot rows
        cols: Number of subplot columns
        height: Chart height in pixels
        colors: List of colors for each column

    Returns:
        Plotly figure object
    """
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=df.columns)

    # Generate hover texts from current hypotheses
    hover_texts = []
    current_state = get_state()
    current_hypotheses = current_state.hypotheses.get(current_state.lround, [])
    current_decisions = current_state.h_decisions.get(current_state.lround, [])

    # Convert to list if it's a single hypothesis object
    if not isinstance(current_hypotheses, list):
        current_hypotheses = [current_hypotheses] if current_hypotheses else []
    if not isinstance(current_decisions, list):
        current_decisions = [current_decisions] if current_decisions else []

    for i in df.index:
        if i != "Alpha Base" and i != "Baseline":
            # Handle different index formats safely
            if isinstance(i, str) and i.startswith("hypo_"):
                try:
                    idx = int(i[5:])  # "hypo_" is 5 characters
                    if idx < len(current_hypotheses) and idx < len(current_decisions):
                        hover_texts.append(hypothesis_hover_text(current_hypotheses[idx], current_decisions[idx]))
                except (ValueError, IndexError, KeyError):
                    pass
            elif isinstance(i, int):
                # Handle integer indices directly
                try:
                    if i < len(current_hypotheses) and i < len(current_decisions):
                        hover_texts.append(hypothesis_hover_text(current_hypotheses[i], current_decisions[i]))
                except (IndexError, KeyError):
                    pass

    if current_state.alpha_baseline_metrics is not None:
        hover_texts = ["Baseline"] + hover_texts

    # Add traces for each column
    for ci, col in enumerate(df.columns):
        row = ci // cols + 1
        col_num = ci % cols + 1
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[col],
                name=col,
                mode="lines+markers",
                connectgaps=True,
                marker=dict(size=10, color=colors[ci]) if colors else dict(size=10),
                hovertext=hover_texts,
                hovertemplate="%{hovertext}<br><br><span style='color: black'>%{x} Value:</span> <span style='color: blue'>%{y}</span><extra></extra>",
            ),
            row=row,
            col=col_num,
        )

    fig.update_layout(showlegend=False, height=height)

    # Update x-axis styling for baseline metrics
    if current_state.alpha_baseline_metrics is not None:
        for i in range(1, rows + 1):  # rows
            for j in range(1, cols + 1):  # columns
                fig.update_xaxes(
                    tickvals=[df.index[0]] + list(df.index[1:]),
                    ticktext=[f'<span style="color:blue; font-weight:bold">{df.index[0]}</span>'] + list(df.index[1:]),
                    row=i,
                    col=j,
                )

    return fig


def metrics_window(df: pd.DataFrame, rows: int, cols: int, *, height: int = 300, colors: Optional[list[str]] = None):
    """Display metrics chart with download option.

    Args:
        df: DataFrame with metrics data
        rows: Number of subplot rows
        cols: Number of subplot columns
        height: Chart height in pixels
        colors: List of colors for each column
    """
    fig = create_metrics_chart(df, rows, cols, height, colors)
    st.plotly_chart(fig)

    # Add download button for CSV export
    buffer = BytesIO()
    df.to_csv(buffer)
    buffer.seek(0)
    st.download_button(
        label="download the metrics (csv)",
        data=buffer,
        file_name="metrics.csv",
        mime="text/csv"
    )


def display_metrics_dataframe(df: pd.DataFrame, title: str = "Metrics"):
    """Display metrics as a styled dataframe.

    Args:
        df: DataFrame to display
        title: Title for the metrics table
    """
    st.subheader(title)

    def style_rows(row):
        if row.name == "Alpha Base" or row.name == "Baseline":
            return ["background-color: lightblue"] * len(row)
        return [""] * len(row)

    def style_columns(col):
        if col.name in ["IC", "ICIR", "Rank IC", "Rank ICIR"]:
            return ["background-color: lightgreen"] * len(col)
        return [""] * len(col)

    styled_df = df.style.apply(style_rows, axis=1).apply(style_columns, axis=0)
    st.dataframe(styled_df, use_container_width=True)