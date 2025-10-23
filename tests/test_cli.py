"""
Basic tests for Salt Docs CLI.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the CLI module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from salt_docs.cli import main
from salt_docs.config import load_config, save_config


class TestCLI:
    """Test CLI functionality."""
    
    def test_init_command(self):
        """Test that init command works without errors."""
        with patch('salt_docs.cli.init_config') as mock_init:
            with patch('sys.argv', ['salt-docs', 'init']):
                main()
                mock_init.assert_called_once()
    
    def test_config_show_command(self):
        """Test config show command."""
        # Create a temporary config file
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            test_config = {
                "output_dir": "/tmp/test",
                "language": "english",
                "max_abstractions": 10
            }
            
            with patch('salt_docs.config.CONFIG_FILE', config_path):
                save_config(test_config)
                
                with patch('sys.argv', ['salt-docs', 'config', 'show']):
                    with patch('builtins.print') as mock_print:
                        main()
                        # Should print the config
                        assert mock_print.called
    
    def test_main_without_config(self):
        """Test that main exits when config doesn't exist."""
        with patch('salt_docs.cli.check_config_exists', return_value=False):
            with patch('sys.argv', ['salt-docs', '--help']):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1


class TestConfig:
    """Test configuration functionality."""
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            test_config = {
                "output_dir": "/tmp/test",
                "language": "english",
                "max_abstractions": 10
            }
            
            with patch('salt_docs.config.CONFIG_FILE', config_path):
                save_config(test_config)
                loaded_config = load_config()
                # Check that our specific values are preserved
                assert loaded_config["output_dir"] == "/tmp/test"
                assert loaded_config["language"] == "english"
                assert loaded_config["max_abstractions"] == 10
                # Check that default values are also present
                assert "exclude_patterns" in loaded_config
                assert "include_patterns" in loaded_config


if __name__ == "__main__":
    pytest.main([__file__])
