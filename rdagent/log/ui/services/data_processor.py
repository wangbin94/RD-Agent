"""Data processing services for RD-Agent UI."""

import re
from collections import defaultdict
from pathlib import Path
from typing import Callable, Dict, List, Optional

from rdagent.log.base import Message
from rdagent.log.storage import FileStorage


class LogFolderProcessor:
    """Handles log folder operations and filtering."""

    @staticmethod
    def filter_log_folders(main_log_path: Path) -> List[Path]:
        """Filter and return the log folders relative to the main log path.

        Args:
            main_log_path: Main log directory path

        Returns:
            List of folder paths sorted by modification time (newest first)
        """
        if not main_log_path.exists():
            return []

        folders = [
            folder.relative_to(main_log_path)
            for folder in main_log_path.iterdir()
            if folder.is_dir()
        ]

        # Sort by modification time, newest first
        folders = sorted(
            folders,
            key=lambda x: (main_log_path / x).stat().st_mtime,
            reverse=True
        )
        return folders

    @staticmethod
    def get_latest_log_folder(main_log_path: Optional[Path]) -> Optional[Path]:
        """Get the latest log folder.

        Args:
            main_log_path: Main log directory path

        Returns:
            Latest log folder path or None if not found
        """
        if not main_log_path:
            return None

        folders = LogFolderProcessor.filter_log_folders(main_log_path)
        return folders[0] if folders else None


class MessageProcessor:
    """Handles message processing and filtering."""

    @staticmethod
    def should_display_message(msg: Message, excluded_tags: List[str], excluded_types: List[str]) -> bool:
        """Check if a message should be displayed.

        Args:
            msg: Message to check
            excluded_tags: List of tags to exclude
            excluded_types: List of content types to exclude

        Returns:
            True if message should be displayed
        """
        # Check excluded tags
        all_excluded_tags = excluded_tags + ["debug_tpl", "debug_llm"]
        for tag in all_excluded_tags:
            if tag in msg.tag.split("."):
                return False

        # Check excluded types
        if type(msg.content).__name__ in excluded_types:
            return False

        return True

    @staticmethod
    def clean_message_tag(tag: str) -> str:
        """Clean and normalize message tags.

        Args:
            tag: Original message tag

        Returns:
            Cleaned tag string
        """
        # Remove evolving loop tags
        tag = re.sub(r"\.evo_loop_\d+", "", tag)
        tag = re.sub(r"Loop_\d+\.[^.]+", "", tag)
        tag = re.sub(r"\.\.", ".", tag)

        # Remove old redundant tags
        tag = re.sub(r"init\.", "", tag)
        tag = re.sub(r"r\.", "", tag)
        tag = re.sub(r"d\.", "", tag)
        tag = re.sub(r"ef\.", "", tag)

        return tag.strip(".")

    @staticmethod
    def categorize_message(msg: Message) -> str:
        """Categorize message based on its tag and content.

        Args:
            msg: Message to categorize

        Returns:
            Category string
        """
        tag = msg.tag.lower()

        if "hypothesis" in tag:
            return "hypothesis"
        elif "feedback" in tag:
            return "feedback"
        elif "evolving" in tag or "coding" in tag:
            return "development"
        elif "experiment" in tag:
            return "experiment"
        elif "research" in tag:
            return "research"
        else:
            return "other"


class MessageStreamProcessor:
    """Processes message streams and updates state."""

    def __init__(self):
        self.message_processor = MessageProcessor()

    def process_messages_until(
        self,
        fs_iterator,
        excluded_tags: List[str],
        excluded_types: List[str],
        end_func: Callable[[Message], bool] = lambda _: True
    ) -> Dict[str, any]:
        """Process messages from file storage iterator until end condition.

        Args:
            fs_iterator: Message iterator from FileStorage.iter_msg()
            excluded_tags: Tags to exclude from processing
            excluded_types: Content types to exclude
            end_func: Function to determine when to stop processing

        Returns:
            Dictionary with processed data including messages, rounds, etc.
        """
        result = {
            "msgs": defaultdict(lambda: defaultdict(list)),
            "lround": 0,
            "erounds": defaultdict(int),
            "current_tags": [],
            "last_msg": None,
            "hypotheses": defaultdict(lambda: None),
            "h_decisions": defaultdict(bool),
        }

        while True:
            try:
                msg = next(fs_iterator)
                if not self.message_processor.should_display_message(msg, excluded_tags, excluded_types):
                    continue

                tags = msg.tag.split(".")

                # Update round counter for hypothesis generation
                if "hypothesis generation" in msg.tag:
                    result["lround"] += 1

                # Clean message tag
                msg.tag = self.message_processor.clean_message_tag(msg.tag)

                # Update evolving rounds
                if "evolving code" not in result["current_tags"] and "evolving code" in tags:
                    result["erounds"][result["lround"]] += 1
                elif "coding" not in result["current_tags"] and "coding" in tags:
                    result["erounds"][result["lround"]] += 1

                result["current_tags"] = tags

                # Store message by category
                category = self.message_processor.categorize_message(msg)
                result["msgs"][result["lround"]][category].append(msg)
                result["last_msg"] = msg

                # Check end condition
                if end_func(msg):
                    break

            except StopIteration:
                break

        return result


class MetricsProcessor:
    """Processes and analyzes metrics data."""

    @staticmethod
    def extract_hypothesis_metrics(hypotheses_data: Dict) -> Dict[str, float]:
        """Extract metrics from hypotheses data.

        Args:
            hypotheses_data: Dictionary containing hypotheses information

        Returns:
            Dictionary of extracted metrics
        """
        metrics = {}

        # Extract common metrics if available
        for key, value in hypotheses_data.items():
            if isinstance(value, (int, float)):
                metrics[key] = float(value)

        return metrics

    @staticmethod
    def calculate_success_rate(decisions: Dict[int, bool]) -> float:
        """Calculate success rate from decisions.

        Args:
            decisions: Dictionary mapping round to success boolean

        Returns:
            Success rate as a percentage
        """
        if not decisions:
            return 0.0

        successful = sum(1 for decision in decisions.values() if decision)
        total = len(decisions)

        return (successful / total) * 100.0

    @staticmethod
    def aggregate_round_metrics(round_data: Dict[int, Dict]) -> Dict[str, any]:
        """Aggregate metrics across rounds.

        Args:
            round_data: Dictionary mapping round number to round data

        Returns:
            Aggregated metrics
        """
        total_rounds = len(round_data)
        if total_rounds == 0:
            return {"total_rounds": 0}

        aggregated = {
            "total_rounds": total_rounds,
            "completed_rounds": total_rounds,
            "average_metrics": {},
        }

        # Collect all metric keys
        all_metrics = set()
        for round_metrics in round_data.values():
            if isinstance(round_metrics, dict):
                all_metrics.update(round_metrics.keys())

        # Calculate averages for each metric
        for metric in all_metrics:
            values = []
            for round_metrics in round_data.values():
                if isinstance(round_metrics, dict) and metric in round_metrics:
                    value = round_metrics[metric]
                    if isinstance(value, (int, float)):
                        values.append(float(value))

            if values:
                aggregated["average_metrics"][metric] = sum(values) / len(values)

        return aggregated