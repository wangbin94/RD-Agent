"""Styling utilities for RD-Agent UI."""

import streamlit as st


class UIStyles:
    """Contains CSS styles and styling utilities."""

    # Color scheme
    COLORS = {
        "primary": "#1f77b4",
        "secondary": "#ff7f0e",
        "success": "#2ca02c",
        "warning": "#d62728",
        "info": "#17becf",
        "light": "#f8f9fa",
        "dark": "#212529",
        "border": "#dee2e6",
    }

    # Common CSS styles
    CARD_STYLE = """
    <style>
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        margin: 0.5rem 0;
    }

    .status-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 500;
        display: inline-block;
    }

    .status-success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }

    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }

    .status-error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }

    .progress-container {
        width: 100%;
        background-color: #e9ecef;
        border-radius: 0.25rem;
        overflow: hidden;
    }

    .progress-bar {
        height: 1rem;
        background-color: #007bff;
        transition: width 0.6s ease;
    }

    .hypothesis-accepted {
        border-left: 4px solid #28a745;
        background-color: #f8fff9;
    }

    .hypothesis-rejected {
        border-left: 4px solid #dc3545;
        background-color: #fff8f8;
    }

    .compact-table {
        font-size: 0.875rem;
    }

    .compact-table th {
        padding: 0.5rem;
        background-color: #f8f9fa;
    }

    .compact-table td {
        padding: 0.5rem;
        border-bottom: 1px solid #dee2e6;
    }
    </style>
    """

    @classmethod
    def apply_global_styles(cls):
        """Apply global CSS styles to the Streamlit app."""
        st.markdown(cls.CARD_STYLE, unsafe_allow_html=True)

    @classmethod
    def create_metric_card(cls, title: str, value: str, description: str = "") -> str:
        """Create a styled metric card.

        Args:
            title: Card title
            value: Main value to display
            description: Optional description

        Returns:
            HTML string for the metric card
        """
        desc_html = f"<small class='text-muted'>{description}</small>" if description else ""
        return f"""
        <div class="metric-card">
            <h6 class="mb-1">{title}</h6>
            <h4 class="mb-1">{value}</h4>
            {desc_html}
        </div>
        """

    @classmethod
    def create_status_badge(cls, text: str, status: str = "info") -> str:
        """Create a status badge.

        Args:
            text: Badge text
            status: Badge status (success, warning, error, info)

        Returns:
            HTML string for the status badge
        """
        status_class = f"status-{status}"
        return f'<span class="status-badge {status_class}">{text}</span>'

    @classmethod
    def create_progress_bar(cls, percentage: float, label: str = "") -> str:
        """Create a progress bar.

        Args:
            percentage: Progress percentage (0-100)
            label: Optional label

        Returns:
            HTML string for the progress bar
        """
        label_html = f"<small>{label}</small>" if label else ""
        return f"""
        {label_html}
        <div class="progress-container">
            <div class="progress-bar" style="width: {percentage}%"></div>
        </div>
        """

    @classmethod
    def style_hypothesis_card(cls, accepted: bool) -> str:
        """Get CSS class for hypothesis card styling.

        Args:
            accepted: Whether hypothesis was accepted

        Returns:
            CSS class name
        """
        return "hypothesis-accepted" if accepted else "hypothesis-rejected"


class ComponentStyles:
    """Styles for specific UI components."""

    @staticmethod
    def style_dataframe_for_hypotheses(df, decisions):
        """Apply styling to hypothesis dataframe.

        Args:
            df: DataFrame to style
            decisions: Dictionary of decisions

        Returns:
            Styled DataFrame
        """
        def highlight_rows(row):
            if row.name in decisions and decisions[row.name]:
                return ['background-color: #d4edda'] * len(row)
            return [''] * len(row)

        def style_hypothesis_column(col):
            if 'hypothesis' in col.name.lower():
                return ['font-weight: bold'] * len(col)
            return ['font-style: italic'] * len(col)

        return df.style.apply(highlight_rows, axis=1).apply(style_hypothesis_column, axis=0)

    @staticmethod
    def style_metrics_dataframe(df):
        """Apply styling to metrics dataframe.

        Args:
            df: DataFrame to style

        Returns:
            Styled DataFrame
        """
        def highlight_baseline(row):
            if row.name in ["Alpha Base", "Baseline"]:
                return ['background-color: lightblue'] * len(row)
            return [''] * len(row)

        def highlight_ic_columns(col):
            if col.name in ["IC", "ICIR", "Rank IC", "Rank ICIR"]:
                return ['background-color: lightgreen'] * len(col)
            return [''] * len(col)

        return df.style.apply(highlight_baseline, axis=1).apply(highlight_ic_columns, axis=0)


class ThemeManager:
    """Manages theme and appearance settings."""

    @staticmethod
    def get_theme_colors():
        """Get current theme colors from Streamlit.

        Returns:
            Dictionary of theme colors
        """
        # Try to detect if dark mode is enabled
        try:
            # This is a basic detection - Streamlit's theme detection is limited
            return {
                "background": "#ffffff",
                "text": "#262730",
                "primary": "#ff6b6b",
                "secondary": "#4ecdc4",
            }
        except Exception:
            # Fallback to default colors
            return UIStyles.COLORS

    @staticmethod
    def apply_theme_dependent_styles():
        """Apply styles that depend on the current theme."""
        colors = ThemeManager.get_theme_colors()

        theme_css = f"""
        <style>
        .theme-card {{
            background-color: {colors['background']};
            color: {colors['text']};
            border: 1px solid {colors.get('border', '#dee2e6')};
        }}

        .theme-primary {{
            color: {colors['primary']};
        }}

        .theme-secondary {{
            color: {colors['secondary']};
        }}
        </style>
        """

        st.markdown(theme_css, unsafe_allow_html=True)


class IconManager:
    """Manages icons and emojis for the UI."""

    ICONS = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "research": "🔍",
        "hypothesis": "💡",
        "experiment": "🧪",
        "feedback": "📝",
        "development": "🛠️",
        "metrics": "📊",
        "chart": "📈",
        "download": "⬇️",
        "upload": "⬆️",
        "config": "⚙️",
        "loop": "♾️",
        "task": "🚩",
        "factor": "🔢",
        "model": "🤖",
        "strategy": "💼",
    }

    @classmethod
    def get_icon(cls, name: str) -> str:
        """Get icon by name.

        Args:
            name: Icon name

        Returns:
            Icon emoji/symbol
        """
        return cls.ICONS.get(name, "")

    @classmethod
    def format_with_icon(cls, text: str, icon_name: str) -> str:
        """Format text with an icon.

        Args:
            text: Text to format
            icon_name: Name of icon to use

        Returns:
            Formatted string with icon
        """
        icon = cls.get_icon(icon_name)
        return f"{icon} {text}" if icon else text


# Convenience functions for common styling operations
def apply_ui_styles():
    """Apply all UI styles."""
    UIStyles.apply_global_styles()
    ThemeManager.apply_theme_dependent_styles()


def create_success_message(message: str) -> str:
    """Create a success message with styling."""
    return UIStyles.create_status_badge(message, "success")


def create_error_message(message: str) -> str:
    """Create an error message with styling."""
    return UIStyles.create_status_badge(message, "error")


def create_warning_message(message: str) -> str:
    """Create a warning message with styling."""
    return UIStyles.create_status_badge(message, "warning")