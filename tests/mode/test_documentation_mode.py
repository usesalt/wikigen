"""
Test documentation mode configuration.
"""

import pytest
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wikigen.config import load_config, save_config, CONFIG_FILE
from wikigen.defaults import DEFAULT_CONFIG


class TestDocumentationMode:
    """Test documentation mode configuration."""

    def test_default_is_minimal(self):
        """Test that DEFAULT_CONFIG has minimal as default."""
        assert (
            DEFAULT_CONFIG["documentation_mode"] == "minimal"
        ), "Default should be minimal"

    def test_config_saves_documentation_mode(self):
        """Test that documentation_mode can be saved and loaded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            with patch("wikigen.config.CONFIG_FILE", config_file):
                # Test minimal mode
                test_config = {
                    "output_dir": "/tmp/test",
                    "language": "english",
                    "max_abstractions": 10,
                    "documentation_mode": "minimal",
                }
                save_config(test_config)
                loaded_config = load_config()
                assert (
                    loaded_config.get("documentation_mode") == "minimal"
                ), "Should save and load minimal mode"

                # Test comprehensive mode
                test_config["documentation_mode"] = "comprehensive"
                save_config(test_config)
                loaded_config = load_config()
                assert (
                    loaded_config.get("documentation_mode") == "comprehensive"
                ), "Should save and load comprehensive mode"

    def test_config_defaults_to_minimal_when_not_set(self):
        """Test that config defaults to minimal when documentation_mode is not set."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            with patch("wikigen.config.CONFIG_FILE", config_file):
                # Save config without documentation_mode
                test_config = {
                    "output_dir": "/tmp/test",
                    "language": "english",
                    "max_abstractions": 10,
                }
                save_config(test_config)
                loaded_config = load_config()
                # Should get minimal from DEFAULT_CONFIG
                assert (
                    loaded_config.get("documentation_mode") == "minimal"
                ), "Should default to minimal when not set"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
