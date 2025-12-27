"""
Tests for CI/CD integration features in WikiGen CLI.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from wikigen.cli import main, _run_documentation_generation


class TestCIIntegration:
    """Test CI/CD specific functionality."""

    def test_ci_flag_parsing(self):
        """Test that --ci flag is correctly parsed and passed to generation."""
        with (
            patch("wikigen.cli.check_config_exists", return_value=True),
            patch("wikigen.cli.load_config", return_value={"output_dir": "docs"}),
            patch("wikigen.cli._run_documentation_generation") as mock_run,
        ):

            # Test with explicit --ci flag
            with patch("sys.argv", ["wikigen", "run", ".", "--ci"]):
                main()
                args = mock_run.call_args[0][2]
                assert args.ci is True

    def test_ci_env_var_detection(self):
        """Test that CI environment variable is detected."""
        # Mock args object
        mock_args = MagicMock()
        mock_args.ci = False
        mock_args.output_path = None
        mock_args.update = False
        mock_args.check_changes = False
        mock_args.name = "test-project"
        mock_args.token = None

        mock_config = {
            "output_dir": "output",
            "include_patterns": [],
            "exclude_patterns": [],
            "max_file_size": 1000,
            "language": "english",
            "use_cache": True,
            "max_abstractions": 10,
        }

        # Test with CI=true environment variable
        with (
            patch.dict(os.environ, {"CI": "true"}),
            patch("wikigen.cli.create_wiki_flow") as mock_flow_factory,
            patch("wikigen.cli.print_info") as mock_print_info,
        ):

            mock_flow = MagicMock()
            mock_flow_factory.return_value = mock_flow

            _run_documentation_generation(None, ".", mock_args, mock_config)

            # Verify CI mode was detected and passed to shared context
            shared_context = mock_flow.run.call_args[0][0]
            assert shared_context["ci_mode"] is True

            # Verify "CI Mode Enabled" was printed
            mock_print_info.assert_any_call("CI Mode", "Enabled")

    def test_output_path_flag(self):
        """Test that --output-path flag overrides config output_dir."""
        mock_args = MagicMock()
        mock_args.ci = True
        mock_args.output_path = "custom/docs/path"
        mock_args.update = False
        mock_args.check_changes = False
        mock_args.name = "test-project"
        mock_args.token = None

        mock_config = {
            "output_dir": "default/output",
            "include_patterns": [],
            "exclude_patterns": [],
            "max_file_size": 1000,
            "language": "english",
            "use_cache": True,
            "max_abstractions": 10,
        }

        with (
            patch("wikigen.cli.create_wiki_flow") as mock_flow_factory,
            patch("wikigen.cli.print_info"),
        ):

            mock_flow = MagicMock()
            mock_flow_factory.return_value = mock_flow

            _run_documentation_generation(None, ".", mock_args, mock_config)

            # Verify output_dir was updated in shared context
            shared_context = mock_flow.run.call_args[0][0]
            assert shared_context["output_dir"] == "custom/docs/path"

    def test_check_changes_exit_code(self):
        """Test that --check-changes exits with 1 if changes detected."""
        mock_args = MagicMock()
        mock_args.ci = True
        mock_args.check_changes = True
        mock_args.output_path = None
        mock_args.update = False
        mock_args.name = "test-project"
        mock_args.token = None

        mock_config = {
            "output_dir": "output",
            "include_patterns": [],
            "exclude_patterns": [],
            "max_file_size": 1000,
            "language": "english",
            "use_cache": True,
            "max_abstractions": 10,
        }

        with (
            patch("wikigen.cli.create_wiki_flow") as mock_flow_factory,
            patch("wikigen.cli.print_info"),
            patch("wikigen.cli.print_final_success"),
        ):

            mock_flow = MagicMock()

            # Simulate flow run setting docs_changed = True
            def side_effect(shared):
                shared["docs_changed"] = True

            mock_flow.run.side_effect = side_effect
            mock_flow_factory.return_value = mock_flow

            # Expect SystemExit(1) because changes were detected
            with pytest.raises(SystemExit) as exc_info:
                _run_documentation_generation(None, ".", mock_args, mock_config)
            assert exc_info.value.code == 1

    def test_check_changes_no_exit_code(self):
        """Test that --check-changes exits with 0 if no changes detected."""
        mock_args = MagicMock()
        mock_args.ci = True
        mock_args.check_changes = True
        mock_args.output_path = None
        mock_args.update = False
        mock_args.name = "test-project"
        mock_args.token = None

        mock_config = {
            "output_dir": "output",
            "include_patterns": [],
            "exclude_patterns": [],
            "max_file_size": 1000,
            "language": "english",
            "use_cache": True,
            "max_abstractions": 10,
        }

        with (
            patch("wikigen.cli.create_wiki_flow") as mock_flow_factory,
            patch("wikigen.cli.print_info"),
            patch("wikigen.cli.print_final_success"),
        ):

            mock_flow = MagicMock()

            # Simulate flow run setting docs_changed = False
            def side_effect(shared):
                shared["docs_changed"] = False

            mock_flow.run.side_effect = side_effect
            mock_flow_factory.return_value = mock_flow

            # Expect SystemExit(0) because no changes were detected
            with pytest.raises(SystemExit) as exc_info:
                _run_documentation_generation(None, ".", mock_args, mock_config)
            assert exc_info.value.code == 0
