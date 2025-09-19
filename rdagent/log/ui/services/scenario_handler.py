"""Scenario handling services for RD-Agent UI."""

import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from rdagent.core.scenario import Scenario
from rdagent.log.storage import FileStorage
from rdagent.scenarios.general_model.scenario import GeneralModelScenario
from rdagent.scenarios.kaggle.experiment.scenario import KGScenario
from rdagent.scenarios.qlib.experiment.factor_experiment import QlibFactorScenario
from rdagent.scenarios.qlib.experiment.factor_from_report_experiment import QlibFactorFromReportScenario
from rdagent.scenarios.qlib.experiment.model_experiment import QlibModelScenario
from rdagent.scenarios.qlib.experiment.quant_experiment import QlibQuantScenario
from rdagent.scenarios.quant_strategy_lab_scenario import CustomStrategyScenario


class ScenarioLoader:
    """Handles loading and identification of scenarios."""

    SUPPORTED_SCENARIOS = {
        "QlibModelScenario": QlibModelScenario,
        "QlibFactorScenario": QlibFactorScenario,
        "QlibFactorFromReportScenario": QlibFactorFromReportScenario,
        "QlibQuantScenario": QlibQuantScenario,
        "KGScenario": KGScenario,
        "CustomStrategyScenario": CustomStrategyScenario,
        "GeneralModelScenario": GeneralModelScenario,
    }

    @classmethod
    def load_scenario_from_path(cls, log_path: Path) -> Optional[Scenario]:
        """Load scenario from log path.

        Args:
            log_path: Path to log directory

        Returns:
            Loaded scenario instance or None if not found
        """
        # Try direct scenario.pkl first (old format)
        scenario_path = log_path / "scenario.pkl"
        if scenario_path.exists():
            try:
                with open(scenario_path, "rb") as f:
                    scenario = pickle.load(f)
                return scenario
            except Exception as e:
                print(f"Error loading scenario from {scenario_path}: {e}")

        # Try new format: scenario/<session_id>/<timestamp>.pkl
        scenario_dir = log_path / "scenario"
        if scenario_dir.exists() and scenario_dir.is_dir():
            for session_dir in scenario_dir.iterdir():
                if session_dir.is_dir():
                    for pkl_file in session_dir.glob("*.pkl"):
                        try:
                            with open(pkl_file, "rb") as f:
                                scenario = pickle.load(f)
                            return scenario
                        except Exception as e:
                            print(f"Error loading scenario from {pkl_file}: {e}")
                            continue

        return None

    @classmethod
    def identify_scenario_type(cls, scenario: Scenario) -> str:
        """Identify the type of scenario.

        Args:
            scenario: Scenario instance

        Returns:
            Scenario type string
        """
        scenario_type = type(scenario).__name__
        return scenario_type

    @classmethod
    def is_supported_scenario(cls, scenario: Scenario) -> bool:
        """Check if scenario is supported.

        Args:
            scenario: Scenario instance

        Returns:
            True if scenario is supported
        """
        scenario_type = cls.identify_scenario_type(scenario)
        return scenario_type in cls.SUPPORTED_SCENARIOS

    @classmethod
    def get_scenario_capabilities(cls, scenario: Scenario) -> Dict[str, bool]:
        """Get capabilities of a scenario.

        Args:
            scenario: Scenario instance

        Returns:
            Dictionary of capabilities
        """
        capabilities = {
            "has_hypotheses": False,
            "has_feedback": False,
            "has_evolution": False,
            "has_experiments": False,
            "has_charts": False,
            "supports_download": False,
        }

        scenario_type = cls.identify_scenario_type(scenario)

        # Define capabilities per scenario type
        scenario_capabilities = {
            "QlibModelScenario": {
                "has_hypotheses": True,
                "has_feedback": True,
                "has_evolution": True,
                "has_experiments": True,
                "has_charts": True,
                "supports_download": True,
            },
            "QlibFactorScenario": {
                "has_hypotheses": True,
                "has_feedback": True,
                "has_evolution": True,
                "has_experiments": True,
                "has_charts": True,
                "supports_download": True,
            },
            "QlibFactorFromReportScenario": {
                "has_hypotheses": True,
                "has_feedback": True,
                "has_evolution": True,
                "has_experiments": True,
                "has_charts": True,
                "supports_download": True,
            },
            "QlibQuantScenario": {
                "has_hypotheses": True,
                "has_feedback": True,
                "has_evolution": True,
                "has_experiments": True,
                "has_charts": True,
                "supports_download": True,
            },
            "KGScenario": {
                "has_hypotheses": True,
                "has_feedback": True,
                "has_evolution": True,
                "has_experiments": True,
                "has_charts": False,
                "supports_download": True,
            },
            "CustomStrategyScenario": {
                "has_hypotheses": True,
                "has_feedback": True,
                "has_evolution": True,
                "has_experiments": True,
                "has_charts": True,
                "supports_download": True,
            },
            "GeneralModelScenario": {
                "has_hypotheses": False,
                "has_feedback": False,
                "has_evolution": True,
                "has_experiments": True,
                "has_charts": False,
                "supports_download": False,
            },
        }

        return scenario_capabilities.get(scenario_type, capabilities)


class ScenarioConfigManager:
    """Manages scenario configurations and settings."""

    @staticmethod
    def get_experiment_setting(scenario: Scenario) -> str:
        """Get experiment setting for scenario.

        Args:
            scenario: Scenario instance

        Returns:
            Experiment setting as HTML string
        """
        if hasattr(scenario, "experiment_setting"):
            return scenario.experiment_setting
        return "No experiment setting available"

    @staticmethod
    def get_scenario_description(scenario: Scenario) -> str:
        """Get human-readable description of scenario.

        Args:
            scenario: Scenario instance

        Returns:
            Scenario description
        """
        scenario_type = ScenarioLoader.identify_scenario_type(scenario)

        descriptions = {
            "QlibModelScenario": "Quantitative Model Development with Qlib",
            "QlibFactorScenario": "Factor Research and Development with Qlib",
            "QlibFactorFromReportScenario": "Factor Extraction from Research Reports",
            "QlibQuantScenario": "Quantitative Strategy Development",
            "KGScenario": "Kaggle Competition Modeling",
            "CustomStrategyScenario": "Custom Trading Strategy Development",
            "GeneralModelScenario": "General Model Research and Development",
        }

        return descriptions.get(scenario_type, f"Unknown Scenario: {scenario_type}")

    @staticmethod
    def get_scenario_tags(scenario: Scenario) -> List[str]:
        """Get relevant tags for scenario.

        Args:
            scenario: Scenario instance

        Returns:
            List of tags
        """
        scenario_type = ScenarioLoader.identify_scenario_type(scenario)

        tag_mapping = {
            "QlibModelScenario": ["qlib", "model", "ml", "finance"],
            "QlibFactorScenario": ["qlib", "factor", "finance", "research"],
            "QlibFactorFromReportScenario": ["qlib", "factor", "report", "extraction"],
            "QlibQuantScenario": ["qlib", "quant", "strategy", "finance"],
            "KGScenario": ["kaggle", "competition", "ml"],
            "CustomStrategyScenario": ["strategy", "custom", "trading"],
            "GeneralModelScenario": ["general", "model", "research"],
        }

        return tag_mapping.get(scenario_type, ["unknown"])


class FileStorageManager:
    """Manages file storage operations for scenarios."""

    @staticmethod
    def create_file_storage(log_path: Path) -> Optional[FileStorage]:
        """Create file storage instance for log path.

        Args:
            log_path: Path to log directory

        Returns:
            FileStorage instance or None if creation fails
        """
        try:
            return FileStorage(log_path)
        except Exception as e:
            print(f"Error creating file storage: {e}")
            return None

    @staticmethod
    def create_message_iterator(log_path: Path):
        """Create message iterator for log path.

        Args:
            log_path: Path to log directory

        Returns:
            Message iterator or None if creation fails
        """
        try:
            storage = FileStorage(log_path)
            return storage.iter_msg()
        except Exception as e:
            print(f"Error creating message iterator: {e}")
            return None

    @staticmethod
    def validate_log_path(log_path: Path) -> bool:
        """Validate that log path contains required files.

        Args:
            log_path: Path to validate

        Returns:
            True if path is valid log directory
        """
        if not log_path.exists() or not log_path.is_dir():
            return False

        # Check for scenario.pkl (old format)
        if (log_path / "scenario.pkl").exists():
            return True

        # Check for new format: scenario/<session_id>/<timestamp>.pkl
        scenario_dir = log_path / "scenario"
        if scenario_dir.exists() and scenario_dir.is_dir():
            for session_dir in scenario_dir.iterdir():
                if session_dir.is_dir():
                    pkl_files = list(session_dir.glob("*.pkl"))
                    if pkl_files:
                        return True

        return False

    @staticmethod
    def get_log_metadata(log_path: Path) -> Dict[str, Any]:
        """Get metadata about log directory.

        Args:
            log_path: Path to log directory

        Returns:
            Dictionary with log metadata
        """
        if not log_path.exists():
            return {}

        stat = log_path.stat()
        return {
            "created_time": stat.st_ctime,
            "modified_time": stat.st_mtime,
            "size_bytes": sum(f.stat().st_size for f in log_path.rglob("*") if f.is_file()),
            "file_count": len(list(log_path.rglob("*"))),
            "has_scenario": (log_path / "scenario.pkl").exists(),
        }